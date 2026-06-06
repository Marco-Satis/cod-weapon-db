#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Promote v2-Staging -> publiziertes data/weapons/ (validate + normalize).

Ersetzt das v1-build.py fuer das Rich-Format (full-stat aus TGD-API):
  Quelle:  cod_db_deltas_v2/<id>.json   (read-only Staging)
  Schema:  schema/weapon.v2.schema.json (Draft 2020-12)
  Ziel:    data/weapons/<id>.json       (publiziert, ueberschrieben)

Unterschied zu build.py: v2-Feld-/Base-Reihenfolge, akzeptiert damage/slots-als-
Objekt-von-Arrays/meta_build/blocking. Bei Schema-Fehler wird die Waffe NICHT
geschrieben und Exit-Code != 0.

_raw/ wird ignoriert (Rohdaten, keine Waffen-Files).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPO_ROOT.parent
SRC = PROJECT_ROOT / "cod_db_deltas_v2"
OUT = REPO_ROOT / "data" / "weapons"
SCHEMA = REPO_ROOT / "schema" / "weapon.v2.schema.json"

FIELD_ORDER = [
    "id", "name", "name_de", "class", "game", "weapon_type", "in_warzone",
    "source", "data_version", "unlock_level", "note", "not_buildable",
    "fire_modes", "base", "damage", "slots", "meta_build", "blocking",
]
BASE_ORDER = [
    "rpm", "alt_rpm", "mag", "reload_s", "ads_ms", "sprint_to_fire_ms",
    "velocity_ms", "move_speed", "crouch_move_speed", "ads_move_speed",
    "sprint_speed", "swap_speed", "gun_kick", "vert_recoil", "horiz_recoil",
    "idle_sway", "hipfire_max", "flinch_resistance", "target_flinch",
    "tac_spread", "zoom_x", "obd",
]

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("promote_v2")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ordered(d: dict, order: list[str]) -> dict:
    out = {k: d[k] for k in order if k in d}
    for k in sorted(d):  # defensiv: unbekannte Felder ans Ende
        if k not in out:
            out[k] = d[k]
    return out


def normalize(w: dict) -> dict:
    out = ordered(w, FIELD_ORDER)
    if isinstance(out.get("base"), dict):
        out["base"] = ordered(out["base"], BASE_ORDER)
    if isinstance(out.get("slots"), dict):
        out["slots"] = {k: out["slots"][k] for k in sorted(out["slots"])}
    return out


def atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    schema = load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SRC.glob("*.json"))
    ok = bad = 0
    seen: dict[str, Path] = {}
    for path in files:
        try:
            w = load(path)
        except (OSError, json.JSONDecodeError) as exc:
            log.error("%s: nicht lesbar (%s)", path.name, exc)
            bad += 1
            continue
        errors = sorted(validator.iter_errors(w), key=lambda e: list(e.path))
        if errors:
            bad += 1
            for err in errors[:3]:
                loc = "/".join(str(p) for p in err.path) or "<root>"
                log.error("%s: %s -> %s", path.name, loc, err.message)
            continue
        wid = w["id"]
        if wid in seen:
            log.error("%s: doppelte id %r (zuerst %s)", path.name, wid, seen[wid].name)
            bad += 1
            continue
        seen[wid] = path
        atomic_write(OUT / f"{wid}.json", normalize(w))
        ok += 1
    log.info("Promote-v2: %d ok, %d fehlerhaft -> %s", ok, bad, OUT)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
