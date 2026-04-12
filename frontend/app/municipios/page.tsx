import { Metadata } from 'next';
import Link from 'next/link';
import { buildCanonical } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

// Sprint 4 Parte 13: hub de municípios para SEO programático
export const metadata: Metadata = {
  title: 'Licitações por Município — Editais Abertos nas Principais Cidades',
  description:
    'Consulte licitações abertas nos principais municípios brasileiros. ' +
    'Dados diários do PNCP com população IBGE e histórico de compras públicas.',
  alternates: { canonical: buildCanonical('/municipios') },
  robots: { index: true, follow: true },
  openGraph: {
    title: 'Licitações por Município — SmartLic',
    description: 'Editais abertos nas principais cidades do Brasil, atualizados diariamente.',
    type: 'website',
    locale: 'pt_BR',
  },
};

// Capitais para destaque no hub
const CAPITAIS = [
  { slug: 'sao-paulo-sp',       nome: 'São Paulo',     uf: 'SP' },
  { slug: 'rio-de-janeiro-rj',  nome: 'Rio de Janeiro', uf: 'RJ' },
  { slug: 'brasilia-df',        nome: 'Brasília',      uf: 'DF' },
  { slug: 'belo-horizonte-mg',  nome: 'Belo Horizonte', uf: 'MG' },
  { slug: 'salvador-ba',        nome: 'Salvador',      uf: 'BA' },
  { slug: 'fortaleza-ce',       nome: 'Fortaleza',     uf: 'CE' },
  { slug: 'curitiba-pr',        nome: 'Curitiba',      uf: 'PR' },
  { slug: 'manaus-am',          nome: 'Manaus',        uf: 'AM' },
  { slug: 'recife-pe',          nome: 'Recife',        uf: 'PE' },
  { slug: 'porto-alegre-rs',    nome: 'Porto Alegre',  uf: 'RS' },
  { slug: 'belem-pa',           nome: 'Belém',         uf: 'PA' },
  { slug: 'goiania-go',         nome: 'Goiânia',       uf: 'GO' },
  { slug: 'sao-luis-ma',        nome: 'São Luís',      uf: 'MA' },
  { slug: 'maceio-al',          nome: 'Maceió',        uf: 'AL' },
  { slug: 'natal-rn',           nome: 'Natal',         uf: 'RN' },
  { slug: 'teresina-pi',        nome: 'Teresina',      uf: 'PI' },
  { slug: 'campo-grande-ms',    nome: 'Campo Grande',  uf: 'MS' },
  { slug: 'joao-pessoa-pb',     nome: 'João Pessoa',   uf: 'PB' },
  { slug: 'aracaju-se',         nome: 'Aracaju',       uf: 'SE' },
  { slug: 'porto-velho-ro',     nome: 'Porto Velho',   uf: 'RO' },
  { slug: 'macapa-ap',          nome: 'Macapá',        uf: 'AP' },
  { slug: 'cuiaba-mt',          nome: 'Cuiabá',        uf: 'MT' },
  { slug: 'florianopolis-sc',   nome: 'Florianópolis', uf: 'SC' },
  { slug: 'vitoria-es',         nome: 'Vitória',       uf: 'ES' },
  { slug: 'palmas-to',          nome: 'Palmas',        uf: 'TO' },
  { slug: 'rio-branco-ac',      nome: 'Rio Branco',    uf: 'AC' },
  { slug: 'boa-vista-rr',       nome: 'Boa Vista',     uf: 'RR' },
];

// Principais polos regionais
const POLOS = [
  { slug: 'campinas-sp',             nome: 'Campinas',             uf: 'SP' },
  { slug: 'guarulhos-sp',            nome: 'Guarulhos',            uf: 'SP' },
  { slug: 'ribeirao-preto-sp',       nome: 'Ribeirão Preto',       uf: 'SP' },
  { slug: 'uberlandia-mg',           nome: 'Uberlândia',           uf: 'MG' },
  { slug: 'joinville-sc',            nome: 'Joinville',            uf: 'SC' },
  { slug: 'londrina-pr',             nome: 'Londrina',             uf: 'PR' },
  { slug: 'maringa-pr',              nome: 'Maringá',              uf: 'PR' },
  { slug: 'feira-de-santana-ba',     nome: 'Feira de Santana',     uf: 'BA' },
  { slug: 'juazeiro-do-norte-ce',    nome: 'Juazeiro do Norte',    uf: 'CE' },
  { slug: 'campina-grande-pb',       nome: 'Campina Grande',       uf: 'PB' },
  { slug: 'novo-hamburgo-rs',        nome: 'Novo Hamburgo',        uf: 'RS' },
  { slug: 'passo-fundo-rs',          nome: 'Passo Fundo',          uf: 'RS' },
  { slug: 'caxias-do-sul-rs',        nome: 'Caxias do Sul',        uf: 'RS' },
  { slug: 'anapolis-go',             nome: 'Anápolis',             uf: 'GO' },
  { slug: 'sobral-ce',               nome: 'Sobral',               uf: 'CE' },
  { slug: 'montes-claros-mg',        nome: 'Montes Claros',        uf: 'MG' },
  { slug: 'rondonopolis-mt',         nome: 'Rondonópolis',         uf: 'MT' },
  { slug: 'santarem-pa',             nome: 'Santarém',             uf: 'PA' },
  { slug: 'blumenau-sc',             nome: 'Blumenau',             uf: 'SC' },
  { slug: 'pelotas-rs',              nome: 'Pelotas',              uf: 'RS' },
];

const jsonLd = [
  {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Licitações por Município — SmartLic',
    description:
      'Diretório de licitações públicas abertas nos principais municípios brasileiros, ' +
      'com dados do PNCP e indicadores populacionais do IBGE.',
    url: 'https://smartlic.tech/municipios',
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
      { '@type': 'ListItem', position: 2, name: 'Municípios', item: 'https://smartlic.tech/municipios' },
    ],
  },
];

export default function MunicipiosHubPage() {
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
          <span className="text-gray-900 font-medium">Municípios</span>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Licitações por Município
          </h1>
          <p className="text-gray-600 mb-8 max-w-2xl">
            Consulte editais abertos, histórico de compras públicas e indicadores
            econômicos dos principais municípios do Brasil. Dados atualizados diariamente
            a partir do Portal Nacional de Contratações Públicas (PNCP) e do IBGE.
          </p>

          {/* Capitais */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Capitais Estaduais</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {CAPITAIS.map((c) => (
                <Link
                  key={c.slug}
                  href={`/municipios/${c.slug}`}
                  className="bg-white rounded-lg border border-gray-200 px-4 py-3 text-sm font-medium text-gray-800 hover:border-blue-400 hover:text-blue-700 hover:shadow-sm transition-all"
                >
                  {c.nome}
                  <span className="ml-1 text-xs text-gray-400">{c.uf}</span>
                </Link>
              ))}
            </div>
          </section>

          {/* Polos Regionais */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Principais Polos Regionais</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {POLOS.map((c) => (
                <Link
                  key={c.slug}
                  href={`/municipios/${c.slug}`}
                  className="bg-white rounded-lg border border-gray-200 px-4 py-3 text-sm font-medium text-gray-800 hover:border-blue-400 hover:text-blue-700 hover:shadow-sm transition-all"
                >
                  {c.nome}
                  <span className="ml-1 text-xs text-gray-400">{c.uf}</span>
                </Link>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="bg-blue-50 rounded-lg p-6 text-center mt-4">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore licitações em qualquer município
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic rastreia editais abertos no PNCP e filtra automaticamente
              as oportunidades mais relevantes para o seu setor e região.
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
