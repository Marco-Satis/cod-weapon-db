#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roster-Einträge fuer Melee / Special / Launcher (TGD-untracked).

TGD liefert keine ballistischen Werte fuer diese 3 Kategorien -> beim API-Rebuild
fehlten sie komplett. Quelle: Roster-Recherche (callofduty.com offiziell + Fandom +
Game8/Dexerto/gamesatlas), Report:
  research/websuche_bo7_melee_special_launcher_roster_2026-06-07.md

Schreibt Staging-Files nach cod_db_deltas_v2/<id>.json (danach promote_v2 + consolidate).
Sparse base-Stats nur wo eine Quelle numerische Werte hatte; sonst base={}.
Qualitative Mechanik + Konfidenz im note-Feld. Keine Slots (keine Attachments getrackt).
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "cod_db_deltas_v2"
SRC = "callofduty.com + Fandom + Game8/Dexerto/gamesatlas (Roster-Recherche, non-TGD)"
DV = "S4_2026-06-07"

# (id, name, class, weapon_type, subclass, unlock, unlock_level|None, base, note)
ROWS = [
    # --- Melee ---
    ("knife", "Knife", "Melee", "Melee", "Knife", "Launch (Standard, Level 1)", 1, {},
     "Hoher Schaden, kurze Reichweite, schnelle Angriffsgeschwindigkeit. Max Weapon-Level 30."),
    ("flatline-mk2", "Flatline MK.II", "Melee", "Melee", "Blunt/Bat", "Launch (Level 49)", 49, {},
     "Hoher Schaden, moderate Angriffsgeschwindigkeit. Max Weapon-Level 30."),
    ("ballistic-knife", "Ballistic Knife", "Melee", "Melee", "Knife (Projektil)",
     "Season 1 - Weekly Challenge Week 1 (6 Challenges)", None, {"range_m": 1.5, "sprint_to_fire_ms": 225},
     "Projektil-Blade (retrievable). Max Weapon-Level 30."),
    ("h311-saw", "H311-SAW", "Melee", "Melee", "Saw/Blade",
     "Season 2 - Battle Pass Page 10 / Armory 250k XP", None, {},
     "Hoher Schaden, laengere Reichweite als Knife/Flatline, langsamer. Max Weapon-Level 30. [Unlock-Weg: Game8 nennt Armory 250k XP, andere Quelle Battle-Pass Page 10 - evtl. beides.]"),
    ("katana", "Katana", "Melee", "Melee", "Sword",
     "Season 3 - C.O.D.E. Navigator Event (7 Challenges, 8.-21. Mai 2026)", None, {"range_m": 2},
     "Moderater Schaden + Geschwindigkeit; Charged Attack 55 Grad Trefferwinkel. Max Weapon-Level 30."),
    ("executioners-duet", "Executioner's Duet", "Melee", "Melee", "Axe",
     "Season 4 - Mid-Season Event (Event-Details offen)", None, {},
     "Hoher Schaden, kurze Reichweite, sehr schnelle Angriffsgeschwindigkeit. [Konfidenz wahrscheinlich - S4-Mid-Season-Unlock zum Recherche-Zeitpunkt nicht final offenbart.]"),
    # --- Special ---
    ("nx-ravager", "NX Ravager", "Special", "Special", "Crossbow / Bolt Launcher",
     "Season 1 - Rally Point Event (Community + Personal Missions)", None, {},
     "Hochschaden-Bolzen; Fire-Mod explosive Bolzen (Detonation nach Impact); Prestige Tribolt (3 Bolzen). Keine numerischen TGD-Stats."),
    ("gdl-havoc", "GDL Havoc", "Special", "Special", "Grenade Launcher (Remote Detonation)",
     "Season 2 - Armory Unlock (250k XP)", None, {},
     "Pump-action; Granaten haften an Oberflaechen + remote-detonierbar; kein ADS; Schadenstyp Explosion. Keine numerischen TGD-Stats."),
    ("siren", "Siren", "Special", "Special", "Energy Weapon",
     "Season 3 Reloaded - RoboCop Event Pass (Free Track, 460k XP)", None, {},
     "Charge-basiert; durchdringendes Energie-Projektil (pass-through); Charge erhoeht Projektilgeschwindigkeit; Prestige MFS Deflection Core (Ricochet + mehr Mag). Keine numerischen TGD-Stats."),
    ("grimhawk", "Grimhawk", "Special", "Special", "Homing-Rounds Rifle (Auto)",
     "Season 4 - Weekly Challenge Week 1 (6 Challenges aus MP/Zombies/Endgame/Warzone)", None, {"mag": 60},
     "Vollautomatisch; Low-Velocity-Projektile mit leichtem Homing auf feuernde Gegner. Special (NICHT Melee - 1 GameRant-Artikel falsch). Keine weiteren numerischen TGD-Stats."),
    # --- Launcher ---
    ("aarow-109", "AAROW 109", "Launcher", "Launcher", "Hybrid Launcher (Rocket)",
     "Launch (Standard, default)", None, {},
     "Hybrid: Lock-on fuer Fahrzeuge + Scorestreaks; auch Free-Fire moeglich; Zombies-Upgrade BAALIST AARTILLERY. Keine numerischen TGD-Stats."),
    ("arc-m1", "A.R.C. M1", "Launcher", "Launcher", "Energy Charge Launcher",
     "Launch (Level 25)", 25, {"mag": 3},
     "Halten = Energiestrahl aufladen; durchdringt Gegner; hoher Schaden gegen Fahrzeuge + Scorestreaks; kein Lock-on. (= Named-Exotic 'Criticality'/Mortar in Endgame.)"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for wid, name, cls, wt, sub, unlock, ulevel, base, note in ROWS:
        w = {
            "id": wid, "name": name, "class": cls, "game": "bo7", "weapon_type": wt,
            "in_warzone": True, "source": SRC, "data_version": DV, "subclass": sub,
            "unlock": unlock, "note": note, "base": base, "slots": {},
        }
        if ulevel is not None:
            w["unlock_level"] = ulevel
        (OUT / f"{wid}.json").write_text(json.dumps(w, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
    print(f"{n} Melee/Special/Launcher-Roster-Files geschrieben -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
