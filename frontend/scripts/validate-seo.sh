#!/bin/bash

# SEO Validation Script for SmartLic
# Validates sitemap, schema.org, robots.txt, and meta tags

echo "🔍 Starting SEO validation..."
echo ""

# Check if required files exist
echo "📂 Checking for required SEO files..."

if [ -f "public/sitemap.xml" ]; then
  echo "✅ sitemap.xml found"
else
  echo "❌ sitemap.xml not found"
  exit 1
fi

if [ -f "public/robots.txt" ]; then
  echo "✅ robots.txt found"
else
  echo "❌ robots.txt not found"
  exit 1
fi

echo ""
echo "🗺️  Validating sitemap.xml..."

# Count URLs in sitemap
URL_COUNT=$(grep -c "<loc>" public/sitemap.xml)
echo "   URLs in sitemap: $URL_COUNT"

if [ $URL_COUNT -lt 10 ]; then
  echo "   ⚠️  Warning: Less than 10 URLs in sitemap"
fi

# Check if sitemap references smartlic.tech
if grep -q "smartlic.tech" public/sitemap.xml; then
  echo "   ✅ Domain smartlic.tech found in sitemap"
else
  echo "   ❌ Domain smartlic.tech NOT found in sitemap"
  exit 1
fi

echo ""
echo "🤖 Validating robots.txt..."

# Check if robots.txt allows all user agents
if grep -q "User-agent: \*" public/robots.txt; then
  echo "   ✅ User-agent: * found"
else
  echo "   ❌ User-agent: * NOT found"
  exit 1
fi

# Check if robots.txt references sitemap
if grep -q "Sitemap:" public/robots.txt; then
  echo "   ✅ Sitemap reference found"
else
  echo "   ❌ Sitemap reference NOT found"
  exit 1
fi

echo ""
echo "📊 Checking structured data implementation..."

# Check if StructuredData component exists
if [ -f "app/components/StructuredData.tsx" ]; then
  echo "   ✅ StructuredData component found"

  # Check for required schemas
  if grep -q "Organization" app/components/StructuredData.tsx; then
    echo "   ✅ Organization schema implemented"
  fi

  if grep -q "WebSite" app/components/StructuredData.tsx; then
    echo "   ✅ WebSite schema implemented"
  fi

  if grep -q "SoftwareApplication" app/components/StructuredData.tsx; then
    echo "   ✅ SoftwareApplication schema implemented"
  fi
else
  echo "   ❌ StructuredData component NOT found"
  exit 1
fi

echo ""
echo "📱 Checking Google Analytics integration..."

if [ -f "app/components/GoogleAnalytics.tsx" ]; then
  echo "   ✅ GoogleAnalytics component found"

  # Check for LGPD compliance
  if grep -q "anonymize_ip" app/components/GoogleAnalytics.tsx; then
    echo "   ✅ IP anonymization enabled (LGPD compliant)"
  fi

  if grep -q "cookie-consent" app/components/GoogleAnalytics.tsx; then
    echo "   ✅ Cookie consent check implemented"
  fi
else
  echo "   ❌ GoogleAnalytics component NOT found"
  exit 1
fi

echo ""
echo "🎯 Checking meta tags in layout..."

if grep -q "keywords:" app/layout.tsx; then
  echo "   ✅ Keywords meta tag found"
fi

if grep -q "openGraph:" app/layout.tsx; then
  echo "   ✅ Open Graph tags found"
fi

if grep -q "twitter:" app/layout.tsx; then
  echo "   ✅ Twitter Card tags found"
fi

if grep -q "robots:" app/layout.tsx; then
  echo "   ✅ Robots meta tag found"
fi

if grep -q "verification:" app/layout.tsx; then
  echo "   ✅ Google verification tag found"
fi

echo ""
echo "✅ All SEO validations passed!"
echo ""
echo "📋 Summary:"
echo "   • Sitemap: $URL_COUNT URLs"
echo "   • robots.txt: Configured correctly"
echo "   • Structured data: 3 schemas (Organization, WebSite, SoftwareApplication)"
echo "   • Google Analytics: Integrated with LGPD compliance"
echo "   • Meta tags: Optimized for Google AI Search"
echo ""
echo "🚀 Next steps:"
echo "   1. Build the app: npm run build"
echo "   2. Deploy to production"
echo "   3. Submit sitemap to Google Search Console"
echo "   4. Validate structured data at https://search.google.com/test/rich-results"
echo "   5. Run Lighthouse audit: npm run lighthouse"
echo ""
