"""
Bouncer LLM Agent - Handles conversation with the negotiator persona.
"""

import os
import uuid
from typing import List, Dict, Optional, Tuple
from config_loader import Config
from agent_router import AgentRouter
from discount_service import DiscountService
from trait_detector import TraitDetector

class BouncerAgent:
    """Manages conversation with the Bouncer persona using LLM."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.config = Config()
        self.session_id = session_id or str(uuid.uuid4())
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self.config.get_persona_prompt()
        self.llm_client = self._initialize_llm_client()
        self.agent_router = AgentRouter()
        self.discount_service = DiscountService()
        self.trait_detector = TraitDetector(self.config)
        self.pending_fact_check: Optional[Dict] = None
        self.last_discount_code: Optional[str] = None
        
        # Add system prompt to conversation history
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })
    
    def _initialize_llm_client(self):
        """Initialize LLM client based on available API keys."""
        # Prefer OpenAI if available, otherwise Anthropic
        if self.config.openai_api_key:
            try:
                from openai import OpenAI
                return OpenAI(api_key=self.config.openai_api_key)
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")
        
        elif self.config.anthropic_api_key:
            try:
                from anthropic import Anthropic
                return Anthropic(api_key=self.config.anthropic_api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        
        else:
            raise ValueError(
                "No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env file"
            )
    
    def chat(self, user_message: str) -> Tuple[str, Optional[str]]:
        """
        Process user message and return Bouncer's response.
        
        Returns:
            Tuple of (response, consent_request)
            - response: Bouncer's response message
            - consent_request: Optional consent prompt if fact-checking is needed
        """
        # Check if this is a consent response
        if self.pending_fact_check and self._is_consent_response(user_message):
            return self._handle_consent_response(user_message)
        
        # Check if user is asking for discount or negotiating price
        negotiation_context = self._detect_negotiation_intent(user_message)
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Detect if fact-checking is needed
        conversation_context = self._get_conversation_context()
        detection = self.agent_router.detect_fact_check_needed(user_message, conversation_context)
        
        # Detect traits FIRST - only offer discount if traits are detected
        conversation_text = self._get_conversation_context()
        detected_traits = self.trait_detector.detect_traits(conversation_text)
        
        # Only offer discount if:
        # 1. User is negotiating AND
        # 2. Valuable traits are detected
        should_offer = negotiation_context.get("should_offer_discount") and len(detected_traits) > 0
        
        if should_offer:
            discount_info = self._create_discount_offer(conversation_text)
            
            if discount_info.get("success"):
                # Build discount context with trait info - keep it brief and dismissive
                detected_traits_list = discount_info.get("detected_traits", [])
                trait_note = ""
                
                if detected_traits_list:
                    trait_names = ", ".join(detected_traits_list)
                    if discount_info.get("trait_bonus_applied"):
                        trait_note = f" They claim to be {trait_names[0]}. Fine, I'll give them {discount_info['discount_pct']}% instead of {discount_info.get('base_discount_pct', discount_info['discount_pct'])}%."
                    else:
                        trait_note = f" They claim to be {trait_names[0]}. I'm skeptical."
                
                discount_context = (
                    f"[Discount Available]: Code '{discount_info['discount_code']}' - {discount_info['discount_pct']}% off. "
                    f"Expires in 10 min. Counter: {discount_info['counter']}/3.{trait_note}"
                )
                
                self.conversation_history.append({
                    "role": "system",
                    "content": discount_context
                })
                self.last_discount_code = discount_info['discount_code']
        elif negotiation_context.get("should_offer_discount") and len(detected_traits) == 0:
            # User is asking for discount but no traits detected - add context to probe
            probe_context = (
                "[No Discount Yet]: Customer asked for discount but hasn't provided valuable traits. "
                "Probe them: 'What makes you special? Are you a beauty influencer? Salon owner? Distributor? "
                "Otherwise, prices are what they are.'"
            )
            self.conversation_history.append({
                "role": "system",
                "content": probe_context
            })
        
        # Get response from LLM
        response = self._get_llm_response()
        
        # If fact-checking is needed and consent should be asked, prepare consent request
        consent_request = None
        if detection.get("needed") and self.agent_router.should_ask_consent(detection):
            self.pending_fact_check = detection
            agent_type = detection.get("agent_type")
            if agent_type == "brave":
                consent_request = f"Can I verify that on Brave search? (yes/no)"
            elif agent_type == "linkedin":
                consent_request = f"Can I look that up on LinkedIn? (yes/no)"
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response, consent_request
    
    def _detect_negotiation_intent(self, user_message: str) -> Dict[str, any]:
        """Detect if user is negotiating or asking for discounts."""
        message_lower = user_message.lower()
        
        negotiation_keywords = [
            "discount", "deal", "cheaper", "lower price", "reduce", "haggle",
            "negotiate", "offer", "promo", "coupon", "code", "save money",
            "too expensive", "price", "cost", "afford"
        ]
        
        for keyword in negotiation_keywords:
            if keyword in message_lower:
                return {
                    "should_offer_discount": True,
                    "intent": "negotiation"
                }
        
        return {
            "should_offer_discount": False,
            "intent": "general"
        }
    
    def _create_discount_offer(self, conversation_text: Optional[str] = None) -> Dict[str, any]:
        """Create a discount offer for the current session."""
        try:
            return self.discount_service.create_negotiation_discount(
                session_id=self.session_id,
                discount_pct=None,
                expires_minutes=10,
                conversation_text=conversation_text
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_consent_response(self, user_message: str) -> Tuple[str, Optional[str]]:
        """Handle user's consent response."""
        if not self.pending_fact_check:
            return "I don't have a pending fact-check request.", None
        
        # Check if consent was given
        user_lower = user_message.lower().strip()
        consent_given = user_lower in ['yes', 'y', 'yeah', 'sure', 'ok', 'okay', 'go ahead']
        
        if consent_given:
            # Execute fact-check
            detection = self.pending_fact_check
            agent_type = detection.get("agent_type")
            query = detection.get("query")
            context = detection.get("extracted_info")
            
            fact_check_result = self.agent_router.execute_fact_check(
                agent_type=agent_type,
                query=query,
                context={"extracted_info": context} if context else None
            )
            
            # Add fact-check result to conversation context
            fact_check_summary = f"[Fact-check result via {agent_type}]: {fact_check_result.get('summary', 'No results found')}"
            
            self.conversation_history.append({
                "role": "system",
                "content": fact_check_summary
            })
            
            # Get updated response from LLM with fact-check context
            response = self._get_llm_response()
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            self.pending_fact_check = None
            return response, None
        else:
            # Consent denied
            self.conversation_history.append({
                "role": "assistant",
                "content": "No problem, I won't look that up. How else can I help you?"
            })
            self.pending_fact_check = None
            return "No problem, I won't look that up. How else can I help you?", None
    
    def _is_consent_response(self, user_message: str) -> bool:
        """Check if user message is a response to a consent request."""
        return self.pending_fact_check is not None
    
    def _get_conversation_context(self) -> str:
        """Get recent conversation context as a string."""
        # Get last 6 messages for context
        recent_messages = [
            msg.get("content", "") 
            for msg in self.conversation_history[-6:] 
            if msg.get("role") in ["user", "assistant"]
        ]
        return " ".join(recent_messages)
    
    def _get_llm_response(self) -> str:
        """Call LLM API and return response."""
        # Check if using OpenAI or Anthropic
        if hasattr(self.llm_client, 'chat'):
            # OpenAI client
            response = self.llm_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=150  # Reduced from 500 for shorter responses
            )
            return response.choices[0].message.content.strip()
        
        elif hasattr(self.llm_client, 'messages'):
            # Anthropic client
            # Filter out system message (Anthropic handles it differently)
            messages = [
                msg for msg in self.conversation_history 
                if msg['role'] != 'system'
            ]
            
            response = self.llm_client.messages.create(
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
                max_tokens=150,  # Reduced from 500 for shorter responses
                system=self.system_prompt,
                messages=messages
            )
            return response.content[0].text.strip()
        
        else:
            raise ValueError("Unknown LLM client type")
