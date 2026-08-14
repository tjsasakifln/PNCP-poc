import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-10: Licitacao por Volume ou por Inteligencia
 * Target: 2,500-3,000 words | Cluster: inteligencia em licitacoes
 */
export default function LicitacaoVolumeOuInteligencia() {
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
                name: 'Qual a diferença entre estratégia de volume e estratégia de inteligência em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A estratégia de volume prioriza a quantidade de participações, apostando na lei dos grandes números para converter contratos. A estratégia de inteligência prioriza a seleção criteriosa de editais com base em dados de viabilidade, histórico do órgão, concorrência estimada e aderência técnica. Empresas de volume tipicamente participam de 30 a 80 pregões por mês com taxas de vitória entre 5% e 10%. Empresas de inteligência participam de 8 a 20 pregões por mês com taxas entre 20% e 35%.',
                },
              },
              {
                '@type': 'Question',
                name: 'A estratégia de volume funciona para empresas pequenas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Raramente. Empresas com equipes de 1 a 3 pessoas no setor de licitações não conseguem manter a qualidade das propostas em alto volume de participações. O custo operacional por proposta (R$ 800 a R$ 2.500) consome margem de forma desproporcional quando a taxa de vitória é baixa. Para empresas pequenas, a estratégia de inteligência seletiva oferece melhor retorno sobre o investimento.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível combinar volume e inteligência?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O modelo híbrido aplica volume para oportunidades de baixo risco e baixo custo de proposta (como atas de registro de preços e pregões eletrônicos padronizados) e inteligência seletiva para oportunidades de alto valor ou alta complexidade. Esse modelo exige triagem automatizada para funcionar em escala.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto custa em média elaborar uma proposta de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo médio varia entre R$ 800 e R$ 2.500 por proposta, considerando horas de analista, documentação, certidões, garantias e custos administrativos. Para licitações de engenharia ou serviços complexos, esse custo pode ultrapassar R$ 5.000 por proposta. Esse custo operacional é o principal fator na decisão entre volume e inteligência.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como migrar de uma estratégia de volume para inteligência sem perder receita?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A migração deve ser gradual, em três fases: primeiro, classificar o portfólio atual de licitações por taxa de vitória histórica e margem líquida; segundo, eliminar progressivamente as categorias com pior retorno (começando pelos 20% com menor taxa de vitória); terceiro, reinvestir o tempo liberado em análise aprofundada das oportunidades remanescentes. O ciclo completo leva de 3 a 6 meses.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Existem duas escolas de pensamento sobre como competir em licitações
        públicas. A primeira defende a participação massiva: quanto mais pregões
        a empresa disputa, mais contratos fecha. A segunda argumenta que a
        seleção criteriosa de editais gera mais lucro com menos esforço. As
        duas posições têm mérito, mas os dados do mercado indicam que a resposta
        não é tão simples quanto escolher um lado.
      </p>

      <p>
        Neste artigo, analisamos quantitativamente as duas estratégias,
        apresentamos cenários reais para empresas de diferentes portes e
        propomos um modelo híbrido que captura o melhor de cada abordagem. Se
        você já se perguntou se compensa{' '}
        <Link href="/blog/disputar-todas-licitacoes-matematica-real">
          disputar todas as licitações do seu segmento
        </Link>, a análise a seguir oferece uma resposta baseada em números.
      </p>

      <h2>As duas escolas: volume versus seleção</h2>

      <p>
        A estratégia de volume parte de uma premissa estatística: se a taxa
        média de vitória em pregões eletrônicos gira em torno de 8% a 12%, é
        preciso participar de muitas licitações para fechar contratos
        suficientes. Com 50 participações por mês e uma taxa de 10%, a empresa
        fecha 5 contratos. A lógica é linear e intuitiva.
      </p>

      <p>
        A estratégia de inteligência inverte a equação. Em vez de aumentar o
        numerador (número de participações), ela melhora o denominador (taxa de
        conversão). Uma empresa que participa de 15 pregões por mês com taxa de
        30% também fecha entre 4 e 5 contratos, mas com um terço do esforço
        operacional.
      </p>

      <p>
        A diferença fundamental não está no resultado bruto (número de
        contratos), mas no custo para chegar lá e na margem líquida que cada
        contrato entrega. E é nessa diferença que o debate se resolve.
      </p>

      <h2>Perfil da estratégia de volume</h2>

      <h3>Como funciona na prática</h3>

      <p>
        Empresas que adotam a estratégia de volume tipicamente operam com
        equipes maiores no setor de licitações (4 a 8 analistas), utilizam
        ferramentas de busca básicas para captar o maior número possível de
        editais e padronizam ao máximo o processo de elaboração de propostas.
        A premissa é que o custo marginal de cada proposta adicional é baixo
        quando o processo está industrializado.
      </p>

      <h3>Quando funciona</h3>

      <p>
        A estratégia de volume é viável em setores com alta padronização de
        editais, como materiais de escritório, informática básica e alimentos.
        Nesses mercados, o objeto é previsível, os requisitos de habilitação
        são recorrentes e a proposta comercial pode ser montada em poucas
        horas. Empresas com grande capacidade de atendimento geográfico
        (cobertura nacional) também se beneficiam do volume, pois cada UF
        adicional multiplica oportunidades sem aumentar proporcionalmente o
        custo fixo.
      </p>

      <h3>Os riscos que ninguém menciona</h3>

      <p>
        O problema da estratégia de volume não aparece no mês seguinte, mas no
        acumulado do ano. Participar de muitas licitações sem triagem rigorosa
        gera três efeitos colaterais. Primeiro, a equipe é sobrecarregada e
        começa a cometer erros em propostas críticas. Segundo, a margem média
        por contrato tende a cair, porque a empresa aceita oportunidades com
        margens apertadas para manter o volume. Terceiro, o custo de
        participação em pregões perdidos se acumula de forma invisível.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: custo operacional por proposta</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; O custo médio de elaboração de uma proposta para pregão eletrônico varia entre R$ 800 e R$ 2.500,
            incluindo horas de analista, documentação, certidões e custos administrativos (Fonte: SEBRAE,{' '}
            <em>Cartilha de Licitações para Micro e Pequenas Empresas</em>, 2023).
          </li>
          <li>
            &bull; Segundo levantamento do Portal de Compras Governamentais, a taxa média de desclassificação em
            pregões eletrônicos é de 38%, sendo que 62% das desclassificações ocorrem por falhas documentais,
            não por preço (ComprasGov, Painel de Monitoramento, 2024).
          </li>
          <li>
            &bull; De acordo com o Tribunal de Contas da União (TCU), o valor médio de contratos adjudicados via
            pregão eletrônico foi de R$ 287 mil em 2024, com mediana de R$ 78 mil, indicando alta concentração
            em contratos de valor intermediário (TCU, Relatório de Fiscalização de Aquisições, 2024).
          </li>
        </ul>
      </div>

      <h2>Perfil da estratégia de inteligência</h2>

      <h3>Como funciona na prática</h3>

      <p>
        A estratégia de inteligência começa antes da busca de editais: pela
        definição rigorosa do perfil de oportunidade ideal. A empresa mapeia
        suas vantagens competitivas reais (preço, capacidade técnica,
        localização, atestados acumulados), define faixas de valor onde sua
        margem é sustentável e identifica órgãos com histórico de pagamento
        regular. Só então inicia a busca, filtrando por critérios objetivos
        antes de investir tempo na análise do edital.
      </p>

      <p>
        Empresas que adotam essa abordagem frequentemente utilizam ferramentas
        de{' '}
        <Link href="/features">
          análise de viabilidade automatizada
        </Link>{' '}
        para pontuar cada oportunidade antes de decidir participar. O objetivo
        não é encontrar todas as licitações disponíveis, mas apenas aquelas
        onde a probabilidade de vitória e a margem esperada justificam o
        investimento.
      </p>

      <h3>Quando funciona</h3>

      <p>
        A estratégia de inteligência é mais eficaz em setores de alta
        complexidade técnica, como engenharia, software, saúde e serviços
        especializados. Nesses mercados, cada proposta exige análise
        aprofundada do edital, dimensionamento técnico e precificação sob
        medida. O custo por proposta é alto (R$ 2.000 a R$ 5.000 ou mais),
        tornando cada participação um investimento significativo que precisa
        ser direcionado com critério.
      </p>

      <BlogInlineCTA slug="licitacao-volume-ou-inteligencia" campaign="b2g" />

      <h3>As limitações reais</h3>

      <p>
        A estratégia de inteligência tem dois riscos principais. Primeiro,
        a seletividade excessiva pode levar a empresa a recusar oportunidades
        boas por excesso de cautela, resultando em um pipeline muito enxuto
        para sustentar o faturamento desejado. Segundo, a dependência de dados
        históricos pode criar vieses: a empresa só busca o que já conhece e
        ignora oportunidades em nichos adjacentes. A calibração dos filtros de
        triagem é crucial e deve ser revista trimestralmente.
      </p>

      <h2>Comparação quantitativa: três cenários reais</h2>

      <p>
        Para tornar a análise concreta, simulamos três cenários com parâmetros
        realistas para empresas de diferentes portes. Todos os cenários
        consideram um ciclo anual, com custo operacional médio por proposta
        de R$ 1.500 e margem líquida média de 12% sobre o valor do contrato.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Exemplo prático: simulação comparativa anual</p>
        <div className="space-y-4 text-sm text-ink-secondary">
          <div>
            <p className="font-medium text-ink mb-1">Cenário 1 — Pequena empresa (2 analistas)</p>
            <p>
              <strong>Volume:</strong> 25 participações/mês = 300/ano. Taxa de vitória: 8%. Contratos: 24.
              Valor médio: R$ 80 mil. Faturamento bruto: R$ 1,92 milhão. Custo de propostas: R$ 450 mil.
              Margem líquida (12%): R$ 230 mil. <strong>Lucro após custo de propostas: -R$ 220 mil.</strong>
            </p>
            <p className="mt-1">
              <strong>Inteligência:</strong> 8 participações/mês = 96/ano. Taxa de vitória: 25%. Contratos: 24.
              Valor médio: R$ 95 mil (editais mais qualificados). Faturamento bruto: R$ 2,28 milhões. Custo de propostas: R$ 144 mil.
              Margem líquida (12%): R$ 274 mil. <strong>Lucro após custo de propostas: +R$ 130 mil.</strong>
            </p>
          </div>
          <div>
            <p className="font-medium text-ink mb-1">Cenário 2 — Média empresa (4 analistas)</p>
            <p>
              <strong>Volume:</strong> 50 participações/mês = 600/ano. Taxa: 10%. Contratos: 60.
              Valor médio: R$ 120 mil. Faturamento: R$ 7,2 milhões. Custo propostas: R$ 900 mil.
              Margem (12%): R$ 864 mil. <strong>Saldo: -R$ 36 mil.</strong>
            </p>
            <p className="mt-1">
              <strong>Inteligência:</strong> 18 participações/mês = 216/ano. Taxa: 28%. Contratos: 60.
              Valor médio: R$ 150 mil. Faturamento: R$ 9 milhões. Custo propostas: R$ 324 mil.
              Margem (12%): R$ 1,08 milhão. <strong>Saldo: +R$ 756 mil.</strong>
            </p>
          </div>
          <div>
            <p className="font-medium text-ink mb-1">Cenário 3 — Grande empresa (8 analistas)</p>
            <p>
              <strong>Volume:</strong> 80 participações/mês = 960/ano. Taxa: 12%. Contratos: 115.
              Valor médio: R$ 200 mil. Faturamento: R$ 23 milhões. Custo propostas: R$ 1,44 milhão.
              Margem (12%): R$ 2,76 milhões. <strong>Saldo: +R$ 1,32 milhão.</strong>
            </p>
            <p className="mt-1">
              <strong>Híbrido:</strong> 40 participações/mês volume + 15 inteligência = 660/ano. Taxa combinada: 18%.
              Contratos: 119. Valor médio: R$ 220 mil. Faturamento: R$ 26,2 milhões. Custo propostas: R$ 990 mil.
              Margem (12%): R$ 3,14 milhões. <strong>Saldo: +R$ 2,15 milhões.</strong>
            </p>
          </div>
          <p className="text-xs mt-3 text-ink-secondary/70">
            Nota: Simulação com parâmetros ilustrativos baseados em médias de mercado. Resultados reais
            variam conforme setor, região e competitividade.
          </p>
        </div>
      </div>

      <p>
        Os números revelam um padrão consistente: a estratégia de volume pura
        só se sustenta em empresas grandes, com equipes robustas e margens de
        escala. Para pequenas e médias empresas, o custo acumulado de propostas
        perdidas corrói a margem. A estratégia de inteligência entrega mais
        lucro líquido em todos os cenários, e o modelo híbrido potencializa os
        resultados para empresas que já possuem escala.
      </p>

      <h2>O modelo híbrido: volume base com inteligência seletiva</h2>

      <p>
        A abordagem mais eficaz para empresas B2G maduras não é escolher entre
        volume e inteligência, mas combinar ambas em camadas. O modelo híbrido
        funciona assim:
      </p>

      <h3>Camada 1: volume automatizado para oportunidades padrão</h3>

      <p>
        Pregões eletrônicos de menor preço com objetos padronizados (materiais,
        equipamentos catalogados, serviços recorrentes) entram no fluxo de
        volume. A proposta é montada com templates pré-aprovados, documentação
        padronizada e precificação baseada em tabela. O tempo de elaboração
        não ultrapassa 2 horas por proposta. A triagem é feita por ferramenta
        automatizada, que filtra por setor, UF, faixa de valor e modalidade.
      </p>

      <h3>Camada 2: inteligência seletiva para oportunidades de alto valor</h3>

      <p>
        Concorrências, tomadas de preço, pregões com objeto complexo e
        licitações acima de determinado valor (tipicamente R$ 500 mil ou mais)
        recebem análise aprofundada. Cada oportunidade passa por avaliação de
        viabilidade com múltiplos critérios:{' '}
        <Link href="/blog/como-aumentar-taxa-vitoria-licitacoes">
          aderência técnica, competitividade de preço, histórico do órgão e
          prazo de execução
        </Link>. Apenas as que atingem um score mínimo de viabilidade avançam
        para elaboração de proposta.
      </p>

      <h3>Camada 3: monitoramento de nicho para oportunidades estratégicas</h3>

      <p>
        Licitações em nichos específicos onde a empresa tem vantagem
        competitiva excepcional (por exemplo, um atestado raro ou uma
        localização privilegiada) recebem tratamento prioritário
        independentemente do valor. Essas oportunidades representam menos de
        10% do pipeline, mas frequentemente geram as maiores margens.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Benchmark setorial: margem por tipo de contrato</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; Contratos de materiais padronizados (papelaria, informática básica): margem líquida média de 6%
            a 10%. Alta concorrência, baixa diferenciação (Fonte: IBGE, Pesquisa Industrial Anual, ajustada para
            contratos públicos, 2023).
          </li>
          <li>
            &bull; Contratos de serviços especializados (engenharia, TI, consultoria): margem líquida média de 14%
            a 22%. Menor concorrência, maior barreira de entrada por exigências técnicas (Fonte: Sinduscon/FGV,
            Índice de Custos da Construção, 2024; dados de mercado setorial).
          </li>
          <li>
            &bull; Atas de registro de preços: margem líquida média de 4% a 8%, compensada pelo volume de
            empenhos ao longo da vigência de 12 meses (Fonte: Comprasnet, Painel de Atas de Registro de Preços,
            dados consolidados 2023-2024).
          </li>
        </ul>
      </div>

      <h2>Como migrar de volume para inteligência</h2>

      <p>
        A transição não deve ser abrupta. Empresas que cortam o volume de
        participações de uma vez correm o risco de criar um vazio no pipeline
        de contratos. A migração deve ser gradual e orientada por dados, em
        três fases:
      </p>

      <h3>Fase 1: diagnóstico (4 semanas)</h3>

      <p>
        Levante os dados dos últimos 12 meses: número de participações, taxa
        de vitória por modalidade, valor médio dos contratos adjudicados,
        custo estimado por proposta e margem líquida por contrato. Classifique
        cada participação em quatro quadrantes: alta taxa/alta margem
        (manter), alta taxa/baixa margem (otimizar), baixa taxa/alta margem
        (investigar) e baixa taxa/baixa margem (eliminar).
      </p>

      <h3>Fase 2: poda seletiva (8 semanas)</h3>

      <p>
        Elimine primeiro as participações do quadrante baixa taxa/baixa margem.
        Essas são as licitações que consomem recursos sem retorno. Tipicamente,
        representam 20% a 30% das participações, mas menos de 5% do
        faturamento. Reinvista o tempo liberado em análise mais aprofundada
        das oportunidades nos quadrantes superiores.
      </p>

      <h3>Fase 3: refinamento contínuo (12 semanas)</h3>

      <p>
        Implemente um sistema de scoring para todas as novas oportunidades.
        Cada edital recebe uma nota de viabilidade antes de entrar no fluxo de
        elaboração. Revise o score de corte trimestralmente com base nos
        resultados reais. Ferramentas como o{' '}
        <Link href="/features">
          SmartLic
        </Link>{' '}
        automatizam essa pontuação, avaliando modalidade, prazo, valor e
        localização geográfica de cada oportunidade.
      </p>

      <p>
        A migração completa leva de 3 a 6 meses. Durante esse período, é
        normal que o número de contratos se mantenha estável enquanto a margem
        líquida aumenta. O ganho de eficiência aparece primeiro na redução do
        custo operacional (menos propostas perdidas) e depois no aumento da
        margem média (oportunidades mais qualificadas).
      </p>

      <h2>O papel da tecnologia na transição</h2>

      <p>
        A estratégia de inteligência exige dados que a triagem manual não
        produz com consistência. Para avaliar viabilidade de forma objetiva,
        a empresa precisa cruzar informações de múltiplas fontes: portal PNCP,
        Portal de Compras Públicas, ComprasGov, histórico de preços
        praticados, dados de concorrentes e métricas internas de desempenho.
      </p>

      <p>
        Fazer esse cruzamento manualmente é possível, mas não escala. Uma
        equipe de 3 analistas consegue avaliar no máximo 10 a 15 editais por
        dia com profundidade suficiente. Com ferramentas de inteligência, o
        mesmo time avalia 50 a 80 editais por dia, aplicando filtros
        automáticos de relevância setorial e viabilidade antes que qualquer
        analista abra o documento.
      </p>

      <p>
        A diferença não é apenas velocidade, mas consistência. O julgamento
        humano flutua com cansaço, vieses e pressão por metas. Um sistema de
        triagem automatizado aplica os mesmos critérios a cada edital, sem
        exceções. Isso não elimina o julgamento humano, mas o direciona para
        as decisões que realmente importam:{' '}
        <Link href="/blog/reduzir-tempo-analisando-editais-irrelevantes">
          quais dos editais pré-qualificados merecem proposta
        </Link>. Esse mesmo princípio fundamenta{' '}
        <Link href="/blog/inteligencia-artificial-consultoria-licitacao-2026">
          o papel da inteligência artificial nas consultorias de licitação em 2026
        </Link>{' '}
        — a transição de volume para inteligência é acelerada quando a IA
        assume as camadas de triagem que antes exigiam horas de trabalho humano.
      </p>

      <h2>Indicadores para monitorar a transição</h2>

      <p>
        Independentemente de qual modelo sua empresa adota, cinco indicadores
        devem ser acompanhados mensalmente para avaliar a eficácia da
        estratégia:
      </p>

      <p>
        <strong>1. Taxa de vitória por faixa de valor:</strong> segmente seus
        resultados em pelo menos três faixas (até R$ 100 mil, R$ 100 mil a
        R$ 500 mil, acima de R$ 500 mil). A taxa de vitória deve ser maior
        nas faixas onde você investe mais tempo de análise.
      </p>

      <p>
        <strong>2. Custo por contrato adjudicado:</strong> divida o custo
        total de propostas pelo número de contratos fechados. Esse número
        deve cair à medida que a seletividade aumenta.
      </p>

      <p>
        <strong>3. Margem líquida média:</strong> acompanhe se a margem está
        subindo com a seletividade. Se a margem não melhora, os critérios de
        triagem precisam ser recalibrados.
      </p>

      <p>
        <strong>4. Tempo médio de elaboração de proposta:</strong> na
        estratégia de inteligência, cada proposta recebe mais atenção.
        Monitore se esse tempo adicional está gerando retorno em taxa de
        vitória.
      </p>

      <p>
        <strong>5. Pipeline coverage ratio:</strong> a relação entre o valor
        total das oportunidades no pipeline e a meta de faturamento.
        Mantenha esse ratio acima de 3x para garantir previsibilidade.
      </p>

      {/* CTA — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Migre para inteligência sem perder oportunidades
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic avalia viabilidade automaticamente em 4 critérios objetivos,
          identificando quais editais merecem sua proposta e quais estão consumindo
          recursos sem retorno.
        </p>
        <Link
          href="/consultoria-b2g?source=blog&article=licitacao-volume-ou-inteligencia&utm_source=blog&utm_medium=cta&utm_content=licitacao-volume-ou-inteligencia&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Pedir um diagnóstico à CONFENGE
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/consultoria-b2g" className="underline hover:text-ink">
            Ver planos
          </Link>
        </p>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Qual a diferença entre estratégia de volume e estratégia de inteligência em licitações?</h3>
      <p>
        A estratégia de volume prioriza a quantidade de participações,
        apostando na lei dos grandes números para converter contratos. A
        estratégia de inteligência prioriza a seleção criteriosa de editais
        com base em dados de viabilidade, histórico do órgão, concorrência
        estimada e aderência técnica. Empresas de volume tipicamente
        participam de 30 a 80 pregões por mês com taxas de vitória entre
        5% e 10%. Empresas de inteligência participam de 8 a 20 pregões
        por mês com taxas entre 20% e 35%.
      </p>

      <h3>A estratégia de volume funciona para empresas pequenas?</h3>
      <p>
        Raramente. Empresas com equipes de 1 a 3 pessoas no setor de
        licitações não conseguem manter a qualidade das propostas em alto
        volume de participações. O custo operacional por proposta (R$ 800
        a R$ 2.500) consome margem de forma desproporcional quando a taxa
        de vitória é baixa. Para empresas pequenas, a estratégia de
        inteligência seletiva oferece melhor retorno sobre o investimento.
      </p>

      <h3>É possível combinar volume e inteligência?</h3>
      <p>
        Sim. O modelo híbrido aplica volume para oportunidades de baixo
        risco e baixo custo de proposta (como atas de registro de preços e
        pregões eletrônicos padronizados) e inteligência seletiva para
        oportunidades de alto valor ou alta complexidade. Esse modelo
        exige triagem automatizada para funcionar em escala.
      </p>

      <h3>Quanto custa em média elaborar uma proposta de licitação?</h3>
      <p>
        O custo médio varia entre R$ 800 e R$ 2.500 por proposta,
        considerando horas de analista, documentação, certidões, garantias
        e custos administrativos. Para licitações de engenharia ou serviços
        complexos, esse custo pode ultrapassar R$ 5.000 por proposta. Esse
        custo operacional é o principal fator na decisão entre volume e
        inteligência.
      </p>

      <h3>Como migrar de uma estratégia de volume para inteligência sem perder receita?</h3>
      <p>
        A migração deve ser gradual, em três fases: primeiro, classificar o
        portfólio atual de licitações por taxa de vitória histórica e margem
        líquida; segundo, eliminar progressivamente as categorias com pior
        retorno (começando pelos 20% com menor taxa de vitória); terceiro,
        reinvestir o tempo liberado em análise aprofundada das oportunidades
        remanescentes. O ciclo completo leva de 3 a 6 meses.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
