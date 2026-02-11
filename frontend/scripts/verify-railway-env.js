#!/usr/bin/env node
/**
 * Railway Environment Variables Diagnostic Script
 *
 * PURPOSE: Verify OAuth-related environment variables in Railway deployment
 *
 * USAGE:
 *   Local: node scripts/verify-railway-env.js
 *   Railway: Add as a service command or run via Railway shell
 *
 * CHECKS:
 *   1. NEXT_PUBLIC_CANONICAL_URL (critical for OAuth redirect)
 *   2. NEXT_PUBLIC_SUPABASE_URL (required for Supabase)
 *   3. NEXT_PUBLIC_SUPABASE_ANON_KEY (required for Supabase)
 *   4. BACKEND_URL (optional, for API calls)
 */

const chalk = require('chalk');

// ANSI colors for environments without chalk
const colors = {
  red: (str) => `\x1b[31m${str}\x1b[0m`,
  green: (str) => `\x1b[32m${str}\x1b[0m`,
  yellow: (str) => `\x1b[33m${str}\x1b[0m`,
  blue: (str) => `\x1b[34m${str}\x1b[0m`,
  bold: (str) => `\x1b[1m${str}\x1b[0m`,
};

console.log('\n' + colors.bold('=========================================='));
console.log(colors.bold('Railway Environment Variables Diagnostic'));
console.log(colors.bold('==========================================') + '\n');

const requiredVars = [
  {
    name: 'NEXT_PUBLIC_SUPABASE_URL',
    required: true,
    description: 'Supabase project URL',
    example: 'https://xxxxx.supabase.co',
  },
  {
    name: 'NEXT_PUBLIC_SUPABASE_ANON_KEY',
    required: true,
    description: 'Supabase anonymous key',
    example: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  },
  {
    name: 'NEXT_PUBLIC_CANONICAL_URL',
    required: false, // Marked optional in docs, but CRITICAL for OAuth
    description: 'Production canonical URL (CRITICAL for OAuth redirect)',
    example: 'https://smartlic.tech',
    critical: true,
  },
  {
    name: 'BACKEND_URL',
    required: false,
    description: 'Backend API URL',
    example: 'https://backend-production-xxxx.up.railway.app',
  },
];

let allGood = true;
let criticalMissing = false;

console.log(colors.blue('Checking environment variables...\n'));

requiredVars.forEach(({ name, required, description, example, critical }) => {
  const value = process.env[name];
  const isSet = !!value;
  const isCritical = required || critical;

  if (isSet) {
    // Mask sensitive values
    let displayValue = value;
    if (name.includes('KEY') || name.includes('SECRET')) {
      displayValue = value.substring(0, 20) + '...' + value.substring(value.length - 10);
    }

    console.log(colors.green('✓') + ` ${colors.bold(name)}`);
    console.log(`  ${colors.green('SET')}: ${displayValue}`);
    console.log(`  Description: ${description}\n`);
  } else {
    const status = isCritical ? colors.red('✗ MISSING (CRITICAL)') : colors.yellow('⚠ MISSING (OPTIONAL)');
    console.log(status + ` ${colors.bold(name)}`);
    console.log(`  Description: ${description}`);
    console.log(`  Example: ${example}\n`);

    if (isCritical) {
      allGood = false;
      if (critical || required) {
        criticalMissing = true;
      }
    }
  }
});

console.log(colors.bold('=========================================='));
console.log(colors.bold('OAuth Redirect URL Analysis'));
console.log(colors.bold('==========================================') + '\n');

const canonicalUrl = process.env.NEXT_PUBLIC_CANONICAL_URL;
const fallbackUrl = 'https://smartlic.tech'; // From middleware.ts

if (canonicalUrl) {
  const redirectUrl = `${canonicalUrl}/auth/callback`;
  console.log(colors.green('✓') + ' OAuth redirect URL will be:');
  console.log(`  ${colors.bold(redirectUrl)}\n`);
} else {
  console.log(colors.yellow('⚠') + ' NEXT_PUBLIC_CANONICAL_URL not set');
  console.log('  OAuth will use: ' + colors.yellow('window.location.origin + "/auth/callback"'));
  console.log('  This may cause issues if Railway URL changes!\n');
  console.log(colors.yellow('  RECOMMENDATION: Set NEXT_PUBLIC_CANONICAL_URL to:'));
  console.log(`  ${colors.bold(fallbackUrl)}\n`);
}

console.log(colors.bold('=========================================='));
console.log(colors.bold('Summary'));
console.log(colors.bold('==========================================') + '\n');

if (allGood && canonicalUrl) {
  console.log(colors.green('✓ All environment variables configured correctly!'));
  console.log(colors.green('✓ OAuth redirect URL is properly set.\n'));
} else {
  console.log(colors.red('✗ Issues detected:\n'));

  if (criticalMissing) {
    console.log(colors.red('  - Critical environment variables missing'));
  }

  if (!canonicalUrl) {
    console.log(colors.yellow('  - NEXT_PUBLIC_CANONICAL_URL not set (may cause OAuth issues)'));
  }

  console.log('\n' + colors.bold('Next Steps:'));
  console.log('1. Go to Railway Dashboard: https://railway.app/');
  console.log('2. Select your project and service');
  console.log('3. Go to "Variables" tab');
  console.log('4. Add/update missing variables');
  console.log('5. Redeploy the service\n');

  if (!canonicalUrl) {
    console.log(colors.bold('CRITICAL for OAuth fix:'));
    console.log(`Add: NEXT_PUBLIC_CANONICAL_URL = ${fallbackUrl}`);
    console.log('This ensures consistent OAuth redirect URLs.\n');
  }
}

console.log(colors.bold('=========================================='));
console.log(colors.bold('Google Cloud Console Configuration'));
console.log(colors.bold('==========================================') + '\n');

const expectedRedirectUrl = canonicalUrl
  ? `${canonicalUrl}/auth/callback`
  : `${fallbackUrl}/auth/callback`;

console.log('Verify in Google Cloud Console:');
console.log('1. Go to: https://console.cloud.google.com/apis/credentials');
console.log('2. Select your OAuth 2.0 Client ID');
console.log('3. Check "Authorized redirect URIs" includes:');
console.log(`   ${colors.bold(expectedRedirectUrl)}`);
console.log('4. Also verify Supabase Dashboard has same URL\n');

console.log(colors.bold('==========================================\n'));

// Exit with error code if critical issues found
process.exit(allGood && canonicalUrl ? 0 : 1);
