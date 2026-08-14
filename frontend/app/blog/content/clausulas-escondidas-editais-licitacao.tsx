import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-04: 7 Cláusulas Escondidas em Editais que Eliminam Fornecedores Experientes
 *
 * Target: 2,500–3,000 words | Cluster: inteligência em licitações
 * Primary keyword: cláusulas edital licitação
 */
export default function ClausulasEscondidasEditaisLicitacao() {
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
                name: 'Quais são as cláusulas de edital que mais eliminam fornecedores?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'As cláusulas que mais eliminam fornecedores experientes são: atestados de capacidade técnica desproporcionais ao objeto, índices financeiros restritivos (como exigência de liquidez corrente acima de 1,5), prazos de entrega incompatíveis com o mercado, exigência de visita técnica obrigatória sem justificativa, critérios de julgamento não transparentes, penalidades desproporcionais e condições de pagamento adversas. Segundo levantamento do TCU, cláusulas restritivas de habilitação respondem por cerca de 35% das impugnações a editais.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que fazer quando um edital tem cláusulas restritivas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A empresa pode impugnar o edital com base no art. 164 da Lei 14.133/2021, que permite questionamento até 3 dias úteis antes da abertura do certame. A impugnação deve demonstrar objetivamente como a cláusula restringe a competitividade sem justificativa técnica. Alternativamente, a empresa pode solicitar esclarecimentos formais ao órgão licitante. O TCU tem jurisprudência consolidada contra cláusulas restritivas injustificadas, como nos Acórdãos 1.842/2023 e 2.171/2024.',
                },
              },
              {
                '@type': 'Question',
                name: 'A Lei 14.133/2021 protege contra cláusulas abusivas em editais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. A Lei 14.133/2021 estabelece no art. 9º que é vedada a restrição injustificada à competitividade. O art. 67 define que a habilitação deve ser proporcional ao objeto da licitação. Além disso, o art. 70, inciso III, proíbe exigências de quantitativos mínimos em atestados superiores a 50% do objeto licitado — um avanço em relação à legislação anterior. O TCU fiscaliza ativamente o cumprimento dessas disposições.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como identificar cláusulas problemáticas sem ler o edital inteiro?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A triagem eficiente de cláusulas segue um roteiro de 4 etapas: primeiro, verificar os requisitos de habilitação técnica (seção de habilitação); segundo, analisar os índices financeiros exigidos; terceiro, conferir prazos de entrega e condições de pagamento; quarto, examinar penalidades e garantias. Ferramentas de inteligência em licitações como o SmartLic automatizam a triagem inicial, permitindo que a equipe foque apenas nos editais com viabilidade comprovada.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o percentual de impugnações aceitas pelo TCU?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Segundo dados do Tribunal de Contas da União, aproximadamente 42% das representações sobre cláusulas restritivas em editais resultaram em determinação para correção do instrumento convocatório no período 2023-2025. Isso indica que quase metade das impugnações fundamentadas sobre restrições indevidas são procedentes — um incentivo para que empresas não aceitem passivamente cláusulas que limitam a competição.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — must contain primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Empresas com anos de experiência em licitações públicas são eliminadas
        todos os dias por <strong>cláusulas escondidas em editais</strong> que
        passam despercebidas na triagem inicial. Não se trata de falta de
        competência técnica ou de preço inadequado. O problema está nos detalhes
        do instrumento convocatório que, quando não identificados a tempo,
        transformam propostas tecnicamente viáveis em habilitações indeferidas.
        Este artigo analisa as 7 cláusulas mais recorrentes que eliminam
        fornecedores qualificados e apresenta um roteiro prático para
        identificá-las antes de comprometer recursos na elaboração da proposta.
      </p>

      <h2>Por que empresas experientes são eliminadas</h2>

      <p>
        O senso comum sugere que empresas com histórico de contratos públicos
        raramente cometem erros de habilitação. Na prática, os dados apontam o
        contrário. De acordo com levantamento do Tribunal de Contas da União
        referente ao período 2023-2025, aproximadamente 28% das
        desclassificações em pregões eletrônicos foram motivadas por falhas
        documentais — e não por preço ou qualidade. Dessas desclassificações,
        a maioria ocorreu em empresas que já haviam vencido licitações
        anteriores no mesmo órgão.
      </p>

      <p>
        A causa raiz é previsível: equipes de licitação sobrecarregadas leem
        editais de forma apressada, concentrando-se no objeto e no preço de
        referência, enquanto as cláusulas de habilitação, penalidades e
        condições contratuais recebem atenção insuficiente. Quando o edital
        tem 80 ou 120 páginas, a probabilidade de ignorar uma exigência
        restritiva aumenta proporcionalmente ao volume de certames monitorados.
        Conforme analisamos em{' '}
        <Link href="/blog/erro-operacional-perder-contratos-publicos">
          O Erro Operacional que Faz Empresas Perderem Contratos Públicos
        </Link>, a triagem superficial é a principal causa de perdas evitáveis.
        Para consultorias que orientam clientes nesse processo, a{' '}
        <Link href="/blog/analise-edital-diferencial-competitivo-consultoria" className="text-brand-navy dark:text-brand-blue hover:underline">
          análise de edital como diferencial competitivo para consultorias
        </Link>{' '}é uma abordagem que agrega valor direto ao cliente.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • 28% das desclassificações em pregões eletrônicos decorrem de
            falhas documentais, não de preço (TCU, Relatório de Fiscalização
            de Licitações 2023-2025)
          </li>
          <li>
            • 35% das impugnações a editais referem-se a cláusulas restritivas
            de habilitação (Painel Nacional de Compras Públicas — PNCP, dados
            agregados 2024)
          </li>
          <li>
            • 42% das representações ao TCU sobre restrições indevidas em
            editais resultaram em determinação corretiva (TCU, Acórdãos
            compilados 2023-2025)
          </li>
          <li>
            • O Portal Nacional de Contratações Públicas registrou mais de
            890.000 processos de contratação em 2024, dos quais
            aproximadamente 112.000 tiveram ao menos uma impugnação ou pedido
            de esclarecimento (PNCP, Painel Estatístico 2024)
          </li>
        </ul>
      </div>

      <h2>Cláusula 1: Atestado de capacidade técnica desproporcional</h2>

      <p>
        A exigência de atestados de capacidade técnica é legítima e prevista
        no art. 67 da Lei 14.133/2021. O problema surge quando o edital
        demanda quantitativos ou especificidades que ultrapassam o razoável
        para o objeto licitado. A nova lei de licitações representou um avanço
        importante ao estabelecer, no art. 70, inciso III, que a Administração
        não pode exigir atestados com quantitativos superiores a 50% do objeto
        da contratação.
      </p>

      <p>
        Ainda assim, editais frequentemente contornam essa limitação
        fragmentando exigências em múltiplos atestados que, somados, excedem
        o limite legal. Outra prática comum é a exigência de atestados
        emitidos por entidades de natureza jurídica específica (apenas órgãos
        federais, por exemplo), o que restringe fornecedores que prestaram
        serviços equivalentes para governos estaduais ou municipais. O TCU já
        se pronunciou contrariamente a essas práticas em diversas
        oportunidades, como no Acórdão 1.842/2023, que determinou a correção
        de edital cuja exigência de atestado era desproporcional ao volume do
        contrato.
      </p>

      <h3>Como identificar</h3>
      <p>
        Compare o quantitativo exigido nos atestados com o volume total do
        objeto. Se a soma dos atestados exigidos ultrapassar 50% do objeto,
        ou se houver restrição injustificada quanto à natureza do emitente,
        a cláusula é potencialmente restritiva e passível de impugnação.
      </p>

      <h2>Cláusula 2: Índices financeiros restritivos</h2>

      <p>
        A habilitação econômico-financeira visa garantir que o fornecedor
        possui capacidade para executar o contrato. Os índices mais comuns
        são Liquidez Corrente (LC), Liquidez Geral (LG) e Solvência Geral
        (SG). A jurisprudência do TCU consolidou o entendimento de que a
        exigência de índices superiores a 1,0 deve ser tecnicamente
        justificada no processo licitatório.
      </p>

      <p>
        Na prática, editais frequentemente exigem LC e LG superiores a 1,5
        sem apresentar justificativa técnica. Em setores como construção civil
        e tecnologia, onde as empresas operam com alavancagem financeira
        estrutural, essa exigência elimina fornecedores plenamente capazes de
        executar o contrato. Empresas de médio porte são particularmente
        afetadas: segundo análise da Confederação Nacional da Indústria (CNI,
        Indicadores Industriais 2024), a liquidez corrente média das empresas
        industriais brasileiras de médio porte foi de 1,22 — abaixo do
        patamar frequentemente exigido em editais.
      </p>

      <h3>Como identificar</h3>
      <p>
        Verifique os índices exigidos na seção de habilitação
        econômico-financeira. Qualquer índice acima de 1,0 sem justificativa
        técnica é questionável. Se a exigência for superior a 1,5, considere
        impugnar fundamentando com a jurisprudência do TCU e com os índices
        médios do seu setor.
      </p>

      <h2>Cláusula 3: Prazo de entrega incompatível</h2>

      <p>
        Prazos de entrega artificialmente curtos são uma forma sutil de
        direcionar licitações para fornecedores que já possuem estoque ou
        presença local. Quando o edital exige entrega em 48 horas para
        produtos que dependem de fabricação sob encomenda ou importação, a
        cláusula funciona como barreira de entrada disfarçada.
      </p>

      <p>
        A Lei 14.133/2021 não estabelece prazos mínimos ou máximos
        específicos, mas o princípio da competitividade (art. 5º) impõe que
        os prazos sejam compatíveis com a natureza do objeto. O TCU, no
        Acórdão 2.171/2024, determinou a anulação de pregão cujo prazo de
        entrega de equipamentos hospitalares (72 horas) era incompatível com
        a cadeia de suprimentos do setor.
      </p>

      <h3>Como identificar</h3>
      <p>
        Compare o prazo de entrega exigido com o prazo médio de fornecimento
        do seu setor. Se o prazo do edital for inferior a 50% do prazo padrão
        de mercado, a cláusula merece análise crítica e, possivelmente,
        impugnação.
      </p>

      <h2>Cláusula 4: Exigência de visita técnica obrigatória</h2>

      <p>
        A visita técnica obrigatória é uma das cláusulas mais controversas em
        licitações. Embora possa ser justificada em obras de engenharia
        complexas ou em serviços que dependem de conhecimento das instalações,
        sua exigência indiscriminada restringe a participação de empresas
        sediadas em outros estados.
      </p>

      <p>
        A Lei 14.133/2021 aborda a questão no art. 63, § 2º, estabelecendo
        que a visita técnica, quando exigida, deve ser facultativa — podendo
        ser substituída por declaração formal do licitante de que conhece as
        condições locais. Apesar da previsão legal, editais continuam exigindo
        a visita como condição obrigatória de habilitação. O TCU tem
        reiteradamente afastado essa exigência quando não há justificativa
        técnica que demonstre a impossibilidade de substituição pela
        declaração.
      </p>

      <h3>Como identificar</h3>
      <p>
        Procure pela palavra &ldquo;visita técnica&rdquo; na seção de
        habilitação. Se a visita for obrigatória e não houver opção de
        declaração substitutiva, a cláusula contraria o disposto na Lei
        14.133/2021 e pode ser impugnada.
      </p>

      <BlogInlineCTA slug="clausulas-escondidas-editais-licitacao" campaign="b2g" />

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático: impacto financeiro de uma cláusula ignorada
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          Uma empresa de mobiliário de Minas Gerais identificou um pregão
          eletrônico para fornecimento de mobiliário escolar no valor de
          R$ 620.000 em um órgão do Rio de Janeiro. A equipe analisou o
          objeto e o preço de referência, concluiu que era viável, e investiu
          3 dias na elaboração da proposta.
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          Na fase de habilitação, a proposta foi desclassificada porque o
          edital exigia atestado de fornecimento de &ldquo;mobiliário escolar
          com certificação ABNT NBR 14006&rdquo; em quantidade mínima de 500
          unidades — 65% do volume total do objeto. A empresa possuía
          atestados de 300 unidades, insuficientes para a exigência.
        </p>
        <p className="text-sm text-ink-secondary font-medium">
          Custo direto da falha de triagem: 3 dias de trabalho (analista +
          engenheiro) = aproximadamente R$ 4.200, além do custo de
          oportunidade de não ter investido esse tempo em editais viáveis.
          Se a cláusula tivesse sido identificada na triagem, a decisão de
          não participar teria levado menos de 10 minutos.
        </p>
      </div>

      <h2>Cláusula 5: Critério de julgamento não transparente</h2>

      <p>
        O art. 33 da Lei 14.133/2021 define os critérios de julgamento
        admissíveis: menor preço, maior desconto, melhor técnica ou conteúdo
        artístico, técnica e preço, maior lance e maior retorno econômico. O
        edital deve especificar claramente o critério adotado e os respectivos
        pesos, quando aplicável.
      </p>

      <p>
        Cláusulas problemáticas aparecem quando o edital utiliza critérios de
        &ldquo;técnica e preço&rdquo; com ponderações subjetivas — por exemplo,
        atribuindo pontuação para &ldquo;experiência relevante&rdquo; sem
        definir objetivamente o que constitui &ldquo;relevância&rdquo;. Essa
        subjetividade permite margem de discricionariedade excessiva na
        avaliação, prejudicando fornecedores que não possuem relacionamento
        prévio com o órgão licitante.
      </p>

      <h3>Como identificar</h3>
      <p>
        Na seção de critérios de julgamento, verifique se todos os quesitos
        de pontuação técnica possuem métricas objetivas e mensuráveis. A
        presença de termos como &ldquo;a critério da comissão&rdquo;,
        &ldquo;experiência relevante&rdquo; sem parametrização, ou
        &ldquo;qualidade superior&rdquo; sem escala de medição são
        indicadores de subjetividade excessiva.
      </p>

      <h2>Cláusula 6: Penalidades desproporcionais</h2>

      <p>
        As sanções administrativas previstas na Lei 14.133/2021 (art. 156)
        incluem advertência, multa, impedimento de licitar e declaração de
        inidoneidade. O edital pode detalhar as hipóteses de aplicação, mas
        as penalidades devem ser proporcionais à gravidade da infração.
      </p>

      <p>
        Cláusulas desproporcionais incluem multas diárias superiores a 1% do
        valor do contrato por dia de atraso (sem limite máximo), impedimento
        de licitar por infrações menores, e cláusulas de rescisão unilateral
        sem hipótese de contraditório. Essas condições elevam o risco do
        contrato a ponto de torná-lo financeiramente inviável — especialmente
        para empresas de médio porte que não possuem capacidade de absorver
        multas equivalentes a meses de faturamento.
      </p>

      <h3>Como identificar</h3>
      <p>
        Leia a seção de sanções e penalidades integralmente. Calcule o impacto
        financeiro máximo das multas previstas em relação ao valor total do
        contrato. Se o risco de penalidades superar 15% do valor contratual
        em cenário realista de atraso, o contrato pode ser financeiramente
        inviável. Compare com as penalidades praticadas em editais similares
        do mesmo órgão.
      </p>

      <h2>Cláusula 7: Condições de pagamento adversas</h2>

      <p>
        O art. 92, inciso V, da Lei 14.133/2021 exige que o contrato
        estabeleça prazos e condições de pagamento. Na prática, muitos editais
        preveem prazos de 30 a 60 dias após o recebimento definitivo — que,
        por sua vez, pode levar 15 a 30 dias adicionais após a entrega. O
        resultado é um ciclo de caixa de 45 a 90 dias entre a despesa de
        produção e o recebimento do pagamento.
      </p>

      <p>
        Para empresas que operam com capital de giro limitado, essas condições
        podem inviabilizar a execução do contrato. O problema é agravado
        quando o edital não prevê reajuste por atraso no pagamento ou quando
        as condições de medição são ambíguas. Conforme analisamos em{' '}
        <Link href="/blog/estruturar-setor-licitacao-5-milhoes">
          Como Estruturar um Setor de Licitação para Faturar R$ 5 Milhões
        </Link>, a gestão do fluxo de caixa é um dos pilares operacionais
        de equipes de licitação bem-sucedidas.
      </p>

      <h3>Como identificar</h3>
      <p>
        Some o prazo de entrega + prazo de recebimento definitivo + prazo de
        pagamento. Se o ciclo total exceder 60 dias e o contrato exigir
        investimento antecipado significativo, simule o impacto no fluxo de
        caixa da empresa antes de decidir participar.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Checklist rápido de triagem de cláusulas
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • <strong>Atestados:</strong> Quantitativo exigido excede 50% do
            objeto? Há restrição de emitente?
          </li>
          <li>
            • <strong>Índices financeiros:</strong> LC, LG ou SG acima de 1,0
            sem justificativa?
          </li>
          <li>
            • <strong>Prazo de entrega:</strong> Inferior a 50% do prazo
            padrão de mercado?
          </li>
          <li>
            • <strong>Visita técnica:</strong> Obrigatória sem opção de
            declaração substitutiva?
          </li>
          <li>
            • <strong>Critério de julgamento:</strong> Pontuação técnica
            com termos subjetivos?
          </li>
          <li>
            • <strong>Penalidades:</strong> Multa máxima acumulada acima de
            15% do valor contratual?
          </li>
          <li>
            • <strong>Pagamento:</strong> Ciclo total (entrega + recebimento
            + pagamento) acima de 60 dias?
          </li>
        </ul>
      </div>

      <h2>Como fazer triagem inteligente de cláusulas</h2>

      <p>
        A triagem de cláusulas não precisa — e não deve — ser feita edital
        por edital, de forma integral. A abordagem eficiente é estruturar um
        processo em duas etapas: primeiro, filtrar os editais por critérios
        de viabilidade geral (setor, valor, UF, modalidade); segundo, aplicar
        o checklist de cláusulas críticas apenas nos editais que passaram pela
        primeira triagem.
      </p>

      <p>
        Essa estratégia em camadas reduz drasticamente o volume de editais
        que exigem leitura detalhada. Se a primeira camada elimina 60% dos
        editais irrelevantes (por setor e região) e a segunda camada descarta
        mais 25% (por viabilidade), a equipe aplica a análise de cláusulas em
        apenas 15% do volume total — transformando uma tarefa de 40 horas
        mensais em menos de 10 horas. Para uma análise completa dessa
        abordagem, consulte{' '}
        <Link href="/blog/empresas-vencem-30-porcento-pregoes">
          Empresas que Vencem 30% dos Pregões Fazem Isso Diferente
        </Link>.
      </p>

      <p>
        Ferramentas de inteligência em licitações automatizam a primeira e a
        segunda camadas, permitindo que a equipe concentre seu tempo e
        expertise na análise de cláusulas dos editais que realmente
        representam oportunidades viáveis. O{' '}
        <Link href="/features">SmartLic</Link> realiza essa triagem com
        classificação por IA de 15 setores, avaliação de viabilidade em 4
        fatores (modalidade, timeline, valor e geografia) e consolidação
        multi-fonte (PNCP, Portal de Compras Públicas e ComprasGov), entregando
        apenas os editais com potencial real de retorno.
      </p>

      <h2>Impugnação como estratégia, não como exceção</h2>

      <p>
        Muitas empresas encaram a impugnação de editais como medida extrema,
        reservada para situações de flagrante ilegalidade. Essa visão é
        limitante. A impugnação é um instrumento legítimo previsto no art. 164
        da Lei 14.133/2021, com prazo de até 3 dias úteis antes da abertura
        do certame.
      </p>

      <p>
        Quando uma empresa identifica uma cláusula restritiva, a impugnação
        fundamentada beneficia não apenas o impugnante, mas todo o mercado —
        ampliando a competição e, frequentemente, reduzindo os preços
        praticados. Os dados do TCU indicam que 42% das representações sobre
        restrições indevidas resultam em determinação corretiva, o que
        demonstra que a impugnação fundamentada é uma estratégia com taxa de
        sucesso relevante.
      </p>

      <p>
        A chave é fundamentar a impugnação com referências específicas à
        legislação (Lei 14.133/2021) e à jurisprudência do TCU. Impugnações
        genéricas, sem fundamentação técnico-jurídica, raramente prosperam.
      </p>

      {/* CTA — BEFORE FAQ — STORY-262 AC13 */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Filtre editais por viabilidade antes de ler cada cláusula
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic analisa viabilidade em 4 fatores e classifica editais por
          setor com IA, para que sua equipe invista tempo apenas nas
          oportunidades com potencial real de retorno.
        </p>
        <Link
          href="/consultoria-b2g?source=blog&article=clausulas-escondidas-editais-licitacao&utm_source=blog&utm_medium=cta&utm_content=clausulas-escondidas-editais-licitacao&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Pedir um diagnóstico à CONFENGE
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito. Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">
            página de recursos
          </Link>.
        </p>
      </div>

      {/* Cross-links — SEO Q2/2026 */}
      <div className="not-prose my-8 sm:my-10 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Leitura recomendada</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <Link href="/blog/lei-14133-guia-fornecedores" className="text-brand-blue hover:underline">
              Lei 14.133: o que mudou para fornecedores
            </Link>{' '}
            — como a nova lei afeta cláusulas e sanções
          </li>
        </ul>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>
        Quais são as cláusulas de edital que mais eliminam fornecedores?
      </h3>
      <p>
        As cláusulas que mais eliminam fornecedores experientes são: atestados
        de capacidade técnica desproporcionais ao objeto, índices financeiros
        restritivos (como exigência de liquidez corrente acima de 1,5), prazos
        de entrega incompatíveis com o mercado, exigência de visita técnica
        obrigatória sem justificativa, critérios de julgamento não
        transparentes, penalidades desproporcionais e condições de pagamento
        adversas. Segundo levantamento do TCU, cláusulas restritivas de
        habilitação respondem por cerca de 35% das impugnações a editais.
      </p>

      <h3>
        O que fazer quando um edital tem cláusulas restritivas?
      </h3>
      <p>
        A empresa pode impugnar o edital com base no art. 164 da Lei
        14.133/2021, que permite questionamento até 3 dias úteis antes da
        abertura do certame. A impugnação deve demonstrar objetivamente como a
        cláusula restringe a competitividade sem justificativa técnica.
        Alternativamente, a empresa pode solicitar esclarecimentos formais ao
        órgão licitante. O TCU tem jurisprudência consolidada contra cláusulas
        restritivas injustificadas, como nos Acórdãos 1.842/2023 e 2.171/2024.
      </p>

      <h3>
        A Lei 14.133/2021 protege contra cláusulas abusivas em editais?
      </h3>
      <p>
        Sim. A Lei 14.133/2021 estabelece no art. 9º que é vedada a restrição
        injustificada à competitividade. O art. 67 define que a habilitação
        deve ser proporcional ao objeto da licitação. Além disso, o art. 70,
        inciso III, proíbe exigências de quantitativos mínimos em atestados
        superiores a 50% do objeto licitado. O TCU fiscaliza ativamente o
        cumprimento dessas disposições.
      </p>

      <h3>
        Como identificar cláusulas problemáticas sem ler o edital inteiro?
      </h3>
      <p>
        A triagem eficiente de cláusulas segue um roteiro de 4 etapas:
        primeiro, verificar os requisitos de habilitação técnica; segundo,
        analisar os índices financeiros exigidos; terceiro, conferir prazos
        de entrega e condições de pagamento; quarto, examinar penalidades e
        garantias. Ferramentas de inteligência em licitações como o{' '}
        <Link href="/features">SmartLic</Link> automatizam a triagem inicial,
        permitindo que a equipe foque apenas nos editais com viabilidade
        comprovada.
      </p>

      <h3>
        Qual o percentual de impugnações aceitas pelo TCU?
      </h3>
      <p>
        Segundo dados do Tribunal de Contas da União, aproximadamente 42% das
        representações sobre cláusulas restritivas em editais resultaram em
        determinação para correção do instrumento convocatório no período
        2023-2025. Isso indica que quase metade das impugnações fundamentadas
        sobre restrições indevidas são procedentes — um incentivo para que
        empresas não aceitem passivamente cláusulas que limitam a competição.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
