# AGENTS.md — pylxd Agent Instructions

pylxd is the Python client library for the [LXD](https://ubuntu.com/lxd) REST API.
Package: `pylxd` on PyPI. License: Apache-2.0. Default branch and PR target: `main`.

These instructions are for any AI coding agent, whichever tool or model drives it.
The human contribution guide is `doc/source/contributing.rst`; read it too.

## Prerequisites

- Python 3.10 or higher and [tox](https://tox.wiki/) 4.21 or higher.
- Every check runs through tox. Environments are defined in `pyproject.toml` under
  `[tool.tox]`; there is no `tox.ini`, `Makefile`, or `requirements.txt`.
- Linting, type checking, and unit tests need no LXD daemon.

```bash
python3 -m venv venv
. ./venv/bin/activate
pip install --upgrade pip tox
```

tox needs network access the first time it builds an environment. If you have none,
say which checks you skipped in the pull request; CI runs all of them.

## Repository layout

```
pylxd/
  __init__.py        Re-exports Client and EventType
  client.py          Client, _APINode (REST tree traversal), transports, events
  managers.py        BaseManager and one manager class per resource
  exceptions.py      Exception hierarchy (LXDAPIException, NotFound, ...)
  models/
    _model.py        Model base class, Attribute descriptors, save/delete/sync
    <resource>.py    One module per LXD resource
    tests/           Unit tests for the models
  tests/
    mock_lxd.py      Mock LXD responses (RULES) shared by every unit test
    testing.py       PyLXDTestCase base class and test helpers
    test_client.py   Unit tests for the client
integration/         Integration tests (need a real LXD daemon)
doc/source/          Sphinx documentation, one page per resource plus api.rst
contrib_testing/     Manual scripts, not run by CI
```

No tracked file is generated. `build/`, `dist/`, `*.egg-info`, `.tox/`, and `doc/build/`
are local artifacts; never commit them.

## Build

pylxd is pure Python and has no build step for development. `tox -e release` builds the
sdist and wheel; maintainers use it when cutting a release.

## Architecture

1. `pylxd.Client` is the only public entry point. `client.api` is an `_APINode`
   that maps attribute and item access onto REST paths:
   `client.api.instances["c1"].get()` issues `GET /1.0/instances/c1`.
2. Managers in `pylxd/managers.py` expose each model's class methods (`get`, `all`,
   `create`, `exists`) on the client, for example `client.instances.get("c1")`.
3. Models in `pylxd/models/` declare their fields with `model.Attribute(...)` and
   inherit `sync`/`save`/`delete` from `Model`.

Adding or extending a resource usually touches, in this order:

| Step | File |
|------|------|
| Model and its attributes | `pylxd/models/<resource>.py` |
| Export (new classes only) | `pylxd/models/__init__.py` |
| Manager wiring (new resources only) | `pylxd/managers.py`, `pylxd/client.py` |
| Mock responses | `pylxd/tests/mock_lxd.py` |
| Unit tests | `pylxd/models/tests/test_<resource>.py` |
| Integration tests | `integration/test_<resource>.py` |
| Documentation | `doc/source/<resource>.rst`, `doc/source/api.rst` |

## Validate before committing

Run these in order. Each must pass before moving to the next.

```bash
# 1. Auto-format (isort + Black)
tox -e format

# 2. Lint (Black and isort checks, flake8, check-manifest)
tox -e lint

# 3. Type check (mypy)
tox -e check

# 4. Unit tests (pytest with doctests)
tox -e unit

# 5. Coverage; the total must not drop
tox -e coverage

# 6. Only if doc/ changed
tox -e doc

# 7. Only if a shell script changed (CI runs this in the lint job)
shellcheck integration/run-integration-tests*
```

`tox -e lint` runs `check-manifest`. A new tracked file that is not Python must be
either shipped through `MANIFEST.in` or listed under `[tool.check-manifest]` in
`pyproject.toml`.

Run a subset of the unit tests by passing pytest arguments after `--`:

```bash
tox -e unit -- pylxd/models/tests/test_project.py -k test_get
```

## Tests

### Unit tests

- Subclass `pylxd.tests.testing.PyLXDTestCase`. It mocks HTTP with `requests-mock`,
  loads `mock_lxd.RULES`, and provides `self.client`.
- Never contact a real LXD daemon from a unit test.
- Add shared responses to `RULES` in `pylxd/tests/mock_lxd.py`. Override a response
  for a single test with `self.add_rule({...})`.
- The mock server advertises no API extensions. Enable them per test with
  `testing.add_api_extension_helper(self, ["extension_name"])`.
- Assert on what was sent with `self.last_matching_request(method, url)`.
- Mark lines that genuinely cannot be tested with `# pragma: no cover` and say why.

### Integration tests

- Subclass `integration.testing.IntegrationTestCase` and register cleanups with
  `self.addCleanup(...)` for everything the test creates.
- Do not run `integration/run-integration-tests` or `tox -e integration` on a
  machine whose LXD matters. They install packages with `sudo`, change the LXD
  server configuration (`core.https_address`, trust store, default storage pool),
  and create and delete real resources.
- The safe local option is `tox -e integration-in-lxd`. It needs a working local LXD
  that allows nesting, launches ephemeral containers, and runs the suite inside them.
- CI runs the suite against LXD `4.0`, `5.0`, `5.21`, and `6` with Python 3.10, 3.12,
  and 3.14 (`.github/workflows/tests.yml`).
- If you cannot run the integration tests, say so in the pull request. Do not report
  checks you did not run as passing.

## Key conventions

### Compatibility

- One pylxd release must work with every LXD version in the CI matrix. Do not call
  an endpoint or send a field that only newer servers understand without a gate.
- Gate on API extensions, never on the server version string:
  - `client.assert_has_api_extension("name")` when the feature cannot work without
    it. It raises `LXDAPIExtensionNotAvailable`.
  - `if client.has_api_extension("name"):` when there is a fallback.
- LXD is the source of truth. Endpoints, methods, and field names come from
  [`doc/rest-api.yaml`](https://github.com/canonical/lxd/blob/main/doc/rest-api.yaml);
  extension names come from
  [`doc/api-extensions.md`](https://github.com/canonical/lxd/blob/main/doc/api-extensions.md).
  Do not invent either.
- Unit-test both sides of a gate: extension present and extension absent.
- A field the server returns but the model does not declare triggers an "unknown
  attribute" warning. Declare it with `model.Attribute(...)`. Use `optional=True`
  when older LXD versions do not return it and `readonly=True` when the server
  rejects changes to it.
- Keep the public API backward compatible. Do not rename or remove public methods
  or parameters; add new parameters with defaults. To retire something, emit a
  `DeprecationWarning` first.
- Supported Python starts at 3.10. Do not use newer syntax or standard library APIs.

### Python style

- Black, isort (`profile = "black"`), and flake8 settle formatting; do not hand-tune
  it. Do not add `# noqa` or `# type: ignore` without a comment explaining why.
- Reach the API through `client.api...`; do not build URLs by hand.
- Raise exceptions from `pylxd/exceptions.py`, not bare `Exception`.
- Operations that LXD runs asynchronously take `wait=False` and, when `wait` is
  true, block with `client.operations.wait_for_operation(...)`.
- Public methods get docstrings in the Sphinx field style used across the codebase
  (`:param name:`, `:type name:`, `:returns:`, `:raises:`); `doc/source/api.rst`
  renders them with autodoc.
- Add type hints to new code where they are cheap; `tox -e check` must stay clean.
- New modules carry the Apache 2.0 header used by neighboring files.
- Do not add a runtime dependency without maintainer agreement in an issue first.

### Commit format

Format: `<area>: <short description>`. The area is the path of the changed file or
package without its extension. The description is lowercase and imperative.

| Area | Example commit message |
|------|------------------------|
| `pylxd/models/<module>` | `pylxd/models/image: add return type hint for create` |
| `pylxd/models/tests/<module>` | `pylxd/models/tests/test_storage: assert that volume delete worked` |
| `pylxd/tests` | `pylxd/tests/testing: add docstrings` |
| `integration/` | `integration/testing: explain why NotFound is ignored` |
| `doc/source/<page>` | `doc/source/contributing: fix typo` |
| `.github/` | `github: update tags pattern in release workflow` |
| `pyproject.toml` | `pyproject: tweak default PYLXD_WARNINGS value` |

Keep commits small and logical: code, tests, and documentation changes are easier to
review as separate commits than as one large one.

All commits must be signed off (`git commit -s`). `Signed-off-by` is a Developer
Certificate of Origin (DCO) certification, a legal assertion that the submitter wrote
the code or has the right to submit it. Only a human can make that certification. AI
agents must not add a `Signed-off-by` line; prepare the commit message and let the
human committer run `git commit -s`.

### Pull requests

- Features and non-trivial fixes need a GitHub issue first so the proposal can be
  discussed before the work starts.
- A mergeable pull request has: signed-off commits, unit tests for the change, no
  drop in coverage, integration tests when behavior against a real server changes,
  and updated pages under `doc/source/` when the public API changes.
- First-time contributors add themselves to `CONTRIBUTORS.rst`. That entry names the
  human, not the tool.
- Do not bump the version in `pyproject.toml` or touch `.github/workflows/release.yml`;
  releases are cut by maintainers.
- Keep the diff focused. Do not reformat or refactor code unrelated to the change.
