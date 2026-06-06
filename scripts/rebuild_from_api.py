#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild aller Waffen aus den TGD-Backend-API-Rohdaten (voll-stat).

Quelle (read-only):
  cod_db_deltas_v2/_raw/wz3_base.json              (212 Records, alle Base-Stats)
  cod_db_deltas_v2/_raw/wz3_attach_blocking.json   ([attachments[], blocking[]])

Bestehende cod_db_repo/data/weapons/*.json liefern die kuratierten Identitaets-
Felder (id, name, name_de, class, game, in_warzone, note) die in der API fehlen.
Join per normalisiertem Namen (191/191 verifiziert).

Output (Staging, NICHT publiziertes data/ ueberschreiben):
  cod_db_deltas_v2/<id>.json   -- voll-stat, strukturierte Mods, alle Slots inline.

Erweitertes Ziel (Marco 2026-06-06): saemtliche Werte speichern fuer spaetere
Build-Optimierung -> kein Slot-Allowlist-Filter, alle Stat-Mods je Attachment,
Schadenstabelle (simple_damage) + Fire-Modes geparst.
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPO_ROOT.parent
RAW = PROJECT_ROOT / "cod_db_deltas_v2" / "_raw"
WEAPONS_IN = REPO_ROOT / "data" / "weapons"
OUT = PROJECT_ROOT / "cod_db_deltas_v2"
DATA_VERSION = "S3.5_2026-04-25"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("rebuild")

# Base-Feld-Mapping TGD -> unser Schema (transparente Namen, Rohwerte beibehalten).
BASE_MAP = {
    "rpm": "rpm", "alt_rpm": "alt_rpm", "mag_size": "mag", "reload": "reload_s",
    "ads": "ads_ms", "stf": "sprint_to_fire_ms", "bv": "velocity_ms",
    "movement": "move_speed", "crouch_movement": "crouch_move_speed",
    "ads_movement": "ads_move_speed", "sprint": "sprint_speed",
    "swap_speed": "swap_speed", "gun_kick": "gun_kick", "vert_recoil": "vert_recoil",
    "horiz_recoil": "horiz_recoil", "idle_sway": "idle_sway", "hipfire_max": "hipfire_max",
    "flinch_resistance": "flinch_resistance", "target_flinch": "target_flinch",
    "tac_spread": "tac_spread", "zoom1": "zoom_x", "obd": "obd",
}
MOD_FIELDS = [
    "ads_mod", "gun_kick_mod", "vert_recoil_mod", "horiz_recoil_mod",
    "ads_movement_mod", "hipfire_max_mod", "range_mod", "idle_sway_mod",
    "stf_mod", "bv_mod", "crouch_movement_mod", "movement_mod", "sprint_mod",
    "reload_mod", "flinch_resistance_mod", "rpm_mod", "target_flinch_mod",
    "swap_speed_mod", "fire_mode_mod",
]
SLOT_FIX = {"UDERBARREL": "UNDERBARREL", "COMB": "COMB", "slot": None}  # TGD-OCR-Typos


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def load(p: Path):
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def parse_json_field(val):
    """fire_modes / simple_damage liegen als JSON-String vor."""
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val
    return None


def build_base(rec: dict) -> dict:
    out = {}
    for tgd_key, our_key in BASE_MAP.items():
        v = rec.get(tgd_key)
        if v not in (None, "", "null"):
            out[our_key] = v
    return out


def build_slots(rows: list[dict]) -> dict:
    slots: dict[str, list] = defaultdict(list)
    for r in rows:
        slot = r.get("slot")
        slot = SLOT_FIX.get(slot, slot)
        if not slot:
            continue
        name = r.get("attachment") or r.get("ocr_attachment")
        if not name:
            continue
        mods = {k: r[k] for k in MOD_FIELDS if k in r and r[k] not in (None, "", 1, "1")}
        entry = {"name": name}
        if mods:
            entry["mods"] = mods
        slots[slot].append(entry)
    return dict(slots)


def main() -> int:
    base = load(RAW / "wz3_base.json")
    att_blk = load(RAW / "wz3_attach_blocking.json")
    attachments = att_blk[0] if isinstance(att_blk, list) else att_blk
    blocking = att_blk[1] if isinstance(att_blk, list) and len(att_blk) > 1 else []

    base_by_name = {norm(r["gun"]): r for r in base}
    att_by_name: dict[str, list] = defaultdict(list)
    for r in attachments:
        att_by_name[norm(r["gun"])].append(r)
    blk_by_name: dict[str, list] = defaultdict(list)
    for b in blocking:
        key = norm(b.get("gun", "")) if isinstance(b, dict) else ""
        if key:
            blk_by_name[key].append(b)

    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    missing = []
    for f in sorted(WEAPONS_IN.glob("*.json")):
        old = load(f)
        nk = norm(old["name"])
        rec = base_by_name.get(nk)
        if not rec:
            missing.append(old["name"])
            continue

        new = {
            "id": old["id"],
            "name": old["name"],
        }
        if old.get("name_de"):
            new["name_de"] = old["name_de"]
        new["class"] = old.get("class")
        # game aus TGD (authoritative); old nur Fallback. Kuratierte Tags hatten
        # 40 Mismatches gegen die Quelle (Web-verifiziert: TGD korrekt).
        new["game"] = rec.get("game") or old.get("game")
        new["weapon_type"] = rec.get("weapon_type")
        new["in_warzone"] = old.get("in_warzone", True)
        new["source"] = "truegamedata-api"
        new["data_version"] = DATA_VERSION
        if rec.get("unlock_level") not in (None, "", 0):
            new["unlock_level"] = rec.get("unlock_level")
        if old.get("note"):
            new["note"] = old["note"]

        fm = parse_json_field(rec.get("fire_modes"))
        if fm:
            new["fire_modes"] = fm
        new["base"] = build_base(rec)
        dmg = parse_json_field(rec.get("simple_damage"))
        if dmg:
            new["damage"] = dmg
        new["slots"] = build_slots(att_by_name.get(nk, []))
        blk = blk_by_name.get(nk)
        if blk:
            new["blocking"] = blk

        with (OUT / f"{old['id']}.json").open("w", encoding="utf-8") as fh:
            json.dump(new, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        ok += 1

    log.info("Rebuild: %d Waffen geschrieben -> %s", ok, OUT)
    if missing:
        log.warning("OHNE API-Match (%d): %s", len(missing), missing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
