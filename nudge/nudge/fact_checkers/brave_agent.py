"""
Brave search fact-checking agent using Composio MCP.
"""

from typing import Dict, Optional
from composio_client import ComposioClient

class BraveAgent:
    """Agent for fact-checking using Brave search via Composio MCP."""
    
    def __init__(self):
        self.composio = ComposioClient()
        self.app_name = "brave"
    
    def search(self, query: str) -> Dict[str, any]:
        """
        Perform a Brave search query.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with search results including:
            - results: List of search result items
            - summary: Summary of findings
            - success: Boolean indicating if search was successful
        """
        try:
            # Get Composio toolset
            toolset = self.composio.get_toolset()
            
            # Execute Brave search action
            # Note: Adjust this based on actual Composio API for Brave
            # The exact method may vary depending on Composio SDK version
            result = toolset.execute_action(
                app=self.app_name,
                action="search",
                params={"query": query}
            )
            
            return {
                "success": True,
                "results": result.get("results", []),
                "summary": self._format_results(result),
                "query": query
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "summary": f"Failed to search Brave: {str(e)}"
            }
    
    def _format_results(self, result: Dict) -> str:
        """Format search results into a readable summary."""
        if not result or "results" not in result:
            return "No results found."
        
        results = result.get("results", [])
        if not results:
            return "No results found."
        
        summary_parts = []
        for i, item in enumerate(results[:3], 1):  # Top 3 results
            title = item.get("title", "Untitled")
            snippet = item.get("snippet", item.get("description", ""))
            url = item.get("url", "")
            
            summary_parts.append(f"{i}. {title}")
            if snippet:
                summary_parts.append(f"   {snippet[:150]}...")
            if url:
                summary_parts.append(f"   Source: {url}")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def fact_check(self, claim: str) -> Dict[str, any]:
        """
        Fact-check a claim by searching Brave.
        
        Args:
            claim: The claim to verify
            
        Returns:
            Dictionary with fact-check results
        """
        # Enhance query for fact-checking
        query = f"{claim} verification facts"
        
        return self.search(query)

