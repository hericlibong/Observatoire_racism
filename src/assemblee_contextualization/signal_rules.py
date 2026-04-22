from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class SignalRule:
    family: str
    trigger: str
    intensity: int


@dataclass(frozen=True)
class SignalHit:
    signal_candidate: bool
    signal_family: str
    signal_trigger: str
    signal_intensity: int


SIGNAL_RULES = [
    SignalRule("devalorisation", "honteuse", 2),
    SignalRule("devalorisation", "une honte", 2),
    SignalRule("devalorisation", "propos deshonorants", 2),
    SignalRule("devalorisation", "inadmissibles", 2),
    SignalRule("devalorisation", "irresponsable", 2),
    SignalRule("devalorisation", "inacceptable", 2),
    SignalRule("devalorisation", "mepris", 2),
    SignalRule("devalorisation", "trahir", 2),
    SignalRule("tension_politique", "passage en force", 2),
    SignalRule("tension_politique", "ligne rouge", 2),
    SignalRule("tension_politique", "chaos", 2),
    SignalRule("tension_politique", "colere", 2),
    SignalRule("tension_politique", "violences", 2),
    SignalRule("tension_politique", "obstruction", 2),
    SignalRule("designation_groupe", "anti-independantistes", 2),
    SignalRule("designation_groupe", "puissance colonisatrice", 2),
    SignalRule("designation_groupe", "independantistes", 1),
    SignalRule("designation_groupe", "non-independantistes", 1),
    SignalRule("designation_groupe", "peuple kanak", 1),
    SignalRule("designation_groupe", "identite kanak", 1),
    SignalRule("designation_groupe", "communautes", 1),
    SignalRule("designation_groupe", "loyalistes", 1),
    SignalRule("designation_groupe", "kanaky", 1),
    SignalRule("designation_groupe", "flnks", 1),
]


def normalize_for_signal(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.replace("\u2019", "'")).strip()


def signal_hit_from_text(text: str) -> SignalHit:
    normalized = normalize_for_signal(text)
    best_match: SignalRule | None = None

    for rule in SIGNAL_RULES:
        trigger = normalize_for_signal(rule.trigger)
        if re.search(rf"(?<!\w){re.escape(trigger)}(?!\w)", normalized):
            if best_match is None or rule.intensity > best_match.intensity:
                best_match = rule

    if best_match is None:
        return SignalHit(False, "", "", 0)

    return SignalHit(True, best_match.family, best_match.trigger, best_match.intensity)
