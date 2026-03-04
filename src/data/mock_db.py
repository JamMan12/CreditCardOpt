from src.models.schemas import Card, PointValuation

# Static Point Valuations (CPP - Cents Per Point)
POINT_VALUATIONS = {
    "aeroplan": 2.1,
    "amex_mr": 2.0,
    "cashback": 1.0,
    "avios": 1.5,
    "scene_plus": 1.0,  # 1 cent per point flat
}

# Mock Database of Credit Cards
MOCK_CARDS = [
    Card(
        id="amex_cobalt",
        name="American Express Cobalt",
        issuer="Amex",
        network="Amex",
        annual_fee=155.88, # $12.99/month
        first_year_fee=155.88,
        earning_rates={
            "dining": 5.0, # 5x MR on eats
            "grocery": 5.0, # 5x MR on grocery
            "streaming": 3.0,
            "travel": 2.0,
            "transit": 2.0,
            "gas": 2.0,
            "other": 1.0
        },
        point_system="amex_mr",
        welcome_bonus_points=15000,
        welcome_bonus_spend_req=3000.0,
        has_no_fx_fee=False,
        has_lounge_access=False
    ),
    Card(
        id="td_aeroplan_vi",
        name="TD Aeroplan Visa Infinite",
        issuer="TD",
        network="Visa",
        annual_fee=139.0,
        first_year_fee=0.0, # Often first year free
        earning_rates={
            "grocery": 1.5,
            "gas": 1.5,
            "air_canada": 2.0,
            "travel": 1.0,
            "dining": 1.0,
            "other": 1.0
        },
        point_system="aeroplan",
        welcome_bonus_points=40000,
        welcome_bonus_spend_req=5000.0,
        has_no_fx_fee=False,
        has_lounge_access=False # Actually has ML lounge passes but ignoring for now
    ),
    Card(
        id="scotia_passport_vi",
        name="Scotiabank Passport Visa Infinite",
        issuer="Scotiabank",
        network="Visa",
        annual_fee=150.0,
        first_year_fee=0.0,
        earning_rates={
            "grocery": 2.0,
            "dining": 2.0,
            "entertainment": 2.0,
            "transit": 2.0,
            "other": 1.0
        },
        point_system="scene_plus",
        welcome_bonus_points=30000,
        welcome_bonus_spend_req=1000.0,
        has_no_fx_fee=True,
        has_lounge_access=True # 6 lounge passes
    ),
    Card(
        id="tangerine_moneyback",
        name="Tangerine Money-Back Credit Card",
        issuer="Tangerine",
        network="Mastercard",
        annual_fee=0.0,
        first_year_fee=0.0,
        earning_rates={
            # Standard Tangerine gives 2% on 2/3 categories. We'll simulate it as just fixed categories for simplicity
            "grocery": 2.0,
            "gas": 2.0,
            "recurring": 2.0,
            "other": 0.5
        },
        point_system="cashback",
        welcome_bonus_points=10000, # Assuming a generic welcome bonus for cashback $100
        welcome_bonus_spend_req=1000.0,
        has_no_fx_fee=False,
        has_lounge_access=False
    ),
    Card(
        id="cibc_dividend_vi",
        name="CIBC Dividend Visa Infinite",
        issuer="CIBC",
        network="Visa",
        annual_fee=120.0,
        first_year_fee=0.0,
        earning_rates={
            "grocery": 4.0,
            "gas": 4.0,
            "dining": 2.0,
            "transit": 2.0,
            "recurring": 2.0,
            "other": 1.0
        },
        point_system="cashback",
        welcome_bonus_points=25000, # $250 cashback
        welcome_bonus_spend_req=3000.0,
        has_no_fx_fee=False,
        has_lounge_access=False
    )
]

def get_card_by_id(card_id: str) -> Card:
    return next((c for c in MOCK_CARDS if c.id == card_id), None)
