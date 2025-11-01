"""
Trait detection service - identifies valuable customer traits for discount eligibility.
"""

import re
from typing import Dict, List, Optional
from config_loader import Config

class TraitDetector:
    """Detects valuable customer traits from conversation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.detected_traits: List[str] = []
        self.trait_keywords = self._load_trait_keywords()
    
    def _load_trait_keywords(self) -> Dict[str, List[str]]:
        """Load trait keywords from merchant config."""
        traits_config = self.config.merchant_config.get('valuable_traits', {})
        
        # Use ONLY traits from merchant config - no defaults
        trait_keywords = {}
        
        # Load traits from merchant config
        for trait_name, trait_info in traits_config.items():
            if isinstance(trait_info, dict) and 'keywords' in trait_info:
                trait_keywords[trait_name] = trait_info['keywords']
            elif isinstance(trait_info, list):
                # Legacy format: trait is just a list of keywords
                trait_keywords[trait_name] = trait_info
        
        return trait_keywords
    
    def detect_traits(self, conversation_text: str) -> List[Dict[str, any]]:
        """
        Detect valuable traits from conversation text.
        
        Args:
            conversation_text: Full conversation text or recent messages
            
        Returns:
            List of detected traits with confidence scores
        """
        detected = []
        text_lower = conversation_text.lower()
        
        for trait_name, keywords in self.trait_keywords.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            
            if matches > 0:
                # Calculate confidence based on number of keyword matches
                confidence = min(matches / len(keywords) * 2, 1.0)  # Cap at 1.0
                
                detected.append({
                    'trait': trait_name,
                    'confidence': confidence,
                    'matches': matches
                })
        
        # Sort by confidence (highest first)
        detected.sort(key=lambda x: x['confidence'], reverse=True)
        
        self.detected_traits = [t['trait'] for t in detected]
        return detected
    
    def get_discount_bonus(self, traits: List[Dict[str, any]]) -> float:
        """
        Calculate additional discount percentage based on detected traits.
        
        Args:
            traits: List of detected traits
            
        Returns:
            Additional discount percentage (0-100)
        """
        if not traits:
            return 0.0
        
        traits_config = self.config.merchant_config.get('valuable_traits', {})
        total_bonus = 0.0
        
        for trait_info in traits:
            trait_name = trait_info['trait']
            confidence = trait_info['confidence']
            
            # Get discount bonus for this trait
            trait_config = traits_config.get(trait_name, {})
            
            if isinstance(trait_config, dict):
                bonus_pct = trait_config.get('discount_bonus_pct', 0.0)
            else:
                # Legacy: if trait_config is just a number or list
                bonus_pct = 0.0
            
            # Apply confidence weighting
            weighted_bonus = bonus_pct * confidence
            total_bonus += weighted_bonus
        
        # Cap bonus at reasonable limit (e.g., 10% max bonus)
        max_bonus = self.config.merchant_config.get('max_trait_bonus_pct', 10.0)
        return min(total_bonus, max_bonus)
    
    def has_valuable_trait(self) -> bool:
        """Check if any valuable traits have been detected."""
        return len(self.detected_traits) > 0

