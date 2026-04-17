# pylxd Copilot Instructions

## Overview

pylxd is a Python library for interacting with the LXD REST API. It provides a high-level interface for managing LXD containers, images, networks, and other resources. The library is designed to be easy to use and integrates well with Python applications.

## Project Layout and Architecture

### Key Configuration Files

- **`pyproject.toml`** - Python project configuration: dependencies, tox environments, linting rules, and build settings
- **`.github/workflows/tests.yml`** - Main CI pipeline (lint, unit tests, integration matrix)
- **`doc/source/contributing.rst`** - Contribution guidelines, PR requirements, code standards, and release process
- **`integration/run-integration-tests`** - Shell script that configures LXD and runs `tox -e integration` (requires a running LXD daemon; not safe for local use)
- **`integration/run-integration-tests-in-lxd`** - Shell script that runs the integration test suite inside a nested LXD container (safe for local use — does not modify the host LXD setup)

### Code Architecture

pylxd is structured in three layers:

1. **`pylxd/client.py`** — `Client` is the sole public entry point. It connects to LXD via a Unix socket (default) or HTTPS, and wires up all resource managers. `_APINode` provides fluent tree traversal of the LXD REST API:

   ```python
   client = pylxd.Client()
   # Resolves to GET /1.0/instances/my-instance
   response = client.api.instances["my-instance"].get()
   ```

2. **`pylxd/managers.py`** — `BaseManager` subclasses (e.g. `InstanceManager`, `ImageManager`) proxy the class-level methods (`get`, `all`, `create`, `exists`) of each model. They are attached to `Client` as attributes (`client.instances`, `client.images`, etc.).

3. **`pylxd/models/`** — One file per LXD resource. All models inherit from `Model` (defined in `_model.py`), which uses `Attribute` descriptors to map JSON fields to Python attributes and drives `get`/`save`/`delete` operations. `instance.py` is the shared base class for `container.py` and `virtual_machine.py`.

`pylxd/exceptions.py` defines the custom exception hierarchy (`LXDAPIException`, `NotFound`, `Conflict`, `LXDAPIExtensionNotAvailable`, etc.).

### Package & Test Structure

```
pylxd/
  __init__.py             # Re-exports Client and EventType
  client.py               # Client, _APINode, transport adapters, EventType
  managers.py             # BaseManager + per-resource manager classes
  exceptions.py           # Custom exception hierarchy
  models/
    _model.py             # Model base class + Attribute descriptors
    instance.py           # Instance (base for Container and VirtualMachine)
    container.py          # Container subclass of Instance
    virtual_machine.py    # VirtualMachine subclass of Instance
    image.py
    network.py            # Network, NetworkForward, NetworkState
    storage_pool.py       # StoragePool, StorageVolume, StorageVolumeSnapshot
    profile.py
    project.py
    cluster.py            # Cluster, ClusterMember, ClusterCertificate
    certificate.py
    operation.py
    tests/                # Unit tests mirroring the models/ structure
      test_instance.py
      test_image.py
      test_network.py
      test_storage.py
      test_cluster.py
      test_cluster_member.py
      test_cluster_certificate.py
      test_certificate.py
      test_profile.py
      test_project.py
      test_operation.py
      test_model.py
  tests/
    mock_lxd.py           # Mock LXD HTTP server used by all unit tests
    test_client.py
    testing.py

integration/              # Integration tests (require a running LXD daemon)
  run-integration-tests           # Sets up LXD then calls tox -e integration
  run-integration-tests-in-lxd   # Launches an LXD container and runs the above inside it
  test_client.py
  test_instances.py
  test_containers.py
  test_images.py
  test_networks.py
  test_profiles.py
  test_projects.py
  test_storage.py
  test_cluster_members.py
```

## Continuous Integration

### GitHub Actions Workflows

The CI pipeline (`.github/workflows/tests.yml`) runs:

1. **Lint** (`ubuntu-slim`):
   - ShellCheck on `integration/run-integration-tests*` and any `*.sh` files
   - `tox -e lint` — Black + isort check + flake8
   - `tox -e check` — mypy type checking

2. **Unit Tests** (`ubuntu-slim`):
   - `tox -e unit` — pytest with `--doctest-modules`
   - `tox -e coverage` — pytest with `--cov=pylxd`
   - Codecov upload (on `main` branch only)

3. **Tests** (matrix):
   - **Python version**: 3.10, 3.12, 3.14
   - **LXD snap track / OS**:
     - `6/edge`, `5.21/edge`, `5.0/edge` on Ubuntu 24.04
     - `4.0/edge` on Ubuntu 22.04 (Python 3.10 only)
   - Sets up LXD via the `canonical/setup-lxd` action, then runs `integration/run-integration-tests`

## Development Guidelines

### Contributing Workflow

See `doc/source/contributing.rst`.

### Code Standards

pylxd formats code with **Black** and **isort**; linting uses **flake8** (config in `pyproject.toml` `[tool.flake8]`); type checking uses **mypy** (config in `[tool.mypy]`).

```bash
tox -e lint    # check formatting and linting
tox -e format  # auto-fix formatting with isort + Black
tox -e check   # mypy type check
```

### Test Recommendations

[`tox`](https://tox.wiki/) (≥ 4.21) is the project's test runner. All environments are defined in `pyproject.toml` under `[tool.tox]`. There is no separate `tox.ini`.

#### Setting up a development environment

The basic setup mirrors what CI does:

```bash
# Create and activate a virtual environment
python3 -m venv venv
. ./venv/bin/activate

# Install pip and tox
pip install --upgrade pip tox

# Run all CI checks at once
tox -e unit,coverage,lint,check
```

Additional optional commands for local development:

```bash
# Auto-fix formatting (not in CI; use before committing)
tox -e format

# Run integration tests inside ephemeral LXD containers (safe for local use)
# Launches one container per supported Ubuntu release (jammy, noble) and invokes
# integration/run-integration-tests inside each
tox -e integration-in-lxd

# Build Sphinx documentation (if docs were added/modified)
tox -e doc
```

#### Unit test guidelines

- Unit tests live in `pylxd/tests/` (client-level) and `pylxd/models/tests/` (model-level), mirroring the source layout.
- Always reuse `pylxd/tests/mock_lxd.py` — it provides a fake LXD HTTP server. Never call a real LXD daemon from unit tests.
- Coverage must not drop. Lines that are genuinely untestable should be excluded with `# NOQA`.

#### Integration tests

Integration tests live in `integration/` and require a running LXD daemon. To avoid modifying your local LXD setup, use `tox -e integration-in-lxd`, which launches one ephemeral LXD container per supported Ubuntu release (jammy and noble), copies the repository into each, and runs the tests inside.

### Release Process

See the "Releasing" section in `doc/source/contributing.rst` for complete release process details.
