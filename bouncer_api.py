"""
Flask API server for Bouncer agent - exposes chat endpoint for Shopify integration.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import os
from bouncer import BouncerAgent

app = Flask(__name__)
CORS(app)  # Enable CORS for Shopify frontend

# Store sessions in memory (in production, use Redis or database)
sessions: dict[str, BouncerAgent] = {}

def get_or_create_session(session_id: str) -> BouncerAgent:
    """Get or create a Bouncer agent session."""
    if session_id not in sessions:
        sessions[session_id] = BouncerAgent(session_id=session_id)
    return sessions[session_id]

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for Shopify chatbot.
    
    Request body:
    {
        "message": "user message",
        "session_id": "optional session id"
    }
    
    Response:
    {
        "response": "bouncer response",
        "session_id": "session id",
        "discount_code": "optional discount code",
        "consent_request": "optional consent prompt"
    }
    """
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get or create session
        session_id = data.get('session_id') or str(uuid.uuid4())
        agent = get_or_create_session(session_id)
        
        # Get response from Bouncer
        response, consent_request = agent.chat(message)
        
        # Build response
        result = {
            'response': response,
            'session_id': session_id,
            'consent_request': consent_request
        }
        
        # Include discount code if available
        if agent.last_discount_code:
            result['discount_code'] = agent.last_discount_code
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.getenv('BOUNCER_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

