# Quick Start: Connect Bouncer to Shopify Chatbot

## Setup Steps

### 1. Install Python Dependencies

```bash
cd /Users/justinhou/Development/Nudge
pip install -r requirements.txt
```

### 2. Configure Environment

Ensure your `.env` file has:
```bash
OPENAI_API_KEY=your_key_here
```

For the Shopify app, set (in `nudge` folder or environment):
```bash
BOUNCER_API_URL=http://localhost:5000
```

### 3. Start Python Bouncer API

```bash
cd /Users/justinhou/Development/Nudge
python bouncer_api.py
```

You should see: `Running on http://0.0.0.0:5000`

### 4. Start Shopify App

In a new terminal:
```bash
cd /Users/justinhou/Development/Nudge/nudge
npm run dev
```

### 5. Test the Integration

1. Open your Shopify storefront
2. Click the Nudge button to open chat
3. Try: "Can I get a discount? I am a beauty influencer"
4. The Bouncer should respond with a discount code

## API Flow

```
Storefront Chatbot → /api/nudge/chat → Python Flask API → Bouncer Agent
```

## Files Modified

- `bouncer_api.py` - New Flask API server
- `nudge/web/index.js` - Added proxy endpoint
- `nudge/extensions/nudge-button/assets/src/ChatbotPopup.tsx` - Updated to call API

## Troubleshooting

- **"Failed to connect"**: Make sure Python API is running on port 5000
- **No discount codes**: Customer must mention traits (beauty influencer, salon owner, etc.)
- **CORS errors**: Flask-CORS should handle this automatically

