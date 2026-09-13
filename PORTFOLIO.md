# Reviewing the AI infrastructure portfolio

Membership is defined exclusively by the `dimaggi-ai` organization custom
property `portfolio` containing `ai-infrastructure`. It is an optional
multi-select with no default. Unset is the absence of a value, not an option.
Topics, repository names, visibility and README content never establish scope.
The portfolio includes public and private repositories. Its membership can evolve;
there is no hard-coded repository list or permanent expected count in the runner.

## Capture a review

Use GitHub CLI authenticated to an account with full organization repository
visibility and permission to read organization custom properties:

```sh
python3 tools/portfolio_snapshot.py
```

The command reads every page of repository inventory and property values, compares
their repository IDs and checks inventory coverage against the organization counts.
It resolves each selected default branch to a full commit SHA and prints the set.
The timestamped JSON manifest records scope, visibility, branches, commit URLs,
retrieval times and failures. These requests form a timestamped observation window,
not an atomic GitHub transaction. Branch names can differ between repositories.

Proceed only on exit code `0` and manifest `status: complete`. Missing properties,
empty selection, unavailable private inventory counts, count/ID mismatches, API
failures or unresolved commits produce an incomplete manifest and nonzero exit.
GitHub permissions determine what the account can read; a partial inventory must
not be presented as an organization-wide review.

Compare membership with a previous complete run when available:

```sh
python3 tools/portfolio_snapshot.py --previous portfolio-runs/PREVIOUS.json
```

Repository IDs distinguish renames from additions and removals. A count change
is reported through the membership diff; it is not automatically rejected.
Reports live in the ignored `portfolio-runs/` directory and may name private
repositories. Keep them local or in an appropriately restricted report location.
The snapshot command only reads GitHub; it does not clone, edit, publish or run code.

## Analyze the recorded commits

Before analysis, report the selected repositories and SHAs. Fetch those exact
commits into dedicated clean checkouts, verify each checkout's `HEAD` against the
manifest, and read that repository's instructions. Do not analyze a moving branch
or include uncommitted local edits under a recorded commit SHA. Select checks for
the repository's actual contents: models, contracts, documentation and integration
experiments need different reviews. Membership does not imply production readiness.

Keep the manifest with the report. Record analysis instructions, tool versions and
external evidence separately if reproducibility beyond source inputs is required.
Identify collective findings and repository-specific improvements. Changes should
be proposed against each repository's current base and revalidated for intervening
changes. A review request alone does not authorize live infrastructure operations.

## Navigate and maintain membership

In the GitHub repository dashboard, create a saved view named **AI Infrastructure**:

```text
organization:dimaggi-ai props.portfolio:ai-infrastructure
```

The [filtered organization repository list](https://github.com/orgs/dimaggi-ai/repositories?q=props.portfolio%3Aai-infrastructure)
is also a bookmarkable entry point. This UI query is not the automation API.

Organization administrators manage membership in **Settings → Repository → Custom
properties → Set values**. Add or remove the `ai-infrastructure` selection explicitly,
preserving other portfolio memberships and unrelated properties. New repositories
remain outside the portfolio until assigned. Optional descriptive topics do not
need to match the portfolio membership.

References: [custom properties](https://docs.github.com/en/organizations/managing-organization-settings/managing-custom-properties-for-repositories-in-your-organization),
[property-values API](https://docs.github.com/en/rest/orgs/custom-properties#list-custom-property-values-for-organization-repositories),
[saved repository views](https://docs.github.com/en/repositories/creating-and-managing-repositories/viewing-all-your-repositories).
