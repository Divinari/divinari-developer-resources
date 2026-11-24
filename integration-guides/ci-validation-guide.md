# Running CI Validation Locally & in GitHub Actions

```bash
python3 validator/divinari_validate.py --schema schemas/lexicon-entry.schema.json examples/valid-lexicon-tl.json
```

All checks enforce read-only CI tokens (`permissions: contents: read`) with full 40-character pinned Action commit SHAs.
