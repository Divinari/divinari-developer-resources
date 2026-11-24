# Community Pull Request Workflow

1. Author JSON resources matching `schemas/*.schema.json` using UTF-8 NFC + LF line endings.
2. Validate locally using `divinari_validate.py`.
3. Sign commits with `git commit -s` (DCO 1.1) and submit PR for Language Lead + Maintainer review.
4. Merged resources are released openly under `CC BY 4.0` and queued for manual maintainer evaluation into future app builds.
