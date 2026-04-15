#!/usr/bin/env node
/**
 * Cleanup Stripe test-mode customers created by billing E2E specs.
 *
 * Scans Stripe for customers whose email matches the E2E prefix
 * (`e2e-billing-*@test.smartlic.tech`) and deletes them.  Supports
 * --dry-run to preview without side-effects.
 *
 * Usage:
 *   STRIPE_TEST_SECRET_KEY=sk_test_... node scripts/cleanup-stripe-test-customers.js
 *   STRIPE_TEST_SECRET_KEY=sk_test_... node scripts/cleanup-stripe-test-customers.js --dry-run
 *
 * Safety:
 *   - Refuses to run unless the key starts with `sk_test_`.
 *   - Only touches customers whose email matches E2E_PREFIX + @E2E_DOMAIN.
 *
 * STORY-3.5 — EPIC-TD-2026Q2 (P1)
 */

'use strict';

const E2E_PREFIX = 'e2e-billing-';
const E2E_DOMAIN = 'test.smartlic.tech';
const API_ROOT = 'https://api.stripe.com/v1';

function parseArgs(argv) {
  return {
    dryRun: argv.includes('--dry-run'),
    verbose: argv.includes('--verbose') || argv.includes('-v'),
  };
}

function log(msg) {
  // eslint-disable-next-line no-console
  console.log(msg);
}

async function stripeGet(path, key) {
  const res = await fetch(`${API_ROOT}${path}`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${key}` },
  });
  if (!res.ok) {
    throw new Error(`Stripe GET ${path} failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

async function stripeDelete(path, key) {
  const res = await fetch(`${API_ROOT}${path}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${key}` },
  });
  if (!res.ok) {
    throw new Error(`Stripe DELETE ${path} failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

async function listAllCustomers(key) {
  const results = [];
  let startingAfter = null;
  while (true) {
    const query = new URLSearchParams({ limit: '100' });
    if (startingAfter) query.set('starting_after', startingAfter);
    const page = await stripeGet(`/customers?${query.toString()}`, key);
    results.push(...(page.data || []));
    if (!page.has_more || page.data.length === 0) break;
    startingAfter = page.data[page.data.length - 1].id;
  }
  return results;
}

function isE2ECustomer(customer) {
  const email = (customer.email || '').toLowerCase();
  return email.startsWith(E2E_PREFIX) && email.endsWith(`@${E2E_DOMAIN}`);
}

async function main() {
  const { dryRun, verbose } = parseArgs(process.argv.slice(2));
  const key = process.env.STRIPE_TEST_SECRET_KEY;

  if (!key) {
    // eslint-disable-next-line no-console
    console.error('FATAL: STRIPE_TEST_SECRET_KEY env var not set.');
    process.exit(2);
  }
  if (!key.startsWith('sk_test_')) {
    // eslint-disable-next-line no-console
    console.error('FATAL: STRIPE_TEST_SECRET_KEY does not look like a test key (must start with sk_test_).');
    process.exit(2);
  }

  log(`[cleanup] Stripe key: ${key.slice(0, 12)}... (test mode)`);
  log(`[cleanup] Mode: ${dryRun ? 'DRY-RUN (no deletions)' : 'LIVE DELETE'}`);
  log(`[cleanup] Scanning Stripe for E2E customers (${E2E_PREFIX}*@${E2E_DOMAIN})...`);

  const customers = await listAllCustomers(key);
  const matches = customers.filter(isE2ECustomer);

  log(`[cleanup] Found ${customers.length} total customers, ${matches.length} E2E matches.`);
  if (verbose) {
    for (const c of matches) log(`[cleanup]   - ${c.id}  ${c.email}`);
  }

  if (matches.length === 0) {
    log('[cleanup] Nothing to delete.');
    return;
  }

  if (dryRun) {
    log('[cleanup] DRY-RUN: skipping deletions.');
    return;
  }

  let deleted = 0;
  let failed = 0;
  for (const c of matches) {
    try {
      await stripeDelete(`/customers/${c.id}`, key);
      deleted++;
      if (verbose) log(`[cleanup] deleted ${c.id}`);
    } catch (err) {
      failed++;
      // eslint-disable-next-line no-console
      console.error(`[cleanup] delete failed for ${c.id}: ${err.message}`);
    }
  }

  log(`[cleanup] Done: ${deleted} deleted, ${failed} failed.`);
  if (failed > 0) process.exit(1);
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error('[cleanup] Fatal:', err);
  process.exit(1);
});
