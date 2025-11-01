"""
Agent router - detects when fact-checking is needed and orchestrates micro-agents.
"""

import re
from typing import Dict, Optional, Tuple
from fact_checkers.brave_agent import BraveAgent
from fact_checkers.linkedin_agent import LinkedInAgent
from config_loader import Config

class AgentRouter:
    """Routes requests to appropriate fact-checking agents based on context."""
    
    def __init__(self):
        self.config = Config()
        # Initialize agents only if Composio is configured and tool is enabled
        self.brave_agent = None
        self.linkedin_agent = None
        
        if "brave" in self.config.tool_calls:
            try:
                self.brave_agent = BraveAgent()
            except (ValueError, ImportError, RuntimeError) as e:
                # Composio not configured, agent will be None
                pass
        
        if "linkedin" in self.config.tool_calls:
            try:
                self.linkedin_agent = LinkedInAgent()
            except (ValueError, ImportError, RuntimeError) as e:
                # Composio not configured, agent will be None
                pass
    
    def detect_fact_check_needed(self, user_message: str, conversation_context: str = "") -> Optional[Dict]:
        """
        Detect if fact-checking is needed based on user message.
        
        Returns:
            Dictionary with detection results:
            - needed: bool
            - agent_type: 'brave' or 'linkedin' or None
            - query: extracted query/claim
            - confidence: confidence level (0.0 to 1.0)
        """
        message_lower = user_message.lower()
        context_lower = conversation_context.lower()
        
        # Patterns that suggest fact-checking is needed
        fact_check_patterns = [
            r"i (work|am) at (.+)",
            r"i'm (a|an) (.+)",
            r"my company is (.+)",
            r"(.+) (is|are) (a|an) (.+)",
            r"according to (.+)",
            r"i (read|heard|saw) (.+)",
            r"(.+) (said|claims|stated) (.+)",
            r"(.+) (has|have) (.+)",
        ]
        
        # LinkedIn lookup patterns
        linkedin_patterns = [
            r"i work at (.+)",
            r"my company is (.+)",
            r"i'm (a|an) (.+) at (.+)",
            r"look up (.+) on linkedin",
            r"find (.+) on linkedin",
        ]
        
        # Brave search patterns
        brave_patterns = [
            r"(.+) (is|are) (.+)",
            r"according to (.+)",
            r"i (read|heard|saw) (.+)",
            r"(.+) (said|claims|stated) (.+)",
        ]
        
        # Check for LinkedIn patterns first
        for pattern in linkedin_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                query = match.group(1) if match.groups() else user_message
                return {
                    "needed": True,
                    "agent_type": "linkedin",
                    "query": query,
                    "confidence": 0.7,
                    "extracted_info": self._extract_linkedin_info(user_message)
                }
        
        # Check for Brave search patterns
        for pattern in brave_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                query = user_message  # Use full message as query
                return {
                    "needed": True,
                    "agent_type": "brave",
                    "query": query,
                    "confidence": 0.6,
                    "claim": user_message
                }
        
        # Check for general fact-check patterns
        for pattern in fact_check_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                return {
                    "needed": True,
                    "agent_type": "brave",
                    "query": user_message,
                    "confidence": 0.5,
                    "claim": user_message
                }
        
        return {
            "needed": False,
            "agent_type": None,
            "query": None,
            "confidence": 0.0
        }
    
    def _extract_linkedin_info(self, message: str) -> Dict[str, Optional[str]]:
        """Extract person/company info from message."""
        # Simple extraction - can be enhanced with NLP
        info = {
            "name": None,
            "company": None,
            "title": None
        }
        
        # Look for "I work at X" or "I'm Y at X"
        work_at_match = re.search(r"i work at (.+)", message.lower())
        if work_at_match:
            info["company"] = work_at_match.group(1).strip()
        
        # Look for "I'm X at Y"
        title_match = re.search(r"i'm (a|an) (.+?) at (.+)", message.lower())
        if title_match:
            info["title"] = title_match.group(2).strip()
            info["company"] = title_match.group(3).strip()
        
        return info
    
    def execute_fact_check(self, agent_type: str, query: str, context: Optional[Dict] = None) -> Dict:
        """
        Execute fact-check using the appropriate agent.
        
        Args:
            agent_type: 'brave' or 'linkedin'
            query: Query or claim to fact-check
            context: Optional context dictionary
            
        Returns:
            Dictionary with fact-check results
        """
        if agent_type == "brave" and self.brave_agent:
            return self.brave_agent.fact_check(query)
        
        elif agent_type == "linkedin" and self.linkedin_agent:
            if context and context.get("extracted_info"):
                info = context["extracted_info"]
                if info.get("company"):
                    if info.get("name"):
                        return self.linkedin_agent.lookup_person(
                            name=info["name"],
                            company=info["company"]
                        )
                    else:
                        return self.linkedin_agent.lookup_company(company_name=info["company"])
                elif info.get("name"):
                    return self.linkedin_agent.lookup_person(name=info["name"])
            
            # Fallback: try to extract from query
            return self.linkedin_agent.lookup_person(name=query)
        
        else:
            return {
                "success": False,
                "error": f"Agent type '{agent_type}' not available or not configured",
                "agent_type": agent_type
            }
    
    def should_ask_consent(self, detection_result: Dict) -> bool:
        """Determine if user consent should be asked before fact-checking."""
        if not detection_result.get("needed", False):
            return False
        
        agent_type = detection_result.get("agent_type")
        # Only ask consent if agent is actually available
        if agent_type == "brave" and not self.brave_agent:
            return False
        if agent_type == "linkedin" and not self.linkedin_agent:
            return False
        
        return detection_result.get("confidence", 0) >= 0.5

