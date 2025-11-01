import json
import os
from pathlib import Path

class Config:
    """Loads and manages configuration from merchant_config.json and environment variables."""
    
    def __init__(self):
        # Get the directory where this file is located
        script_dir = Path(__file__).parent.absolute()
        # Config files are in the config/ directory relative to the script
        self.config_path = script_dir / "config" / "merchant_config.json"
        self.load_config()
        self.load_env()
    
    def load_config(self):
        """Load merchant configuration from JSON file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.merchant_config = json.load(f)
        else:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
    
    def load_env(self):
        """Load environment variables."""
        from dotenv import load_dotenv
        load_dotenv()
        
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.composio_api_key = os.getenv('COMPOSIO_API_KEY')
        self.store_name = os.getenv('STORE_NAME', self.merchant_config.get('store_name', 'Your Store'))
        
        # Shopify credentials
        self.shopify_store_domain = os.getenv('SHOPIFY_STORE_DOMAIN')
        self.shopify_access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    def get_persona_prompt(self):
        """Load and format the Bouncer persona prompt."""
        script_dir = Path(__file__).parent.absolute()
        prompt_path = script_dir / "config" / "prompts" / "bouncer_prompt.txt"
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                prompt = f.read()
            
            # Replace placeholders with actual values
            prompt = prompt.replace('<STORE_NAME>', self.store_name)
            prompt = prompt.replace('<floor_margin_pct>', str(self.merchant_config.get('floor_margin_pct', 18)))
            prompt = prompt.replace('<max_discount_pct>', str(self.merchant_config.get('max_discount_pct', 20)))
            prompt = prompt.replace('<first_offer_pct>', str(self.merchant_config.get('first_offer_pct', 8)))
            prompt = prompt.replace('<counter_step_pct>', str(self.merchant_config.get('counter_step_pct', 3)))
            
            return prompt
        else:
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    @property
    def max_discount_pct(self):
        return self.merchant_config.get('max_discount_pct', 20)
    
    @property
    def floor_margin_pct(self):
        return self.merchant_config.get('floor_margin_pct', 18)
    
    @property
    def tool_calls(self):
        return self.merchant_config.get('tool_calls', [])
    
    @property
    def first_offer_pct(self):
        return self.merchant_config.get('first_offer_pct', 8)
    
    @property
    def counter_step_pct(self):
        return self.merchant_config.get('counter_step_pct', 3)

