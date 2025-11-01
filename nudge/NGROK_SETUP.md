# Ngrok Setup Guide for Shopify App

## ✅ What I Fixed

### 1. **Extension API URL Issue** ✅ FIXED
   - **Problem**: The extension was calling `/api/nudge/chat` as a relative path, which would fail when running on the storefront (e.g., `yourstore.myshopify.com`)
   - **Solution**: 
     - Updated `ChatbotPopup.tsx` to read API URL from a data attribute on the block
     - Added `api_url` setting in the extension schema
     - Extension now uses the absolute ngrok URL to call your backend

### 2. **CORS Configuration** ✅ FIXED
   - **Problem**: Backend needed to allow cross-origin requests from Shopify storefronts
   - **Solution**: Added CORS middleware to allow requests from `.myshopify.com` domains

### 3. **Backend-Frontend Connection** ✅ VERIFIED
   - **Status**: ✅ Connected properly
   - The backend serves the frontend in production (`serveStatic` from `/frontend/dist`)
   - In development, Vite dev server proxies to backend
   - Frontend correctly injects `SHOPIFY_API_KEY` from environment

### 4. **Configuration Files** ✅ UPDATED
   - Added comments to `shopify.app.toml` with instructions for ngrok setup
   - Note: `automatically_update_urls_on_dev = true` means Shopify CLI will update URLs automatically during `shopify app dev`

## 📋 What You Need to Do

### Step 1: Set Up Ngrok
```bash
# Install ngrok if you haven't already
# Then run ngrok to forward port 3000 (or your BACKEND_PORT)
ngrok http 3000
```

### Step 2: Update Configuration Files
After starting ngrok, you'll get a URL like: `https://abc123.ngrok.io`

**Update `shopify.app.toml`:**
```toml
application_url = "https://abc123.ngrok.io"
redirect_urls = [ "https://abc123.ngrok.io/api/auth" ]
```

**OR** use `shopify app dev` which will automatically update these URLs if `automatically_update_urls_on_dev = true` is set.

### Step 3: Set Environment Variables
```bash
# Set your Shopify API key
export SHOPIFY_API_KEY="your-api-key-here"

# Optional: Set custom ports (defaults are fine)
export BACKEND_PORT=3000
export FRONTEND_PORT=5173

# If your Python Flask API (Bouncer) is on a different host/port
export BOUNCER_API_URL="http://localhost:5000"
```

### Step 4: Configure Extension in Shopify Admin
1. Go to your Shopify admin → Online Store → Themes → Customize
2. Add the "Nudge Button" block to a section
3. **IMPORTANT**: Set the "API URL" field to your ngrok URL: `https://abc123.ngrok.io`
   - This is the new setting I added - it tells the extension where to find your backend

### Step 5: Start Your Server
```bash
# From project root
npm run dev
# or
yarn dev
```

Or manually:
```bash
# Terminal 1: Start backend
cd web
npm run dev

# Terminal 2: Start frontend (in development)
cd web/frontend
npm run dev
```

## 🔍 How It Works

1. **Backend (`web/index.js`)**:
   - Runs on port 3000 (or `BACKEND_PORT`)
   - Handles Shopify OAuth/auth
   - Serves frontend in production
   - Has API routes: `/api/nudge/chat` (proxies to Python Flask) and `/api/nudge/track`
   - CORS enabled for storefront requests

2. **Frontend (`web/frontend/`)**:
   - React app with Shopify App Bridge
   - In production: served by Express from `/frontend/dist`
   - In development: Vite dev server proxies to backend

3. **Extension (`extensions/nudge-button/`)**:
   - Runs on storefront (customer-facing)
   - Calls your backend via the ngrok URL you configure
   - Makes requests to `${api_url}/api/nudge/chat`

## ⚠️ Important Notes

1. **Ngrok URLs Change**: If you restart ngrok, you'll get a new URL. Update both:
   - `shopify.app.toml` 
   - The extension block setting in Shopify admin

2. **Python Flask API**: Make sure your Python Flask API (Bouncer) is running on the port specified by `BOUNCER_API_URL` (default: `localhost:5000`)

3. **Shopify App Settings**: After updating `shopify.app.toml`, you may need to update your app settings in the Shopify Partners dashboard:
   - App URL: Your ngrok URL
   - Allowed redirection URLs: Your ngrok URL + `/api/auth/callback`

4. **Testing**: 
   - Test the admin app (embedded app in Shopify admin)
   - Test the extension (on your storefront/product pages)
   - Check browser console for any CORS or API errors

## 🚀 Quick Test Checklist

- [ ] Ngrok is running and forwarding to port 3000
- [ ] Backend is running (`npm run dev` or manually)
- [ ] `shopify.app.toml` has your ngrok URL
- [ ] Extension block in Shopify has API URL configured
- [ ] Can access admin app at `https://your-ngrok-url.ngrok.io`
- [ ] Extension appears on storefront
- [ ] Extension chat calls work (check Network tab in browser DevTools)

## 📞 Troubleshooting

**Extension can't reach backend:**
- Verify API URL in extension block settings
- Check CORS headers in Network tab
- Ensure ngrok URL is correct and active

**OAuth/auth not working:**
- Verify `shopify.app.toml` has correct ngrok URL
- Check Shopify Partners dashboard app settings
- Ensure redirect URL includes `/api/auth/callback`

**Frontend not loading:**
- Check if `SHOPIFY_API_KEY` environment variable is set
- Verify frontend is built (`npm run build` in `web/frontend/`)
- Check browser console for errors

