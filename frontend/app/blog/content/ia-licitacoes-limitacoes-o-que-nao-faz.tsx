import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — CLUSTER-IA-03: Limitações da IA em Licitações
 *
 * Content cluster: IA em Licitações (fundo de funil)
 * Target: ~2,800 words | Primary KW: limitações IA licitações
 */
export default function IaLicitacoesLimitacoesOQueNaoFaz() {
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
                name: 'O que a IA não consegue fazer em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A IA não participa de pregão eletrônico (sessão de disputa requer interação humana em tempo real), não prevê vencedores com confiabilidade (variáveis como estratégia de lance são imprevisíveis), não analisa cláusulas jurídicas complexas com segurança (interpretação subjetiva e jurisprudência local exigem advogado), e não garante 100% de recall (7-15% dos editais relevantes podem não ser capturados). Também não substitui o conhecimento setorial do profissional.',
                },
              },
              {
                '@type': 'Question',
                name: 'A IA pode participar de um pregão eletrônico automaticamente?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não. Sessões de pregão eletrônico exigem interação humana em tempo real: envio de lances, respostas a questionamentos do pregoeiro, upload de documentos complementares, participação em fase de habilitação. A IA pode ajudar a preparar a proposta e escolher o edital certo para participar, mas a execução da disputa requer um profissional humano na plataforma.',
                },
              },
              {
                '@type': 'Question',
                name: 'A IA consegue prever o vencedor de uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não com confiabilidade. O vencedor de uma licitação depende de variáveis imprevisíveis: estratégia de lance em tempo real de outros participantes, erros de habilitação de concorrentes, questionamentos do pregoeiro durante a sessão. O que a IA pode fazer é estimar faixas de preço competitivo com base em dados históricos de contratos similares — mas não prever o resultado da disputa.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual é a taxa de acerto da IA em classificação de licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Plataformas sérias informam entre 85% e 93% de precisão na classificação setorial. O SmartLic declara 85% de precisão e 70% de recall, validados por amostragem de 15 editais por setor em 800K+ publicações. Isso significa que ~15% dos editais classificados como relevantes podem ser falsos positivos (o analista descarta rapidamente) e ~30% dos editais relevantes não são capturados automaticamente.',
                },
              },
              {
                '@type': 'Question',
                name: 'A IA substitui o analista de licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não substitui — complementa. A IA executa bem triagem volumétrica, deduplicação e classificação inicial. O analista humano é insubstituível para análise de cláusulas jurídicas complexas, decisões estratégicas (go/no-go em editais com nuances específicas do mercado local), relacionamento com pregoeiros e elaboração de propostas diferenciadas. Empresas que entendem essa divisão tiram mais valor da IA.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Transparência radical: este artigo vai explicar o que a{' '}
        <strong>inteligência artificial em licitações não consegue fazer</strong>. Em
        um mercado onde todo fornecedor de software promete milagres com &ldquo;IA&rdquo;,
        conhecer as limitações reais é uma vantagem competitiva — porque permite alocar
        recursos humanos exatamente onde a tecnologia falha. Empresas que entendem as
        limitações da IA tiram <strong>mais</strong> valor dela, não menos.
      </p>

      <h2>Limitação 1 — A IA não participa de pregão eletrônico</h2>

      <p>
        Esta é a limitação mais importante e mais frequentemente mal compreendida. Sessões
        de pregão eletrônico — no ComprasNet, PCP, Licitanet ou qualquer outra plataforma
        homologada — exigem interação humana em tempo real com o sistema e com o pregoeiro.
      </p>

      <p>
        Durante uma sessão de pregão, o fornecedor precisa: acompanhar a fase de abertura
        de propostas, decidir quando cobrir o menor lance (e por quanto), responder a
        questionamentos do pregoeiro em tempo hábil, enviar documentos complementares de
        habilitação quando solicitado, e aguardar a fase recursal. Cada etapa depende de
        julgamento humano em tempo real — adaptando-se ao comportamento dos concorrentes
        e às decisões do pregoeiro.
      </p>

      <p>
        A IA atua <em>antes</em> da sessão de pregão: encontrando o edital certo, avaliando
        se a empresa tem perfil para participar, estimando o preço competitivo com base em
        contratos históricos, e organizando o pipeline de oportunidades. Quando a sessão
        começa, o controle passa para o profissional humano.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Onde a IA atua × onde o humano é insubstituível
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>IA faz bem:</strong> Descoberta de editais, classificação setorial, análise de viabilidade, deduplicação multi-fonte, alertas de prazo</li>
          <li><strong>Humano é necessário:</strong> Sessão de pregão ao vivo, lances em tempo real, habilitação, recursos, estratégia de preço final</li>
          <li><strong>IA apoia, humano decide:</strong> Análise de cláusulas, elaboração de proposta técnica, go/no-go em editais complexos</li>
        </ul>
      </div>

      <p>
        Isso não diminui o valor da IA — pelo contrário. Ao automatizar a fase de
        descoberta e triagem, a IA libera o analista para se concentrar no que realmente
        importa na sessão de pregão: estratégia de preço e decisões táticas de lance.
        Um analista que gasta 3 horas por dia varrendo o PNCP chega à sessão de pregão
        cansado e com menos tempo para preparar a estratégia de lance. Um analista que
        delegou a triagem à IA chega com foco total.
      </p>

      <h2>Limitação 2 — A IA não prevê o vencedor de uma licitação</h2>

      <p>
        Algumas plataformas prometem &ldquo;previsão de vencedores&rdquo; com base em
        dados históricos. É uma promessa enganosa. O vencedor de um pregão eletrônico
        depende de variáveis que são fundamentalmente imprevisíveis no momento anterior
        à sessão:
      </p>

      <ul className="list-disc pl-6 space-y-2">
        <li>
          <strong>Estratégia de lance em tempo real:</strong> Até que ponto um concorrente
          está disposto a baixar o preço? Ele tem caixa para aguentar uma guerra de
          lances? Essa informação não existe em nenhuma base de dados histórica.
        </li>
        <li>
          <strong>Habilitação dos concorrentes:</strong> Um concorrente pode ser o menor
          lance e ser inabilitado por documentação faltante. Isso inverte completamente
          o resultado esperado.
        </li>
        <li>
          <strong>Interpretação do pregoeiro:</strong> Decisões sobre aceitabilidade de
          propostas, critérios de desempate e fase recursal têm componente subjetivo
          que nenhum modelo consegue prever com confiabilidade.
        </li>
        <li>
          <strong>Condições de mercado no dia:</strong> Flutuação de preço de insumos,
          disponibilidade logística, decisões de última hora de participar ou não.
        </li>
      </ul>

      <p>
        O que a IA <em>consegue</em> fazer é estimar faixas de preço competitivo com base
        em contratos históricos similares. O SmartLic analisa contratos adjudicados no
        PNCP para estimar o P50 (mediana) e P90 (percentil 90) de preços em contratos
        com objeto, UF e modalidade semelhantes. Isso não prevê o vencedor — mas orienta
        a formação de preço de proposta.
      </p>

      <h2>Limitação 3 — A IA não analisa cláusulas jurídicas complexas com confiabilidade</h2>

      <p>
        Esta é a limitação mais crítica do ponto de vista de risco empresarial. Editais
        de licitação frequentemente contêm cláusulas que podem ser armadilhas para
        fornecedores despreparados: exigências de habilitação desproporcional, critérios
        de julgamento subjetivos, cláusulas de reajuste desfavoráveis, penalidades
        assimétricas.
      </p>

      <p>
        A IA consegue flagrar termos suspeitos — a plataforma pode identificar cláusulas
        que se desviam do padrão da Lei 14.133/2021 ou que diferem de contratos anteriores
        do mesmo órgão. Para isso, veja o artigo sobre{' '}
        <Link href="/blog/clausulas-escondidas-editais-licitacao">
          cláusulas escondidas em editais
        </Link>
        . Mas interpretar o <em>impacto</em> de uma cláusula no contexto específico da
        empresa — considerando jurisprudência local, histórico do órgão, e estrutura
        contratual da empresa — requer um advogado especializado.
      </p>

      <p>
        O risco de confiar exclusivamente em IA para análise jurídica é real: uma cláusula
        de penalidade de 30% do valor do contrato por descumprimento parcial pode passar
        despercebida em uma análise automatizada e representar risco existencial para
        uma empresa pequena. A IA sinaliza — o advogado decide.
      </p>

      <BlogInlineCTA
        slug="ia-licitacoes-limitacoes-o-que-nao-faz"
        campaign="guias"
        ctaMessage="Teste triagem e viabilidade automática — Dado público verificável."
        ctaText="Começar Trial Gratuito"
      />

      <h2>Limitação 4 — A IA não garante 100% de recall</h2>

      <p>
        Recall — a capacidade de encontrar todos os editais relevantes — é a limitação
        mais honesta e mais importante de declarar. O SmartLic declara 70% de recall:
        isso significa que 30% dos editais que seriam relevantes para o usuário podem
        não ser capturados automaticamente pela classificação por IA.
      </p>

      <p>
        Por que isso acontece? O setor público usa uma variedade extraordinária de
        terminologias para o mesmo produto ou serviço. Um edital de &ldquo;aquisição
        de solução de segurança cibernética para proteção de infraestrutura crítica&rdquo;
        e outro de &ldquo;contratação de serviço de monitoramento e resposta a incidentes
        de segurança da informação&rdquo; são o mesmo tipo de contrato para uma empresa
        de TI — mas podem usar vocabulários completamente diferentes das palavras-chave
        cadastradas.
      </p>

      <p>
        O SmartLic ataca este problema com duas camadas: primeiro, matching de palavras-chave
        com scoring de densidade; segundo, classificação por LLM (GPT-4.1-nano) para
        editais com zero correspondência de palavras-chave — o que o sistema chama de
        &ldquo;zero-match classification&rdquo;. Dados do beta mostram que 11% dos editais
        aprovados pela IA não seriam encontrados por busca de palavras-chave convencional.
      </p>

      <p>
        Mas mesmo com LLM, editais com terminologia extremamente atípica ou em setores
        de nicho muito específico podem escapar. A solução prática: complementar a
        triagem automática com uma revisão manual quinzenal do PNCP para editais do
        seu nicho mais específico — usando o tempo liberado pela IA para fazer essa
        revisão de forma mais eficiente.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          O que 85% de precisão e 70% de recall significa na prática
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>100 editais apresentados pela IA como relevantes:</strong> 85 são
            realmente relevantes; 15 são falsos positivos (descartados em segundos pelo analista)
          </li>
          <li>
            <strong>200 editais relevantes no total:</strong> A IA captura 140 (70%);
            60 precisam de revisão complementar
          </li>
          <li>
            <strong>Comparação com triagem manual (100%):</strong> 20h de analista
            para revisar todos os 200, sem filtro de qualidade
          </li>
          <li>
            <strong>Com IA (85%/70%):</strong> 5,4h para revisar os 100 apresentados
            pela IA + revisão pontual dos 60 restantes — total: ~8h, 60% menos tempo
          </li>
        </ul>
      </div>

      <p>
        O ponto crucial: mesmo com 30% de recall perdido, o tempo economizado com a
        triagem automática dos 70% capturados é muito maior do que o tempo necessário
        para cobrir o gap manualmente. O analista usa o tempo liberado para fazer
        a revisão pontual do que a IA não captura — com foco, não com exaustão.
      </p>

      <p>
        Para entender como a precisão da IA é medida e o que esses números significam
        em diferentes contextos setoriais, veja o artigo sobre{' '}
        <Link href="/blog/precisao-ia-licitacoes-taxa-acerto">
          precisão da IA em licitações
        </Link>
        .
      </p>

      <h2>Limitação 5 — A IA não substitui a experiência setorial</h2>

      <p>
        Conhecimento de mercado — quem são os concorrentes dominantes em cada UF, quais
        órgãos têm histórico de impugnar editais, quais preços de referência de mercado
        estão desatualizados nos sistemas do governo, quais fornecedores têm reputação
        problemática — é um ativo que só se constrói com anos de atuação no setor.
      </p>

      <p>
        A IA classifica editais com base em características textuais e dados históricos.
        Ela não sabe que um determinado órgão municipal tem histórico de cancelar licitações
        na fase de habilitação por razões políticas. Não sabe que um concorrente específico
        pratica dumping em contratos de baixo valor para construir relacionamento com o
        órgão e depois vencer os contratos de alto valor. Não sabe que o preço de
        referência de um contrato de TI em determinada UF está 40% acima do mercado
        porque foi estimado há 3 anos.
      </p>

      <p>
        Esse conhecimento tácito — que profissionais experientes de licitação acumulam ao
        longo de anos — é o que transforma uma boa análise de viabilidade em uma decisão
        estratégica superior. A IA fornece os dados; o profissional fornece o contexto.
      </p>

      <p>
        Para aprofundar como a IA e a experiência humana se complementam no processo de
        consultoria, veja o artigo sobre{' '}
        <Link href="/blog/inteligencia-artificial-consultoria-licitacao-2026">
          inteligência artificial na consultoria de licitações
        </Link>
        .
      </p>

      <h2>Por que entender as limitações é uma vantagem competitiva</h2>

      <p>
        Aqui está a percepção contraintuitiva central deste artigo: empresas que entendem
        as limitações da IA tiram <strong>mais</strong> valor dela — não menos.
      </p>

      <p>
        A razão é simples. Uma empresa que acredita que a IA &ldquo;faz tudo&rdquo; vai
        delegar decisões que não deveriam ser delegadas (análise jurídica de cláusulas de
        risco, estratégia de preço em pregões competitivos) e negligenciar atividades
        humanas críticas. O resultado: propostas mal estruturadas, editais com cláusulas
        problemáticas aceitas sem revisão, estratégias de lance improvisadas.
      </p>

      <p>
        Uma empresa que conhece as limitações da IA faz exatamente o contrário: delega
        para a IA o que ela faz bem (triagem volumétrica, classificação setorial,
        deduplicação, alertas de prazo) e aloca analistas nas tarefas onde o julgamento
        humano é insubstituível (análise jurídica, estratégia de lance, relacionamento
        com pregoeiros, elaboração de propostas diferenciadas).
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Divisão ótima de trabalho: IA × analista humano
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>IA processa:</strong> 800K+ publicações/mês — tarefa impossível para humanos no mesmo tempo
          </li>
          <li>
            <strong>Analista foca em:</strong> os top 10-20 editais mais viáveis identificados pela IA por semana
          </li>
          <li>
            <strong>Resultado:</strong> 133% mais oportunidades qualificadas/semana (dados beta SmartLic) com o mesmo time
          </li>
          <li>
            <strong>Tempo liberado:</strong> 73% menos horas em triagem = analista investe em análise jurídica e estratégia de proposta
          </li>
        </ul>
      </div>

      <p>
        O dado que ilustra isso com precisão: empresas beta do SmartLic que passaram a
        usar IA para triagem não apenas encontraram mais editais — melhoraram a qualidade
        de suas propostas porque os analistas tinham mais tempo para dedicar a cada
        proposta. Menos editais analisados por impulso, mais editais analisados com
        profundidade estratégica.
      </p>

      <p>
        Para calcular o ROI dessa divisão de trabalho para o porte específico da sua
        empresa, veja o artigo sobre{' '}
        <Link href="/blog/roi-ia-licitacoes-calculadora-retorno">
          ROI de inteligência artificial em licitações
        </Link>
        .
      </p>

      <h2>O que a IA FAZ bem — contraponto</h2>

      <p>
        Para equilibrar o diagnóstico, aqui está o que a IA executa com desempenho
        superior ao humano no contexto de licitações:
      </p>

      <ul className="list-disc pl-6 space-y-2">
        <li>
          <strong>Triagem volumétrica em tempo real:</strong> Processar 800K+ publicações
          por trimestre em 27 UFs e 6 modalidades — impossível para qualquer equipe humana.
        </li>
        <li>
          <strong>Classificação setorial consistente:</strong> Sem cansaço, sem viés de
          humor, sem pressa de sexta-feira à tarde. A IA classifica o 800.000.º edital
          com a mesma atenção do primeiro.
        </li>
        <li>
          <strong>Deduplicação entre fontes:</strong> Um edital publicado no PNCP e no
          PCP aparece uma vez nos resultados — automaticamente, sem checagem manual.
        </li>
        <li>
          <strong>Alertas de prazo crítico:</strong> Identificação imediata de editais
          com prazo de participação em menos de 5 dias úteis — que a triagem manual
          diária frequentemente descobre tarde.
        </li>
        <li>
          <strong>Análise de viabilidade ponderada:</strong> Scoring automático de 4
          fatores (modalidade, prazo, valor, geografia) antes do analista investir
          tempo de leitura no edital.
        </li>
        <li>
          <strong>Descoberta zero-match:</strong> Editais com terminologia atípica
          que nenhuma busca por palavra-chave encontraria — 11% dos editais aprovados
          no beta SmartLic vieram desta camada.
        </li>
      </ul>

      <p>
        Para uma explicação detalhada dos mecanismos de classificação — como a IA decide
        entre keyword matching e LLM zero-match, e como o viability score é calculado —,
        veja o artigo completo sobre{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona">
          como a inteligência artificial funciona em licitações
        </Link>
        .
      </p>

      <h2>Perguntas frequentes</h2>

      <h3>O que a IA não consegue fazer em licitações?</h3>
      <p>
        Cinco limitações principais: (1) não participa de pregão eletrônico — disputa
        exige humano em tempo real; (2) não prevê vencedores com confiabilidade — variáveis
        como estratégia de lance são imprevisíveis; (3) não analisa cláusulas jurídicas
        complexas com segurança — requer advogado especializado; (4) não garante 100%
        de recall — 30% dos editais relevantes podem escapar; (5) não substitui
        experiência setorial acumulada.
      </p>

      <h3>A IA pode participar de um pregão eletrônico automaticamente?</h3>
      <p>
        Não. Sessões de pregão exigem interação humana em tempo real: lances, respostas
        ao pregoeiro, habilitação, recursos. A IA ajuda na preparação e descoberta —
        a execução da disputa requer um profissional humano na plataforma.
      </p>

      <h3>A IA consegue prever o vencedor de uma licitação?</h3>
      <p>
        Não com confiabilidade. O resultado depende de variáveis imprevisíveis: estratégia
        de lance de concorrentes, erros de habilitação, decisões do pregoeiro. O que a
        IA faz é estimar faixas de preço competitivo com base em contratos históricos
        — útil para formação de preço, não para prever resultado.
      </p>

      <h3>Qual é a taxa de acerto da IA na classificação de licitações?</h3>
      <p>
        O SmartLic declara 85% de precisão e 70% de recall, validados por amostragem em
        800K+ publicações. Isso significa 15% de falsos positivos (analista descarta
        rapidamente) e 30% de editais relevantes que precisam de revisão complementar.
        Plataformas que afirmam 100% de acerto não têm sustentação técnica.
      </p>

      <h3>A IA substitui o analista de licitações?</h3>
      <p>
        Não — complementa. A IA executa triagem volumétrica, classificação e análise
        de viabilidade automática. O analista é insubstituível para cláusulas jurídicas,
        estratégia de lance, elaboração de propostas diferenciadas e decisões que exigem
        conhecimento setorial acumulado. Empresas que entendem essa divisão tiram mais
        valor da IA.
      </p>

      <h2>Fontes</h2>

      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br) —
          dados de publicações e contratos 2025-2026
        </li>
        <li>
          SmartLic base de dados — dados de classificação e zero-match, jan-mar 2026
          (800K+ publicações processadas)
        </li>
        <li>
          Programa beta SmartLic — 30+ empresas B2G, jan-mar 2026: 73% redução
          em triagem, 11% editais via zero-match, 133% aumento em oportunidades qualificadas
        </li>
        <li>
          Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos,
          modalidades e prazos
        </li>
        <li>
          Tribunal de Contas da União (TCU) — jurisprudência em habilitação e
          cláusulas de edital, acórdãos 2024-2025
        </li>
        <li>
          OpenAI — GPT-4.1-nano documentation — capabilities and limitations for
          classification tasks, 2026
        </li>
      </ul>
    </>
  );
}
