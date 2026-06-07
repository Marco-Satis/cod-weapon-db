#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Einordnungs-Korrektur: game-Tag gegen TGD (authoritative) angleichen.

Hintergrund: die kuratierten `game`-Tags der Alt-Daten hatten 40 Mismatches
gegen die TGD-Quelle (REV-46-Lehre: nicht raten, gegen Quelle pruefen). Web-
Stichproben (Coda 9=BO7, Merrick 556=BO6, Jager 45=BO7, 556 Icarus/Cronen
Squall=MW2, Renetti=MW3) bestaetigten in jedem klaren Fall TGD. Daher: game
deterministisch aus TGD setzen. Legacy-Integration (HDR: MW2019-Origin, in
BO6-S3 integriert) wird per Note dokumentiert.

Patch ueber Staging (cod_db_deltas_v2), damit die bereits angereicherten Felder
(meta_build, not_buildable, zoom_x, dedup/cleanup) erhalten bleiben. `--dry-run`
listet alle Aenderungen.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STAGING = PROJECT_ROOT / "cod_db_deltas_v2"
RAW = STAGING / "_raw" / "wz3_base.json"

# class-Korrekturen (Web-verifiziert) + Taxonomie-Vereinheitlichung.
CLASS_FIX = {
    "coda-9": "Pistol",            # BO7-Pistole, nicht SMG
    "rk-9": "SMG",                 # 3-Round-Burst-SMG (callofduty.com /smg/rk-9), nicht Pistol
    "abr-a1": "AR",               # Steyr AUG 3-Burst-AR, nicht Marksman
    "kar98k": "Marksman Rifle",    # vereinheitlicht (war 'Marksman/Sniper')
}

# Note-Korrekturen: alte Substrings mit falschem game-/class-Claim ersetzen.
NOTE_SUBST = {
    "coda-9": ("Off-Meta BO6 SMG", "Off-Meta BO7 Pistol (vollauto)"),
    "jager-45": ("Off-Meta BO6 Pistol", "Off-Meta BO7 Pistol"),
    "merrick-556": ("BO7-native AR (5.56, 732 RPM).", "BO6 AR (5.56, 732 RPM, Season-6-BP)."),
    "rk-9": ("Off-Meta BO7 Pistol", "Off-Meta BO7 SMG (3-Round-Burst)"),
    "abr-a1": ("Off-Meta BO6 Marksman (2x)", "Off-Meta BO6 AR (3-Round-Burst AUG, 2x)"),
}
# Note-Anhang fuer Legacy-Integration (Origin != TGD-game).
NOTE_APPEND = {
    "hdr": " Origin: Modern Warfare 2019; in BO6 Season 3 (free) integriert -> TGD-game=bo6.",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw = json.loads(RAW.read_text(encoding="utf-8"))
    tgd_game = {norm(r["gun"]): r.get("game") for r in raw}

    changes = []
    for f in sorted(STAGING.glob("*.json")):
        w = json.loads(f.read_text(encoding="utf-8"))
        wid = w["id"]
        dirty = False

        tg = tgd_game.get(norm(w["name"]))
        if tg and w.get("game") != tg:
            changes.append((wid, "game", w.get("game"), tg))
            w["game"] = tg
            dirty = True

        if wid in CLASS_FIX and w.get("class") != CLASS_FIX[wid]:
            changes.append((wid, "class", w.get("class"), CLASS_FIX[wid]))
            w["class"] = CLASS_FIX[wid]
            dirty = True

        if wid in NOTE_SUBST:
            old_s, new_s = NOTE_SUBST[wid]
            if old_s in w.get("note", ""):
                w["note"] = w["note"].replace(old_s, new_s)
                changes.append((wid, "note", old_s, new_s))
                dirty = True

        if wid in NOTE_APPEND and NOTE_APPEND[wid].strip() not in w.get("note", ""):
            w["note"] = w.get("note", "") + NOTE_APPEND[wid]
            changes.append((wid, "note+", "", NOTE_APPEND[wid].strip()))
            dirty = True

        if dirty and not args.dry_run:
            tmp = f.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(w, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(f)

    game_n = sum(1 for c in changes if c[1] == "game")
    print(f"{'DRY-RUN' if args.dry_run else 'APPLIED'}: {len(changes)} Aenderungen ({game_n} game-Tags).")
    for wid, field, old, new in changes:
        print(f"  {wid:16} {field:6} {old!r} -> {new!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
