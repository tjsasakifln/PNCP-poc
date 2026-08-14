'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

interface Props {
  refParam: string;
  label?: string;
}

export default function StickyTrialCTA({ refParam, label = 'Pedir diagnóstico à CONFENGE' }: Props) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 600);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  if (!show) return null;

  const handleClick = () => {
    if (typeof window !== 'undefined' && window.mixpanel) {
      window.mixpanel.track('sticky_cta_clicked', { ref: refParam });
    }
  };

  return (
    <div className="fixed bottom-0 inset-x-0 z-40 sm:hidden bg-white border-t border-gray-200 px-4 py-3 shadow-lg">
      <Link
        href={`/consultoria-b2g?ref=${refParam}`}
        onClick={handleClick}
        className="block w-full bg-green-600 hover:bg-green-700 text-white text-center font-bold py-3 rounded-lg"
      >
        {label} →
      </Link>
      <p className="text-center text-xs text-gray-500 mt-1">Sem cartão de crédito</p>
    </div>
  );
}
