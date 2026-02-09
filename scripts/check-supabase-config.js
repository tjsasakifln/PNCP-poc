#!/usr/bin/env node

const https = require('https');

const SUPABASE_PROJECT_REF = 'fqqyovlzdzimiwfofdjk';
const SUPABASE_API_URL = `/v1/projects/${SUPABASE_PROJECT_REF}/config/auth`;

function getAccessToken() {
  const token = process.env.SUPABASE_ACCESS_TOKEN;
  if (!token) {
    console.error('❌ SUPABASE_ACCESS_TOKEN not found');
    process.exit(1);
  }
  return token;
}

async function getCurrentConfig() {
  return new Promise((resolve, reject) => {
    const token = getAccessToken();
    const options = {
      hostname: 'api.supabase.com',
      path: SUPABASE_API_URL,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };

    https.get(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(body));
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    }).on('error', reject);
  });
}

async function main() {
  try {
    const config = await getCurrentConfig();
    console.log('\n📋 Current Supabase OAuth Configuration:\n');
    console.log('REDIRECT_URLS:', config.REDIRECT_URLS || '(none)');
    console.log();

    if (config.REDIRECT_URLS) {
      const urls = config.REDIRECT_URLS.split(',').map(url => url.trim());
      console.log('Configured URLs:');
      urls.forEach(url => console.log(`  - ${url}`));
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

main();
