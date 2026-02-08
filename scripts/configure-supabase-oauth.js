#!/usr/bin/env node

/**
 * Configure Supabase OAuth Redirect URLs via Management API
 *
 * This script automates the Supabase dashboard configuration required
 * for OAuth Google login to work properly.
 *
 * Fixes: OAuth callback redirect issue (PR #313)
 */

const https = require('https');

// Configuration
const SUPABASE_PROJECT_REF = 'fqqyovlzdzimiwfofdjk';
const SUPABASE_API_URL = `https://api.supabase.com/v1/projects/${SUPABASE_PROJECT_REF}/config/auth`;

// Required redirect URLs for OAuth to work
const REQUIRED_REDIRECT_URLS = [
  'https://bidiq-frontend-production.up.railway.app/auth/callback',
  'http://localhost:3000/auth/callback',
];

// URLs to remove (cause the bug)
const URLS_TO_REMOVE = [
  'https://bidiq-frontend-production.up.railway.app/',
  'http://localhost:3000/',
];

/**
 * Get Supabase Access Token from environment
 */
function getAccessToken() {
  // Try multiple sources
  const token = process.env.SUPABASE_ACCESS_TOKEN
    || process.env.SUPABASE_SERVICE_KEY
    || process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!token) {
    console.error('\n❌ Error: SUPABASE_ACCESS_TOKEN not found\n');
    console.log('Please set one of these environment variables:');
    console.log('  - SUPABASE_ACCESS_TOKEN (from Supabase dashboard)');
    console.log('  - SUPABASE_SERVICE_KEY');
    console.log('  - SUPABASE_SERVICE_ROLE_KEY\n');
    console.log('To get your access token:');
    console.log('  1. Go to: https://app.supabase.com/account/tokens');
    console.log('  2. Generate a new token');
    console.log('  3. Set: export SUPABASE_ACCESS_TOKEN=<your-token>\n');
    process.exit(1);
  }

  return token;
}

/**
 * Make HTTPS request to Supabase Management API
 */
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const token = getAccessToken();
    const url = new URL(path, 'https://api.supabase.com');

    const options = {
      hostname: url.hostname,
      path: url.pathname,
      method: method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };

    const req = https.request(options, (res) => {
      let body = '';

      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(body));
          } catch (err) {
            resolve(body);
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }

    req.end();
  });
}

/**
 * Get current auth configuration
 */
async function getCurrentConfig() {
  console.log('📡 Fetching current auth configuration...');
  try {
    const config = await makeRequest('GET', SUPABASE_API_URL);
    console.log('✅ Current configuration retrieved\n');
    return config;
  } catch (error) {
    console.error('❌ Failed to fetch configuration:', error.message);
    throw error;
  }
}

/**
 * Update auth configuration with new redirect URLs
 */
async function updateRedirectUrls(currentConfig) {
  console.log('🔧 Updating redirect URLs...\n');

  // Get current redirect URLs (if any)
  const currentUrls = currentConfig.REDIRECT_URLS
    ? currentConfig.REDIRECT_URLS.split(',').map(url => url.trim()).filter(Boolean)
    : [];

  console.log('Current redirect URLs:');
  if (currentUrls.length === 0) {
    console.log('  (none configured)');
  } else {
    currentUrls.forEach(url => console.log(`  - ${url}`));
  }
  console.log();

  // Build new URL list
  let newUrls = [...currentUrls];

  // Remove problematic URLs
  URLS_TO_REMOVE.forEach(urlToRemove => {
    if (newUrls.includes(urlToRemove)) {
      console.log(`❌ Removing: ${urlToRemove} (causes bug)`);
      newUrls = newUrls.filter(url => url !== urlToRemove);
    }
  });

  // Add required URLs
  REQUIRED_REDIRECT_URLS.forEach(requiredUrl => {
    if (!newUrls.includes(requiredUrl)) {
      console.log(`✅ Adding: ${requiredUrl}`);
      newUrls.push(requiredUrl);
    } else {
      console.log(`ℹ️  Already configured: ${requiredUrl}`);
    }
  });

  console.log();

  // Check if changes are needed
  const urlsChanged = JSON.stringify(currentUrls.sort()) !== JSON.stringify(newUrls.sort());

  if (!urlsChanged) {
    console.log('✅ Configuration already correct, no changes needed\n');
    return false;
  }

  // Update configuration
  console.log('📝 New redirect URLs:');
  newUrls.forEach(url => console.log(`  - ${url}`));
  console.log();

  const updatePayload = {
    REDIRECT_URLS: newUrls.join(','),
  };

  try {
    await makeRequest('PATCH', SUPABASE_API_URL, updatePayload);
    console.log('✅ Redirect URLs updated successfully!\n');
    return true;
  } catch (error) {
    console.error('❌ Failed to update configuration:', error.message);
    throw error;
  }
}

/**
 * Verify configuration
 */
async function verifyConfiguration() {
  console.log('🔍 Verifying configuration...');

  try {
    const config = await getCurrentConfig();
    const configuredUrls = config.REDIRECT_URLS
      ? config.REDIRECT_URLS.split(',').map(url => url.trim()).filter(Boolean)
      : [];

    let allCorrect = true;

    REQUIRED_REDIRECT_URLS.forEach(requiredUrl => {
      if (configuredUrls.includes(requiredUrl)) {
        console.log(`✅ ${requiredUrl}`);
      } else {
        console.log(`❌ Missing: ${requiredUrl}`);
        allCorrect = false;
      }
    });

    URLS_TO_REMOVE.forEach(badUrl => {
      if (configuredUrls.includes(badUrl)) {
        console.log(`⚠️  Still present (should be removed): ${badUrl}`);
        allCorrect = false;
      }
    });

    console.log();

    if (allCorrect) {
      console.log('🎉 Configuration verified successfully!\n');
    } else {
      console.log('⚠️  Configuration incomplete or incorrect\n');
    }

    return allCorrect;
  } catch (error) {
    console.error('❌ Verification failed:', error.message);
    return false;
  }
}

/**
 * Main execution
 */
async function main() {
  console.log('\n🔧 Supabase OAuth Configuration Script\n');
  console.log('Project:', SUPABASE_PROJECT_REF);
  console.log('Purpose: Configure redirect URLs for Google OAuth\n');
  console.log('─'.repeat(60));
  console.log();

  try {
    // Step 1: Get current configuration
    const currentConfig = await getCurrentConfig();

    // Step 2: Update redirect URLs
    const updated = await updateRedirectUrls(currentConfig);

    // Step 3: Verify configuration
    const verified = await verifyConfiguration();

    // Summary
    console.log('─'.repeat(60));
    console.log('\n📊 Summary:\n');

    if (updated) {
      console.log('✅ Configuration updated');
    } else {
      console.log('ℹ️  No changes needed');
    }

    if (verified) {
      console.log('✅ Verification passed');
    } else {
      console.log('⚠️  Verification warnings (see above)');
    }

    console.log();
    console.log('🎯 Next Steps:');
    console.log('  1. Test OAuth Google login in production');
    console.log('  2. Verify redirect to /auth/callback (NOT homepage)');
    console.log('  3. Confirm user authentication works');
    console.log();
    console.log('📝 Testing URL: https://bidiq-frontend-production.up.railway.app/login');
    console.log();

    process.exit(verified ? 0 : 1);

  } catch (error) {
    console.error('\n❌ Script failed:', error.message);
    console.log();
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { getCurrentConfig, updateRedirectUrls, verifyConfiguration };
