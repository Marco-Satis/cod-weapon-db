#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schema-Validierung aller Daten-Files im Repo gegen schema/weapon.schema.json.

Standalone-Pruefung (unabhaengig von build.py): laeuft ueber alle bereits
gebauten data/weapons/*.json (und, falls vorhanden, data/meta/*.json soweit
sie dem Waffen-Schema folgen) und meldet jede Schema-Verletzung mit Pfad.

Exit 0 = alles gruen, Exit 1 = mindestens eine Verletzung (CI/Preflight-tauglich).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SCHEMA = REPO_ROOT / "schema" / "weapon.schema.json"
DEFAULT_DATA = REPO_ROOT / "data" / "weapons"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("validate")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_dir(data_dir: Path, validator: Draft202012Validator) -> tuple[int, int]:
    """Validiert alle *.json in data_dir. Returns (ok, bad)."""
    if not data_dir.is_dir():
        log.warning("Verzeichnis fehlt (uebersprungen): %s", data_dir)
        return 0, 0

    files = sorted(data_dir.glob("*.json"))
    ok = 0
    bad = 0
    for path in files:
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            log.error("%s: nicht lesbar/parsebar (%s)", path.name, exc)
            bad += 1
            continue
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            bad += 1
            for err in errors:
                loc = "/".join(str(p) for p in err.path) or "<root>"
                log.error("%s: %s -> %s", path.name, loc, err.message)
        else:
            ok += 1
    return ok, bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="jsonschema-Check aller data/*.json gegen schema/.")
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help=f"Schema (default: {DEFAULT_SCHEMA})")
    ap.add_argument("--data", type=Path, action="append",
                    help=f"Daten-Verzeichnis(se) (default: {DEFAULT_DATA})")
    args = ap.parse_args(argv)

    schema = load_json(args.schema)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    data_dirs = args.data or [DEFAULT_DATA]
    total_ok = 0
    total_bad = 0
    for d in data_dirs:
        ok, bad = validate_dir(d, validator)
        log.info("%s: %d gueltig, %d ungueltig", d, ok, bad)
        total_ok += ok
        total_bad += bad

    log.info("Validierung gesamt: %d gueltig, %d ungueltig", total_ok, total_bad)
    if total_ok == 0 and total_bad == 0:
        log.error("Keine Daten-Files gefunden -> erst build.py laufen lassen.")
        return 1
    return 0 if total_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
