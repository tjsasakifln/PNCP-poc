'use client';

// STORY-432 AC3: Botão de copiar código de embed (client component)
export function CopyEmbedButton({ code }: { code: string }) {
  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      const btn = document.getElementById('copy-embed-btn');
      if (btn) {
        btn.textContent = '✓ Copiado!';
        setTimeout(() => { if (btn) btn.textContent = 'Copiar código'; }, 2500);
      }
    } catch {
      // fallback: select text
    }
  }

  return (
    <button
      id="copy-embed-btn"
      type="button"
      onClick={handleCopy}
      className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
    >
      Copiar código
    </button>
  );
}
