#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build-Pipeline: cod_db_deltas/<id>.json -> data/weapons/<id>.json.

Merge der per-Waffe-Delta-Files (L1-Eigentum, nur lesen) in den
oeffentlichen data/weapons/-Tree des Repos. Pro Waffe wird:

1. geladen (UTF-8),
2. gegen schema/weapon.schema.json validiert (Draft 2020-12),
3. normalisiert (feste Feld-Reihenfolge, Slot-Keys sortiert),
4. pretty (indent=2, ensure_ascii=False) geschrieben.

Slot-Delta-Strings bleiben ROH (der spaetere Build-Parser strukturiert sie).
Bei Schema-Fehlern wird die Waffe NICHT geschrieben und der Exit-Code != 0.

PHASE 2 (nach L1-Abschluss): identischer Lauf gegen die vollen 194 Waffen
plus optionaler Meta-Merge aus cod_db_drumherum_json/ (L3) -> data/meta/.

Quelle ist read-only (Cross-Session-Write-Race-Vermeidung): dieses Script
schreibt ausschliesslich in data/weapons/, nie zurueck nach cod_db_deltas/.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

# --- Pfade (Repo-relativ, keine Annahmen ueber CWD) --------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent                      # cod_db_repo/
PROJECT_ROOT = REPO_ROOT.parent                    # CoD_Waffen_DB/
DEFAULT_SRC = PROJECT_ROOT / "cod_db_deltas"        # L1-Eigentum (read-only)
DEFAULT_OUT = REPO_ROOT / "data" / "weapons"
DEFAULT_SCHEMA = REPO_ROOT / "schema" / "weapon.schema.json"

# Feste Feld-Reihenfolge fuer normalisierte Ausgabe (On-Disk-Konvention).
FIELD_ORDER = [
    "id", "name", "name_de", "class", "game", "in_warzone",
    "source", "data_version", "note", "base_note", "extraction",
    "all_slots", "base", "slots", "_universal",
]
# base-Reihenfolge fix (CLAUDE.md): 8 Kern-Felder + optional zoom_x.
BASE_ORDER = [
    "rpm", "mag", "reload_s", "ads_ms", "velocity_ms",
    "move_ms", "sprint_to_fire_ms", "sprint_ms", "zoom_x",
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("build")


def load_json(path: Path) -> dict:
    """Laedt eine JSON-Datei als UTF-8."""
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def normalize(weapon: dict) -> dict:
    """Erzeugt ein deterministisch geordnetes Waffen-Dict.

    Slot-Strings bleiben unveraendert (roh). Nur Schluessel-Reihenfolge
    wird vereinheitlicht: bekannte Felder zuerst (FIELD_ORDER), unbekannte
    danach (sortiert, defensiv falls L1 neue Felder einfuehrt).
    """
    out: dict = {}
    for key in FIELD_ORDER:
        if key in weapon:
            out[key] = weapon[key]
    for key in sorted(weapon):                      # defensiv: unbekannte Felder
        if key not in out:
            out[key] = weapon[key]

    if isinstance(out.get("base"), dict):
        base = out["base"]
        out["base"] = {k: base[k] for k in BASE_ORDER if k in base}
        for k in sorted(base):                      # defensiv
            if k not in out["base"]:
                out["base"][k] = base[k]

    if isinstance(out.get("slots"), dict):
        slots = out["slots"]
        # _universal ans Ende, sonst alphabetisch fuer stabile Diffs.
        ordered = sorted(slots, key=lambda s: (s == "_universal", s))
        out["slots"] = {k: slots[k] for k in ordered}
    return out


def atomic_write(path: Path, data: dict) -> None:
    """Atomic-Write via .tmp + replace (kein halb-geschriebenes File)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    tmp.replace(path)


def build(src: Path, out: Path, schema_path: Path) -> int:
    """Validiert + normalisiert alle Waffen aus src nach out.

    Returns 0 bei Erfolg, sonst Anzahl fehlerhafter Dateien.
    """
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)       # Schema selbst pruefen
    validator = Draft202012Validator(schema)

    if not src.is_dir():
        log.error("Quell-Verzeichnis fehlt: %s", src)
        return 1
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(src.glob("*.json"))
    if not files:
        log.error("Keine *.json in %s", src)
        return 1

    ok = 0
    bad = 0
    seen_ids: dict[str, Path] = {}
    for path in files:
        try:
            weapon = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            log.error("%s: nicht lesbar/parsebar (%s)", path.name, exc)
            bad += 1
            continue

        errors = sorted(validator.iter_errors(weapon), key=lambda e: list(e.path))
        if errors:
            bad += 1
            for err in errors:
                loc = "/".join(str(p) for p in err.path) or "<root>"
                log.error("%s: %s -> %s", path.name, loc, err.message)
            continue

        wid = weapon["id"]
        if path.stem != wid:
            log.warning("%s: Dateiname != id (%r)", path.name, wid)
        if wid in seen_ids:
            log.error("%s: doppelte id %r (zuerst in %s)", path.name, wid, seen_ids[wid].name)
            bad += 1
            continue
        seen_ids[wid] = path

        atomic_write(out / f"{wid}.json", normalize(weapon))
        ok += 1

    log.info("Build fertig: %d ok, %d fehlerhaft -> %s", ok, bad, out)
    return bad


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Merge cod_db_deltas/ -> data/weapons/ (validate + normalize).")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC, help=f"Quell-Deltas (default: {DEFAULT_SRC})")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Ziel data/weapons (default: {DEFAULT_OUT})")
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help=f"Schema (default: {DEFAULT_SCHEMA})")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return 0 if build(args.src, args.out, args.schema) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
