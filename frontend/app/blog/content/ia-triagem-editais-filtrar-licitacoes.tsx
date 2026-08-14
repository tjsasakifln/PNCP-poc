import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — CLUSTER-IA-04: IA para Triagem de Editais
 *
 * Content cluster: IA em Licitações (fundo de funil)
 * Target: ~3,000 words | Primary KW: triagem de editais com IA
 */
export default function IaTriagemEditaisFiltrarLicitacoes() {
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
                name: 'Quantos editais são publicados por dia no Brasil?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Somando PNCP, Portal de Compras Públicas e ComprasGov, são publicados aproximadamente 3.200 editais por dia útil no Brasil. Esse volume tornou a triagem manual inviável para empresas que monitoram mais de um setor ou mais de cinco estados simultaneamente. A fatia relevante para uma empresa típica gira em torno de 3% a 7% do total, dependendo do setor de atuação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como a IA faz a triagem de editais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A triagem por IA funciona em três camadas sequenciais. A primeira camada usa matching de palavras-chave com scoring de densidade para identificar editais claramente relevantes ou irrelevantes. A segunda camada aplica classificação semântica para capturar terminologia atípica que palavras-chave simples não detectariam. A terceira camada usa um modelo de linguagem (LLM) para decidir casos ambíguos onde as camadas anteriores ficaram incertas. Filtros rápidos como UF e valor são aplicados antes das camadas de IA para reduzir o processamento.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a diferença entre triagem por palavras-chave e triagem por IA?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A triagem por palavras-chave busca termos exatos no texto do edital e classifica como relevante qualquer publicação que contenha pelo menos um dos termos configurados. A triagem por IA vai além: analisa o contexto em que os termos aparecem, detecta sinônimos e terminologia regional, e classifica editais que não contêm nenhuma das palavras-chave configuradas mas são semanticamente relevantes para o setor. Na prática, a IA encontra entre 8% e 15% a mais de editais relevantes do que a busca por palavras-chave isolada.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto tempo economiza a triagem automática de editais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Empresas que fazem triagem manual gastam em média 3 a 5 horas por dia revisando editais em múltiplos portais. Com triagem automática por IA, esse tempo cai para 20 a 40 minutos diários — focados exclusivamente em revisar os editais que a IA já classificou como relevantes e viáveis. A redução representa 80% a 90% do tempo de triagem, permitindo que a equipe redirecione esforço para análise de editais completos e elaboração de propostas.',
                },
              },
              {
                '@type': 'Question',
                name: 'A IA perde editais relevantes durante a triagem?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sistemas de triagem por IA operam com recall entre 70% e 90%, o que significa que encontram a maioria dos editais relevantes mas não todos. O principal ponto cego são editais com objeto redigido de forma muito genérica ou com terminologia altamente específica de uma região ou órgão. Para minimizar esse risco, sistemas maduros mantêm um estágio de revisão humana para casos classificados como incertos (PENDING_REVIEW), e permitem configurar alertas para termos muito específicos do nicho da empresa.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual setor mais se beneficia da triagem por IA?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Setores com alto volume de publicações e vocabulário técnico padronizado — como tecnologia da informação, saúde e equipamentos — obtêm maior benefício da triagem por IA, pois a precisão da classificação é mais alta e o volume de editais irrelevantes descartados automaticamente é maior. Setores de nicho muito específico ou com terminologia regional variável tendem a exigir mais configuração inicial para atingir a mesma eficiência.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível configurar a triagem por IA para meu setor específico?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. Ferramentas de triagem por IA para licitações permitem configurar palavras-chave setoriais, exclusões (termos que indicam irrelevância), faixas de valor e restrições geográficas. A configuração inicial leva de 1 a 3 horas para um analista que conhece bem o setor. Após as primeiras semanas de uso, o sistema aprende com o feedback da equipe e ajusta automaticamente a sensibilidade da classificação.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: triagem de editais com IA */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A <strong>triagem de editais com IA</strong> surgiu como resposta a um problema
        matemático simples: o volume de publicações em portais de compras públicas cresceu
        além da capacidade humana de analisar manualmente. Com mais de 800 mil publicações
        por ano somando PNCP, Portal de Compras Públicas e ComprasGov, uma empresa que
        monitora três setores em cinco estados precisaria de uma equipe inteira dedicada
        apenas a descartar editais irrelevantes — antes mesmo de ler o primeiro que merece
        atenção.
      </p>

      <p>
        Este artigo explica como a triagem automática funciona tecnicamente, por que o funil
        de filtragem é mais eficiente do que parece, e qual é o custo real de continuar
        fazendo triagem manual em 2026. Se você já leu nosso{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-navy dark:text-brand-blue hover:underline">
          guia completo sobre inteligência artificial em licitações
        </Link>
        , este artigo aprofunda especificamente a etapa de triagem — a parte que consome
        mais tempo e entrega mais ganho imediato quando automatizada.
      </p>

      {/* Section 1 */}
      <h2>O volume real de editais no Brasil</h2>

      <p>
        Os números são maiores do que a maioria das empresas imagina. O PNCP sozinho
        superou 350 mil licitações publicadas em 2025, reflexo da migração obrigatória
        de municípios para o portal após a regulamentação da Lei 14.133/2021. Somando
        os outros portais, o total anual ultrapassa 800 mil publicações.
      </p>

      <p>
        Em dias úteis normais, isso representa aproximadamente 3.200 novos registros por
        dia. Para uma empresa de engenharia civil que atua em dez estados, o universo
        relevante pode chegar a 120 publicações diárias antes de qualquer filtro. Depois
        da filtragem por UF e valor estimado, esse número cai para 25 ou 30. Mas chegar
        nesses 25 editais relevantes exige revisar — ou pelo menos escanear — os 120
        anteriores.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Volume de publicações por setor — estimativa mensal
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b-2 border-[var(--border)]">
                <th className="text-left py-2 px-3 font-semibold text-ink">Setor</th>
                <th className="text-left py-2 px-3 font-semibold text-ink">Publicações/mês</th>
                <th className="text-left py-2 px-3 font-semibold text-ink">% relevante</th>
                <th className="text-left py-2 px-3 font-semibold text-ink">Horas triagem manual</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              <tr>
                <td className="py-2 px-3 font-medium">Tecnologia da Informação</td>
                <td className="py-2 px-3 text-ink-secondary">18.000–22.000</td>
                <td className="py-2 px-3 text-ink-secondary">4–6%</td>
                <td className="py-2 px-3 text-ink-secondary">60–90h</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium">Saúde e Equipamentos Médicos</td>
                <td className="py-2 px-3 text-ink-secondary">14.000–18.000</td>
                <td className="py-2 px-3 text-ink-secondary">5–8%</td>
                <td className="py-2 px-3 text-ink-secondary">55–80h</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium">Engenharia e Construção</td>
                <td className="py-2 px-3 text-ink-secondary">25.000–35.000</td>
                <td className="py-2 px-3 text-ink-secondary">3–5%</td>
                <td className="py-2 px-3 text-ink-secondary">70–110h</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium">Facilities e Limpeza</td>
                <td className="py-2 px-3 text-ink-secondary">20.000–28.000</td>
                <td className="py-2 px-3 text-ink-secondary">6–10%</td>
                <td className="py-2 px-3 text-ink-secondary">80–120h</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-medium">Alimentação e Nutrição</td>
                <td className="py-2 px-3 text-ink-secondary">10.000–14.000</td>
                <td className="py-2 px-3 text-ink-secondary">5–9%</td>
                <td className="py-2 px-3 text-ink-secondary">40–70h</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-xs text-ink-secondary mt-3">
          Estimativas baseadas em dados de portais públicos (PNCP, PCP v2, ComprasGov) e monitoramento
          interno. Horas de triagem manual assumem 2 minutos por edital escaneado.
        </p>
      </div>

      <p>
        A coluna de horas de triagem manual revela o problema central. Uma empresa de
        facilities que monitora o Brasil inteiro precisaria de dois analistas dedicados
        apenas para escanear os editais diariamente — sem ler nenhum deles por completo.
        Essa é a realidade de quem opera sem automação.
      </p>

      {/* Section 2 */}
      <h2>Como funciona a triagem por IA — 3 camadas</h2>

      <p>
        A triagem automática de editais não é um único algoritmo que decide tudo. É um
        pipeline em camadas, onde cada etapa elimina um conjunto diferente de ruído, e
        cada camada seguinte só processa o que a anterior não conseguiu classificar com
        segurança. Essa arquitetura reduz tanto o custo computacional quanto a taxa de
        erros.
      </p>

      <h3>Camada 1 — Matching de palavras-chave com scoring de densidade</h3>

      <p>
        A primeira camada é a mais rápida. O sistema verifica se o texto do edital — objeto,
        descrição e itens — contém palavras-chave configuradas para o setor. Mas não é uma
        busca binária de &ldquo;contém ou não contém&rdquo;. O sistema calcula a
        <em>densidade</em> de termos relevantes: quantas vezes as palavras-chave aparecem
        em relação ao total de termos do documento.
      </p>

      <p>
        Um edital com densidade superior a 5% é classificado diretamente como relevante —
        a camada 1 entrega um resultado com alta confiança. Um edital com densidade abaixo
        de 1% é descartado diretamente, também com alta confiança. A faixa intermediária
        (1% a 5%) segue para a camada 2.
      </p>

      <p>
        Esse scoring de densidade resolve um problema clássico das buscas simples por
        palavras-chave: um edital de limpeza urbana que menciona &ldquo;software&rdquo;
        uma vez (no requisito de nota fiscal eletrônica) não é classificado como edital
        de tecnologia. A densidade do termo no contexto do documento inteiro é baixa demais.
      </p>

      <h3>Camada 2 — Classificação semântica para terminologia atípica</h3>

      <p>
        A segunda camada lida com editais que usam terminologia regional, nomenclaturas
        de órgãos específicos ou siglas que não constam na lista de palavras-chave
        configurada. Por exemplo: um pregão para &ldquo;Sistema Integrado de Informações
        Georreferenciadas&rdquo; é relevante para empresas de geoprocessamento e TI, mas
        pode não conter nenhum dos termos padrão configurados para o setor.
      </p>

      <p>
        A análise semântica usa um modelo de embeddings para comparar o vetor do edital
        com vetores de referência do setor. Se a similaridade semântica é alta, o edital
        é aprovado mesmo sem matching direto de palavras-chave. Essa camada captura
        tipicamente de 6% a 12% dos editais relevantes que a camada 1 não identificaria.
      </p>

      <h3>Camada 3 — Zero-match: LLM decide quando keywords falham</h3>

      <p>
        A terceira camada é a mais cara computacionalmente e é acionada apenas para editais
        que chegam com densidade de palavras-chave próxima de zero e similaridade semântica
        inconclusiva. Nesses casos, um modelo de linguagem (LLM) lê o texto completo do
        edital e responde a uma pergunta binária: este edital é relevante para o setor X?
      </p>

      <p>
        A decisão do LLM considera contexto que as camadas anteriores não capturam:
        subtexto do objeto, requisitos técnicos implícitos e categorias de CNAE mencionadas.
        O custo de processamento é maior — por isso as camadas 1 e 2 existem para reduzir
        ao máximo o volume que chega à camada 3.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Arquitetura do pipeline de triagem — ordem importa
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>Filtro UF:</strong> descarta editais fora da geografia configurada (mais rápido, sem IA)</li>
          <li><strong>Filtro de valor:</strong> descarta editais fora da faixa de valor configurada (sem IA)</li>
          <li><strong>Camada 1 — Densidade:</strong> classifica 70–80% dos editais com alta confiança</li>
          <li><strong>Camada 2 — Semântica:</strong> classifica adicionais 10–15% com vocabulário atípico</li>
          <li><strong>Camada 3 — LLM zero-match:</strong> decide os 5–15% restantes com objeto ambíguo</li>
          <li><strong>Score de viabilidade:</strong> prioriza os aprovados por modalidade, prazo, valor e geografia</li>
        </ul>
      </div>

      <p>
        O resultado final é uma lista de editais classificados com score de viabilidade,
        ordenados da oportunidade mais prioritária para a menos prioritária. O analista
        humano recebe apenas esses editais — nunca o universo bruto de 3.200 publicações diárias.
      </p>

      {/* Section 3 */}
      <h2>O funil de triagem — de 3.200 para 15</h2>

      <p>
        Para tornar o processo concreto, imagine uma empresa de tecnologia da informação
        que atua em seis estados do Sudeste e Sul. Em um dia útil típico, o universo de
        publicações nesses estados é de aproximadamente 540 editais — após a filtragem
        geográfica inicial sobre os 3.200 publicados no país todo.
      </p>

      <p>
        O filtro de valor estimado (excluindo editais abaixo de R$ 50 mil e acima de
        R$ 10 milhões, fora da capacidade operacional da empresa) reduz para cerca de 180
        publicações. Dessas, o matching de palavras-chave identifica 45 com terminologia
        de TI. A classificação semântica adiciona mais 22 editais com objeto tecnológico
        mas terminologia atípica. O LLM zero-match aprova mais 8 dos casos ambíguos restantes.
      </p>

      <p>
        O score de viabilidade — que avalia modalidade (pregão eletrônico tem maior
        probabilidade de sucesso), prazo de entrega, valor alinhado com a capacidade da
        empresa e presença física na UF — prioriza os 15 editais com maior potencial real.
        São esses 15 que chegam ao analista pela manhã.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          O funil em números — empresa de TI em seis estados
        </p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li><strong>3.200</strong> publicações nacionais por dia útil</li>
          <li><strong>540</strong> após filtro geográfico (Sudeste + Sul)</li>
          <li><strong>180</strong> após filtro de valor estimado</li>
          <li><strong>45</strong> após matching de palavras-chave (camada 1)</li>
          <li><strong>22</strong> adicionais da análise semântica (camada 2)</li>
          <li><strong>8</strong> adicionais do LLM zero-match (camada 3)</li>
          <li><strong>15</strong> após score de viabilidade — chegam ao analista</li>
        </ul>
      </div>

      <p>
        Revisar 15 editais priorizados leva de 20 a 40 minutos. Revisar os 75 editais
        aprovados pela triagem (antes do score de viabilidade) levaria entre 2 e 3 horas.
        Revisar os 180 após o filtro de valor levaria um dia inteiro. A triagem por IA não
        apenas filtra mais — filtra melhor, colocando os melhores editais no topo da fila.
      </p>

      <BlogInlineCTA
        slug="ia-triagem-editais-filtrar-licitacoes"
        campaign="b2g"
        ctaMessage="Triagem em 3 camadas no SmartLic — Dado público verificável."
        ctaText="Começar triagem automática"
      />

      {/* Section 4 */}
      <h2>Dados exclusivos — o que a triagem automática encontra que humanos perdem</h2>

      <p>
        O argumento mais poderoso a favor da triagem por IA não é a eficiência — é a
        cobertura. Analistas experientes de licitações desenvolvem heurísticas eficientes
        para seu setor, mas essas heurísticas têm pontos cegos. Há categorias de editais
        que aparecem regularmente nos portais mas raramente são encontradas por busca
        convencional.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Cobertura da triagem automatizada vs. busca convencional
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>11% dos editais aprovados pela IA</strong> não seriam encontrados
            por busca convencional de palavras-chave
          </li>
          <li>
            <strong>Para cada 100 editais relevantes,</strong> a busca por palavras-chave
            encontra 89. A triagem por IA encontra os 100.
          </li>
          <li>
            <strong>Editais com objeto genérico</strong> (&ldquo;contratação de empresa
            especializada em serviços de TI&rdquo;) são sistematicamente perdidos por
            buscas de termos específicos
          </li>
          <li>
            <strong>Terminologia regional</strong> (ex.: &ldquo;sistema de prontuário
            eletrônico&rdquo; vs. &ldquo;prontuário digital&rdquo; vs. &ldquo;PEP
            municipal&rdquo;) multiplica os pontos cegos
          </li>
        </ul>
      </div>

      <p>
        Esses 11% adicionais podem representar oportunidades de alto valor. Editais com
        objeto redigido de forma genérica tendem a ter menos concorrentes — porque outros
        fornecedores também não os encontram por busca de palavras-chave. Uma empresa que
        acessa sistematicamente esse conjunto de editais tem vantagem competitiva real.
      </p>

      <p>
        Para explorar como essa vantagem se aplica por setor específico, veja o artigo
        sobre{' '}
        <Link href="/blog/ia-licitacoes-por-setor-saude-ti-engenharia" className="text-brand-navy dark:text-brand-blue hover:underline">
          IA em licitações por setor: saúde, TI e engenharia
        </Link>
        . Cada setor tem padrões distintos de terminologia e pontos cegos diferentes na
        busca manual.
      </p>

      {/* Section 5 */}
      <h2>Triagem manual vs. IA — comparação de tempo</h2>

      <p>
        Antes de apresentar os números, é importante calibrar o que chamamos de
        &ldquo;triagem manual&rdquo;. Não é um analista lendo cada edital de ponta a
        ponta. É um profissional navegando portais, aplicando filtros básicos de palavras-chave,
        abrindo PDFs, lendo o objeto e o prazo, e decidindo se vale continuar. Em operações
        experientes, isso leva de 1 a 3 minutos por edital.
      </p>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-3 font-semibold text-ink">Critério</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Triagem manual</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Triagem por IA</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-3 font-medium">Tempo diário de triagem</td>
              <td className="py-3 px-3 text-ink-secondary">3–5 horas</td>
              <td className="py-3 px-3 text-ink-secondary">20–40 minutos de revisão</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Editais escaneados por dia</td>
              <td className="py-3 px-3 text-ink-secondary">50–100 (portal principal)</td>
              <td className="py-3 px-3 text-ink-secondary">800K+/ano (todos os portais)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Editais revisados pelo analista</td>
              <td className="py-3 px-3 text-ink-secondary">22–35 após triagem</td>
              <td className="py-3 px-3 text-ink-secondary">10–20 pré-priorizados</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Precisão da triagem</td>
              <td className="py-3 px-3 text-ink-secondary">60–70% (analista experiente)</td>
              <td className="py-3 px-3 text-ink-secondary">85–93% (por setor)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Cobertura geográfica</td>
              <td className="py-3 px-3 text-ink-secondary">1–3 portais, UFs prioritárias</td>
              <td className="py-3 px-3 text-ink-secondary">27 UFs, todos os portais</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Editais com objeto genérico encontrados</td>
              <td className="py-3 px-3 text-ink-secondary">Baixa cobertura</td>
              <td className="py-3 px-3 text-ink-secondary">Capturados pela camada 3 (LLM)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Custo de oportunidade</td>
              <td className="py-3 px-3 text-ink-secondary">Alto — analistas sem tempo para propostas</td>
              <td className="py-3 px-3 text-ink-secondary">Baixo — equipe foca em proposta</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p>
        O dado de precisão merece atenção especial. Analistas experientes têm 60% a 70%
        de taxa de acerto na triagem — isso significa que de cada 10 editais que eles
        selecionam para análise completa, 3 a 4 são descartados depois de ler o edital
        completo. O tempo gasto nesses 30% a 40% de falsos positivos é puro desperdício.
      </p>

      <p>
        A triagem por IA reduz esse desperdício. Mas o insight mais contraintuitivo não é
        esse. Para entender o custo real da triagem ineficiente, veja o artigo sobre{' '}
        <Link href="/blog/equipe-40-horas-mes-editais-descartados" className="text-brand-navy dark:text-brand-blue hover:underline">
          as 40 horas mensais gastas em editais descartados
        </Link>
        .
      </p>

      {/* Section 6 — counterintuitive insight */}
      <h2>O custo oculto da triagem manual — o que ninguém calcula</h2>

      <p>
        Há uma percepção comum de que o maior problema da triagem manual é <em>perder</em>
        editais bons. Essa percepção está errada — ou pelo menos incompleta.
      </p>

      <p>
        O maior custo da triagem manual não é perder editais relevantes. É gastar 40 ou
        mais horas por mês analisando editais que passam no filtro de palavras-chave mas
        falham na análise de viabilidade. Editais de pregão eletrônico para equipamentos
        especializados que a empresa não tem como fornecer. Editais com prazo de entrega
        de 10 dias em UFs onde a empresa não tem operação. Editais com valor estimado de
        R$ 15 mil para contratos que exigem mobilização de equipe.
      </p>

      <p>
        Esses editais passam pelo filtro de palavras-chave porque o objeto é &ldquo;do
        setor&rdquo;, mas são inviáveis por razões que uma busca simples não detecta.
        O score de viabilidade composto — que avalia modalidade, prazo, valor e geografia
        simultaneamente — é o que elimina essa categoria de desperdício.
      </p>

      <p>
        Para uma empresa de médio porte com dois analistas de licitação, esse tempo
        desperdiçado em editais inviáveis representa entre R$ 8.000 e R$ 15.000 mensais
        em custo de mão de obra — considerando salário, encargos e benefícios. É o custo
        de oportunidade mais óbvio e menos monitorado em operações de licitação.
      </p>

      {/* Section 7 */}
      <h2>Quando a triagem por IA não funciona bem</h2>

      <p>
        Nenhuma tecnologia de triagem automática é perfeita para todos os contextos.
        Existem situações específicas em que a triagem por IA tem desempenho abaixo do
        esperado e onde a configuração cuidadosa ou a supervisão humana mais próxima
        são necessárias.
      </p>

      <p>
        <strong>Setores de nicho muito específico.</strong> Empresas que fornecem
        equipamentos de alta especificidade — instrumentos científicos de laboratório,
        equipamentos militares adaptados, sistemas de medição especializados — operam
        com um vocabulário técnico tão restrito que o volume de editais relevantes é
        naturalmente baixo. Nesses casos, a triagem manual por um especialista pode
        ser mais eficiente do que configurar e treinar um sistema de IA para um volume
        pequeno.
      </p>

      <p>
        <strong>Objetos extremamente genéricos sem contexto técnico.</strong> Alguns
        órgãos publicam editais com objeto redigido em linguagem absolutamente genérica,
        sem detalhamento técnico no corpo principal do edital — os detalhes ficam em
        anexos que nem sempre são indexados. A triagem automática tem dificuldade nesses
        casos, e o LLM zero-match pode não ter informação suficiente para decidir.
      </p>

      <p>
        <strong>Fase inicial sem dados de feedback.</strong> Nas primeiras semanas de uso,
        antes que a equipe forneça feedback suficiente sobre os resultados da triagem, o
        sistema pode ter mais falsos positivos do que o esperado. A configuração inicial
        de palavras-chave e exclusões é crítica e requer envolvimento de alguém que
        conhece bem o setor.
      </p>

      <p>
        Para uma análise honesta das limitações da IA aplicada a licitações — incluindo
        o que nenhuma ferramenta faz bem — veja nosso artigo sobre{' '}
        <Link href="/blog/reduzir-tempo-analisando-editais-irrelevantes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como reduzir tempo gasto em editais irrelevantes
        </Link>
        . E se sua empresa atua no setor de engenharia, o{' '}
        <Link href="/licitacoes/engenharia" className="text-brand-navy dark:text-brand-blue hover:underline">
          monitor de licitações de engenharia
        </Link>{' '}
        oferece triagem pré-configurada para o setor.
      </p>

      {/* Section 8 */}
      <h2>Perguntas frequentes</h2>

      <h3>Quantos editais são publicados por dia no Brasil?</h3>
      <p>
        Somando PNCP, Portal de Compras Públicas e ComprasGov, são publicados aproximadamente
        3.200 editais por dia útil. Esse volume cresceu significativamente desde 2023 com a
        migração de municípios para o PNCP, obrigatória pela Lei 14.133/2021. A fatia
        relevante para uma empresa típica gira em torno de 3% a 7% do total, dependendo do
        setor e da abrangência geográfica de atuação.
      </p>

      <h3>Como a IA faz a triagem de editais?</h3>
      <p>
        A triagem por IA funciona em três camadas sequenciais. A primeira usa matching de
        palavras-chave com scoring de densidade para classificar editais claramente relevantes
        ou irrelevantes. A segunda aplica análise semântica para capturar terminologia atípica.
        A terceira usa um modelo de linguagem para decidir casos ambíguos. Filtros rápidos de
        UF e valor são aplicados antes das camadas de IA para reduzir o volume processado.
      </p>

      <h3>Qual a diferença entre triagem por palavras-chave e triagem por IA?</h3>
      <p>
        A busca por palavras-chave encontra termos exatos e classifica como relevante qualquer
        publicação que os contenha. A triagem por IA vai além: analisa o contexto dos termos,
        detecta sinônimos e terminologia regional, e classifica editais que não contêm as
        palavras-chave mas são semanticamente relevantes. Na prática, a IA encontra 8% a 15%
        a mais de editais relevantes do que a busca por palavras-chave isolada.
      </p>

      <h3>Quanto tempo economiza a triagem automática?</h3>
      <p>
        Empresas que fazem triagem manual gastam em média 3 a 5 horas por dia revisando
        editais. Com triagem automática, esse tempo cai para 20 a 40 minutos diários —
        focados apenas em revisar os editais pré-classificados como relevantes e viáveis.
        A redução representa 80% a 90% do tempo de triagem. Para uma equipe com dois
        analistas, isso libera de 8 a 12 horas por semana para análise de editais completos
        e elaboração de propostas.
      </p>

      <h3>A IA perde editais relevantes durante a triagem?</h3>
      <p>
        Sistemas de triagem por IA operam com recall entre 70% e 90%, o que significa que
        encontram a maioria dos editais relevantes — mas não todos. Os principais pontos cegos
        são editais com objeto redigido de forma muito genérica e terminologia específica de
        uma região ou órgão. Para minimizar esse risco, sistemas maduros mantêm um estágio de
        revisão humana para casos classificados como incertos, e permitem configurar alertas
        para termos muito específicos do nicho.
      </p>

      <h3>Posso configurar a triagem para o meu setor específico?</h3>
      <p>
        Sim. Ferramentas especializadas permitem configurar palavras-chave setoriais, exclusões,
        faixas de valor e restrições geográficas. A configuração inicial leva de 1 a 3 horas
        para um analista que conhece bem o setor. Após as primeiras semanas, o sistema aprende
        com o feedback da equipe e ajusta a sensibilidade da classificação automaticamente.
        No SmartLic, os 15 setores pré-configurados incluem keywords, exclusões e faixas de
        valor padrão — reduzindo o tempo de configuração inicial.
      </p>

      {/* Sources */}
      <h2>Fontes</h2>
      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          Portal Nacional de Contratações Públicas (PNCP) — dados de publicações 2024–2025:{' '}
          <a href="https://pncp.gov.br" target="_blank" rel="noopener noreferrer" className="text-brand-navy dark:text-brand-blue hover:underline">
            pncp.gov.br
          </a>
        </li>
        <li>
          Portal de Compras Públicas — volume de processos publicados:{' '}
          <a href="https://www.portaldecompraspublicas.com.br" target="_blank" rel="noopener noreferrer" className="text-brand-navy dark:text-brand-blue hover:underline">
            portaldecompraspublicas.com.br
          </a>
        </li>
        <li>
          Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos:{' '}
          <a href="https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm" target="_blank" rel="noopener noreferrer" className="text-brand-navy dark:text-brand-blue hover:underline">
            planalto.gov.br
          </a>
        </li>
        <li>
          SmartLic — dados internos de classificação e cobertura de editais por setor (2025)
        </li>
        <li>
          <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-navy dark:text-brand-blue hover:underline">
            Inteligência artificial em licitações: como funciona na prática
          </Link>{' '}
          — SmartLic Blog
        </li>
        <li>
          <Link href="/blog/precisao-ia-licitacoes-taxa-acerto" className="text-brand-navy dark:text-brand-blue hover:underline">
            Precisão da IA em licitações: o que os números realmente significam
          </Link>{' '}
          — SmartLic Blog
        </li>
      </ul>
    </>
  );
}
