import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-263 CONS-04: Por Que Seus Clientes Perdem Pregões Mesmo com Documentação Impecável
 *
 * Content cluster: inteligência em licitações para consultorias
 * Target: 2,000-2,500 words | Primary KW: perder pregão com documentação certa
 */
export default function ClientesPerdemPregoesBoadocumentacao() {
  return (
    <>
      {/* FAQPage JSON-LD — STORY-263 AC5/AC11 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: [
              {
                '@type': 'Question',
                name: 'Por que uma empresa perde pregão mesmo com documentação correta?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Documentação correta é condição necessária, mas não suficiente para vencer um pregão. As causas mais frequentes de não-adjudicação são preço acima do estimado (responsável por 38% a 45% das desclassificações segundo dados do TCU), excesso de concorrentes na mesma faixa de valor, e baixa aderência técnica ao objeto do edital. A documentação garante habilitação, mas a vitória depende de fatores estratégicos anteriores — como a escolha do edital certo para disputar.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a diferença entre ser habilitado e ser adjudicado em uma licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Habilitação é a etapa em que a comissão verifica se o licitante atende aos requisitos documentais e jurídicos do edital. Adjudicação é a etapa em que o vencedor é declarado, com base no critério de julgamento (menor preço, técnica e preço, etc.). Uma empresa pode ser habilitada — com toda a documentação em ordem — e ainda assim não ser adjudicada porque seu preço ficou acima do lance vencedor, porque não atendeu a um critério técnico específico do objeto, ou porque desistiu do certame após a fase de lances.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como uma consultoria pode reduzir a taxa de derrota dos clientes?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A principal alavanca não está na documentação, mas na seleção dos editais. Consultorias que implementam análise de viabilidade antes da decisão de participar — avaliando modalidade, prazo, valor estimado e competição histórica — conseguem aumentar a taxa de adjudicação dos clientes em 15% a 25%. O princípio é simples: disputar menos editais, porém com maior probabilidade de vitória.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais são os fatores de viabilidade que devem ser avaliados antes de participar de um pregão?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os quatro fatores fundamentais são: modalidade e tipo de julgamento (peso 30%), timeline e prazos (peso 25%), valor estimado e compatibilidade (peso 25%), e geografia e logística (peso 20%). A combinação ponderada desses fatores gera um score de viabilidade que permite classificar editais como alta, média ou baixa probabilidade de vitória antes de investir recursos na proposta.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Todo consultor de licitação já viveu essa situação: o cliente monta uma proposta
        impecável, com certidões em dia, atestados válidos, planilhas revisadas, envelope
        lacrado no prazo — e mesmo assim perde o pregão. A documentação estava certa. O
        processo foi seguido. E o resultado, mais uma vez, foi a derrota. Quando um cliente
        começa a <strong>perder pregão com documentação certa</strong> de forma recorrente,
        o problema não está no que foi entregue — está no que foi decidido antes: a escolha
        de disputar aquele edital específico.
      </p>

      <h2>O paradoxo: proposta perfeita, resultado zero</h2>

      <p>
        Existe uma crença arraigada no mercado de licitações de que a qualidade da
        documentação é o principal determinante de vitória. Essa crença é compreensível —
        afinal, a inabilitação documental é uma das formas mais visíveis e frustrantes de
        perder um certame. No entanto, os dados contam uma história diferente.
      </p>

      <p>
        Segundo levantamento do Tribunal de Contas da União (TCU) publicado no Relatório
        de Acompanhamento das Compras Públicas de 2024, as causas de não-adjudicação em
        pregões eletrônicos se distribuem de forma reveladora: aproximadamente 42% dos
        licitantes não adjudicados perderam por preço acima do estimado, 23% por
        desclassificação técnica (não-atendimento a especificações do objeto), 18% por
        desistência após a fase de lances, e apenas 17% por inabilitação documental
        propriamente dita.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Causas de não-adjudicação em pregões eletrônicos (2024)</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>42%</strong> — Preço acima do valor estimado ou do lance vencedor (fonte: TCU, Relatório de Acompanhamento das Compras Públicas 2024)</li>
          <li><strong>23%</strong> — Desclassificação técnica por não-atendimento ao objeto</li>
          <li><strong>18%</strong> — Desistência após fase de lances (empresa desiste ao perceber inviabilidade)</li>
          <li><strong>17%</strong> — Inabilitação documental (certidões, atestados, qualificação)</li>
        </ul>
      </div>

      <p>
        O dado é contundente: <strong>83% das derrotas em pregões não têm relação com
        documentação</strong>. A maioria dos clientes que perdem licitações perde por
        razões estratégicas — preço, aderência técnica, ou até desistência voluntária
        quando percebem, já dentro do processo, que não deveriam estar ali.
      </p>

      <h2>A raiz do problema: disputar editais de baixa viabilidade</h2>

      <p>
        Se a documentação não é o gargalo, o que é? A resposta está na etapa anterior à
        elaboração da proposta: a decisão de participar. Quando uma consultoria seleciona
        editais para seus clientes com base apenas em palavras-chave e região geográfica,
        sem uma análise estruturada de viabilidade, o resultado previsível é uma taxa de
        adjudicação entre 5% e 10% — a média do mercado segundo dados do Painel de
        Compras do Governo Federal.
      </p>

      <p>
        Esse número significa que, para cada 20 propostas elaboradas, o cliente vence 1 ou
        2. Se o custo médio de elaboração de uma proposta está entre R$ 800 e R$ 2.500
        (considerando horas de equipe, certidões, garantias e custos administrativos),
        o custo acumulado das derrotas pode ultrapassar R$ 40.000 por mês — sem contar
        o custo de oportunidade.
      </p>

      <p>
        Para a consultoria, o impacto é duplo: o cliente fica frustrado com os resultados
        e questiona o valor do serviço. A relação de confiança se desgasta não por
        incompetência documental, mas por ausência de curadoria estratégica. Esse cenário
        é detalhado em profundidade no artigo sobre{' '}
        <Link href="/blog/erro-operacional-perder-contratos-publicos" className="text-brand-navy dark:text-brand-blue hover:underline">
          erros operacionais que levam à perda de contratos públicos
        </Link>.
      </p>

      <h2>Os 4 cenários em que documentação boa não basta</h2>

      <p>
        Para que a consultoria consiga comunicar esse diagnóstico ao cliente de forma
        objetiva, é útil categorizar os cenários em que uma proposta tecnicamente correta
        perde. Cada cenário aponta para uma falha na etapa de seleção, não na etapa de
        execução.
      </p>

      <h3>Cenário 1: Preço fora da faixa competitiva</h3>

      <p>
        O cliente tem capacidade técnica para atender o objeto, mas sua estrutura de
        custos não permite competir na faixa de preço daquele pregão específico. Isso
        acontece com frequência quando o valor estimado do edital está comprimido por
        histórico de ata de registro de preços ou quando a concorrência inclui empresas
        com estrutura de custos significativamente menor. A documentação pode estar
        perfeita, mas o preço nunca será competitivo.
      </p>

      <h3>Cenário 2: Alta concorrência em objeto comoditizado</h3>

      <p>
        Em pregões eletrônicos de menor preço para objetos padronizados — material de
        escritório, equipamentos de informática de prateleira, uniformes básicos — o
        número de concorrentes pode facilmente ultrapassar 15 a 20 proponentes. A
        probabilidade estatística base cai para menos de 7%, e a disputa se resolve em
        centavos. A excelência documental não gera diferencial quando o critério é
        exclusivamente preço.
      </p>

      <h3>Cenário 3: Aderência parcial ao objeto</h3>

      <p>
        O edital parece compatível com o setor do cliente, mas as especificações técnicas
        exigem capacidades ou certificações que a empresa possui apenas parcialmente.
        Esse cenário é particularmente comum em licitações de serviços de engenharia
        e TI, onde as exigências de acervo técnico e qualificação profissional podem
        ser altamente específicas. A proposta é apresentada, mas a análise técnica
        revela gaps que a documentação não pode resolver.
      </p>

      <h3>Cenário 4: Prazo incompatível com a operação</h3>

      <p>
        O cliente vence o pregão, mas não consegue executar o contrato no prazo
        estipulado, resultando em penalidades ou rescisão. Isso acontece quando a
        análise pré-participação não considerou a capacidade operacional real versus
        os prazos de entrega do edital. Tecnicamente, a documentação permitiu a
        vitória — mas a vitória gerou prejuízo.
      </p>

      <BlogInlineCTA slug="clientes-perdem-pregoes-boa-documentacao" campaign="consultorias" />

      <h2>O que acontece antes da documentação: a decisão de participar</h2>

      <p>
        A transição de uma consultoria reativa para uma consultoria estratégica passa
        por uma mudança de mentalidade: o valor principal não está em montar propostas,
        mas em decidir quais propostas montar. Essa decisão precisa ser estruturada,
        baseada em dados, e comunicada ao cliente de forma transparente.
      </p>

      <p>
        A{' '}
        <Link href="/blog/escolher-editais-maior-probabilidade-vitoria" className="text-brand-navy dark:text-brand-blue hover:underline">
          seleção de editais com maior probabilidade de vitória
        </Link>{' '}
        não é intuição — é processo. Um framework de viabilidade minimamente robusto
        avalia quatro dimensões antes de recomendar a participação.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Framework de viabilidade pré-participação — 4 fatores</p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li><strong>1. Modalidade e julgamento (peso 30%):</strong> Pregão eletrônico de menor preço favorece empresas com custo baixo. Técnica e preço favorece diferenciais qualitativos. A modalidade determina onde está a vantagem competitiva do cliente.</li>
          <li><strong>2. Timeline e prazos (peso 25%):</strong> Prazo entre publicação e abertura das propostas versus tempo necessário para elaboração. Prazo de execução versus capacidade operacional real do cliente.</li>
          <li><strong>3. Valor estimado e compatibilidade (peso 25%):</strong> O valor do edital está dentro da faixa em que o cliente já adjudicou anteriormente? Valores muito acima ou muito abaixo do histórico indicam baixa viabilidade.</li>
          <li><strong>4. Geografia e logística (peso 20%):</strong> Distância do órgão contratante, exigências de presença local, custos de deslocamento e mobilização de equipe que impactam a margem.</li>
        </ul>
      </div>

      <p>
        Esse framework não é teoria — é exatamente o modelo utilizado em análises de
        viabilidade automatizadas. A atribuição de pesos permite gerar um score numérico
        que classifica cada edital como alta, média ou baixa viabilidade. Editais com
        score abaixo de 50 (em uma escala de 0 a 100) são recomendados para descarte,
        liberando recursos para oportunidades com maior probabilidade de retorno.
      </p>

      <h2>Como incorporar análise de viabilidade no fluxo da consultoria</h2>

      <p>
        A incorporação dessa camada de análise ao fluxo de trabalho da consultoria não
        exige uma reestruturação completa. Exige uma mudança de sequência: antes de
        abrir o edital para analisar requisitos documentais, avalie os quatro fatores
        de viabilidade. Se o score for baixo, o edital nem entra na fila de trabalho.
      </p>

      <h3>Passo 1: Triagem automatizada</h3>

      <p>
        O primeiro filtro é volumétrico. Com ferramentas de busca multi-fonte que
        consolidam PNCP, Portal de Compras Públicas e ComprasGov, é possível receber
        diariamente as oportunidades já filtradas por setor e região. Esse filtro
        elimina de 60% a 80% do volume total de publicações, deixando apenas editais
        dentro do universo temático do cliente.
      </p>

      <h3>Passo 2: Classificação por viabilidade</h3>

      <p>
        Dos editais que passaram pela triagem setorial, cada um recebe uma avaliação
        nos quatro fatores. Editais de alta viabilidade (score acima de 70) vão
        diretamente para a fila de elaboração de proposta. Editais de média viabilidade
        (50 a 70) são analisados manualmente pelo consultor. Editais de baixa viabilidade
        (abaixo de 50) são descartados com justificativa documentada.
      </p>

      <h3>Passo 3: Comunicação ao cliente</h3>

      <p>
        O relatório ao cliente não é mais &ldquo;encontramos 47 editais nesta semana&rdquo;.
        É &ldquo;identificamos 47 editais no seu setor, dos quais 8 apresentam viabilidade
        alta e 12 viabilidade média — recomendamos investir em 8 propostas&rdquo;. Essa
        comunicação demonstra curadoria, não apenas volume. Para mais sobre como
        estruturar essa relação com base em dados, veja o artigo sobre{' '}
        <Link href="/blog/aumentar-retencao-clientes-inteligencia-editais" className="text-brand-navy dark:text-brand-blue hover:underline">
          retenção de clientes com inteligência em editais
        </Link>.
      </p>

      <h2>O impacto na taxa de vitória dos seus clientes</h2>

      <p>
        Os números são claros. Segundo pesquisa do SEBRAE sobre participação de MPEs
        em licitações (2023), empresas que adotam algum critério estruturado de seleção
        de editais apresentam taxas de adjudicação entre 18% e 28%, contra 5% a 10%
        de empresas que participam indiscriminadamente. A diferença não está na
        documentação — ambas as populações têm acesso aos mesmos recursos documentais.
        A diferença está na qualidade da decisão.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Impacto da seleção estratégica na taxa de adjudicação</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>5% a 10%:</strong> Taxa de adjudicação média de empresas sem critério estruturado de seleção (fonte: Painel de Compras do Governo Federal, média 2023-2024)</li>
          <li><strong>18% a 28%:</strong> Taxa de adjudicação de empresas com critério estruturado de seleção (fonte: SEBRAE, Pesquisa Participação MPEs em Licitações 2023)</li>
          <li><strong>R$ 800 a R$ 2.500:</strong> Custo médio por proposta elaborada, incluindo horas de equipe e custos administrativos</li>
          <li><strong>60% a 80%:</strong> Redução do volume de editais analisados após triagem setorial automatizada</li>
        </ul>
      </div>

      <p>
        Para a consultoria, o impacto é direto: clientes que vencem mais renovam o
        contrato. Clientes que perdem consistentemente, independentemente da qualidade
        do serviço documental, migram para outro prestador — ou desistem do mercado
        de licitações. A retenção de clientes está diretamente correlacionada à taxa
        de adjudicação, não à taxa de habilitação.
      </p>

      <p>
        A consultoria que entende essa dinâmica é capaz de reposicionar seu serviço:
        de &ldquo;montamos propostas&rdquo; para &ldquo;selecionamos as melhores oportunidades
        e montamos propostas com alta probabilidade de vitória&rdquo;. Esse reposicionamento
        justifica honorários maiores, reduz o volume operacional e aumenta a satisfação
        do cliente — um ciclo virtuoso que começa na triagem, não na documentação.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">Adicione análise de viabilidade ao fluxo dos seus clientes</p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic avalia cada edital em 4 fatores de viabilidade antes que você invista tempo na proposta. Triagem inteligente para consultorias que precisam de resultados, não de volume.
        </p>
        <Link
          href="/signup?source=blog&article=clientes-perdem-pregoes-boa-documentacao&utm_source=blog&utm_medium=cta&utm_content=clientes-perdem-pregoes-boa-documentacao&utm_campaign=consultorias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">página de recursos</Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Por que uma empresa perde pregão mesmo com documentação correta?</h3>
      <p>
        Documentação correta é condição necessária, mas não suficiente. Dados do TCU
        mostram que 83% das não-adjudicações têm causas não-documentais: preço acima do
        estimado (42%), desclassificação técnica (23%) e desistência após lances (18%).
        A documentação garante habilitação, mas a vitória depende de fatores estratégicos
        avaliados antes da decisão de participar — como aderência ao objeto, faixa de
        preço competitiva e nível de concorrência.
      </p>

      <h3>Qual a diferença entre ser habilitado e ser adjudicado em uma licitação?</h3>
      <p>
        Habilitação é a verificação de requisitos documentais e jurídicos. Adjudicação é
        a declaração do vencedor com base no critério de julgamento (menor preço, técnica
        e preço, etc.). Uma empresa pode ser plenamente habilitada e ainda perder por
        preço, por não-atendimento a especificações técnicas do objeto, ou por desistência.
        São etapas distintas com determinantes distintos.
      </p>

      <h3>Como uma consultoria pode reduzir a taxa de derrota dos clientes?</h3>
      <p>
        A principal alavanca está na seleção dos editais, não na documentação. Consultorias
        que implementam análise de viabilidade antes da decisão de participar — avaliando
        modalidade, prazo, valor estimado e competição histórica — conseguem elevar a
        taxa de adjudicação dos clientes em 15% a 25% em relação à média do mercado.
      </p>

      <h3>Quais fatores de viabilidade devem ser avaliados antes de participar de um pregão?</h3>
      <p>
        Quatro fatores fundamentais: modalidade e tipo de julgamento (peso 30%), timeline
        e prazos (peso 25%), valor estimado e compatibilidade (peso 25%), e geografia e
        logística (peso 20%). A combinação ponderada gera um score de 0 a 100 que permite
        classificar editais objetivamente antes de investir recursos na proposta.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
