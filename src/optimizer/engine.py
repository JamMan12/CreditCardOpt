from typing import List, Dict, Optional
from ortools.sat.python import cp_model
from src.models.schemas import Card, UserPreferences, WalletRecommendation
from src.data.mock_db import POINT_VALUATIONS

class CreditCardOptimizer:
    def __init__(self, cards: List[Card], user_prefs: UserPreferences):
        self.cards = cards
        self.user_prefs = user_prefs
        
        # Build category index
        self.categories = [cs.category for cs in self.user_prefs.monthly_spend]
        self.annual_spend = {cs.category: int(cs.annual_amount * 100) for cs in self.user_prefs.monthly_spend} # Convert to cents
        
        # Point valuations mapped by system
        self.cpp = POINT_VALUATIONS
        
    def _get_card_value_rate(self, card: Card, category: str) -> float:
        """Returns the value generated per dollar spent in cents."""
        # e.g., 5x points * 2.1 cpp = 10.5 cents per dollar
        multiplier = card.earning_rates.get(category, card.earning_rates.get('other', 1.0))
        val_cpp = self.cpp.get(card.point_system, 1.0)
        return multiplier * val_cpp

    def optimize(self) -> Optional[WalletRecommendation]:
        model = cp_model.CpModel()
        
        # 1. Variables
        # y[c]: 1 if card c is selected, 0 otherwise
        y = {}
        for c in self.cards:
            y[c.id] = model.NewBoolVar(f"y_{c.id}")
            
        # x[c, k]: cents spent on card c in category k
        x = {}
        for c in self.cards:
            for k in self.categories:
                # Max spend on any card in a category is the total category spend
                max_spend = self.annual_spend[k]
                x[c.id, k] = model.NewIntVar(0, max_spend, f"x_{c.id}_{k}")
                
        # 2. Constraints
        # Spend must be fully allocated for each category
        for k in self.categories:
            model.Add(sum(x[c.id, k] for c in self.cards) == self.annual_spend[k])
            
        # Spend on a card can only happen if the card is selected
        for c in self.cards:
            for k in self.categories:
                model.Add(x[c.id, k] <= self.annual_spend[k] * y[c.id])
                
        # Budget constraint: Sum of first year fees <= Max Annual Fee
        # OR Tools requires integer coefficients
        max_fee_cents = int(self.user_prefs.max_annual_fee * 100)
        # Note: CpModel only supports integer coefficients. We will convert fees to integers (cents)
        model.Add(sum(y[c.id] * int(c.effective_first_year_fee * 100) for c in self.cards) <= max_fee_cents)
        
        # Max cards constraint
        model.Add(sum(y[c.id] for c in self.cards) <= self.user_prefs.max_cards)
        
        # Required Perks constraints
        if self.user_prefs.require_no_fx_fee:
            fx_cards = [c.id for c in self.cards if c.has_no_fx_fee]
            if fx_cards:
                model.Add(sum(y[c_id] for c_id in fx_cards) >= 1)
            else:
                return None # Infeasible if no cards have fx fee
                
        if self.user_prefs.require_lounge_access:
            lounge_cards = [c.id for c in self.cards if c.has_lounge_access]
            if lounge_cards:
                model.Add(sum(y[c_id] for c_id in lounge_cards) >= 1)
            else:
                return None
        
        # Welcome Bonus Logic
        # For simplicity, we assume the user meets the minimum spend if it's less than total user spend.
        # A more complex model would track if sum(x[c.id, k]) >= welcome_bonus_spend_req.
        # Since CP-SAT doesn't support float multiplication directly, we multiply later or carefully scale.
        
        total_user_annual_spend = sum(self.annual_spend.values())
        
        # 3. Objective Function
        # Maximize: Rewards from Spend + Welcome Bonuses - Annual Fees
        
        # Since we multiplied spend by 100 (cents) and cpp is cents/point
        # Reward Value (cents) = (Spend in Cents / 100) * Earning Rate * CPP
        # Let's scale the objective function by a factor of 1000 to maintain precision with floats that we convert to ints
        
        # Calculate coefficients for the objective function
        spend_reward_expr = []
        for c in self.cards:
            for k in self.categories:
                # Value generated per 1 dollar spent (in cents)
                val_per_dollar_cents = self._get_card_value_rate(c, k)
                
                # To avoid floats, we multiply the continuous variable `x` by an integer weight.
                # x is already in cents.
                # value_in_cents = (x / 100) * val_per_dollar_cents = x * (val_per_dollar_cents / 100)
                # To make the coefficient integer, we can multiply the whole objective roughly by 1000
                weight = int(val_per_dollar_cents * 10) # 10 = 1000 / 100
                spend_reward_expr.append(x[c.id, k] * weight)
                
        bonus_expr = []
        fee_expr = []
        for c in self.cards:
            # Assume welcome bonus met if total spend > requirement
            val_cpp = self.cpp.get(c.point_system, 1.0)
            bonus_val_cents = c.welcome_bonus_points * val_cpp
            
            # Add bonus term conditionally on card selection (scaled by 1000 to match x weight)
            bonus_weight = int(bonus_val_cents * 10)
            bonus_expr.append(y[c.id] * bonus_weight)
            
            # Subtract fees based on selected cards (scaled by 1000)
            fee_weight = int(c.effective_first_year_fee * 100 * 10)
            fee_expr.append(y[c.id] * fee_weight)
            
        # Maximize the terms
        model.Maximize(sum(spend_reward_expr) + sum(bonus_expr) - sum(fee_expr))
        
        # 4. Solve Configuration
        solver = cp_model.CpSolver()
        # solver.parameters.max_time_in_seconds = 10.0 # Time limit just in case
        status = solver.Solve(model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            selected_cards_out = []
            allocations_out = {k: [] for k in self.categories}
            total_rewards_value_cents = 0.0
            total_wb_value_cents = 0.0
            total_fees_cents = 0.0
            
            for c in self.cards:
                if solver.Value(y[c.id]) == 1:
                    selected_cards_out.append(c)
                    total_fees_cents += c.effective_first_year_fee * 100
                    
                    val_cpp = self.cpp.get(c.point_system, 1.0)
                    total_wb_value_cents += c.welcome_bonus_points * val_cpp
                    
                    for k in self.categories:
                        spend_cents = solver.Value(x[c.id, k])
                        if spend_cents > 0:
                            # Convert back to dollars for output
                            spend_dollars = spend_cents / 100.0
                            allocations_out[k].append((c.id, spend_dollars))
                            
                            val_per_dollar_cents = self._get_card_value_rate(c, k)
                            total_rewards_value_cents += spend_dollars * val_per_dollar_cents
                            
            return WalletRecommendation(
                selected_cards=selected_cards_out,
                spend_allocations=allocations_out,
                total_rewards_value=total_rewards_value_cents / 100.0,
                total_welcome_bonus_value=total_wb_value_cents / 100.0,
                total_annual_fees=total_fees_cents / 100.0
            )
            
        return None # No solution found (infeasible)
