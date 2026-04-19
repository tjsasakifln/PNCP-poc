import type { Metadata } from 'next';
import FoundingObrigadoClient from './FoundingObrigadoClient';

export const metadata: Metadata = {
  title: 'Bem-vindo ao SmartLic Founding Partners',
  description: 'Próximos passos para o seu trial SmartLic como founding partner.',
  robots: { index: false, follow: false },
};

export default function FoundingObrigadoPage() {
  return <FoundingObrigadoClient />;
}
