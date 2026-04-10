import { Metadata } from 'next';
import Link from 'next/link';
import { buildCanonical } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

// Sprint 6 Parte 13: hub de benchmark de preços por CATMAT
export const metadata: Metadata = {
  title: 'Benchmark de Preços Governamentais por CATMAT — Substitui Painel de Preços | SmartLic',
  description:
    'Consulte o preço médio (P10, P50, P90) que o governo federal paga por materiais e serviços. ' +
    'Dados reais do PNCP — substitui o Painel de Preços do ComprasGov (descontinuado jul/2025).',
  alternates: { canonical: buildCanonical('/itens') },
  robots: { index: true, follow: true },
  openGraph: {
    title: 'Benchmark de Preços Governamentais — SmartLic',
    description: 'P10/P50/P90 de materiais e serviços comprados pelo governo federal. Dados do PNCP.',
    type: 'website',
    locale: 'pt_BR',
  },
};

interface CatmatDestaque {
  catmat: string;
  nome: string;
  categoria: string;
}

const DESTAQUES_POR_CATEGORIA: { categoria: string; itens: CatmatDestaque[] }[] = [
  {
    categoria: 'Materiais de Escritório',
    itens: [
      { catmat: '109210', nome: 'Papel A4 75g/m²',              categoria: 'Materiais de Escritório' },
      { catmat: '109218', nome: 'Caneta esferográfica azul',     categoria: 'Materiais de Escritório' },
      { catmat: '109228', nome: 'Lápis preto nº 2',             categoria: 'Materiais de Escritório' },
      { catmat: '109260', nome: 'Grampo 26/6',                   categoria: 'Materiais de Escritório' },
      { catmat: '109290', nome: 'Fita adesiva transparente',     categoria: 'Materiais de Escritório' },
      { catmat: '109300', nome: 'Corretivo líquido',             categoria: 'Materiais de Escritório' },
    ],
  },
  {
    categoria: 'Limpeza e Higiene',
    itens: [
      { catmat: '220050', nome: 'Papel higiênico folha simples', categoria: 'Limpeza e Higiene' },
      { catmat: '220080', nome: 'Detergente líquido neutro',     categoria: 'Limpeza e Higiene' },
      { catmat: '220090', nome: 'Desinfetante pinho',            categoria: 'Limpeza e Higiene' },
      { catmat: '220100', nome: 'Água sanitária',               categoria: 'Limpeza e Higiene' },
      { catmat: '220110', nome: 'Álcool 70 graus',              categoria: 'Limpeza e Higiene' },
      { catmat: '220120', nome: 'Saco de lixo 100L preto',       categoria: 'Limpeza e Higiene' },
    ],
  },
  {
    categoria: 'Informática',
    itens: [
      { catmat: '330010', nome: 'Computador desktop',            categoria: 'Informática' },
      { catmat: '330020', nome: 'Monitor LED 21 pol.',           categoria: 'Informática' },
      { catmat: '330030', nome: 'Notebook 15 pol.',              categoria: 'Informática' },
      { catmat: '330040', nome: 'Impressora laser monocromática',categoria: 'Informática' },
      { catmat: '330060', nome: 'Mouse óptico USB',              categoria: 'Informática' },
      { catmat: '330080', nome: 'Nobreak 600VA',                 categoria: 'Informática' },
    ],
  },
  {
    categoria: 'Material de Saúde',
    itens: [
      { catmat: '440010', nome: 'Seringa descartável 10ml',      categoria: 'Material de Saúde' },
      { catmat: '440030', nome: 'Gaze estéril 10x10',            categoria: 'Material de Saúde' },
      { catmat: '440060', nome: 'Soro fisiológico 250ml',        categoria: 'Material de Saúde' },
      { catmat: '440070', nome: 'Termômetro digital axilar',     categoria: 'Material de Saúde' },
      { catmat: '440090', nome: 'Oxímetro de pulso',             categoria: 'Material de Saúde' },
      { catmat: '440110', nome: 'Cadeira de rodas',              categoria: 'Material de Saúde' },
    ],
  },
  {
    categoria: 'Construção Civil',
    itens: [
      { catmat: '550010', nome: 'Cimento CP-II 50kg',            categoria: 'Construção Civil' },
      { catmat: '550020', nome: 'Tijolo cerâmico 9 furos',       categoria: 'Construção Civil' },
      { catmat: '550060', nome: 'Tinta látex PVA branca 18L',   categoria: 'Construção Civil' },
      { catmat: '550110', nome: 'Fio elétrico 2,5mm 100m',      categoria: 'Construção Civil' },
      { catmat: '550120', nome: 'Disjuntor bipolar 20A',         categoria: 'Construção Civil' },
      { catmat: '550130', nome: 'Tubo PVC esgoto 100mm 6m',     categoria: 'Construção Civil' },
    ],
  },
  {
    categoria: 'Gêneros Alimentícios',
    itens: [
      { catmat: '770010', nome: 'Arroz agulhinha tipo 1 5kg',    categoria: 'Gêneros Alimentícios' },
      { catmat: '770020', nome: 'Feijão carioca tipo 1 1kg',     categoria: 'Gêneros Alimentícios' },
      { catmat: '770060', nome: 'Leite longa vida integral 1L',  categoria: 'Gêneros Alimentícios' },
      { catmat: '770070', nome: 'Frango inteiro congelado kg',   categoria: 'Gêneros Alimentícios' },
      { catmat: '770050', nome: 'Café torrado moído 500g',       categoria: 'Gêneros Alimentícios' },
      { catmat: '770090', nome: 'Ovos brancos dúzia',            categoria: 'Gêneros Alimentícios' },
    ],
  },
  {
    categoria: 'Mobiliário',
    itens: [
      { catmat: '990010', nome: 'Cadeira giratória com braço',   categoria: 'Mobiliário' },
      { catmat: '990020', nome: 'Mesa de escritório 1,20x0,60m', categoria: 'Mobiliário' },
      { catmat: '990030', nome: 'Armário de aço 2 portas',       categoria: 'Mobiliário' },
      { catmat: '990040', nome: 'Estante de aço 6 prateleiras',  categoria: 'Mobiliário' },
      { catmat: '990060', nome: 'Cadeira plástica sem braço',    categoria: 'Mobiliário' },
      { catmat: '990080', nome: 'Arquivo de aço 4 gavetas',      categoria: 'Mobiliário' },
    ],
  },
];

const jsonLd = [
  {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Benchmark de Preços Governamentais por CATMAT — SmartLic',
    description:
      'Diretório de benchmarks de preços governamentais por código CATMAT, ' +
      'com P10/P50/P90 calculados a partir de contratos reais do PNCP.',
    url: 'https://smartlic.tech/itens',
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
      { '@type': 'ListItem', position: 2, name: 'Benchmark de Preços', item: 'https://smartlic.tech/itens' },
    ],
  },
];

export default function ItensHubPage() {
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
          <span className="text-gray-900 font-medium">Benchmark de Preços</span>
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-3">
            <span className="inline-block text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-medium">
              Substitui o Painel de Preços do ComprasGov (descontinuado jul/2025)
            </span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Benchmark de Preços Governamentais
          </h1>
          <p className="text-gray-600 mb-8 max-w-2xl">
            Consulte quanto o governo federal paga por materiais e serviços, com
            preços P10 (mínimo), P50 (mediano) e P90 (máximo) calculados a partir
            de contratos reais registrados no PNCP. Dados atualizados diariamente.
          </p>

          {/* Categorias com itens em destaque */}
          {DESTAQUES_POR_CATEGORIA.map((cat) => (
            <section key={cat.categoria} className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{cat.categoria}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {cat.itens.map((item) => (
                  <Link
                    key={item.catmat}
                    href={`/itens/${item.catmat}`}
                    className="bg-white rounded-lg border border-gray-200 px-4 py-3 hover:border-blue-400 hover:shadow-sm transition-all group"
                  >
                    <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700 line-clamp-2">
                      {item.nome}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">CATMAT {item.catmat}</p>
                  </Link>
                ))}
              </div>
            </section>
          ))}

          {/* Sobre o CATMAT */}
          <section className="bg-white rounded-lg border p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">O que é o código CATMAT?</h2>
            <p className="text-sm text-gray-600 leading-relaxed">
              O CATMAT (Catálogo de Materiais) é o sistema oficial do Governo Federal para
              padronização de materiais utilizados nas compras públicas. Cada item recebe um
              código numérico único que facilita a comparação de preços entre diferentes
              órgãos e processos licitatórios. O SmartLic agrega os contratos do Portal
              Nacional de Contratações Públicas (PNCP) para calcular benchmarks de preço
              por código CATMAT, preenchendo o vazio deixado pelo descontinuado Painel de
              Preços do ComprasGov.
            </p>
          </section>

          {/* CTA */}
          <section className="mt-4 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore licitações de materiais específicos
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic rastreia editais abertos no PNCP e identifica automaticamente
              oportunidades de fornecimento para os materiais e serviços do seu portfólio.
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
