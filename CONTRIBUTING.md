# Contributing

This repository is primarily a professional portfolio project, but well-scoped improvements are welcome.

## Development Workflow

1. Create a feature branch from `main`.
2. Keep generated data deterministic by preserving the configured random seed.
3. Add or update tests for behavioral changes.
4. Run `make lint` and `make test`.
5. Regenerate analytical outputs when feature logic, model logic or source schemas change.
6. Explain business impact, validation evidence and any backward incompatibility in the pull request.

## Quality Expectations

- Do not commit real personal or confidential business data.
- Avoid target leakage and document every new predictive target.
- Prefer time-based validation for customer behavior models.
- Preserve customer-level keys and relational integrity.
- Do not weaken consent, fairness, drift or quality gates.
- Update model cards, data dictionaries and the changelog when relevant.

## Commit Style

Use concise imperative messages, for example:

- `Add campaign eligibility validation`
- `Improve CLV model comparison`
- `Document churn threshold governance`

