# Nudge — Shopify Negotiation Assistant

**Goal:**  
Convert the ~70% of visitors who leave without buying by adding a playful, persona-driven negotiator (“Bouncer”) to Shopify stores. The agent haggles within merchant-set limits, collects lead data, identifies ICPs, and (with consent) follows up via SMS/email.

---

## ⚙️ Architecture

**Frontend:**  
- React/Shopify App Bridge chat widget  
- Triggers: product page, cart, or exit intent  

**Backend:**  
- LLM conversation engine (persona prompt)  
- Negotiation policy service (floors, counters, bundles)  
- Tool calling (MCP → Brave/LinkedIn with consent)  
- Shopify Admin GraphQL API for time-limited discounts  
- Twilio/Klaviyo for compliant SMS/email follow-ups  
- PostgreSQL/Supabase for sessions, offers, leads, consents  
- Merchant dashboard for rules, persona, analytics  

---

## 🧩 Merchant Config Example

```json
{
  "persona": "Bouncer",
  "max_discount_pct": 20,
  "floor_margin_pct": 18,
  "first_offer_pct": 8,
  "counter_step_pct": 3,
  "min_cart_value_for_chat": 35,
  "enable_exit_intent": true,
  "tool_calls": ["brave", "linkedin"],
  "sms_opt_in_enabled": true
}

# 💬 Flow Summary

### 1. Trigger  
User browses or moves to exit → chat opens.

### 2. Negotiate  
Bouncer banters, applies margin rules, and offers a time-limited discount code.

### 3. Capture Intel  
Extract role, company, use case, price sensitivity, and helpful flags (e.g., UGC creator).

### 4. Ask Consent  
> “Want me to text you the deal or future offers? Msg & data rates apply.”  
✅ User must check consent box.

### 5. Double Opt-In  
Send confirmation text (“Reply Y to confirm”).

### 6. Follow-Up  
Text/email a personalized offer or reconsideration message.  
Include “STOP to opt out” on all messages.

---

# 🧱 Data Model

| Table | Key Fields |
|-------|-------------|
| **sessions** | session_id, visitor_id, cart_snapshot, transcript |
| **offers** | offer_id, discount_pct, expires_at, accepted |
| **leads** | email/phone, role, helpful_flags, consent_ts |
| **consents** | phone, consent_text, ip, ts, status |
| **icp_signals** | claims[], icp_score |

---

# 📊 Analytics

- Capture rate = chats / visitors  
- Acceptance rate = offers accepted / negotiations  
- Avg discount % and margin delta  
- Helpful flags discovered (UGC creator, distributor, etc.)  
- Opt-in and SMS conversion rates  

---

# 🧠 Compliance Checklist

- ✅ Explicit consent before any SMS/email  
- ✅ Double opt-in confirmation (reply “Y” to confirm)  
- ✅ “STOP” opt-out on all messages  
- ✅ Encrypt PII and store consent logs securely  
- 🚫 No unsolicited texting or scraping  
- 🚫 No discriminatory dynamic pricing  

---

# 📱 Legal SMS Follow-Up Flow

1. **Exit-intent popup:** Bouncer offers a text follow-up deal with consent checkbox.  
2. **Record consent:** Store consent text, timestamp, IP, and user agent.  
3. **Double opt-in via SMS:**  
   > “Reply Y to confirm you’d like messages from <STORE>. Reply STOP anytime.”  
4. **If confirmed:** Send one-time deal with discount code (Shopify single-use).  
5. **Opt-out support:** Monitor STOP/HELP keywords, update consent status immediately.  
6. **Compliance log retention:** 4+ years (TCPA evidence).  

---

# 🧩 Twilio Example (Double Opt-In)

```js
const twilio = require('twilio')(ACC_SID, AUTH_TOKEN);

await twilio.messages.create({
  body: "Reply Y to confirm opt-in to texts from <STORE>. Reply STOP to cancel.",
  from: TWILIO_NUMBER,
  to: phone
});

# 🧾 Shopify Discount Example

```graphql
mutation discountCodeBasicCreate($input: DiscountCodeBasicInput!) {
  discountCodeBasicCreate(basicCodeDiscount: $input) {
    userErrors { field message }
    discountCode { code }
  }
}
# percentage: 12, startsAt: now, endsAt: now + 10min, usageLimit: 1

# 🚀 MVP Deliverables (2–3 Weeks)

- Chat widget (PDP/Cart/Exit intent)  
- LLM negotiation (3 counters, static rules)  
- Shopify discount code integration  
- Session + lead logging  
- SMS double opt-in + follow-up via Twilio  
- Analytics dashboard (capture rate, conversion, discount usage)  

---

# 🧠 Prompt + Consent Example

### Bouncer Prompt  
> You are “The Bouncer” for `<STORE>`. Be witty and persuasive.  
> Goal: convert while maintaining margin ≥ `<floor_margin_pct>`.  
> Use ≤3 counters. Offer bundles if needed.  
> Ask explicit consent before any external lookup or texting.

### Consent Copy  
> “Yes — text me one-time offers & deals. Msg/data rates apply.  
> Reply STOP to opt out. By entering my phone, I consent to receive messages from `<STORE>`.”

---

# 🔒 Privacy & Security

- Encrypt all PII (AES-256)  
- Limit internal access  
- Allow deletion/export requests (GDPR/CCPA)  
- Store consent text for each user  
- Respect MAP and platform pricing policies  

---

# 🧠 ICP Learning

- Extract keywords (role, budget, region, intent) from chat transcripts.  
- Cluster embeddings → discover top buyer personas.  
- Flag “helpful” leads (e.g., UGC creators) for merchant follow-up.  
- Export data to CRM or CSV.  

---

# 📦 Next Steps

Generate:
- Prompt pack (Bouncer/Concierge/Friendly)  
- GraphQL snippets (Shopify discounts)  
- React widget skeleton (chat + opt-in modal)  
- Twilio endpoints (double opt-in + STOP handling)  
- SQL schema (sessions, offers, leads, consents)  

---

# 🧾 TL;DR

AI Bouncer negotiates conversationally, captures leads and ICP data, and—only after verified consent—texts or emails personalized offers to recover lost sales, staying fully compliant.

---

# 🚀 Terminal Chat Setup

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys:
   # - OPENAI_API_KEY or ANTHROPIC_API_KEY (required)
   # - COMPOSIO_API_KEY (optional, for fact-checking)
   # - SHOPIFY_STORE_DOMAIN (optional, e.g., "your-store.myshopify.com")
   # - SHOPIFY_ACCESS_TOKEN (optional, Admin API access token)
   # - STORE_NAME (optional, defaults to config)
   ```

3. **Configure merchant settings:**
   Edit `config/merchant_config.json` with your store settings.

4. **Run the chat:**
   ```bash
   python chat.py
   ```

## Features

- **Interactive Terminal Chat**: Chat with The Bouncer persona in your terminal
- **Pricing Negotiation**: Automatic discount code generation with merchant-set limits
- **Shopify Integration**: Creates real discount codes in Shopify (optional)
- **Negotiation Limits**: Enforces max discount %, floor margin %, and counter limits
- **Fact-Checking Agents**: Brave search and LinkedIn lookup via Composio MCP (optional)
- **Consent Flow**: Explicit consent prompts before any external lookups
- **Conversation Memory**: Maintains context throughout the conversation

## Usage Example

```
You: This is too expensive, can you give me a discount?
Bouncer: [responds with personality and offers discount code]
Bouncer: Here's your discount code: ABC12345 - 8% off! Expires in 10 minutes.

You: Can you do better?
Bouncer: [counters with higher discount, up to max limit]
```

## Shopify Setup (Optional)

To enable real Shopify discount codes:

1. Create a Shopify Admin API access token:
   - Go to Shopify Admin → Settings → Apps and sales channels → Develop apps
   - Create a custom app with `write_discounts` scope
   - Copy the Admin API access token

2. Add to `.env`:
   ```
   SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
   SHOPIFY_ACCESS_TOKEN=your_access_token_here
   ```

3. Without Shopify configured, the system will generate simulated discount codes that still enforce pricing limits.

## Requirements

- Python 3.8+
- OpenAI or Anthropic API key (required)
- Shopify credentials (optional, for real discount codes)
- Composio API key (optional, for fact-checking features)
- See `requirements.txt` for Python dependencies

## Project Structure

```
nudge/
├── chat.py                 # Main terminal chat interface
├── bouncer.py              # Bouncer LLM agent with fact-checking
├── agent_router.py         # Routes to fact-checking agents
├── composio_client.py      # Composio MCP client wrapper
├── shopify_client.py       # Shopify Admin GraphQL API client
├── pricing_service.py      # Pricing negotiation with limits
├── discount_service.py     # Discount code creation service
├── config_loader.py        # Configuration management
├── config/
│   ├── merchant_config.json
│   └── prompts/
│       └── bouncer_prompt.txt
└── fact_checkers/
    ├── brave_agent.py      # Brave search agent
    └── linkedin_agent.py   # LinkedIn lookup agent
```
