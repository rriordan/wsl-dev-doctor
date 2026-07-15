# Security policy

## Data handling

`wsl-dev-doctor` is designed for local, read-only diagnostics.

- It does not modify system configuration.
- It never prints environment-variable values.
- It records only environment-variable names in reports.
- It does not read shell history, SSH keys, cloud credentials, `.env` files, or Docker configuration.

Review a generated report before sharing it. System and tool version strings can still reveal operational details.

## Reporting a vulnerability

Do not open a public issue for a suspected security vulnerability. Contact the repository owner privately once this project is published.
