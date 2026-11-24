# Concept Hub Conceptual Model

Divinari separates **language-independent semantic concepts** (`concept_key`, e.g., `GREETING_MORNING`, `NOUN_HOME`) from **language-specific lexical realizations** (`sense_key`, `term`, `register`, `pronunciation`).

## Design Principles

- **Clean Public Identifiers Only:** Public JSON datasets use human-readable uppercase `concept_key` and lowercase `sense_key` strings rather than internal relational database primary keys.
- **One Concept, Distinct Senses:** Polysemous headwords remain isolated in separate sense objects so learners and cross-language mappers never conflate unrelated meanings.
- **Character-Exact Example Spans:** Example sentence `tokens` reference `[char_start, char_end)` offsets verified strictly against `sentence_text[char_start:char_end] == surface`.
