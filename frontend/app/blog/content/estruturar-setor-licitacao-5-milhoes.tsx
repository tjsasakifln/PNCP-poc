import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-07: Como Estruturar um Setor de Licitação Enxuto para Faturar R$ 5 Milhões por Ano
 * Target: 3,000–3,500 words
 */
export default function EstruturarSetorLicitacao5Milhões() {
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
                name: 'Quantas pessoas precisa ter um setor de licitação para faturar R$ 5 milhões por ano?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Um setor de licitação enxuto e bem estruturado pode faturar R$ 5 milhões anuais com 2 a 3 profissionais dedicados: um analista de editais (triagem e compliance), um especialista em propostas (precificação e documentação) e, opcionalmente, um gestor de contratos. A chave está na automação da triagem e na especialização de cada papel, não no volume de pessoas.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o salário médio de um analista de licitações no Brasil?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Segundo dados consolidados de plataformas de emprego como Glassdoor e Catho (2025), o salário médio de um analista de licitações no Brasil varia entre R$ 3.200 e R$ 5.800 por mês, dependendo da região e do porte da empresa. Em capitais como São Paulo e Brasília, profissionais sêniores podem alcançar R$ 7.000 a R$ 9.000 mensais.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais KPIs devo acompanhar no setor de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os KPIs essenciais de um setor de licitação são: taxa de adjudicação (meta acima de 20%), valor médio dos contratos ganhos, custo por proposta elaborada, tempo médio entre publicação do edital e envio da proposta, volume de editais triados versus propostas efetivamente enviadas, e valor total do pipeline ativo. O acompanhamento mensal desses indicadores permite ajustes rápidos na estratégia.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível terceirizar parte do setor de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. A triagem de editais e a organização documental são as atividades mais terceirizáveis, podendo ser delegadas a consultorias especializadas ou ferramentas de automação. A precificação e a elaboração da proposta técnica, por envolverem conhecimento específico do negócio, devem permanecer internas. A gestão de contratos também pode ser parcialmente terceirizada, especialmente em empresas com volume alto de contratos simultâneos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o investimento inicial para montar um setor de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O investimento inicial para um setor de licitação enxuto (2 pessoas + ferramentas) gira em torno de R$ 12.000 a R$ 18.000 mensais, considerando salários, encargos e ferramentas de monitoramento. Esse investimento se paga com um a dois contratos adjudicados por trimestre, dependendo do ticket médio do setor de atuação.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Faturar R$ 5 milhões por ano com licitações públicas não exige uma equipe de 10 pessoas,
        um departamento inteiro ou anos de experiência prévia no mercado B2G. Exige, sim, uma
        estrutura enxuta, processos bem definidos e a capacidade de filtrar oportunidades com
        critério. Neste artigo, apresentamos o modelo operacional que empresas de médio porte
        utilizam para alcançar esse patamar com apenas 2 a 3 profissionais dedicados — e como
        a tecnologia elimina os gargalos que, historicamente, exigiam mais pessoas.
      </p>

      <p>
        O mercado de compras públicas no Brasil movimentou R$ 1,4 trilhão entre 2023 e 2024,
        segundo dados do Painel de Compras do Governo Federal. Desse montante, mais de 60% foi
        operado por meio de pregões eletrônicos, acessíveis a empresas de qualquer porte. O
        volume de oportunidades é abundante — o que falta na maioria das empresas não é mercado,
        mas capacidade operacional para capturar essas oportunidades de forma sistemática.
      </p>

      <h2>O modelo enxuto: 2 a 3 pessoas mais tecnologia</h2>

      <p>
        A estrutura tradicional de um setor de licitação em empresas de médio porte geralmente
        envolve 4 a 6 pessoas: analistas juniores para monitoramento, analistas plenos para
        elaboração de propostas, um coordenador e apoio administrativo. Esse modelo gera custos
        fixos elevados e, paradoxalmente, não garante resultados proporcionais ao investimento.
      </p>

      <p>
        O modelo enxuto inverte essa lógica. Em vez de contratar mais pessoas para processar
        mais editais, ele combina especialização de papéis com automação de tarefas repetitivas.
        A estrutura se resume a três funções complementares, das quais a terceira é opcional
        nos primeiros anos de operação.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: custos do modelo enxuto vs. tradicional</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• Modelo tradicional (5 pessoas): R$ 35.000 a R$ 55.000/mês em salários e encargos (fonte: Glassdoor Brasil, mediana salarial 2025 para analistas de licitação)</li>
          <li>• Modelo enxuto (2-3 pessoas + ferramentas): R$ 12.000 a R$ 22.000/mês incluindo software de monitoramento</li>
          <li>• Ticket médio de contratos públicos por pregão eletrônico: R$ 180.000 a R$ 450.000, variando por setor (fonte: Painel de Compras Governamentais, 2024)</li>
          <li>• Taxa de adjudicação média do mercado: 8% a 12% (fonte: pesquisa Bidding Analytics, 2024)</li>
        </ul>
      </div>

      <h2>Papel 1: Analista de editais — triagem e compliance</h2>

      <p>
        O analista de editais é a primeira linha de defesa contra desperdício de recursos. Sua
        função central é separar oportunidades viáveis de editais que não merecem investimento
        de tempo. Essa triagem precisa ser rápida, sistemática e baseada em critérios objetivos
        — não em intuição.
      </p>

      <h3>Responsabilidades principais</h3>

      <p>
        O analista de editais é responsável pelo monitoramento diário de publicações nos portais
        PNCP, ComprasGov e Portal de Compras Públicas; pela triagem inicial com base em
        alinhamento setorial, faixa de valor e região geográfica; pela verificação de requisitos
        de habilitação (atestados técnicos, certidões, qualificação econômica); e pela
        alimentação do pipeline de oportunidades com editais pré-qualificados. Para entender
        como organizar esse pipeline de forma eficiente,{' '}
        <Link href="/blog/pipeline-licitações-funil-comercial">
          veja nosso guia sobre funil comercial em licitações
        </Link>.
      </p>

      <h3>Perfil e faixa salarial</h3>

      <p>
        O perfil ideal combina formação em Administração, Direito ou áreas correlatas com
        experiência prática em leitura de editais. Segundo dados da Catho e Glassdoor
        atualizados em 2025, a faixa salarial para analistas de licitação no Brasil é:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Faixas salariais — Analista de Licitações (2025)</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• Júnior (0-2 anos): R$ 2.800 a R$ 4.200/mês (fonte: Catho, mediana nacional 2025)</li>
          <li>• Pleno (2-5 anos): R$ 4.500 a R$ 6.500/mês (fonte: Glassdoor, mediana nacional 2025)</li>
          <li>• Sênior (5+ anos): R$ 6.500 a R$ 9.000/mês, podendo chegar a R$ 11.000 em Brasília e São Paulo</li>
        </ul>
      </div>

      <p>
        No modelo enxuto, um analista pleno é suficiente. A automação da triagem inicial
        permite que essa pessoa dedique tempo à análise qualitativa dos editais pré-filtrados,
        em vez de gastar horas lendo publicações irrelevantes.
      </p>

      <h2>Papel 2: Especialista em propostas — precificação e documentação</h2>

      <p>
        Se o analista define quais licitações merecem atenção, o especialista em propostas
        define como competir. Essa função exige conhecimento técnico profundo do setor de
        atuação da empresa, domínio de precificação competitiva e experiência com a elaboração
        de documentos que atendam rigorosamente aos requisitos do edital.
      </p>

      <h3>Responsabilidades principais</h3>

      <p>
        O especialista em propostas é responsável pela composição de preços com margem de
        segurança e competitividade; pela elaboração da proposta técnica, quando exigida; pela
        montagem e conferência do envelope de habilitação; pelo acompanhamento da sessão
        pública (pregão eletrônico) e interposição de recursos quando pertinente; e pela
        análise pós-resultado para retroalimentar os critérios de triagem.
      </p>

      <h3>Perfil e faixa salarial</h3>

      <p>
        O especialista em propostas geralmente tem formação na área técnica do setor da empresa
        (engenharia para obras, TI para software, nutrição para alimentação) combinada com
        experiência em licitações. A faixa salarial é ligeiramente superior à do analista,
        refletindo a especialização técnica: R$ 5.500 a R$ 8.500 para perfil pleno, podendo
        ultrapassar R$ 10.000 para sêniores em setores de alta complexidade como engenharia e
        saúde (fonte: Glassdoor Brasil, 2025).
      </p>

      <h2>Papel 3 (opcional): Gestor de contratos</h2>

      <p>
        Nos primeiros anos de operação, a gestão de contratos pode ser absorvida pelo
        especialista em propostas ou pelo gestor geral da empresa. Conforme o volume de
        contratos ativos cresce — tipicamente acima de 5 contratos simultâneos —, a dedicação
        de uma pessoa a essa função torna-se necessária.
      </p>

      <h3>Quando contratar</h3>

      <p>
        O indicador mais confiável é o número de contratos ativos simultâneos. Até 4 contratos,
        a gestão pode ser absorvida pela equipe existente. Entre 5 e 8 contratos, a dedicação
        parcial (meio período) já se justifica. Acima de 8 contratos, a dedicação integral
        evita atrasos em entregas, multas contratuais e perda de reputação junto aos órgãos
        contratantes.
      </p>

      <p>
        O gestor de contratos acompanha prazos de entrega, processos de medição, emissão de
        notas fiscais, e antecipa renovações ou aditivos. A faixa salarial é similar à do
        analista pleno: R$ 4.500 a R$ 7.500 mensais.
      </p>

      <h2>A cadeia operacional: prospecção, triagem, análise, proposta e acompanhamento</h2>

      <p>
        O setor de licitação enxuto opera em cinco etapas sequenciais, cada uma com
        responsável e critérios claros de transição. A eficiência do setor depende da
        fluidez dessa cadeia — um gargalo em qualquer etapa compromete o resultado final.
      </p>

      <h3>Etapa 1: Prospecção</h3>

      <p>
        A prospecção consiste no monitoramento diário de novas publicações nos portais de
        compras públicas. Em um modelo manual, essa etapa consome entre 1 e 3 horas diárias.
        Com ferramentas automatizadas de monitoramento, o tempo cai para 15 a 30 minutos
        de revisão de alertas já filtrados por setor e região.
      </p>

      <h3>Etapa 2: Triagem</h3>

      <p>
        Dos editais identificados na prospecção, a triagem seleciona aqueles que atendem aos
        critérios mínimos da empresa: alinhamento setorial, faixa de valor compatível,
        região geográfica viável, e ausência de requisitos de habilitação inalcançáveis.
        A taxa de aprovação típica nessa etapa é de 15% a 25% — ou seja, a cada 100 editais
        monitorados, entre 15 e 25 passam para análise detalhada.
      </p>

      <h3>Etapa 3: Análise detalhada</h3>

      <p>
        Os editais aprovados na triagem passam por análise completa: leitura integral do
        edital e anexos, verificação de requisitos de habilitação, levantamento de histórico
        do órgão contratante e avaliação de competitividade. Essa etapa é conduzida pelo
        analista de editais com apoio do especialista em propostas.
      </p>

      <BlogInlineCTA slug="estruturar-setor-licitação-5-milhões" campaign="b2g" />

      <h3>Etapa 4: Elaboração da proposta</h3>

      <p>
        Somente os editais aprovados na análise detalhada recebem investimento de elaboração
        de proposta. O especialista em propostas conduz a precificação, a redação técnica e
        a montagem documental. O tempo médio de elaboração varia de 8 a 40 horas, dependendo
        da complexidade do objeto.
      </p>

      <h3>Etapa 5: Acompanhamento</h3>

      <p>
        Após o envio da proposta, o acompanhamento inclui participação na sessão pública,
        resposta a diligências, interposição ou contrarrazão de recursos, e assinatura do
        contrato em caso de adjudicação.
      </p>

      <h2>Ferramentas essenciais: da planilha ao sistema</h2>

      <p>
        O estágio de maturidade das ferramentas utilizadas pelo setor de licitação tem
        impacto direto na produtividade. A maioria das empresas inicia com planilhas e
        migra para sistemas especializados conforme o volume de operação justifica o
        investimento.
      </p>

      <h3>Estágio 1: Planilha e busca manual</h3>

      <p>
        No estágio inicial, a equipe busca editais diretamente nos portais (PNCP, ComprasNet,
        portais estaduais) e registra oportunidades em planilhas. Esse modelo funciona para
        até 10 a 15 editais acompanhados simultaneamente, mas colapsa rapidamente com o
        aumento de volume.
      </p>

      <h3>Estágio 2: Alertas e monitoramento automatizado</h3>

      <p>
        Ferramentas de monitoramento que agregam publicações de múltiplos portais e enviam
        alertas filtrados por setor eliminam a etapa de busca manual. O ganho típico é de
        60% a 70% do tempo de prospecção.
      </p>

      <h3>Estágio 3: Inteligência e classificação por IA</h3>

      <p>
        No estágio mais avançado, ferramentas como o{' '}
        <Link href="/features">SmartLic</Link> vão além do monitoramento: classificam
        editais por relevância setorial usando inteligência artificial, avaliam viabilidade
        com base em quatro critérios objetivos (modalidade, prazo, valor e geografia) e
        organizam o pipeline de oportunidades em formato visual. Isso permite que a equipe
        enxuta se concentre exclusivamente nas etapas que exigem julgamento humano —
        análise detalhada e elaboração de propostas.
      </p>

      <h2>KPIs do setor de licitação</h2>

      <p>
        Um setor de licitação sem métricas opera no escuro. Os indicadores a seguir permitem
        que a gestão identifique gargalos, ajuste a estratégia e projete resultados com
        maior previsibilidade. O acompanhamento deve ser mensal, com revisão trimestral
        de metas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">KPIs essenciais do setor de licitação</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• <strong>Taxa de adjudicação:</strong> percentual de propostas enviadas que resultam em contrato. Meta mínima: 20%. Empresas de alto desempenho operam entre 25% e 35% (fonte: Bidding Analytics, 2024)</li>
          <li>• <strong>Volume de pipeline:</strong> soma do valor estimado de todos os editais em acompanhamento ativo. Deve ser de 3x a 5x a meta de faturamento anual</li>
          <li>• <strong>Custo por proposta:</strong> custo total do setor dividido pelo número de propostas enviadas no período. Referência de mercado: R$ 2.500 a R$ 8.000 por proposta</li>
          <li>• <strong>Tempo médio de resposta:</strong> dias entre publicação do edital e envio da proposta. Quanto menor, maior a chance de identificar pendências a tempo</li>
          <li>• <strong>Taxa de triagem:</strong> percentual de editais monitorados que passam para análise. Referência: 15% a 25%</li>
          <li>• <strong>Valor médio por contrato:</strong> acompanhamento por setor e modalidade para calibrar as faixas de valor buscadas</li>
        </ul>
      </div>

      <p>
        O acompanhamento desses indicadores permite identificar rapidamente se o setor está
        investindo tempo nos editais certos. Uma taxa de adjudicação abaixo de 15%
        consistentemente indica problemas na triagem ou na precificação.{' '}
        <Link href="/blog/como-aumentar-taxa-vitória-licitações">
          Veja estratégias específicas para aumentar a taxa de vitória
        </Link>.
      </p>

      <h2>Meta de R$ 5 milhões: o funil reverso</h2>

      <p>
        Para atingir R$ 5 milhões em contratos públicos por ano, é preciso construir o
        raciocínio de trás para frente — o funil reverso. Esse exercício revela quantos
        editais o setor precisa monitorar, triar, analisar e licitar para alcançar a meta.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Exemplo prático: funil reverso para R$ 5 milhões/ano</p>
        <div className="text-sm text-ink-secondary space-y-3">
          <p><strong>Premissas (setor de materiais elétricos, região Sudeste):</strong></p>
          <ul className="space-y-1 ml-4">
            <li>• Ticket médio por contrato: R$ 250.000</li>
            <li>• Taxa de adjudicação estimada: 22%</li>
            <li>• Taxa de aprovação na triagem: 20%</li>
            <li>• Taxa de conversão análise detalhada para proposta: 60%</li>
          </ul>
          <p><strong>Cálculo reverso:</strong></p>
          <ul className="space-y-1 ml-4">
            <li>• Meta anual: R$ 5.000.000</li>
            <li>• Contratos necessários: R$ 5.000.000 / R$ 250.000 = <strong>20 contratos</strong></li>
            <li>• Propostas necessárias: 20 / 0,22 = <strong>91 propostas/ano</strong> (aproximadamente 8 por mês)</li>
            <li>• Editais em análise detalhada: 91 / 0,60 = <strong>152 editais analisados/ano</strong></li>
            <li>• Editais triados: 152 / 0,20 = <strong>760 editais triados/ano</strong> (63 por mês)</li>
          </ul>
          <p><strong>Resultado:</strong> o setor precisa monitorar e triar aproximadamente 63 editais por mês para sustentar um pipeline que gere 20 contratos de R$ 250 mil ao longo do ano. Com triagem automatizada, esse volume é perfeitamente gerenciável por 2 pessoas.</p>
        </div>
      </div>

      <p>
        Esse cálculo evidencia por que a triagem automatizada é tão crítica. Triar 63 editais
        por mês manualmente — lendo cada um para verificar alinhamento setorial, requisitos
        de habilitação e viabilidade — consome dezenas de horas. Com classificação automatizada,
        o analista recebe apenas os 12 a 15 editais que já passaram pelo filtro de relevância
        e viabilidade, concentrando o esforço humano na análise que realmente importa.
      </p>

      <p>
        Cabe observar que o exemplo acima assume um ticket médio de R$ 250.000, típico de
        setores como materiais elétricos, mobiliário e informática. Para setores com tickets
        maiores — como engenharia civil (R$ 500.000 a R$ 2.000.000) — o número de contratos
        necessários cai proporcionalmente, mas a complexidade de cada proposta aumenta. O
        modelo enxuto se aplica em ambos os cenários; o que muda é a distribuição de tempo
        entre triagem e elaboração.
      </p>

      <h2>Cronograma de implantação</h2>

      <p>
        Montar um setor de licitação não é um projeto de meses. Uma empresa que já tem
        conhecimento do seu setor e experiência comercial pode ter o departamento operacional
        em 4 a 6 semanas, seguindo um cronograma realista.
      </p>

      <h3>Semana 1 a 2: Definição de escopo e contratação</h3>

      <p>
        Definir os setores e regiões de atuação prioritários, os critérios mínimos de triagem
        (faixa de valor, modalidades, requisitos de habilitação) e iniciar o processo de
        seleção do analista de editais. Paralelamente, configurar as ferramentas de
        monitoramento.
      </p>

      <h3>Semana 3 a 4: Operação assistida</h3>

      <p>
        O analista inicia a operação com supervisão próxima. Os primeiros editais triados
        servem como calibragem dos critérios. É comum que as primeiras semanas revelem
        ajustes necessários nos filtros — setores muito amplos, faixas de valor inadequadas,
        ou regiões com poucos editais relevantes.
      </p>

      <h3>Semana 5 a 6: Primeira proposta e ajustes</h3>

      <p>
        O envio da primeira proposta é o marco real de início de operação. A partir desse
        ponto, o ciclo de feedback entre triagem, análise e resultado começa a gerar dados
        para refinamento contínuo dos critérios.
      </p>

      <h2>Erros mais comuns na estruturação</h2>

      <p>
        A experiência de empresas que passaram por esse processo revela padrões recorrentes
        de erro que devem ser evitados desde o início.
      </p>

      <p>
        O primeiro erro é tentar cobrir muitos setores simultaneamente. Empresas que atuam
        em três ou quatro setores devem priorizar um ou dois no início e expandir conforme
        o setor ganha maturidade operacional. O segundo erro é não definir critérios de
        triagem antes de começar — o que resulta em analisar editais que nunca deveriam
        ter chegado à mesa do analista. O terceiro erro é negligenciar a retroalimentação:
        sem analisar por que perdeu ou ganhou cada licitação, o setor não evolui.
      </p>

      <p>
        Empresas que mantêm uma disciplina de análise pós-resultado — registrando o motivo
        de cada vitória e derrota — apresentam evolução consistente na taxa de adjudicação
        ao longo de 6 a 12 meses. Para entender quais fatores diferenciam empresas com
        alta taxa de vitória,{' '}
        <Link href="/blog/empresas-vencem-30-porcento-pregões">
          leia nossa análise sobre empresas que vencem 30% dos pregões
        </Link>. Vale também conhecer{' '}
        <Link href="/blog/escalar-consultoria-sem-depender-horas-técnicas">
          como consultorias escalam sem depender de horas técnicas
        </Link>{' '}
        — o modelo enxuto descrito aqui tem paralelos diretos com a estrutura
        que assessorias de licitação adotam para crescer com eficiência.
      </p>

      <h2>O papel da tecnologia na viabilidade do modelo enxuto</h2>

      <p>
        O modelo de 2 a 3 pessoas só é viável porque a tecnologia absorve as tarefas de
        maior volume e menor valor agregado. Sem automação, o mesmo resultado exigiria 4 a
        6 pessoas — o que inviabiliza o retorno sobre investimento para empresas de médio
        porte.
      </p>

      <p>
        As três áreas de maior impacto da automação no setor de licitação são: a prospecção
        (monitoramento automatizado de múltiplos portais), a triagem (classificação por
        relevância e viabilidade) e o controle de pipeline (visão consolidada de todas as
        oportunidades em andamento com prazos e status). O{' '}
        <Link href="/planos">SmartLic</Link> cobre essas três áreas em uma única plataforma,
        permitindo que a equipe enxuta opere com a mesma eficiência de departamentos maiores.
      </p>

      {/* CTA — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Automatize a triagem e libere sua equipe para o que importa
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic monitora PNCP, ComprasGov e Portal de Compras Públicas, classifica editais por
          setor e viabilidade, e organiza seu pipeline de oportunidades — para que sua equipe
          enxuta foque em elaborar propostas vencedoras.
        </p>
        <Link
          href="/signup?source=blog&article=estruturar-setor-licitação-5-milhões&utm_source=blog&utm_medium=cta&utm_content=estruturar-setor-licitação-5-milhões&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/planos" className="underline hover:text-ink">
            Ver planos
          </Link>
        </p>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Quantas pessoas precisa ter um setor de licitação para faturar R$ 5 milhões por ano?</h3>
      <p>
        Um setor de licitação enxuto e bem estruturado pode faturar R$ 5 milhões anuais com 2 a 3
        profissionais dedicados: um analista de editais (triagem e compliance), um especialista em
        propostas (precificação e documentação) e, opcionalmente, um gestor de contratos. A chave
        está na automação da triagem e na especialização de cada papel, não no volume de pessoas.
      </p>

      <h3>Qual o salário médio de um analista de licitações no Brasil?</h3>
      <p>
        Segundo dados consolidados de plataformas de emprego como Glassdoor e Catho (2025), o
        salário médio de um analista de licitações no Brasil varia entre R$ 3.200 e R$ 5.800 por
        mês, dependendo da região e do porte da empresa. Em capitais como São Paulo e Brasília,
        profissionais sêniores podem alcançar R$ 7.000 a R$ 9.000 mensais.
      </p>

      <h3>Quais KPIs devo acompanhar no setor de licitação?</h3>
      <p>
        Os KPIs essenciais são: taxa de adjudicação (meta acima de 20%), valor médio dos contratos
        ganhos, custo por proposta elaborada, tempo médio entre publicação e envio da proposta,
        volume de editais triados versus propostas enviadas, e valor total do pipeline ativo. O
        acompanhamento mensal desses indicadores permite ajustes rápidos na estratégia.
      </p>

      <h3>É possível terceirizar parte do setor de licitação?</h3>
      <p>
        Sim. A triagem de editais e a organização documental são as atividades mais terceirizáveis,
        podendo ser delegadas a consultorias especializadas ou ferramentas de automação. A
        precificação e a elaboração da proposta técnica, por envolverem conhecimento específico do
        negócio, devem permanecer internas.
      </p>

      <h3>Qual o investimento inicial para montar um setor de licitação?</h3>
      <p>
        O investimento inicial para um setor de licitação enxuto (2 pessoas + ferramentas) gira em
        torno de R$ 12.000 a R$ 18.000 mensais, considerando salários, encargos e ferramentas de
        monitoramento. Esse investimento se paga com um a dois contratos adjudicados por trimestre,
        dependendo do ticket médio do setor de atuação.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
