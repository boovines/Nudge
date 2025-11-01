# Integration Guide: Connecting Bouncer Agent to Shopify Chatbot

## Overview
This setup connects the Python Bouncer negotiation agent to the Shopify chatbot UI.

## Architecture

```
Shopify Storefront (Chatbot UI)
    ↓
Node.js Express Server (/api/nudge/chat)
    ↓
Python Flask API (bouncer_api.py)
    ↓
Bouncer Agent (bouncer.py)
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
cd /Users/justinhou/Development/Nudge
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create/update `.env` file in the root directory:

```bash
# OpenAI API (required)
OPENAI_API_KEY=your_openai_api_key

# Shopify (optional, for real discount codes)
SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_access_token

# Bouncer API Port (optional, defaults to 5000)
BOUNCER_PORT=5000
```

In the `nudge` folder, update `.env` or environment:

```bash
# URL to Python Bouncer API
BOUNCER_API_URL=http://localhost:5000
```

### 3. Start Python Bouncer API

```bash
cd /Users/justinhou/Development/Nudge
python bouncer_api.py
```

The API will run on `http://localhost:5000` by default.

### 4. Start Shopify App

```bash
cd /Users/justinhou/Development/Nudge/nudge
npm run dev
```

### 5. Test the Integration

1. Open your Shopify storefront
2. The chatbot should appear via the Nudge button extension
3. Start chatting - messages will be sent to the Bouncer agent
4. The Bouncer will respond with judgmental, skeptical responses
5. Discount codes will be generated when traits are detected

## API Endpoints

### Python Flask API (`bouncer_api.py`)

- `POST /api/chat` - Chat endpoint
  - Request: `{ "message": "user message", "session_id": "optional" }`
  - Response: `{ "response": "bouncer reply", "session_id": "id", "discount_code": "optional", "consent_request": "optional" }`
- `GET /health` - Health check

### Node.js Proxy (`/api/nudge/chat`)

- Proxies requests to Python Flask API
- Handles errors gracefully
- Returns responses to frontend

## Features

- ✅ Session management (persists conversation state)
- ✅ Trait detection (beauty influencer, salon professional, etc.)
- ✅ Discount code generation (only when traits detected)
- ✅ Consent flow (for fact-checking)
- ✅ Error handling

## Development

### Running Both Servers

Terminal 1 (Python API):
```bash
cd /Users/justinhou/Development/Nudge
python bouncer_api.py
```

Terminal 2 (Shopify App):
```bash
cd /Users/justinhou/Development/Nudge/nudge
npm run dev
```

### Testing the API Directly

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Can I get a discount? I am a beauty influencer"}'
```

## Troubleshooting

1. **Chat not responding**: Check if Python API is running on port 5000
2. **CORS errors**: Ensure Flask-CORS is installed and configured
3. **Discount codes not appearing**: Check if traits are detected (beauty influencer, salon professional, etc.)
4. **Session not persisting**: Check browser sessionStorage

## Next Steps

- Add Redis/database for session persistence
- Add rate limiting
- Add logging and monitoring
- Deploy Python API to production server

