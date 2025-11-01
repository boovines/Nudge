// @ts-check
import { join } from "path";
import { readFileSync } from "fs";
import express from "express";
import serveStatic from "serve-static";

import shopify from "./shopify.js";
import productCreator from "./product-creator.js";
import PrivacyWebhookHandlers from "./privacy.js";

const PORT = parseInt(process.env.BACKEND_PORT || process.env.PORT || "3000", 10);

const STATIC_PATH =
  process.env.NODE_ENV === "production"
    ? `${process.cwd()}/frontend/dist`
    : `${process.cwd()}/frontend/`;

const app = express();

// Parse JSON for API routes
app.use(express.json());

// Bouncer chat API proxy (forwards to Python Flask API)
const BOUNCER_API_URL = process.env.BOUNCER_API_URL || "http://localhost:5000";

app.post("/api/nudge/chat", async (req, res) => {
  try {
    const response = await fetch(`${BOUNCER_API_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body)
    });

    if (!response.ok) {
      throw new Error(`Bouncer API error: ${response.status}`);
    }

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error("Bouncer API proxy error:", error);
    res.status(500).json({ 
      error: "Failed to connect to chat service",
      response: "Sorry, I'm having trouble right now. Please try again."
    });
  }
});

/**
 * Public tracking endpoint for storefront beacons.
 * Accepts sendBeacon (text/plain) and JSON fetch. No auth required.
 */
app.options("/api/nudge/track", (req, res) => {
  res.set({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  });
  res.sendStatus(204);
});

app.post(
  "/api/nudge/track",
  // Parse either text/plain or application/json
  (req, res, next) => {
    const ct = req.headers["content-type"] || "";
    if (ct.startsWith("text/plain")) return express.text({ type: "*/*" })(req, res, next);
    return express.json({ type: "*/*" })(req, res, next);
  },
  (req, res) => {
    let payload = req.body;
    if (typeof payload === "string") {
      try {
        payload = JSON.parse(payload);
      } catch {
        payload = { raw: payload };
      }
    }
    console.log("nudge-track", {
      ...payload,
      ip: req.ip,
      ua: req.headers["user-agent"],
      at: new Date().toISOString()
    });
    res.set({
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    });
    res.sendStatus(204);
  }
);

// Shopify auth and webhooks
app.get(shopify.config.auth.path, shopify.auth.begin());
app.get(
  shopify.config.auth.callbackPath,
  shopify.auth.callback(),
  shopify.redirectToShopifyOrAppRoot()
);
app.post(
  shopify.config.webhooks.path,
  shopify.processWebhooks({ webhookHandlers: PrivacyWebhookHandlers })
);

// Bouncer chat endpoint is public (no auth required for storefront)
// Protect other authenticated admin API routes
app.use("/api/products/*", shopify.validateAuthenticatedSession());

// Example admin API routes
app.get("/api/products/count", async (_req, res) => {
  const client = new shopify.api.clients.Graphql({
    session: res.locals.shopify.session
  });

  const countData = await client.request(`
    query shopifyProductCount {
      productsCount {
        count
      }
    }
  `);

  res.status(200).send({ count: countData.data.productsCount.count });
});

app.post("/api/products", async (_req, res) => {
  let status = 200;
  let error = null;

  try {
    await productCreator(res.locals.shopify.session);
  } catch (e) {
    console.log(`Failed to process products/create: ${e.message}`);
    status = 500;
    error = e.message;
  }
  res.status(status).send({ success: status === 200, error });
});

app.use(shopify.cspHeaders());
app.use(serveStatic(STATIC_PATH, { index: false }));

app.use("/*", shopify.ensureInstalledOnShop(), async (_req, res) => {
  return res
    .status(200)
    .set("Content-Type", "text/html")
    .send(
      readFileSync(join(STATIC_PATH, "index.html"))
        .toString()
        .replace("%VITE_SHOPIFY_API_KEY%", process.env.SHOPIFY_API_KEY || "")
    );
});

app.listen(PORT);
