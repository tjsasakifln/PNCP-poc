import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — BOFU-04: SmartLic vs Licitanet
 *
 * Content cluster: comparação BOFU (fundo de funil)
 * Target: ~3,000 words | Primary KW: smartlic vs licitanet
 */
export default function SmartlicVsLicitanetComparacao() {
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
                name: 'Qual a diferença entre SmartLic e Licitanet?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'SmartLic é uma plataforma de inteligência em licitações que usa IA (GPT-4.1-nano) para buscar, classificar e avaliar a viabilidade de editais automaticamente. Licitanet é uma plataforma de pregão eletrônico onde órgãos públicos realizam as sessões de disputa e fornecedores enviam lances. Atuam em fases diferentes do processo licitatório: SmartLic na descoberta e triagem, Licitanet na execução da disputa.',
                },
              },
              {
                '@type': 'Question',
                name: 'SmartLic e Licitanet são concorrentes?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não diretamente. SmartLic e Licitanet resolvem problemas em fases distintas do processo licitatório. O SmartLic ajuda a encontrar e filtrar editais relevantes (antes da disputa). A Licitanet é o ambiente onde a disputa efetivamente acontece (durante o pregão). São ferramentas complementares — usar o SmartLic para triagem e depois disputar na Licitanet é um fluxo comum.',
                },
              },
              {
                '@type': 'Question',
                name: 'A Licitanet cobra por sessão de pregão?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O modelo de cobrança da Licitanet varia. Órgãos públicos contratam a plataforma para operar pregões eletrônicos (em geral sem custo para o órgão, subsidiado por taxa do fornecedor vencedor). Para fornecedores, pode haver taxa de cadastro ou percentual sobre o valor do contrato adjudicado, dependendo do edital. O SmartLic cobra mensalidade fixa (R$ 297 a R$ 397/mês) independente do número de editais analisados.',
                },
              },
              {
                '@type': 'Question',
                name: 'Posso usar SmartLic e Licitanet juntos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, e é a combinação mais lógica. O SmartLic é usado para descobrir editais relevantes, classificar por setor e avaliar viabilidade. Quando o edital é aprovado no pipeline do SmartLic, o fornecedor acessa a Licitanet (ou outra plataforma de pregão) para participar da sessão de disputa. Não há conflito técnico entre as duas plataformas.',
                },
              },
              {
                '@type': 'Question',
                name: 'A Licitanet tem classificação por inteligência artificial?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não. A Licitanet é uma plataforma de execução de pregão eletrônico — seu foco é operar a sessão de disputa, não classificar ou filtrar editais. Não possui IA para triagem, análise de viabilidade ou scoring de oportunidades. Para classificação automática de editais, plataformas de inteligência como o SmartLic utilizam modelos de linguagem (LLM) para categorização setorial.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual plataforma ajuda mais a ganhar licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Depende de onde está o gargalo. Se a empresa perde oportunidades por não encontrar editais a tempo ou por analisar editais irrelevantes, o SmartLic tem maior impacto — dados mostram 73% de redução no tempo de triagem com classificação por IA. Se a empresa encontra editais mas perde na disputa de preço ou na sessão de pregão, a competência na plataforma de disputa (Licitanet, PCP ou ComprasNet) é mais relevante.',
                },
              },
              {
                '@type': 'Question',
                name: 'A Licitanet cobre todos os estados do Brasil?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Licitanet opera em diversos estados, mas sua cobertura depende de quais órgãos públicos contratam a plataforma para operar seus pregões. Órgãos federais tendem a usar o ComprasNet/ComprasGov, enquanto estados e municípios podem usar Licitanet, PCP ou outras plataformas homologadas. O SmartLic monitora editais de todas as 27 UFs via PNCP, PCP v2 e ComprasGov v3, independentemente de onde a disputa será realizada.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        <strong>SmartLic</strong> e <strong>Licitanet</strong> aparecem
        frequentemente quando empresas B2G pesquisam ferramentas para
        licitações. Mas compará-las diretamente é como comparar um GPS com
        uma estrada — resolvem problemas em fases completamente diferentes
        do processo licitatório. Este artigo explica o que cada uma faz,
        onde cada uma é superior, e em qual cenário faz sentido usar uma,
        outra ou ambas.
      </p>

      <h2>Por que a comparação existe (e por que é enganosa)</h2>

      <p>
        O processo licitatório tem pelo menos 4 fases distintas:
        (1) descoberta de editais, (2) triagem e análise de viabilidade,
        (3) elaboração de proposta e documentação, e (4) disputa e lance.
        Ferramentas de licitação se especializam em uma ou duas dessas fases.
      </p>

      <p>
        O <strong>SmartLic</strong> se concentra nas fases 1 e 2 — encontrar
        editais relevantes em meio ao volume do PNCP e avaliar se vale a pena
        participar. Usa IA (GPT-4.1-nano) para classificação setorial
        automática e scoring de viabilidade com 4 fatores.
      </p>

      <p>
        A <strong>Licitanet</strong> atua na fase 4 — é uma plataforma de
        pregão eletrônico onde órgãos públicos realizam sessões de disputa.
        Fornecedores se cadastram, enviam propostas e dão lances em tempo
        real. A Licitanet é a infraestrutura onde o pregão acontece, não
        uma ferramenta para decidir de quais pregões participar.
      </p>

      <p>
        A confusão surge porque ambas estão no ecossistema de &ldquo;licitações
        públicas&rdquo;. Mas dizer que competem entre si é como dizer que o
        Waze compete com o Uber — um ajuda a decidir o caminho, o outro
        executa a viagem.
      </p>

      <h2>Comparação direta: SmartLic vs Licitanet</h2>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-3 font-semibold text-ink">Critério</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">SmartLic</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Licitanet</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-3 font-medium">Foco principal</td>
              <td className="py-3 px-3">Inteligência na descoberta + triagem de editais</td>
              <td className="py-3 px-3">Operação de pregão eletrônico (sala de disputa)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Fase do processo</td>
              <td className="py-3 px-3">Fases 1-2 (descoberta e análise)</td>
              <td className="py-3 px-3">Fase 4 (disputa e lance)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Classificação por IA</td>
              <td className="py-3 px-3">Sim — GPT-4.1-nano com 15 setores</td>
              <td className="py-3 px-3">Não — plataforma de execução</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Análise de viabilidade</td>
              <td className="py-3 px-3">Automática (4 fatores: modalidade, prazo, valor, geografia)</td>
              <td className="py-3 px-3">Não se aplica</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Fontes de dados</td>
              <td className="py-3 px-3">PNCP + PCP v2 + ComprasGov v3 (dedup automática)</td>
              <td className="py-3 px-3">Editais dos órgãos que usam a plataforma</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Cobertura geográfica</td>
              <td className="py-3 px-3">27 UFs simultâneas (todas as fontes)</td>
              <td className="py-3 px-3">Varia conforme órgãos contratantes</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Sala de disputa</td>
              <td className="py-3 px-3">Não — foco é pré-disputa</td>
              <td className="py-3 px-3">Sim — pregão eletrônico em tempo real</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Envio de propostas</td>
              <td className="py-3 px-3">Não</td>
              <td className="py-3 px-3">Sim — upload de documentos + proposta de preço</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Lance em tempo real</td>
              <td className="py-3 px-3">Não</td>
              <td className="py-3 px-3">Sim — sessão ao vivo com pregoeiro</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Pipeline de oportunidades</td>
              <td className="py-3 px-3">Kanban visual com drag-and-drop</td>
              <td className="py-3 px-3">Não — lista de pregões disponíveis</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Exportação Excel</td>
              <td className="py-3 px-3">Sim, com resumo executivo gerado por IA</td>
              <td className="py-3 px-3">Exportação de atas e documentos do pregão</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Modelo de preço</td>
              <td className="py-3 px-3">R$ 297-397/mês (assinatura fixa)</td>
              <td className="py-3 px-3">Taxa por sessão ou cadastro (varia por edital)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Trial gratuito</td>
              <td className="py-3 px-3">14 dias, sem cartão de crédito</td>
              <td className="py-3 px-3">Cadastro gratuito (custos na adjudicação)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Público principal</td>
              <td className="py-3 px-3">Empresas B2G + consultorias de licitação</td>
              <td className="py-3 px-3">Órgãos públicos (compradores) + fornecedores</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>Onde o SmartLic é superior</h2>

      <h3>Inteligência na descoberta de editais</h3>

      <p>
        O SmartLic não é uma plataforma de pregão — é uma plataforma de{' '}
        <strong>inteligência</strong>. Cada edital publicado no PNCP é analisado
        por três camadas: matching de palavras-chave com scoring de densidade,
        classificação semântica por IA para editais com terminologia atípica
        (zero-match), e verificação cruzada com exclusões setoriais.
      </p>

      <p>
        Na prática, um edital de &ldquo;aquisição de solução integrada para
        gerenciamento de ativos de tecnologia da informação&rdquo; é
        classificado automaticamente no setor de TI, mesmo que nenhuma
        palavra-chave padrão como &ldquo;software&rdquo; ou
        &ldquo;computador&rdquo; esteja presente. Na Licitanet, esse edital
        aparece na lista geral sem classificação — o fornecedor precisa ler
        o objeto manualmente para decidir se é relevante.
      </p>

      <p>
        Dados do programa beta do SmartLic mostram que{' '}
        <strong>11% dos editais aprovados pela IA não seriam encontrados
        por busca de palavras-chave convencional</strong>. Para quem monitora
        200 editais/mês, são ~22 oportunidades que passariam despercebidas
        em qualquer plataforma sem classificação por IA.
      </p>

      <h3>Consolidação multi-fonte com deduplicação</h3>

      <p>
        O SmartLic agrega dados de 3 fontes — PNCP, PCP v2 e ComprasGov
        v3 — em uma busca unificada, com deduplicação automática por
        prioridade (PNCP {">"} PCP {">"} ComprasGov). Um edital publicado
        simultaneamente no PNCP e no PCP aparece uma única vez nos
        resultados, com a versão mais completa.
      </p>

      <p>
        A Licitanet mostra apenas os editais dos órgãos que a contrataram
        como plataforma de pregão. Se o órgão usa o ComprasNet ou o PCP
        para realizar seus pregões, esses editais não aparecem na
        Licitanet — e vice-versa.
      </p>

      <BlogInlineCTA
        slug="smartlic-vs-licitanet-comparacao"
        campaign="guias"
        ctaMessage="Teste a classificação por IA do SmartLic — Dado público verificável."
        ctaText="Começar Trial Gratuito"
      />

      <h3>Análise de viabilidade automática</h3>

      <p>
        Cada edital no SmartLic recebe um score de viabilidade baseado em 4
        fatores ponderados: modalidade (30%), timeline/prazo (25%), valor
        estimado (25%) e proximidade geográfica (20%). Isso permite ordenar
        editais por probabilidade de sucesso{' '}
        <strong>antes de investir tempo na leitura completa</strong>.
      </p>

      <p>
        Na Licitanet, a decisão de participar é inteiramente do fornecedor.
        A plataforma lista os pregões disponíveis, mas não oferece scoring
        nem filtragem inteligente — a análise de viabilidade é manual.
      </p>

      <h3>Preço previsível</h3>

      <p>
        O SmartLic cobra mensalidade fixa: R$ 297/mês (plano anual) a
        R$ 397/mês (plano mensal). Não importa se o fornecedor analisa 10
        ou 1.000 editais por mês — o custo é o mesmo. Isso facilita o
        planejamento financeiro, especialmente para consultorias que
        gerenciam múltiplos clientes.
      </p>

      <p>
        A Licitanet tem modelo de cobrança variável. Para fornecedores,
        o custo pode incluir taxa de cadastro, percentual sobre o valor
        adjudicado, ou ambos, dependendo do contrato do órgão com a
        plataforma. O custo total depende de quantos pregões o fornecedor
        vence e do valor dos contratos.
      </p>

      <h2>Onde a Licitanet é superior</h2>

      <h3>Execução de pregão eletrônico</h3>

      <p>
        A grande força da Licitanet é ser{' '}
        <strong>a plataforma onde o pregão acontece</strong>. Sala de
        disputa em tempo real, envio de propostas, upload de documentos de
        habilitação, comunicação com o pregoeiro, registro de ata — todo
        o fluxo de execução do pregão eletrônico é operado na plataforma.
      </p>

      <p>
        O SmartLic não oferece nada equivalente. Seu escopo termina na
        decisão de go/no-go — quando o fornecedor decide participar de um
        edital, a execução da disputa acontece em outra plataforma
        (Licitanet, PCP, ComprasNet ou outra homologada pelo órgão).
      </p>

      <h3>Homologação junto a órgãos públicos</h3>

      <p>
        A Licitanet é uma plataforma homologada para operação de pregão
        eletrônico — órgãos públicos a contratam como infraestrutura
        oficial de compras. Isso significa que o fornecedor{' '}
        <strong>precisa</strong> da Licitanet quando o edital determina
        que a disputa será realizada nela. Não é opcional.
      </p>

      <p>
        O SmartLic é uma ferramenta de decisão, não de execução. Nenhum
        edital exige que o fornecedor use o SmartLic. A escolha de usar
        ou não é do fornecedor, baseada no valor que a inteligência
        automatizada traz para sua operação.
      </p>

      <h3>Interação com pregoeiro em tempo real</h3>

      <p>
        Durante a sessão de pregão, a Licitanet oferece chat com o
        pregoeiro, notificações de fase (classificação, habilitação,
        recursos), e acompanhamento de lances de outros participantes.
        Essa interação em tempo real é crítica para a estratégia de
        lance — saber quando dar o próximo lance e quando parar.
      </p>

      <p>
        O SmartLic não tem funcionalidade de acompanhamento de disputa.
        Seu valor está em garantir que o fornecedor chegue à sala de
        disputa com as melhores oportunidades selecionadas — não em
        executar a disputa em si.
      </p>

      <h3>Credenciamento e documentação de pregão</h3>

      <p>
        A Licitanet gerencia o credenciamento de fornecedores para pregões
        específicos: envio de documentos de habilitação, declarações,
        proposta comercial e técnica. Alguns órgãos aceitam documentação
        previamente cadastrada no sistema, acelerando a participação em
        múltiplos pregões.
      </p>

      <p>
        O SmartLic não gerencia documentação de habilitação. Para
        funcionalidade de gestão documental, plataformas como a{' '}
        <Link href="/blog/smartlic-vs-effecti-comparacao-2026">
          Effecti
        </Link>{' '}
        são mais adequadas.
      </p>

      <h2>Cenários de uso: quando escolher cada uma</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          SmartLic resolve quando:
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary mb-4">
          <li>✓ O gargalo é encontrar editais relevantes em meio ao volume do PNCP</li>
          <li>✓ A equipe gasta mais de 15 horas/semana buscando e triando editais</li>
          <li>✓ Atua em múltiplos setores e precisa de classificação automática</li>
          <li>✓ Monitora 3+ UFs e precisa de consolidação multi-fonte</li>
          <li>✓ Quer análise de viabilidade automática antes de investir tempo na leitura</li>
          <li>✓ É consultoria que gerencia oportunidades para múltiplos clientes</li>
        </ul>
        <p className="text-sm font-semibold text-ink mb-3">
          Licitanet é necessária quando:
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>✓ O edital determina que a disputa será realizada na Licitanet</li>
          <li>✓ O fornecedor precisa enviar proposta e dar lances em pregão eletrônico</li>
          <li>✓ Precisa interagir com pregoeiro durante a sessão de disputa</li>
          <li>✓ Quer credenciar-se antecipadamente em órgãos que usam a plataforma</li>
        </ul>
      </div>

      <h2>A combinação SmartLic + Licitanet: o fluxo completo</h2>

      <p>
        A forma mais eficiente de operar em licitações públicas é usar
        ferramentas especializadas em cada fase. O fluxo SmartLic +
        Licitanet cobre da descoberta à disputa:
      </p>

      <ol className="list-decimal pl-6 space-y-2">
        <li>
          <strong>SmartLic</strong> busca editais em 3 fontes (PNCP, PCP,
          ComprasGov), classifica por setor com IA e avalia viabilidade
          automática → analista revisa os top 10-20 da semana.
        </li>
        <li>
          Editais aprovados entram no{' '}
          <Link href="/blog/pipeline-licitacoes-funil-comercial">
            pipeline do SmartLic
          </Link>
          {' '}→ decisão de go/no-go com dados concretos de viabilidade.
        </li>
        <li>
          Editais com go cujo pregão será na Licitanet → fornecedor acessa
          a <strong>Licitanet</strong>, credencia-se e envia proposta.
        </li>
        <li>
          Na data do pregão, fornecedor participa da sessão de disputa na
          Licitanet — lances, habilitação, recursos, adjudicação.
        </li>
      </ol>

      <p>
        O custo combinado (R$ 397/mês SmartLic + taxas Licitanet por
        adjudicação) é justificável para empresas que faturam R$ 50K+
        em contratos públicos por mês. O SmartLic reduz o tempo de
        triagem em 73% (dados do beta); a Licitanet é obrigatória quando
        o órgão determina.
      </p>

      <h2>Dados exclusivos: impacto da inteligência na fase pré-disputa</h2>

      <p>
        A maioria das empresas B2G investe desproporcionalmente na fase
        de disputa (melhor preço, estratégia de lance) e subinveste na
        fase de descoberta. Dados do SmartLic entre janeiro e março de
        2026 (800.000+ publicações processadas) revelam o impacto da
        inversão dessa prioridade:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>73% menos tempo</strong> em triagem de editais
            irrelevantes — a IA classifica em milissegundos o que um
            analista leva 5-15 minutos por edital.
          </li>
          <li>
            <strong>11% de oportunidades encontradas exclusivamente
            pela IA</strong> — editais com terminologia atípica que
            nenhuma busca por palavra-chave capturaria.
          </li>
          <li>
            <strong>4,2 editais viáveis por semana</strong> (média por
            empresa beta) — versus 1,8 editais/semana antes da adoção,
            um aumento de 133% em oportunidades qualificadas.
          </li>
        </ul>
      </div>

      <p>
        Esses dados se referem à fase <strong>antes</strong> da disputa —
        a fase onde a Licitanet não atua. Uma empresa que encontra 4,2
        editais viáveis por semana em vez de 1,8 tem mais que o dobro de
        oportunidades para disputar na Licitanet (ou em qualquer outra
        plataforma de pregão).
      </p>

      <h2>
        E as outras plataformas? Effecti, PCP e ComprasNet
      </h2>

      <p>
        A Licitanet não é a única plataforma de pregão eletrônico. O
        ecossistema inclui:
      </p>

      <ul className="list-disc pl-6 space-y-2">
        <li>
          <strong>Portal de Compras Públicas (PCP):</strong> Plataforma
          gratuita para órgãos. Sem taxa de adesão para fornecedores.
          Comum em municípios de médio porte.
        </li>
        <li>
          <strong>ComprasNet / ComprasGov:</strong> Plataforma federal.
          Obrigatória para órgãos do governo federal. Maior volume de
          pregões de alto valor.
        </li>
        <li>
          <strong>
            <Link href="/blog/smartlic-vs-effecti-comparacao-2026">
              Effecti
            </Link>:
          </strong>{' '}
          Automação documental para propostas e habilitação. Atua na
          fase 3 (elaboração), entre a triagem (SmartLic) e a disputa
          (Licitanet).
        </li>
      </ul>

      <p>
        Para uma comparação completa de todas as plataformas, incluindo
        preço, cobertura e funcionalidades, veja o{' '}
        <Link href="/blog/melhores-plataformas-licitacao-2026-ranking">
          ranking de plataformas de licitação 2026
        </Link>
        .
      </p>

      <h2>Veredito honesto</h2>

      <p>
        <strong>SmartLic e Licitanet não são alternativas</strong> — são
        ferramentas para fases diferentes do processo licitatório. Comparar
        as duas é como perguntar &ldquo;GPS ou carro?&rdquo; — a resposta é
        que você precisa de ambos.
      </p>

      <p>
        <strong>Se o maior problema da sua operação B2G é encontrar
        e filtrar editais relevantes</strong> em meio ao volume diário
        do PNCP, o SmartLic resolve com IA de classificação setorial e
        viabilidade automática. É uma ferramenta de{' '}
        <strong>decisão</strong>.
      </p>

      <p>
        <strong>Se o edital que você quer disputar está na
        Licitanet</strong>, você vai precisar usar a Licitanet. É uma
        ferramenta de <strong>execução</strong> — e em muitos casos, não
        é uma escolha, mas uma exigência do edital.
      </p>

      <p>
        <strong>Para empresas que faturam R$ 100K+ em B2G por ano e
        atuam em múltiplos setores/UFs</strong>, a combinação SmartLic
        (triagem) + plataforma de pregão (disputa) + opcionalmente{' '}
        <Link href="/blog/smartlic-vs-effecti-comparacao-2026">
          Effecti
        </Link>{' '}
        (documentação) cobre o processo de ponta a ponta.
      </p>

      <p>
        E se você ainda gerencia oportunidades em{' '}
        <Link href="/blog/smartlic-vs-planilha-excel-quando-automatizar">
          planilha Excel
        </Link>
        , vale entender quando a automação da fase de descoberta passa a
        fazer sentido financeiro.
      </p>

      <h2>Perguntas frequentes</h2>

      <h3>Qual a diferença entre SmartLic e Licitanet?</h3>
      <p>
        SmartLic é plataforma de inteligência (descoberta + triagem com IA).
        Licitanet é plataforma de pregão eletrônico (sala de disputa +
        lances). Atuam em fases diferentes: SmartLic antes da disputa,
        Licitanet durante a disputa.
      </p>

      <h3>SmartLic e Licitanet são concorrentes?</h3>
      <p>
        Não diretamente. Resolvem problemas em fases distintas do processo
        licitatório. São ferramentas complementares — usar SmartLic para
        triagem e depois disputar na Licitanet é um fluxo comum.
      </p>

      <h3>A Licitanet cobra por sessão de pregão?</h3>
      <p>
        O modelo de cobrança varia. Para fornecedores, pode haver taxa de
        cadastro ou percentual sobre o valor adjudicado. O SmartLic cobra
        mensalidade fixa (R$ 297 a R$ 397/mês).
      </p>

      <h3>Posso usar SmartLic e Licitanet juntos?</h3>
      <p>
        Sim. SmartLic para descobrir e filtrar editais, Licitanet para
        participar da sessão de disputa. Não há conflito técnico. É a
        combinação mais lógica para cobrir da descoberta à adjudicação.
      </p>

      <h3>A Licitanet tem inteligência artificial?</h3>
      <p>
        Não. A Licitanet é plataforma de execução de pregão — seu foco é
        operar a sessão de disputa, não classificar editais. Para
        classificação automática, o SmartLic utiliza GPT-4.1-nano para
        categorização setorial.
      </p>

      <h3>Qual plataforma ajuda mais a ganhar licitações?</h3>
      <p>
        Depende do gargalo. Se é encontrar editais a tempo: SmartLic
        (73% menos tempo de triagem). Se é a execução da disputa:
        competência na plataforma de pregão (Licitanet, PCP ou
        ComprasNet). Idealmente, uma empresa B2G madura investe nas
        duas fases.
      </p>

      <h3>A Licitanet cobre todos os estados?</h3>
      <p>
        A cobertura depende de quais órgãos contratam a Licitanet. O
        SmartLic monitora{' '}
        <Link href="/blog/pncp-guia-completo-empresas">
          todas as 27 UFs via PNCP
        </Link>
        , independentemente de onde a disputa será realizada.
      </p>

      <h2>Fontes</h2>

      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br) —
          volume de publicações 2025-2026
        </li>
        <li>
          Lei 14.133/2021 — Nova Lei de Licitações e Contratos
          Administrativos
        </li>
        <li>
          SmartLic base de dados — dados de classificação e triagem, jan-mar
          2026 (800K+ publicações)
        </li>
        <li>
          Licitanet — funcionalidades conforme site oficial, abril/2026
        </li>
        <li>
          Programa beta SmartLic — feedback de 30+ empresas B2G, jan-mar
          2026
        </li>
      </ul>
    </>
  );
}
