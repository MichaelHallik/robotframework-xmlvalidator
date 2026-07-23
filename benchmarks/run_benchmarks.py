"""
Runs scenario-based performance benchmarks with pyperf.

The benchmarks call the public ``XmlValidator`` Python API directly.
They are macro benchmarks: each measured function validates a complete
scenario folder rather than a tiny isolated function.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
from functools import partial
from pathlib import Path
from typing import Any, Protocol, cast
from unittest.mock import patch

import pyperf
from generate_fixtures import (
    DEFAULT_DATA_DIR,
    DEFAULT_SCENARIOS,
    generate_all_fixtures,
    load_scenarios,
)

from xmlvalidator import XmlValidator


class BenchmarkArgs(Protocol):
    """
    Parsed command-line arguments used by the benchmark runner.
    """

    scenarios: Path
    data_dir: Path
    scenario: list[str] | None
    generate: bool
    force_generate: bool
    list: bool
    include_library_logs: bool


def add_worker_args(cmd: list[str], args: argparse.Namespace) -> None:
    """
    Adds custom benchmark arguments to pyperf worker commands.
    """
    benchmark_args = cast(BenchmarkArgs, args)
    cmd.extend(["--scenarios", str(benchmark_args.scenarios)])
    cmd.extend(["--data-dir", str(benchmark_args.data_dir)])
    for scenario_id in benchmark_args.scenario or []:
        cmd.extend(["--scenario", scenario_id])
    if benchmark_args.include_library_logs:
        cmd.append("--include-library-logs")


def run_validation_scenario(
    scenario: dict[str, Any],
    data_dir: Path,
    suppress_library_logs: bool = True
) -> tuple[int, str | None]:
    """
    Runs one validation scenario and returns collected result metadata.
    """
    scenario_dir = data_dir / str(scenario["id"])
    xml_dir = scenario_dir / "xml"
    xsd_dir = scenario_dir / "xsd"
    matching = scenario["matching"]

    if matching == "single_schema":
        xsd_path: str | Path | None = xsd_dir / "schema.xsd"
        xsd_search_strategy = None
    elif matching == "namespace":
        xsd_path = xsd_dir
        xsd_search_strategy = "by_namespace"
    elif matching == "filename":
        xsd_path = xsd_dir
        xsd_search_strategy = "by_file_name"
    else:
        raise ValueError(f"Unsupported matching mode: {matching!r}.")

    with suppress_robot_logger(suppress_library_logs):
        validator = XmlValidator(fail_on_errors=False)
        errors, csv_path = validator.validate_xml_files(
            xml_dir,
            xsd_path=xsd_path,
            xsd_search_strategy=xsd_search_strategy,
            pre_parse=bool(scenario["pre_parse"]),
            write_to_csv=False,
            error_table=False,
            fail_on_errors=False,
            reset_errors=True
        )
    return len(errors), csv_path


def select_scenarios(
    scenarios: list[dict[str, Any]],
    selected_ids: list[str] | None
) -> list[dict[str, Any]]:
    """
    Filters scenarios by id, preserving scenario-file order.
    """
    if not selected_ids:
        return scenarios
    selected = set(selected_ids)
    filtered = [
        scenario
        for scenario in scenarios
        if scenario["id"] in selected
    ]
    missing = selected - {scenario["id"] for scenario in filtered}
    if missing:
        raise ValueError(f"Unknown benchmark scenario(s): {sorted(missing)}")
    return filtered


def build_arg_parser() -> argparse.ArgumentParser:
    """
    Builds the command-line parser used by pyperf.
    """
    parser = argparse.ArgumentParser(
        description="Run robotframework-xmlvalidator performance benchmarks."
    )
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=DEFAULT_SCENARIOS,
        help="Path to the benchmark scenario JSON file."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing generated benchmark fixtures."
    )
    parser.add_argument(
        "--scenario",
        action="append",
        help="Scenario id to run. Can be passed more than once."
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate missing fixtures before running benchmarks."
    )
    parser.add_argument(
        "--force-generate",
        action="store_true",
        help="Regenerate fixtures before running benchmarks."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit."
    )
    parser.add_argument(
        "--include-library-logs",
        action="store_true",
        help=(
            "Do not suppress XmlValidator logging during benchmarks. "
            "Use this only when measuring logging overhead explicitly."
        )
    )
    return parser


@contextlib.contextmanager
def suppress_robot_logger(enabled: bool):
    """
    Suppresses Robot Framework logger calls during benchmark timing.

    Logging can dominate high-volume benchmark output. By default, the
    benchmark measures validation work without console/log emission.
    Pass ``--include-library-logs`` to include logging overhead.
    """
    if not enabled:
        yield
        return

    module_names = [
        "xmlvalidator.XmlValidator",
        "xmlvalidator.files",
        "xmlvalidator.namespaces",
        "xmlvalidator.results",
        "xmlvalidator.schema.manager",
        "xmlvalidator.schema.resolver",
        "xmlvalidator.validation",
    ]
    with contextlib.ExitStack() as stack:
        for module_name in module_names:
            module = importlib.import_module(module_name)
            if not hasattr(module, "logger"):
                continue
            for method_name in ("info", "warn", "warning", "error", "console"):
                if hasattr(module.logger, method_name):
                    stack.enter_context(
                        patch.object(
                            module.logger,
                            method_name,
                            lambda *_, **__: None
                        )
                    )
        yield


def main() -> None:
    """
    CLI entry point.
    """
    runner = pyperf.Runner(
        _argparser=build_arg_parser(),
        add_cmdline_args=add_worker_args
    )
    runner.parse_args()
    if runner.args is None:
        raise RuntimeError("pyperf did not parse benchmark arguments.")
    args = cast(BenchmarkArgs, runner.args)
    scenarios = load_scenarios(args.scenarios)
    scenarios = select_scenarios(scenarios, args.scenario)

    if args.list:
        for scenario in scenarios:
            print(f"{scenario['id']}: {scenario['description']}")
        return

    if args.generate or args.force_generate:
        generate_all_fixtures(
            scenarios,
            args.data_dir,
            force=args.force_generate
        )

    for scenario in scenarios:
        scenario_id = scenario["id"]
        benchmark = partial(
            run_validation_scenario,
            scenario,
            args.data_dir,
            suppress_library_logs=not args.include_library_logs
        )
        runner.bench_func(f"validate:{scenario_id}", benchmark)


if __name__ == "__main__":
    main()
