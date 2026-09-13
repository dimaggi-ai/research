import copy
import json
import subprocess
import unittest
from unittest.mock import patch

from portfolio_snapshot import compare_membership, github, snapshot


SHA = "a" * 40


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.repos = [
            dict(id=1, full_name="example/topic-only", visibility="public",
                 archived=False, default_branch="main", topics=["ai-infrastructure"]),
            dict(id=2, full_name="example/selected", visibility="public",
                 archived=False, default_branch="main", topics=[]),
            dict(id=3, full_name="example/private-member", visibility="private",
                 archived=True, default_branch="build/integration", topics=[]),
        ]
        self.props = [dict(repository_id=r["id"], repository_full_name=r["full_name"],
                           properties=[] if r["id"] == 1 else [
                               dict(property_name="portfolio", value=["other", "ai-infrastructure"])])
                      for r in self.repos]
        self.calls = []

    def api(self, endpoint, paginate=False):
        self.calls.append((endpoint, paginate))
        if endpoint.endswith("/properties/schema/portfolio"):
            return dict(value_type="multi_select", allowed_values=["ai-infrastructure"])
        if endpoint == "orgs/example":
            return dict(public_repos=2, total_private_repos=1)
        if "/repos?" in endpoint:
            self.assertTrue(paginate)
            return self.repos
        if "/properties/values?" in endpoint:
            self.assertTrue(paginate)
            return self.props
        if "/commits/" in endpoint:
            return dict(sha=SHA)
        raise AssertionError(endpoint)

    def test_property_only_scope_includes_private_archived_and_slash_branch(self):
        result = snapshot("example", api=self.api)
        self.assertEqual(result["status"], "complete")
        self.assertEqual([r["repository_id"] for r in result["repositories"]], [3, 2])
        self.assertTrue(all(r["commit_sha"] == SHA for r in result["repositories"]))
        self.assertIn(("repos/example/private-member/commits/build%2Fintegration", False), self.calls)

    def test_all_pages_are_used(self):
        def run(command, **kwargs):
            endpoint = command[4]
            paginated = "--paginate" in command
            data = self.api(endpoint, paginate=paginated)
            if paginated:
                self.assertIn("--slurp", command)
                data = [data[:1], data[1:]]
            return subprocess.CompletedProcess(command, 0, json.dumps(data), "")
        with patch("portfolio_snapshot.subprocess.run", side_effect=run):
            result = snapshot("example")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["selected_count"], 2)

    def test_pagination_failure_never_accepts_partial_stdout(self):
        response = subprocess.CompletedProcess([], 1, json.dumps([self.props[:1]]), "page 2 denied")
        with patch("portfolio_snapshot.subprocess.run", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "page 2 denied"):
                github("orgs/example/properties/values", paginate=True)

    def test_missing_commit_is_incomplete_and_keeps_full_selected_set(self):
        def api(endpoint, **kwargs):
            if "private-member/commits/" in endpoint:
                raise RuntimeError("access denied")
            return self.api(endpoint, **kwargs)
        result = snapshot("example", api=api)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(len(result["repositories"]), 2)
        self.assertIsNone(result["repositories"][0]["commit_sha"])
        self.assertIn("access denied", result["errors"][0])

    def test_inventory_mismatch_and_partial_access_fail(self):
        self.props.pop()
        result = snapshot("example", api=self.api)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("inventor", result["errors"][0])
        self.repos.pop()
        result = snapshot("example", api=self.api)
        self.assertIn("count", result["errors"][0])

    def test_unavailable_organization_count_fails(self):
        def api(endpoint, **kwargs):
            if endpoint == "orgs/example":
                return dict(public_repos=2)
            return self.api(endpoint, **kwargs)
        result = snapshot("example", api=api)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("coverage", result["errors"][0])

    def test_empty_or_malformed_membership_never_falls_back_to_topics(self):
        for row in self.props:
            row["properties"] = []
        result = snapshot("example", api=self.api)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("empty", result["errors"][0])
        self.props[0]["properties"] = [dict(property_name="portfolio", value="ai-infrastructure")]
        result = snapshot("example", api=self.api)
        self.assertIn("multi-select", result["errors"][0])

    def test_membership_diff_uses_stable_ids_and_rejects_incomplete_runs(self):
        current = snapshot("example", api=self.api)
        previous = copy.deepcopy(current)
        previous["repositories"][0]["repository"] = "example/old-name"
        previous["repositories"][1]["repository_id"] = 4
        previous["repositories"][1]["repository"] = "example/removed"
        changes = compare_membership(current, previous)
        self.assertEqual(changes["added"], ["example/selected"])
        self.assertEqual(changes["removed"], ["example/removed"])
        self.assertEqual(changes["renamed"], [
            {"from": "example/old-name", "to": "example/private-member"}])
        previous["status"] = "incomplete"
        with self.assertRaisesRegex(ValueError, "complete"):
            compare_membership(current, previous)


if __name__ == "__main__":
    unittest.main()
