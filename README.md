<!-- Brand Tokens: Dark Teal #0A1A1D | Gold #FFD700 | Royal Purple #6A1B9A | Fonts: Poppins & Lora -->

# Divinari Developer Resources

**Where faith meets fluency.**  
*Learn languages. Discover heritage. Grow in faith.*

`divinari-developer-resources` publishes public Draft 2020-12 JSON Schemas, clean-room technical specifications, synthetic example fixtures, and a standalone Python 3 validation CLI for builders, researchers, and tooling authors working with Divinari's **public open data formats**.

> **Proprietary Application Notice:** Divinari (`https://divinari.app`) is a commercially operated, proprietary platform. This repository publishes **only** intentionally supported open-data specifications and validation tooling. It contains **no** Flutter application source code, backend APIs, encryption/signing formats or keys, Firebase config, AI tutoring prompts, or subscription logic.

---

## Contents

- `schemas/` — JSON Schema (Draft 2020-12) definitions for `language-metadata`, `lexicon-entry`, `example-sentence`, `writing-system`, `curriculum-unit`, `heritage-contribution`, and `scripture-bundle`
- `specifications/` — Clean-room conceptual models (`concept-hub-model`, `[0.0, 1.0]` vector strokes, CEFR/ACTFL alignment, and contribution/provenance envelopes)
- `validator/` — Zero-credential Python 3 CLI validator (`divinari_validate.py`) and `pytest` suite (`validator/tests/`)
- `examples/` — 100% synthetic valid and negative test fixtures
- `bundle-formats/`, `integration-guides/`, `documentation/`, and `api-documentation/` — Public contribution package formats, SemVer policy, and API scope boundaries

---

## Quick Start

```bash
python3 -m pip install -r validator/requirements.txt
python3 validator/divinari_validate.py --schema schemas/lexicon-entry.schema.json examples/valid-lexicon-tl.json
pytest -q validator/tests/
```

---

## Licensing, Contributions & Security

- Code, schemas, specifications, and tooling: **Apache License, Version 2.0** ([LICENSE](./LICENSE), [NOTICE](./NOTICE)).
- All contributions require **Developer Certificate of Origin (DCO 1.1)** sign-off (`git commit -s`; see [CONTRIBUTING.md](./CONTRIBUTING.md)) and adhere to [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
- Trademarks and Hummingbird marks remain **All Rights Reserved** ([TRADEMARK.md](./TRADEMARK.md)).
- Vulnerability reporting: [SECURITY.md](./SECURITY.md).
