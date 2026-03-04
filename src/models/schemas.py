from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Card(BaseModel):
    id: str
    name: str
    issuer: str
    network: str # Visa, Mastercard, Amex
    annual_fee: float
    first_year_fee: Optional[float] = None
    
    # Earning rates per category. Key represents the spending category (e.g., 'dining', 'grocery', 'travel', 'gas', 'transit', 'other')
    # Value is the multiplier (e.g., 5.0 means 5x points per dollar spent)
    earning_rates: Dict[str, float]
    
    # Points system the card earns (e.g., 'aeroplan', 'amex_mr', 'mbna_rewards')
    point_system: str
    
    # Welcome Bonus details
    welcome_bonus_points: int = 0
    welcome_bonus_spend_req: float = 0
    
    # Perks
    has_no_fx_fee: bool = False
    has_lounge_access: bool = False
    
    @property
    def effective_first_year_fee(self) -> float:
        """Returns the first year fee if defined, otherwise the annual fee."""
        fee = self.first_year_fee
        if fee is not None:
            return fee
        return self.annual_fee

class PointValuation(BaseModel):
    system: str
    cpp_value: float # Cents Per Point (e.g., 2.1 for Aeroplan)

class CategorySpend(BaseModel):
    category: str
    monthly_amount: float
    
    @property
    def annual_amount(self) -> float:
        return self.monthly_amount * 12

class UserPreferences(BaseModel):
    monthly_spend: List[CategorySpend]
    max_annual_fee: float = Field(default=float('inf'), description="Maximum total annual fee willing to pay")
    max_cards: int = Field(default=3, description="Maximum number of cards in wallet")
    
    # Required Perks
    require_no_fx_fee: bool = False
    require_lounge_access: bool = False

class WalletRecommendation(BaseModel):
    selected_cards: List[Card]
    # Mapping of category name to the List of tuples (Card ID, Amount Allocated)
    # E.g. {'grocery': [('amex_cobalt', 6000)]}
    spend_allocations: Dict[str, List[tuple[str, float]]]
    
    total_rewards_value: float
    total_welcome_bonus_value: float
    total_annual_fees: float
    
    @property
    def net_first_year_value(self) -> float:
        """Total value in the first year including welcome bonuses, minus first year fees."""
        # Calculating net first year value accurately requires knowing the exact first year fees of selected cards
        # We will compute this in the optimizer output
        return 0.0
    
    @property
    def net_second_year_value(self) -> float:
        return self.total_rewards_value - self.total_annual_fees
