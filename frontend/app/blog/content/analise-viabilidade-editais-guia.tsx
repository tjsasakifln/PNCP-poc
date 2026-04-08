import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * T5: Análise de Viabilidade de Editais: O que Considerar antes de Participar
 *
 * Target: 3,000+ words | Cluster: guias transversais
 * Primary keyword: análise viabilidade editais
 */
export default function AnaliseViabilidadeEditaisGuia() {
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
                name: 'O que é análise de viabilidade de edital?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Análise de viabilidade de edital é o processo de avaliar, antes de investir na elaboração de proposta, se uma licitação é compatível com o perfil, capacidade e estratégia da empresa. A análise considera fatores como modalidade, prazo, valor estimado, localização geográfica, requisitos de habilitação e concorrência esperada. O objetivo é evitar que a empresa desperdice recursos em editais com baixa probabilidade de adjudicação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais os 4 fatores de viabilidade?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os quatro fatores principais são: Modalidade (peso 30%) — avalia se a modalidade favorece o perfil da empresa; Timeline (peso 25%) — verifica se o prazo entre publicação e abertura é suficiente; Valor estimado (peso 25%) — analisa se o valor está na faixa de competitividade da empresa; e Geografia (peso 20%) — considera custos logísticos e viabilidade de execução no local.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como calcular o custo real de participar de uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo real inclui: horas de analista para leitura e análise do edital (4 a 16 horas dependendo da complexidade), elaboração de proposta comercial e técnica (8 a 40 horas), obtenção e atualização de certidões e atestados, custos de garantia (quando exigida, de 1% a 5% do valor da proposta), eventual visita técnica (passagem, hospedagem, diárias) e custos administrativos (autenticações, reconhecimento de firma, envio de documentação). Para pregões simples, o custo total fica entre R$ 1.500 e R$ 5.000. Para concorrências com proposta técnica, pode ultrapassar R$ 15.000.',
                },
              },
              {
                '@type': 'Question',
                name: 'Devo participar de toda licitação do meu setor?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não. Participar de toda licitação do setor é um dos erros mais comuns e custosos. Empresas com taxa de adjudicação saudável (acima de 15%) são seletivas — participam de 20% a 30% dos editais que encontram. A seletividade permite concentrar recursos nos editais com maior probabilidade de vitória, elaborar propostas mais competitivas e manter a equipe focada em qualidade, não volume.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível automatizar a análise de viabilidade?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. Ferramentas de inteligência em licitações com IA avaliam automaticamente os 4 fatores de viabilidade para cada edital. O sistema pondera modalidade, timeline, valor e geografia com pesos configuráveis e gera um score composto que indica a viabilidade da participação. A automação não substitui a decisão final humana, mas elimina a análise repetitiva de editais claramente inviáveis — que representam 60% a 70% do volume total.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a taxa de adjudicação saudável?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A taxa de adjudicação (percentual de licitações vencidas em relação às disputadas) varia por setor e porte da empresa. Para empresas de médio porte em setores competitivos como TI e facilities, uma taxa entre 15% e 25% é considerada saudável. Para empresas especializadas em nichos com menor concorrência, a taxa pode ultrapassar 30%. Taxas abaixo de 10% indicam que a empresa está participando de editais inadequados ao seu perfil — e a análise de viabilidade é o caminho para corrigir isso.',
                },
              },
            ],
          }),
        }}
      />

      {/* HowTo JSON-LD — 6 steps */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'HowTo',
            name: 'Como Fazer Análise de Viabilidade de Editais',
            description:
              'Guia prático com 6 etapas para avaliar a viabilidade de participação em uma licitação pública antes de investir na elaboração de proposta.',
            totalTime: 'PT30M',
            step: [
              {
                '@type': 'HowToStep',
                position: 1,
                name: 'Verificar a modalidade e suas implicações',
                text: 'Identifique a modalidade da licitação (pregão eletrônico, concorrência, tomada de preços, diálogo competitivo). Pregão eletrônico exige menor investimento na proposta e tem processo mais rápido. Concorrência exige proposta técnica detalhada e maior investimento. Avalie se a modalidade é compatível com a capacidade e o histórico de participação da sua empresa.',
              },
              {
                '@type': 'HowToStep',
                position: 2,
                name: 'Avaliar o prazo entre publicação e abertura',
                text: 'Calcule os dias úteis entre a data atual e a data de abertura do edital. Mínimo viável para pregão de bens: 5 a 7 dias úteis. Para serviços com proposta técnica: 10 a 15 dias úteis. Para obras e engenharia: 15 a 20 dias úteis. Se o prazo for insuficiente para preparar uma proposta competitiva, descarte o edital.',
              },
              {
                '@type': 'HowToStep',
                position: 3,
                name: 'Analisar o valor estimado vs capacidade da empresa',
                text: 'Compare o valor estimado do edital com a faixa de valor onde sua empresa é mais competitiva. Verifique se possui atestados de capacidade técnica compatíveis com o volume (tipicamente 50% do valor total). Avalie se a margem esperada justifica o custo de participação. Editais muito acima ou abaixo da faixa ideal devem ser descartados.',
              },
              {
                '@type': 'HowToStep',
                position: 4,
                name: 'Avaliar a localização geográfica e logística',
                text: 'Identifique o local de execução do contrato. Calcule custos de mobilização (transporte, hospedagem, equipe). Para serviços presenciais, avalie se a distância permite supervisão eficiente. Para fornecimento de bens, estime o custo de frete como percentual do valor total. Empresas com atuação regional devem priorizar editais na sua área de abrangência.',
              },
              {
                '@type': 'HowToStep',
                position: 5,
                name: 'Verificar requisitos de habilitação vs documentação disponível',
                text: 'Liste todos os requisitos de habilitação do edital: certidões (CND, CRF, CNDT), atestados de capacidade técnica (quantidades e valores mínimos), índices financeiros (liquidez, endividamento), garantia de proposta (se exigida), registros profissionais (CREA, CRM, CRA). Compare com a documentação disponível da empresa. Itens pendentes com prazo de obtenção superior ao prazo do edital são eliminatórios.',
              },
              {
                '@type': 'HowToStep',
                position: 6,
                name: 'Calcular custo de participação vs probabilidade de vitória',
                text: 'Some todos os custos de participação: horas-analista, elaboração de proposta, certidões, garantia, visita técnica. Estime a probabilidade de adjudicação com base no histórico de participação em editais semelhantes. Se o custo de participação multiplicado pelo inverso da probabilidade for maior que a margem esperada do contrato, a licitação não é viável economicamente.',
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: análise viabilidade editais */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A decisão mais importante no processo de licitações públicas não é como
        participar — é <strong>quais licitações disputar</strong>. A{' '}
        <strong>análise de viabilidade de editais</strong> é o processo que separa
        empresas lucrativas no mercado B2G de empresas que queimam caixa
        perseguindo oportunidades inadequadas. Uma empresa que participa de 50
        licitações por ano com taxa de adjudicação de 5% está gastando recursos
        em 47 propostas que não geraram receita. Uma empresa que participa de 20
        licitações selecionadas com taxa de adjudicação de 25% gera o mesmo
        resultado com menos da metade do investimento.
      </p>

      <p>
        Este guia apresenta um framework completo de análise de viabilidade com
        quatro fatores ponderados, exemplos práticos e critérios objetivos para
        a decisão go/no-go. O conteúdo é aplicável a empresas de qualquer setor
        e porte que participam de compras públicas.
      </p>

      {/* Section 2 */}
      <h2>O custo real de participar de uma licitação</h2>

      <p>
        A maioria das empresas subestima o custo de participar de uma licitação.
        O cálculo intuitivo considera apenas o preço da proposta, mas o custo
        real inclui todos os recursos investidos desde a identificação do edital
        até o resultado final.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Custo real por tipo de licitação (estimativa por proposta)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Pregão eletrônico — bens padronizados:</strong> R$ 1.500 a
            R$ 3.000. Inclui: 4 a 8 horas de análise do edital, 4 a 8 horas de
            elaboração de proposta, atualização de certidões (se necessário),
            participação na sessão de lances (2 a 4 horas).
          </li>
          <li>
            <strong>Pregão eletrônico — serviços contínuos:</strong> R$ 3.000 a
            R$ 8.000. Inclui: 8 a 16 horas de análise (edital + termo de
            referência), elaboração de planilha de custos com BDI, composição de
            equipe mínima, cálculo de encargos trabalhistas, participação na
            sessão.
          </li>
          <li>
            <strong>Concorrência com proposta técnica:</strong> R$ 8.000 a
            R$ 15.000. Inclui: 16 a 40 horas de análise e elaboração de proposta
            técnica, mobilização de equipe técnica (currículos, atestados
            individuais), eventual visita técnica ao local (R$ 1.500 a R$ 3.000),
            garantia de proposta (1% a 5% do valor).
          </li>
          <li>
            <strong>Obras e engenharia:</strong> R$ 10.000 a R$ 25.000+. Inclui:
            projeto básico, orçamento detalhado com composição de custos
            unitários, cronograma físico-financeiro, BDI discriminado, ART/RRT,
            visita técnica obrigatória, garantia de proposta.
          </li>
        </ul>
      </div>

      <p>
        Com esses números em perspectiva, uma empresa que participa de 30 pregões
        de serviços por ano com taxa de adjudicação de 10% investe entre R$ 90 mil
        e R$ 240 mil em propostas — das quais 27 não geram retorno. Se a mesma
        empresa melhorar a seletividade e participar de 15 pregões com taxa de
        adjudicação de 20%, o investimento cai para R$ 45 mil a R$ 120 mil com o
        mesmo número de contratos vencidos. A análise de viabilidade é o mecanismo
        que viabiliza essa transição.
      </p>

      <p>
        Para uma análise detalhada do impacto financeiro, veja{' '}
        <Link href="/blog/custo-invisivel-disputar-pregoes-errados" className="text-brand-navy dark:text-brand-blue hover:underline">
          o custo invisível de disputar pregões errados
        </Link>.
      </p>

      {/* Section 3 -- Fator 1 */}
      <h2>Fator 1: Modalidade — como cada modalidade afeta a viabilidade</h2>

      <p>
        A modalidade da licitação é o fator com maior peso na análise de viabilidade
        (30%) porque determina o nível de investimento necessário na proposta, o
        grau de concorrência esperado e a dinâmica do processo.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Impacto da modalidade na viabilidade
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Pregão eletrônico (modalidades 5/6):</strong> Investimento
            baixo a médio. Concorrência alta (5 a 30+ participantes). Critério:
            menor preço ou maior desconto. Prazo mínimo legal: 8 dias úteis.
            Melhor para: empresas com boa estrutura de custos e agilidade
            operacional.
          </li>
          <li>
            <strong>Concorrência (modalidade 4):</strong> Investimento alto.
            Concorrência moderada (3 a 10 participantes). Critério: menor preço
            ou técnica e preço. Prazo mínimo legal: 35 dias corridos (Lei
            14.133). Melhor para: empresas com equipe técnica qualificada e
            atestados robustos.
          </li>
          <li>
            <strong>Diálogo competitivo (modalidade 7):</strong> Investimento
            muito alto. Concorrência baixa (3 a 5 participantes). Envolve fases
            de diálogo prévio com o órgão. Melhor para: empresas com expertise
            técnica diferenciada em soluções complexas.
          </li>
          <li>
            <strong>Inexigibilidade (modalidade 8):</strong> Investimento baixo.
            Sem concorrência (contratação direta). Exige comprovação de
            exclusividade ou notória especialização. Melhor para: empresas com
            produtos ou serviços exclusivos devidamente documentados.
          </li>
        </ul>
      </div>

      <p>
        A regra prática: se a empresa tem histórico de participação e taxa de
        adjudicação para determinada modalidade, use esse dado como referência. Se
        a taxa de adjudicação em concorrências é consistentemente abaixo de 10%,
        considere concentrar esforço em pregões — onde o investimento por proposta
        é menor e o volume de oportunidades é maior. A exceção são contratos de
        alto valor onde a margem justifica o investimento mesmo com probabilidade
        menor.
      </p>

      <p>
        Para entender as modalidades em detalhe, consulte{' '}
        <Link href="/blog/como-participar-primeira-licitacao-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          o guia completo de como participar da primeira licitação em 2026
        </Link>.
      </p>

      {/* Section 4 -- Fator 2 */}
      <h2>Fator 2: Prazo (timeline) — o tempo é eliminatório</h2>

      <p>
        O prazo entre a data de publicação (ou a data em que a empresa identifica o
        edital) e a data de abertura é um fator eliminatório, não apenas ponderável.
        Se não há tempo suficiente para preparar uma proposta competitiva, o edital
        deve ser descartado independentemente dos outros fatores.
      </p>

      <h3>Prazos mínimos viáveis por tipo de contratação</h3>

      <p>
        <strong>Bens padronizados (pregão):</strong> 5 a 7 dias úteis. A empresa
        precisa verificar estoque ou prazo de entrega do fornecedor, atualizar
        preços, preparar a proposta e organizar documentação de habilitação. Se a
        documentação estiver atualizada (certidões válidas, atestados organizados),
        é possível trabalhar com 5 dias. Com certidões vencidas, 7 dias é o mínimo.
      </p>

      <p>
        <strong>Serviços com planilha de custos:</strong> 10 a 15 dias úteis. A
        elaboração da planilha de custos com BDI, composição de equipe, cálculo de
        encargos trabalhistas e insumos exige tempo de pesquisa e validação. Erros
        na planilha resultam em desclassificação ou margens negativas. Não comprima
        esse prazo.
      </p>

      <p>
        <strong>Obras e engenharia:</strong> 15 a 20 dias úteis. Orçamento
        detalhado com composição de custos unitários (SINAPI/SICRO), cronograma
        físico-financeiro, visita técnica (quando obrigatória) e ART/RRT de
        responsabilidade técnica. Editais de obras com menos de 15 dias úteis
        até a abertura são viáveis apenas para empresas que já têm projetos
        semelhantes orçados.
      </p>

      <h3>O efeito da descoberta tardia</h3>

      <p>
        Um edital publicado há 10 dias com abertura em 5 dias tem o mesmo prazo
        legal que um edital publicado há 1 dia com abertura em 14 dias. Mas para
        a empresa, a situação é completamente diferente. A descoberta tardia —
        causada por monitoramento infrequente dos portais — transforma editais
        viáveis em editais inviáveis. O monitoramento automatizado com alertas
        diários elimina esse problema. Veja como a IA pode ajudar em{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-navy dark:text-brand-blue hover:underline">
          inteligência artificial em licitações: como funciona na prática
        </Link>.
      </p>

      <h3>Prazo de execução como fator de viabilidade</h3>

      <p>
        Além do prazo para preparar a proposta, avalie o prazo de execução do
        contrato. Um contrato de 12 meses de serviço contínuo exige planejamento
        de capacidade diferente de um fornecimento pontual. Se a empresa não
        tem equipe disponível para iniciar a execução na data prevista, participar
        gera risco de inadimplemento — com penalidades que podem chegar a 20% do
        valor do contrato e impedimento de licitar por até 3 anos (Lei 14.133/2021,
        arts. 155 a 163).
      </p>

      {/* Section 5 -- Fator 3 */}
      <h2>Fator 3: Valor estimado — a faixa que faz sentido para a empresa</h2>

      <p>
        O{' '}
        <Link href="/glossario#valor-estimado" className="text-brand-navy dark:text-brand-blue hover:underline">
          valor estimado
        </Link>{' '}
        da licitação é o terceiro fator de viabilidade (peso 25%). A análise
        não é simplesmente &ldquo;o valor é alto, então vale a pena&rdquo;. Cada
        empresa tem uma faixa de valor onde sua competitividade é máxima, e editais
        fora dessa faixa — tanto acima quanto abaixo — reduzem a probabilidade de
        adjudicação.
      </p>

      <h3>Por que editais acima da faixa ideal são arriscados</h3>

      <p>
        Editais com valor estimado significativamente acima da capacidade histórica
        da empresa criam dois riscos. Primeiro, a{' '}
        <Link href="/glossario#habilitacao" className="text-brand-navy dark:text-brand-blue hover:underline">
          habilitação
        </Link>{' '}
        exige atestados de capacidade técnica proporcionais ao volume — tipicamente
        50% do quantitativo principal. Uma empresa que nunca executou contrato acima
        de R$ 500 mil terá dificuldade em comprovar capacidade para um contrato de
        R$ 2 milhões. Segundo, a execução de contratos acima da capacidade
        operacional gera risco de inadimplemento, com penalidades severas.
      </p>

      <h3>Por que editais abaixo da faixa ideal desperdiçam recursos</h3>

      <p>
        Editais com valor muito baixo consomem o mesmo esforço de preparação de
        proposta (análise, documentação, sessão) mas geram margem que não
        justifica o investimento. Uma empresa com estrutura para contratos de
        R$ 300 mil que disputa pregões de R$ 20 mil está alocando o tempo da equipe
        em oportunidades com retorno marginal. O custo de oportunidade — licitações
        maiores que deixou de analisar — é o prejuízo real.
      </p>

      <h3>Como definir a faixa ideal</h3>

      <p>
        A faixa ideal é determinada por três variáveis: os atestados de capacidade
        técnica disponíveis (definem o teto), a estrutura de custos fixos (define
        o piso — abaixo do qual a margem é insuficiente) e o histórico de
        adjudicação (valida empiricamente a faixa onde a empresa é mais
        competitiva). Uma análise simples: liste as últimas 20 licitações
        disputadas, separe as vencidas das perdidas, e identifique a faixa de valor
        onde a taxa de adjudicação é maior. Essa é a faixa ideal para concentrar
        esforço.
      </p>

      {/* BlogInlineCTA at ~40% */}
      <BlogInlineCTA
        slug="analise-viabilidade-editais-guia"
        campaign="guias"
        ctaHref="/explorar"
        ctaText="Explorar licitações grátis"
        ctaMessage="Descubra editais abertos no seu setor — busca gratuita"
      />

      {/* Section 7 -- Fator 4 */}
      <h2>Fator 4: Geografia — custos logísticos e presença regional</h2>

      <p>
        A geografia é o quarto fator (peso 20%) e frequentemente subestimada por
        empresas que buscam editais em todo o território nacional sem considerar
        o impacto logístico na margem do contrato.
      </p>

      <h3>Serviços presenciais: distância como fator eliminatório</h3>

      <p>
        Para serviços que exigem presença física (limpeza, manutenção predial,
        segurança, obras), a distância entre a base operacional da empresa e o
        local de execução determina custos de mobilização, supervisão e manutenção
        da equipe. Uma empresa sediada em Curitiba que vence um contrato de
        facilities em Manaus precisa considerar: passagens aéreas para supervisão
        mensal, hospedagem de equipe, diferenças salariais regionais e dificuldade
        de substituição rápida de funcionários. Esses custos podem consumir 15% a
        30% da margem prevista. Para o setor de engenharia especificamente, veja{' '}
        <Link href="/blog/licitacoes-engenharia-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          licitações de engenharia em 2026
        </Link>.
      </p>

      <h3>Fornecimento de bens: frete como variável de margem</h3>

      <p>
        Para fornecimento de bens, o custo de frete varia de 3% a 15% do valor
        do contrato dependendo do volume, peso e distância. Entregas em capitais
        da região Norte (Manaus, Belém, Porto Velho) a partir de centros de
        distribuição no Sudeste podem ter custo de frete 3 a 5 vezes maior que
        entregas regionais. Esse custo precisa ser incorporado na proposta de
        preço — e se não for, reduz a margem a ponto de tornar o contrato
        deficitário.
      </p>

      <h3>Visita técnica: custo e viabilidade</h3>

      <p>
        Alguns editais exigem visita técnica ao local de execução como condição de
        habilitação. O custo da visita (transporte, hospedagem, diárias do
        responsável técnico) varia de R$ 500 a R$ 3.000 dependendo da localização.
        Para editais de valor baixo (até R$ 50 mil), o custo da visita técnica
        pode representar 5% ou mais do valor total — impactando diretamente a
        viabilidade. Avalie se o edital permite declaração de conhecimento das
        condições locais como alternativa à visita.
      </p>

      <h3>A vantagem da atuação regionalizada</h3>

      <p>
        Empresas que concentram atuação em uma região geográfica definida (por
        exemplo, 3 a 5 estados contíguos) têm vantagens estruturais: custos
        logísticos menores, rede de fornecedores estabelecida, conhecimento dos
        órgãos compradores e capacidade de resposta rápida. A análise de
        viabilidade deve refletir essa realidade — editais na região de atuação
        recebem pontuação mais alta que editais em regiões distantes, a menos que
        o valor do contrato justifique a expansão geográfica.
      </p>

      {/* Section 8 -- Framework go/no-go */}
      <h2>O framework go/no-go: combinando os 4 fatores em uma decisão</h2>

      <p>
        Os quatro fatores individualmente já filtram editais inviáveis. Combinados
        em um score ponderado, criam um framework de decisão objetivo que pode ser
        aplicado sistematicamente a cada edital identificado.
      </p>

      <h3>Scoring simplificado</h3>

      <p>
        Para cada fator, atribua uma nota de 0 a 10. Multiplique pelo peso do
        fator. Some os quatro resultados. O score máximo é 10.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Framework de scoring go/no-go
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Modalidade (peso 0,30):</strong> 10 = modalidade com maior
            taxa histórica de adjudicação da empresa. 5 = modalidade com taxa
            intermediária. 0 = modalidade nunca disputada ou com taxa abaixo de 5%.
          </li>
          <li>
            <strong>Timeline (peso 0,25):</strong> 10 = prazo confortável (acima
            do mínimo viável + 5 dias). 5 = prazo mínimo viável. 0 = prazo
            insuficiente para proposta competitiva.
          </li>
          <li>
            <strong>Valor (peso 0,25):</strong> 10 = centro da faixa ideal da
            empresa. 5 = borda da faixa ideal. 0 = fora da faixa (acima ou
            abaixo).
          </li>
          <li>
            <strong>Geografia (peso 0,20):</strong> 10 = região de atuação
            principal. 5 = região acessível com custo logístico moderado. 0 =
            região remota com custo logístico superior a 15% da margem.
          </li>
        </ul>
        <div className="mt-4 pt-3 border-t border-[var(--border)]">
          <p className="text-sm text-ink-secondary">
            <strong>Decisão:</strong> Score acima de 7,0 = GO (participar). Score
            entre 5,0 e 7,0 = análise aprofundada do edital antes de decidir.
            Score abaixo de 5,0 = NO-GO (descartar).
          </p>
        </div>
      </div>

      <p>
        A vantagem do scoring é tornar a decisão objetiva e repetível. Em vez de
        debates subjetivos sobre &ldquo;se vale a pena&rdquo;, a equipe aplica o
        framework e concentra a discussão nos editais da faixa intermediária (5,0
        a 7,0). Editais acima de 7,0 avançam automaticamente para análise
        detalhada. Editais abaixo de 5,0 são descartados sem consumir tempo da
        equipe. Sobre a decisão de disputar ou não, consulte{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao" className="text-brand-navy dark:text-brand-blue hover:underline">
          como saber se vale a pena disputar um pregão
        </Link>.
      </p>

      {/* Section 9 -- Exemplo prático */}
      <h2>Exemplo prático: analisando 3 editais com o framework</h2>

      <p>
        Para ilustrar a aplicação do framework, considere uma empresa de TI
        sediada em Belo Horizonte (MG), com faturamento anual de R$ 3 milhões,
        que participa principalmente de pregões eletrônicos de software e
        serviços de TI na região Sudeste.
      </p>

      <h3>Edital A — Pregão eletrônico para licenças de software (MG)</h3>

      <p>
        Modalidade: pregão eletrônico (nota 9 — modalidade principal da empresa).
        Timeline: 12 dias úteis até abertura (nota 8 — prazo confortável).
        Valor: R$ 180 mil (nota 9 — centro da faixa ideal). Geografia: Belo
        Horizonte (nota 10 — sede da empresa).{' '}
        <strong>Score: 9,0 x 0,30 + 8,0 x 0,25 + 9,0 x 0,25 + 10,0 x 0,20 =
        8,95.</strong> Decisão: GO. O edital é altamente compatível com o perfil
        da empresa em todos os fatores.
      </p>

      <h3>Edital B — {' '}
        <Link href="/glossario#concorrencia" className="text-brand-navy dark:text-brand-blue hover:underline">
          Concorrência
        </Link>{' '}
        para sistema integrado de gestão (AM)</h3>

      <p>
        Modalidade: concorrência (nota 4 — empresa tem taxa de 8% nessa
        modalidade). Timeline: 25 dias úteis (nota 7 — viável mas exige
        dedicação). Valor: R$ 1,2 milhão (nota 5 — acima da faixa usual, mas
        há atestados parciais). Geografia: Manaus (nota 2 — fora da região de
        atuação, custo de deslocamento alto).{' '}
        <strong>Score: 4,0 x 0,30 + 7,0 x 0,25 + 5,0 x 0,25 + 2,0 x 0,20 =
        4,60.</strong> Decisão: NO-GO. O custo de participação em concorrência
        fora da região não justifica a probabilidade de adjudicação.
      </p>

      <h3>Edital C — Pregão para manutenção de infraestrutura de TI (SP)</h3>

      <p>
        Modalidade: pregão eletrônico (nota 9). Timeline: 6 dias úteis (nota 4 --
        prazo apertado mas viável se documentação estiver pronta). Valor: R$ 95
        mil (nota 7 — dentro da faixa, mas na borda inferior). Geografia: São
        Paulo capital (nota 7 — acessível, equipe remota viável para TI).{' '}
        <strong>Score: 9,0 x 0,30 + 4,0 x 0,25 + 7,0 x 0,25 + 7,0 x 0,20 =
        6,85.</strong> Decisão: análise aprofundada. O score está na faixa
        intermediária — vale ler o edital completo antes de decidir. O prazo
        apertado é o principal risco.
      </p>

      <p>
        O exemplo demonstra que o framework não é binário para todos os casos.
        Editais na faixa 5,0 a 7,0 exigem julgamento humano complementar —
        mas a grande maioria dos editais (os claramente bons e os claramente
        ruins) são decididos automaticamente pelo scoring.
      </p>

      {/* Section 10 -- Automatização */}
      <h2>Automatizando a análise de viabilidade com IA</h2>

      <p>
        O framework manual descrito acima funciona, mas exige que o analista
        avalie cada fator para cada edital — uma tarefa que consome de 5 a 15
        minutos por edital. Para uma empresa que monitora 100 editais por semana,
        isso representa 8 a 25 horas semanais apenas na fase de viabilidade.
      </p>

      <p>
        Ferramentas de inteligência em licitações com IA automatizam essa análise.
        O sistema extrai automaticamente a modalidade, data de abertura, valor
        estimado e localização do edital, aplica os pesos configuráveis e gera o
        score composto em milissegundos. O analista recebe uma lista já ordenada
        por viabilidade — os editais com score acima de 7,0 no topo, seguidos pela
        faixa intermediária, com os editais abaixo de 5,0 já filtrados.
      </p>

      <p>
        A automação também resolve o problema da consistência. Quando dois analistas
        avaliam o mesmo edital manualmente, é comum que atribuam notas diferentes
        aos fatores — introduzindo subjetividade no processo. A avaliação por IA é
        determinística: o mesmo edital recebe o mesmo score sempre, independentemente
        de quem processou. Para entender como a IA aplica esses fatores na prática,
        veja{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-navy dark:text-brand-blue hover:underline">
          inteligência artificial em licitações: como funciona
        </Link>.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Impacto da automação na análise de viabilidade
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Tempo de análise por edital:</strong> Manual: 5 a 15 minutos.
            Automatizado: menos de 1 segundo. Redução: 99%+.
          </li>
          <li>
            <strong>Consistência:</strong> Manual: depende do analista, varia com
            cansaço e carga de trabalho. Automatizado: determinístico, mesmo
            score para o mesmo edital sempre.
          </li>
          <li>
            <strong>Cobertura:</strong> Manual: analista avalia 20 a 40 editais
            por dia. Automatizado: processa milhares de editais por hora.
          </li>
          <li>
            <strong>Custo por análise:</strong> Manual: R$ 5 a R$ 15 (tempo do
            analista). Automatizado: menos de R$ 0,01 por edital.
          </li>
        </ul>
      </div>

      {/* Section 11 -- Por setor */}
      <h2>Viabilidade por setor: particularidades que mudam a ponderação</h2>

      <p>
        Os pesos padrão (30% modalidade, 25% timeline, 25% valor, 20% geografia)
        funcionam como ponto de partida, mas setores específicos têm
        particularidades que justificam ajustes na ponderação.
      </p>

      <h3>Engenharia e obras</h3>

      <p>
        Para o setor de engenharia, a geografia deve ter peso maior (30% ou mais).
        Obras exigem presença física contínua, mobilização de equipamentos pesados
        e equipe local. A distância entre a base da empresa e o local da obra é
        frequentemente o fator mais determinante na margem do contrato. Os atestados
        de capacidade técnica para engenharia são também mais restritivos — exigem
        acervo técnico (CAT/CREA) com quantitativos proporcionais. Veja mais em{' '}
        <Link href="/blog/licitacoes-engenharia-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          licitações de engenharia em 2026
        </Link>.
      </p>

      <h3>Tecnologia da informação</h3>

      <p>
        Para TI, a timeline deve ter peso maior (30% ou mais). Propostas de TI
        frequentemente exigem demonstração de solução, prova de conceito ou
        adequação técnica que demanda tempo de preparação. Por outro lado, a
        geografia tem peso menor (10% a 15%) — muitos serviços de TI são
        executados remotamente, e o pregão eletrônico permite participação de
        qualquer UF sem custo logístico significativo. Para oportunidades
        específicas do setor, veja{' '}
        <Link href="/blog/licitacoes-ti-software-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          licitações de TI e software em 2026
        </Link>.
      </p>

      <h3>Saúde e equipamentos médicos</h3>

      <p>
        Para o setor de saúde, os requisitos de habilitação têm peso implícito
        alto. Registros na ANVISA, licenças sanitárias e certificações específicas
        são eliminatórios e frequentemente não aparecem no resumo do edital — exigem
        leitura do termo de referência completo. A recomendação é adicionar um
        &ldquo;fator 5&rdquo; informal para o setor de saúde: requisitos
        regulatórios, com peso de 15% (redistribuído dos outros quatro fatores).
      </p>

      <h3>Alimentação e facilities</h3>

      <p>
        Para serviços contínuos como alimentação e limpeza, o valor estimado deve
        ser analisado com atenção especial aos encargos trabalhistas. Contratos
        de mão de obra intensiva têm margem operacional entre 5% e 12% — qualquer
        erro no cálculo de encargos (INSS, FGTS, férias, 13º, provisões de
        rescisão) pode tornar o contrato deficitário. A análise de viabilidade para
        esses setores deve incluir uma verificação rápida da compatibilidade do
        valor estimado com o piso salarial regional e os encargos aplicáveis.
      </p>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>O que é análise de viabilidade de edital?</h3>
      <p>
        Análise de viabilidade de edital é o processo de avaliar, antes de investir
        tempo e recursos na elaboração de proposta, se uma licitação é compatível
        com o perfil, a capacidade operacional e a estratégia comercial da empresa.
        A análise considera fatores como modalidade, prazo disponível, valor
        estimado, localização geográfica, requisitos de habilitação e nível de
        concorrência esperado. O objetivo é direcionar os recursos da empresa para
        editais com maior probabilidade de adjudicação e evitar o desperdício de
        investimento em oportunidades inadequadas ao perfil da empresa.
      </p>

      <h3>Quais os 4 fatores de viabilidade?</h3>
      <p>
        Os quatro fatores são: Modalidade (peso 30%), que avalia se o tipo de
        certame favorece o perfil competitivo da empresa com base no histórico de
        participação; Timeline (peso 25%), que verifica se o prazo entre a data
        atual e a abertura do edital é suficiente para preparar uma proposta
        competitiva; Valor estimado (peso 25%), que analisa se o valor da
        contratação está na faixa onde a empresa é mais competitiva, considerando
        atestados e estrutura de custos; e Geografia (peso 20%), que pondera os
        custos logísticos e a viabilidade de execução no local indicado no edital.
      </p>

      <h3>Como calcular o custo real de participar de uma licitação?</h3>
      <p>
        O custo real inclui todos os recursos investidos desde a identificação do
        edital até o resultado final: horas de analista para leitura e análise do
        edital (4 a 16 horas), elaboração de proposta comercial e técnica (8 a 40
        horas), obtenção e atualização de certidões e atestados, custos de garantia
        quando exigida (1% a 5% do valor da proposta), visita técnica (passagem,
        hospedagem, diárias), custos administrativos (autenticações, envio de
        documentação) e participação na sessão (2 a 4 horas em pregão eletrônico).
        Para pregões simples, o custo total fica entre R$ 1.500 e R$ 3.000. Para
        concorrências com proposta técnica, pode ultrapassar R$ 15.000 por edital.
      </p>

      <h3>Devo participar de toda licitação do meu setor?</h3>
      <p>
        Não. Participar de toda licitação do setor é um dos erros mais custosos no
        mercado B2G. Empresas com taxa de adjudicação saudável (acima de 15%) são
        seletivas — participam de 20% a 30% dos editais identificados. A
        seletividade permite elaborar propostas mais competitivas, manter a
        equipe focada em qualidade e não volume, e preservar o caixa para as
        oportunidades com maior retorno. A análise de viabilidade é o instrumento
        que torna essa seletividade objetiva e sistemática.
      </p>

      <h3>É possível automatizar a análise de viabilidade?</h3>
      <p>
        Sim. Ferramentas de inteligência em licitações com IA avaliam
        automaticamente os 4 fatores de viabilidade para cada edital publicado.
        O sistema extrai a modalidade, data de abertura, valor estimado e
        localização, aplica os pesos configuráveis e gera um score composto que
        ordena as oportunidades por viabilidade. A automação reduz o tempo de
        análise de 5 a 15 minutos por edital para menos de 1 segundo, permite
        processar centenas de editais por dia sem aumentar a equipe e garante
        consistência na avaliação — eliminando a subjetividade da análise manual.
      </p>

      <h3>Qual a taxa de adjudicação saudável?</h3>
      <p>
        A taxa de adjudicação varia por setor, modalidade e porte da empresa. Para
        empresas de médio porte em setores competitivos como tecnologia da
        informação e facilities, uma taxa entre 15% e 25% é considerada saudável.
        Para empresas especializadas em nichos com menor concorrência (equipamentos
        hospitalares específicos, software vertical), a taxa pode ultrapassar 30%.
        Taxas abaixo de 10% indicam que a empresa está participando de editais
        inadequados ao seu perfil — e a análise de viabilidade é a ferramenta para
        aumentar essa taxa concentrando esforço nas oportunidades certas.
      </p>
    </>
  );
}
