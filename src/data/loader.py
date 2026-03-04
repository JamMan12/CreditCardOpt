"""
DataLoader: loads credit card data from the static cards.json database.
This replaces the mock_db.py and provides the full ~25-card universe.
"""

import json
from pathlib import Path
from src.models.schemas import Card

_DATA_PATH = Path(__file__).parent / "cards.json"


def _load_raw() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_raw = _load_raw()

# ─── Point Valuations ───────────────────────────────────────────────────────────
# Cents per point for each rewards program, sourced from Prince of Travel.
POINT_VALUATIONS: dict[str, float] = _raw["point_valuations"]


# ─── Cards ──────────────────────────────────────────────────────────────────────
def _build_card(raw_card: dict) -> Card:
    return Card(
        id=raw_card["id"],
        name=raw_card["name"],
        issuer=raw_card["issuer"],
        network=raw_card["network"],
        annual_fee=raw_card["annual_fee"],
        first_year_fee=raw_card.get("first_year_fee"),
        earning_rates=raw_card["earning_rates"],
        point_system=raw_card["point_system"],
        welcome_bonus_points=raw_card.get("welcome_bonus_points", 0),
        welcome_bonus_spend_req=raw_card.get("welcome_bonus_spend_req", 0),
        has_no_fx_fee=raw_card.get("has_no_fx_fee", False),
        has_lounge_access=raw_card.get("has_lounge_access", False),
    )


ALL_CARDS: list[Card] = [_build_card(c) for c in _raw["cards"]]


def get_card_by_id(card_id: str) -> Card | None:
    return next((c for c in ALL_CARDS if c.id == card_id), None)


def get_cards_by_issuer(issuer: str) -> list[Card]:
    return [c for c in ALL_CARDS if c.issuer.lower() == issuer.lower()]


def get_cards_with_perk(no_fx: bool = False, lounge: bool = False) -> list[Card]:
    return [
        c for c in ALL_CARDS
        if (not no_fx or c.has_no_fx_fee) and (not lounge or c.has_lounge_access)
    ]
