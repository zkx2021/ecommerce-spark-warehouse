# GitHub Workflow

Repository name: `ecommerce-spark-warehouse`

## Branches

- `main` is the main branch.
- Keep implementation commits small and aligned with project stages.

## Commit Pattern

- `chore: initialize project foundation`
- `feat: add crawler pipeline`
- `feat: add hive warehouse layers`
- `feat: add spark offline jobs`
- `feat: add fastapi dashboard api`
- `feat: add vue ecommerce dashboard`
- `docs: add deployment and warehouse documentation`
- `chore: verify docker compose deployment`

## Before Commit

Run:

```powershell
git status --short
```

Check that generated data, logs, secrets, local volumes, and `.env` files are not staged.
