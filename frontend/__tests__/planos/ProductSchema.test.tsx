/**
 * STORY-SEO-004 AC6: ProductSchema emits valid JSON-LD with pricing
 * that matches the shared source of truth in `lib/plan-pricing.ts`.
 */

import React from "react";
import { render } from "@testing-library/react";
import { ProductSchema } from "@/app/planos/components/ProductSchema";
import {
  PRO_PRICING,
  CONSULTORIA_PRICING,
  AGGREGATE_OFFER_BOUNDS,
  getPriceValidUntil,
} from "@/lib/plan-pricing";

type OfferNode = {
  "@type": "Offer";
  price: string;
  priceCurrency: string;
  availability: string;
  priceValidUntil: string;
  category: string;
  url: string;
};

type ProductNode = {
  "@context": "https://schema.org";
  "@type": "Product";
  name: string;
  description: string;
  brand: { "@type": "Brand"; name: string };
  offers: OfferNode[];
};

function extractSchemas(container: HTMLElement): ProductNode[] {
  const scripts = Array.from(
    container.querySelectorAll<HTMLScriptElement>('script[type="application/ld+json"]')
  );
  return scripts.map((s) => JSON.parse(s.textContent ?? "") as ProductNode);
}

describe("ProductSchema (STORY-SEO-004)", () => {
  it("emits exactly 2 Product schemas (Pro + Consultoria)", () => {
    const { container } = render(<ProductSchema />);
    const schemas = extractSchemas(container);
    expect(schemas).toHaveLength(2);
    expect(schemas.map((s) => s.name)).toEqual(["SmartLic Pro", "SmartLic Consultoria"]);
  });

  it("each Product schema is well-formed JSON-LD with required fields", () => {
    const { container } = render(<ProductSchema />);
    const schemas = extractSchemas(container);

    for (const schema of schemas) {
      expect(schema["@context"]).toBe("https://schema.org");
      expect(schema["@type"]).toBe("Product");
      expect(schema.name).toBeTruthy();
      expect(schema.description.length).toBeGreaterThan(20);
      expect(schema.brand).toEqual({ "@type": "Brand", name: "SmartLic" });
      expect(schema.offers).toHaveLength(3); // monthly + semiannual + annual
    }
  });

  it("Pro offers match PRO_PRICING source of truth", () => {
    const { container } = render(<ProductSchema />);
    const [proSchema] = extractSchemas(container);

    const priceByPeriod = Object.fromEntries(
      proSchema.offers.map((o) => [o.category, Number(o.price)])
    );

    expect(priceByPeriod.monthly).toBe(PRO_PRICING.monthly.monthly);
    expect(priceByPeriod.semiannual).toBe(PRO_PRICING.semiannual.monthly);
    expect(priceByPeriod.annual).toBe(PRO_PRICING.annual.monthly);
  });

  it("Consultoria offers match CONSULTORIA_PRICING source of truth", () => {
    const { container } = render(<ProductSchema />);
    const [, consultoriaSchema] = extractSchemas(container);

    const priceByPeriod = Object.fromEntries(
      consultoriaSchema.offers.map((o) => [o.category, Number(o.price)])
    );

    expect(priceByPeriod.monthly).toBe(CONSULTORIA_PRICING.monthly.monthly);
    expect(priceByPeriod.semiannual).toBe(CONSULTORIA_PRICING.semiannual.monthly);
    expect(priceByPeriod.annual).toBe(CONSULTORIA_PRICING.annual.monthly);
  });

  it("all offers declare BRL currency, InStock availability, and priceValidUntil ≥ today", () => {
    const { container } = render(<ProductSchema />);
    const schemas = extractSchemas(container);
    const today = new Date().toISOString().split("T")[0];

    for (const schema of schemas) {
      for (const offer of schema.offers) {
        expect(offer.priceCurrency).toBe("BRL");
        expect(offer.availability).toBe("https://schema.org/InStock");
        expect(offer.priceValidUntil >= today).toBe(true);
      }
    }
  });

  it("offer prices are formatted with two decimal places (schema.org convention)", () => {
    const { container } = render(<ProductSchema />);
    const schemas = extractSchemas(container);

    for (const schema of schemas) {
      for (const offer of schema.offers) {
        expect(offer.price).toMatch(/^\d+\.\d{2}$/);
      }
    }
  });

  it("AggregateOffer bounds agree with per-plan Offers", () => {
    // Invariant documented in `lib/plan-pricing.ts`: AGGREGATE_OFFER_BOUNDS
    // must cover all per-plan prices emitted by ProductSchema.
    const { container } = render(<ProductSchema />);
    const schemas = extractSchemas(container);
    const allPrices = schemas.flatMap((s) => s.offers.map((o) => Number(o.price)));
    expect(Math.min(...allPrices)).toBe(AGGREGATE_OFFER_BOUNDS.lowPrice);
    expect(Math.max(...allPrices)).toBe(AGGREGATE_OFFER_BOUNDS.highPrice);
    expect(allPrices).toHaveLength(AGGREGATE_OFFER_BOUNDS.offerCount);
  });

  it("getPriceValidUntil returns YYYY-MM-DD exactly 1 year ahead of input", () => {
    const fixed = new Date("2026-04-21T12:00:00Z");
    expect(getPriceValidUntil(fixed)).toBe("2027-04-21");
  });
});
