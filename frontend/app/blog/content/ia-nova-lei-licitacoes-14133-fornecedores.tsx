import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — CLUSTER-IA-08: IA e a Nova Lei de Licitações (14.133)
 *
 * Content cluster: IA em Licitações (fundo de funil)
 * Target: ~3,000 words | Primary KW: IA nova lei licitações 14133
 */
export default function IaNovaLeiLicitacoes14133Fornecedores() {
  return (
    <>
      {/* FAQPage JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: [
              {
                '@type': 'Question',
                name: 'O que a Lei 14.133/2021 mudou para fornecedores que participam de licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 substituiu a Lei 8.666/93 e trouxe mudanças estruturais: publicação obrigatória no PNCP (Portal Nacional de Contratações Públicas), novas modalidades como diálogo competitivo, critérios de sustentabilidade obrigatórios, e prazos revisados para cada modalidade. Para fornecedores, o impacto principal foi a centralização de dados no PNCP — o que aumentou a transparência mas também criou uma sobrecarga de informação que tornou a triagem manual inviável para a maioria das empresas.',
                },
              },
              {
                '@type': 'Question',
                name: 'O PNCP é obrigatório para todos os órgãos públicos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, a partir de 2024. A Lei 14.133 tornou obrigatória a publicação de todas as contratações públicas no PNCP — federal, estadual e municipal. Na prática, a adesão municipal ainda é parcial: alguns municípios menores publicam com atraso ou de forma incompleta. Órgãos federais e a maioria dos estaduais já publicam de forma consistente.',
                },
              },
              {
                '@type': 'Question',
                name: 'A IA consegue acompanhar as mudanças da Lei 14.133?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, para as mudanças que se refletem nos dados publicados. A IA classifica automaticamente editais com novas modalidades (diálogo competitivo, concurso), identifica critérios de sustentabilidade em descrições, e processa o volume crescente de publicações no PNCP. O que a IA não faz é interpretar mudanças jurisprudenciais ou regulamentações locais que não estão descritas no texto do edital — isso exige revisão humana especializada.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como a publicação obrigatória no PNCP afeta empresas pequenas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Paradoxalmente, a obrigatoriedade aumentou e reduziu a transparência ao mesmo tempo. Aumentou porque todas as licitações estão em um portal único. Reduziu porque o volume de publicações triplicou — de cerca de 25.000 por mês em 2024 para mais de 70.000 em Q1/2026 — tornando impossível para uma empresa sem ferramentas monitorar tudo manualmente. Empresas com IA e filtros inteligentes se beneficiam; empresas sem essas ferramentas ficam mais perdidas que antes.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais modalidades de licitação a Lei 14.133 criou ou modificou?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133 manteve o pregão eletrônico (que continua sendo a modalidade mais usada, ~84% das publicações), reformulou a concorrência e o leilão, e criou o diálogo competitivo — modalidade para contratos complexos onde o órgão discute soluções com os fornecedores antes de definir o objeto. A tomada de preços e o convite foram extintos. Para ferramentas de IA, cada modalidade tem pesos diferentes na análise de viabilidade.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais critérios de sustentabilidade a nova lei exige?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133 (art. 11, IV e art. 144) torna obrigatória a consideração de desenvolvimento nacional sustentável nas contratações públicas. Na prática, editais incluem critérios como certificações ambientais, eficiência energética, destinação de resíduos e política de logística reversa. Ferramentas de IA podem identificar automaticamente editais com cláusulas de sustentabilidade, permitindo que empresas com certificações ESG filtrem oportunidades onde têm vantagem competitiva.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A <strong>Lei 14.133/2021</strong> — a Nova Lei de Licitações —
        transformou o cenário de compras públicas no Brasil. Para fornecedores,
        a mudança mais impactante não foi uma cláusula específica: foi o efeito
        colateral da centralização obrigatória no PNCP. O volume de publicações
        triplicou em dois anos, criando uma sobrecarga de informação que tornou
        a triagem manual economicamente inviável. Este artigo analisa as
        mudanças artigo por artigo, mostra como ferramentas de{' '}
        <strong>inteligência artificial</strong> se adaptam a cada uma, e
        explica por que a nova lei acidentalmente criou o melhor argumento a
        favor da automação.
      </p>

      <h2>O que a Lei 14.133 mudou para fornecedores</h2>

      <p>
        A Lei 14.133/2021 substituiu a Lei 8.666/93 (após 30 anos de vigência),
        a Lei do Pregão (10.520/2002) e a Lei do RDC (12.462/2011). As
        mudanças mais relevantes para fornecedores que participam de licitações:
      </p>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-3 font-semibold text-ink">Aspecto</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Lei 8.666/93 (antiga)</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Lei 14.133/2021 (nova)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-3 font-medium">Publicação</td>
              <td className="py-3 px-3">Diário Oficial + jornal de grande circulação</td>
              <td className="py-3 px-3">PNCP obrigatório para todos os entes</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Modalidades</td>
              <td className="py-3 px-3">5 modalidades (convite, tomada de preços, concorrência, leilão, concurso)</td>
              <td className="py-3 px-3">5 modalidades (pregão, concorrência, concurso, leilão, diálogo competitivo)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Pregão eletrônico</td>
              <td className="py-3 px-3">Bens e serviços comuns</td>
              <td className="py-3 px-3">Bens e serviços comuns + obras até R$1,5M (lei complementar)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Sustentabilidade</td>
              <td className="py-3 px-3">Recomendação (Decreto 7.746/12)</td>
              <td className="py-3 px-3">Obrigatória (art. 11, IV)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Controle</td>
              <td className="py-3 px-3">TCU + tribunais estaduais</td>
              <td className="py-3 px-3">TCU + PNCP como instrumento de transparência</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Sanções</td>
              <td className="py-3 px-3">Advertência, multa, suspensão, declaração de inidoneidade</td>
              <td className="py-3 px-3">Advertência, multa, impedimento, declaração de inidoneidade (com prazos definidos)</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p>
        Para um guia completo sobre a{' '}
        <Link href="/blog/lei-14133-guia-fornecedores">
          Lei 14.133 para fornecedores
        </Link>
        , incluindo prazos, modalidades e exigências de habilitação, consulte
        o artigo dedicado.
      </p>

      <h2>O efeito colateral da transparência — sobrecarga de informação</h2>

      <p>
        A Lei 14.133 foi desenhada para aumentar a transparência nas
        contratações públicas. E conseguiu: o PNCP centralizou publicações que
        antes estavam dispersas em Diários Oficiais de 5.570 municípios. Mas o
        efeito colateral foi devastador para fornecedores sem ferramentas de
        automação.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Crescimento de publicações no PNCP — impacto da obrigatoriedade
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>2024 (início da obrigatoriedade):</strong> ~25.000 publicações/mês — adesão parcial, principalmente federal
          </li>
          <li>
            <strong>2025 (expansão estadual):</strong> ~45.000 publicações/mês — a maioria dos estados aderiu
          </li>
          <li>
            <strong>Q1/2026 (maturidade):</strong> ~70.000+ publicações/mês — 800K+ no ano, incluindo municipais
          </li>
          <li>
            <strong>Crescimento:</strong> 180% em 2 anos — triplicou o volume que fornecedores precisam processar
          </li>
        </ul>
      </div>

      <p>
        A ironia: a lei que deveria nivelar o campo para todos os fornecedores
        criou uma vantagem estrutural para quem tem ferramentas de filtragem.
        Uma empresa com IA processa 70.000 publicações/mês em horas. Uma
        empresa sem ferramentas gasta semanas tentando — e inevitavelmente
        perde prazos.
      </p>

      <h2>Como a IA resolve cada desafio da nova lei</h2>

      <h3>PNCP obrigatório → IA monitora 24/7, humano revisa os relevantes</h3>

      <p>
        A centralização no PNCP é uma boa notícia para a IA: em vez de crawlar
        dezenas de fontes com formatos diferentes, o pipeline pode se concentrar
        em uma API estruturada. O SmartLic ingere dados do PNCP 3 vezes ao dia
        (8h, 14h, 20h), cobre 27 UFs × 6 modalidades, e classifica cada
        publicação por setor automaticamente. O analista humano revisa apenas os
        15-25 editais mais relevantes do dia — não os 3.200+ que foram
        publicados.
      </p>

      <h3>Novas modalidades → IA classifica automaticamente</h3>

      <p>
        O diálogo competitivo — modalidade nova da Lei 14.133 para contratos
        complexos — tem características distintas: objeto indefinido
        inicialmente, múltiplas fases, e prazos mais longos. A IA identifica
        essas modalidades pela classificação do código (modalidade 12 no PNCP) e
        ajusta o peso na análise de viabilidade: o prazo mais longo aumenta o
        score, o objeto indefinido reduz a precisão de classificação setorial.
      </p>

      <BlogInlineCTA
        slug="ia-nova-lei-licitacoes-14133-fornecedores"
        campaign="guias"
        ctaMessage="IA filtra editais da Lei 14.133 — Dado público verificável."
        ctaText="Começar Trial Gratuito"
      />

      <h3>Critérios de sustentabilidade → IA identifica cláusulas ESG</h3>

      <p>
        O artigo 11, IV da Lei 14.133 torna obrigatória a consideração de
        desenvolvimento sustentável. Na prática, editais incluem termos como
        &ldquo;certificação ISO 14001&rdquo;, &ldquo;eficiência energética
        classe A&rdquo;, &ldquo;logística reversa&rdquo; e &ldquo;crédito de
        carbono&rdquo;. A classificação por IA pode identificar
        automaticamente editais com critérios ESG — permitindo que empresas
        com certificações ambientais filtrem oportunidades onde têm vantagem
        competitiva sobre concorrentes não certificados.
      </p>

      <h3>Registro cadastral centralizado → IA cruza dados SICAF + PNCP</h3>

      <p>
        A Lei 14.133 reforçou o papel do{' '}
        <Link href="/blog/sicaf-como-cadastrar-manter-ativo-2026">
          SICAF como cadastro federal centralizado
        </Link>
        . Para fornecedores, isso significa que a habilitação em um órgão vale
        para todos. Para ferramentas de IA, a padronização do cadastro
        simplifica a verificação de elegibilidade: é possível cruzar dados do
        SICAF com requisitos do edital para identificar automaticamente se a
        empresa atende aos critérios de habilitação antes de investir tempo na
        análise detalhada.
      </p>

      <h2>O PNCP como fonte única de verdade</h2>

      <p>
        Antes da Lei 14.133, monitorar licitações no Brasil exigia consultar
        dezenas de fontes: Diários Oficiais estaduais, portais de compras
        municipais, ComprasGov federal, bolsas de licitação privadas. Cada
        fonte com formato, frequência e cobertura diferentes. O PNCP
        consolidou tudo — mas o volume bruto é inacessível sem filtro.
      </p>

      <p>
        Para entender como o{' '}
        <Link href="/blog/pncp-guia-completo-empresas">
          PNCP funciona na prática
        </Link>
        , incluindo como buscar editais, filtrar por setor e UF, e acompanhar
        publicações, consulte o guia completo. A camada de IA transforma o
        PNCP de um repositório de dados brutos em um feed curado e priorizado
        — mostrando apenas o que é relevante para o perfil de cada empresa.
      </p>

      <h2>Dados exclusivos — crescimento do PNCP e impacto na triagem</h2>

      <p>
        O pipeline de ingestão do SmartLic processa todas as publicações do
        PNCP diariamente. Os dados de crescimento permitem quantificar o
        impacto da Lei 14.133 na operação de triagem:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Impacto da Lei 14.133 no volume de dados — SmartLic base de dados
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>800K+ publicações processadas</strong> em Q1/2026 pelo pipeline de ingestão SmartLic
          </li>
          <li>
            <strong>~3.200 publicações/dia útil</strong> — impossível revisar manualmente (levaria 16+ horas a 3 minutos/edital)
          </li>
          <li>
            <strong>Apenas 3-7% relevantes</strong> para qualquer setor específico — a IA filtra os outros 93-97%
          </li>
          <li>
            <strong>84% são pregão eletrônico</strong> — a modalidade mais frequente e com prazos mais curtos (3-8 dias úteis)
          </li>
          <li>
            <strong>Média de 4-8h de latência</strong> entre publicação no PNCP e disponibilidade na plataforma com classificação
          </li>
        </ul>
      </div>

      <p>
        Para{' '}
        <Link href="/blog/ia-licitacoes-pequenas-empresas-mei-epp">
          pequenas empresas e MEIs
        </Link>
        , a Lei 14.133 manteve as preferências da LC 123 — mas o volume
        crescente de publicações torna ainda mais necessário o uso de
        ferramentas para identificar as oportunidades exclusivas para ME/EPP.
      </p>

      <h2>O que a lei NÃO resolveu (e a IA também não)</h2>

      <p>
        Transparência é necessária mas não suficiente. Apesar da centralização
        no PNCP, problemas estruturais persistem:
      </p>

      <ul className="list-disc pl-6 space-y-3">
        <li>
          <strong>Atraso na publicação municipal:</strong> alguns municípios
          menores publicam no PNCP dias após a abertura do certame, quando o
          prazo para participação já encerrou. A IA não pode encontrar o que
          ainda não foi publicado.
        </li>
        <li>
          <strong>Inconsistências entre DO e PNCP:</strong> existem casos em
          que a versão do Diário Oficial difere da versão no PNCP (erros de
          digitação, valores diferentes, prazos inconsistentes). A IA processa
          o que encontra no PNCP — não faz reconciliação automática com DOs.
        </li>
        <li>
          <strong>Descrições de objeto genéricas:</strong> mesmo com a nova lei,
          muitos órgãos publicam descrições vagas como &ldquo;aquisição de
          materiais diversos&rdquo;, o que dificulta a classificação setorial
          — tanto por IA quanto por humanos.
        </li>
        <li>
          <strong>Regulamentação estadual heterogênea:</strong> cada estado
          pode regulamentar aspectos da Lei 14.133 de forma diferente,
          criando variações que a IA não captura automaticamente nos textos
          dos editais.
        </li>
      </ul>

      <p>
        Para uma visão completa das{' '}
        <Link href="/blog/ia-licitacoes-limitacoes-o-que-nao-faz">
          limitações da IA em licitações
        </Link>
        , incluindo 5 coisas que nenhum vendedor menciona, veja o artigo
        dedicado.
      </p>

      <h2>Linha do tempo: transição da Lei 8.666 para a Lei 14.133</h2>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-3 font-semibold text-ink">Data</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Marco</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Impacto para fornecedores</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-3 font-medium">Abril/2021</td>
              <td className="py-3 px-3">Lei 14.133 sancionada</td>
              <td className="py-3 px-3">Período de transição de 2 anos (convivência das leis)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">2021-2023</td>
              <td className="py-3 px-3">Convivência Lei 8.666 + 14.133</td>
              <td className="py-3 px-3">Órgãos escolhiam qual lei aplicar por edital</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Dezembro/2023</td>
              <td className="py-3 px-3">Fim da convivência</td>
              <td className="py-3 px-3">Lei 8.666 revogada — Lei 14.133 exclusiva</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">2024</td>
              <td className="py-3 px-3">PNCP obrigatório para todos</td>
              <td className="py-3 px-3">Volume de publicações cresce 80%+</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">2025-2026</td>
              <td className="py-3 px-3">Maturidade do PNCP</td>
              <td className="py-3 px-3">800K+ publicações/ano — triagem manual inviável</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>O futuro: regulamentação e novas exigências</h2>

      <p>
        A Lei 14.133 continua sendo regulamentada por decretos e instruções
        normativas. Mudanças previstas para 2026-2027 incluem a ampliação do
        catálogo de materiais no PNCP (padronização de códigos), integração
        com o novo SICAF digital, e possível criação de um marketplace público
        para compras de baixo valor.
      </p>

      <p>
        Para ferramentas de IA, cada nova regulamentação é uma oportunidade
        de agregar mais valor: quanto mais estruturados os dados no PNCP, maior
        a precisão da classificação. A tendência é que a combinação Lei 14.133
        + PNCP + IA torne o mercado de licitações progressivamente mais
        acessível para fornecedores de todos os portes — desde que tenham as
        ferramentas adequadas para navegar o volume.
      </p>

      <p>
        Para entender como a{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona">
          inteligência artificial funciona na prática
        </Link>{' '}
        dentro desse novo cenário regulatório, incluindo o pipeline de
        classificação de 3 camadas e a análise de viabilidade, consulte o
        artigo hub do cluster.
      </p>

      <h2>Perguntas frequentes</h2>

      <h3>O que a Lei 14.133/2021 mudou para fornecedores?</h3>
      <p>
        As mudanças principais são: publicação obrigatória no PNCP (todas as
        licitações em um portal único), novas modalidades (diálogo competitivo),
        critérios de sustentabilidade obrigatórios, e prazos revisados. O
        impacto prático maior é o volume: as publicações triplicaram em 2 anos.
      </p>

      <h3>O PNCP é obrigatório para todos os órgãos?</h3>
      <p>
        Sim, desde 2024. Federal, estadual e municipal. Na prática, a adesão
        municipal ainda é parcial — alguns municípios publicam com atraso.
        Órgãos federais e estaduais já publicam de forma consistente.
      </p>

      <h3>A IA acompanha as mudanças da Lei 14.133?</h3>
      <p>
        Sim, para mudanças que se refletem nos dados. A IA classifica novas
        modalidades, identifica critérios ESG, e processa o volume crescente.
        Não interpreta jurisprudência ou regulamentações locais não presentes
        no texto do edital.
      </p>

      <h3>A publicação obrigatória no PNCP ajuda ou atrapalha empresas pequenas?</h3>
      <p>
        Ambos. Ajuda porque centraliza informação. Atrapalha porque o volume
        triplicou — sem ferramentas, é impossível processar 70K+ publicações/mês.
        Empresas com IA se beneficiam; empresas sem ferramentas ficam mais
        perdidas.
      </p>

      <h3>Quais modalidades a Lei 14.133 criou?</h3>
      <p>
        Criou o diálogo competitivo (para contratos complexos). Manteve pregão,
        concorrência, concurso e leilão (reformulados). Extinguiu convite e
        tomada de preços. Pregão eletrônico continua sendo ~84% das
        publicações.
      </p>

      <h3>Quais critérios de sustentabilidade a nova lei exige?</h3>
      <p>
        O art. 11, IV torna obrigatória a consideração de desenvolvimento
        sustentável. Editais incluem certificações ambientais, eficiência
        energética, logística reversa. IA identifica automaticamente editais
        com cláusulas ESG — vantagem para empresas certificadas.
      </p>

      <h2>Fontes</h2>

      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos
        </li>
        <li>
          PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br)
        </li>
        <li>
          Decreto 10.764/2021 — Regulamenta o PNCP
        </li>
        <li>
          Lei 8.666/1993 — Lei de Licitações revogada (referência comparativa)
        </li>
        <li>
          SmartLic base de dados — volume de publicações PNCP, 2024-2026 (800K+ processadas Q1/2026)
        </li>
      </ul>
    </>
  );
}
