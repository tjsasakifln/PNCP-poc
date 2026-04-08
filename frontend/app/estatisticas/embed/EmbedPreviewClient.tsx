'use client';

import { useState } from 'react';

interface EmbedPreviewClientProps {
  code: string;
  label: string;
}

export default function EmbedPreviewClient({ code, label }: EmbedPreviewClientProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for non-secure contexts
      const textarea = document.createElement('textarea');
      textarea.value = code;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className="space-y-4">
      {/* Preview */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-6">
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide font-medium">
          Preview do {label}
        </p>
        <div dangerouslySetInnerHTML={{ __html: code }} />
      </div>

      {/* Code block */}
      <div className="relative">
        <pre className="bg-gray-900 dark:bg-gray-800 rounded-lg p-4 text-sm text-gray-300 overflow-x-auto">
          <code>{code}</code>
        </pre>
        <button
          onClick={handleCopy}
          className="absolute top-3 right-3 px-3 py-1.5 text-xs font-medium rounded-md
                     bg-gray-700 text-gray-200 hover:bg-gray-600 transition-colors"
        >
          {copied ? 'Copiado!' : 'Copiar HTML'}
        </button>
      </div>
    </div>
  );
}
