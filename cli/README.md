### Boilerplate: `cli/README.md`


# CLI Dashboard

## Commands
- `list-prs`: List recent analyzed PRs
- `show-pr <id>`: Show details and comments
- `recheck-pr <id>`: Trigger re-review

## Examples
```bash
python cli.py list-prs --limit 10
python cli.py show-pr 42