#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S4-Neuwaffen die TGD S3.5 nicht hatte (Roster-Ergaenzung).

CBRS-3, KRS-7.62, AN-94, VX Compact (BP/Event) + Kilonova/Infraradiance (S4-Reloaded
Exotics). Quelle: callofduty.com offiziell + GameRant/Dexerto/Game8/GameSpot (non-TGD).
Sparse base nur wo dokumentiert; sonst base={}. Keine Slots (TGD-untracked).
Schreibt Staging-Files -> promote_v2 + consolidate.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "cod_db_deltas_v2"
SRC = "callofduty.com + GameRant/Dexerto/Game8/GameSpot (S4-Recherche, non-TGD)"
DV = "S4_2026-06-08"

# (id, name, class, weapon_type, subclass, unlock, base, note)
ROWS = [
    ("cbrs-3", "CBRS-3", "SMG", "SMG", "Full-Auto SMG",
     "Season 4 - Battle Pass Page 6 (HVT)", {"mag": 60},
     "Full-Auto SMG fuer Dauerfeuer, 60-Round-Mag default, ueberdurchschnittliche Range + Recoil-Kontrolle. Rechamber-Pause nach 20 (MP)/30 (WZ) Schuss -> MFS Carousel Fast Mag empfohlen. S4-Neuwaffe, nicht in TGD S3.5."),
    ("krs-7-62", "KRS-7.62", "Marksman Rifle", "MR", "Semi-Auto Marksman",
     "Season 4 - Battle Pass Page 3 (HVT)", {},
     "Semi-auto Marksman, hoher Schaden + gute Mobility, signifikanter First-Shot-Recoil. 2-Hit-Kill bis ~25m. S4-Neuwaffe, nicht in TGD."),
    ("an-94", "AN-94", "AR", "AR", "Assault Rifle",
     "Season 4 - Mid-Season Event", {},
     "S4-Neuwaffe (AR), Mid-Season-Event-Unlock. Stats nicht in TGD / oeffentlich detailliert."),
    ("vx-compact", "VX Compact", "AR", "AR", "Compact AR",
     "Season 4 - Illicit Cargo Camo Event", {},
     "S4-Neuwaffe (AR), via Illicit-Cargo-Event (+ BO3-Remaster-Camos). Stats nicht in TGD."),
    ("kilonova", "Kilonova", "SMG", "SMG", "Full-Auto SMG (Exotic, Graviton)",
     "Season 4 Reloaded - Loot-Pool / Exotic", {},
     "S4-Reloaded Exotic-SMG, fuer Mobility/CQC, Affinity Graviton Rounds. Base-Weapon-Mapping unklar (evtl. eigene Waffe). Nicht in TGD."),
    ("infraradiance", "Infraradiance", "Shotgun", "SG", "Semi-Auto Shotgun (Exotic, Photon)",
     "Season 4 Reloaded - Loot-Pool / Exotic", {},
     "S4-Reloaded Exotic-Semi-Auto-Shotgun, aggressiv, Affinity Photon Rounds. Nicht in TGD."),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for wid, name, cls, wt, sub, unlock, base, note in ROWS:
        w = {
            "id": wid, "name": name, "class": cls, "game": "bo7", "weapon_type": wt,
            "in_warzone": True, "source": SRC, "data_version": DV, "subclass": sub,
            "unlock": unlock, "note": note, "base": base, "slots": {},
        }
        (OUT / f"{wid}.json").write_text(json.dumps(w, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
    print(f"{n} S4-Neuwaffen geschrieben -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
