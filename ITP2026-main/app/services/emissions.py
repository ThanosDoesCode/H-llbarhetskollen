from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


# Factor är en oföränderlig datastruktur (frozen=True) som representerar en emissionsfaktor
# frozen=True betyder att värdena inte kan ändras efter att objektet skapats
@dataclass(frozen=True)
class Factor:
    category: str        # t.ex. "travel"
    key: str             # t.ex. "car"
    unit: str            # t.ex. "km"
    co2e_per_unit: float # kg CO₂e per enhet — hämtas från databasen


# FactorMap är en typdefinition för ordboken som används för snabba uppslag
# Nyckeln är en tupel (category, key) och värdet är ett Factor-objekt
FactorMap = Dict[Tuple[str, str], Factor]


def calculate_co2e(category: str, key: str, amount: float, factors: FactorMap) -> float:
    """Beräkna CO₂e för en aktivitet.

    - category: t.ex. 'travel', 'food', 'energy'
    - key: t.ex. 'car', 'train', 'beef'
    - amount: t.ex. km, portioner, kWh (beror på unit)
    - factors: mapping (category, key) -> Factor

    (För kursen: håll beräkningen transparent och enkel.)
    """
    # Validerar att mängden är positiv innan beräkningen görs
    if amount <= 0:
        raise ValueError("amount must be > 0")

    # Slår upp emissionsfaktorn med (category, key) som nyckel i ordboken
    factor = factors.get((category, key))

    # Om faktorn inte finns i databasen kastas ett KeyError — detta fångas i main.py
    if factor is None:
        raise KeyError(f"No emission factor for ({category}, {key})")

    # Själva beräkningen: mängd × CO₂e per enhet = total CO₂e i kg
    return amount * factor.co2e_per_unit
