# Project roadmap

This document outlines planned features and/or ideas for the future development of the `robotframework-xmlvalidator` library.

This roadmap is aspirational and may evolve based on user feedback input and practical constraints.

---

## In progress / near-term

-

---

## Planned / future

-

---

## Community wishlist / open for discussion

-

---

## Ideas
- Support for separate error facets for malformed XML errors vs. XSD violation errors.
- XSD 1.1 support using XMLSchema 1.1 features (e.g., assertions, conditional types).
- Explicit validation of XSD schemas using W3C meta-schema.
- Flexible handling of wildcard elements (`<xs:any>`), with support for:
  - `strict`: must be validatable
  - `lax`: validate if possible
  - `skip`: accept without validation
- Support for additional schema types (e.g., RelaxNG, Schematron).
- Optional CLI runner for validation outside of Robot Framework.
- Export error details to more formats (e.g. JSON, XML).
- Enbed error collection as HTML tables in the log file (inline validation summaries).
- Built-in diffs between schema versions.
- GUI frontend for non-technical users.

---

Last updated: 2025-06-13

> Want to contribute or suggest a feature? Feel free to open an issue or join the discussion.