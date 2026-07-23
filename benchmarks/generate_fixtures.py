"""
Generates XML/XSD benchmark fixtures.

Generated files are written below ``benchmarks/_data`` by default and
are intentionally ignored by Git. The generated XML documents are simple
but exercise the same validation paths as real project usage:

- single shared schema validation;
- namespace-based XML-to-XSD matching;
- filename-based XML-to-XSD matching;
- valid and invalid XML content.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parent
DEFAULT_SCENARIOS = ROOT / "scenarios.json"
DEFAULT_DATA_DIR = ROOT / "_data"

MatchingMode = Literal["single_schema", "namespace", "filename"]
ValidityMode = Literal["valid", "few_errors", "many_errors"]


def load_scenarios(scenarios_path: Path) -> list[dict[str, Any]]:
    """
    Loads benchmark scenarios from JSON.
    """
    with scenarios_path.open(encoding="utf-8") as scenario_file:
        scenarios = json.load(scenario_file)
    if not isinstance(scenarios, list):
        raise ValueError("Scenario file must contain a JSON list.")
    return scenarios


def generate_all_fixtures(
    scenarios: list[dict[str, Any]],
    data_dir: Path,
    force: bool = False
) -> None:
    """
    Generates fixtures for all configured benchmark scenarios.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        generate_scenario_fixture(scenario, data_dir, force=force)


def generate_scenario_fixture(
    scenario: dict[str, Any],
    data_dir: Path,
    force: bool = False
) -> None:
    """
    Generates XML and XSD files for one benchmark scenario.
    """
    scenario_id = str(scenario["id"])
    scenario_dir = data_dir / scenario_id
    if scenario_dir.exists():
        if not force:
            return
        _safe_rmtree(scenario_dir, data_dir)
    xml_dir = scenario_dir / "xml"
    xsd_dir = scenario_dir / "xsd"
    xml_dir.mkdir(parents=True, exist_ok=True)
    xsd_dir.mkdir(parents=True, exist_ok=True)

    xml_files = int(scenario["xml_files"])
    records_per_file = int(scenario["records_per_file"])
    validity = scenario["validity"]
    matching = scenario["matching"]

    if matching == "single_schema":
        namespace = "http://example.com/benchmark/shared"
        _write_schema(xsd_dir / "schema.xsd", namespace)
        for index in range(xml_files):
            _write_xml(
                xml_dir / f"document_{index:05d}.xml",
                namespace,
                records_per_file,
                validity
            )
        return

    if matching == "namespace":
        namespaces = [
            "http://example.com/benchmark/a",
            "http://example.com/benchmark/b",
        ]
        for index, namespace in enumerate(namespaces):
            _write_schema(xsd_dir / f"schema_{index}.xsd", namespace)
        for index in range(xml_files):
            namespace = namespaces[index % len(namespaces)]
            _write_xml(
                xml_dir / f"document_{index:05d}.xml",
                namespace,
                records_per_file,
                validity
            )
        return

    if matching == "filename":
        namespace = "http://example.com/benchmark/filename"
        for index in range(xml_files):
            stem = f"document_{index:05d}"
            _write_schema(xsd_dir / f"{stem}.xsd", namespace)
            _write_xml(
                xml_dir / f"{stem}.xml",
                namespace,
                records_per_file,
                validity
            )
        return

    raise ValueError(f"Unsupported matching mode: {matching!r}.")


def _write_schema(path: Path, namespace: str) -> None:
    """
    Writes a compact schema used by benchmark XML documents.
    """
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    targetNamespace="{namespace}"
    xmlns="{namespace}"
    elementFormDefault="qualified">
    <xs:element name="records">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="record" maxOccurs="unbounded">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="id" type="xs:int"/>
                            <xs:element name="name" type="xs:string"/>
                            <xs:element name="amount" type="xs:decimal"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>
""",
        encoding="utf-8"
    )


def _write_xml(
    path: Path,
    namespace: str,
    records_per_file: int,
    validity: ValidityMode
) -> None:
    """
    Writes one benchmark XML file.
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<records xmlns="{namespace}">',
    ]
    for index in range(records_per_file):
        invalid_record = (
            validity == "many_errors"
            or (validity == "few_errors" and index == 0)
        )
        record_id = "not-an-int" if invalid_record else str(index)
        amount = "not-a-decimal" if invalid_record else f"{index}.25"
        lines.extend([
            "  <record>",
            f"    <id>{record_id}</id>",
            f"    <name>Record {index}</name>",
            f"    <amount>{amount}</amount>",
            "  </record>",
        ])
    lines.append("</records>")
    path.write_text("\n".join(lines), encoding="utf-8")


def _safe_rmtree(target: Path, data_dir: Path) -> None:
    """
    Removes a generated scenario directory after checking its location.
    """
    resolved_target = target.resolve()
    resolved_data_dir = data_dir.resolve()
    if resolved_data_dir not in resolved_target.parents:
        raise ValueError(f"Refusing to remove path outside data dir: {target}")
    shutil.rmtree(resolved_target)


def main() -> None:
    """
    CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description="Generate XML/XSD benchmark fixtures."
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
        help="Directory where generated fixtures are written."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate existing scenario fixture directories."
    )
    args = parser.parse_args()
    scenarios = load_scenarios(args.scenarios)
    generate_all_fixtures(scenarios, args.data_dir, force=args.force)
    print(f"Benchmark fixtures available in: {args.data_dir}")


if __name__ == "__main__":
    main()
