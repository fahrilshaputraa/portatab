"""PortaTap settings package.

Choose an environment module explicitly:

- ``config.settings.dev``  — local development (default for ``manage.py``)
- ``config.settings.test`` — test suite
- ``config.settings.prod`` — production

There is deliberately no importable ``config.settings`` module with defaults so a
deployment can never accidentally run with development settings.
"""
