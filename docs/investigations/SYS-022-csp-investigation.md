# SYS-022: CSP Investigation — Nonce-Based CSP for Next.js + Stripe.js

**Date:** 2026-03-09
**Status:** Investigation Complete
**Recommendation:** Keep current policy with `unsafe-inline`/`unsafe-eval`; nonce-based CSP not feasible yet.

## Current State (STORY-311)

The frontend already has a comprehensive, **enforcing** CSP policy in `frontend/middleware.ts`:

```
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://static.cloudflareinsights.com https://cdn.sentry.io https://www.clarity.ms
style-src 'self' 'unsafe-inline'
```

Additional security headers: HSTS (1yr + preload), X-Frame-Options DENY, COOP same-origin, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy (camera/mic/geo disabled).

CSP violation reporting active via `/api/csp-report` (rate-limited, structured JSON logging).

## Research: Nonce-Based CSP with Next.js

### Next.js Built-in Support (v13.4+)

Next.js supports nonce-based CSP via middleware. The pattern:

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import crypto from 'crypto';

export function middleware(request) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  const cspHeader = `script-src 'self' 'nonce-${nonce}' 'strict-dynamic';`;

  const response = NextResponse.next();
  response.headers.set('Content-Security-Policy', cspHeader);
  response.headers.set('x-nonce', nonce);
  return response;
}
```

Then in `app/layout.tsx`:
```tsx
import { headers } from 'next/headers';

export default async function RootLayout({ children }) {
  const nonce = (await headers()).get('x-nonce');
  return (
    <html>
      <body>
        <Script nonce={nonce} src="..." />
        {children}
      </body>
    </html>
  );
}
```

### Blockers for SmartLic

#### 1. Stripe.js Requires `unsafe-inline` (CRITICAL BLOCKER)

Stripe.js injects inline scripts for its fraud detection (Stripe Radar). Per [Stripe CSP docs](https://docs.stripe.com/security/content-security-policy):

- `script-src`: needs `https://js.stripe.com`
- `frame-src`: needs `https://js.stripe.com`
- Stripe Radar **dynamically injects inline scripts** that cannot receive nonces
- Stripe explicitly recommends `'unsafe-inline'` as fallback when nonces aren't propagated

**Verdict:** Cannot remove `unsafe-inline` from `script-src` without breaking Stripe checkout.

#### 2. `unsafe-eval` Required by Dependencies

- **Sentry SDK**: Uses `eval()` for source map processing in some modes
- **Microsoft Clarity**: Session replay requires `eval()` for DOM serialization
- **Framer Motion**: Some animation patterns use `new Function()`

**Verdict:** Cannot remove `unsafe-eval` without disabling or replacing these dependencies.

#### 3. `unsafe-inline` in `style-src`

- **Tailwind CSS**: JIT-compiled styles sometimes use inline `<style>` tags
- **Framer Motion**: Applies inline styles for animations (`style={{ transform: ... }}`)
- **Recharts**: SVG chart rendering uses inline styles

**Verdict:** Cannot use nonce-based `style-src` without breaking UI.

#### 4. `strict-dynamic` Cascading Limitation

Using `'strict-dynamic'` with nonces would require ALL third-party scripts to be loaded via nonced `<script>` tags. Our third-party scripts (Stripe, Sentry, Clarity, Mixpanel, Cloudflare) are loaded via multiple entry points — some dynamically by the SDKs themselves. This would require significant refactoring.

## Mitigation Plan (Current)

Since nonce-based CSP is not feasible, the current policy already provides strong protection through:

1. **Domain whitelisting**: Only known, trusted domains in `script-src` (Stripe, Sentry, Clarity, Cloudflare)
2. **CSP violation reporting**: Active monitoring at `/api/csp-report` with rate limiting
3. **Object-src none**: Blocks Flash/Java applets
4. **Frame-src restricted**: Only Stripe iframes allowed
5. **Connect-src restricted**: Only known API endpoints
6. **HSTS preload**: Forces HTTPS everywhere
7. **X-Frame-Options DENY**: Prevents clickjacking
8. **Referrer-Policy**: Limits referer leakage

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| XSS via inline script injection | Medium | Domain whitelist limits what executes; CSP reporting detects attempts |
| eval()-based attacks | Low | `unsafe-eval` is constrained to whitelisted domains only |
| Style injection | Low | Style-only XSS is extremely limited in impact |
| Third-party script compromise | Medium | SRI (Subresource Integrity) can be added for static scripts |

## Future Recommendations

1. **Monitor CSP reports** — If zero `unsafe-inline` violations are reported after 30 days, the current allowances are sufficient
2. **Re-evaluate when Stripe updates** — Stripe may add nonce support in future SDK versions
3. **Consider SRI** — Add `integrity` attributes to third-party `<script>` tags for tamper detection
4. **Next.js 17+** — Re-evaluate if Next.js adds better nonce propagation for third-party script loaders
5. **Accept as documented risk** — The combination of domain whitelist + violation reporting + other security headers provides defense-in-depth

## Conclusion

**`unsafe-inline` and `unsafe-eval` are REQUIRED** by Stripe.js, Sentry, Clarity, and CSS-in-JS patterns. Removing them would break payment processing and monitoring. The current policy is the industry-standard approach for applications with these dependencies. This is an **accepted risk with comprehensive mitigation**.
