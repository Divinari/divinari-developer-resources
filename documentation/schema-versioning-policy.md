# Schema Versioning Policy

Public JSON Schemas follow Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR (`X.0.0`):** Breaking schema changes (renaming/removing properties or tightening enums on existing valid files).
- **MINOR (`1.X.0`):** Backward-compatible optional fields or expanded enum options.
- **PATCH (`1.0.X`):** Clarifications to descriptions, error documentation, or validator bug fixes.
