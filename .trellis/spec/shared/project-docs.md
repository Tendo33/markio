# Project Docs

Public docs remain useful facts and should not be deleted during Trellis migration.

- `README.md` / `README.zh.md`: product overview and setup
- `docs/cli_usage*.md`: CLI usage
- `docs/sdk_usage*.md`: SDK usage
- `docs/console_frontend*.md`: Vue console behavior
- `docs/REDIS_INTEGRATION.md`: Redis task/cache integration
- `docs/biological_data_parsing*.md`: FASTA and GenBank parser behavior
- `tests/README.md`: test structure

When code changes conflict with docs, update the public docs and `.trellis/spec/` together.
