# Third-party Python packages

This inventory covers NFR-004 for the Python packages the core installs at runtime. `uv.lock` pins each one by hash, and setup installs it from there, so none is copied into this package. Each package's own license file arrives with it. `scripts/build_third_party.py` writes this file, and the `catalog-license` lane fails if it differs from the lock.

Graphviz is a separate program that each machine installs, under the Eclipse Public License 1.0. It is not bundled either.

Icons delivered by `diagrams` and the assets bundled here are in [NOTICE.md](NOTICE.md).

| Package | Version | License |
|---|---|---|
| annotated-types | 0.8.0 | MIT |
| cfgv | 3.5.0 | MIT |
| diagrams | 0.25.1 | MIT |
| distlib | 0.4.4 | Python Software Foundation License |
| filelock | 4.2.6 | MIT |
| graphviz | 0.20.3 | MIT License |
| identify | 2.6.20 | MIT |
| jinja2 | 3.1.6 | BSD License |
| markupsafe | 3.0.4 | BSD-3-Clause |
| nodeenv | 1.12.0 | BSD License |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| platformdirs | 4.14.3 | MIT |
| pre-commit | 4.7.0 | MIT |
| pydantic | 2.14.2 | MIT |
| pydantic-core | 2.50.2 | MIT |
| python-discovery | 1.9.0 | MIT |
| pyyaml | 6.0.3 | MIT License |
| typing-extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.4 | MIT |
| virtualenv | 21.15.2 | MIT |
