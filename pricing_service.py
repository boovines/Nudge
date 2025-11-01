"""
Pricing negotiation service - enforces merchant limits and tracks negotiation state.
"""

from typing import Dict, Optional, List
from datetime import datetime
from config_loader import Config

class NegotiationState:
    """Tracks the state of a single negotiation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.counter = 0
        self.max_counters = 3
        self.current_discount_pct = 0.0
        self.offers: List[Dict] = []
        self.started_at = datetime.now()
    
    def can_make_counter(self) -> bool:
        """Check if another counter offer can be made."""
        return self.counter < self.max_counters
    
    def make_offer(self, discount_pct: float) -> Dict[str, any]:
        """
        Make a discount offer.
        
        Args:
            discount_pct: Discount percentage to offer
            
        Returns:
            Dictionary with offer details and validation status
        """
        # Validate discount is within limits
        if discount_pct > self.config.max_discount_pct:
            return {
                "success": False,
                "error": f"Discount {discount_pct}% exceeds maximum {self.config.max_discount_pct}%",
                "discount_pct": None
            }
        
        # Check if we've exceeded counter limit
        if self.counter >= self.max_counters:
            return {
                "success": False,
                "error": f"Maximum {self.max_counters} counters reached",
                "discount_pct": None
            }
        
        # Calculate margin
        margin_pct = 100 - discount_pct
        if margin_pct < self.config.floor_margin_pct:
            return {
                "success": False,
                "error": f"Discount {discount_pct}% would result in margin {margin_pct}% below floor {self.config.floor_margin_pct}%",
                "discount_pct": None
            }
        
        # Offer is valid
        self.counter += 1
        self.current_discount_pct = discount_pct
        
        offer = {
            "counter": self.counter,
            "discount_pct": discount_pct,
            "margin_pct": margin_pct,
            "timestamp": datetime.now().isoformat()
        }
        self.offers.append(offer)
        
        return {
            "success": True,
            "discount_pct": discount_pct,
            "margin_pct": margin_pct,
            "counter": self.counter,
            "remaining_counters": self.max_counters - self.counter
        }
    
    def get_next_offer(self, previous_discount: Optional[float] = None) -> Dict[str, any]:
        """
        Calculate the next counter offer based on negotiation strategy.
        
        Args:
            previous_discount: Previous discount offered (for incremental increases)
            
        Returns:
            Offer dictionary
        """
        if self.counter == 0:
            # First offer
            discount = self.config.first_offer_pct
        elif previous_discount is not None:
            # Increment from previous offer
            discount = previous_discount + self.config.counter_step_pct
        else:
            # Increment from current offer
            discount = self.current_discount_pct + self.config.counter_step_pct
        
        # Ensure we don't exceed max
        discount = min(discount, self.config.max_discount_pct)
        
        return self.make_offer(discount)
    
    def get_summary(self) -> Dict:
        """Get summary of negotiation state."""
        return {
            "counter": self.counter,
            "max_counters": self.max_counters,
            "current_discount_pct": self.current_discount_pct,
            "remaining_counters": self.max_counters - self.counter,
            "can_continue": self.can_make_counter(),
            "offers": self.offers
        }

class PricingService:
    """Service for managing pricing negotiations."""
    
    def __init__(self):
        self.config = Config()
        self.negotiations: Dict[str, NegotiationState] = {}
    
    def get_negotiation(self, session_id: str) -> NegotiationState:
        """Get or create a negotiation state for a session."""
        if session_id not in self.negotiations:
            self.negotiations[session_id] = NegotiationState(self.config)
        return self.negotiations[session_id]
    
    def make_discount_offer(self, session_id: str, discount_pct: Optional[float] = None, trait_bonus_pct: float = 0.0) -> Dict[str, any]:
        """
        Make a discount offer for a session.
        
        Args:
            session_id: Session identifier
            discount_pct: Specific discount to offer (None for auto-calculation)
            trait_bonus_pct: Additional discount percentage from valuable traits
            
        Returns:
            Offer dictionary
        """
        negotiation = self.get_negotiation(session_id)
        
        if discount_pct is None:
            # Auto-calculate next offer
            previous_discount = negotiation.current_discount_pct if negotiation.offers else None
            result = negotiation.get_next_offer(previous_discount)
        else:
            # Specific discount requested
            result = negotiation.make_offer(discount_pct)
        
        # Apply trait bonus if offer was successful
        if result.get("success") and trait_bonus_pct > 0:
            base_discount = result["discount_pct"]
            bonus_discount = base_discount + trait_bonus_pct
            
            # Ensure trait bonus doesn't exceed max discount
            max_allowed = self.config.max_discount_pct
            final_discount = min(bonus_discount, max_allowed)
            
            # Only update if bonus actually applies
            if final_discount > base_discount:
                # Check if final discount would violate floor margin
                final_margin = 100 - final_discount
                if final_margin >= self.config.floor_margin_pct:
                    # Update the current offer with bonus (don't increment counter again)
                    negotiation.current_discount_pct = final_discount
                    # Update the last offer in the list
                    if negotiation.offers:
                        negotiation.offers[-1]["discount_pct"] = final_discount
                        negotiation.offers[-1]["margin_pct"] = final_margin
                    
                    result["discount_pct"] = final_discount
                    result["margin_pct"] = final_margin
                    result["trait_bonus_applied"] = True
                    result["base_discount_pct"] = base_discount
                    result["trait_bonus_pct"] = trait_bonus_pct
        
        return result
    
    def can_negotiate(self, session_id: str) -> bool:
        """Check if negotiation can continue for a session."""
        negotiation = self.get_negotiation(session_id)
        return negotiation.can_make_counter()
    
    def get_negotiation_summary(self, session_id: str) -> Dict:
        """Get summary of negotiation state."""
        negotiation = self.get_negotiation(session_id)
        return negotiation.get_summary()

