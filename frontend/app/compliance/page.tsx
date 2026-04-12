import { Metadata } from 'next';
import Link from 'next/link';
import { buildCanonical } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

// Sprint 5 Parte 13: hub de due diligence B2G
export const metadata: Metadata = {
  title: 'Due Diligence B2G — Consulta CEIS e CNEP por CNPJ',
  description:
    'Verifique se um fornecedor possui sanções no CEIS (Cadastro de Empresas Inidôneas) ' +
    'ou penalidades no CNEP antes de contratar ou participar de licitação. Dados do Portal da Transparência.',
  alternates: { canonical: buildCanonical('/compliance') },
  robots: { index: true, follow: true },
  openGraph: {
    title: 'Due Diligence B2G — Consulta CEIS e CNEP | SmartLic',
    description: 'Verifique sanções e impedimentos de fornecedores antes de licitar. Dados do Portal da Transparência.',
    type: 'website',
    locale: 'pt_BR',
  },
};

const EXEMPLOS_CONSULTA = [
  { label: 'Como consultar CEIS pelo CNPJ',     slug: 'consulta-ceis-cnpj' },
  { label: 'O que é o CNEP',                    slug: 'o-que-e-cnep' },
  { label: 'Empresa pode licitar com sanção?',  slug: 'empresa-sancao-licitar' },
];

const jsonLd = [
  {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: 'Due Diligence B2G — Consulta CEIS e CNEP por CNPJ',
    description:
      'Ferramenta para verificação de sanções e impedimentos de fornecedores ' +
      'nos cadastros CEIS e CNEP do Portal da Transparência do Governo Federal.',
    url: 'https://smartlic.tech/compliance',
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      url: 'https://smartlic.tech',
    },
  },
  {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'SmartLic', item: 'https://smartlic.tech' },
      { '@type': 'ListItem', position: 2, name: 'Due Diligence B2G', item: 'https://smartlic.tech/compliance' },
    ],
  },
];

export default function ComplianceHubPage() {
  return (
    <>
      <LandingNavbar />
      <main className="min-h-screen bg-gray-50 pt-20 pb-16">
        {jsonLd.map((ld, i) => (
          <script
            key={i}
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }}
          />
        ))}

        {/* Breadcrumb */}
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 text-sm text-gray-500">
          <Link href="/" className="hover:text-blue-600">SmartLic</Link>
          <span className="mx-1">/</span>
          <span className="text-gray-900 font-medium">Due Diligence B2G</span>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Due Diligence B2G — Consulta CEIS e CNEP
          </h1>
          <p className="text-gray-600 mb-8 max-w-2xl">
            Verifique se um fornecedor ou concorrente possui sanções ativas no CEIS
            (Cadastro de Empresas Inidôneas e Suspensas) ou penalidades no CNEP
            (Cadastro Nacional de Empresas Punidas), antes de participar de uma licitação
            ou fechar um contrato. Dados diários do Portal da Transparência.
          </p>

          {/* Explicação dos cadastros */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-10">
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">O que é o CEIS?</h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                O Cadastro de Empresas Inidôneas e Suspensas (CEIS) registra pessoas físicas e
                jurídicas que sofreram sanções de inidoneidade ou suspensão do direito de contratar
                com o Poder Público. Empresas no CEIS com sanções ativas estão impedidas de participar
                de licitações em qualquer esfera do governo.
              </p>
            </div>
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">O que é o CNEP?</h2>
              <p className="text-sm text-gray-600 leading-relaxed">
                O Cadastro Nacional de Empresas Punidas (CNEP) registra sanções aplicadas com base na
                Lei Anticorrupção (Lei 12.846/2013), incluindo multas e proibições de contratar com
                o poder público por atos lesivos à administração pública. Um registro no CNEP pode
                indicar histórico de corrupção ou fraude em licitações.
              </p>
            </div>
          </div>

          {/* Instruções de uso */}
          <section className="bg-white rounded-lg border p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Como consultar</h2>
            <p className="text-sm text-gray-600 mb-4">
              Para consultar a situação de um fornecedor, acesse diretamente a URL com o CNPJ
              da empresa (14 dígitos, somente números):
            </p>
            <div className="bg-gray-50 rounded-lg p-4 font-mono text-sm text-blue-700">
              smartlic.tech/compliance/<span className="font-bold">14digitosdoCNPJ</span>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              Exemplo: smartlic.tech/compliance/00000000000191 verifica a Caixa Econômica Federal.
            </p>
          </section>

          {/* Artigos relacionados */}
          {EXEMPLOS_CONSULTA.length > 0 && (
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Dúvidas Frequentes</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {EXEMPLOS_CONSULTA.map((e) => (
                  <Link
                    key={e.slug}
                    href={`/perguntas/${e.slug}`}
                    className="bg-white rounded-lg border border-gray-200 px-4 py-3 text-sm text-blue-600 hover:border-blue-400 hover:shadow-sm transition-all"
                  >
                    {e.label}
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* CTA */}
          <section className="mt-4 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore a situação dos seus concorrentes automaticamente
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic verifica periodicamente a situação de fornecedores relevantes
              para o seu mercado e notifica você sobre mudanças de status nos cadastros
              governamentais.
            </p>
            <Link
              href="/signup"
              className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Teste grátis por 14 dias
            </Link>
          </section>
        </div>
      </main>
      <Footer />
    </>
  );
}
