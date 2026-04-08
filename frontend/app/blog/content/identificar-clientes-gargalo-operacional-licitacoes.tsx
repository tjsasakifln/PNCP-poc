import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-263 CONS-12: Identificar Clientes pelo Gargalo Operacional em Licitações
 *
 * Content cluster: inteligência em licitações para consultorias
 * Target: 2,500-3,000 words | Primary KW: prospectar clientes consultoria licitação
 */
export default function IdentificarClientesGargaloOperacionalLicitacoes() {
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
                name: 'Quais sinais indicam que uma empresa precisa de consultoria de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os sete sinais mais confiáveis são: taxa de adjudicação abaixo de 10% (participação alta, resultado baixo), equipe de licitação sobrecarregada com acúmulo de editais sem análise, perda frequente de prazos para submissão de propostas, desistência de editais após início da análise por falta de tempo, concentração das participações em poucos órgãos contratantes, ausência de processo formal de triagem de oportunidades, e monitoramento de apenas um portal (ignorando PNCP, ComprasGov ou Portal de Compras Públicas).',
                },
              },
              {
                '@type': 'Question',
                name: 'Como oferecer diagnóstico gratuito para prospectar clientes B2G?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O diagnóstico gratuito é uma oferta de baixo risco para o prospect que demonstra o valor da consultoria antes de qualquer compromisso comercial. A estrutura recomendada inclui: análise do setor e UFs de atuação do prospect, levantamento do volume de oportunidades disponíveis nos últimos 30 dias, estimativa do valor total de editais viáveis, e comparação entre o volume monitorado pelo prospect versus o volume real disponível. O diagnóstico pode ser gerado em 30 a 60 minutos com ferramentas de inteligência em licitações.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais perfis de empresa B2G são mais receptivos à contratação de consultoria?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os perfis mais receptivos são empresas de médio porte (faturamento entre R$ 5 milhões e R$ 50 milhões) com setor de licitação composto por 1 a 3 pessoas, que participam de licitações há mais de 2 anos mas com resultados inconsistentes. Empresas em fase de crescimento que querem ampliar a carteira de contratos públicos e empresas que sofreram perda recente de um contrato relevante também são prospects de alta receptividade.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como abordar um prospect que não sabe que tem um problema operacional em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A abordagem mais eficaz é baseada em dados, não em discurso comercial. Em vez de afirmar que o prospect tem um problema, apresente dados do setor dele: quantas licitações foram publicadas no último mês no setor e nas UFs onde ele atua, qual o valor total dessas oportunidades, e quantas ele provavelmente não monitorou. O contraste entre o volume real de oportunidades e o que o prospect acompanha manualmente evidencia o gargalo sem necessidade de argumentação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a taxa de conversão esperada ao prospectar com diagnóstico gratuito?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Consultorias que usam diagnóstico gratuito baseado em dados como ferramenta de prospecção reportam taxas de conversão entre 15% e 30% do diagnóstico para contrato, versus 3% a 8% em abordagens comerciais tradicionais. A diferença se deve ao fato de que o diagnóstico demonstra valor antes de pedir compromisso, e filtra naturalmente os prospects com dor real daqueles que não têm necessidade imediata.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: prospectar clientes consultoria licitação */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A maioria das abordagens comerciais para{' '}
        <strong>prospectar clientes para consultoria de licitação</strong> segue
        um roteiro genérico: listar empresas que participam de licitações,
        enviar apresentações institucionais, esperar retorno. A taxa de conversão
        é baixa porque a abordagem ignora o timing — nem toda empresa que
        participa de licitações precisa de consultoria agora. O prospect ideal
        é aquele que já tem uma dor operacional identificável, que consome
        recursos e limita resultados. Este artigo mapeia sete sinais concretos
        de gargalo operacional em licitações que indicam que uma empresa está
        pronta para contratar ajuda externa, e apresenta scripts de abordagem
        calibrados para cada perfil.
      </p>

      {/* Section 1 */}
      <h2>O melhor cliente é o que já tem dor</h2>

      <p>
        Em vendas B2B de serviços consultivos, a variável que mais impacta a taxa
        de conversão não é a qualidade do pitch nem o preço — é a presença de uma
        dor ativa no prospect. Uma empresa que está satisfeita com seus resultados
        em licitações, mesmo que esses resultados sejam objetivamente medianos, é
        um prospect de baixa conversão. Uma empresa que perdeu três prazos no
        último mês, que viu sua taxa de adjudicação cair, ou que está com a equipe
        sobrecarregada, é um prospect que já reconhece a necessidade de mudança.
      </p>

      <p>
        A questão prática para a consultoria é: como identificar essas empresas
        sem acesso aos dados internos delas? A resposta está nos sinais públicos
        e semi-públicos de ineficiência operacional em licitações — indicadores
        que podem ser observados a partir de dados disponíveis nos portais de
        compras públicas e no comportamento de participação das empresas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência — Perfil de empresas com gargalo operacional em licitações
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Universo de empresas:</strong> O PNCP registra mais de
            180.000 fornecedores ativos (que participaram de ao menos uma
            licitação nos últimos 12 meses). Desses, estima-se que 60% a 70%
            são micro e pequenas empresas com 1 a 2 pessoas dedicadas a
            licitações (Fonte: PNCP + SEBRAE, Pesquisa Fornecedores
            Governamentais, 2023-2024).
          </li>
          <li>
            <strong>Taxa média de adjudicação:</strong> Entre 8% e 15% para
            empresas que participam regularmente. Apenas 4% das empresas
            reportam taxas acima de 30% (Fonte: SEBRAE, levantamento com 1.200
            MPEs, 2023).
          </li>
          <li>
            <strong>Taxa de desistência pós-início:</strong> Cerca de 22% das
            empresas que iniciam análise de um edital desistem antes de submeter
            proposta por falta de tempo ou recursos, segundo dados de plataformas
            de gestão de licitações (Fonte: pesquisa setorial Licitações.net,
            2024).
          </li>
          <li>
            <strong>Monitoramento de portais:</strong> 68% das empresas B2G
            consultam apenas 1 portal de licitações regularmente, perdendo
            oportunidades publicadas em fontes complementares como PNCP,
            ComprasGov e Portal de Compras Públicas (Fonte: SEBRAE,
            levantamento de práticas de monitoramento, 2023).
          </li>
        </ul>
      </div>

      {/* Section 2 */}
      <h2>Sinal 1: Participação alta, adjudicação baixa</h2>

      <p>
        O primeiro e mais confiável indicador de gargalo operacional é a
        desproporção entre volume de participação e resultados. Uma empresa que
        disputa 20 a 30 licitações por mês e adjudica 1 a 2 não tem um problema
        de competitividade — tem um problema de seleção. Está investindo recursos
        em editais onde não tem vantagem competitiva.
      </p>

      <p>
        Esse sinal pode ser parcialmente identificado a partir de dados públicos:
        nos portais de compras, é possível verificar a frequência de participação
        de uma empresa e cruzar com o número de adjudicações no mesmo período. A
        desproporção indica que a empresa precisa de triagem mais rigorosa — e
        triagem é exatamente o serviço que a consultoria pode oferecer.
      </p>

      <h3>Abordagem recomendada para esse perfil</h3>

      <p>
        Não comece com &ldquo;sua taxa de vitória está baixa&rdquo;. Comece com
        dados do setor: &ldquo;no setor de [setor], a taxa média de adjudicação
        de empresas com triagem estruturada é de 25% a 35%. Como está a sua?&rdquo;
        A pergunta provoca reflexão sem soar como julgamento. Se a empresa
        reconhece que está abaixo da média, o próximo passo é oferecer um
        diagnóstico gratuito para identificar as causas.
      </p>

      {/* Section 3 */}
      <h2>Sinal 2: Equipe de licitação sobrecarregada</h2>

      <p>
        Uma empresa com 1 a 2 pessoas no setor de licitações que atua em mais de
        3 UFs e monitora mais de 2 setores está operacionalmente sobrecarregada.
        A conta não fecha: monitorar PNCP, ComprasGov e outros portais, classificar
        editais, analisar viabilidade, preparar propostas e gerenciar documentação
        para múltiplos setores e regiões exige mais horas do que a equipe tem
        disponível.
      </p>

      <p>
        O sinal externo é a inconsistência: a empresa participa intensamente em
        alguns meses e quase desaparece em outros. Essa sazonalidade artificial
        indica que a equipe opera em ciclos de sobrecarga e recuperação, em vez
        de manter um fluxo constante e sustentável.
      </p>

      <h3>Abordagem recomendada para esse perfil</h3>

      <p>
        Foque na dor de tempo, não na dor de resultado: &ldquo;quantas horas por
        semana sua equipe dedica à busca e triagem de editais?&rdquo; Se a
        resposta for acima de 15 horas semanais, há espaço claro para
        automação. A consultoria pode demonstrar como reduzir esse tempo em
        70% a 85% com triagem automatizada, liberando a equipe para
        elaboração de propostas.
      </p>

      {/* Section 4 */}
      <h2>Sinal 3: Perda de prazos frequente</h2>

      <p>
        Perder o prazo de submissão de uma proposta é o sintoma mais visível de
        uma operação que ultrapassou sua capacidade. Quando a empresa identifica
        uma oportunidade relevante mas não consegue preparar a proposta a tempo,
        o custo é duplo: a oportunidade perdida e o custo afundado das horas
        já investidas na análise parcial.
      </p>

      <p>
        Esse sinal é mais difícil de identificar externamente, mas pode ser
        inferido: empresas que iniciam pedidos de esclarecimento (protocolo
        público) mas não aparecem na lista de propostas submetidas estão
        provavelmente enfrentando problemas de prazo ou capacidade.
      </p>

      <h3>Abordagem recomendada para esse perfil</h3>

      <p>
        A abordagem direta funciona: &ldquo;nos últimos 6 meses, quantas
        oportunidades sua empresa identificou como relevantes mas não
        conseguiu submeter proposta a tempo?&rdquo; Se o número for superior
        a 3, a empresa está deixando dinheiro na mesa. A consultoria pode
        quantificar o custo dessas oportunidades perdidas e posicionar seu
        serviço como investimento com retorno mensurável.
      </p>

      <BlogInlineCTA slug="identificar-clientes-gargalo-operacional-licitacoes" campaign="consultorias" />

      {/* Section 5 */}
      <h2>Sinal 4: Desistência após início de análise</h2>

      <p>
        Diferente da perda de prazo, a desistência deliberada ocorre quando a
        equipe começa a analisar um edital e descobre, após investir 4 a 8 horas,
        que a oportunidade não é viável — exigência de atestado incompatível,
        valor abaixo do mínimo operacional, cláusula restritiva identificada
        tardiamente.
      </p>

      <p>
        Esse padrão indica ausência de triagem estruturada. A empresa não filtra
        antes de analisar — investe tempo e depois descarta. Estima-se que
        consultorias que implementam triagem por viabilidade reduzem em 60% a
        75% os editais que chegam à fase de análise detalhada, eliminando a
        maioria das desistências tardias.
      </p>

      <h3>Abordagem recomendada para esse perfil</h3>

      <p>
        Quantifique o desperdício: &ldquo;se sua equipe analisa 15 editais por
        mês e desiste de 8 após a análise inicial, são 32 a 64 horas perdidas
        mensalmente. A R$ 100/hora, são R$ 3.200 a R$ 6.400 em trabalho sem
        retorno. Nosso serviço de triagem elimina 70% desses editais antes que
        sua equipe gaste uma hora sequer.&rdquo;
      </p>

      {/* Section 6 */}
      <h2>Sinal 5: Concentração em poucos órgãos</h2>

      <p>
        Uma empresa que participa de licitações de apenas 2 a 3 órgãos
        contratantes em um universo de dezenas ou centenas de órgãos relevantes
        para seu setor está operando com uma fração do mercado disponível. A
        concentração geralmente não é estratégica — é consequência de
        limitação operacional: a equipe só consegue monitorar os portais que
        já conhece.
      </p>

      <p>
        Os dados públicos permitem verificar essa concentração: no PNCP, é
        possível consultar o histórico de participação de um CNPJ e identificar
        a distribuição por órgão contratante. Uma concentração superior a 70%
        em 3 ou menos órgãos sinaliza oportunidade para diversificação — que é
        exatamente o que a consultoria pode facilitar.
      </p>

      {/* Section 7 */}
      <h2>Sinal 6: Sem processo formal de triagem</h2>

      <p>
        A ausência de critérios formais para decidir quais editais disputar é
        talvez o gargalo mais comum e o mais facilmente endereçável por uma
        consultoria. Empresas sem processo formal de triagem operam por intuição:
        o analista lê o título do edital, verifica o valor, e decide com base na
        &ldquo;sensação&rdquo; de que a oportunidade é boa.
      </p>

      <p>
        O resultado é inconsistência: a mesma empresa disputa editais de R$ 10.000
        e de R$ 2 milhões, em modalidades que vão de pregão eletrônico a
        concorrência, em UFs onde tem presença e em UFs onde nunca operou. Sem
        critérios, a seleção é aleatória — e os resultados refletem essa
        aleatoriedade.
      </p>

      <p>
        Para a consultoria, esse é o prospect mais receptivo a um serviço de
        triagem estruturada: o valor é imediato e demonstrável. A implementação
        de critérios formais de viabilidade pode elevar a taxa de adjudicação
        em 2 a 3 vezes em 6 meses. Sobre como usar dados para comprovar
        eficiência, veja{' '}
        <Link href="/blog/usar-dados-provar-eficiencia-licitacoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como usar dados para provar eficiência em licitações
        </Link>.
      </p>

      {/* Section 8 */}
      <h2>Sinal 7: Desconhecimento de fontes — uso de apenas 1 portal</h2>

      <p>
        A pesquisa do SEBRAE (2023) indica que 68% das empresas B2G consultam
        regularmente apenas 1 portal de licitações. Isso significa que a maioria
        dos fornecedores do governo está perdendo oportunidades publicadas
        exclusivamente em outras fontes. O PNCP é o portal de convergência
        previsto pela Lei 14.133/2021, mas a adesão de municípios e estados
        ainda é parcial. Oportunidades relevantes continuam sendo publicadas em
        portais como ComprasGov, Portal de Compras Públicas, e sites de
        prefeituras.
      </p>

      <p>
        Para a consultoria, esse sinal representa a oportunidade de demonstração
        de valor mais direta possível: mostrar ao prospect quantas licitações
        relevantes foram publicadas no último mês em fontes que ele não monitora.
        O contraste entre &ldquo;você viu 15 editais&rdquo; e &ldquo;existiam 47
        editais relevantes&rdquo; é um argumento comercial que dispensa
        explicação.
      </p>

      {/* Section 9 */}
      <h2>O diagnóstico gratuito como porta de entrada</h2>

      <p>
        Todos os sete sinais descritos convergem para uma ferramenta de prospecção
        poderosa: o diagnóstico gratuito de eficiência em licitações. Em vez de
        vender serviço de imediato, a consultoria oferece ao prospect uma análise
        objetiva da sua operação em licitações, baseada em dados.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Framework — Estrutura do diagnóstico gratuito para prospecção
        </p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>1. Mapeamento de mercado:</strong> Quantas licitações foram
            publicadas no setor e nas UFs do prospect nos últimos 30 dias? Qual
            o valor total estimado dessas oportunidades?
          </li>
          <li>
            <strong>2. Cobertura atual:</strong> De quantas desses editais o
            prospect teve conhecimento? (geralmente 20% a 40% do total
            disponível)
          </li>
          <li>
            <strong>3. Análise de viabilidade:</strong> Dos editais disponíveis,
            quantos tinham score de viabilidade acima de 7/10 para o perfil do
            prospect?
          </li>
          <li>
            <strong>4. Oportunidade perdida:</strong> Valor total dos editais
            viáveis que o prospect não monitorou. Este número é o argumento
            central.
          </li>
          <li>
            <strong>5. Recomendação:</strong> 3 a 5 ações concretas que o
            prospect pode implementar imediatamente, independentemente de
            contratar a consultoria.
          </li>
          <li className="pt-2 font-semibold">
            Tempo de execução: 30 a 60 minutos com ferramenta de inteligência em
            licitações. Taxa de conversão diagnóstico-para-contrato: 15% a 30%.
          </li>
        </ul>
      </div>

      <p>
        O diagnóstico funciona como filtro bidirecional: demonstra valor ao
        prospect que tem dor real e filtra prospects sem necessidade imediata
        (que não converteriam de qualquer forma). Para a consultoria, é mais
        eficiente investir 45 minutos em um diagnóstico que converte 25% do
        que investir horas em apresentações que convertem 5%.{' '}
        <Link href="/blog/diagnostico-eficiencia-licitacao-servico-premium" className="text-brand-navy dark:text-brand-blue hover:underline">
          Veja como transformar o diagnóstico em um serviço premium recorrente
        </Link>.
      </p>

      {/* Section 10 */}
      <h2>Script de abordagem por sinal identificado</h2>

      <p>
        A eficácia da abordagem depende de calibrar a mensagem ao sinal
        específico do prospect. Abordagens genéricas (&ldquo;somos uma
        consultoria de licitação, gostaria de conhecer nossos serviços?&rdquo;)
        têm taxa de resposta inferior a 5%. Abordagens calibradas por sinal
        chegam a 15% a 25% de taxa de resposta.
      </p>

      <p>
        <strong>Para o Sinal 1 (participação alta, adjudicação baixa):</strong>{' '}
        &ldquo;Notei que a [empresa] participou de [X] pregões no setor de
        [setor] nos últimos 3 meses. Empresas do mesmo perfil que implementam
        triagem por viabilidade costumam duplicar a taxa de adjudicação em 6
        meses. Posso preparar um diagnóstico gratuito mostrando onde estão as
        oportunidades de maior encaixe para o perfil de vocês?&rdquo;
      </p>

      <p>
        <strong>Para o Sinal 5 (concentração em poucos órgãos):</strong>{' '}
        &ldquo;Identifiquei que a [empresa] fornece predominantemente para [órgão
        A] e [órgão B]. Nos últimos 30 dias, foram publicados [X] editais
        relevantes para o setor de [setor] em [UFs de interesse] — a maioria em
        órgãos que vocês provavelmente ainda não monitoram. Posso compartilhar
        essa análise?&rdquo;
      </p>

      <p>
        <strong>Para o Sinal 7 (apenas 1 portal):</strong>{' '}
        &ldquo;Sua empresa monitora editais no [portal atual]. Nos últimos 30
        dias, [X] licitações relevantes para o setor de [setor] foram publicadas
        exclusivamente em outras fontes (PNCP, ComprasGov, Portal de Compras
        Públicas). O valor total estimado dessas oportunidades é de R$ [valor].
        Preparei um levantamento — posso enviar?&rdquo;
      </p>

      <p>
        Em todos os casos, a abordagem segue a mesma estrutura: dado específico
        sobre o prospect, referência de mercado que contextualiza o dado, e
        oferta de diagnóstico gratuito como próximo passo. Sem pressão
        comercial, sem discurso de vendas. O dado faz o trabalho. Para entender
        como esses gargalos operacionais resultam em perda de contratos, veja{' '}
        <Link href="/blog/erro-operacional-perder-contratos-publicos" className="text-brand-navy dark:text-brand-blue hover:underline">
          o erro operacional que faz empresas perderem contratos públicos
        </Link>.{' '}
        <Link href="/blog/aumentar-retencao-clientes-inteligencia-editais" className="text-brand-navy dark:text-brand-blue hover:underline">
          Saiba como essa mesma abordagem baseada em dados aumenta a retenção
          de clientes já existentes
        </Link>.
      </p>

      {/* CTA Section — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Ofereça diagnóstico com dados reais — use o SmartLic na demonstração
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Busque licitações por setor e UF, veja o volume de oportunidades com
          análise de viabilidade, e mostre ao prospect o que ele está perdendo.
          Diagnóstico pronto em menos de 1 hora.
        </p>
        <Link
          href="/signup?source=blog&article=identificar-clientes-gargalo-operacional-licitacoes&utm_source=blog&utm_medium=cta&utm_content=identificar-clientes-gargalo-operacional-licitacoes&utm_campaign=consultorias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/planos" className="underline hover:text-ink">
            Veja os planos
          </Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Quais sinais indicam que uma empresa precisa de consultoria de licitação?</h3>
      <p>
        Os sete sinais mais confiáveis são: taxa de adjudicação abaixo de 10%
        (participação alta, resultado baixo), equipe de licitação sobrecarregada
        com acúmulo de editais sem análise, perda frequente de prazos para
        submissão de propostas, desistência de editais após início da análise
        por falta de tempo, concentração das participações em poucos órgãos
        contratantes, ausência de processo formal de triagem de oportunidades,
        e monitoramento de apenas um portal (ignorando PNCP, ComprasGov ou
        Portal de Compras Públicas).
      </p>

      <h3>Como oferecer diagnóstico gratuito para prospectar clientes B2G?</h3>
      <p>
        O diagnóstico gratuito é uma oferta de baixo risco para o prospect que
        demonstra o valor da consultoria antes de qualquer compromisso comercial.
        A estrutura recomendada inclui: análise do setor e UFs de atuação do
        prospect, levantamento do volume de oportunidades disponíveis nos
        últimos 30 dias, estimativa do valor total de editais viáveis, e
        comparação entre o volume monitorado pelo prospect versus o volume real
        disponível. O diagnóstico pode ser gerado em 30 a 60 minutos com
        ferramentas de inteligência em licitações.
      </p>

      <h3>Quais perfis de empresa B2G são mais receptivos à contratação de consultoria?</h3>
      <p>
        Os perfis mais receptivos são empresas de médio porte (faturamento entre
        R$ 5 milhões e R$ 50 milhões) com setor de licitação composto por 1 a 3
        pessoas, que participam de licitações há mais de 2 anos mas com
        resultados inconsistentes. Empresas em fase de crescimento que querem
        ampliar a carteira de contratos públicos e empresas que sofreram perda
        recente de um contrato relevante também são prospects de alta
        receptividade.
      </p>

      <h3>Como abordar um prospect que não sabe que tem um problema operacional?</h3>
      <p>
        A abordagem mais eficaz é baseada em dados, não em discurso comercial.
        Em vez de afirmar que o prospect tem um problema, apresente dados do
        setor dele: quantas licitações foram publicadas no último mês no setor
        e nas UFs onde ele atua, qual o valor total dessas oportunidades, e
        quantas ele provavelmente não monitorou. O contraste entre o volume
        real de oportunidades e o que o prospect acompanha manualmente evidencia
        o gargalo sem necessidade de argumentação.
      </p>

      <h3>Qual a taxa de conversão esperada ao prospectar com diagnóstico gratuito?</h3>
      <p>
        Consultorias que usam diagnóstico gratuito baseado em dados como
        ferramenta de prospecção reportam taxas de conversão entre 15% e 30%
        do diagnóstico para contrato, versus 3% a 8% em abordagens comerciais
        tradicionais. A diferença se deve ao fato de que o diagnóstico demonstra
        valor antes de pedir compromisso, e filtra naturalmente os prospects com
        dor real daqueles que não têm necessidade imediata.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
