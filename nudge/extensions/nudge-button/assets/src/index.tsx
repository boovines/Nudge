import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import ChatbotPopup from "./ChatbotPopup";

function ChatApp() {
  const [open, setOpen] = useState(false);
  (window as any).NudgeChat = {
    open: () => setOpen(true),
    close: () => setOpen(false),
    toggle: () => setOpen((v: boolean) => !v)
  };
  return <ChatbotPopup isOpen={open} onClose={() => setOpen(false)} />;
}

// Mount once
const mountId = "nudge-chat-root";
let host = document.getElementById(mountId);
if (!host) {
  host = document.createElement("div");
  host.id = mountId;
  document.body.appendChild(host);
}
createRoot(host!).render(<ChatApp />);

/* ---------- Price preview logic ---------- */
(function () {
  const block = document.getElementById("nudge-block") as HTMLElement | null;
  if (!block) return;

  const handle = block.getAttribute("data-product-handle") || "";
  const currency = block.getAttribute("data-currency") || "USD";
  const codeFromSettings = block.getAttribute("data-discount-code") || "";
  const percentStr = block.getAttribute("data-discount-percent") || "0";
  const previewEnabled = block.getAttribute("data-preview") === "true";
  const overrideTheme = block.getAttribute("data-override") === "true";

  const percent = Math.max(0, Math.min(90, parseInt(percentStr, 10) || 0));
  if (!previewEnabled || !handle || !percent) return;

  const codeFromUrl = new URL(location.href).searchParams.get("discount") || "";
  let activeCode = codeFromSettings || codeFromUrl;
  try {
    if (!activeCode) {
      const s = localStorage.getItem("nudge_code");
      if (s) activeCode = s;
    } else {
      localStorage.setItem("nudge_code", activeCode);
    }
  } catch {}

  let product: any = null;
  let lastVariantId: string | null = null;

  function fmt(cents: number): string {
    const v = cents / 100;
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(v);
    } catch {
      return `$${v.toFixed(2)}`;
    }
  }

  async function loadProduct() {
    if (product) return product;
    const res = await fetch(`/products/${handle}.js`, { credentials: "same-origin" });
    product = await res.json();
    return product;
  }

  function getVariantId(): string | null {
    const hidden = document.querySelector('input[name="id"][type="hidden"]') as HTMLInputElement | null;
    if (hidden?.value) return hidden.value;
    const select = document.querySelector('select[name="id"]') as HTMLSelectElement | null;
    if (select?.value) return select.value;
    const radios = Array.from(document.querySelectorAll('input[name="id"][type="radio"]')) as HTMLInputElement[];
    const checked = radios.find(r => r.checked);
    if (checked?.value) return checked.value;
    const urlVid = new URL(location.href).searchParams.get("variant");
    return urlVid;
  }

  function ensurePreviewEl(): HTMLElement {
    let el = document.getElementById("nudge-price-preview") as HTMLElement | null;
    if (!el) {
      el = document.createElement("div");
      el.id = "nudge-price-preview";
      el.style.marginTop = "6px";
      el.style.fontSize = "14px";
      el.style.color = "#065f46";
      el.style.padding = "6px 8px";
      el.style.border = "1px solid #d1fae5";
      el.style.background = "#ecfdf5";
      el.style.borderRadius = "6px";
      block!.appendChild(el);
    }
    return el;
  }

  function updateThemePriceText(text: string) {
    if (!overrideTheme) return;
    const sels = [
      ".price__container .price-item--regular",
      ".price .price-item--regular",
      ".product__info-container .price-item--regular",
      ".price-item--regular"
    ];
    for (const sel of sels) {
      const el = document.querySelector(sel) as HTMLElement | null;
      if (el) {
        if (!(el as any).dataset?.nudgeOriginal) {
          (el as any).dataset = { ...(el as any).dataset, nudgeOriginal: el.textContent || "" };
        }
        el.textContent = text;
        break;
      }
    }
  }

  async function updatePreview() {
    const p = await loadProduct();
    const vid = getVariantId();
    if (!vid || vid === lastVariantId) return;
    lastVariantId = vid;

    const variant = p.variants.find((v: any) => String(v.id) === String(vid)) || p.variants[0];
    if (!variant) return;

    const discountedCents = Math.max(0, Math.round(variant.price * (1 - percent / 100)));
    const line = activeCode ? `With ${activeCode}: ${fmt(discountedCents)}` : `Discounted: ${fmt(discountedCents)}`;

    const el = ensurePreviewEl();
    el.textContent = line;
    updateThemePriceText(fmt(discountedCents));
  }

  // Run now and keep in sync
  updatePreview();

  // Variant changes: listen to common changes and poll as fallback
  document.addEventListener("change", (e) => {
    const t = e.target as HTMLElement | null;
    if (!t) return;
    if (t.closest('form[action="/cart/add"]')) updatePreview();
    if ((t as HTMLInputElement).name === "id") updatePreview();
  });
  window.addEventListener("popstate", updatePreview);
  setInterval(updatePreview, 800);
})();
