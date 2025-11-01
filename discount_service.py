"""
Discount code service - creates Shopify discount codes tied to negotiations.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from shopify_client import ShopifyClient
from pricing_service import PricingService
from trait_detector import TraitDetector
from config_loader import Config

class DiscountService:
    """Service for creating and managing Shopify discount codes."""
    
    def __init__(self):
        self.config = Config()
        self.shopify_client = None
        self.pricing_service = PricingService()
        self.trait_detector = TraitDetector(self.config)
        
        # Try to initialize Shopify client, but don't fail if not configured
        try:
            self.shopify_client = ShopifyClient()
        except (ValueError, Exception):
            # Shopify not configured - discount codes will be simulated
            pass
    
    def create_negotiation_discount(
        self,
        session_id: str,
        discount_pct: Optional[float] = None,
        code: Optional[str] = None,
        expires_minutes: int = 10,
        usage_limit: int = 1,
        conversation_text: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Create a discount code for a negotiation.
        
        Args:
            session_id: Session identifier
            discount_pct: Discount percentage (auto-calculated if None)
            code: Custom discount code (auto-generated if None)
            expires_minutes: Minutes until discount expires (default: 10)
            usage_limit: Number of times code can be used (default: 1)
            conversation_text: Conversation text for trait detection
            
        Returns:
            Dictionary with discount code info
        """
        # Detect valuable traits if conversation text provided
        trait_bonus_pct = 0.0
        detected_traits = []
        
        if conversation_text:
            traits = self.trait_detector.detect_traits(conversation_text)
            if traits:
                trait_bonus_pct = self.trait_detector.get_discount_bonus(traits)
                detected_traits = [t['trait'] for t in traits]
        
        # Get or create discount offer with trait bonus
        offer_result = self.pricing_service.make_discount_offer(
            session_id, 
            discount_pct, 
            trait_bonus_pct=trait_bonus_pct
        )
        
        if not offer_result.get("success"):
            return offer_result
        
        discount_pct = offer_result["discount_pct"]
        
        # Create discount code in Shopify
        if self.shopify_client:
            try:
                starts_at = datetime.now()
                ends_at = starts_at + timedelta(minutes=expires_minutes)
                
                result = self.shopify_client.create_discount_code(
                    percentage=discount_pct,
                    code=code,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    usage_limit=usage_limit
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "discount_code": result["code"],
                        "discount_pct": discount_pct,
                        "expires_at": result["expires_at"],
                        "counter": offer_result["counter"],
                        "remaining_counters": offer_result["remaining_counters"],
                        "shopify_id": result.get("discount_id"),
                        "detected_traits": detected_traits,
                        "trait_bonus_applied": offer_result.get("trait_bonus_applied", False),
                        "base_discount_pct": offer_result.get("base_discount_pct", discount_pct)
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Failed to create discount code"),
                        "discount_pct": discount_pct
                    }
            except Exception as e:
                # Shopify API failed, return simulated code
                return self._create_simulated_discount(session_id, discount_pct, code, expires_minutes, offer_result, detected_traits)
        else:
            # Shopify not configured, return simulated code
            return self._create_simulated_discount(session_id, discount_pct, code, expires_minutes, offer_result, detected_traits)
    
    def _create_simulated_discount(
        self,
        session_id: str,
        discount_pct: float,
        code: Optional[str],
        expires_minutes: int,
        offer_result: Dict,
        detected_traits: list
    ) -> Dict[str, any]:
        """Create a simulated discount code when Shopify is not configured."""
        import random
        import string
        
        if code is None:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        expires_at = (datetime.now() + timedelta(minutes=expires_minutes)).isoformat()
        
        return {
            "success": True,
            "discount_code": code,
            "discount_pct": discount_pct,
            "expires_at": expires_at,
            "counter": offer_result["counter"],
            "remaining_counters": offer_result["remaining_counters"],
            "simulated": True,
            "note": "Shopify not configured - this is a simulated discount code",
            "detected_traits": detected_traits,
            "trait_bonus_applied": offer_result.get("trait_bonus_applied", False),
            "base_discount_pct": offer_result.get("base_discount_pct", discount_pct)
        }
    
    def get_negotiation_info(self, session_id: str) -> Dict:
        """Get negotiation information for a session."""
        return self.pricing_service.get_negotiation_summary(session_id)

