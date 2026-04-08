import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-02: O Erro Operacional que Faz Empresas Perderem Contratos Publicos
 *
 * Content cluster: inteligencia em licitacoes para empresas B2G
 * Target: 2,000-2,500 words | Primary KW: erro operacional licitacao
 */
export default function ErroOperacionalPerderContratosPublicos() {
  return (
    <>
      {/* FAQPage JSON-LD — STORY-262 AC5/AC11 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: [
              {
                '@type': 'Question',
                name: 'Qual o erro operacional mais comum em empresas que perdem licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O erro mais comum é investir tempo e recursos na elaboração de propostas para editais de baixa viabilidade — licitações onde a empresa não tem vantagem competitiva real, seja por valor fora da faixa ideal, prazo insuficiente, modalidade desfavorável ou localização geográfica inviável. Esse erro consome entre 60% e 70% do orçamento operacional do setor de licitações sem retorno proporcional.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto custa para uma empresa elaborar uma proposta de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo varia por complexidade: propostas simples (fornecimento de bens) custam entre R$ 2.000 e R$ 5.000. Propostas de média complexidade (serviços continuados) custam entre R$ 5.000 e R$ 12.000. Propostas complexas (engenharia, TI) podem custar de R$ 10.000 a R$ 25.000, considerando horas de analista, documentação, certidões e custos indiretos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como saber se minha empresa está investindo tempo nos editais errados?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Cinco sinais indicam esse problema: taxa de adjudicação abaixo de 12%; mais de 60% das propostas elaboradas para editais com valor fora da faixa de maior competitividade da empresa; equipe permanentemente sobrecarregada sem aumento proporcional de contratos; decisão de participar baseada apenas no objeto e valor, sem análise estruturada; e ausência de métricas de custo por proposta e ROI por contrato.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é triagem por viabilidade e como ela corrige o erro?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Triagem por viabilidade é a avaliação estruturada de um edital com base em quatro fatores objetivos: modalidade, prazo, valor estimado e geografia. Cada fator recebe uma pontuação ponderada, e editais abaixo de um limiar definido são descartados antes da análise detalhada. Isso redireciona o esforço da equipe para oportunidades com maior probabilidade de adjudicação.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: erro operacional perder contratos publicos */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Existe um <strong>erro operacional</strong> que custa contratos públicos
        de seis dígitos a empresas tecnicamente qualificadas — e não tem
        relação com a qualidade da proposta, com o preço oferecido ou com a
        documentação de habilitação. O erro acontece antes de tudo isso: na
        decisão de quais editais disputar. Empresas B2G que investem recursos
        em licitações de baixa viabilidade perdem mais do que tempo. Perdem
        contratos que poderiam ter sido conquistados se o esforço tivesse sido
        direcionado corretamente.
      </p>

      {/* Section 1 */}
      <h2>O cenário: empresa qualificada que perde por decisão errada</h2>

      <p>
        Considere o perfil típico de uma empresa de médio porte que atua no
        mercado B2G. Equipe de dois a quatro analistas de licitação. Certidões
        em dia. Atestados de capacidade técnica compatíveis com o segmento.
        Precificação competitiva. Apesar disso, a taxa de adjudicação fica
        entre 8% e 14% — ou seja, para cada sete a doze propostas elaboradas,
        apenas uma resulta em contrato.
      </p>

      <p>
        A conclusão habitual é que o mercado está saturado ou que a
        concorrência pratica preços inviáveis. Embora essas dificuldades
        existam em determinados segmentos, a análise dos dados revela um padrão
        diferente: na maioria dos casos, a empresa não perde por falta de
        competitividade. Ela perde porque está competindo nos editais errados.
      </p>

      <p>
        O Tribunal de Contas da União, em seus relatórios de governança de
        aquisições, aponta que entre 25% e 40% das licitações públicas
        recebem propostas de empresas que não atendem plenamente aos
        requisitos de habilitação ou que oferecem condições fora dos
        parâmetros do edital. Isso significa que uma parcela significativa do
        esforço das empresas é desperdiçada em oportunidades onde a chance de
        sucesso era baixa desde o início.
      </p>

      {/* Section 2 */}
      <h2>O erro: investir tempo em editais de baixa viabilidade</h2>

      <p>
        O erro operacional não é participar de licitações — é participar sem
        critério. A dinâmica típica funciona assim: o analista acessa o PNCP ou
        outros portais diariamente, identifica editais pelo objeto e pelo
        valor, e encaminha os que parecem relevantes para análise. A decisão de
        prosseguir ou descartar é baseada em leitura rápida e percepção
        subjetiva.
      </p>

      <p>
        Nesse modelo, fatores críticos são frequentemente ignorados ou
        subestimados: a modalidade favorece o perfil da empresa? O prazo entre
        publicação e abertura é suficiente para preparar uma proposta
        competitiva? O valor estimado está na faixa onde a empresa historicamente
        tem melhor desempenho? A localização permite execução rentável?
      </p>

      <p>
        Sem essa avaliação estruturada, a empresa acaba investindo o mesmo
        esforço em um edital de alta viabilidade e em um de baixa viabilidade.
        O resultado é previsível: os editais de baixa viabilidade consomem
        recursos sem retorno, e os de alta viabilidade recebem propostas
        apressadas porque a equipe está sobrecarregada.
      </p>

      <p>
        Para uma análise detalhada sobre a dinâmica de custos desse
        comportamento, veja{' '}
        <Link href="/blog/custo-invisivel-disputar-pregoes-errados" className="text-brand-navy dark:text-brand-blue hover:underline">
          o custo invisível de disputar pregões errados
        </Link>. Consultorias especializadas enfrentam desafio semelhante ao
        explicar a clientes{' '}
        <Link href="/blog/clientes-perdem-pregoes-boa-documentacao" className="text-brand-navy dark:text-brand-blue hover:underline">
          por que clientes perdem pregões mesmo com boa documentação
        </Link>.
      </p>

      {/* Section 3 */}
      <h2>O custo real: cálculo detalhado</h2>

      <p>
        O impacto financeiro desse erro vai além do tempo perdido. Para
        dimensioná-lo, é necessário considerar todos os componentes de custo
        de uma proposta que não resulta em contrato.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático — Custo anual do erro de triagem
        </p>
        <p className="text-sm text-ink-secondary mb-4">
          Empresa de facilities com 3 analistas, 20 propostas/mês, taxa de
          adjudicação de 10%:
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Propostas elaboradas por ano:</strong> 240
          </li>
          <li>
            <strong>Propostas sem adjudicação:</strong> 216 (90%)
          </li>
          <li>
            <strong>Custo médio por proposta:</strong> R$ 4.200
            (analista: 18h x R$ 85/h = R$ 1.530 + proposta comercial: 8h x R$ 85/h = R$ 680 +
            documentação: 6h x R$ 85/h = R$ 510 + certidões/custos diretos: R$ 380 +
            overhead operacional: R$ 1.100)
          </li>
          <li>
            <strong>Custo total das propostas sem retorno:</strong> 216 x
            R$ 4.200 = R$ 907.200/ano
          </li>
          <li className="pt-2">
            <strong>Se a triagem reduzisse propostas para 12/mês com taxa de 25%:</strong>
          </li>
          <li>Propostas anuais: 144 | Sem adjudicação: 108 | Custo desperdiçado: R$ 453.600</li>
          <li className="font-semibold pt-1">
            Economia anual: R$ 453.600 — com mais contratos obtidos (36 vs 24)
          </li>
        </ul>
      </div>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência — Custos e desclassificação
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Custo-hora médio de analista de licitação:</strong> entre
            R$ 65 e R$ 120/hora (inclui encargos), variando por região e
            senioridade (Fonte: pesquisa salarial Catho/Robert Half, cargos
            administrativos especializados, 2024).
          </li>
          <li>
            <strong>Taxa de desclassificação por erros formais:</strong> entre
            18% e 30% das propostas apresentadas em pregões eletrônicos
            contêm alguma irregularidade documental (Fonte: Relatórios de
            auditoria do TCU, acórdãos de 2023 sobre governança de aquisições).
          </li>
          <li>
            <strong>Valor médio de contratos por faixa:</strong> 62% dos
            contratos publicados no PNCP em 2024 estavam na faixa de
            R$ 50.000 a R$ 500.000; 23% entre R$ 500.000 e R$ 2.000.000;
            15% acima de R$ 2.000.000
            (Fonte: PNCP, painel de estatísticas de contratações, 2024).
          </li>
        </ul>
      </div>

      <p>
        O cálculo acima demonstra que o custo do erro não está apenas nas
        propostas perdidas, mas na alocação subótima de recursos que impede a
        empresa de investir adequadamente nas oportunidades viáveis. Para um
        aprofundamento sobre eficiência operacional na análise de editais,
        consulte{' '}
        <Link href="/blog/reduzir-tempo-analisando-editais-irrelevantes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como reduzir em 50% o tempo gasto analisando editais irrelevantes
        </Link>.
      </p>

      <BlogInlineCTA slug="erro-operacional-perder-contratos-publicos" campaign="b2g" />

      {/* Section 4 */}
      <h2>Os 5 sinais de que você está cometendo esse erro</h2>

      <p>
        Os indicadores abaixo permitem diagnosticar se a sua empresa está
        investindo recursos em editais de baixa viabilidade de forma
        sistemática.
      </p>

      <h3>Sinal 1: Taxa de adjudicação abaixo de 12%</h3>
      <p>
        Se menos de uma em cada oito propostas resulta em contrato, o
        problema provavelmente não é competitividade de preço — é seleção de
        editais. Empresas com triagem estruturada operam entre 20% e 35%.
      </p>

      <h3>Sinal 2: Mais de 60% das propostas são para editais fora da faixa ideal</h3>
      <p>
        Analise as últimas 50 propostas: quantas foram para editais com valor
        estimado dentro da faixa onde a empresa historicamente vence? Se a
        maioria está fora dessa faixa, a triagem não está funcionando.
      </p>

      <h3>Sinal 3: Equipe permanentemente sobrecarregada sem aumento de contratos</h3>
      <p>
        Analistas trabalhando além da capacidade, prazos sempre apertados para
        entrega de propostas, e ainda assim o número de contratos não cresce.
        Esse é o sintoma clássico de volume sem inteligência: muita atividade,
        pouco resultado.
      </p>

      <h3>Sinal 4: Decisão de participar baseada apenas em objeto e valor</h3>
      <p>
        Se a decisão de elaborar proposta se resume a &ldquo;o objeto é do
        nosso segmento&rdquo; e &ldquo;o valor parece bom&rdquo;, sem
        avaliação de modalidade, prazo, geografia e histórico do órgão, a
        empresa está operando com triagem insuficiente.
      </p>

      <h3>Sinal 5: Ausência de métricas de custo por proposta</h3>
      <p>
        Se a empresa não sabe quanto custa, em média, elaborar uma proposta,
        não consegue calcular o ponto de equilíbrio entre esforço e retorno.
        Sem essa métrica, é impossível avaliar se o volume atual de
        participações é sustentável.
      </p>

      {/* Section 5 */}
      <h2>A correção: triagem baseada em viabilidade</h2>

      <p>
        A solução não é participar de menos licitações arbitrariamente. É
        implementar um processo de avaliação que identifique, antes de
        comprometer recursos, quais editais oferecem retorno proporcional ao
        investimento.
      </p>

      <p>
        O modelo de triagem por viabilidade utiliza quatro fatores objetivos,
        cada um com peso calibrado conforme sua influência nos resultados
        históricos: modalidade (30%), prazo (25%), valor estimado (25%) e
        geografia (20%). Cada edital recebe uma pontuação de 0 a 10. Editais
        abaixo do limiar definido pela empresa (tipicamente entre 5,0 e 6,0)
        são descartados sem análise detalhada.
      </p>

      <p>
        O benefício imediato é duplo: a equipe gasta menos tempo em editais
        sem retorno, e as propostas elaboradas para editais viáveis recebem
        mais atenção e qualidade. Ambos os efeitos convergem para o aumento
        da taxa de adjudicação.
      </p>

      <p>
        A implementação pode ser manual (planilha com critérios ponderados) ou
        automatizada (ferramentas que aplicam os critérios e classificam
        editais por pontuação de viabilidade). A diferença entre as abordagens
        é de escala: a triagem manual funciona para 10-20 editais por semana,
        mas não escala para centenas. Para entender como empresas de alto
        desempenho implementam esse processo, veja{' '}
        <Link href="/blog/empresas-vencem-30-porcento-pregoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          o que empresas que vencem 30% dos pregões fazem de diferente
        </Link>.
      </p>

      <p>
        A longo prazo, a triagem por viabilidade transforma a dinâmica do
        setor de licitações: em vez de uma operação reativa (reagir a cada
        edital publicado), a empresa passa a operar de forma estratégica
        (investir apenas nas oportunidades que se encaixam no seu perfil de
        competitividade).
      </p>

      {/* CTA Section — STORY-262 AC18/AC19 — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Identifique editais viáveis antes de investir horas
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic avalia cada edital com 4 fatores de viabilidade e entrega
          apenas as oportunidades com real encaixe para o perfil da sua empresa.
          Pare de desperdiçar recursos em editais de baixa probabilidade.
        </p>
        <Link
          href="/signup?source=blog&article=erro-operacional-perder-contratos-publicos&utm_source=blog&utm_medium=cta&utm_content=erro-operacional-perder-contratos-publicos&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito. Conheça todos os recursos na{' '}
          <Link href="/features" className="underline hover:text-ink">
            página de funcionalidades
          </Link>.
        </p>
      </div>

      {/* FAQ Section — STORY-262 AC5 */}
      <h2>Perguntas Frequentes</h2>

      <h3>Qual o erro operacional mais comum em empresas que perdem licitações?</h3>
      <p>
        O erro mais comum é investir tempo e recursos na elaboração de
        propostas para editais de baixa viabilidade — licitações onde a
        empresa não tem vantagem competitiva real, seja por valor fora da faixa
        ideal, prazo insuficiente, modalidade desfavorável ou localização
        geográfica inviável. Esse erro consome entre 60% e 70% do orçamento
        operacional do setor de licitações sem retorno proporcional.
      </p>

      <h3>Quanto custa para uma empresa elaborar uma proposta de licitação?</h3>
      <p>
        O custo varia por complexidade. Propostas simples de fornecimento de
        bens custam entre R$ 2.000 e R$ 5.000. Propostas de média
        complexidade para serviços continuados custam entre R$ 5.000 e
        R$ 12.000. Propostas complexas de engenharia ou tecnologia podem
        custar de R$ 10.000 a R$ 25.000, considerando horas de analista,
        documentação, certidões e custos indiretos.
      </p>

      <h3>Como saber se minha empresa está investindo tempo nos editais errados?</h3>
      <p>
        Cinco sinais indicam esse problema: taxa de adjudicação abaixo de 12%;
        mais de 60% das propostas elaboradas para editais com valor fora da
        faixa de maior competitividade da empresa; equipe permanentemente
        sobrecarregada sem aumento proporcional de contratos; decisão de
        participar baseada apenas no objeto e valor, sem análise estruturada;
        e ausência de métricas de custo por proposta e ROI por contrato.
      </p>

      <h3>O que é triagem por viabilidade e como ela corrige o erro?</h3>
      <p>
        Triagem por viabilidade é a avaliação estruturada de um edital com base
        em quatro fatores objetivos: modalidade (peso 30%), prazo (25%), valor
        estimado (25%) e geografia (20%). Cada fator recebe uma pontuação
        ponderada, e editais abaixo de um limiar definido são descartados antes
        da análise detalhada. Isso redireciona o esforço da equipe para
        oportunidades com maior probabilidade de adjudicação, aumentando a taxa
        de vitória sem necessidade de mais contratações.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
