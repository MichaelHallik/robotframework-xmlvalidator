# Performance benchmarks

This folder contains a small benchmark harness for measuring
`robotframework-xmlvalidator` under heavier XML/XSD workloads.

The benchmark suite intentionally separates:

- committed benchmark code and scenario definitions;
- generated XML/XSD fixtures;
- generated benchmark results.

Generated fixtures and results are ignored by Git:

```text
benchmarks/_data/
benchmarks/results/
```

## Install benchmark dependencies

`pyperf` is included as a development dependency.

```bash
poetry install --with dev
```

## Generate fixtures

```bash
poetry run python benchmarks/generate_fixtures.py
```

By default, fixtures are generated from:

```text
benchmarks/scenarios.json
```

## Run benchmarks

Quick smoke run:

```bash
poetry run python benchmarks/run_benchmarks.py --generate --fast
```

Write pyperf JSON results:

```bash
poetry run python benchmarks/run_benchmarks.py --generate --fast -o benchmarks/results/current.json
```

Run a single scenario:

```bash
poetry run python benchmarks/run_benchmarks.py --generate --scenario many-small-valid-namespace --fast
```

By default, the benchmark runner suppresses XmlValidator's Robot
Framework logger calls. This keeps benchmark output readable and avoids
measuring console/log overhead unless requested explicitly.

To include library logging overhead:

```bash
poetry run python benchmarks/run_benchmarks.py --scenario many-small-valid-namespace --include-library-logs --fast
```

Use pyperf's built-in memory tracking where supported:

```bash
poetry run python benchmarks/run_benchmarks.py --generate --scenario few-large-valid-single-schema --track-memory --fast
```

## Compare benchmark results

After collecting two pyperf JSON files:

```bash
poetry run python -m pyperf compare_to benchmarks/results/before.json benchmarks/results/after.json
```

## Scenario dimensions

The default scenarios cover:

- many small XML files;
- a few larger XML files;
- valid files;
- invalid files with few errors;
- invalid files with many errors;
- namespace-based schema matching;
- filename-based schema matching;
- `pre_parse=True` and `pre_parse=False`.

The default fixture sizes are intentionally moderate. For enterprise
stress testing, increase `xml_files` and/or `records_per_file` in
`benchmarks/scenarios.json`.
