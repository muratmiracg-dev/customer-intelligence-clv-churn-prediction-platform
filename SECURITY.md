# Security Policy

## Supported Version

The current `main` branch is the supported portfolio version.

## Reporting a Vulnerability

Do not create a public issue containing credentials, exploitable details or personal data. Contact the repository owner privately and include:

- the affected component;
- reproduction steps;
- potential impact;
- a proposed mitigation, when available.

## Security Controls

- No credentials are committed.
- `.env` files and local runtime state are ignored.
- API requests are schema-validated.
- Container execution uses a non-root application user.
- Dependencies are pinned in the project configuration.
- GitHub Actions runs linting, tests and coverage checks.
- The synthetic dataset contains no real PII.

