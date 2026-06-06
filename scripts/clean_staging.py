#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Staging-Cleanup VOR Promote: dedup + scoped OCR-Garbage-Drop.

Zwei Quell-Daten-Defekte aus den TGD-Rohdaten (NICHT unser Rebuild-Bug):

1. **Doubling** — einige (meist S4-Neu-)Waffen listen Aufsaetze ~2x (zwei
   OCR-Paesse). Exakte Namens-Dubletten je Slot werden per normalisiertem Namen
   entfernt (keep-first = sauberer erster Pass). Idempotent.

2. **OCR-Garbage** — bei 2 S4-Neu-Waffen (rev-46, ds20-mirage) hat TGD den
   STOCK-Slot nicht sauber OCR't; das `attachment`-Feld enthaelt Buchstaben-Salat
   ("Lenteteistee ETo? VEVTiSt"). Unbrauchbar -> verworfen.

Garbage-Erkennung ist BEWUSST eng gehalten (CoD-Namen haben legitime
vokalfreie Model-Tokens "VLK 4.0", "CHF", camelCase "MicroFlex" -> eine globale
Heuristik wuerde reale Namen zerstoeren):
  - universal: Namen mit '?' (kein realer CoD-Aufsatz hat ein Fragezeichen).
  - scoped: NUR in den 2 bekannt-korrupten Slots wird ein Eintrag verworfen,
    wenn sein Name KEIN Slot-Vokabel-Wort enthaelt UND global auf <2 Waffen
    vorkommt. Reale Eintraege ("Full Stock", "MFS Reforge Flip Stock") bleiben.

`--dry-run` listet jeden geplanten Drop ohne zu schreiben.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STAGING = PROJECT_ROOT / "cod_db_deltas_v2"

# (weapon-id, slot) Paare mit nachweislich korruptem OCR (manuell verifiziert).
CORRUPT_SCOPE = {("rev-46", "STOCK"), ("ds20-mirage", "STOCK")}
# Vokabel die einen STOCK-Namen als real ausweist (Case-insensitive Teilstring).
SLOT_VOCAB = {"stock", "akimbo", "pad", "brace", "buffer", "folding", "fixed", "full"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def has_vocab(name: str) -> bool:
    low = name.lower()
    return any(v in low for v in SLOT_VOCAB)


def build_freq(files: list[Path]) -> dict[str, int]:
    """Normalisierter Name -> Anzahl verschiedener Waffen (global)."""
    weapons_per_name: dict[str, set] = defaultdict(set)
    for f in files:
        w = json.loads(f.read_text(encoding="utf-8"))
        slots = w.get("slots")
        if not isinstance(slots, dict):
            continue
        for entries in slots.values():
            for e in entries:
                weapons_per_name[norm(e.get("name", ""))].add(w["id"])
    return {k: len(v) for k, v in weapons_per_name.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(STAGING.glob("*.json"))
    freq = build_freq(files)

    drops: list = []
    changed = 0
    for f in files:
        w = json.loads(f.read_text(encoding="utf-8"))
        slots = w.get("slots")
        if not isinstance(slots, dict) or not slots:
            continue
        wid = w["id"]
        new_slots = {}
        before = sum(len(v) for v in slots.values())
        for slot, entries in slots.items():
            seen = set()
            kept = []
            for e in entries:
                nm = e.get("name", "")
                if "?" in nm:
                    drops.append((wid, slot, "qmark", nm))
                    continue
                if (wid, slot) in CORRUPT_SCOPE and not has_vocab(nm) and freq.get(norm(nm), 0) < 2:
                    drops.append((wid, slot, "garbage", nm))
                    continue
                nn = norm(nm)
                if nn in seen:
                    drops.append((wid, slot, "dup", nm))
                    continue
                seen.add(nn)
                kept.append(e)
            if kept:
                new_slots[slot] = kept
        after = sum(len(v) for v in new_slots.values())
        if after != before:
            changed += 1
            if not args.dry_run:
                w["slots"] = new_slots
                tmp = f.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(w, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                tmp.replace(f)

    kinds: dict[str, int] = defaultdict(int)
    for _, _, kind, _ in drops:
        kinds[kind] += 1
    print(f"{'DRY-RUN' if args.dry_run else 'APPLIED'}: {changed} Waffen geaendert | "
          f"dups={kinds['dup']} garbage={kinds['garbage']} qmark={kinds['qmark']}")
    print("--- Drops (weapon | slot | kind | name) ---")
    for wid, slot, kind, nm in drops:
        print(f"  {wid} | {slot} | {kind} | {nm!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
