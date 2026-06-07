#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut cod_db_drumherum_json/calling_cards.json aus der S4-Enumeration.

Quelle: audits/full_audit_2026-06-06/calling_cards_enumeration.md (web-researcher,
multi-source: detonated/PCGamesN/Windows Central/Dexerto/Game8/GameRant/Sportskeeda/
Activision + CoD Fandom Wiki als EINE Beispielquelle, nicht exklusiv).

Fokus: bedingungs-gated Cards (Dark Ops, Zombies-EE, Ranked, Mastery, Events).
Battle-Pass/Store = reine Kosmetik -> Sammelkategorie. Reproduzierbar: re-run
ueberschreibt die JSON deterministisch (Atomic-Write).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent.parent / "cod_db_drumherum_json" / "calling_cards.json"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s


def cards(rows, **fixed):
    """rows = list of (card, condition, conf[, season/map/mode]) -> list of dicts."""
    out = []
    for r in rows:
        card, cond, conf = r[0], r[1], r[2]
        d = {"id": slug(card), "card": card, "condition": cond, "confidence": conf}
        d.update(fixed)
        if len(r) > 3 and r[3]:
            d["season"] = r[3]
        out.append(d)
    return out


dark_campaign = cards([
    ("Undaunted", "Ueberlebe die Fear-Horde in Mission: Suppression", "bestaetigt"),
    ("Exotic Arsenal", "Kills mit 6 verschiedenen Exotic Weapons in Endgame", "bestaetigt"),
    ("Green Thumb", "Besiege The Nightmare in Mission: Distortion ohne Schaden", "bestaetigt"),
    ("Absolute Loss", "Besiege Menendez nur mit Machetes in Mission: Exposure", "bestaetigt"),
    ("Overpowered", "1.000.000 Power in Endgame (kumulativ)", "bestaetigt"),
    ("Monkeying Around", "Parkour- UND Dive-Strecke in Endgame absolvieren", "bestaetigt"),
    ("Dream Team", "25x aus Zone IV entkommen in Endgame", "bestaetigt"),
    ("Pest Control", "Endgame Final Boss besiegen", "bestaetigt"),
    ("Predator Becomes Prey", "Hunter Activity aktivieren und besiegen", "wahrscheinlich"),
    ("Mountain Climber", "Auf dem Toxic Tyrant reiten", "wahrscheinlich", "S1"),
    ("Giant Feeling", "Exfil via Colossus of Avalon", "wahrscheinlich", "S1"),
    ("Titan Hunter", "3 einzigartige World Events absolvieren", "wahrscheinlich", "S1"),
    ("Stationary Stalwart", "Anfangszonen in Root Crasher ohne Down erobern", "bestaetigt", "S2"),
    ("Off-Meta", "Root Crasher ohne Crash Cart oder Ballistic Shield", "bestaetigt", "S2"),
    ("Run It Back", "3 Operator-Skins aus Root Crasher freischalten", "bestaetigt", "S2"),
    ("Elusive", "Link Forger Glitch Boss ohne gestunnt zu werden eliminieren", "bestaetigt", "S3"),
    ("Single-Threaded", "Link Forger Glitch solo absolvieren", "bestaetigt", "S3"),
    ("Go Fetch", "D.A.W.G.-Schild mit zurueckgeworfener D.A.W.G.-Ausruestung zerstoeren", "bestaetigt", "S3"),
], mode="Campaign/Endgame")

dark_mp = cards([
    ("Frenzy Killer", "Frenzy Kill Medal (5 Rapid Kills)", "bestaetigt"),
    ("Mega Killer", "Mega Kill Medal (6 Rapid Kills)", "bestaetigt"),
    ("Ultra Killer", "Ultra Kill Medal (7 Rapid Kills)", "bestaetigt"),
    ("Chain Killer", "Kill Chain Medal (>7 Rapid Kills)", "bestaetigt"),
    ("Relentless Killer", "Relentless Medal (20 Kills ohne Tod)", "bestaetigt"),
    ("Brutal Killer", "Brutal Medal (25 Kills ohne Tod)", "bestaetigt"),
    ("Nuclear Killer", "Nuclear Medal (30 Kills ohne Tod, nur Waffen/Equipment/Field Upgrades)", "bestaetigt"),
    ("Nuked Out", "Nuclear Medal in Free For All ohne Scorestreaks", "bestaetigt"),
    ("Very Nuclear", "Nuclear Medal mit 25 verschiedenen Waffen", "bestaetigt"),
    ("Same Day Delivery", "2+ Kills mit einer einzelnen Body-Shield-Explosion", "bestaetigt"),
    ("Trip Cap", "Alle 3 Domination-Ziele 3 Minuten am Stueck halten", "bestaetigt"),
    ("Castled", "10 Kills ohne eine Objective-Zone zu verlassen", "bestaetigt"),
    ("Gift Horse", "Kill mit aus feindlichem Care Package gestohlenem Scorestreak", "bestaetigt"),
    ("Extreme Precision", "5 Sniper-Headshots ohne Nachladen/Tod", "bestaetigt"),
    ("Reverse Card", "Kill durch Beschuss von gegnerischem Equipment/Field Upgrade", "bestaetigt"),
    ("Circus Act", "Bankshot Medal (Combat-Axe-Kill nach Wandprall)", "bestaetigt"),
    ("Pushing the Limits", "40 Overclock-Upgrades in Gunsmith freischalten", "bestaetigt"),
    ("100k", "100.000 Eliminations in Multiplayer", "bestaetigt"),
    ("Touch Grass", "Weapon Prestige Master Max Level mit 30 Waffen", "bestaetigt"),
], mode="MP")

dark_zombies = (
    cards([
        ("Box Addict", "30 verschiedene Mystery-Box-Waffen in einem Match", "bestaetigt", "Alle"),
        ("Lucidity", "Tank Dempsey Side Quest auf Ashes of the Damned", "bestaetigt", "Ashes"),
        ("Armed to the Teeth", "3x PaP-LvIII-Legendary mit Ammo-Mods + 8 Perks gleichzeitig", "bestaetigt", "Alle"),
        ("Invincible", "Runde 50 ohne einmal Down", "bestaetigt", "Alle"),
        ("Another Round", "Runde 100 erreichen", "bestaetigt", "Alle"),
        ("Countdown", "Elite-Zombie per Jump-Pad in den Tod befoerdern", "bestaetigt", "Alle"),
        ("New Main", "1.000 Zombie-Kills mit jedem Dedicated-Crew-Operator", "bestaetigt", "Alle"),
        ("Harbinger of Doom", "100 Zombie-Kills mit einem einzelnen Scorestreak", "bestaetigt", "Alle"),
        ("Social Distancing", "Runde 20 ohne Schaden", "bestaetigt", "Alle"),
        ("Action Hero", "100 Zombies ohne Nachladen toeten", "bestaetigt", "Alle"),
        ("Ingenuity", "Runde 50 in Cursed Mode mit Dragon Wings & Lawyer's Pen Relics", "bestaetigt", "Ashes"),
        ("Showboat", "Ashes Main Quest bei Runde 100+ abschliessen", "bestaetigt", "Ashes"),
        ("Boss Rush", "Ashes Endboss in <=5 Minuten besiegen", "bestaetigt", "Ashes"),
        ("Anathema", "1.000.000 Zombies eliminieren (kumulativ)", "bestaetigt", "Alle"),
        ("The One", "Runde 999 erreichen", "bestaetigt", "Alle"),
        ("Martial Artist", "Runde 50 nur mit Melee & Combat Axes", "bestaetigt", "Alle"),
        ("The Usual, Please", "Juggernog 20x in einem Match trinken", "bestaetigt", "Alle"),
        ("Hard Mode", "Ashes EE in Cursed Mode mit 3 Wicked Relics", "bestaetigt", "Ashes"),
        ("Serious Monkey Business", "Papaback in Hardcore Dead Ops Arcade besiegen", "bestaetigt", "Dead Ops"),
        ("Flushed For Cash", "25 Mio Silverback Cash verdienen (kumulativ)", "bestaetigt", "Alle"),
        ("Ready For Publishing", "Alle Augments fuer alle Items erforschen", "bestaetigt", "Alle"),
        ("Reliquary", "Alle Relics in Ashes of the Damned sammeln", "bestaetigt", "Ashes"),
        ("Mythic Cynic", "Runde 50 mit allen Ashes-Relics aktiv", "bestaetigt", "Ashes"),
        ("Blitzed", "Ashes EE mit Samantha's Drawing & Teddy Bear Relics in <=1 Std", "bestaetigt", "Ashes"),
        ("Echoes", "Echoes of the Damned Side Quest abschliessen", "bestaetigt", "Astra Malorum"),
        ("Astronomical", "Astra Malorum Main Quest mit Spider Fang + Civil Protector Head + Golden Spork Relics", "bestaetigt", "Astra Malorum"),
        ("Neutronomic", "Paradox Junction Main Quest bei Runde 100", "bestaetigt", "Paradox Junction"),
        ("Chronomancer", "Paradox Junction Main Quest ohne Time-Travel-Fee", "bestaetigt", "Paradox Junction"),
        ("Relativity", "Paradox Junction Main Quest in unter 1 Stunde", "bestaetigt", "Paradox Junction"),
        ("The Bomba", "Paradox Junction Main Quest mit allen Mantis Relics", "bestaetigt", "Paradox Junction"),
        ("Domineering", "Echoes of the Damned (Richtofen-Side-Quest auf Totenreich)", "bestaetigt", "Totenreich"),
        ("Deicide", "Totenreich Main Quest bei Runde 100", "bestaetigt", "Totenreich"),
        ("Aether Ruler", "Totenreich Main Quest mit allen Hard Relics aktiv", "wahrscheinlich", "Totenreich"),
        ("Shaman", "100 Alchemist Medals (>=5 Zombies mit >=2 Elementen rapid)", "wahrscheinlich", "Totenreich"),
    ], mode="Zombies")
)

dark_warzone = cards([
    ("Blind Lead", "Elimination mit Hipfire einer Sniper Rifle", "bestaetigt"),
    ("Holstered", "5 Pistol-Eliminations in einem Match", "bestaetigt"),
    ("Boom Boom", "5 Launcher-Eliminations in einem Match", "bestaetigt"),
    ("Chop Chop", "1 Elimination beim Helicopter-Reiten", "bestaetigt"),
    ("Repeat Exploder", "3 Eliminations durch feindliche Grenade-Sticks in einem Match", "bestaetigt"),
    ("Make It Stick", "Most Wanted Contract Target per Grenade Stick eliminieren", "bestaetigt"),
    ("Last Cap Standing", "5 Recon Contracts in einem Match", "bestaetigt"),
    ("Next", "5 Bounty Contracts in einem Match", "bestaetigt"),
    ("Humbled", "3 Big Game Bounty Contracts in einem Match", "bestaetigt"),
    ("Gotta Run", "5 Supply Run Contracts in einem Match", "bestaetigt"),
    ("All Mine", "5 Scavenger Contracts in einem Match", "bestaetigt"),
    ("Ascendance", "1 Match gewinnen ohne zu sterben", "bestaetigt"),
    ("Flawless Feed", "4 Eliminations ohne Nachladen in einem Match", "bestaetigt"),
    ("One Round Crowns", "100 Headshots (kumulativ)", "bestaetigt"),
    ("Backlog", "7 Contracts in einem Match", "bestaetigt"),
    ("Sliced", "5 Melee-Eliminations in einem Match", "bestaetigt"),
    ("The Cleaner", "50 Squads wipen (kumulativ)", "bestaetigt"),
    ("Deleted", "20 Eliminations in einem Match", "bestaetigt"),
    ("Ground War", "100 Eliminations mit Ground-Loot-Waffen (kumulativ)", "bestaetigt"),
    ("Efficient Execution", "5 One-Shot-Sniper-Eliminations in einem Match", "bestaetigt"),
    ("Royalty", "Alle 9 Black Ops Royale Operator Orders abschliessen", "bestaetigt", "S2"),
], mode="Warzone")

zombies_milestone = cards([
    ("Totenreich Completion", "Totenreich Main Quest abschliessen", "bestaetigt", "Totenreich"),
    ("Totenreich Early Completion", "Totenreich Main Quest vor Season-4-Start (vor Directed Mode)", "bestaetigt", "Totenreich"),
    ("Totenreich Mastery", "Alle Totenreich Map-Challenges abschliessen", "bestaetigt", "Totenreich"),
    ("Totenreich Intel Collection", "Alle Intel-Stuecke auf Totenreich sammeln", "bestaetigt", "Totenreich"),
], mode="Zombies")


def ranked(season, tiers):
    return [{"id": f"ranked-{season.lower()}-{slug(t[0])}", "card": f"Ranked {season} — {t[0]}",
             "condition": t[1], "confidence": t[2], "mode": "Ranked", "season": season}
            for t in tiers]


ranked_s2 = ranked("Season 02", [
    ("Silver", "Silver Rank in S2 erreichen", "wahrscheinlich"),
    ("Gold", "Gold Rank in S2 erreichen", "bestaetigt"),
    ("Platinum", "Platinum Rank in S2 erreichen", "wahrscheinlich"),
    ("Diamond", "Diamond Rank in S2 erreichen", "wahrscheinlich"),
    ("Crimson", "Crimson Rank in S2 erreichen", "wahrscheinlich"),
    ("Iridescent", "Iridescent Rank in S2 erreichen", "wahrscheinlich"),
    ("Top 250 Champion", "Top-250-Abschlussrang in S2", "wahrscheinlich"),
])
ranked_s3 = ranked("Season 03", [
    ("Silver", "Silver Rank in S3 erreichen", "bestaetigt"),
    ("Gold", "Gold Rank in S3 erreichen", "bestaetigt"),
    ("Platinum", "Platinum Rank in S3 erreichen", "bestaetigt"),
    ("Diamond", "Diamond Rank in S3 erreichen", "wahrscheinlich"),
    ("Crimson", "Crimson Rank in S3 erreichen", "wahrscheinlich"),
    ("Iridescent", "Iridescent Rank in S3 erreichen", "wahrscheinlich"),
    ("Top 250 Champion", "Top-250-Abschlussrang in S3", "wahrscheinlich"),
])
ranked_s4 = ranked("Season 04", [
    ("Silver", "Silver Rank in S4 erreichen", "bestaetigt"),
    ("Gold", "Gold Rank in S4 erreichen", "bestaetigt"),
    ("Platinum", "Platinum Rank in S4 erreichen", "bestaetigt"),
    ("Diamond", "Diamond Rank in S4 erreichen", "bestaetigt"),
    ("Crimson", "Crimson Rank in S4 erreichen", "bestaetigt"),
    ("Iridescent", "Iridescent Rank in S4 erreichen (Animated)", "bestaetigt"),
    ("Top 250", "Season-4-Abschlussrang Top 250 (Animated)", "bestaetigt"),
    ("Top 250 Champion", "Season-4-Abschlussrang #1 Gesamt (Animated)", "bestaetigt"),
])

mastery_percenter = cards([
    ("100 Percenter (Multiplayer)", "Alle MP Challenge-Karten freischalten (Dark Ops ausgenommen)", "bestaetigt", "MP"),
    ("100 Percenter (Zombies)", "Alle Zombies Challenge-Karten freischalten (Dark Ops ausgenommen)", "bestaetigt", "Zombies"),
    ("100 Percenter (Campaign)", "Alle Campaign Challenge-Karten freischalten (Dark Ops ausgenommen)", "bestaetigt", "Campaign"),
    ("100 Percenter (Warzone)", "Alle Warzone Challenge-Karten freischalten (Dark Ops ausgenommen)", "bestaetigt", "Warzone"),
    ("400 Percenter", "Alle 4 Modus-100-Percenter-Cards erhalten", "wahrscheinlich", "Cross-Mode"),
])
mastery_prestige = cards([
    ("Prestige 1 Mastery Card", "Alle Prestige-1-Mastery-Challenges abschliessen", "wahrscheinlich"),
    ("Prestige 2-10 Mastery Cards (x9)", "Jeweilige Prestige-Mastery-Challenges (pro Prestige unique Karte)", "wahrscheinlich"),
    ("Prestige Master Mastery Card", "Prestige Master Level + dessen Challenges", "wahrscheinlich"),
], mode="MP/Zombies")

events = cards([
    ("Terms of Disservice (Animated)", "Operation Wall Breaker: alle 9 Steps + Command Killer Glitch Boss auf Nightmare", "bestaetigt", "S4"),
    ("Illicit Cargo Event Card(s)", "Illicit Cargo Camo Event Challenge-Completion (Name nicht namentlich publiziert)", "unsicher", "S4"),
], mode="Event")

# Flache Aggregat-Liste (Pflicht-Key 'items' fuer drumherum-validate + Bot-Suche).
def tag(rows, group):
    return [{**r, "group": group} for r in rows]


flat_items = (
    tag(dark_campaign, "dark_ops_campaign_endgame")
    + tag(dark_mp, "dark_ops_mp")
    + tag(dark_zombies, "dark_ops_zombies")
    + tag(dark_warzone, "dark_ops_warzone")
    + tag(zombies_milestone, "zombies_milestone")
    + tag(ranked_s2, "ranked_s2") + tag(ranked_s3, "ranked_s3") + tag(ranked_s4, "ranked_s4")
    + tag(mastery_percenter, "mastery_percenter") + tag(mastery_prestige, "mastery_prestige")
    + tag(events, "events")
)

db = {
    "category": "calling_cards",
    "game": "bo7",
    "data_version": "S4 (2026-06-06)",
    "source": "detonated/PCGamesN/Windows Central/Dexerto/Game8/GameRant/Sportskeeda/Activision/overgear/grindout + CoD Fandom Wiki (eine von mehreren Quellen, nicht exklusiv)",
    "scope_note": "Fokus auf bedingungs-gated Cards (Dark Ops, Zombies-EE, Ranked, Mastery, Events) mit Freischalt-Bedingung. Battle-Pass/Store = reine Kosmetik -> Sammelkategorie. Stand 2 Tage nach S4-Launch: S4-Dark-Ops noch nicht community-dokumentiert.",
    "nomenclature_note": "Jede Dark-Ops-Card traegt den Namen ihrer Challenge (Challenge 'Nuked Out' -> Card 'Nuked Out').",
    "counts": {
        "dark_ops": len(dark_campaign) + len(dark_mp) + len(dark_zombies) + len(dark_warzone),
        "zombies_milestone": len(zombies_milestone),
        "ranked": len(ranked_s2) + len(ranked_s3) + len(ranked_s4),
        "mastery": len(mastery_percenter) + len(mastery_prestige),
        "events": len(events),
    },
    "unlock_system": [
        {"source": "Dark Ops", "detail": "versteckte Challenges, Card = Challenge-Name; oft die prestigetraechtigsten"},
        {"source": "Multiplayer-Challenges", "detail": "inkl. Ranked Play + 100-Percenter"},
        {"source": "Zombies-Challenges", "detail": "Round-Meilensteine, Map-Easter-Eggs, Directed Mode"},
        {"source": "Warzone-Challenges", "detail": "Contracts, Eliminations, Royale Orders"},
        {"source": "Ranked Play", "detail": "saisonal exklusiv (Silver-Iridescent + Top 250), laufen mit Saisonende aus"},
        {"source": "Mastery/Prestige", "detail": "100-Percenter + Prestige-Mastery + Camo-Challenge-Cards"},
        {"source": "Events", "detail": "Limited-Time (Operation Wall Breaker etc.)"},
        {"source": "Battle Pass / BlackCell / Store", "detail": "reine Kosmetik, nicht bedingungs-gated"},
    ],
    "dark_ops": {
        "campaign_endgame": dark_campaign,
        "multiplayer": dark_mp,
        "zombies": dark_zombies,
        "warzone": dark_warzone,
        "season4_status": "2 Tage nach S4-Launch noch keine neuen S4-Dark-Ops community-dokumentiert. Kowakujo (S4 Reloaded ~Juli 2026) bringt voraussichtlich weitere. ~1 Woche nach Launch detonated.com/windowscentral neu pruefen.",
    },
    "zombies_milestone": zombies_milestone,
    "ranked": {
        "season2": ranked_s2,
        "season3": ranked_s3,
        "season4": ranked_s4,
        "note": "SR-Schwellen offiziell nicht publiziert; 10.000 SR = Iridescent-Eintritt, ab dort Leaderboard-Platz fuer Top 250. Season 1 hatte kein vollstaendiges Ranked-System.",
    },
    "mastery": {
        "percenter": mastery_percenter,
        "prestige": mastery_prestige,
        "camo_challenge_category": {
            "description": "Separate Cards gekoppelt an Mastery-Camo-Stufen (z.B. 'Camo Challenge - Shattered Gold AR'). ~100+ ueber Waffenklasse x Camo-Tier.",
            "confidence": "wahrscheinlich",
            "note": "Kategorie bestaetigt, Einzelnamen nur in-game einsehbar.",
        },
    },
    "events": events,
    "items": flat_items,
    "bulk_categories": [
        {"category": "Battle Pass Cards", "estimate": "~8-12 pro Season", "headliner": "Animated Cards an Token-Tiers (30/50/90+)", "source": "boostmatch"},
        {"category": "BlackCell Premium Cards", "estimate": "~2-4 pro Season", "headliner": "exklusive Animated Cards im BlackCell-Track", "source": "GameRant"},
        {"category": "Store Bundle Cards", "estimate": ">50 ueber alle Seasons", "headliner": "'Never Broken' (Endowment Legacy Bundle), Operator-Bundle-Cards", "source": "Game8"},
        {"category": "Default Cards", "estimate": "6", "headliner": "Fractured Mind, Systemic, New World, Enforcement, Undercover, Conspiracy", "source": "Game8"},
    ],
    "gaps": [
        {"item": "Season 4 Dark Ops", "status": "2 Tage nach Launch nicht community-dokumentiert; Kowakujo (~Juli 2026) folgt", "todo": True},
        {"item": "Totenreich Aether Ruler + Shaman", "status": "Existenz bestaetigt, Vollbedingung nicht primaer-belegt", "todo": True},
        {"item": "Ranked S1/S2 Tier-Namen (ausser S2 Gold)", "status": "strukturell wahrscheinlich, nicht alle namentlich belegt", "todo": True},
        {"item": "Prestige-Mastery Card-Namen P1-P10", "status": "Existenz belegt, Einzelnamen nur in-game", "todo": True},
        {"item": "Camo-Challenge-Cards (~100+)", "status": "Kategorie bestaetigt, Vollliste nur in-game", "todo": True},
        {"item": "Battle-Pass/Store 1:1-Enumeration", "status": "bewusst nicht eingezogen (reine Kosmetik)", "todo": False},
    ],
    "full_list_sources": [
        {"name": "detonated.com (Dark Ops, umfangreichste Einzelquelle)", "url": "https://detonated.com/all-black-ops-7-dark-ops-challenges-multiplayer-zombies-campaign/"},
        {"name": "PCGamesN Dark Ops", "url": "https://www.pcgamesn.com/call-of-duty-black-ops-7/dark-ops-challenges"},
        {"name": "Windows Central Dark Ops", "url": "https://www.windowscentral.com/gaming/here-are-all-of-the-call-of-duty-black-ops-7-dark-ops-challenges-and-the-rewards-you-can-get"},
        {"name": "Dexerto Ranked Rewards", "url": "https://www.dexerto.com/wikis/black-ops-7-guides-walkthrough-tips/black-ops-7-ranked-play-rewards/"},
        {"name": "GameRant S4 Ranked", "url": "https://gamerant.com/call-of-duty-cod-black-ops-7-bo7-warzone-season-4-ranked-play-rewards-camos-how-to-get/"},
        {"name": "Game8 All Calling Cards", "url": "https://game8.co/games/Call-of-Duty-Black-Ops-7/archives/565483"},
        {"name": "CoD Fandom Wiki Calling Cards (eine Beispielquelle)", "url": "https://callofduty.fandom.com/wiki/Calling_Cards/Call_of_Duty:_Black_Ops_7"},
    ],
}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUT)
    total = sum(db["counts"].values())
    print(f"calling_cards.json geschrieben: {total} bedingungs-gated Cards + 4 Bulk-Kategorien -> {OUT}")
    print("  counts:", db["counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
