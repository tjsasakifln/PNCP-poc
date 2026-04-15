/**
 * STORY-4.3 (TD-FE-004) — ESLint rule: no-hardcoded-hex.
 *
 * Blocks arbitrary Tailwind values (`bg-[#fff]`, `text-[#abc]`, etc.) and
 * hex literals inside `style={{...}}` props. Tokens in `tailwind.config.ts`
 * are the single source of truth for colour.
 *
 * Allowlist handled via `.eslintrc.json` overrides — notably:
 *   - `app/api/og/**` (Vercel OG requires literal hex, no CSS vars)
 *   - test files, storybook, sentry config
 *
 * Esc override per-line:
 *   // eslint-disable-next-line local-rules/no-hardcoded-hex -- reason
 */

'use strict';

const HEX_LITERAL = /#[0-9a-fA-F]{3,8}\b/;
const TAILWIND_ARBITRARY = /\b(bg|text|border|ring|fill|stroke|from|to|via|outline|decoration|placeholder|caret|accent|shadow|divide)-\[#[0-9a-fA-F]{3,8}\]/;

/** @type {import('eslint').Rule.RuleModule} */
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow hardcoded hex colors — use Tailwind semantic tokens from tailwind.config.ts',
      recommended: false,
    },
    schema: [
      {
        type: 'object',
        properties: {
          tokenHint: { type: 'string' },
        },
        additionalProperties: false,
      },
    ],
    messages: {
      arbitraryClass:
        "{{hint}}: arbitrary Tailwind hex `{{match}}` found. Use a semantic token (e.g. bg-primary, text-success).",
      inlineStyle:
        "{{hint}}: hardcoded hex `{{match}}` in inline style. Use a semantic token (className) or add a token in tailwind.config.ts.",
      stringLiteral:
        "{{hint}}: hardcoded hex `{{match}}` in string literal. Use a semantic token or token lookup.",
    },
  },
  create(context) {
    const options = context.options[0] || {};
    const hint =
      options.tokenHint ||
      'STORY-4.3 (TD-FE-004): use Tailwind semantic tokens — see frontend/tailwind.config.ts';

    function reportHex(node, match, messageId) {
      context.report({
        node,
        messageId,
        data: { match, hint },
      });
    }

    function checkClassNameValue(node, value) {
      if (typeof value !== 'string') return;
      const m = value.match(TAILWIND_ARBITRARY);
      if (m) reportHex(node, m[0], 'arbitraryClass');
    }

    function checkInlineStyleValue(node, value) {
      if (typeof value !== 'string') return;
      const m = value.match(HEX_LITERAL);
      if (m) reportHex(node, m[0], 'inlineStyle');
    }

    return {
      JSXAttribute(node) {
        const name = node.name && node.name.name;
        if (!node.value) return;

        if (name === 'className') {
          // className="bg-[#abc] ..."
          if (node.value.type === 'Literal') {
            checkClassNameValue(node, node.value.value);
          }
          // className={`bg-[#abc] ...`} or className={"..."}
          if (node.value.type === 'JSXExpressionContainer') {
            const expr = node.value.expression;
            if (expr && expr.type === 'Literal') {
              checkClassNameValue(node, expr.value);
            }
            if (expr && expr.type === 'TemplateLiteral') {
              for (const quasi of expr.quasis) {
                checkClassNameValue(node, quasi.value && quasi.value.raw);
              }
            }
          }
        }

        if (name === 'style' && node.value.type === 'JSXExpressionContainer') {
          // style={{ color: '#fff' }}
          const expr = node.value.expression;
          if (expr && expr.type === 'ObjectExpression') {
            for (const prop of expr.properties) {
              if (
                prop.type === 'Property' &&
                prop.value &&
                prop.value.type === 'Literal' &&
                typeof prop.value.value === 'string'
              ) {
                const m = prop.value.value.match(HEX_LITERAL);
                if (m) reportHex(prop, m[0], 'inlineStyle');
              }
              if (
                prop.type === 'Property' &&
                prop.value &&
                prop.value.type === 'TemplateLiteral'
              ) {
                for (const quasi of prop.value.quasis) {
                  const raw = quasi.value && quasi.value.raw;
                  if (!raw) continue;
                  const m = raw.match(HEX_LITERAL);
                  if (m) reportHex(prop, m[0], 'inlineStyle');
                }
              }
            }
          }
        }
      },
    };
  },
};
