# pylxd Copilot Instructions

pylxd is the Python client library for the LXD REST API. It supports Python 3.10 or
higher and every LXD version in the CI matrix (`.github/workflows/tests.yml`).
See [`AGENTS.md`](../AGENTS.md) for the full development runbook.

## Repository layout

```
pylxd/client.py      Client, _APINode     pylxd/managers.py    Resource managers
pylxd/models/        One module per LXD resource, base class in _model.py
pylxd/tests/         mock_lxd.py, testing.py, client unit tests
pylxd/models/tests/  Model unit tests     integration/         Need a real LXD
doc/source/          Sphinx docs          pyproject.toml       Deps, tox envs, lint config
```

## Validate

```bash
tox -e format   # isort + Black
tox -e lint     # Black, isort, flake8, check-manifest
tox -e check    # mypy
tox -e unit     # pytest with doctests
tox -e coverage # must not drop
```

## Review checklist

- New endpoints and fields are gated with `client.assert_has_api_extension(...)` or
  `client.has_api_extension(...)`, never on the server version.
- Unit tests subclass `PyLXDTestCase`, reuse `pylxd/tests/mock_lxd.py`, and never
  contact a real LXD daemon. Both sides of an extension gate are tested.
- The public API stays backward compatible; public API changes update `doc/source/`.
- Untestable lines use `# pragma: no cover` with a reason.
- No new runtime dependencies without maintainer agreement.

## Commit requirements

Format `<area>: <lowercase imperative description>`, for example
`pylxd/models/image: add return type hint for create`. All commits are signed off
with `git commit -s` by the human committer; AI agents must not add `Signed-off-by`.
