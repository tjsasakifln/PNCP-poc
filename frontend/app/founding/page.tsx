import type { Metadata } from 'next';
import FoundingClient from './FoundingClient';

export const metadata: Metadata = {
  title: 'SmartLic Founding Partners — Os primeiros 10 clientes moldam o produto',
  description:
    '30% off por 12 meses, linha direta com o fundador e voz no roadmap para os primeiros 10 clientes pagantes do SmartLic. Restrito a novas contas, 10 vagas totais.',
  robots: { index: false, follow: false },
};

export default function FoundingPage() {
  return <FoundingClient />;
}
