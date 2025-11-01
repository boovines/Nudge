"""
LinkedIn lookup fact-checking agent using Composio MCP.
"""

from typing import Dict, Optional
from composio_client import ComposioClient

class LinkedInAgent:
    """Agent for fact-checking using LinkedIn lookups via Composio MCP."""
    
    def __init__(self):
        self.composio = ComposioClient()
        self.app_name = "linkedin"
    
    def lookup_person(self, name: str, company: Optional[str] = None) -> Dict[str, any]:
        """
        Look up a person on LinkedIn.
        
        Args:
            name: Person's name to search for
            company: Optional company name to narrow search
            
        Returns:
            Dictionary with LinkedIn profile information
        """
        try:
            toolset = self.composio.get_toolset()
            
            # Build search parameters
            params = {"name": name}
            if company:
                params["company"] = company
            
            # Execute LinkedIn lookup action
            # Note: Adjust this based on actual Composio API for LinkedIn
            result = toolset.execute_action(
                app=self.app_name,
                action="search_person",
                params=params
            )
            
            return {
                "success": True,
                "profile": result.get("profile", {}),
                "summary": self._format_profile(result),
                "name": name,
                "company": company
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "name": name,
                "company": company,
                "profile": {},
                "summary": f"Failed to lookup LinkedIn profile: {str(e)}"
            }
    
    def lookup_company(self, company_name: str) -> Dict[str, any]:
        """
        Look up a company on LinkedIn.
        
        Args:
            company_name: Company name to search for
            
        Returns:
            Dictionary with company information
        """
        try:
            toolset = self.composio.get_toolset()
            
            result = toolset.execute_action(
                app=self.app_name,
                action="search_company",
                params={"company": company_name}
            )
            
            return {
                "success": True,
                "company_info": result.get("company", {}),
                "summary": self._format_company(result),
                "company_name": company_name
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "company_name": company_name,
                "company_info": {},
                "summary": f"Failed to lookup LinkedIn company: {str(e)}"
            }
    
    def _format_profile(self, result: Dict) -> str:
        """Format LinkedIn profile into readable summary."""
        if not result or "profile" not in result:
            return "No profile found."
        
        profile = result.get("profile", {})
        parts = []
        
        name = profile.get("name", "Unknown")
        title = profile.get("title", profile.get("headline", ""))
        company = profile.get("company", "")
        location = profile.get("location", "")
        
        parts.append(f"Name: {name}")
        if title:
            parts.append(f"Title: {title}")
        if company:
            parts.append(f"Company: {company}")
        if location:
            parts.append(f"Location: {location}")
        
        return "\n".join(parts) if parts else "Limited profile information available."
    
    def _format_company(self, result: Dict) -> str:
        """Format LinkedIn company info into readable summary."""
        if not result or "company" not in result:
            return "No company found."
        
        company = result.get("company", {})
        parts = []
        
        name = company.get("name", "Unknown")
        industry = company.get("industry", "")
        size = company.get("size", "")
        description = company.get("description", "")
        
        parts.append(f"Company: {name}")
        if industry:
            parts.append(f"Industry: {industry}")
        if size:
            parts.append(f"Size: {size}")
        if description:
            parts.append(f"Description: {description[:200]}...")
        
        return "\n".join(parts) if parts else "Limited company information available."

