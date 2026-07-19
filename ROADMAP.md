# Project roadmap

This document outlines planned features and/or ideas for the future development of the `robotframework-xmlvalidator` library.

This roadmap is aspirational and may evolve based on user feedback input and practical constraints.

Want to contribute or suggest a feature? Feel free to open an issue or join the discussion.

## In progress / near-term

- Currently none.

## Planned / future

### Functional

- Support for separate error facets for malformed XML errors vs. XSD violation errors.
- XSD 1.1 support using XMLSchema 1.1 features (e.g. assertions, conditional types).
- Export error details to more formats (e.g. JSON, XML).
- Explicit validation of XSD schemas using W3C meta-schema.
- Configurable ignored schema namespaces for dynamic XSD matching.
  - Add keywords to let users add or remove namespace URIs that should not participate in XML/XSD namespace matching.
  - Keep built-in infrastructure namespaces ignored by default.
- Flexible handling of wildcard elements (`<xs:any>`), with support for:
  - `strict`: must be validatable
  - `lax`: validate if possible
  - `skip`: accept without validation
- Optional CLI runner for validation outside of Robot Framework.
- Support for additional schema types (e.g., RelaxNG, Schematron).
- Built-in diffs between schema versions.

### Performance

The library is intended to be useful in enterprise-style XML validation contexts, where payloads may be large, schemas may be complex, and batch validation may involve many files.

We should investigate and benchmark performance on realistic XML/XSD workloads and address identified performance bottlenecks.

The following candidate performance enhancements should be evaluated with benchmarks before implementation.

- Cache compiled XSD schemas.
  - `xmlschema.XMLSchema(...)` compilation is likely one of the more expensive repeated operations.
  - Namespace-based schema matching currently loads candidate schemas while searching for matches.
  - A schema cache keyed by XSD path and `base_url` could avoid recompiling the same schema multiple times during batch validation.

- Pre-index schema metadata for dynamic namespace matching.
  - Instead of loading and checking every candidate XSD for every XML file, load each schema once and build an index of:
    - target namespace
    - imported namespaces
    - schema path
  - This could reduce namespace-based matching from repeated nested loops to faster dictionary/set lookups.

- Optimize filename-based schema matching.
  - Filename matching can pre-build a dictionary such as `{xsd_path.stem: xsd_path}`.
  - This avoids repeatedly looping over all XSD files for each XML file.

- Review the default `pre_parse=True` behavior.
  - Pre-parsing catches malformed XML/XSD issues early, but it may also parse files that will later be parsed again during schema validation.
  - A future option could avoid duplicate parsing where `xmlschema` already performs sufficient validation.
  - Any change must preserve current error reporting behavior.

- Benchmark nested namespace extraction.
  - `include_nested=True` walks the full XML tree via `element.iter(None)`.
  - This is safe and clear, but potentially expensive for large or deeply nested XML documents.
  - Possible optimizations include keeping nested extraction opt-in, stopping early when enough namespace information has been found, or using a streaming/event-based approach for namespace discovery.

- Consider streaming-based XML inspection for large files.
  - `lxml.etree.parse()` builds an in-memory tree.
  - For very large XML files, streaming approaches such as `iterparse()` may reduce memory pressure for namespace discovery or preliminary checks.
  - This needs careful design because full XSD validation still depends on the underlying validation engine.

- Avoid unnecessary file reads during sanity checks.
  - `sanity_check_files()` checks file existence, size, extension, and optionally parses files.
  - When the same files are later parsed or validated again, some work may be duplicated.
  - A future refactor could separate cheap filesystem checks from expensive parse checks more explicitly.

- Make detailed error processing lazy or configurable.
  - Collecting many error facets across many validation errors can become expensive.
  - The library could keep the default small facet set and document that larger facet sets may have performance costs.
  - Advanced modes could cap collected errors per file or allow fail-fast validation.

- Add an optional fail-fast / max-errors mode.
  - Current batch validation intentionally collects all errors.
  - For very large invalid files or CI smoke checks, users may prefer stopping after the first error or after a configured maximum number of errors.
  - This would be an opt-in behavior change only.

- Reduce logging overhead for large batches.
  - Per-file and per-error Robot Framework logging can become expensive when validating many files or collecting many errors.
  - A future verbosity setting could reduce console/log output while preserving structured result data.

- Optimize CSV and HTML error table generation.
  - `pandas` is convenient, but may be heavier than necessary for simple CSV writing and HTML table generation.
  - For large error reports, standard-library CSV writing and lighter HTML generation may reduce runtime and dependency weight.

- Consider parallel validation for independent files.
  - XML files in a batch are often independent and could theoretically be validated in parallel.
  - This is a larger design change because schema caching, Robot Framework logging, deterministic output ordering, and error aggregation would need careful handling.

- Add benchmark tests and performance regression checks.
  - Before optimizing, create representative benchmark fixtures:
    - small, medium, and large XML files
    - deeply nested XML files
    - many XML files with one schema
    - many XML files with many schemas
    - valid and heavily invalid XML files
  - Benchmark results should guide which optimizations are worth implementing.

## Open for discussion

- Currently none.

## Last updated

2026-07-19
