# Portfolio reviews

When asked to review the DIMAGGI AI infrastructure portfolio, follow
`PORTFOLIO.md` and run `python3 tools/portfolio_snapshot.py` before analysis.
Use only custom-property membership, retrieve all pages, and report the selected
repositories and commit SHAs. Analyze those exact commits from clean checkouts.
Do not substitute topics, names, README content or the public website's links for
membership. Stop the collective review on an incomplete snapshot and report the
retrieval/access failures. Keep generated manifests containing private repository
details out of public commits. Read each member repository's own instructions.

For changes to snapshot discovery, run:

```sh
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/validate_evidence.py evidence.json
```
