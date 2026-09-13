#!/usr/bin/env python3
"""Resolve explicit portfolio membership and freeze its default-branch commits."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote


def now():
    return datetime.now(timezone.utc).isoformat()


def github(endpoint, paginate=False):
    command = ["gh", "api", "--hostname", "github.com", endpoint,
               "-H", "Accept: application/vnd.github+json"]
    if paginate:
        command += ["--paginate", "--slurp"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"GitHub request failed: {endpoint}: {exc}") from exc
    if result.returncode:
        raise RuntimeError(f"GitHub request failed: {endpoint}: {result.stderr.strip()}")
    try:
        data = json.loads(result.stdout)
    except ValueError as exc:
        raise RuntimeError(f"Invalid JSON returned for {endpoint}") from exc
    if paginate:
        if not isinstance(data, list) or not all(isinstance(page, list) for page in data):
            raise RuntimeError(f"Expected complete array pages for {endpoint}")
        return [row for page in data for row in page]
    return data


def indexed(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if value in result:
            raise ValueError(f"Duplicate repository ID in inventory: {value}")
        result[value] = row
    return result


def selected_repositories(repos, properties, portfolio):
    """A topic, name, description or README can never add a member."""
    repo_ids = indexed(repos, "id")
    prop_ids = indexed(properties, "repository_id")
    if repo_ids.keys() != prop_ids.keys():
        raise ValueError("Repository inventory and property inventory disagree; retry discovery.")
    selected = []
    for repo_id, row in prop_ids.items():
        matches = [p for p in row["properties"] if p["property_name"] == "portfolio"]
        if len(matches) > 1:
            raise ValueError(f"Duplicate portfolio property for {row['repository_full_name']}")
        values = matches[0]["value"] if matches else None
        if values is not None and (
            not isinstance(values, list) or not all(isinstance(v, str) for v in values)
        ):
            raise ValueError(f"Expected multi-select portfolio values for {row['repository_full_name']}")
        if values and portfolio in values:
            repo = repo_ids[repo_id]
            if repo["full_name"] != row["repository_full_name"]:
                raise ValueError("Repository renamed during discovery; retry.")
            selected.append(repo)
    return sorted(selected, key=lambda r: r["full_name"].lower())


def snapshot(org="dimaggi-ai", portfolio="ai-infrastructure", api=github):
    manifest = {
        "schema_version": "dimaggi-portfolio-snapshot/v1",
        "organization": org,
        "selector": {"property": "portfolio", "contains": portfolio},
        "retrieval_started_at": now(),
        "status": "incomplete",
        "errors": [],
        "repositories": [],
    }
    try:
        schema = api(f"orgs/{org}/properties/schema/portfolio")
        if schema["value_type"] != "multi_select" or portfolio not in schema["allowed_values"]:
            raise ValueError("The requested portfolio must be declared in a multi-select schema.")
        organization = api(f"orgs/{org}")
        private_count = organization.get("total_private_repos")
        if not isinstance(private_count, int):
            raise ValueError("Cannot verify organization-wide coverage: private repository count unavailable.")
        repos = api(f"orgs/{org}/repos?type=all&per_page=100", paginate=True)
        expected_count = organization["public_repos"] + private_count
        manifest["inventory_count"] = len(repos)
        manifest["organization_repository_count"] = expected_count
        if len(repos) != expected_count:
            raise ValueError("Accessible repository count does not match organization count; check access or retry.")
        properties = api(f"orgs/{org}/properties/values?per_page=100", paginate=True)
        selected = selected_repositories(repos, properties, portfolio)
        manifest["membership_captured_at"] = now()
        manifest["selected_count"] = len(selected)
        if not selected:
            raise ValueError("Portfolio selection is empty; analysis must not proceed.")
        for repo in selected:
            item = {
                "repository_id": repo["id"],
                "repository": repo["full_name"],
                "visibility": repo["visibility"],
                "archived": repo["archived"],
                "default_branch": repo["default_branch"],
                "commit_sha": None,
            }
            manifest["repositories"].append(item)
            try:
                branch = quote(repo["default_branch"], safe="")
                commit = api(f"repos/{repo['full_name']}/commits/{branch}")
                sha = commit["sha"]
                if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
                    raise ValueError("GitHub did not return a full commit SHA.")
                item.update(commit_sha=sha, resolved_at=now(),
                            commit_url=f"https://github.com/{repo['full_name']}/tree/{sha}")
            except (RuntimeError, ValueError, KeyError, TypeError) as exc:
                manifest["errors"].append(f"{repo['full_name']}: {exc}")
        if not manifest["errors"]:
            manifest["status"] = "complete"
    except (RuntimeError, ValueError, KeyError, TypeError) as exc:
        manifest["errors"].append(str(exc))
    manifest["retrieval_finished_at"] = now()
    return manifest


def compare_membership(current, previous):
    if previous.get("status") != "complete" or current["status"] != "complete":
        raise ValueError("Membership comparison requires two complete snapshots.")
    for field in ("schema_version", "organization", "selector"):
        if previous.get(field) != current[field]:
            raise ValueError(f"Previous snapshot has a different {field}.")
    old = indexed(previous["repositories"], "repository_id")
    new = indexed(current["repositories"], "repository_id")
    return {
        "added": sorted(new[i]["repository"] for i in new.keys() - old.keys()),
        "removed": sorted(old[i]["repository"] for i in old.keys() - new.keys()),
        "renamed": [{"from": old[i]["repository"], "to": new[i]["repository"]}
                    for i in sorted(old.keys() & new.keys())
                    if old[i]["repository"] != new[i]["repository"]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org", default="dimaggi-ai")
    parser.add_argument("--portfolio", default="ai-infrastructure")
    parser.add_argument("--out", type=Path, help="New local manifest file; never overwrites an existing run")
    parser.add_argument("--previous", type=Path, help="Compare membership against a prior complete run")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]+", args.org):
        parser.error("Invalid organization name")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.out or Path(__file__).resolve().parents[1] / "portfolio-runs" / f"{stamp}.json"
    if output.exists():
        parser.error(f"Refusing to overwrite {output}")
    manifest = snapshot(args.org, args.portfolio)
    if args.previous:
        try:
            manifest["membership_changes"] = compare_membership(
                manifest, json.loads(args.previous.read_text()))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            manifest["status"] = "incomplete"
            manifest["errors"].append(f"Previous snapshot: {exc}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as handle:
        output.chmod(0o600)
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(f"{manifest['status'].upper()}: {output}")
    for repo in manifest["repositories"]:
        print(f"{repo['repository']}  {repo['default_branch']}  {repo['commit_sha'] or 'UNRESOLVED'}")
    for error in manifest["errors"]:
        print(error, file=sys.stderr)
    return 0 if manifest["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
