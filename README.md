# CoD Weapon DB

Strukturierte, versionierte **Call-of-Duty-Waffen-Datenbank** für Warzone (Cross-Game-Pool
MW2 → BO7). Pro Waffe: exakte Base-Stats + rohe Attachment-Slot-Deltas, plus Drumherum-Daten
(Camos, Loadouts, Endgame-Abilities, Prestige, MP/Zombies-Meta).

**191 Waffen** · Datenstand **S3.5 (2026-04-25)** · Quelle **TrueGameData** · Lizenz **CC-BY-4.0**

## Struktur

```
data/
  weapons/<id>.json   191 Waffen, 1 Datei/Waffe (kanonisch, schema-validiert)
  meta/<kategorie>.json  10 Drumherum-Kategorien (Camos, Loadouts, Endgame, ...)
  index.json          leichter Katalog (id/name/class/game) + Aggregat-Counts
  db.json             vollständige Single-File-DB (weapons + drumherum)
schema/
  weapon.schema.json  JSON-Schema (Draft 2020-12) für eine Waffe
scripts/
  build.py            cod_db_deltas/ -> data/weapons/ (validate + normalize)
  validate.py         standalone Schema-Check aller data/weapons/ (CI/Preflight)
  consolidate.py      data/weapons/ + meta -> index.json + db.json
```

## Waffen-Schema (Kurz)

| Feld | Typ | Beschreibung |
|---|---|---|
| `id` | string | Slug (`ak-74`, `9mm-daemon`) |
| `name` | string | Anzeigename |
| `class` | enum | AR / SMG / LMG / Sniper / Marksman Rifle / Battle Rifle / Pistol / Shotgun / … |
| `game` | enum | `mw2` / `mw3` / `bo6` / `bo7` / `mw2019` / … |
| `in_warzone` | bool | im WZ-Pool |
| `source` / `data_version` | string | Provenance + Datenstand |
| `base` | object | rpm, mag, reload_s, ads_ms, velocity_ms, move_ms, sprint_to_fire_ms, sprint_ms, [zoom_x] |
| `slots` | object | Slot → Array roher Delta-Strings `"Name :: +X% Stat | -Y% Stat"` |
| `_universal` | string | Referenz auf den geteilten universellen Attachment-Pool |

**Extraktions-Konvention:** Off-Meta-Waffen erfassen nur **weapon-spezifische** Slots
(BARREL/MUZZLE/AMMUNITION/FIRE MODS/MAGAZINE/CONVERSION KIT/…); universelle Slots
(OPTIC/UNDERBARREL/STOCK/LASER/REAR GRIP) sind als `_universal`-Pool-Referenz hinterlegt
(identische Deltas, in den Meta-Files). `base-only` = TGD-S3.5 hatte keine Builder-Daten
(S4-Neuwaffe), nur Base-Stats erfasst.

## Nutzung

```python
import json
db = json.load(open("data/db.json", encoding="utf-8"))
ak = db["weapons"]["ak-74"]
print(ak["base"]["rpm"], ak["slots"]["BARREL"])
```

Bauen/Validieren (benötigt `jsonschema`):

```bash
python scripts/build.py        # deltas -> data/weapons/
python scripts/validate.py     # schema-check
python scripts/consolidate.py  # index.json + db.json + data/meta/
```

## Disclaimer

Nicht mit Activision/Treyarch affiliiert. Daten aus Community-Quellen (primär
[TrueGameData](https://truegamedata.com)) — als Referenz attribuiert, Stände versioniert.
Stats driften pro Season/Patch; `data_version` je Eintrag beachten (S3.5 ist ~1,5 Monate
hinter S4 — Aufsatz-%-Deltas meist stabil, Base-Werte ggf. abweichend).

Lizenz: [CC-BY-4.0](LICENSE).
