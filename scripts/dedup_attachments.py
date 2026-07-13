#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Intra-Slot-Dedup von codmunity-Typo-Duplikat-Attachments (p-2c9864d4ae).

Root-Cause: der codmunity-Mapper legt pro Aufsatz zwei Slot-Eintraege an, weil
`attachmentStats` (Stat-Delta-Tabelle: Name teils vertippt/abgeschnitten, MIT `mods`)
und `attachments[]` (In-Game-Aufsatzliste: kanonischer Name, OHNE `mods`) nur per
EXAKTEM Namen dedupliziert werden. Bei Tippfehlern (`13" Taryos`/`13" Tarvos`,
`MFS Carrousel`/`MFS Carousel`, `9mm Parabellum Overpressu`/`... Overpressured`,
`Grlp`/`Grip`, `Voltve`/`Votive`) matcht exact-dedup nicht -> zwei Eintraege.

Die Herausforderung: naives difflib>0.9 wuerde LEGITIME Varianten falsch mergen
(`10`/`13 Round Mag`, `Extended Mag I`/`II`/`III`, `Suppressor S`/`L`/`XL`,
`.40 Cal`/`.45 Cal`, `7.62x51mm`/`x39mm`). Diese sind KEINE Typos.

Ground-Truth-Fix: `attachments[]` = In-Game-Aufsatzliste (kanonisch). Distinkte
Varianten stehen BEIDE drin -> beide kanonisch -> werden NIE zusammengefaltet.
Ein Typo (nur in der Stat-Tabelle) steht NICHT in `attachments[]` -> wird in den
best-passenden kanonischen Nachbarn (difflib>0.9) gefaltet, dessen Name bleibt,
seine `mods` kommen aus der Stat-Variante. Nichts geht verloren.

Zwei Passes pro Slot:
  1) COLLAPSE-Merge: Eintraege mit identischem alnum-Rumpf (Case/Space/Punkt/
     Encoding) zusammenfuehren. Immer safe, auch ohne Netz.
  2) TYPO-Fold: Nicht-kanonische Eintraege in ihren kanonischen difflib-Nachbarn
     falten; Light-Tier-Guard blockt reine Groessen-/Tier-Token (\\d+, roman,
     S/L/XL) als differenzierendes Token. Nur wenn `attachments[]` abrufbar war.

Ohne Netz (404/Fetch-Fehler) laeuft nur Pass 1 -> keine Korruption, nur weniger
Bereinigung. Nur INTRA-Slot. Default Dry-Run; `--apply` schreibt mit Backup.
Quelle = Source-of-Truth `cod_db_deltas_v2/`; danach `promote_v2.py` +
`consolidate.py` laufen lassen (regeneriert data/weapons/ + db.json).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from difflib import SequenceMatcher
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPO_ROOT.parent
DEFAULT_DIR = PROJECT_ROOT / "cod_db_deltas_v2"

THRESHOLD = 0.9
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://codmunity.gg/"}
GAME_PATH = {"bo7": "bo7", "bo6": "bo6", "mw3": "mw3", "mw2": "mw2",
             "mw2019": "mw2019", "mw2019_mw3": "mw3", "warzone": "bo7", "unknown": "bo7"}
SLUG_OVERRIDE = {
    "velox-5-7": "velox-57", "krs-7-62": "krs-762", "flatline-mk2": "flatline-mkii",
    "mk-78": "mk78", "razer-9mm": "razor-9mm",
}
_NAME_KEYS = ("bo7", "bo6", "mw3", "mw2", "mw2019", "warzone", "warzone-2")
# reine Groessen-/Tier-Marker: als differenzierendes Token = distinkte Variante, kein Typo
PURE_TIER_RE = re.compile(r"^(\d+|[ivx]+|xs|s|m|l|xl|xxl|sx)$")


def norm(s: str) -> str:
    """space-erhaltend: lower, typografische Quotes/Zoll raus, Satzzeichen -> space, collapse."""
    if not s:
        return ""
    s = s.lower().replace("’", "'").replace("”", '"').replace("″", '"')
    s = re.sub(r'["\'.,()]', " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def collapse(s: str) -> str:
    """nur alnum, lower -> Rumpf fuer Case/Space/Punkt/Encoding-Vergleich."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def mod_count(e: dict) -> int:
    m = e.get("mods")
    return len(m) if isinstance(m, dict) else 0


def att_name(a: dict):
    """Aufsatz-Name aus attachments[]-Entry. BO6/BO7: 'Attachmentname'; MW: Spiel-Code-Key."""
    if a.get("Attachmentname"):
        return a["Attachmentname"]
    for k in _NAME_KEYS:
        v = a.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def fetch(game_path: str, wid: str) -> dict:
    slug = SLUG_OVERRIDE.get(wid, wid)
    url = f"https://api.codmunity.gg/website/pages/weapon/{game_path}/{slug}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def build_canon(data: dict) -> dict:
    """slot_upper -> set(collapse(name)) aller In-Game-Aufsaetze (attachments[])."""
    out: dict = {}
    for a in data.get("attachments", []) or []:
        slot = (a.get("Slot") or "").upper().strip()
        nm = att_name(a)
        if slot and nm:
            out.setdefault(slot, set()).add(collapse(nm))
    return out


def light_tier_guard(a: str, b: str) -> bool:
    """True = Fold BLOCKEN. Unterschiedliche Token-Zahl (Basis vs Suffix-Tier) oder
    ein differenzierendes reines Groessen-/Tier-Token (\\d+/roman/S-L-XL)."""
    ta, tb = norm(a).split(), norm(b).split()
    if len(ta) != len(tb):
        return True
    diffs = [(x, y) for x, y in zip(ta, tb) if x != y]
    if not diffs:
        return False
    return any(PURE_TIER_RE.match(x) or PURE_TIER_RE.match(y) for x, y in diffs)


def reorder(e: dict) -> dict:
    if not (isinstance(e, dict) and "name" in e):
        return e
    out = {"name": e["name"]}
    if e.get("unlock_level") is not None:
        out["unlock_level"] = e["unlock_level"]
    if isinstance(e.get("mods"), dict) and e["mods"]:
        out["mods"] = e["mods"]
    for k, v in e.items():
        if k not in out:
            out[k] = v
    return out


def build_merged(members: list[dict], cset: set) -> dict:
    """Kanon-Name = Member in cset (sonst wenigste mods / laengster Name); mods ver-unionen."""
    def rank(m: dict):
        inc = 0 if collapse(m.get("name", "")) in cset else 1
        n = norm(m.get("name", ""))
        return (inc, mod_count(m), -len(n), n)
    canon = min(members, key=rank)
    entry = {"name": canon["name"]}
    ul = canon.get("unlock_level")
    if ul is None:
        for m in members:
            if m.get("unlock_level") is not None:
                ul = m["unlock_level"]
                break
    if ul is not None:
        entry["unlock_level"] = ul
    mods: dict = {}
    for m in sorted(members, key=mod_count, reverse=True):
        md = m.get("mods")
        if isinstance(md, dict):
            for k, v in md.items():
                mods.setdefault(k, v)
    if mods:
        entry["mods"] = mods
    for m in [canon] + [x for x in members if x is not canon]:
        for k, v in m.items():
            if k not in entry and k not in ("name", "unlock_level", "mods"):
                entry[k] = v
    return entry


def fold_into(target: dict, orphan: dict) -> None:
    md = orphan.get("mods")
    if isinstance(md, dict):
        tm = target.setdefault("mods", {})
        for k, v in md.items():
            tm.setdefault(k, v)
    if target.get("unlock_level") is None and orphan.get("unlock_level") is not None:
        target["unlock_level"] = orphan["unlock_level"]
    for k, v in orphan.items():
        if k not in ("name", "unlock_level", "mods") and k not in target:
            target[k] = v


def dedup_slot(entries: list, cset: set) -> tuple[list, list]:
    reports: list = []

    # --- Pass 1: Collapse-Merge (Case/Space/Punkt/Encoding) ---
    groups: dict = OrderedDict()
    for i, e in enumerate(entries):
        key = ("c", collapse(e["name"])) if isinstance(e, dict) and "name" in e else ("raw", i)
        groups.setdefault(key, []).append(i)
    stage1: list = []
    for key, idxs in groups.items():
        if key[0] == "raw" or len(idxs) == 1:
            stage1.append(entries[idxs[0]])
            continue
        members = [entries[i] for i in idxs]
        merged = build_merged(members, cset)
        absorbed = [m["name"] for m in members if m["name"] != merged["name"]]
        if absorbed:
            reports.append(("format", merged["name"], absorbed, []))
        stage1.append(merged)

    # --- Pass 2: Typo-Fold in kanonische attachments[]-Nachbarn (nur mit Ground-Truth) ---
    if cset:
        canon_pos = [i for i, e in enumerate(stage1)
                     if isinstance(e, dict) and "name" in e and collapse(e["name"]) in cset]
        canon_norm = [norm(stage1[i]["name"]) for i in canon_pos]
        drop = set()
        for i, e in enumerate(stage1):
            if not (isinstance(e, dict) and "name" in e):
                continue
            if collapse(e["name"]) in cset or not canon_pos:
                continue
            ne = norm(e["name"])
            best_pos, best_r = None, 0.0
            for cp, cn in zip(canon_pos, canon_norm):
                r = SequenceMatcher(None, ne, cn).ratio()
                if r > best_r:
                    best_r, best_pos = r, cp
            if best_pos is not None and best_r > THRESHOLD \
                    and not light_tier_guard(e["name"], stage1[best_pos]["name"]):
                fold_into(stage1[best_pos], e)
                drop.add(i)
                reports.append(("typo", stage1[best_pos]["name"], [e["name"]], [round(best_r, 3)]))
        stage1 = [e for i, e in enumerate(stage1) if i not in drop]

    stage1 = [reorder(e) for e in stage1]
    return stage1, reports


def process_weapon(w: dict, sleep: float) -> tuple[bool, list]:
    slots = w.get("slots")
    if not isinstance(slots, dict) or not slots:
        return False, []
    cset_all: dict = {}
    gp = GAME_PATH.get(w.get("game"), "bo7")
    try:
        data = fetch(gp, w.get("id", ""))
        cset_all = build_canon(data)
        time.sleep(sleep)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        cset_all = {}  # Fallback: nur Pass 1 (Collapse)
    changed = False
    report: list = []
    for slot, entries in slots.items():
        if slot == "_universal" or not isinstance(entries, list) or len(entries) < 2:
            continue
        cset = cset_all.get(slot.upper().strip(), set())
        new_entries, merges = dedup_slot(entries, cset)
        if merges:
            slots[slot] = new_entries
            changed = True
            for kind, keep, absorbed, ratios in merges:
                report.append((slot, kind, keep, absorbed, ratios))
    return changed, report


def atomic_write(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(DEFAULT_DIR))
    ap.add_argument("--apply", action="store_true", help="Schreiben (sonst Dry-Run)")
    ap.add_argument("--only", help="nur diese comma-getrennten ids")
    ap.add_argument("--sleep", type=float, default=0.15)
    args = ap.parse_args()

    src = Path(args.dir)
    files = sorted(src.glob("*.json"))
    if args.only:
        want = set(args.only.split(","))
        files = [f for f in files if f.stem in want]

    if args.apply:
        backup = src.parent / f"deltas_backup_dedup_{int(time.time())}"
        shutil.copytree(src, backup)
        print(f"Backup -> {backup}")

    n_weapons = n_format = n_typo = 0
    for f in files:
        w = json.loads(f.read_text(encoding="utf-8"))
        changed, report = process_weapon(w, args.sleep)
        if not report:
            continue
        n_weapons += 1
        for slot, kind, keep, absorbed, ratios in report:
            if kind == "format":
                n_format += len(absorbed)
            else:
                n_typo += len(absorbed)
            tag = "FMT " if kind == "format" else "TYPO"
            rs = f" r={ratios}" if ratios else ""
            print(f"{w.get('id', f.stem):<22}[{slot}] {tag} keep {keep!r} <- {absorbed}{rs}")
        if args.apply and changed:
            atomic_write(f, w)

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"\n== {mode}: {n_weapons} Waffen, {n_format} Format-Dupes + {n_typo} Typo-Dupes "
          f"entfernt, threshold={THRESHOLD} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
