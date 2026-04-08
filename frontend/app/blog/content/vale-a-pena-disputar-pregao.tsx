import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-03: Como Saber se Vale a Pena Disputar um Pregao
 *
 * Content cluster: inteligencia em licitacoes para empresas B2G
 * Target: 2,500-3,000 words | Primary KW: vale a pena disputar licitacao
 */
export default function ValeAPenaDisputarPregao() {
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
                name: 'Quais são os 4 fatores de viabilidade de uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os 4 fatores são: Modalidade (peso 30%) — avalia se a modalidade do certame favorece o perfil da empresa; Timeline (peso 25%) — verifica se o prazo é suficiente para preparar proposta competitiva e executar o contrato; Valor estimado (peso 25%) — analisa se o valor está na faixa de maior competitividade da empresa; Geografia (peso 20%) — considera o custo logístico e a viabilidade de execução na localidade do órgão.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como avaliar rapidamente se um pregão vale a pena?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Aplique o checklist de 5 minutos: (1) A modalidade é compatível com seu perfil? (2) Há pelo menos 7 dias úteis até a abertura? (3) O valor estimado está na sua faixa ideal? (4) A execução é viável na localidade? (5) Você tem atestados compatíveis com o volume exigido? Se 4 de 5 respostas forem positivas, o edital merece análise completa.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o prazo mínimo viável para preparar uma proposta de pregão?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Depende da complexidade. Para fornecimento de bens padronizados, 5 a 7 dias úteis são suficientes se a documentação estiver atualizada. Para serviços que exigem proposta técnica detalhada, o mínimo recomendado é 10 a 15 dias úteis. Para obras e engenharia, considere pelo menos 15 a 20 dias úteis para orçamento, cronograma e visita técnica.',
                },
              },
              {
                '@type': 'Question',
                name: 'O valor estimado da licitação influencia na decisão de participar?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, significativamente. Cada empresa tem uma faixa de valor onde é mais competitiva — determinada por sua estrutura de custos, capacidade operacional e atestados disponíveis. Disputar editais com valor muito acima ou abaixo dessa faixa reduz a taxa de adjudicação. A recomendação é concentrar esforço na faixa onde o histórico de vitórias é maior.',
                },
              },
              {
                '@type': 'Question',
                name: 'A localização geográfica realmente impacta a viabilidade de uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. Para serviços, a proximidade do local de execução afeta diretamente o custo de mobilização, supervisão e manutenção do contrato. Para fornecimento de bens, o custo de frete pode representar 5% a 15% do valor do contrato. Empresas com atuação regional concentrada tendem a ter margens melhores em editais da sua região.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: vale a pena disputar pregao */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Uma parcela significativa do tempo investido por equipes de licitação
        é consumida na análise de editais que serão descartados. Estimativas
        setoriais indicam que <strong>entre 60% e 70% dos editais
        identificados como potencialmente relevantes</strong> são abandonados
        após análise parcial — seja por incompatibilidade de prazo, valor fora
        da faixa viável, ou requisitos técnicos que a empresa não atende. A
        pergunta que precede qualquer investimento de tempo deveria ser
        objetiva: vale a pena disputar este pregão? Este artigo apresenta um
        modelo com quatro fatores de viabilidade que permite responder essa
        pergunta em menos de cinco minutos.
      </p>

      {/* Section 1 */}
      <h2>O problema: a maior parte do tempo é gasta em editais descartados</h2>

      <p>
        O fluxo operacional típico de um setor de licitações segue um padrão
        ineficiente. O analista acessa portais como PNCP, ComprasGov e Portal
        de Compras Públicas, identifica editais pelo objeto, faz uma leitura
        inicial do edital completo, e então decide se a empresa deve ou não
        participar. Essa decisão frequentemente ocorre depois de investir
        entre 30 minutos e 2 horas por edital — tempo que não é recuperado
        quando o edital é descartado.
      </p>

      <p>
        Em uma empresa que analisa 15 a 25 editais por semana, o tempo
        acumulado em editais descartados pode ultrapassar 20 horas semanais.
        Ao longo de um mês, são 80 a 100 horas de trabalho qualificado
        consumidas em atividade sem retorno direto.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência — Distribuição de modalidades e prazos
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Distribuição de modalidades no PNCP (2024):</strong> Pregão
            Eletrônico: 58% das contratações; Dispensa: 27%; Concorrência: 8%;
            Inexigibilidade: 5%; Outras: 2%
            (Fonte: PNCP, painel de estatísticas, consolidação 2024).
          </li>
          <li>
            <strong>Prazos mínimos por modalidade (Lei 14.133/2021):</strong>
            {' '}Pregão Eletrônico: 8 dias úteis (bens/serviços comuns);
            Concorrência: 25 dias úteis (obras/serviços especiais); Diálogo
            Competitivo: 25 dias úteis; Dispensa Eletrônica: 3 dias úteis
            (Fonte: Lei 14.133/2021, arts. 55, 59 e 75, regulamentada pelo
            Decreto 11.462/2023).
          </li>
          <li>
            <strong>Distribuição de valores (PNCP, 2024):</strong> Até
            R$ 50.000: 34% dos processos; R$ 50.001 a R$ 500.000: 42%;
            R$ 500.001 a R$ 2.000.000: 15%; Acima de R$ 2.000.000: 9%
            (Fonte: PNCP, painel de contratações por faixa de valor, 2024).
          </li>
        </ul>
      </div>

      <p>
        O modelo de viabilidade proposto neste artigo inverte essa lógica.
        Em vez de analisar o edital completo para então decidir se participa,
        a empresa avalia quatro indicadores objetivos que podem ser verificados
        em minutos. Somente editais que atingem a pontuação mínima seguem para
        análise detalhada.
      </p>

      {/* Section 2 */}
      <h2>Os 4 fatores de viabilidade</h2>

      <p>
        O modelo de avaliação de viabilidade pondera quatro fatores, cada um
        com peso proporcional à sua influência estatística nos resultados de
        adjudicação. O objetivo não é substituir a análise completa do edital,
        mas filtrar antes dela — eliminando editais que, por razões
        estruturais, têm baixa probabilidade de resultar em contrato para a
        empresa.
      </p>

      {/* Factor 1 */}
      <h2>Fator 1: Modalidade — peso 30%</h2>

      <p>
        A modalidade de licitação é o fator com maior peso porque determina a
        dinâmica competitiva do certame. Cada modalidade favorece um perfil
        diferente de empresa.
      </p>

      <h3>Pregão Eletrônico (58% das contratações)</h3>
      <p>
        Critério predominante: menor preço ou maior desconto. Favorece
        empresas com estrutura de custos otimizada, capacidade de produção em
        escala e documentação padronizada. A fase de lances exige agilidade e
        estratégia de precificação em tempo real. Empresas cuja vantagem
        competitiva é técnica, não de preço, tendem a ter menor desempenho
        nessa modalidade.
      </p>

      <h3>Concorrência (8% das contratações)</h3>
      <p>
        Admite critérios de técnica e preço, ou melhor combinação. Favorece
        empresas com portfólio técnico diferenciado, atestados de obras ou
        serviços de grande porte, e capacidade de apresentar propostas
        técnicas detalhadas. O número menor de concorrentes eleva a taxa de
        adjudicação para empresas qualificadas.
      </p>

      <h3>Dispensa de licitação (27% dos processos)</h3>
      <p>
        Volumes menores (até R$ 59.906,02 para compras e R$ 119.812,03 para
        obras/serviços de engenharia, valores atualizados em 2024), com
        processos simplificados. Favorece fornecedores com agilidade de
        resposta e presença regional. A taxa de conversão tende a ser mais
        alta, mas o valor unitário é menor.
      </p>

      <p>
        A avaliação deste fator responde à pergunta: esta modalidade favorece
        o perfil competitivo da minha empresa? Se a resposta é negativa, a
        pontuação deste fator é baixa independentemente dos demais.
      </p>

      {/* Factor 2 */}
      <h2>Fator 2: Timeline — peso 25%</h2>

      <p>
        O fator temporal considera dois prazos distintos: o prazo de
        preparação (entre a publicação e a data de abertura das propostas) e
        o prazo de execução contratual.
      </p>

      <h3>Prazo de preparação</h3>
      <p>
        A Lei 14.133/2021 estabelece prazos mínimos por modalidade, mas muitos
        órgãos publicam editais próximos ao limite legal. O prazo real
        disponível — descontando feriados, tempo de análise do edital e
        elaboração da proposta — é frequentemente insuficiente para propostas
        de qualidade.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático — Avaliação de prazo
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          Pregão eletrônico publicado em 10/03 (segunda-feira) com abertura em
          21/03 (sexta-feira). Prazo legal: 8 dias úteis. Prazo real:
        </p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>Dia 1-2:</strong> Identificação e leitura inicial do
            edital (1-2 dias)
          </li>
          <li>
            <strong>Dia 3:</strong> Decisão de participar + início da
            documentação
          </li>
          <li>
            <strong>Dia 4-6:</strong> Elaboração da proposta comercial +
            cotações de fornecedores
          </li>
          <li>
            <strong>Dia 7-8:</strong> Revisão + upload no sistema
          </li>
          <li className="pt-2 font-semibold">
            Resultado: Prazo é tecnicamente suficiente para fornecimento de
            bens padronizados, mas insuficiente se houver necessidade de
            proposta técnica detalhada ou visita ao local. Pontuação: 6/10 para
            bens; 3/10 para serviços complexos.
          </li>
        </ul>
      </div>

      <h3>Prazo de execução</h3>
      <p>
        O prazo contratual precisa ser compatível com a capacidade operacional
        da empresa. Um contrato de 12 meses de fornecimento é diferente de um
        contrato de entrega única em 30 dias. A avaliação considera se a
        empresa consegue mobilizar recursos dentro do prazo previsto sem
        comprometer contratos em andamento.
      </p>

      <BlogInlineCTA slug="vale-a-pena-disputar-pregao" campaign="b2g" />

      {/* Factor 3 */}
      <h2>Fator 3: Valor estimado — peso 25%</h2>

      <p>
        O valor estimado da contratação é um indicador direto de viabilidade
        econômica, mas sua interpretação não é linear. O critério relevante
        não é se o valor é &ldquo;alto&rdquo; ou &ldquo;baixo&rdquo; em
        termos absolutos, mas se está dentro da faixa onde a empresa
        historicamente tem melhor desempenho.
      </p>

      <h3>Faixa inferior: custo de proposta vs. margem do contrato</h3>
      <p>
        Para cada empresa existe um valor mínimo abaixo do qual o custo de
        elaboração da proposta (horas de analista + documentação + certidões)
        consome uma parcela desproporcional da margem potencial. Se a empresa
        gasta R$ 5.000 para elaborar uma proposta de um contrato de
        R$ 20.000, a margem líquida raramente justifica o esforço.
      </p>

      <h3>Faixa superior: requisitos de habilitação</h3>
      <p>
        Editais de maior valor exigem atestados de capacidade técnica
        proporcionais, garantias de execução mais robustas e, frequentemente,
        experiência prévia em contratos de volume equivalente. Disputar
        licitações acima da capacidade comprovada da empresa resulta em
        desclassificação na fase de habilitação.
      </p>

      <h3>Faixa ideal: onde concentrar esforço</h3>
      <p>
        A análise do histórico de adjudicações da empresa revela a faixa de
        valor onde a taxa de vitória é mais alta. Para a maioria das empresas
        de médio porte, essa faixa corresponde a contratos entre 2x e 10x o
        faturamento mensal com o setor público. Concentrar esforço nessa faixa
        maximiza o retorno por proposta elaborada.
      </p>

      {/* Factor 4 */}
      <h2>Fator 4: Geografia — peso 20%</h2>

      <p>
        A localização do órgão contratante e do local de execução do contrato
        impacta a viabilidade de duas formas: custo direto (deslocamento,
        frete, logística) e custo de gestão (supervisão remota, comunicação
        com o órgão, resolução de problemas).
      </p>

      <h3>Para prestação de serviços</h3>
      <p>
        A proximidade é quase sempre um fator decisivo. Contratos de
        facilities, manutenção predial, vigilância ou serviços de TI
        presenciais exigem presença local regular. O custo de deslocamento
        e hospedagem em localidades distantes pode inviabilizar a operação,
        especialmente em contratos de valor intermediário. Uma empresa sediada
        em Belo Horizonte pode ser competitiva em todo o estado de Minas
        Gerais e estados limítrofes, mas dificilmente terá margem em um
        contrato de serviços no Tocantins.
      </p>

      <h3>Para fornecimento de bens</h3>
      <p>
        A variável crítica é o custo de frete. Para bens de alto valor
        agregado e baixo volume (equipamentos de TI, por exemplo), o frete
        representa parcela pequena do custo total — permitindo atuação
        nacional. Para bens volumosos de baixo valor unitário (materiais de
        escritório, uniformes em grande quantidade), o frete pode representar
        5% a 15% do valor, limitando a competitividade a raios regionais.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático — Impacto da geografia na margem
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          Empresa de uniformes sediada em Goiânia avaliando dois pregões
          equivalentes:
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Pregão A — Goiânia/GO:</strong> valor R$ 180.000 |
            frete estimado: R$ 2.800 (1,6%) | margem líquida projetada: 14% |
            pontuação geografia: 9/10
          </li>
          <li>
            <strong>Pregão B — Belém/PA:</strong> valor R$ 200.000 |
            frete estimado: R$ 18.500 (9,3%) | margem líquida projetada: 5% |
            pontuação geografia: 4/10
          </li>
          <li className="pt-2 font-semibold">
            Apesar do Pregão B ter valor absoluto maior, o custo logístico
            consome a margem. O Pregão A tem retorno superior mesmo com valor
            nominal menor.
          </li>
        </ul>
      </div>

      {/* Section: Checklist */}
      <h2>Checklist rápido de 5 minutos: vale a pena disputar?</h2>

      <p>
        Os quatro fatores acima podem ser sintetizados em um checklist
        operacional que qualquer analista pode aplicar em até cinco minutos,
        usando apenas as informações disponíveis no resumo do edital — sem
        necessidade de leitura completa.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Checklist de triagem rápida (5 minutos)
        </p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li>
            <strong>1. Modalidade compatível?</strong>
            <br />
            A modalidade do certame favorece o perfil competitivo da empresa?
            (Pregão: vantagem de preço? Concorrência: vantagem técnica?)
          </li>
          <li>
            <strong>2. Prazo suficiente?</strong>
            <br />
            Há pelo menos 7 dias úteis até a abertura para bens, ou 12 dias
            úteis para serviços? A equipe tem capacidade disponível no período?
          </li>
          <li>
            <strong>3. Valor na faixa ideal?</strong>
            <br />
            O valor estimado está dentro da faixa de maior competitividade
            histórica da empresa? (Se não sabe a faixa, considere 2x a 10x o
            faturamento mensal com governo.)
          </li>
          <li>
            <strong>4. Execução viável na localidade?</strong>
            <br />
            A empresa consegue executar o contrato na localidade do órgão com
            margem compatível? (Considere frete, deslocamento, presença local.)
          </li>
          <li>
            <strong>5. Atestados compatíveis?</strong>
            <br />
            A empresa possui atestados de capacidade técnica compatíveis com o
            volume e a natureza do objeto?
          </li>
          <li className="pt-2 font-semibold">
            Regra: 4 de 5 respostas positivas = prosseguir para análise
            completa. Menos de 4 = descartar e registrar o motivo.
          </li>
        </ul>
      </div>

      <p>
        Este checklist não substitui a análise completa do edital. Ele
        substitui a análise completa de editais que seriam descartados. A
        diferença é significativa: a análise completa passa a ser reservada
        para editais que já foram pré-qualificados como viáveis.
      </p>

      <p>
        Para uma abordagem mais ampla sobre estratégia de seleção de editais,
        veja{' '}
        <Link href="/blog/como-aumentar-taxa-vitoria-licitacoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como aumentar sua taxa de vitória em licitações sem contratar mais
          analistas
        </Link>. E para entender a matemática de disputar todas as licitações
        do segmento versus focar nas mais viáveis, consulte{' '}
        <Link href="/blog/disputar-todas-licitacoes-matematica-real" className="text-brand-navy dark:text-brand-blue hover:underline">
          a matemática real de disputar todas as licitações do seu segmento
        </Link>. Consultorias que aplicam esse modelo para seus clientes descobrem{' '}
        <Link href="/blog/triagem-editais-vantagem-estrategica-clientes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como transformar triagem de editais em vantagem estratégica
        </Link>.
      </p>

      <h2>Automatizando a avaliação de viabilidade</h2>

      <p>
        O checklist manual funciona bem para volumes moderados — até 15 a 20
        editais por semana. Acima disso, o próprio processo de triagem começa
        a consumir tempo significativo. Para empresas que monitoram múltiplos
        estados ou setores, a triagem manual de centenas de editais semanais
        é inviável.
      </p>

      <p>
        Ferramentas de inteligência em licitações automatizam essa etapa
        aplicando os quatro fatores de viabilidade a cada edital identificado
        nos portais PNCP, ComprasGov e Portal de Compras Públicas. A
        classificação setorial por IA identifica se o objeto é relevante para
        o segmento da empresa, e a pontuação de viabilidade permite ordenar
        editais por probabilidade de retorno.
      </p>

      <p>
        O resultado é que a equipe de licitação recebe uma lista já filtrada
        e priorizada, concentrando o tempo de análise detalhada nos editais
        que passaram pela triagem objetiva. Esse modelo é particularmente
        eficaz para empresas que atuam em mais de um estado ou em setores com
        alto volume de publicações diárias. Para entender como selecionar
        editais com vantagem competitiva, veja{' '}
        <Link href="/blog/escolher-editais-maior-probabilidade-vitoria" className="text-brand-navy dark:text-brand-blue hover:underline">
          como escolher editais com maior probabilidade de vitória
        </Link>.
      </p>

      {/* CTA Section — STORY-262 AC18/AC19 — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          O SmartLic calcula a viabilidade automaticamente
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Cada edital recebe uma pontuação de viabilidade com base em
          modalidade, prazo, valor e geografia. Sua equipe analisa apenas as
          oportunidades com real potencial de retorno.
        </p>
        <Link
          href="/signup?source=blog&article=vale-a-pena-disputar-pregao&utm_source=blog&utm_medium=cta&utm_content=vale-a-pena-disputar-pregao&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito. Veja como funciona na{' '}
          <Link href="/buscar" className="underline hover:text-ink">
            página de busca
          </Link>{' '}
          ou explore todos os{' '}
          <Link href="/features" className="underline hover:text-ink">
            recursos disponíveis
          </Link>.
        </p>
      </div>

      {/* Cross-links — SEO Q2/2026 */}
      <div className="not-prose my-8 sm:my-10 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Aprofunde-se</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <Link href="/blog/analise-viabilidade-editais-guia" className="text-brand-blue hover:underline">
              Análise de viabilidade de editais — guia completo
            </Link>{' '}
            — framework detalhado com os 4 fatores e scoring go/no-go
          </li>
        </ul>
      </div>

      {/* FAQ Section — STORY-262 AC5 */}
      <h2>Perguntas Frequentes</h2>

      <h3>Quais são os 4 fatores de viabilidade de uma licitação?</h3>
      <p>
        Os quatro fatores são: Modalidade (peso 30%), que avalia se o tipo de
        certame favorece o perfil competitivo da empresa; Timeline (peso 25%),
        que verifica se o prazo é suficiente para preparar proposta competitiva
        e executar o contrato; Valor estimado (peso 25%), que analisa se o
        valor está na faixa de maior competitividade da empresa; e Geografia
        (peso 20%), que considera o custo logístico e a viabilidade de
        execução na localidade do órgão.
      </p>

      <h3>Como avaliar rapidamente se um pregão vale a pena?</h3>
      <p>
        Aplique o checklist de cinco minutos com cinco perguntas: a modalidade
        é compatível com seu perfil? Há pelo menos 7 dias úteis até a
        abertura? O valor estimado está na sua faixa ideal? A execução é
        viável na localidade? Você tem atestados compatíveis com o volume
        exigido? Se 4 de 5 respostas forem positivas, o edital merece
        análise completa. Menos de 4 respostas positivas indicam que o edital
        deve ser descartado.
      </p>

      <h3>Qual o prazo mínimo viável para preparar uma proposta de pregão?</h3>
      <p>
        Depende da complexidade do objeto. Para fornecimento de bens
        padronizados, 5 a 7 dias úteis são suficientes se a documentação
        estiver atualizada. Para serviços que exigem proposta técnica
        detalhada, o mínimo recomendado é 10 a 15 dias úteis. Para obras e
        serviços de engenharia, considere pelo menos 15 a 20 dias úteis para
        orçamento, cronograma e visita técnica ao local.
      </p>

      <h3>O valor estimado da licitação influencia na decisão de participar?</h3>
      <p>
        Sim, e de forma significativa. Cada empresa tem uma faixa de valor
        onde é mais competitiva, determinada por sua estrutura de custos,
        capacidade operacional e atestados disponíveis. Disputar editais com
        valor muito acima dessa faixa resulta em desclassificação por falta
        de atestados proporcionais. Disputar editais com valor muito abaixo
        resulta em margem insuficiente para justificar o custo da proposta.
        A recomendação é concentrar esforço na faixa onde o histórico de
        vitórias é maior.
      </p>

      <h3>A localização geográfica realmente impacta a viabilidade de uma licitação?</h3>
      <p>
        Sim, especialmente para serviços presenciais e fornecimento de bens
        volumosos. Para serviços, a proximidade do local de execução afeta
        diretamente o custo de mobilização, supervisão e manutenção do
        contrato. Para fornecimento de bens, o custo de frete pode representar
        entre 5% e 15% do valor total do contrato, dependendo da distância e
        do tipo de produto. Empresas com atuação regional concentrada tendem a
        ter margens melhores em editais da sua região de abrangência.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
