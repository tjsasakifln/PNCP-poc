import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-08: Prazo de vigência de contratos públicos: Guia prático
 * Content cluster: contratos públicos
 * Target: ~2,500 words | Primary KW: prazo vigência contratos públicos
 */
export default function PrazoVigenciaContratosPublicosGuia() {
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
                name: 'Qual é o prazo máximo de vigência de um contrato público pela Lei 14.133/2021?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Pela Lei 14.133/2021 (Nova Lei de Licitações), o prazo máximo de vigência de contratos de serviços e fornecimentos contínuos é de 5 anos (Art. 106). Para contratos com investimentos previstos no plano plurianual ou que envolvam tecnologia e inovação, o prazo pode chegar a 10 anos (Art. 106, §4º). Contratos de Parceria Público-Privada (PPP) têm prazo máximo de 35 anos, incluindo eventual prorrogação (Art. 106, §5º).',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é prorrogação de contrato público e quando ela é permitida?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Prorrogação é a extensão da vigência de um contrato público já existente, sem necessidade de nova licitação. Pela Lei 14.133/2021, a prorrogação de contratos de serviços contínuos é permitida quando houver vantajosidade comprovada para a Administração e desde que o contratado mantenha os preços e condições. O prazo prorrogado não pode ultrapassar o limite máximo legal de 5 anos (ou 10 anos, nos casos especiais).',
                },
              },
              {
                '@type': 'Question',
                name: 'Contratos de fornecimento têm prazo máximo diferente dos contratos de serviços?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. Contratos de fornecimento de bens não continuados ficam limitados à vigência do respectivo crédito orçamentário — em geral, o exercício financeiro (31 de dezembro). Contratos de serviços de natureza contínua seguem as regras do Art. 106 da Lei 14.133/2021, com prazo de até 5 anos prorrogáveis. A distinção entre fornecimento pontual e serviço contínuo é, portanto, decisiva para o prazo máximo aplicável.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a diferença entre prorrogação e nova licitação para o mesmo objeto?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Prorrogação mantém o mesmo contratado, mesmo objeto e mesmas condições, sendo ato administrativo bilateral. Nova licitação abre disputa no mercado, permite ingresso de concorrentes e pode resultar em queda de preços. A Administração deve realizar nova licitação quando: (1) o prazo máximo legal foi atingido, (2) a prorrogação não for vantajosa, ou (3) houver alteração substancial no objeto contratado. Para fornecedores ativos, o vencimento é o momento de risco; para concorrentes, é oportunidade.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como monitorar contratos públicos próximos do vencimento para identificar oportunidades?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O Portal Nacional de Contratações Públicas (PNCP) disponibiliza dados de todos os contratos federais e estaduais, incluindo datas de início e término. É possível filtrar por órgão, UF, objeto e data de vencimento para identificar contratos que entrarão em processo de nova licitação. Plataformas especializadas automatizam esse monitoramento, alertando sobre contratos que vencem nos próximos 90 a 180 dias — janela ideal para preparar a proposta.',
                },
              },
            ],
          }),
        }}
      />

      {/* Abertura */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O prazo de vigência de um contrato público é um dos dados mais estratégicos para qualquer fornecedor
        do setor público. Ele define por quanto tempo o contratado prestará o serviço ou entregará o bem,
        quando o contrato poderá ser prorrogado e — fundamentalmente — quando a Administração precisará abrir
        nova licitação. Conhecer as regras da Lei 14.133/2021 sobre duração dos contratos não é apenas
        obrigação legal do gestor público: é inteligência de mercado para a empresa que quer vencer editais.
      </p>

      <h2>Por que o prazo de vigência importa mais do que parece</h2>
      <p>
        Sob a Lei 8.666/1993, contratos de serviços contínuos eram celebrados pelo prazo de 12 meses e
        prorrogados sucessivamente, em tese por até 60 meses. Na prática, a interpretação era nebulosa e os
        aditivos acumulavam-se de modo pouco transparente. A Lei 14.133/2021 reorganizou essa lógica, fixando
        prazos máximos claros e condicionando a prorrogação à comprovação de vantajosidade para a
        Administração.
      </p>
      <p>
        Para o fornecedor, as implicações práticas são diretas:
      </p>
      <ul>
        <li>
          <strong>Contratos mais longos</strong> significam maior previsibilidade de receita, menor custo de
          mobilização amortizado ao longo do tempo e vantagem competitiva para quem já está operando —
          porque a curva de aprendizado é aproveitada por mais anos.
        </li>
        <li>
          <strong>Contratos mais curtos</strong> geram mais oportunidades de entrada para concorrentes e
          exigem gestão de pipeline mais intensa — o fornecedor estabelecido precisa estar preparado para
          defender o contrato; o desafiante precisa identificar o momento certo de se posicionar.
        </li>
        <li>
          <strong>O calendário de vencimentos</strong> é, em essência, o calendário de oportunidades do
          mercado público. Mapear quando os principais contratos dos órgãos-alvo vencem é parte essencial
          de qualquer estratégia B2G consistente.
        </li>
      </ul>

      <h2>O que diz a Lei 14.133/2021: Arts. 105 a 114</h2>
      <p>
        A Nova Lei de Licitações dedica os Arts. 105 a 114 à disciplina dos contratos administrativos.
        Os dispositivos centrais para o prazo de vigência estão nos Arts. 105, 106 e 107.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3">Art. 105 — Vinculação ao instrumento convocatório</h3>
        <p className="text-sm sm:text-base text-ink-secondary mb-2">
          O contrato deve guardar conformidade com os termos do edital de licitação ou do ato que o
          autorizou. Qualquer prazo fixado no contrato que extrapole os limites estabelecidos no Art. 106
          é nulo de pleno direito — e a responsabilidade recai sobre o gestor que assinou o instrumento.
        </p>
        <p className="text-sm sm:text-base text-ink-secondary">
          <strong>Impacto prático:</strong> Verifique sempre o prazo fixado no edital. Se o edital prevê
          contrato de 12 meses para um serviço contínuo, questione via impugnação se há previsão de
          prorrogação — a omissão pode significar que o órgão pretende realizar nova licitação ao fim do
          período inicial.
        </p>
      </div>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3">Art. 106 — Prazos máximos por tipo de contrato</h3>
        <p className="text-sm sm:text-base text-ink-secondary mb-2">
          O caput do Art. 106 estabelece que contratos de serviços e fornecimentos de natureza contínua
          podem ter vigência de <strong>até 5 anos</strong> — sem necessidade de justificativa específica
          para cada prorrogação anual, desde que a vantajosidade seja mantida.
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-2">
          O <strong>§4º</strong> admite prazo de <strong>até 10 anos</strong> nos seguintes casos especiais:
        </p>
        <ul className="text-sm sm:text-base text-ink-secondary list-disc list-inside space-y-1 mb-2">
          <li>Contratos que gerem receita para a Administração (concessões de uso de bem público);</li>
          <li>Contratações que envolvam transferência de tecnologia ou treinamento especializado;</li>
          <li>Contratos com investimentos relevantes previstos no plano plurianual (PPA);</li>
          <li>Contratos de serviços de TIC estratégicos.</li>
        </ul>
        <p className="text-sm sm:text-base text-ink-secondary">
          O <strong>§5º</strong> reserva o prazo de <strong>até 35 anos</strong> para os contratos de
          Parceria Público-Privada (PPP) regidos pela Lei 11.079/2004, compatível com a amortização dos
          investimentos de longo prazo nessa modalidade.
        </p>
      </div>

      <h2>Comparação com a Lei 8.666/1993</h2>
      <p>
        A lei anterior (8.666/1993) previa, no Art. 57, vigência limitada ao exercício financeiro para
        contratos de fornecimento, e prorrogação de até 60 meses para serviços contínuos — exigindo
        aditivo formal a cada 12 meses, com justificativa específica. A nova lei simplificou o regime:
        permite celebrar contrato já com prazo inicial de até 5 anos, sem a burocracia dos aditivos anuais
        repetitivos.
      </p>
      <p>
        Para contratos firmados ainda sob a égide da 8.666/1993, as regras de prorrogação do Art. 57
        continuam aplicáveis enquanto o contrato estiver vigente. A Lei 14.133/2021 não retroage sobre
        contratos em andamento — apenas os novos contratos firmados após a vigência plena da nova lei
        (desde 1.º de abril de 2023) seguem o novo regime.
      </p>

      <h2>Contratos de fornecimento: a regra do crédito orçamentário</h2>
      <p>
        Para bens e serviços de natureza <em>não contínua</em> — aqueles que se esgotam em uma única
        entrega ou em um conjunto definido de entregas — a vigência fica limitada à disponibilidade do
        crédito orçamentário que sustenta a despesa. Na prática, isso significa que o contrato expira em
        31 de dezembro do exercício financeiro em que foi empenhado, salvo se o empenho for inscrito em
        Restos a Pagar.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3">Atenção ao calendário orçamentário</h3>
        <p className="text-sm sm:text-base text-ink-secondary">
          Contratos de fornecimento firmados no segundo semestre têm prazo de execução muito curto. Editais
          publicados entre agosto e outubro para entrega até dezembro exigem capacidade de mobilização
          rápida — o que favorece fornecedores com estoque regulatório ou capacidade produtiva imediata.
          Planeje seu pipeline de propostas levando em conta o calendário orçamentário federal e estadual.
        </p>
      </div>

      <BlogInlineCTA slug="prazo-vigencia-contratos-publicos-guia" campaign="contratos" />

      <h2>Prorrogação: quando é possível e quais as condições</h2>
      <p>
        A prorrogação de contrato público não é automática nem ilimitada. A Lei 14.133/2021 condiciona
        cada prorrogação à demonstração de que a continuidade do contrato é vantajosa para a
        Administração. Os requisitos cumulativos são:
      </p>
      <ol>
        <li>
          <strong>Vantajosidade comprovada:</strong> O preço contratado deve estar compatível com o mercado,
          verificado por pesquisa de preços atualizada. Se o preço estiver acima do praticado no mercado,
          o órgão deve negociar redução antes de prorrogar.
        </li>
        <li>
          <strong>Desempenho satisfatório do contratado:</strong> A Administração não pode prorrogar
          contrato com empresa que acumula sanções, atrasos ou qualidade de serviço abaixo do previsto
          no contrato.
        </li>
        <li>
          <strong>Interesse público justificado:</strong> A continuidade do serviço deve ser necessária e
          a interrupção, prejudicial. O gestor deve formalizar essa motivação no processo administrativo.
        </li>
        <li>
          <strong>Respeito ao prazo máximo legal:</strong> Nenhuma prorrogação pode levar o contrato a
          superar o limite de 5 anos (ou 10 anos, nos casos do §4º do Art. 106).
        </li>
      </ol>
      <p>
        O gestor que prorrogar contrato sem atender essas condições incorre em irregularidade sujeita a
        questionamento pelo TCU e pelos órgãos de controle interno. Decisões recentes do Tribunal de
        Contas da União (Acórdão 1.590/2021 — Plenário, entre outros) reforçam a necessidade de pesquisa
        de preços atualizada como requisito essencial para a prorrogação.
      </p>

      <h2>Renovação vs. nova licitação: quando cada uma se aplica</h2>
      <p>
        A distinção entre prorrogação (renovação dentro do mesmo contrato) e nova licitação é decisiva
        para o planejamento de fornecedores:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-4">Prorrogação — quando se aplica</h3>
        <ul className="text-sm sm:text-base text-ink-secondary space-y-2">
          <li>Contrato ainda dentro do prazo máximo legal (5 ou 10 anos);</li>
          <li>Preço contratado compatível com o mercado após pesquisa atualizada;</li>
          <li>Histórico de execução satisfatório pelo contratado;</li>
          <li>Objeto do contrato não se alterou substancialmente;</li>
          <li>Continuidade do serviço é conveniente e oportuna para a Administração.</li>
        </ul>
        <p className="text-sm sm:text-base text-ink-secondary mt-3">
          <strong>Vantagem para o fornecedor atual:</strong> Não há disputa. O contratado mantém o
          contrato desde que atenda os requisitos e negocie eventual ajuste de preço.
        </p>
      </div>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-4">Nova licitação — quando é obrigatória</h3>
        <ul className="text-sm sm:text-base text-ink-secondary space-y-2">
          <li>Prazo máximo legal atingido (5 ou 10 anos, conforme o caso);</li>
          <li>Prorrogação não é vantajosa — preço acima do mercado e fornecedor não aceita redução;</li>
          <li>Mudança substancial no objeto (novo escopo exige novo processo);  </li>
          <li>Rescisão do contrato anterior por inadimplência ou interesse da Administração;</li>
          <li>Extinção do contrato por acordo entre as partes (distrato).</li>
        </ul>
        <p className="text-sm sm:text-base text-ink-secondary mt-3">
          <strong>Oportunidade para concorrentes:</strong> A nova licitação é o momento de ingresso.
          Monitorar contratos que atingem o prazo máximo nos próximos 90 a 180 dias é a principal
          ferramenta de geração de oportunidades no mercado público.
        </p>
      </div>

      <h2>Impacto do prazo sobre a precificação da proposta</h2>
      <p>
        A duração do contrato afeta diretamente a estrutura de preços de uma proposta competitiva. Os
        principais efeitos são:
      </p>
      <h3>Contratos de longa duração (4 a 5 anos)</h3>
      <p>
        Permitem diluir os custos de mobilização — treinamento de equipe, aquisição de equipamentos,
        adaptações operacionais — ao longo de um período mais longo, reduzindo o custo unitário por
        período de execução. O fornecedor pode oferecer preço mais competitivo no início, sabendo que
        amortizará o investimento ao longo dos anos.
      </p>
      <p>
        Por outro lado, contratos longos exigem atenção aos reajustes contratuais. O índice de reajuste
        (IPCA, INPC, IGP-M ou índice setorial) deve ser negociado no contrato desde a assinatura. Em
        cenários de inflação elevada, a falta de reajuste adequado corrói a margem do fornecedor ao longo
        dos anos — transformando um contrato vantajoso no primeiro ano em um contrato deficitário no
        quinto ano.
      </p>
      <h3>Contratos de curta duração (12 meses)</h3>
      <p>
        Exigem que todos os custos de mobilização sejam recuperados no primeiro exercício, elevando o
        preço necessário para viabilidade econômica. A vantagem é maior previsibilidade de preço real —
        o fornecedor não precisa projetar a inflação para anos à frente. A desvantagem é o risco de
        perder o contrato na renovação anual para um concorrente que ofereça preço mais baixo.
      </p>
      <p>
        Para contratos de serviços de limpeza e conservação — segmento intensivo em mão de obra —
        a variação da convenção coletiva de trabalho é determinante. Veja exemplos de contratos ativos
        no{' '}
        <Link href="/contratos/limpeza/SP" className="text-brand-blue underline hover:no-underline">
          segmento de limpeza em São Paulo
        </Link>{' '}
        e observe como o histórico de preços varia ao longo dos aditivos de prorrogação.
      </p>

      <h2>Como rastrear contratos próximos do vencimento</h2>
      <p>
        O PNCP (Portal Nacional de Contratações Públicas) é a fonte oficial de dados sobre contratos
        públicos federais, estaduais e municipais publicados desde abril de 2023. Todos os contratos
        celebrados sob a Lei 14.133/2021 devem ser registrados no portal, incluindo data de início,
        data de término e eventuais aditivos de prorrogação.
      </p>
      <p>
        A consulta direta ao PNCP permite filtrar por órgão, UF, objeto e período de vencimento. Para
        uma estratégia sistemática de monitoramento, o processo envolve:
      </p>
      <ol>
        <li>
          <strong>Identificar os órgãos-alvo:</strong> Liste os órgãos que mais contratam no seu segmento
          e na sua área de atuação. Prefira órgãos com histórico de pagamento regular e menor concentração
          de um único fornecedor.
        </li>
        <li>
          <strong>Mapear os contratos ativos:</strong> Para cada órgão-alvo, identifique contratos do
          seu objeto com vigência nos próximos 12 meses. O PNCP permite filtrar por objeto e período.
          Explore também o{' '}
          <Link href="/contratos/orgao/00394460000141" className="text-brand-blue underline hover:no-underline">
            histórico de contratos por órgão
          </Link>{' '}
          para entender padrões de prorrogação e de abertura de novas licitações.
        </li>
        <li>
          <strong>Classificar por janela de oportunidade:</strong> Contratos que vencem em menos de 90
          dias já estão no processo de prorrogação ou nova licitação. Contratos que vencem em 90 a 180
          dias são o momento ideal para se posicionar — o processo licitatório costuma levar entre 45 e
          90 dias.
        </li>
        <li>
          <strong>Monitorar aditivos publicados:</strong> Quando um contrato recebe aditivo de
          prorrogação, o PNCP registra a nova data de término. Monitore aditivos para saber quando o
          prazo máximo será atingido e a nova licitação será inevitável.
        </li>
      </ol>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3">Exemplo de janela de oportunidade</h3>
        <p className="text-sm sm:text-base text-ink-secondary mb-2">
          Um contrato de serviços de limpeza firmado em maio de 2020 (ainda sob a 8.666/1993) com prazo
          de 12 meses e prorrogações anuais atinge o limite de 60 meses em maio de 2025. Nesse ponto, é
          obrigatória nova licitação. Uma empresa monitorando esse contrato desde novembro de 2024 teria
          6 meses para preparar proposta, levantar atestados de capacidade técnica e se posicionar junto
          ao órgão.
        </p>
        <p className="text-sm sm:text-base text-ink-secondary">
          Configure alertas automáticos para{' '}
          <Link href="/alertas-publicos/limpeza/SP" className="text-brand-blue underline hover:no-underline">
            contratos de limpeza em São Paulo
          </Link>{' '}
          e receba notificações quando novos editais forem publicados nesse segmento.
        </p>
      </div>

      <h2>Gestão do calendário: datas-chave para monitorar</h2>
      <p>
        Uma estratégia eficiente de monitoramento de prazos considera as seguintes datas-chave no ciclo
        de vida de um contrato público:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-4">Calendário de ciclo de vida do contrato</h3>
        <div className="space-y-3">
          <div>
            <p className="text-sm font-semibold text-ink">D — Assinatura do contrato</p>
            <p className="text-sm text-ink-secondary">Início do prazo. Publicação obrigatória no PNCP em até 20 dias úteis.</p>
          </div>
          <div>
            <p className="text-sm font-semibold text-ink">D + 6 meses (para contratos de 12 meses)</p>
            <p className="text-sm text-ink-secondary">Momento ideal para o fornecedor iniciar avaliação de vantajosidade e preparar proposta de prorrogação. Para concorrentes, é o momento de mapear o contrato e preparar estratégia de entrada.</p>
          </div>
          <div>
            <p className="text-sm font-semibold text-ink">D + 10 meses (para contratos de 12 meses)</p>
            <p className="text-sm text-ink-secondary">Gestão do órgão abre processo de prorrogação ou inicia planejamento da nova licitação. Pesquisa de preços é realizada nessa fase.</p>
          </div>
          <div>
            <p className="text-sm font-semibold text-ink">D + 11 meses</p>
            <p className="text-sm text-ink-secondary">Publicação do aditivo de prorrogação (se houver) ou do edital da nova licitação. Para contratos que não serão prorrogados, o edital tende a sair nessa janela para garantir continuidade do serviço.</p>
          </div>
          <div>
            <p className="text-sm font-semibold text-ink">Prazo máximo (60 meses ou 10 anos)</p>
            <p className="text-sm text-ink-secondary">Nova licitação obrigatória. O edital deve ser publicado com antecedência suficiente para que o novo contrato entre em vigência antes do término do anterior.</p>
          </div>
        </div>
      </div>

      <h2>Fontes de dados e como acessar informações de contratos</h2>
      <p>
        Além do PNCP, outras fontes complementam o monitoramento de contratos públicos:
      </p>
      <ul>
        <li>
          <strong>ComprasGov (federal):</strong> Base histórica de contratos da União. Útil para órgãos
          federais que ainda não migraram completamente para o PNCP.
        </li>
        <li>
          <strong>Portais de transparência estaduais e municipais:</strong> Estados e municípios de maior
          porte mantêm portais próprios de contratos, com dados que podem não estar integralmente
          no PNCP.
        </li>
        <li>
          <strong>Diário Oficial:</strong> Aditivos de prorrogação e rescisões são publicados no Diário
          Oficial da União, dos estados ou dos municípios. O monitoramento do Diário Oficial é a forma
          mais abrangente de rastrear alterações contratuais.
        </li>
        <li>
          <strong>TCU — Jurisprudência:</strong> O Tribunal de Contas da União publica acórdãos sobre
          irregularidades em prorrogações. Consultar a jurisprudência do TCU ajuda a entender quais
          práticas de gestão contratual estão sob escrutínio — e o que os órgãos-alvo têm evitado.
        </li>
      </ul>
      <p>
        Para uma visão consolidada do mercado de contratos públicos, acesse o{' '}
        <Link href="/contratos" className="text-brand-blue underline hover:no-underline">
          hub de contratos públicos
        </Link>{' '}
        com dados organizados por segmento, UF e órgão. Consulte também o artigo sobre{' '}
        <Link href="/blog/contratos/limpeza" className="text-brand-blue underline hover:no-underline">
          contratos de limpeza e conservação
        </Link>{' '}
        — um dos segmentos com maior volume de prorrogações e novo processos licitatórios no país.
      </p>

      <h2>Resumo: o que a empresa B2G precisa saber</h2>
      <p>
        O prazo de vigência dos contratos públicos é, em última análise, o relógio do mercado B2G. Cada
        contrato que vence é uma oportunidade — para o fornecedor atual defender sua posição e para os
        concorrentes ingressarem na disputa. As regras da Lei 14.133/2021 tornaram o ciclo mais
        previsível: contratos de até 5 anos para serviços contínuos, prorrogáveis desde que vantajoso,
        e nova licitação obrigatória ao fim do prazo máximo.
      </p>
      <p>
        A empresa que sistematiza o monitoramento de vencimentos — cruzando dados do PNCP, acompanhando
        aditivos publicados no Diário Oficial e configurando alertas por segmento e UF — transforma
        informação pública em vantagem competitiva real. O próximo grande contrato do seu setor já está
        em andamento. A questão é se você saberá quando ele vai para disputa.
      </p>

      {/* FAQ */}
      <h2>Perguntas frequentes sobre prazo de vigência de contratos públicos</h2>

      <h3>Qual é o prazo máximo de vigência de um contrato público pela Lei 14.133/2021?</h3>
      <p>
        Pela Lei 14.133/2021, o prazo máximo de vigência de contratos de serviços e fornecimentos
        contínuos é de 5 anos (Art. 106). Para contratos com investimentos previstos no plano plurianual
        ou que envolvam tecnologia e inovação, o prazo pode chegar a 10 anos (Art. 106, §4º). Contratos
        de Parceria Público-Privada (PPP) têm prazo máximo de 35 anos, incluindo eventual prorrogação
        (Art. 106, §5º).
      </p>

      <h3>O que é prorrogação de contrato público e quando ela é permitida?</h3>
      <p>
        Prorrogação é a extensão da vigência de um contrato público já existente, sem necessidade de
        nova licitação. A prorrogação de contratos de serviços contínuos é permitida quando houver
        vantajosidade comprovada para a Administração e desde que o contratado mantenha condições
        adequadas de preço e qualidade. O prazo prorrogado não pode ultrapassar o limite máximo legal
        de 5 anos (ou 10 anos, nos casos especiais).
      </p>

      <h3>Contratos de fornecimento têm prazo máximo diferente dos contratos de serviços?</h3>
      <p>
        Sim. Contratos de fornecimento de bens não continuados ficam limitados à vigência do respectivo
        crédito orçamentário — em geral, o exercício financeiro (31 de dezembro). Contratos de serviços
        de natureza contínua seguem as regras do Art. 106 da Lei 14.133/2021, com prazo de até 5 anos
        prorrogáveis. A distinção entre fornecimento pontual e serviço contínuo é decisiva para o prazo
        máximo aplicável.
      </p>

      <h3>Qual a diferença entre prorrogação e nova licitação para o mesmo objeto?</h3>
      <p>
        Prorrogação mantém o mesmo contratado, mesmo objeto e mesmas condições, sendo ato administrativo
        bilateral. Nova licitação abre disputa no mercado, permite ingresso de concorrentes e pode
        resultar em queda de preços. A Administração deve realizar nova licitação quando o prazo máximo
        legal foi atingido, quando a prorrogação não for vantajosa, ou quando houver alteração substancial
        no objeto contratado.
      </p>

      <h3>Como monitorar contratos públicos próximos do vencimento para identificar oportunidades?</h3>
      <p>
        O PNCP disponibiliza dados de todos os contratos federais e estaduais, incluindo datas de início
        e término. É possível filtrar por órgão, UF, objeto e data de vencimento para identificar
        contratos que entrarão em processo de nova licitação. Plataformas especializadas automatizam
        esse monitoramento, alertando sobre contratos que vencem nos próximos 90 a 180 dias — janela
        ideal para preparar a proposta.
      </p>
    </>
  );
}
