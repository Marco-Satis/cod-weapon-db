#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Konsolidierung: data/weapons/*.json + L3-Drumherum -> Single-File-Artefakte.

Laeuft NACH build.py. Erzeugt drei reproduzierbare Artefakte im Repo:

1. data/meta/<category>.json   -- L3-Drumherum-Files (Camos, Loadouts, Endgame,
   ...) read-only aus cod_db_drumherum_json/ uebernommen (Atomic-Write).
2. data/index.json             -- leichter Katalog: pro Waffe {id,name,class,
   game,in_warzone,base_only}, plus Aggregat-Counts (class/game) und Meta-Liste.
3. data/db.json                -- vollstaendige Single-File-DB: {meta, counts,
   weapons{id->full}, drumherum{category->full}} fuer 1-File-Konsum (Discord-Bot).

Quellen sind read-only; geschrieben wird ausschliesslich in cod_db_repo/data/.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPO_ROOT.parent
WEAPONS_DIR = REPO_ROOT / "data" / "weapons"
META_OUT = REPO_ROOT / "data" / "meta"
DRUMHERUM_SRC = PROJECT_ROOT / "cod_db_drumherum_json"
INDEX_OUT = REPO_ROOT / "data" / "index.json"
DB_OUT = REPO_ROOT / "data" / "db.json"

DATA_VERSION = "S3.5_2026-04-25"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("consolidate")


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def atomic_write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    tmp.replace(path)


def main() -> int:
    weapons: dict[str, dict] = {}
    for p in sorted(WEAPONS_DIR.glob("*.json")):
        w = load(p)
        weapons[w["id"]] = w

    # --- Aggregat-Counts ----------------------------------------------------
    by_class: dict[str, int] = {}
    by_game: dict[str, int] = {}
    base_only = 0
    for w in weapons.values():
        by_class[w["class"]] = by_class.get(w["class"], 0) + 1
        by_game[w["game"]] = by_game.get(w["game"], 0) + 1
        if not w.get("slots") or set(w.get("slots", {})) <= {"_universal"}:
            base_only += 1

    # --- L3-Drumherum -> data/meta/ + Sammlung ------------------------------
    drumherum: dict[str, dict] = {}
    if DRUMHERUM_SRC.is_dir():
        for p in sorted(DRUMHERUM_SRC.glob("*.json")):
            d = load(p)
            cat = d.get("category", p.stem)
            drumherum[cat] = d
            atomic_write(META_OUT / f"{p.stem}.json", d)
    else:
        log.warning("Drumherum-Quelle fehlt (uebersprungen): %s", DRUMHERUM_SRC)

    # --- index.json ---------------------------------------------------------
    catalog = [
        {
            "id": w["id"], "name": w["name"], "class": w["class"],
            "game": w["game"], "in_warzone": w.get("in_warzone", True),
            "base_only": (not w.get("slots") or set(w.get("slots", {})) <= {"_universal"}),
        }
        for w in sorted(weapons.values(), key=lambda x: x["id"])
    ]
    index = {
        "title": "CoD Weapon DB — Katalog",
        "data_version": DATA_VERSION,
        "source": "truegamedata",
        "weapon_count": len(weapons),
        "base_only_count": base_only,
        "counts_by_class": dict(sorted(by_class.items())),
        "counts_by_game": dict(sorted(by_game.items())),
        "meta_categories": sorted(drumherum.keys()),
        "weapons": catalog,
    }
    atomic_write(INDEX_OUT, index)

    # --- db.json (Single-File) ---------------------------------------------
    db = {
        "title": "CoD Weapon DB — Single-File",
        "data_version": DATA_VERSION,
        "source": "truegamedata",
        "license": "CC-BY-4.0",
        "weapon_count": len(weapons),
        "counts_by_class": dict(sorted(by_class.items())),
        "counts_by_game": dict(sorted(by_game.items())),
        "weapons": {wid: weapons[wid] for wid in sorted(weapons)},
        "drumherum": dict(sorted(drumherum.items())),
    }
    atomic_write(DB_OUT, db)

    log.info("Konsolidiert: %d Waffen (%d base-only), %d Meta-Kategorien.",
             len(weapons), base_only, len(drumherum))
    log.info("Klassen: %s", index["counts_by_class"])
    log.info("Games:   %s", index["counts_by_game"])
    log.info("-> %s, %s, data/meta/", INDEX_OUT.name, DB_OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
