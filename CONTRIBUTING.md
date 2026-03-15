# Contributing to SYSWATCH PRO

Thank you for contributing.

SYSWATCH PRO is a modular security monitoring framework designed to detect
system anomalies, suspicious behavior, and potential intrusions.

## Development Guidelines

- Keep modules small and focused
- Follow Bash best practices
- Ensure scripts run without root unless required
- Avoid destructive commands

## Module Development

New modules should be placed inside:

modules/

Modules must:

- be executable
- not break existing scans
- return clear output
- log alerts where necessary

Example module structure:

modules/example_scan.sh

## Reporting Issues

Please open an issue if you discover:

- bugs
- false positives
- detection improvements
- performance issues

## Pull Requests

Pull requests should include:

- clear description
- tested functionality
- minimal changes per PR
