"""
Shopify Admin GraphQL API client.
"""

import os
import requests
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from config_loader import Config

class ShopifyClient:
    """Client for Shopify Admin GraphQL API."""
    
    def __init__(self):
        self.config = Config()
        self.shopify_store = os.getenv('SHOPIFY_STORE_DOMAIN')
        self.shopify_access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        
        if not self.shopify_store or not self.shopify_access_token:
            raise ValueError(
                "Shopify credentials not found. Set SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN in .env"
            )
        
        # Ensure store domain doesn't have protocol
        self.shopify_store = self.shopify_store.replace('https://', '').replace('http://', '').strip('/')
        self.api_url = f"https://{self.shopify_store}/admin/api/2024-01/graphql.json"
        self.headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.shopify_access_token
        }
    
    def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query or mutation.
        
        Args:
            query: GraphQL query/mutation string
            variables: Optional variables dictionary
            
        Returns:
            Response dictionary from Shopify API
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Shopify API request failed: {str(e)}")
    
    def create_discount_code(
        self,
        percentage: float,
        code: Optional[str] = None,
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        usage_limit: int = 1,
        minimum_requirements: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a basic discount code in Shopify.
        
        Args:
            percentage: Discount percentage (0-100)
            code: Custom discount code (auto-generated if None)
            starts_at: Start datetime (defaults to now)
            ends_at: End datetime (defaults to 10 minutes from now)
            usage_limit: Number of times code can be used (default: 1)
            minimum_requirements: Optional dict with 'amount' for minimum purchase
            
        Returns:
            Dictionary with discount code info or error
        """
        if starts_at is None:
            starts_at = datetime.now()
        if ends_at is None:
            ends_at = starts_at + timedelta(minutes=10)
        
        # Generate code if not provided
        if code is None:
            import random
            import string
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        mutation = """
        mutation discountCodeBasicCreate($basicCodeDiscount: DiscountCodeBasicInput!) {
            discountCodeBasicCreate(basicCodeDiscount: $basicCodeDiscount) {
                codeDiscountNode {
                    id
                    codeDiscount {
                        ... on DiscountCodeBasic {
                            codes(first: 1) {
                                nodes {
                                    code
                                }
                            }
                            status
                            usageLimit
                            appliesOncePerCustomer
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        
        # Build minimum requirements
        minimum_requirement = None
        if minimum_requirements and 'amount' in minimum_requirements:
            minimum_requirement = {
                "minimumRequirement": {
                    "minimumPurchaseAmount": {
                        "amount": str(minimum_requirements['amount']),
                        "currencyCode": "USD"
                    }
                }
            }
        
        variables = {
            "basicCodeDiscount": {
                "appliesOncePerCustomer": True,
                "code": code,
                "customerSelection": {
                    "all": True
                },
                "customerGets": {
                    "value": {
                        "percentage": {
                            "value": percentage
                        }
                    },
                    "items": {
                        "all": True
                    }
                },
                "startsAt": starts_at.isoformat(),
                "endsAt": ends_at.isoformat(),
                "usageLimit": usage_limit,
                **(minimum_requirement or {})
            }
        }
        
        result = self.execute_query(mutation, variables)
        
        if result.get("errors"):
            return {
                "success": False,
                "error": result["errors"][0].get("message", "Unknown error"),
                "code": None
            }
        
        discount_node = result.get("data", {}).get("discountCodeBasicCreate", {})
        user_errors = discount_node.get("userErrors", [])
        
        if user_errors:
            return {
                "success": False,
                "error": user_errors[0].get("message", "Unknown error"),
                "code": None
            }
        
        code_discount = discount_node.get("codeDiscountNode", {}).get("codeDiscount", {})
        codes = code_discount.get("codes", {}).get("nodes", [])
        actual_code = codes[0].get("code", code) if codes else code
        
        return {
            "success": True,
            "code": actual_code,
            "discount_id": discount_node.get("codeDiscountNode", {}).get("id"),
            "status": code_discount.get("status"),
            "usage_limit": code_discount.get("usageLimit"),
            "expires_at": ends_at.isoformat()
        }

