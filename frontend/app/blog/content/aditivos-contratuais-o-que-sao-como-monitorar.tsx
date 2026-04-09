import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-06: Aditivos contratuais: O que são e como monitorar
 * Content cluster: contratos públicos
 * Target: ~2,500 words | Primary KW: aditivos contratuais licitação
 */
export default function AditivosContratuaisOQueSaoComoMonitorar() {
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
                name: 'O que é um aditivo contratual em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Aditivo contratual é o instrumento formal que promove alterações em contratos administrativos já celebrados, modificando prazo, valor, escopo ou condições de execução. Previsto nos arts. 124 a 136 da Lei 14.133/2021, o aditivo deve ser justificado por interesse público, assinado pelas partes e publicado no Portal Nacional de Contratações Públicas (PNCP). Sem aditivo formalizado, qualquer alteração contratual é irregular e pode ensejar responsabilização do gestor.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o limite percentual de aditivo contratual na Lei 14.133/2021?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 estabelece no art. 125 o limite de 25% do valor inicial atualizado do contrato para acréscimos ou supressões em obras, serviços e compras. Para obras e serviços de engenharia — reforma de equipamento ou benfeitoria em imóvel existente —, o limite de acréscimo sobe para 50% (art. 125, §2º). Supressões podem ultrapassar os 25% quando resultarem de acordo entre as partes (art. 125, §3º). Esses percentuais são calculados sobre o valor original do contrato, não sobre o valor do último aditivo.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quando um aditivo contratual é sinal de alerta?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'São sinais de alerta: aditivos sucessivos que, somados, se aproximam ou excedem os limites legais (estratégia de "aditivos fracionados"); aditivos de valor que ampliam o escopo original sem justificativa técnica adequada; aditivos de prazo recorrentes sem evidência de caso fortuito ou força maior; e aditivos celebrados próximos ao vencimento do contrato original sem motivação clara. O TCU identifica como irregularidade a utilização de aditivos para compensar planejamento inadequado na fase de licitação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como monitorar aditivos contratuais no PNCP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O Portal Nacional de Contratações Públicas (PNCP) exige a publicação de todos os aditivos contratuais por parte dos órgãos federais, estaduais e municipais vinculados à Lei 14.133/2021. É possível pesquisar contratos por CNPJ do fornecedor, CNPJ do órgão, número do contrato ou período. Ferramentas como o SmartLic automatizam esse monitoramento, consolidando alertas de novos aditivos publicados referentes a contratos de interesse da empresa.',
                },
              },
              {
                '@type': 'Question',
                name: 'O TCU pode anular aditivos contratuais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O TCU, no exercício do controle externo, pode determinar a nulidade de aditivos que excedam os limites legais, que modifiquem o objeto contratual a ponto de descaracterizá-lo (vedado pelo art. 124, §4º da Lei 14.133/2021) ou que sejam celebrados sem justificativa suficiente. Os Acórdãos 1977/2013, 2836/2015 e 1443/2020 do TCU são referências centrais sobre irregularidades em aditivos. A nulidade pode gerar restituição de valores e responsabilização solidária de gestores e contratados.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Aditivos contratuais são parte rotineira da execução de contratos públicos no Brasil — e uma das áreas com maior índice de irregularidades apontadas pelo TCU. Entender o que são, quais os limites legais impostos pela Lei 14.133/2021 e como monitorá-los no PNCP é essencial tanto para empresas fornecedoras quanto para gestores públicos que buscam compliance e transparência.
      </p>

      <h2>O que são aditivos contratuais</h2>
      <p>
        Aditivo contratual é o instrumento jurídico pelo qual as partes — Administração Pública e contratado — promovem alterações formais em um contrato administrativo vigente. Essas alterações podem envolver prazo de execução, valor contratual, escopo do objeto ou condições de entrega, sempre desde que haja justificativa de interesse público e observância dos limites legais.
      </p>
      <p>
        No regime da <strong>Lei 14.133/2021</strong> (Nova Lei de Licitações e Contratos), os aditivos contratuais são disciplinados nos arts. 124 a 136, que tratam das alterações unilaterais e bilaterais de contratos administrativos. A exigência de formalidade é absoluta: qualquer modificação deve ser reduzida a termo, assinada pelas partes e publicada no <strong>Portal Nacional de Contratações Públicas (PNCP)</strong> para produzir efeitos.
      </p>
      <p>
        Diferentemente do contrato original — cujas cláusulas foram objeto de licitação e concorrência —, o aditivo é celebrado de forma direta entre as partes. Justamente por isso, é um instrumento que demanda atenção redobrada dos órgãos de controle: quando mal utilizado, pode subverter o resultado da licitação original e gerar vantagem indevida ao contratado.
      </p>

      <h2>Base legal: Arts. 124 a 136 da Lei 14.133/2021</h2>
      <p>
        A Lei 14.133/2021 consolidou e ampliou a regulação sobre alterações contratuais em relação ao regime anterior da Lei 8.666/1993. Os dispositivos centrais são:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Mapa dos Arts. 124 a 136 — Alterações Contratuais</h3>
        <ul className="space-y-3 text-sm">
          <li>
            <strong>Art. 124 — Hipóteses de alteração:</strong> Define as situações em que o contrato pode ser alterado unilateralmente pela Administração (adequação técnica do projeto, variação de quantidade) ou bilateralmente com o contratado (substituição de garantia, modificação do regime de execução, alteração da forma de pagamento, reequilíbrio econômico-financeiro).
          </li>
          <li>
            <strong>Art. 124, §4º — Vedação à descaracterização do objeto:</strong> Proíbe alterações que modifiquem o objeto do contrato a ponto de transformá-lo em outro de natureza e finalidade distintas. É uma das limitações mais frequentemente descumpridas e apontadas pelo TCU.
          </li>
          <li>
            <strong>Art. 125 — Limites percentuais:</strong> Fixa em 25% o limite para acréscimos e supressões de obras, serviços e compras. Para reformas, o acréscimo pode chegar a 50% (§2º). Supressões acima de 25% são permitidas por acordo entre as partes (§3º).
          </li>
          <li>
            <strong>Art. 131 — Reequilíbrio econômico-financeiro:</strong> Permite a revisão do contrato quando fatos imprevisíveis ou previsíveis de consequências incalculáveis alteram a equação econômica estabelecida na proposta. Base para aditivos de valor decorrentes de variação de insumos.
          </li>
          <li>
            <strong>Art. 136 — Vigência e prorrogação:</strong> Regulamenta as hipóteses de prorrogação contratual, com limites específicos por tipo de objeto (serviços contínuos: até 10 anos; obras: até o prazo de execução).
          </li>
        </ul>
      </div>

      <p>
        A <strong>AGU</strong> publicou pareceres e orientações normativas complementares, especialmente sobre reequilíbrio econômico-financeiro e reajustamento de preços, temas que frequentemente fundamentam aditivos de valor. A Orientação Normativa AGU nº 22/2009 — ainda referenciada na prática administrativa — consolidou entendimentos sobre o tema que foram incorporados ao texto da Lei 14.133/2021.
      </p>

      <h2>Tipos de aditivos contratuais</h2>
      <p>
        Na prática, os aditivos contratuais podem ser agrupados em três categorias principais, que frequentemente se combinam em um único instrumento:
      </p>

      <h3>Aditivo de prazo</h3>
      <p>
        Prorroga a data de término da execução ou vigência do contrato. É o tipo mais comum e, em tese, o mais justificável quando a causa é externa ao contratado (atraso na liberação de área, eventos climáticos, paralisação por determinação do órgão contratante). O problema surge quando o aditivo de prazo é utilizado para encobrir atraso por ineficiência do contratado, sem aplicação das penalidades previstas no contrato.
      </p>
      <p>
        Para serviços de natureza contínua (limpeza, vigilância, TI), a Lei 14.133/2021 prevê prorrogação por até 10 anos consecutivos quando economicamente vantajosa (art. 107), com publicação de justificativa a cada renovação.
      </p>

      <h3>Aditivo de valor</h3>
      <p>
        Altera o valor total do contrato, seja por acréscimo de itens, reajuste de preços ou reequilíbrio econômico-financeiro. O limite de 25% (art. 125) incide sobre o valor inicial atualizado — incluindo reajustes contratuais já aplicados, mas excluindo os próprios aditivos anteriores de valor.
      </p>
      <p>
        Aditivos de valor por reequilíbrio econômico-financeiro são distintos dos aditivos por acréscimo de quantidade: o reequilíbrio não se sujeita ao limite de 25%, pois visa apenas recompor a equação econômica original — e não ampliar o objeto do contrato.
      </p>

      <h3>Aditivo de escopo</h3>
      <p>
        Modifica as especificações técnicas ou o conjunto de itens a ser entregue. É o tipo de maior risco jurídico, pois facilmente pode ultrapassar a vedação do art. 124, §4º — a proibição de transformar o objeto contratado em outro de natureza distinta. Um contrato de fornecimento de equipamentos de informática, por exemplo, não pode ser aditado para incluir a prestação de serviços de desenvolvimento de software, mesmo que dentro do limite de 25% de valor.
      </p>

      <h2>Limites percentuais: a regra dos 25% e os casos de 50%</h2>
      <p>
        O art. 125 da Lei 14.133/2021 estabelece os seguintes limites para alterações quantitativas (acréscimos e supressões):
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Limites de Aditivo — Art. 125 da Lei 14.133/2021</h3>
        <ul className="space-y-3 text-sm">
          <li>
            <strong>Regra geral — 25%:</strong> Obras, serviços e compras em geral. Tanto acréscimos quanto supressões estão limitados a 25% do valor inicial atualizado do contrato.
          </li>
          <li>
            <strong>Caso especial — 50% (art. 125, §2º):</strong> Reforma de equipamento ou benfeitoria em imóvel existente. O limite de acréscimo sobe para 50%, mas apenas na modalidade "reforma" — não para construção nova ou ampliação que configure nova edificação.
          </li>
          <li>
            <strong>Supressão acima de 25% (art. 125, §3º):</strong> Permitida por acordo entre as partes, sem a restrição percentual, desde que o contratado não seja prejudicado além dos limites admissíveis e que haja justificativa formal.
          </li>
          <li>
            <strong>Referência de cálculo:</strong> O percentual incide sobre o "valor inicial atualizado do contrato" — expressão que inclui reajustes de preços já aplicados, mas não os próprios aditivos de acréscimo. Na prática, o TCU tem consolidado a interpretação de que aditivos sucessivos se somam para fins de verificação do limite.
          </li>
        </ul>
      </div>

      <p>
        A verificação do limite deve considerar a soma de todos os aditivos de acréscimo celebrados ao longo do contrato — não apenas o último. A estratégia de fracionamento (celebrar múltiplos aditivos menores para não ultrapassar o limite individualmente) é expressamente condenada pelo TCU e pode configurar irregularidade grave.
      </p>

      <BlogInlineCTA slug="aditivos-contratuais-o-que-sao-como-monitorar" campaign="contratos" />

      <h2>Quando aditivos são legítimos — e quando sinalizam problemas</h2>
      <p>
        Nem todo aditivo contratual é irregular. Há situações em que a alteração do contrato é não apenas legítima, mas necessária para preservar o interesse público. A distinção está na causa e na proporcionalidade.
      </p>

      <h3>Situações que legitimam aditivos</h3>
      <p>
        São hipóteses juridicamente reconhecidas: descoberta de condições de subsolo imprevisíveis em obras de engenharia; variação extraordinária de preços de insumos (aço, combustível, energia) que descaracterize a equação econômica original; modificação do projeto pelo órgão contratante após o início da execução; e prorrogações de prazo decorrentes de atrasos causados pela própria Administração (não liberação de área, demora na emissão de licenças).
      </p>
      <p>
        Nesses casos, o aditivo é o instrumento correto para manter o equilíbrio contratual e a viabilidade da execução. A ausência do aditivo — e a consequente imposição de perdas ao contratado por fatos fora do seu controle — é que configuraria a irregularidade.
      </p>

      <h3>Red flags: sinais de alerta em aditivos</h3>
      <p>
        Os auditores do TCU e dos Tribunais de Contas estaduais aplicam critérios objetivos para identificar aditivos irregulares. Os principais sinais de alerta são:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Red Flags em Aditivos Contratuais — Critérios de Auditoria</h3>
        <ul className="space-y-3 text-sm">
          <li>
            <strong>Aditivos de prazo recorrentes sem causa externa:</strong> Prorrogações sucessivas sem evidência de eventos imprevisíveis — indicam planejamento inadequado da contratação original ou tolerância indevida com atrasos do fornecedor.
          </li>
          <li>
            <strong>Soma de aditivos próxima ao limite legal:</strong> Quando os acréscimos acumulados se aproximam de 24-25% do valor original, pode indicar fracionamento deliberado para postergar a necessidade de nova licitação.
          </li>
          <li>
            <strong>Aditivo celebrado pouco antes do vencimento:</strong> Prorrogações de contrato celebradas nos últimos dias antes do término, sem processo de renovação regular, levantam suspeita sobre a motivação real.
          </li>
          <li>
            <strong>Modificação substancial do objeto:</strong> Inclusão de itens ou serviços que alteram a natureza do que foi licitado, ainda que formalmente dentro do limite de 25% em valor.
          </li>
          <li>
            <strong>Ausência de justificativa técnica adequada:</strong> Aditivos de valor por reequilíbrio sem laudo técnico que demonstre o impacto do evento alegado sobre os custos do contratado.
          </li>
          <li>
            <strong>Benefício exclusivo ao contratado sem contrapartida:</strong> Aditivos que apenas ampliam o prazo ou o valor sem qualquer exigência de melhoria de desempenho ou entrega adicional ao órgão contratante.
          </li>
        </ul>
      </div>

      <h2>Como monitorar aditivos no PNCP</h2>
      <p>
        A Lei 14.133/2021 tornou obrigatória a publicação de todos os contratos e seus aditivos no <strong>PNCP — Portal Nacional de Contratações Públicas</strong>. Para fornecedores e consultores de licitação, isso representa uma fonte primária de inteligência competitiva: é possível monitorar o histórico contratual dos órgãos de interesse, identificar contratos próximos do vencimento ou do limite de aditivos, e mapear o comportamento dos concorrentes.
      </p>
      <p>
        No PNCP, os aditivos são publicados como documentos vinculados ao contrato original. Para monitorar, é possível buscar pelo CNPJ do órgão contratante ou pelo número do contrato. A consulta retorna todos os instrumentos publicados — inclusive os termos aditivos, termos de apostilamento e rescisões.
      </p>
      <p>
        Para fornecedores que atuam em segmentos com alta incidência de aditivos — como{' '}
        <Link href="/contratos/engenharia/SP">obras de engenharia em São Paulo</Link>{' '}
        e serviços de TI — o monitoramento automatizado é especialmente relevante. Contratos com histórico de aditivos de prazo podem sinalizar atraso na execução e proximidade de novo processo licitatório. Contratos com acréscimos próximos de 25% indicam que o órgão precisará licitar novamente em breve.
      </p>

      <p>
        Veja os contratos publicados por{' '}
        <Link href="/contratos/orgao/00394460000141">órgãos federais de referência no PNCP</Link>{' '}
        para entender o padrão de uso de aditivos em diferentes setores. O{' '}
        <Link href="/contratos">hub de contratos públicos</Link>{' '}
        consolida as principais informações sobre contratações ativas e seus históricos de alteração.
      </p>

      <h2>TCU: fiscalização e principais achados em aditivos</h2>
      <p>
        O Tribunal de Contas da União é o principal guardião da legalidade dos contratos administrativos no âmbito federal. Ao longo dos anos, o TCU consolidou uma jurisprudência robusta sobre aditivos contratuais que orienta tanto os gestores públicos quanto os fornecedores.
      </p>
      <p>
        O <strong>Acórdão 1977/2013-TCU-Plenário</strong> é referência central sobre o limite de 25% e a vedação ao fracionamento. O TCU entendeu que a soma dos aditivos ao longo do contrato deve ser considerada para verificação do limite, independentemente de terem sido celebrados em momentos distintos. O <strong>Acórdão 2836/2015-TCU-Plenário</strong> tratou especificamente de obras de engenharia com múltiplos aditivos e fixou que a caracterização de irregularidade prescinde de dolo — a simples inobservância dos limites legais já configura ilegalidade.
      </p>
      <p>
        O <strong>Acórdão 1443/2020-TCU-Plenário</strong> trouxe entendimento relevante sobre aditivos de prazo em serviços contínuos: prorrogações sucessivas sem avaliação da vantajosidade (conforme exige a Lei 14.133/2021) são irregulares, mesmo que individualmente respeitem os limites legais.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Principais Achados do TCU em Auditorias de Aditivos</h3>
        <ul className="space-y-3 text-sm">
          <li>
            <strong>Extrapolação do limite de 25%:</strong> É a irregularidade mais frequente — celebração de aditivos de acréscimo que, somados, excedem o limite legal sem autorização legal específica.
          </li>
          <li>
            <strong>Descaracterização do objeto:</strong> Modificação via aditivo que transforma o contrato em outro de natureza distinta, frustrando o caráter competitivo da licitação original.
          </li>
          <li>
            <strong>Ausência de justificativa técnica:</strong> Aditivos de valor celebrados sem laudo ou nota técnica que demonstre a necessidade e o nexo causal com o evento alegado.
          </li>
          <li>
            <strong>Prorrogações sem avaliação de vantajosidade:</strong> Renovações de serviços contínuos sem análise comparativa de mercado ou verificação das condições de execução.
          </li>
          <li>
            <strong>Aditivos sem publicação tempestiva:</strong> Instrumento assinado pelas partes mas não publicado no PNCP dentro do prazo, o que impede o controle social e viola a exigência de publicidade.
          </li>
        </ul>
      </div>

      <p>
        Para fornecedores, a jurisprudência do TCU sobre aditivos tem implicação prática direta: em caso de aditivo que o órgão contratante pretenda celebrar em desacordo com a lei, é recomendável registrar a posição por escrito antes de assinar — para evitar responsabilização solidária em eventual auditoria. Consulte o{' '}
        <Link href="/blog/contratos/engenharia">guia de contratos de engenharia</Link>{' '}
        para aprofundar o tema nos setores de maior incidência.
      </p>

      <h2>Como o SmartLic monitora aditivos contratuais</h2>
      <p>
        Para empresas que atuam no mercado B2G, monitorar manualmente dezenas ou centenas de contratos no PNCP é inviável no dia a dia. O SmartLic consolida as publicações do PNCP e entrega alertas estruturados sobre aditivos que afetam contratos de interesse — seja da própria empresa (para acompanhamento da execução e compliance), seja de concorrentes (para inteligência competitiva).
      </p>
      <p>
        O sistema identifica contratos com acréscimos próximos do limite de 25%, prorrogações recentes e histórico de aditivos — informações relevantes para antecipar licitações futuras. Empresas que monitoram o ciclo de vida dos contratos dos órgãos-alvo saem na frente no momento em que uma nova licitação é publicada, pois já conhecem o histórico de problemas e os requisitos técnicos que o órgão está buscando suprir.
      </p>
      <p>
        Para verificar o histórico contratual de um fornecedor específico e avaliar seu padrão de aditivos, é possível buscar pelo CNPJ diretamente. Como exemplo, consulte o{' '}
        <Link href="/cnpj/33000167000101">histórico de contratos de grandes fornecedores federais</Link>{' '}
        para entender o volume e a frequência de aditivos em contratos de longa duração.
      </p>

      <h2>Boas práticas para fornecedores</h2>
      <p>
        Para empresas contratadas, ter uma rotina de gestão de aditivos é tão importante quanto vencer a licitação. As principais práticas são:
      </p>
      <p>
        <strong>Monitorar os limites percentuais acumulados.</strong> Mantenha um registro interno dos aditivos já celebrados e calcule o percentual acumulado em relação ao valor original. Quando a soma se aproximar de 20%, comece a avaliar se há necessidade de novo processo licitatório para o próximo período.
      </p>
      <p>
        <strong>Documentar todas as causas de prorrogação.</strong> Para aditivos de prazo decorrentes de fatos alheios ao contratado, produza registro formal — atas de reunião, comunicações oficiais, registros fotográficos — que demonstre a causa. Essa documentação é essencial em eventual auditoria.
      </p>
      <p>
        <strong>Requerer o reequilíbrio economico-financeiro tempestivamente.</strong> O pedido de revisão de preços deve ser formalizado logo após a ocorrência do evento que o justifica — não após a conclusão do contrato. O TCU tem negado pedidos extemporâneos de reequilíbrio por entender que a inércia implica renúncia tácita.
      </p>
      <p>
        <strong>Verificar a publicação no PNCP.</strong> Após assinar o aditivo, confirme que o órgão contratante realizou a publicação no PNCP dentro do prazo previsto. A publicidade é condição de eficácia do instrumento — sem ela, o aditivo não produz efeitos em relação a terceiros.
      </p>

      <h2>Fontes e referências</h2>
      <p>
        As informações deste artigo têm como base as seguintes fontes primárias:
      </p>
      <ul>
        <li>
          <strong>Lei 14.133/2021</strong>, especialmente arts. 124 a 136 (alterações contratuais) e art. 107 (serviços contínuos). Disponível em planalto.gov.br.
        </li>
        <li>
          <strong>TCU — Acórdão 1977/2013-Plenário:</strong> Limites percentuais e vedação ao fracionamento de aditivos.
        </li>
        <li>
          <strong>TCU — Acórdão 2836/2015-Plenário:</strong> Irregularidades em obras com múltiplos aditivos de engenharia.
        </li>
        <li>
          <strong>TCU — Acórdão 1443/2020-Plenário:</strong> Aditivos de prazo em serviços contínuos e avaliação de vantajosidade.
        </li>
        <li>
          <strong>AGU — Orientação Normativa nº 22/2009:</strong> Reequilíbrio econômico-financeiro em contratos administrativos.
        </li>
        <li>
          <strong>PNCP — Portal Nacional de Contratações Públicas:</strong> pncp.gov.br — consulta pública de contratos e aditivos.
        </li>
      </ul>

      <h2>Perguntas frequentes sobre aditivos contratuais</h2>

      <h3>O que é um aditivo contratual em licitações?</h3>
      <p>
        Aditivo contratual é o instrumento formal que promove alterações em contratos administrativos já celebrados, modificando prazo, valor, escopo ou condições de execução. Previsto nos arts. 124 a 136 da Lei 14.133/2021, o aditivo deve ser justificado por interesse público, assinado pelas partes e publicado no PNCP. Sem aditivo formalizado, qualquer alteração contratual é irregular e pode ensejar responsabilização do gestor.
      </p>

      <h3>Qual o limite percentual de aditivo contratual na Lei 14.133/2021?</h3>
      <p>
        A Lei 14.133/2021 estabelece no art. 125 o limite de <strong>25% do valor inicial atualizado</strong> do contrato para acréscimos ou supressões em obras, serviços e compras. Para obras e serviços de engenharia — reforma de equipamento ou benfeitoria em imóvel existente —, o limite de acréscimo sobe para <strong>50%</strong> (art. 125, §2º). Supressões podem ultrapassar os 25% por acordo entre as partes (art. 125, §3º). Esses percentuais são calculados sobre o valor original do contrato, não sobre o valor do último aditivo.
      </p>

      <h3>Quando um aditivo contratual é sinal de alerta?</h3>
      <p>
        São sinais de alerta: aditivos sucessivos que, somados, se aproximam ou excedem os limites legais; aditivos de valor que ampliam o escopo original sem justificativa técnica adequada; aditivos de prazo recorrentes sem evidência de caso fortuito ou força maior; e aditivos celebrados próximos ao vencimento do contrato sem motivação clara. O TCU identifica como irregularidade a utilização de aditivos para compensar planejamento inadequado na fase de licitação.
      </p>

      <h3>Como monitorar aditivos contratuais no PNCP?</h3>
      <p>
        O PNCP exige a publicação de todos os aditivos contratuais pelos órgãos vinculados à Lei 14.133/2021. É possível pesquisar contratos por CNPJ do fornecedor, CNPJ do órgão, número do contrato ou período. O{' '}
        <Link href="/contratos">hub de contratos públicos</Link>{' '}
        consolida essas informações. Ferramentas como o SmartLic automatizam o monitoramento, gerando alertas sobre novos aditivos publicados em contratos de interesse.
      </p>

      <h3>O TCU pode anular aditivos contratuais?</h3>
      <p>
        Sim. O TCU pode determinar a nulidade de aditivos que excedam os limites legais, que modifiquem o objeto contratual a ponto de descaracterizá-lo (vedado pelo art. 124, §4º da Lei 14.133/2021) ou que sejam celebrados sem justificativa suficiente. Os Acórdãos 1977/2013, 2836/2015 e 1443/2020 do TCU são referências centrais. A nulidade pode gerar restituição de valores e responsabilização solidária de gestores e contratados.
      </p>
    </>
  );
}
