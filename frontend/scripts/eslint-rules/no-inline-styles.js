/**
 * STORY-5.14 (TD-FE-003) — ESLint rule: no-inline-styles.
 *
 * Blocks `style={{...}}` props on JSX elements. Static styles should use
 * Tailwind utility classes; dynamic styles that genuinely need runtime
 * computation are allowed with a disable comment:
 *
 *   {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width from percentage *\/}
 *
 * Exempted via `.eslintrc.json` overrides:
 *   - `app/api/og/**` (Vercel OG requires inline styles)
 *   - `app/global-error.tsx` (renders outside Tailwind context)
 *   - test files, e2e helpers, scripts
 */

'use strict';

/** @type {import('eslint').Rule.RuleModule} */
module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      description:
        'Disallow inline style props — use Tailwind utility classes instead',
      recommended: false,
    },
    schema: [],
    messages: {
      noInlineStyle:
        'STORY-5.14 (TD-FE-003): avoid inline `style` prop. ' +
        'Use Tailwind className utilities instead. ' +
        'If the value is computed at runtime, add: ' +
        '// eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: <reason>',
    },
  },
  create(context) {
    return {
      JSXAttribute(node) {
        if (
          node.name &&
          node.name.type === 'JSXIdentifier' &&
          node.name.name === 'style'
        ) {
          context.report({
            node,
            messageId: 'noInlineStyle',
          });
        }
      },
    };
  },
};
