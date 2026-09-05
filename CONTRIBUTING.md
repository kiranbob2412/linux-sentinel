# Contributing

1. Keep collectors read-only and bounded by a timeout.
2. Keep policy decisions in pure check functions.
3. Add tests for normal, warning, critical, and unknown paths where relevant.
4. Keep output stable: check IDs and JSON field names are public interfaces.
5. Run `make test` and `make lint` before opening a pull request.

Please explain the Linux concepts involved in a change. This repository is
intended to be useful as both an operations tool and a learning project.