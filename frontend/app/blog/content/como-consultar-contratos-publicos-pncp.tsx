import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-01: Como consultar contratos públicos no PNCP: Guia completo
 * Content cluster: contratos públicos
 * Target: ~3,000 words | Primary KW: consultar contratos públicos PNCP
 */
export default function ComoConsultarContratosPublicosPncp() {
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
                name: 'Como buscar contratos públicos por CNPJ no PNCP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Para consultar contratos por CNPJ no PNCP, acesse pncp.gov.br, vá à seção "Contratos" e utilize o campo de busca com o CNPJ do fornecedor ou do órgão contratante. O portal exibe todos os contratos vinculados àquele CNPJ, incluindo objeto, valor, vigência e aditivos. Para análise mais aprofundada de histórico de contratos por CNPJ, ferramentas como o SmartLic consolidam dados do PNCP e apresentam o perfil completo de contratações em poucos segundos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais informações estão disponíveis em um contrato público no PNCP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os contratos publicados no PNCP contêm, obrigatoriamente: número e objeto do contrato, CNPJ e razão social do contratado, órgão contratante, modalidade licitatória de origem, valor inicial, data de assinatura e vigência, situação (vigente, encerrado, rescindido) e eventuais aditivos (prorrogações de prazo e acréscimos de valor). A Lei 14.133/2021 (art. 87 e 174) exige a publicação no PNCP em até 20 dias úteis após a assinatura.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível filtrar contratos por valor ou UF no PNCP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O PNCP oferece filtros por UF (estado), órgão, modalidade licitatória, período de vigência e situação do contrato. O filtro por faixa de valor está disponível na API do portal, mas a interface web tem recursos de filtragem limitados. Para combinações avançadas de filtros — como contratos do setor de saúde em São Paulo com valor acima de R$ 500 mil firmados nos últimos 12 meses — o uso da API ou de ferramentas especializadas como o SmartLic é mais eficiente.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é um aditivo de contrato e como consultá-lo no PNCP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Um aditivo (ou termo aditivo) é um instrumento jurídico que altera cláusulas de um contrato original — podendo ampliar o prazo de vigência, aumentar o valor (acréscimo quantitativo) ou alterar condições de execução. No PNCP, os aditivos são publicados como registros vinculados ao contrato original. Para consultá-los, abra a página do contrato e acesse a aba ou seção de aditivos. A Lei 14.133/2021 limita acréscimos a 25% do valor original para obras e serviços de engenharia, e 50% para outros serviços e compras.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como o SmartLic facilita a consulta de contratos públicos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O SmartLic acessa o datalake do PNCP e consolida contratos públicos por setor, UF e órgão, eliminando a necessidade de buscas manuais repetitivas. A plataforma permite visualizar o histórico de contratos de um fornecedor ou órgão, identificar padrões de contratação por segmento, e monitorar aditivos e renovações em tempo real. Empresas B2G utilizam esses dados para qualificar leads, precificar propostas e identificar oportunidades de substituição de concorrentes.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O Brasil publica mais de 200 mil novos contratos públicos por ano no Portal Nacional de
        Contratações Públicas (PNCP). Cada contrato é um registro estruturado de quem o governo
        está comprando, quanto está pagando e por quanto tempo. Para empresas que atuam no mercado
        B2G, saber consultar contratos públicos no PNCP é uma vantagem competitiva concreta —
        permite identificar concorrentes, precificar propostas com benchmarks reais, detectar
        contratos próximos do vencimento e mapear órgãos com histórico sólido de pagamento. Este
        guia apresenta o passo a passo completo para consultar, filtrar e interpretar contratos
        públicos no PNCP, incluindo como o SmartLic automatiza esse processo para equipes que
        precisam analisar dezenas de contratos por semana.
      </p>

      {/* Section 1: O que é o PNCP e por que ele importa */}
      <h2>O que é o PNCP e por que ele é a fonte primária de contratos públicos</h2>

      <p>
        O Portal Nacional de Contratações Públicas (PNCP) foi criado pelo Decreto 10.764/2021 como
        o repositório centralizado obrigatório para publicação de editais, contratos, atas de
        registro de preços e resultados de licitações no Brasil. Antes do PNCP, as informações
        estavam fragmentadas em centenas de diários oficiais, portais estaduais e sistemas
        municipais sem padronização. A Lei 14.133/2021 (Nova Lei de Licitações) tornou o PNCP
        o veículo oficial de transparência para todos os entes federativos.
      </p>

      <p>
        A obrigatoriedade de publicação foi implementada de forma escalonada. Desde abril de 2023,
        todos os órgãos da administração federal direta são obrigados a publicar no PNCP. Estados
        e municípios de grande porte seguiram em 2024 e 2025, e municípios de menor porte têm
        prazo até 2026. Em termos práticos, o PNCP já concentra o maior volume de contratos
        públicos disponíveis em uma única base consultável — com cobertura crescente e API pública
        que permite acesso programático aos dados.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          PNCP em números — referência 2025
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Contratos publicados:</strong> mais de 2 milhões de contratos no acervo
            histórico, com volume mensal crescente conforme novos entes aderem ao portal.
          </li>
          <li>
            <strong>Cobertura federal:</strong> 100% dos órgãos da administração direta federal
            publicam no PNCP desde abril de 2023 (Decreto 10.764/2021).
          </li>
          <li>
            <strong>API pública:</strong> a API do PNCP (pncp.gov.br/api) é gratuita e sem
            autenticação para consultas básicas, com endpoints para contratos, contratações e
            atas de registro de preços.
          </li>
          <li>
            <strong>Prazo de publicação:</strong> contratos devem ser publicados em até 20 dias
            úteis após a assinatura, conforme art. 87 da Lei 14.133/2021.
          </li>
        </ul>
      </div>

      <p>
        Para fornecedores B2G, o PNCP não é apenas um portal de busca de editais — é uma base de
        inteligência de mercado. Os contratos publicados revelam com precisão quais empresas estão
        ganhando em cada segmento, quais órgãos contratam com maior frequência, quais valores são
        praticados e quando os contratos vigentes serão renovados ou substituídos. Saber ler esses
        dados de forma sistemática transforma a estratégia comercial de qualquer empresa B2G.
        Consulte também o{' '}
        <Link
          href="/blog/contratos/saude"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          guia de contratos do setor de saúde
        </Link>{' '}
        para uma análise setorial detalhada.
      </p>

      {/* Section 2: Passo a passo — buscar por CNPJ */}
      <h2>Como consultar contratos por CNPJ no PNCP</h2>

      <p>
        A busca por CNPJ é a consulta mais utilizada por empresas que querem analisar concorrentes
        ou auditar o histórico de um fornecedor específico. Veja o passo a passo completo.
      </p>

      <h3>Acessar a seção de contratos no portal</h3>

      <p>
        Acesse <strong>pncp.gov.br</strong> e, no menu principal, selecione "Contratos". A seção
        de contratos é independente da seção de editais (chamada de "Contratações" no portal).
        Enquanto a seção de contratações lista editais em andamento, a seção de contratos exibe
        instrumentos já firmados — objetos de contrato, valores, prazos e aditivos.
      </p>

      <h3>Inserir o CNPJ e interpretar os resultados</h3>

      <p>
        No campo de busca da seção de contratos, insira o CNPJ de 14 dígitos (com ou sem
        formatação — o portal aceita ambos). O resultado exibirá todos os contratos associados
        àquele CNPJ, seja como contratado (fornecedor) ou como contratante (órgão público). Para
        cada contrato, o portal mostra:
      </p>

      <ul>
        <li>Número do contrato e número do processo licitatório de origem</li>
        <li>Objeto resumido e objeto detalhado</li>
        <li>Valor inicial pactuado e valor atual (após aditivos)</li>
        <li>Data de assinatura, data de início e data de término da vigência</li>
        <li>Situação atual: vigente, encerrado, rescindido ou suspenso</li>
        <li>Número de aditivos publicados e acesso a cada um deles</li>
      </ul>

      <p>
        Uma limitação importante: o PNCP exibe contratos federais com alta consistência, mas a
        cobertura de contratos estaduais e municipais ainda é parcial, dependendo da adesão de
        cada ente ao portal. Para CNPJ de empresas que atuam exclusivamente com municípios de
        pequeno porte, parte dos contratos pode não aparecer.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático — Consulta de contratos por CNPJ
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>CNPJ consultado:</strong>{' '}
            <Link
              href="/cnpj/00394460000141"
              className="text-brand-navy dark:text-brand-blue hover:underline"
            >
              00.394.460/0001-41
            </Link>{' '}
            (Ministério da Saúde — órgão contratante de referência)
          </li>
          <li>
            <strong>Volume típico:</strong> órgãos federais de grande porte como ministérios
            acumulam centenas de contratos ativos, com valores que vão de R$ 10 mil (pequenas
            aquisições por dispensa) a R$ 1 bilhão+ (contratos de serviços contínuos e obras).
          </li>
          <li>
            <strong>Dica:</strong> ordene os resultados por data de término de vigência para
            identificar contratos prestes a vencer — esses são os que provavelmente serão
            relicitados nos próximos 90 a 180 dias.
          </li>
        </ul>
      </div>

      {/* Section 3: Buscar por órgão */}
      <h2>Como consultar contratos por órgão público</h2>

      <p>
        A busca por órgão é especialmente útil para mapear o comportamento de compra de uma
        instituição específica — com que frequência contrata, quais segmentos prioriza, quais
        fornecedores já têm relacionamento estabelecido e quais contratos estão próximos do
        vencimento.
      </p>

      <h3>Localizar o CNPJ do órgão</h3>

      <p>
        No PNCP, os órgãos são identificados pelo CNPJ da unidade gestora responsável pela
        contratação. Para localizar o CNPJ de um ministério, secretaria ou autarquia, consulte o
        SIORG (Sistema de Organização e Inovação Institucional do Governo Federal) ou a própria
        página institucional do órgão. Ministérios federais geralmente têm CNPJs diferentes para
        cada unidade orçamentária ou órgão executor.
      </p>

      <h3>Navegar pelo perfil de contratações do órgão</h3>

      <p>
        Com o CNPJ em mãos, a busca no PNCP exibirá o portfólio completo de contratos do órgão.
        Analise os padrões: quais objetos são contratados com maior frequência, qual a faixa de
        valor predominante, quantos fornecedores diferentes ganharam nos últimos 24 meses.
        Órgãos que contratam regularmente um único fornecedor por muitos anos indicam um mercado
        com alta barreira de entrada, onde a substituição exige estratégia de longo prazo. Órgãos
        com alta rotatividade de fornecedores indicam mercado mais competitivo e oportunidades
        reais para novos entrantes.
      </p>

      <p>
        Confira o perfil de contratos de um órgão de referência diretamente no SmartLic:{' '}
        <Link
          href="/contratos/orgao/00394460000141"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          contratos do Ministério da Saúde
        </Link>
        {' '}— com dados consolidados de modalidade, valor e vigência.
      </p>

      {/* CTA at ~40% depth */}
      <BlogInlineCTA slug="como-consultar-contratos-publicos-pncp" campaign="contratos" />

      {/* Section 4: Buscar por setor */}
      <h2>Como buscar contratos por setor no PNCP</h2>

      <p>
        A busca por setor (ou segmento de mercado) não é uma funcionalidade nativa do PNCP —
        o portal não possui categorização setorial dos contratos. A alternativa é combinar
        palavras-chave relevantes ao setor com os demais filtros disponíveis.
      </p>

      <h3>Estratégia de palavras-chave por segmento</h3>

      <p>
        Cada setor de atuação possui um vocabulário próprio nos editais e contratos públicos.
        Para o setor de saúde, termos como "medicamento", "material hospitalar", "insumo
        hospitalar", "equipamento médico" e "OPME" são altamente discriminativos. Para TI,
        "software", "licença", "suporte técnico", "infraestrutura de TI" e "desenvolvimento de
        sistemas" funcionam bem. Para engenharia e construção, "obra", "reforma", "manutenção
        predial", "pavimentação" e "saneamento" cobrem a maior parte das publicações.
      </p>

      <p>
        A limitação da busca textual no PNCP é que ela opera sobre o campo de objeto do contrato,
        que frequentemente usa linguagem genérica ou abreviada. Um contrato de fornecimento de
        reagentes para laboratório pode estar descrito como "material de consumo" — o que
        dificulta a identificação por palavra-chave específica. Por isso, a combinação com filtros
        por órgão (laboratórios públicos têm CNPJs identificáveis) aumenta a precisão.
      </p>

      <h3>Usar o SmartLic para busca setorial</h3>

      <p>
        O SmartLic resolve o problema da categorização setorial aplicando classificação por IA
        (GPT-4.1-nano) sobre os textos de objeto dos contratos. Em vez de depender de
        palavras-chave exatas, a plataforma identifica a qual setor cada contrato pertence com
        base no conteúdo completo do edital de origem. O resultado é uma visão consolidada por
        setor, acessível diretamente em páginas como{' '}
        <Link
          href="/contratos/saude/SP"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          contratos de saúde em SP
        </Link>{' '}
        ou na{' '}
        <Link
          href="/contratos"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          página de contratos públicos
        </Link>
        , com filtros por UF, modalidade e faixa de valor.
      </p>

      {/* Section 5: Filtros disponíveis */}
      <h2>Filtros disponíveis no PNCP para contratos</h2>

      <p>
        O PNCP oferece um conjunto de filtros que, quando combinados corretamente, reduz
        significativamente o volume de resultados e melhora a precisão da consulta.
      </p>

      <h3>Filtro por UF</h3>

      <p>
        O filtro por Unidade Federativa delimita os contratos ao estado de interesse. É o filtro
        mais básico e eficiente para empresas com atuação geográfica definida. No PNCP, contratos
        são associados à UF do órgão contratante — não necessariamente ao local de execução.
        Uma empresa de São Paulo que contrata com um órgão federal sediado no DF, por exemplo,
        aparecerá nos contratos do DF.
      </p>

      <h3>Filtro por modalidade de contratação</h3>

      <p>
        A modalidade indica o procedimento licitatório que originou o contrato. As modalidades
        previstas na Lei 14.133/2021 são: pregão (eletrônico ou presencial), concorrência,
        concurso, leilão, diálogo competitivo, dispensa de licitação e inexigibilidade. Para
        contratos de serviços contínuos e fornecimento de bens padronizados, o pregão eletrônico
        é a modalidade dominante. Dispensa e inexigibilidade concentram contratações diretas de
        menor valor ou de fornecedor exclusivo.
      </p>

      <h3>Filtro por vigência</h3>

      <p>
        O filtro por vigência permite localizar contratos com data de término dentro de um
        intervalo específico. Esse é um dos filtros mais estratégicos para empresas B2G: contratos
        com vencimento nos próximos 90 dias são candidatos a relicitação iminente. Monitorar esse
        pipeline de vencimentos permite preparar propostas com antecedência e participar do novo
        processo licitatório com informação de preço e especificação baseada no contrato anterior.
      </p>

      <h3>Filtro por valor</h3>

      <p>
        O filtro por faixa de valor está disponível na API do PNCP mas tem suporte limitado na
        interface web. Via API, é possível buscar contratos dentro de intervalos de valor
        específicos, o que é útil para segmentar oportunidades compatíveis com a capacidade de
        execução da empresa. Contratos abaixo de R$ 80 mil têm regras especiais para ME e EPP
        na Lei 14.133/2021, o que torna esse filtro especialmente relevante para pequenas
        empresas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Combinações de filtros recomendadas por objetivo
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Mapear concorrentes:</strong> CNPJ do fornecedor + todos os órgãos + últimos
            24 meses → revela portfólio completo do concorrente e órgãos com relacionamento
            estabelecido.
          </li>
          <li>
            <strong>Identificar oportunidades próximas:</strong> UF de interesse + setor +
            vigência terminando em 90 dias → pipeline de relicitações iminentes.
          </li>
          <li>
            <strong>Precificar proposta:</strong> objeto similar + UF + últimos 12 meses →
            benchmark de valor praticado para o mesmo objeto na mesma região.
          </li>
          <li>
            <strong>Qualificar órgão como cliente:</strong> CNPJ do órgão + últimos 36 meses →
            frequência de contratação, faixa de valor e histórico de aditivos.
          </li>
        </ul>
      </div>

      {/* Section 6: Como interpretar os dados do contrato */}
      <h2>Como interpretar os dados de um contrato público no PNCP</h2>

      <p>
        Acessar o contrato é apenas o primeiro passo. A análise estratégica exige entender o
        que cada campo significa e como os dados se relacionam entre si.
      </p>

      <h3>Valor inicial versus valor atual</h3>

      <p>
        O valor inicial pactuado é o valor do contrato na data de assinatura. O valor atual
        reflete os acréscimos ou supressões realizados via aditivos. A diferença entre os dois
        revela o comportamento histórico do contrato: se o valor atual é muito superior ao
        inicial, o objeto foi ampliado durante a execução — o que pode indicar má estimativa
        original ou expansão planejada do escopo. A Lei 14.133/2021 limita acréscimos a 25% do
        valor original para obras e serviços de engenharia, e a 50% para outros serviços e
        compras (art. 125).
      </p>

      <h3>Aditivos — prorrogação versus acréscimo</h3>

      <p>
        Os aditivos são alterações formais do contrato original, publicados no PNCP como
        registros vinculados. Existem dois tipos principais: aditivos de prazo (prorrogação de
        vigência) e aditivos de valor (acréscimo ou supressão quantitativa). Um contrato com
        muitos aditivos de prazo indica que o fornecedor está sendo reconduzido sucessivamente
        — o órgão é fiel ao parceiro, mas também pode indicar dificuldade de novo processo
        licitatório. Aditivos de valor frequentes indicam objeto mal dimensionado no início ou
        necessidade crescente do órgão.
      </p>

      <h3>Subcontratação</h3>

      <p>
        A subcontratação está prevista na Lei 14.133/2021 (art. 122) e permite que o contratado
        principal transfira parte da execução a terceiros, desde que autorizado em contrato e
        mantida a responsabilidade integral pelo objeto. No PNCP, a subcontratação não é
        registrada de forma estruturada — aparece apenas no texto do contrato ou do termo de
        referência. Para identificar contratos que permitem subcontratação, é necessário ler o
        instrumento contratual completo, geralmente disponível como anexo no registro do PNCP.
      </p>

      <h3>Situação do contrato</h3>

      <p>
        A situação indica o status atual do contrato. "Vigente" significa que o contrato está
        ativo e em execução. "Encerrado" indica término normal do prazo. "Rescindido" significa
        extinção antecipada — pode ter sido por inadimplência do contratado, conveniência da
        Administração ou acordo mútuo. A rescisão por inadimplência do fornecedor é um sinal
        vermelho importante para empresas que estejam avaliando esse fornecedor como parceiro
        ou analisando o histórico do órgão em termos de relacionamento contratual.
      </p>

      <h3>Vigência e data de término</h3>

      <p>
        A data de término da vigência é o dado mais estratégico para prospectores B2G. Contratos
        de serviços contínuos têm vigência máxima de 5 anos (art. 106 da Lei 14.133/2021, com
        possibilidade de prorrogação por mais 5 anos em casos específicos). Contratos de obras
        têm vigência vinculada ao prazo de execução. Um contrato de limpeza e conservação
        firmado por 12 meses, por exemplo, deve ser relicitado anualmente — o que cria uma
        janela de oportunidade recorrente e previsível para novos fornecedores.
      </p>

      {/* Section 7: Como o SmartLic automatiza */}
      <h2>Como o SmartLic automatiza a consulta de contratos públicos</h2>

      <p>
        Consultar contratos manualmente no PNCP é viável para análises pontuais. Mas quando a
        necessidade é monitorar dezenas de órgãos simultaneamente, rastrear vencimentos em
        múltiplas UFs ou construir benchmarks de preço com amostras estatisticamente relevantes,
        a busca manual se torna inviável. O SmartLic foi desenvolvido especificamente para
        resolver esse problema.
      </p>

      <h3>Datalake de contratos públicos</h3>

      <p>
        O SmartLic mantém um datalake atualizado diariamente com dados do PNCP, integrando
        contratos, contratações (editais) e atas de registro de preços em uma base única e
        consultável por setor, UF, órgão, CNPJ de fornecedor e faixa de valor. O processo de
        ingestão roda automaticamente às 2h BRT (horário de Brasília), com atualizações
        incrementais em horários intermediários, garantindo que os dados reflitam o estado atual
        do PNCP com latência máxima de 24 horas.
      </p>

      <h3>Classificação setorial por IA</h3>

      <p>
        O PNCP não possui categorização setorial nativa. O SmartLic aplica classificação
        automática por IA sobre o texto de objeto de cada contrato, mapeando para 15 setores
        predefinidos (saúde, TI, engenharia, limpeza e facilities, alimentação, entre outros).
        Isso permite navegação setorial direta — como acessar todos os contratos de saúde
        publicados em São Paulo nos últimos 12 meses, com filtros de valor e modalidade, sem precisar
        testar dezenas de combinações de palavras-chave.
      </p>

      <h3>Análise de viabilidade baseada em histórico contratual</h3>

      <p>
        Para cada oportunidade de edital identificada, o SmartLic cruza os dados com o histórico
        de contratos do órgão licitante. Um edital de R$ 2 milhões emitido por um órgão que
        historicamente contrata acima de R$ 5 milhões naquele objeto pode indicar compra
        fragmentada ou mudança de estratégia — um dado que o PNCP fornece, mas que exige
        análise manual para ser interpretado. O SmartLic apresenta esse contexto automaticamente
        no painel de análise de viabilidade.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          O que o SmartLic faz que o PNCP nao faz nativamente
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Categorização setorial:</strong> classifica contratos por setor de mercado,
            não apenas por palavra-chave do objeto.
          </li>
          <li>
            <strong>Monitoramento de vencimentos:</strong> alerta quando contratos relevantes
            estão próximos do término de vigência.
          </li>
          <li>
            <strong>Benchmark de preço:</strong> agrega valores de contratos similares para
            calcular o valor médio praticado por setor e UF.
          </li>
          <li>
            <strong>Perfil de órgão:</strong> consolida histórico de contratações por órgão,
            incluindo frequência, fornecedores recorrentes e taxas de aditamento.
          </li>
          <li>
            <strong>Busca multi-fonte:</strong> integra PNCP com Portal de Compras Públicas e
            ComprasGov em uma busca consolidada com deduplicação automática.
          </li>
        </ul>
      </div>

      {/* Section 8: Armadilhas comuns */}
      <h2>Erros comuns ao consultar contratos no PNCP e como evitá-los</h2>

      <p>
        A consulta a contratos públicos no PNCP tem armadilhas que podem comprometer a qualidade
        da análise. Conhecer os erros mais frequentes é tão importante quanto saber usar os filtros.
      </p>

      <h3>Confundir contratação com contrato</h3>

      <p>
        No PNCP, "contratação" refere-se ao processo licitatório — o edital em andamento ou
        encerrado que pode ou não ter resultado em contrato. "Contrato" é o instrumento firmado
        após a conclusão do processo. Um edital publicado não garante que haverá contrato: o
        processo pode ser fracassado, deserto ou revogado. Ao buscar inteligência de mercado
        sobre o que o governo efetivamente compra, a seção de contratos é a fonte correta —
        não a de contratações.
      </p>

      <h3>Ignorar a cobertura parcial de municípios</h3>

      <p>
        Mesmo com a obrigatoriedade da Lei 14.133/2021, muitos municípios de pequeno e médio
        porte ainda não publicam sistematicamente no PNCP. Estimar market share ou volume de
        compras de um segmento baseando-se apenas no PNCP pode subestimar significativamente
        o tamanho real do mercado municipal. Para uma visão mais completa, é necessário
        complementar com portais estaduais e sistemas regionais de compras.
      </p>

      <h3>Não verificar a data de publicação do aditivo</h3>

      <p>
        Um contrato pode aparecer como "vigente" no PNCP mas ter seu último aditivo publicado
        há dois anos. Isso não significa necessariamente que o contrato está em execução ativa —
        pode estar suspenso, em disputa judicial ou simplesmente com publicação atrasada. Sempre
        verifique a data do registro mais recente (contrato original ou aditivo) antes de
        concluir sobre a situação atual de um contrato.
      </p>

      <h3>Usar valor inicial como benchmark sem considerar aditivos</h3>

      <p>
        O valor inicial de um contrato é frequentemente inferior ao valor real pago ao final.
        Em serviços de TI, por exemplo, contratos com valor inicial de R$ 500 mil podem
        acumular acréscimos de 40% a 50% ao longo da vigência via aditivos. Para benchmarks
        de preço confiáveis, some o valor inicial com todos os acréscimos registrados nos
        aditivos. O SmartLic apresenta o valor consolidado (inicial mais aditivos) por padrão,
        evitando esse erro.
      </p>

      <h3>Buscar sem filtro de tempo</h3>

      <p>
        A API do PNCP retorna, por padrão, resultados dos últimos 10 dias. A interface web
        pode não deixar esse comportamento claro para usuários iniciantes. Ao buscar contratos
        históricos — para análise de mercado ou benchmark de preço — é fundamental definir
        explicitamente o intervalo de datas, ampliando para 12 ou 24 meses para amostras
        estatisticamente representativas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Checklist para uma consulta de contratos confiável no PNCP
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>Defina se o objetivo é buscar contratações (editais) ou contratos (instrumentos firmados)</li>
          <li>Selecione UF e órgão antes de aplicar palavras-chave para reduzir ruído</li>
          <li>Defina explicitamente o intervalo de datas para análises históricas</li>
          <li>Verifique a data do registro mais recente (contrato ou aditivo) antes de concluir sobre a situação</li>
          <li>Some valor inicial e aditivos de valor para obter o benchmark real</li>
          <li>Considere que contratos municipais podem estar ausentes ou desatualizados</li>
          <li>Para análises de setor, complemente o PNCP com portais estaduais e regionais</li>
        </ul>
      </div>

      {/* Section 9: Links internos e próximos passos */}
      <h2>Próximos passos: inteligência de contratos na prática</h2>

      <p>
        Consultar contratos públicos no PNCP é uma habilidade que se desenvolve com prática e
        com o desenvolvimento de rotinas sistemáticas de monitoramento. Os usos mais avançados
        — benchmark de preço, mapeamento de concorrência, radar de vencimentos — exigem
        consistência: uma única consulta gera um dado; uma série de consultas ao longo do
        tempo gera inteligência acionável.
      </p>

      <p>
        Para empresas que estão começando no mercado B2G, a recomendação é priorizar três
        consultas essenciais: (1) contratos dos principais concorrentes conhecidos por CNPJ,
        para entender com quem e quanto eles estão ganhando; (2) contratos dos órgãos-alvo
        da empresa nos últimos 24 meses, para mapear frequência e valor das contratações; e
        (3) contratos com vencimento nos próximos 90 dias no setor e UF de atuação, para
        construir um pipeline de oportunidades com horizonte temporal definido.
      </p>

      <p>
        Para acessar dados estruturados de contratos públicos por setor e UF diretamente, acesse
        a{' '}
        <Link
          href="/contratos"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          página de contratos públicos do SmartLic
        </Link>
        , que consolida dados do PNCP com classificação setorial por IA e filtros avançados de
        UF, modalidade e faixa de valor. Para análises de contratações (editais em andamento),
        a busca principal do SmartLic integra PNCP, Portal de Compras Públicas e ComprasGov
        em uma interface única.
      </p>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Como buscar contratos públicos por CNPJ no PNCP?</h3>
      <p>
        Para consultar contratos por CNPJ no PNCP, acesse pncp.gov.br, vá à seção "Contratos"
        e utilize o campo de busca com o CNPJ do fornecedor ou do órgão contratante. O portal
        exibe todos os contratos vinculados àquele CNPJ, incluindo objeto, valor, vigência e
        aditivos. Para análise mais aprofundada de histórico de contratos por CNPJ, ferramentas
        como o SmartLic consolidam dados do PNCP e apresentam o perfil completo de contratações
        em poucos segundos. Veja um exemplo de consulta em{' '}
        <Link
          href="/cnpj/00394460000141"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          perfil de CNPJ do Ministério da Saúde
        </Link>
        .
      </p>

      <h3>Quais informações estão disponíveis em um contrato público no PNCP?</h3>
      <p>
        Os contratos publicados no PNCP contêm, obrigatoriamente: número e objeto do contrato,
        CNPJ e razão social do contratado, órgão contratante, modalidade licitatória de origem,
        valor inicial, data de assinatura e vigência, situação atual (vigente, encerrado,
        rescindido) e eventuais aditivos (prorrogações de prazo e acréscimos de valor). A Lei
        14.133/2021 (art. 87 e 174) exige a publicação no PNCP em até 20 dias úteis após a
        assinatura.
      </p>

      <h3>É possível filtrar contratos por valor ou UF no PNCP?</h3>
      <p>
        Sim. O PNCP oferece filtros por UF (estado), órgão, modalidade licitatória, período de
        vigência e situação do contrato. O filtro por faixa de valor está disponível na API do
        portal, mas a interface web tem recursos de filtragem limitados. Para combinações
        avançadas de filtros — como contratos do setor de saúde em São Paulo com valor acima de R$ 500
        mil firmados nos últimos 12 meses — o uso da API ou de ferramentas especializadas como
        o SmartLic é mais eficiente. Explore os dados em{' '}
        <Link
          href="/contratos/saude/SP"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          contratos de saúde em São Paulo
        </Link>
        .
      </p>

      <h3>O que é um aditivo de contrato e como consultá-lo no PNCP?</h3>
      <p>
        Um aditivo (ou termo aditivo) é um instrumento jurídico que altera cláusulas de um
        contrato original — podendo ampliar o prazo de vigência, aumentar o valor (acréscimo
        quantitativo) ou alterar condições de execução. No PNCP, os aditivos são publicados
        como registros vinculados ao contrato original. Para consultá-los, abra a página do
        contrato e acesse a aba ou seção de aditivos. A Lei 14.133/2021 limita acréscimos a
        25% do valor original para obras e serviços de engenharia, e 50% para outros serviços
        e compras.
      </p>

      <h3>Como o SmartLic facilita a consulta de contratos públicos?</h3>
      <p>
        O SmartLic acessa o datalake do PNCP e consolida contratos públicos por setor, UF e
        órgão, eliminando a necessidade de buscas manuais repetitivas. A plataforma permite
        visualizar o histórico de contratos de um fornecedor ou órgão, identificar padrões de
        contratação por segmento, e monitorar aditivos e renovações em tempo real. Empresas B2G
        utilizam esses dados para qualificar leads, precificar propostas e identificar
        oportunidades de substituição de concorrentes. Acesse a{' '}
        <Link
          href="/contratos"
          className="text-brand-navy dark:text-brand-blue hover:underline"
        >
          central de contratos públicos
        </Link>{' '}
        para começar.
      </p>
    </>
  );
}
