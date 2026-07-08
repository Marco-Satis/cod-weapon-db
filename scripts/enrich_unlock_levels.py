#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aufsatz-Unlock-Level aus codmunity in die v2-Deltas eintragen.

Quelle:  codmunity-API `attachments[]` -> Feld 'Unlock Level' (int = Waffen-Level,
         ODER Text: 'Weapon Prestige' / 'Season 4 Battle Pass' / 'Weekly Challenge Reward').
Ziel:    cod_db_deltas_v2/<id>.json  -> pro slots[SLOT][i] ein neues Feld 'unlock_level'.

Matching (Slot-lokal): normalisierter Name gegen Attachmentname (spezifisch, BO7)
UND Label (generisch) — plus difflib-Fuzzy-Fallback fuer codmunity-Tippfehler
(Taryos<->Tarvos, Carrousel<->Carousel). Base-only-Stubs (keine attachments) bleiben
unveraendert. Atomic-Write (.tmp + os.replace), Backup der Deltas vor dem Lauf.

Attachment-Entry-Reihenfolge nach Enrichment: name -> unlock_level -> mods.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPO_ROOT.parent
DELTA = PROJECT_ROOT / "cod_db_deltas_v2"
BACKUP = PROJECT_ROOT / f"deltas_backup_unlock_{int(SCRIPT_DIR.stat().st_mtime)}"

UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://codmunity.gg/"}
GAME_PATH = {"bo7": "bo7", "bo6": "bo6", "mw3": "mw3", "mw2": "mw2",
             "mw2019": "mw2019", "mw2019_mw3": "mw3", "warzone": "bo7", "unknown": "bo7"}
SLUG_OVERRIDE = {
    "velox-5-7": "velox-57", "krs-7-62": "krs-762", "flatline-mk2": "flatline-mkii",
    "mk-78": "mk78", "razer-9mm": "razor-9mm",
}
FUZZY_CUTOFF = 0.86


def norm(s: str) -> str:
    """Name normalisieren: lower, typografische Quotes/Zoll-Marken raus, nur alnum+space."""
    if not s:
        return ""
    s = s.lower().replace("’", "'").replace("”", '"').replace("″", '"')
    s = re.sub(r'["\'.,()]', " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def fetch(game_path: str, wid: str) -> dict:
    slug = SLUG_OVERRIDE.get(wid, wid)
    url = f"https://api.codmunity.gg/website/pages/weapon/{game_path}/{slug}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


_NAME_KEYS = ("bo7", "bo6", "mw3", "mw2", "mw2019", "warzone", "warzone-2")


def att_name(a: dict):
    """Aufsatz-Name aus codmunity attachments[]-Entry. BO6/BO7: 'Attachmentname'.
    MW-Aera: Name liegt unter dem Spiel-Code-Key (z.B. 'mw2': 'FJX DIOD-70')."""
    if a.get("Attachmentname"):
        return a["Attachmentname"]
    for k in _NAME_KEYS:
        v = a.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def build_unlock_lookup(data: dict) -> dict:
    """slot_upper -> {'byname': {norm: ul}, 'bylabel': {norm: ul}, 'names': [(norm, ul)]}."""
    out: dict = {}
    for a in data.get("attachments", []) or []:
        slot = (a.get("Slot") or "").upper().strip()
        if not slot:
            continue
        ul = a.get("Unlock Level")
        if ul is None:
            continue
        name = att_name(a)
        label = a.get("Label")
        rec = out.setdefault(slot, {"byname": {}, "bylabel": {}, "names": []})
        if name:
            n = norm(name)
            rec["byname"][n] = ul
            rec["names"].append((n, ul))
        if label:
            rec["bylabel"].setdefault(norm(label), ul)
    return out


def lookup_ul(entry_name: str, rec: dict):
    """Unlock-Level fuer einen Slot-Eintrag; None wenn kein Treffer."""
    if not rec:
        return None
    n = norm(entry_name)
    if n in rec["byname"]:
        return rec["byname"][n]
    if n in rec["bylabel"]:
        return rec["bylabel"][n]
    cand = [nm for nm, _ in rec["names"]]
    hit = difflib.get_close_matches(n, cand, n=1, cutoff=FUZZY_CUTOFF)
    if hit:
        for nm, ul in rec["names"]:
            if nm == hit[0]:
                return ul
    return None


def reorder_entry(entry: dict, ul) -> dict:
    """name -> unlock_level -> mods -> Rest."""
    out = {"name": entry["name"]}
    if ul is not None:
        out["unlock_level"] = ul
    if "mods" in entry:
        out["mods"] = entry["mods"]
    for k, v in entry.items():
        if k not in out:
            out[k] = v
    return out


def atomic_write(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="nur diese comma-getrennten ids")
    ap.add_argument("--sleep", type=float, default=0.25)
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    files = sorted(DELTA.glob("*.json"))
    if args.only:
        want = set(args.only.split(","))
        files = [f for f in files if f.stem in want]

    if not args.no_backup and not BACKUP.exists():
        shutil.copytree(DELTA, BACKUP)
        print(f"Backup -> {BACKUP}")

    tot_slots_entries = matched = missed = 0
    weapons_enriched = weapons_skipped = weapons_404 = 0
    miss_samples: list[str] = []

    for f in files:
        w = json.loads(f.read_text(encoding="utf-8"))
        wid = w.get("id", f.stem)
        slots = w.get("slots") or {}
        if not slots:
            weapons_skipped += 1
            continue
        gp = GAME_PATH.get(w.get("game"), "bo7")
        try:
            data = fetch(gp, wid)
        except urllib.error.HTTPError as e:
            print(f"404/{e.code} {wid}: attachments nicht abrufbar -> unveraendert")
            weapons_404 += 1
            continue
        except Exception as e:
            print(f"ERR {wid}: {type(e).__name__} {str(e)[:60]} -> unveraendert")
            weapons_404 += 1
            continue

        lookup = build_unlock_lookup(data)
        w_matched = w_missed = 0
        for slot, entries in slots.items():
            if slot == "_universal" or not isinstance(entries, list):
                continue
            rec = lookup.get(slot.upper().strip())
            new_entries = []
            for entry in entries:
                if not isinstance(entry, dict) or "name" not in entry:
                    new_entries.append(entry)
                    continue
                tot_slots_entries += 1
                ul = lookup_ul(entry["name"], rec)
                if ul is not None:
                    matched += 1
                    w_matched += 1
                else:
                    missed += 1
                    w_missed += 1
                    if len(miss_samples) < 40:
                        miss_samples.append(f"{wid}[{slot}] {entry['name']!r}")
                new_entries.append(reorder_entry(entry, ul))
            slots[slot] = new_entries

        atomic_write(f, w)
        weapons_enriched += 1
        if args.only or w_missed:
            print(f"OK {wid}: matched={w_matched} missed={w_missed}")
        time.sleep(args.sleep)

    print("\n== ENRICH-SUMMARY ==")
    print(f"Waffen enriched={weapons_enriched} skipped(base-only)={weapons_skipped} 404/err={weapons_404}")
    print(f"Attachment-Entries total={tot_slots_entries} matched={matched} missed={missed} "
          f"({100*matched/max(tot_slots_entries,1):.1f}% match)")
    if miss_samples:
        print("Miss-Samples (max 40):")
        for m in miss_samples:
            print("  ", m)


if __name__ == "__main__":
    main()
