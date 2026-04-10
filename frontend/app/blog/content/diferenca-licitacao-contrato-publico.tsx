import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-03: Diferença entre licitação e contrato público
 * Content cluster: contratos públicos
 * Target: ~2,500 words | Primary KW: diferença licitação contrato público
 */
export default function DiferencaLicitacaoContratoPublico() {
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
                name: 'Qual a diferença entre licitação e contrato público?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A licitação é o procedimento administrativo pelo qual o poder público seleciona a proposta mais vantajosa para celebrar um contrato. Ela começa com a publicação do edital e termina com a adjudicação e homologação do resultado. Já o contrato público é o instrumento jurídico que formaliza a relação entre o vencedor da licitação e o órgão público, estabelecendo obrigações, prazos, valores e penalidades. Em síntese: a licitação é o processo de seleção; o contrato é o acordo resultante desse processo.',
                },
              },
              {
                '@type': 'Question',
                name: 'A licitação sempre gera um contrato público?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não necessariamente. Em casos de dispensa ou inexigibilidade de licitação (arts. 74 e 79 da Lei 14.133/2021), o contrato pode ser firmado diretamente sem processo licitatório prévio. Além disso, uma licitação pode ser revogada ou anulada antes de chegar à fase contratual. Quando concluída regularmente, porém, a licitação sempre culmina em um contrato ou instrumento equivalente (nota de empenho, carta-contrato).',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais são as modalidades de licitação previstas na Lei 14.133/2021?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 (Nova Lei de Licitações) prevê cinco modalidades: pregão (bens e serviços comuns), concorrência (obras, serviços especiais e concessões), concurso (trabalho técnico, científico ou artístico), leilão (alienação de bens) e diálogo competitivo (contratações inovadoras). A tomada de preços e o convite, previstos na Lei 8.666/1993, foram extintos para a maioria dos órgãos que já adotaram a nova lei.',
                },
              },
              {
                '@type': 'Question',
                name: 'Por quanto tempo um contrato público pode ser prorrogado?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Depende do tipo de contrato. Contratos de serviços contínuos podem ser prorrogados por até 5 anos (art. 106 da Lei 14.133/2021), podendo chegar a 10 anos em casos específicos. Contratos de fornecimento têm prazo máximo de 1 ano, prorrogável por igual período. Contratos de obras seguem o cronograma físico-financeiro, sem prazo máximo genérico, mas com restrições para aditivos acima de 25% do valor original. Contratos de serviços regulados e concessões podem ter até 35 anos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Onde posso consultar licitações e contratos públicos em andamento?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O Portal Nacional de Contratações Públicas (PNCP) é o repositório oficial e obrigatório para todos os órgãos federais, estaduais e municipais que adotaram a Lei 14.133/2021. Nele é possível pesquisar editais de licitação em andamento, contratos firmados, atas de registro de preços e aditivos. Ferramentas como o SmartLic agregam e classificam esses dados com inteligência artificial, facilitando o monitoramento setorial.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Para quem atua ou quer atuar no mercado de compras públicas, confundir licitação com
        contrato público é um erro que custa oportunidades — e, às vezes, custa multas. Os dois
        conceitos descrevem momentos distintos de uma mesma cadeia:{' '}
        <strong>a licitação é o procedimento de seleção; o contrato é o compromisso legal que
        nasce do seu resultado.</strong> Entender onde um termina e o outro começa, quais normas
        regem cada fase e como monitorar ambos no{' '}
        <Link href="/licitacoes">portal de licitações</Link> e no{' '}
        <Link href="/contratos">portal de contratos</Link> é o ponto de partida para qualquer
        estratégia de negócios com o governo.
      </p>

      <h2>Definições: o que é licitação e o que é contrato público</h2>
      <p>
        A <strong>licitação</strong> é o procedimento administrativo formal pelo qual a Administração
        Pública seleciona a proposta mais vantajosa para a celebração de um contrato. Está definida
        no art. 1º da <strong>Lei 14.133/2021</strong> (Nova Lei de Licitações e Contratos
        Administrativos) como o conjunto de atos destinados a garantir a observância do princípio
        constitucional da isonomia, a seleção da proposta mais vantajosa para a administração e a
        promoção do desenvolvimento nacional sustentável.
      </p>
      <p>
        O <strong>contrato público</strong>, por sua vez, é o instrumento jurídico que formaliza
        as obrigações recíprocas entre o poder público e o particular vencedor da licitação. O
        art. 89 da Lei 14.133/2021 estabelece que os contratos de que trata a lei regulam as
        obrigações das partes, os prazos de execução, a forma de pagamento, as hipóteses de
        reajuste, as sanções por inadimplência e as condições de rescisão. É, em essência, o
        compromisso que transforma o vencedor da licitação em fornecedor efetivo do Estado.
      </p>
      <p>
        A distinção prática é direta: durante a licitação, nenhuma empresa tem direito adquirido
        ao contrato. O edital pode ser revogado, o certame pode ser suspenso e a proposta mais
        barata pode ser desclassificada por irregularidade documental. Só depois da{' '}
        <strong>adjudicação</strong> (atribuição formal do objeto ao vencedor) e da{' '}
        <strong>homologação</strong> (ato de aprovação do procedimento pela autoridade competente)
        é que o direito ao contrato se consolida — e mesmo assim, o contrato ainda precisa ser
        assinado dentro do prazo legal.
      </p>

      <h2>A cadeia completa: do edital ao contrato</h2>
      <p>
        A relação entre licitação e contrato segue uma sequência lógica e obrigatória. Conhecer
        cada etapa é fundamental para saber em que momento monitorar, participar e agir:
      </p>

      {/* Timeline box */}
      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-4">Fase 1 — Licitação (processo de seleção)</h3>
        <ol className="space-y-3 text-sm">
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">1.</span>
            <span>
              <strong>Planejamento e pesquisa de preços:</strong> o órgão define o objeto,
              realiza estudos técnicos e levanta preços de mercado para fixar o valor estimado.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">2.</span>
            <span>
              <strong>Elaboração e publicação do edital:</strong> instrumento convocatório
              publicado no PNCP (obrigatório desde 2023 para órgãos federais e grande parte dos
              estaduais e municipais), contendo todas as condições da contratação.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">3.</span>
            <span>
              <strong>Recebimento e julgamento de propostas:</strong> as empresas habilitadas
              apresentam suas propostas de preço; a comissão julga conforme o critério definido
              no edital (menor preço, melhor técnica, técnica e preço).
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">4.</span>
            <span>
              <strong>Habilitação:</strong> verificação dos documentos do vencedor — regularidade
              fiscal, trabalhista e previdenciária, capacidade técnica e econômico-financeira
              (arts. 62 a 70 da Lei 14.133/2021).
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">5.</span>
            <span>
              <strong>Adjudicação e homologação:</strong> o objeto é atribuído ao vencedor
              (adjudicação) e o procedimento licitatório é validado pela autoridade superior
              (homologação). A partir daí, a empresa tem direito subjetivo ao contrato.
            </span>
          </li>
        </ol>
        <h3 className="text-lg font-semibold mt-6 mb-4">Fase 2 — Contrato (execução)</h3>
        <ol className="space-y-3 text-sm" start={6}>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">6.</span>
            <span>
              <strong>Assinatura do contrato:</strong> deve ocorrer dentro do prazo previsto no
              edital (geralmente 5 dias úteis após a convocação). A recusa injustificada sujeita
              o vencedor a sanções.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">7.</span>
            <span>
              <strong>Publicação no PNCP:</strong> obrigatória para conferir eficácia ao contrato
              (art. 94 da Lei 14.133/2021). Contratos não publicados no prazo legal estão sujeitos
              à anulação.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">8.</span>
            <span>
              <strong>Execução e fiscalização:</strong> o fornecedor executa o objeto; o órgão
              fiscaliza e atesta o recebimento. O fiscal do contrato é designado formalmente
              (art. 117) e responde pela conformidade da entrega.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="flex-shrink-0 font-bold text-brand">9.</span>
            <span>
              <strong>Pagamento e encerramento:</strong> o pagamento deve ocorrer em até 30 dias
              após o ateste (art. 141). O contrato é encerrado com o recebimento definitivo do
              objeto e, quando aplicável, a liberação de garantias.
            </span>
          </li>
        </ol>
      </div>

      <h2>Modalidades de licitação: art. 28 da Lei 14.133/2021</h2>
      <p>
        O <strong>art. 28</strong> da Lei 14.133/2021 estabelece as cinco modalidades licitatórias
        vigentes no regime atual. Cada modalidade tem escopo específico e não pode ser utilizada
        fora dos limites legais:
      </p>

      <h3>Pregão (art. 29)</h3>
      <p>
        Modalidade obrigatória para a aquisição de bens e serviços comuns — aqueles cujos padrões
        de qualidade podem ser objetivamente definidos por edital. O pregão eletrônico é a forma
        preferencial (art. 17, §2º) e representa a maior parte das licitações publicadas no PNCP.
        O julgamento se dá pelo critério de menor preço ou maior desconto, com fase de lances em
        sessão pública. A Lei 8.666/1993 não previa o pregão — ele foi introduzido pela Lei
        10.520/2002 e incorporado à nova lei com regras aprimoradas.
      </p>

      <h3>Concorrência (art. 30)</h3>
      <p>
        Modalidade aplicável a obras, serviços especiais de engenharia, compras com critério de
        melhor técnica ou técnica e preço, e concessões de serviços públicos. É a modalidade mais
        completa em termos de exigências procedimentais e tem prazo mínimo de publicidade de 25
        dias úteis (ou 60 dias úteis para contratos de grande vulto). Substitui a antiga
        concorrência da Lei 8.666 e incorpora a tomada de preços e parte do convite para objetos
        de maior valor.
      </p>

      <h3>Concurso (art. 31)</h3>
      <p>
        Destinado à seleção de trabalho técnico, científico ou artístico. O julgamento se baseia
        em critérios de qualidade estabelecidos em regulamento específico. Não tem relação com
        concurso público para provimento de cargos — é exclusivamente para aquisição de produção
        intelectual ou artística.
      </p>

      <h3>Leilão (art. 31)</h3>
      <p>
        Utilizado para a alienação de bens móveis inservíveis, imóveis oriundos de dação em
        pagamento ou judicial, e para concessões de direito real de uso. O julgamento se dá pelo
        maior lance, acima do valor de avaliação fixado pela administração.
      </p>

      <h3>Diálogo Competitivo (art. 32)</h3>
      <p>
        Modalidade sem equivalente na Lei 8.666. Aplicável a contratações inovadoras nas quais a
        administração não consegue definir previamente a solução técnica adequada. O órgão realiza
        rodadas de diálogo com os licitantes pré-selecionados para desenvolver alternativas, e só
        então lança o edital definitivo. É comum em projetos de infraestrutura tecnológica complexa
        e parcerias público-privadas inovadoras.
      </p>

      <BlogInlineCTA slug="diferenca-licitacao-contrato-publico" campaign="contratos" />

      <h2>Tipos de contratos públicos: arts. 89 a 91 da Lei 14.133/2021</h2>
      <p>
        Os <strong>arts. 89 a 91</strong> da Lei 14.133/2021 disciplinam os contratos
        administrativos. Diferente das modalidades de licitação (que classificam o procedimento),
        os tipos de contrato classificam o <em>objeto</em> da relação jurídica:
      </p>

      <h3>Contratos de fornecimento</h3>
      <p>
        Têm por objeto a entrega de bens. Podem ser de execução imediata (entrega em parcela
        única) ou de execução continuada (entregas periódicas ao longo da vigência). O prazo
        máximo é de 1 ano, prorrogável por igual período quando previsto no edital e demonstrada
        a vantajosidade. Para bens de natureza contínua adquiridos via Sistema de Registro de
        Preços, as regras do art. 84 prevalecem (vigência máxima de 2 anos da ARP).
      </p>

      <h3>Contratos de serviço contínuo</h3>
      <p>
        Abrangem serviços cuja interrupção comprometeria as atividades essenciais do órgão:
        limpeza, vigilância, manutenção predial, TI, call center, entre outros. O art. 106
        autoriza prazo inicial de até 5 anos, renovável até o limite de 10 anos em casos
        justificados pela natureza do objeto e pela manutenção das condições vantajosas. É o
        tipo de contrato que gera maior volume de gastos públicos continuados. Veja exemplos
        por estado em{' '}
        <Link href="/contratos/saude/SP">contratos de saúde em São Paulo</Link>.
      </p>

      <h3>Contratos de obra e serviço de engenharia</h3>
      <p>
        Destinados à construção, reforma, ampliação ou demolição de bens públicos, bem como à
        prestação de serviços especiais de engenharia. Não têm prazo máximo genérico — a vigência
        segue o cronograma físico-financeiro aprovado. Aditivos que excedam 25% do valor original
        para acréscimos de objeto (ou 50% para reformas de edifício ou equipamento) exigem
        autorização especial e são objeto de fiscalização pelo TCU. Para aprofundar, consulte o{' '}
        <Link href="/blog/contratos/engenharia">guia de contratos de engenharia</Link>.
      </p>

      <h3>Contratos de concessão e PPP</h3>
      <p>
        Regulados por legislação específica (Lei 8.987/1995 para concessões comuns; Lei 11.079/2004
        para PPPs), podem ter prazo de até 35 anos. São firmados após concorrência pública com
        critério de melhor proposta econômica. A distinção entre concessão administrativa e
        patrocinada determina quem remunera o concessionário (usuário, poder público ou ambos).
      </p>

      <h3>Ata de Registro de Preços</h3>
      <p>
        Tecnicamente não é um contrato, mas um instrumento pré-contratual: registra o preço do
        fornecedor sem obrigar o governo a comprar. Cada pedido de fornecimento emitido com base
        na ARP formaliza uma contratação individual. A vigência máxima é de 2 anos (art. 84).
        A ARP permite que outros órgãos adiram ao registro original via carona, ampliando o
        alcance do fornecedor sem custos adicionais de processo licitatório.
      </p>

      <h2>Quadro comparativo: licitação vs. contrato público</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-4">Licitação vs. Contrato Público — Comparativo</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left py-2 pr-4 font-semibold">Critério</th>
                <th className="text-left py-2 pr-4 font-semibold">Licitação</th>
                <th className="text-left py-2 font-semibold">Contrato Público</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              <tr>
                <td className="py-2 pr-4 font-medium">Natureza</td>
                <td className="py-2 pr-4">Procedimento administrativo</td>
                <td className="py-2">Instrumento jurídico bilateral</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Quem participa</td>
                <td className="py-2 pr-4">Qualquer empresa habilitada</td>
                <td className="py-2">Somente o vencedor adjudicado</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Obrigações geradas</td>
                <td className="py-2 pr-4">Nenhuma (até a adjudicação)</td>
                <td className="py-2">Entrega, pagamento, penalidades</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Prazo</td>
                <td className="py-2 pr-4">Variável (dias a meses)</td>
                <td className="py-2">1 a 35 anos (conforme tipo)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Publicidade obrigatória</td>
                <td className="py-2 pr-4 text-green-700 dark:text-green-400">Sim — PNCP + Diário Oficial</td>
                <td className="py-2 text-green-700 dark:text-green-400">Sim — PNCP (art. 94)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Pode ser cancelado?</td>
                <td className="py-2 pr-4 text-green-700 dark:text-green-400">Sim, por revogação ou anulação</td>
                <td className="py-2 text-amber-700 dark:text-amber-400">Sim, com indenizações ao contratado</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Recurso administrativo</td>
                <td className="py-2 pr-4">Sim, durante a sessão pública</td>
                <td className="py-2">Limitado (rescisão, reequilíbrio)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Penalidade por descumprimento</td>
                <td className="py-2 pr-4">Impedimento (recusa de assinar)</td>
                <td className="py-2">Multa, suspensão, declaração de inidoneidade</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Base legal principal</td>
                <td className="py-2 pr-4">Arts. 28–72 (Lei 14.133/2021)</td>
                <td className="py-2">Arts. 89–154 (Lei 14.133/2021)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <h2>Lei 8.666/1993 vs. Lei 14.133/2021: o que mudou</h2>
      <p>
        A Lei 8.666/1993, conhecida como Lei Geral de Licitações, foi revogada pela Lei
        14.133/2021 com vigência plena a partir de 30 de dezembro de 2023. Para quem monitora
        contratos públicos mais antigos ou atua em municípios que adotaram a transição tardia,
        entender as diferenças é importante:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-4">Lei 8.666/1993 vs. Lei 14.133/2021 — Principais Mudanças</h3>
        <div className="space-y-4 text-sm">
          <div>
            <p className="font-semibold text-ink">Modalidades licitatórias</p>
            <p className="text-ink-secondary mt-1">
              <span className="font-medium">Antes:</span> concorrência, tomada de preços, convite, concurso, leilão (definidas por faixa de valor).<br />
              <span className="font-medium">Agora:</span> pregão, concorrência, concurso, leilão, diálogo competitivo (definidas por natureza do objeto).
            </p>
          </div>
          <div>
            <p className="font-semibold text-ink">Prazos de serviços contínuos</p>
            <p className="text-ink-secondary mt-1">
              <span className="font-medium">Antes:</span> máximo 60 meses (5 anos), prorrogável por mais 12 meses em caso excepcional.<br />
              <span className="font-medium">Agora:</span> 5 anos, prorrogável até 10 anos em casos justificados (art. 106).
            </p>
          </div>
          <div>
            <p className="font-semibold text-ink">Publicidade e eficácia</p>
            <p className="text-ink-secondary mt-1">
              <span className="font-medium">Antes:</span> Diário Oficial + portal próprio do órgão.<br />
              <span className="font-medium">Agora:</span> PNCP como repositório centralizado e obrigatório. Contratos têm eficácia condicionada à publicação no PNCP (art. 94).
            </p>
          </div>
          <div>
            <p className="font-semibold text-ink">Catálogo de sanções</p>
            <p className="text-ink-secondary mt-1">
              <span className="font-medium">Antes:</span> advertência, multa, suspensão (até 2 anos), declaração de inidoneidade.<br />
              <span className="font-medium">Agora:</span> advertência, multa (até 30% do valor do contrato), impedimento (até 3 anos), declaração de inidoneidade (até 6 anos). Cadastro unificado no PNCP.
            </p>
          </div>
          <div>
            <p className="font-semibold text-ink">Limites de aditivos</p>
            <p className="text-ink-secondary mt-1">
              <span className="font-medium">Antes:</span> 25% para obras e serviços; 50% para reformas de equipamentos ou edifícios (art. 65, Lei 8.666).<br />
              <span className="font-medium">Agora:</span> mantidos os mesmos percentuais, com regras mais rígidas de justificativa e publicação obrigatória no PNCP (art. 124, Lei 14.133).
            </p>
          </div>
        </div>
      </div>

      <h2>Jurisprudência do TCU sobre a relação licitação-contrato</h2>
      <p>
        O Tribunal de Contas da União (TCU) tem extensa jurisprudência sobre os limites entre
        o procedimento licitatório e a execução contratual. Alguns posicionamentos relevantes
        para fornecedores:
      </p>
      <ul>
        <li>
          <strong>Acórdão 2.622/2015-Plenário:</strong> o TCU consolidou o entendimento de que
          a modificação do objeto contratual além dos limites legais configura contratação direta
          irregular, sujeita à responsabilização solidária do gestor e do contratado.
        </li>
        <li>
          <strong>Acórdão 1.214/2013-Plenário:</strong> estabeleceu que o reequilíbrio
          econômico-financeiro não pode ser utilizado para corrigir erro de precificação do
          próprio contratado — apenas desequilíbrios causados por fato externo imprevisível.
        </li>
        <li>
          <strong>Súmula TCU 269:</strong> em contratos de serviços contínuos, a remuneração
          dos empregados alocados não pode ser superior à prevista em convenção coletiva da
          categoria, salvo justificativa específica devidamente documentada.
        </li>
        <li>
          <strong>Acórdão 2.066/2017-Plenário:</strong> definiu que a publicação no Diário
          Oficial (e, agora, no PNCP) é condição de eficácia — e não mera formalidade. Contratos
          executados antes da publicação têm validade questionável, com risco de glosa dos
          pagamentos pelo controle externo.
        </li>
      </ul>
      <p>
        Esses precedentes têm peso operacional direto: compreender os limites do contrato
        firmado — e não apenas as condições do edital que o originou — é fundamental para
        evitar autuações e garantir o recebimento integral.
      </p>

      <h2>Erros comuns de quem confunde licitação com contrato</h2>
      <p>
        Na prática, a confusão entre os dois conceitos gera problemas recorrentes que custam
        tempo e dinheiro às empresas participantes:
      </p>
      <ul>
        <li>
          <strong>Mobilizar recursos antes da adjudicação:</strong> empresas que contratam
          funcionários e compram insumos imediatamente após vencer o pregão — antes da homologação
          e da assinatura do contrato — assumem risco real. O certame pode ser impugnado, o
          resultado pode ser anulado e o contrato pode não ser firmado. Aguardar a assinatura
          formal antes de mobilizar operações é prudência, não lentidão.
        </li>
        <li>
          <strong>Ignorar prazos de assinatura:</strong> após a adjudicação, o vencedor tem o
          prazo estabelecido no edital (geralmente 5 dias úteis) para assinar o contrato. A
          recusa injustificada configura descumprimento e sujeita a empresa às mesmas penalidades
          da inexecução contratual — incluindo impedimento de licitar por até 3 anos.
        </li>
        <li>
          <strong>Confundir prazo da proposta com prazo do contrato:</strong> o prazo de validade
          da proposta (até quando o preço ofertado se mantém vinculante) é diferente da vigência
          do contrato. Uma proposta válida por 60 dias pode gerar um contrato com duração de 5 anos.
        </li>
        <li>
          <strong>Tratar aditivos como relicitação:</strong> aditivos contratuais (de prazo ou
          valor) são alterações do contrato já firmado — não requerem nova licitação, mas têm
          limites legais rígidos (art. 124 da Lei 14.133/2021). Ultrapassar esses limites pode
          gerar rescisão e responsabilização do gestor e do contratado.
        </li>
      </ul>

      <h2>Como monitorar licitações e contratos públicos</h2>
      <p>
        Para empresas que atuam ou querem atuar no mercado B2G, o monitoramento sistemático
        precisa cobrir dois fluxos distintos:
      </p>

      <h3>Monitorar licitações (fase pré-contratual)</h3>
      <p>
        A principal fonte é o <strong>PNCP</strong>, onde todos os editais federais e a maioria
        dos estaduais e municipais são publicados. A busca pode ser feita por órgão, modalidade,
        unidade federativa, período de publicação e situação (aberto, suspenso, revogado).
      </p>
      <p>
        O desafio não é o acesso aos dados — é a relevância. Um fabricante de equipamentos de
        diagnóstico médico que monitora o PNCP sem filtros vai se deparar com milhares de pregões
        de material de limpeza, uniformes e combustível. Ferramentas com classificação setorial
        por inteligência artificial — como o SmartLic — resolvem esse problema ao filtrar apenas
        os editais com probabilidade real de relevância para o setor do usuário.
      </p>

      <h3>Monitorar contratos (fase pós-licitatória)</h3>
      <p>
        A consulta a contratos firmados serve a dois propósitos estratégicos: (1) identificar
        quais empresas concorrentes foram contratadas, em que valor e por qual prazo — gerando
        inteligência competitiva; (2) monitorar contratos próximos do vencimento para antecipar
        novas licitações do mesmo objeto. Contratos com vigência expirando em 90 a 180 dias
        geralmente indicam uma nova licitação iminente — e o melhor momento para se preparar.
      </p>
      <p>
        O{' '}
        <Link href="/contratos">portal de contratos públicos</Link> do SmartLic consolida esses
        dados por setor e UF, facilitando o rastreamento de oportunidades emergentes com base
        no histórico contratual.
      </p>

      {/* Info box */}
      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-ink mb-2">
          O que o PNCP publica — e o que você pode consultar gratuitamente
        </p>
        <ul className="text-sm text-ink-secondary space-y-2">
          <li>
            <span className="font-medium text-ink">Licitações:</span> edital completo, atas de sessão,
            resultado por fornecedor, recursos interpostos e decisões.
          </li>
          <li>
            <span className="font-medium text-ink">Contratos:</span> instrumento contratual, valor,
            vigência, CNPJ do contratado, fiscal designado e histórico de aditivos.
          </li>
          <li>
            <span className="font-medium text-ink">Atas de Registro de Preços:</span> preço registrado
            por item, quantidades, órgão gerenciador e adesões por carona.
          </li>
          <li>
            <span className="font-medium text-ink">Sanções:</span> empresas impedidas ou declaradas
            inidôneas, com prazo e fundamentação.
          </li>
        </ul>
        <p className="text-sm text-ink-secondary mt-3">
          Fonte: <strong>PNCP — pncp.gov.br</strong>, obrigatório desde 30/12/2023 (Lei 14.133/2021, art. 174).
        </p>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Qual a diferença entre licitação e contrato público?</h3>
      <p>
        A licitação é o procedimento administrativo pelo qual o poder público seleciona a proposta
        mais vantajosa para celebrar um contrato. Ela começa com a publicação do edital e termina
        com a adjudicação e homologação do resultado. O contrato público é o instrumento jurídico
        que formaliza a relação entre o vencedor e o órgão, estabelecendo obrigações, prazos,
        valores e penalidades. Em síntese: a licitação é o processo de seleção; o contrato é o
        acordo resultante desse processo.
      </p>

      <h3>A licitação sempre gera um contrato público?</h3>
      <p>
        Não necessariamente. Em casos de dispensa ou inexigibilidade de licitação (arts. 74 e 79
        da Lei 14.133/2021), o contrato pode ser firmado diretamente sem processo licitatório
        prévio. Além disso, uma licitação pode ser revogada ou anulada antes de chegar à fase
        contratual. Quando concluída regularmente, a licitação sempre culmina em um contrato ou
        instrumento equivalente (nota de empenho, carta-contrato, ordem de fornecimento).
      </p>

      <h3>Quais são as modalidades de licitação previstas na Lei 14.133/2021?</h3>
      <p>
        A Lei 14.133/2021 prevê cinco modalidades: pregão (bens e serviços comuns),
        concorrência (obras, serviços especiais e concessões), concurso (trabalho técnico,
        científico ou artístico), leilão (alienação de bens) e diálogo competitivo
        (contratações inovadoras). A tomada de preços e o convite, previstos na Lei 8.666/1993,
        foram extintos para os órgãos que já adotaram a nova lei.
      </p>

      <h3>Por quanto tempo um contrato público pode ser prorrogado?</h3>
      <p>
        Depende do tipo de contrato. Contratos de serviços contínuos podem ser prorrogados por
        até 5 anos (art. 106 da Lei 14.133/2021), podendo chegar a 10 anos em casos específicos.
        Contratos de fornecimento têm prazo máximo de 1 ano, prorrogável por igual período.
        Contratos de obras seguem o cronograma físico-financeiro, sem prazo máximo genérico,
        mas com restrições para aditivos acima de 25% do valor original. Contratos de concessão
        e PPP podem ter vigência de até 35 anos.
      </p>

      <h3>Onde posso consultar licitações e contratos públicos em andamento?</h3>
      <p>
        O Portal Nacional de Contratações Públicas (PNCP) é o repositório oficial e obrigatório
        para todos os órgãos que adotaram a Lei 14.133/2021. Nele é possível pesquisar editais
        de licitação em andamento, contratos firmados, atas de registro de preços e aditivos.
        Ferramentas como o SmartLic agregam e classificam esses dados com inteligência artificial,
        facilitando o monitoramento por setor, região e tipo de objeto. Acesse o{' '}
        <Link href="/licitacoes">portal de licitações</Link> ou o{' '}
        <Link href="/contratos">portal de contratos</Link> para começar.
      </p>
    </>
  );
}
