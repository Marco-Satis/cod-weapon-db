# CoD Weapon DB

Strukturierte, versionierte **Call-of-Duty-Waffen-Datenbank** für Warzone (Cross-Game-Pool
MW2 → BO7). Pro Waffe: **vollständiger Stat-Satz** (Base + Schadenstabelle) + strukturierte
Attachment-Slot-Deltas mit Stat-Multiplikatoren, plus Drumherum-Daten (Camos, Loadouts,
Calling Cards, Endgame-Abilities, Prestige, MP/Zombies-Meta).

**191 Waffen** · Datenstand **S3.5 (2026-04-25)** · Quelle **TrueGameData** (Backend-API) · Lizenz **CC-BY-4.0**

## Struktur

```
data/
  weapons/<id>.json      191 Waffen, 1 Datei/Waffe (kanonisch, v2-schema-validiert)
  meta/<kategorie>.json   10 Drumherum-Kategorien (Camos, Loadouts, Calling Cards, ...)
  index.json             leichter Katalog (id/name/class/game) + Aggregat-Counts
  db.json                vollständige Single-File-DB (weapons + drumherum)
schema/
  weapon.v2.schema.json  JSON-Schema (Draft 2020-12), kanonisch (Rich-Format)
  weapon.schema.json     Legacy v1-Schema (historisch)
scripts/
  rebuild_from_api.py    TGD-API-Rohdaten -> Staging (full-stat Rebuild)
  clean_staging.py       Dedup + OCR-Garbage-Drop vor Promote
  promote_v2.py          Staging -> data/weapons/ (v2-validate + normalize)
  build_calling_cards.py baut meta/calling_cards.json aus Recherche-Enumeration
  consolidate.py         data/weapons/ + meta -> index.json + db.json
```

## Waffen-Schema (Kurz)

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` / `name` | string | Slug (`ak-74`) + Anzeigename |
| `class` | string | AR / SMG / LMG / Sniper / Marksman Rifle / Battle Rifle / Pistol / … |
| `weapon_type` | enum | TGD-Klasse (AR/SMG/BR/LMG/MR/SR/Pistols/SG) |
| `game` | enum | `mw2` / `mw3` / `bo6` / `bo7` / `mw2019` / … |
| `in_warzone` | bool | im WZ-Pool |
| `source` / `data_version` | string | Provenance + Datenstand |
| `base` | object | ~18 Roh-Stats: rpm, mag, reload_s, ads_ms, velocity_ms, move_speed, gun_kick, vert/horiz_recoil, idle_sway, hipfire_max, flinch_resistance, … |
| `damage` | array | Schadenstabelle pro Range-Stufe (Körperzonen + dropoff + rpm) |
| `slots` | object | Slot → Array `{name, mods:{<stat>_mod: 1.14, …}}` (1.14 = +14 %) |
| `meta_build` | array | empfohlene Sekundärquellen-Builds (nur Namen) für Waffen ohne TGD-Builder-Daten |
| `not_buildable` | bool | keine echte baubare Waffe (z. B. Carry-Over-Artefakt) |

**Full-Stat-Rebuild:** Daten stammen aus den TGD-Backend-JSON-Endpoints (nicht mehr DOM-Scrape).
Alle Slots inline mit strukturierten Multiplikatoren — kein `_universal`-Pool mehr. `base-only`
= TGD-S3.5 ohne Builder-Daten (S4-Neuwaffe); für einige davon ist ein `meta_build` aus
Sekundärquellen (codmunity/warzoneloadout/wzhub) hinterlegt, klar getrennt von `slots`.

## Drumherum: Calling Cards

`meta/calling_cards.json` enumeriert **128 bedingungs-gated Cards** (92 Dark Ops + 22 Ranked +
8 Mastery + 4 Zombies-Milestone + 2 Event), jeweils mit Freischalt-Bedingung + Konfidenz +
Quellen. Battle-Pass/Store-Cards (reine Kosmetik) als Sammelkategorie. Quellen: detonated,
PCGamesN, Windows Central, Dexerto, Game8, GameRant u. a. (CoD-Fandom-Wiki als eine von mehreren).

## Nutzung

```python
import json
db = json.load(open("data/db.json", encoding="utf-8"))
ak = db["weapons"]["ak-74"]
print(ak["base"]["rpm"], ak["slots"]["BARREL"][0])      # Name + mods
print(db["drumherum"]["calling_cards"]["counts"])        # Card-Counts
```

Bauen/Validieren (benötigt `jsonschema`):

```bash
python scripts/promote_v2.py    # Staging -> data/weapons/ (v2-validate)
python scripts/consolidate.py   # index.json + db.json + data/meta/
```

## Disclaimer

Nicht mit Activision/Treyarch affiliiert. Daten aus Community-Quellen (primär
[TrueGameData](https://truegamedata.com)) — als Referenz attribuiert, Stände versioniert.
Stats driften pro Season/Patch; `data_version` je Eintrag beachten (S3.5 ist ~1,5 Monate
hinter S4 — Aufsatz-%-Deltas meist stabil, Base-Werte ggf. abweichend). Einzelne S4-Neuwaffen
haben unsaubere TGD-OCR-Slots (in `note` markiert).

Lizenz: [CC-BY-4.0](LICENSE).
