import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-04: Como verificar se uma empresa tem contratos com o governo
 * Content cluster: contratos públicos
 * Target: ~2,800 words | Primary KW: verificar empresa contratos governo
 */
export default function ComoVerificarEmpresaContratosGoverno() {
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
                name: 'Como verificar se uma empresa tem contratos com o governo?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'É possível verificar contratos governamentais de qualquer empresa pelo PNCP (Portal Nacional de Contratações Públicas) ou pelo Portal da Transparência, buscando pelo CNPJ do fornecedor. Plataformas como o SmartLic consolidam essas informações em uma única visão, incluindo histórico de valores, órgãos contratantes e aditivos.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é o PNCP e como usá-lo para pesquisar contratos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O PNCP (Portal Nacional de Contratações Públicas) é o repositório oficial obrigatório, criado pela Lei 14.133/2021, onde todos os órgãos da União, estados e municípios devem publicar contratos. Para pesquisar, acesse pncp.gov.br, vá em "Contratos" e filtre pelo CNPJ do fornecedor desejado.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais informações estão disponíveis nos contratos públicos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os contratos públicos trazem: valor total e parcelas, nome do fornecedor e CNPJ, órgão contratante, objeto (descrição do bem ou serviço), datas de vigência, modalidade de licitação, número do processo e eventuais aditivos com justificativas e novos valores.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como interpretar aditivos em contratos governamentais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Aditivos são alterações formais ao contrato original. Podem prorrogar prazo, acrescentar ou reduzir valor (limitado a 25% para obras e serviços, conforme a Lei 14.133/2021), ou alterar o objeto. Contratos com muitos aditivos de valor merecem atenção: pode indicar subprecificação inicial ou execução deficiente.',
                },
              },
              {
                '@type': 'Question',
                name: 'Por que verificar contratos públicos de um concorrente ou parceiro?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A verificação de contratos públicos serve a múltiplos fins: due diligence antes de parcerias, inteligência competitiva (identificar em quais órgãos e com quais valores o concorrente atua), qualificação de leads B2G, auditorias de conformidade e avaliação de capacidade técnica e financeira de fornecedores.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Verificar se uma empresa tem contratos com o governo é um procedimento cada vez mais
        estratégico no mercado B2G brasileiro. Seja para avaliar um concorrente, qualificar um
        potencial parceiro ou realizar due diligence antes de uma negociação, o histórico de
        contratos públicos de um fornecedor é um dos dados mais ricos e confiáveis disponíveis
        em fontes abertas. Este guia apresenta três métodos práticos — PNCP, Portal da
        Transparência e SmartLic — para que você saiba exatamente onde buscar, o que interpretar
        e quais sinais de alerta observar.
      </p>

      {/* Section 1: Por que verificar */}
      <h2>Por que verificar contratos públicos de uma empresa?</h2>
      <p>
        O Brasil registra anualmente mais de R$ 800 bilhões em contratações públicas, distribuídas
        entre União, estados e municípios. Todos esses contratos são públicos por determinação
        constitucional e pela Lei de Acesso à Informação (Lei 12.527/2011, a LAI), o que significa
        que qualquer pessoa pode consultá-los sem necessidade de cadastro ou justificativa.
      </p>
      <p>
        Esse volume de dados cria oportunidades concretas para empresas que operam no mercado
        governamental:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3 text-base">
          Principais casos de uso para consulta de contratos
        </h3>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong className="text-ink">Due diligence de parceiros:</strong> antes de firmar uma
            parceria ou subcontratação, verifique se o potencial parceiro tem experiência real e
            comprovada com órgãos públicos.
          </li>
          <li>
            <strong className="text-ink">Inteligência competitiva:</strong> identifique em quais
            órgãos seus concorrentes já atuam, com quais valores e em que condições, para definir
            onde focar seus esforços comerciais.
          </li>
          <li>
            <strong className="text-ink">Qualificação de leads B2G:</strong> ao prospectar clientes
            que vendem ao governo, o histórico de contratos revela o porte real do comprador e seu
            potencial de compra.
          </li>
          <li>
            <strong className="text-ink">Auditoria de fornecedores:</strong> gestores públicos e
            compliance officers verificam contratos de fornecedores para prevenir irregularidades.
          </li>
          <li>
            <strong className="text-ink">Avaliação de capacidade técnica:</strong> acervos de
            contratos anteriores demonstram experiência setorial — fundamental em licitações que
            exigem qualificação técnica.
          </li>
        </ul>
      </div>

      <p>
        A transparência das contratações públicas é garantida especialmente pela Nova Lei de
        Licitações (Lei 14.133/2021), que tornou obrigatória a publicação no PNCP de todos os
        contratos celebrados por entes federais, estaduais e municipais a partir de sua
        implementação progressiva. O resultado prático é que o Brasil dispõe hoje de um dos
        sistemas de transparência de compras governamentais mais abrangentes da América Latina.
      </p>

      {/* Section 2: Método 1 — PNCP */}
      <h2>Método 1: PNCP — a fonte oficial e mais completa</h2>
      <p>
        O Portal Nacional de Contratações Públicas (PNCP) é o repositório centralizado criado pela
        Lei 14.133/2021. Todos os órgãos e entidades da administração pública direta e indireta
        são obrigados a publicar seus contratos na plataforma, o que a torna a fonte mais
        abrangente para pesquisar o histórico de um fornecedor.
      </p>

      <h3>Passo a passo no PNCP</h3>
      <ol>
        <li>
          Acesse <strong>pncp.gov.br</strong> e clique em &quot;Contratos&quot; no menu principal.
        </li>
        <li>
          No campo de busca, selecione a opção <strong>&quot;CNPJ do Fornecedor&quot;</strong> e
          insira o CNPJ sem pontuação (apenas os 14 dígitos).
        </li>
        <li>
          Aplique filtros de período para delimitar o intervalo de consulta — por padrão, o PNCP
          retorna os contratos mais recentes.
        </li>
        <li>
          Cada resultado exibe: número do contrato, órgão contratante, objeto, valor global, data
          de assinatura e vigência.
        </li>
        <li>
          Clique no contrato para acessar o detalhamento completo, incluindo documentos anexos e
          histórico de aditivos.
        </li>
      </ol>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-2 text-base">Exemplo prático: Petrobras como fornecedora</h3>
        <p className="text-sm text-ink-secondary mb-3">
          Quer ver todos os contratos firmados pela Petrobras com órgãos públicos? Utilize o CNPJ
          33.000.167/0001-01. No SmartLic, você pode acessar o perfil consolidado diretamente em:
        </p>
        <Link
          href="/cnpj/33000167000101"
          className="inline-block text-sm font-medium text-brand-primary hover:underline"
        >
          smartlic.tech/cnpj/33000167000101 — Perfil Petrobras no governo
        </Link>
      </div>

      <p>
        O PNCP apresenta limitações importantes que o usuário deve conhecer. A cobertura é mais
        completa para contratações federais e para municípios que já migraram para o sistema. Alguns
        contratos mais antigos, celebrados sob a Lei 8.666/1993, podem não estar disponíveis.
        Além disso, a interface de busca do PNCP não permite cruzamentos complexos nem exportação
        em lote — para análises mais sofisticadas, ferramentas especializadas são mais adequadas.
      </p>

      {/* Section 3: Método 2 — Portal da Transparência */}
      <h2>Método 2: Portal da Transparência do Governo Federal</h2>
      <p>
        O Portal da Transparência (transparencia.gov.br), mantido pela Controladoria-Geral da União
        (CGU), é especialmente indicado para contratos do Governo Federal. Sua base de dados inclui
        contratos desde 1996, o que o torna superior ao PNCP em profundidade histórica para o
        âmbito federal.
      </p>

      <h3>Passo a passo no Portal da Transparência</h3>
      <ol>
        <li>
          Acesse <strong>transparencia.gov.br</strong> e navegue até
          &quot;Beneficiários&gt;Contratos&quot; ou use o caminho direto em
          &quot;Gastos&gt;Contratos e Convênios&quot;.
        </li>
        <li>
          No campo de pesquisa de favorecido, insira o CNPJ ou razão social da empresa que deseja
          investigar.
        </li>
        <li>
          Filtre por período, órgão contratante (UG/UASG), modalidade ou faixa de valor conforme
          necessário.
        </li>
        <li>
          O sistema retorna uma lista com: número do contrato, órgão, objeto resumido, valor
          original, valor atual (com aditivos) e situação (vigente ou encerrado).
        </li>
        <li>
          Clique em &quot;Detalhes&quot; para ver o histórico completo de empenhos e pagamentos
          realizados — dado ausente no PNCP.
        </li>
      </ol>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-2 text-base">
          Diferencial: empenhos e pagamentos realizados
        </h3>
        <p className="text-sm text-ink-secondary">
          Uma vantagem exclusiva do Portal da Transparência federal é a visibilidade sobre o
          fluxo financeiro real: não apenas o valor contratado, mas quanto efetivamente foi
          empenhado e pago a cada fornecedor. Isso permite saber se um contrato de R$ 5 milhões
          foi integralmente executado ou apenas parcialmente liquidado — informação crítica para
          análise de capacidade financeira e de execução.
        </p>
      </div>

      <p>
        O Portal da Transparência cobre apenas contratos do Executivo Federal. Para estados e
        municípios, cada ente tem seu próprio portal de transparência — o que torna a pesquisa
        fragmentada quando o objetivo é obter uma visão nacional do fornecedor.
      </p>

      {/* Inline CTA at ~40% */}
      <BlogInlineCTA slug="como-verificar-empresa-contratos-governo" campaign="contratos" />

      {/* Section 4: Método 3 — SmartLic */}
      <h2>Método 3: SmartLic — visão consolidada por CNPJ</h2>
      <p>
        Para profissionais que realizam análise de fornecedores com frequência, a consulta manual
        em múltiplos portais é ineficiente. O SmartLic agrega dados do PNCP e de outras fontes
        oficiais em uma interface única, disponível na rota{' '}
        <Link href="/cnpj/33000167000101" className="text-brand-primary hover:underline">
          /cnpj/[cnpj]
        </Link>
        , que entrega o perfil completo de um fornecedor no mercado governamental.
      </p>

      <h3>O que o perfil de fornecedor no SmartLic inclui</h3>
      <ul>
        <li>
          <strong>Histórico de contratos agregado:</strong> todos os contratos localizados nas
          fontes oficiais, com valor original, valor atualizado por aditivos e status atual.
        </li>
        <li>
          <strong>Distribuição por órgão:</strong> quais entidades públicas mais contrataram o
          fornecedor e em que volume financeiro.
        </li>
        <li>
          <strong>Distribuição geográfica:</strong> em quais estados o fornecedor tem maior presença
          contratual, útil para avaliar cobertura regional.
        </li>
        <li>
          <strong>Setores de atuação:</strong> classificação automática dos contratos por setor
          (TI, construção, saúde, etc.) com base no objeto contratado.
        </li>
        <li>
          <strong>Linha do tempo:</strong> evolução do volume contratual ao longo dos anos, que
          revela tendências de crescimento ou retração do fornecedor no mercado público.
        </li>
      </ul>

      <p>
        Para pesquisar fornecedores em um órgão específico, o SmartLic também disponibiliza a visão
        por órgão contratante, como em{' '}
        <Link href="/contratos/orgao/00394460000141" className="text-brand-primary hover:underline">
          /contratos/orgao/00394460000141
        </Link>
        , onde é possível identificar todos os fornecedores que atendem aquele órgão e os
        respectivos contratos ativos.
      </p>

      {/* Section 5: Dados disponíveis */}
      <h2>Quais dados estão disponíveis nos contratos públicos?</h2>
      <p>
        A Lei 14.133/2021 e a LAI garantem que os contratos públicos sejam disponibilizados com
        um conjunto mínimo de informações. Na prática, os dados variam conforme o portal e o ente
        federativo, mas os campos abaixo são universalmente exigidos:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3 text-base">Campos obrigatórios em contratos públicos</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <p className="text-xs font-semibold text-ink uppercase tracking-wide mb-1">Identificação</p>
            <ul className="text-sm text-ink-secondary space-y-1">
              <li>Número do contrato</li>
              <li>CNPJ e razão social do fornecedor</li>
              <li>Órgão e unidade contratante</li>
              <li>Número do processo licitatório</li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-ink uppercase tracking-wide mb-1">Financeiro</p>
            <ul className="text-sm text-ink-secondary space-y-1">
              <li>Valor global original</li>
              <li>Valor atualizado (com aditivos)</li>
              <li>Dotação orçamentária</li>
              <li>Forma de pagamento</li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-ink uppercase tracking-wide mb-1">Vigência</p>
            <ul className="text-sm text-ink-secondary space-y-1">
              <li>Data de assinatura</li>
              <li>Data de início da vigência</li>
              <li>Data de término previsto</li>
              <li>Situação atual</li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-ink uppercase tracking-wide mb-1">Objeto</p>
            <ul className="text-sm text-ink-secondary space-y-1">
              <li>Descrição do objeto contratado</li>
              <li>Modalidade de licitação</li>
              <li>Catmat/Catser (código do bem)</li>
              <li>Histórico de aditivos</li>
            </ul>
          </div>
        </div>
      </div>

      <p>
        Além desses campos, contratos federais registrados no SIAFI disponibilizam também os dados
        de empenho e liquidação, que permitem rastrear cada pagamento efetuado ao fornecedor. Esse
        nível de detalhe é exclusivo do Governo Federal — estados e municípios raramente publicam
        dados financeiros com essa granularidade.
      </p>

      {/* Section 6: Interpretar dados */}
      <h2>Como interpretar os dados: contratos ativos, encerrados e aditivos</h2>
      <p>
        Ter acesso aos dados é apenas o primeiro passo. A interpretação correta exige conhecer as
        nuances do ciclo de vida de um contrato público e o que cada indicador representa.
      </p>

      <h3>Contratos ativos versus encerrados</h3>
      <p>
        Um contrato ativo significa que o fornecedor está em plena relação contratual com o órgão
        — existe obrigação de entrega e o órgão tem compromisso de pagamento. Contratos encerrados
        compõem o acervo técnico do fornecedor. Para fins de qualificação em licitações, ambos são
        relevantes: contratos recentes (últimos 3-5 anos) pesam mais, mas contratos mais antigos
        demonstram experiência acumulada em setores específicos.
      </p>
      <p>
        Atenção a contratos &quot;encerrados por rescisão&quot;: rescisões unilaterais pela
        administração indicam descumprimento contratual — um sinal negativo significativo na
        análise de um fornecedor.
      </p>

      <h3>Aditivos: o que revelam</h3>
      <p>
        Aditivos são instrumentos formais que alteram o contrato original. Existem três tipos
        principais:
      </p>
      <ul>
        <li>
          <strong>Aditivos de prazo:</strong> prorrogam a vigência. Permitidos para serviços de
          natureza continuada por até 60 meses (Lei 14.133/2021, art. 107).
        </li>
        <li>
          <strong>Aditivos de valor:</strong> acrescentam ou reduzem o valor contratado. Limitados
          a 25% do valor original para serviços e compras, e a 50% para obras (art. 125).
        </li>
        <li>
          <strong>Aditivos de objeto:</strong> alteram o escopo do que será entregue, sempre
          mantendo a essência do contrato original.
        </li>
      </ul>
      <p>
        Para consultores de licitações e empresas B2G, os aditivos de valor são os mais
        informativos: revelam se o fornecedor consegue ampliar o escopo de trabalho em órgãos onde
        já está presente — um indicador de relacionamento e capacidade técnica.
      </p>

      {/* Section 7: Red flags */}
      <h2>Sinais de alerta ao analisar contratos de um fornecedor</h2>
      <p>
        A análise de contratos públicos também serve para identificar riscos antes de uma parceria
        ou subcontratação. Os padrões a seguir merecem atenção especial:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3 text-base">Red flags em contratos governamentais</h3>
        <ul className="space-y-3 text-sm">
          <li>
            <p className="font-medium text-ink">Excesso de aditivos de valor</p>
            <p className="text-ink-secondary">
              Contratos que acumulam aditivos sucessivos próximos ao limite legal de 25% podem
              indicar subprecificação intencional na proposta original (prática conhecida como
              &quot;jogo de planilha&quot;). É relevante verificar a proporção entre valor original
              e valor final.
            </p>
          </li>
          <li>
            <p className="font-medium text-ink">Concentração em um único órgão</p>
            <p className="text-ink-secondary">
              Fornecedores com mais de 70-80% do faturamento governamental concentrado em um único
              órgão apresentam risco de dependência e, em alguns casos, podem sinalizar relação
              atípica com aquele órgão.
            </p>
          </li>
          <li>
            <p className="font-medium text-ink">Contratos por inexigibilidade ou dispensa recorrentes</p>
            <p className="text-ink-secondary">
              Embora legítimas, contratações diretas recorrentes com o mesmo fornecedor no mesmo
              objeto podem indicar direcionamento e merecem análise mais cuidadosa do contexto.
            </p>
          </li>
          <li>
            <p className="font-medium text-ink">Rescisões contratuais</p>
            <p className="text-ink-secondary">
              Qualquer rescisão unilateral pelo poder público é um sinal de descumprimento
              contratual. Verifique sempre o motivo da rescisão antes de fechar parceria.
            </p>
          </li>
          <li>
            <p className="font-medium text-ink">Empresa com contrato mas sem licitação anterior</p>
            <p className="text-ink-secondary">
              Quando um contrato de alto valor aparece sem processo licitatório rastreável, pode
              indicar uso indevido de modalidades de dispensa ou irregularidade formal.
            </p>
          </li>
        </ul>
      </div>

      {/* Section 8: Subcontratação */}
      <h2>Subcontratação e acervo técnico: atenção a fornecedores intermediários</h2>
      <p>
        Em setores como construção civil, TI e saúde, é comum que o contratado principal
        subcontrate parte dos serviços. A subcontratação é permitida pela Lei 14.133/2021 (art.
        122), desde que prevista no edital e no contrato, e limitada percentualmente.
      </p>
      <p>
        O risco para quem analisa o histórico de um fornecedor é confundir empresa executora
        (subcontratada) com empresa contratada (o CNPJ que aparece no contrato). Para fins de
        acervo técnico e comprovação de capacidade, apenas o contrato original — no CNPJ
        diretamente vinculado ao órgão público — conta como experiência válida.
      </p>
      <p>
        Ao pesquisar um fornecedor, portanto, verifique se os contratos listados são de titularidade
        direta ou se há indícios de que a empresa atua como subcontratada de outra. Isso é
        especialmente relevante em processos que exigem atestado de capacidade técnica para
        habilitação.
      </p>

      {/* Section 9: Diretórios e setores */}
      <h2>Encontrando fornecedores por setor e estado</h2>
      <p>
        Além da pesquisa por CNPJ, é possível mapear o mercado fornecedor por setor e localidade.
        O SmartLic disponibiliza diretórios segmentados, como o{' '}
        <Link href="/fornecedores/ti/SP" className="text-brand-primary hover:underline">
          diretório de fornecedores de TI em São Paulo
        </Link>
        , que lista empresas com histórico de contratos governamentais naquele segmento e estado.
      </p>
      <p>
        Esses diretórios são úteis para:
      </p>
      <ul>
        <li>
          Identificar concorrentes ativos em um mercado-alvo antes de entrar numa licitação.
        </li>
        <li>
          Encontrar potenciais parceiros com experiência comprovada em determinado segmento.
        </li>
        <li>
          Mapear o campo competitivo em um estado antes de decidir onde priorizar esforços
          comerciais.
        </li>
      </ul>
      <p>
        Para aprofundamento em contratos de TI especificamente, o{' '}
        <Link href="/blog/contratos/ti" className="text-brand-primary hover:underline">
          guia de contratos de TI no setor público
        </Link>{' '}
        traz análises de modalidades mais usadas, valores médios por objeto e os principais órgãos
        contratantes do segmento.
      </p>

      {/* Section 10: Step-by-step comparativo */}
      <h2>Comparativo dos três métodos: qual usar em cada situação?</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3 text-base">Guia de seleção do método</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left py-2 pr-4 font-semibold text-ink">Situação</th>
                <th className="text-left py-2 pr-4 font-semibold text-ink">Método recomendado</th>
                <th className="text-left py-2 font-semibold text-ink">Por que</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              <tr>
                <td className="py-2 pr-4 text-ink-secondary">Verificação pontual de um CNPJ</td>
                <td className="py-2 pr-4 text-ink">PNCP</td>
                <td className="py-2 text-ink-secondary">Fonte oficial, dados em tempo real</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 text-ink-secondary">Histórico financeiro federal detalhado</td>
                <td className="py-2 pr-4 text-ink">Portal da Transparência</td>
                <td className="py-2 text-ink-secondary">Empenhos e pagamentos desde 1996</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 text-ink-secondary">Análise comparativa entre fornecedores</td>
                <td className="py-2 pr-4 text-ink">SmartLic</td>
                <td className="py-2 text-ink-secondary">Visão consolidada multi-fonte</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 text-ink-secondary">Mapeamento de mercado por setor</td>
                <td className="py-2 pr-4 text-ink">SmartLic</td>
                <td className="py-2 text-ink-secondary">Diretórios segmentados por CNAE</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 text-ink-secondary">Due diligence de parceiro estadual/municipal</td>
                <td className="py-2 pr-4 text-ink">PNCP + SmartLic</td>
                <td className="py-2 text-ink-secondary">PNCP para dados brutos, SmartLic para visão</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 11: Hub de contratos */}
      <h2>Explore o hub de contratos públicos do SmartLic</h2>
      <p>
        O SmartLic mantém um{' '}
        <Link href="/contratos" className="text-brand-primary hover:underline">
          hub centralizado de contratos públicos
        </Link>{' '}
        com dados atualizados diariamente a partir do PNCP. O hub permite navegar por órgão
        contratante, estado, faixa de valor, modalidade e setor — tudo sem necessidade de
        cadastro para consultas básicas.
      </p>
      <p>
        Para empresas que precisam monitorar continuamente contratos de concorrentes, o SmartLic
        disponibiliza alertas automáticos que notificam quando um fornecedor específico é contemplado
        em novos contratos ou quando um órgão-alvo publica novas contratações no seu setor.
      </p>

      {/* Conclusion */}
      <h2>Conclusão</h2>
      <p>
        Verificar contratos públicos de uma empresa é uma prática cada vez mais acessível e
        estratégica. Com o PNCP, o Portal da Transparência e ferramentas como o SmartLic, qualquer
        gestor, consultor ou empresário B2G pode obter em minutos uma visão detalhada do histórico
        governamental de qualquer fornecedor — sem custos e sem burocracia.
      </p>
      <p>
        O diferencial competitivo está em saber interpretar esses dados: entender o que os aditivos
        revelam sobre a execução contratual, identificar padrões de concentração que representam
        riscos e usar as informações de concorrentes para calibrar estratégias comerciais. Empresas
        que institucionalizam a análise de contratos públicos na sua inteligência de mercado tomam
        decisões mais bem fundamentadas e identificam oportunidades antes da concorrência.
      </p>

      {/* Sources */}
      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="font-semibold text-ink mb-3 text-base">Fontes e referências</h3>
        <ul className="space-y-1 text-sm text-ink-secondary">
          <li>
            PNCP — Portal Nacional de Contratações Públicas:{' '}
            <span className="text-ink">pncp.gov.br</span>
          </li>
          <li>
            Portal da Transparência do Governo Federal:{' '}
            <span className="text-ink">transparencia.gov.br</span>
          </li>
          <li>
            Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos
          </li>
          <li>
            Lei 12.527/2011 — Lei de Acesso à Informação (LAI)
          </li>
          <li>
            SmartLic — Plataforma de inteligência em licitações públicas:{' '}
            <span className="text-ink">smartlic.tech</span>
          </li>
        </ul>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas frequentes</h2>

      <h3>Como verificar se uma empresa tem contratos com o governo?</h3>
      <p>
        É possível verificar contratos governamentais de qualquer empresa pelo PNCP
        (pncp.gov.br) ou pelo Portal da Transparência (transparencia.gov.br), buscando pelo CNPJ
        do fornecedor. Plataformas como o SmartLic consolidam essas informações em uma única visão,
        incluindo histórico de valores, órgãos contratantes e aditivos, com atualização diária.
      </p>

      <h3>O que é o PNCP e como usá-lo para pesquisar contratos?</h3>
      <p>
        O PNCP é o repositório oficial obrigatório, criado pela Lei 14.133/2021, onde todos os
        órgãos da União, estados e municípios devem publicar contratos. Para pesquisar, acesse
        pncp.gov.br, navegue até &quot;Contratos&quot; e filtre pelo CNPJ do fornecedor desejado.
        O sistema retorna contratos com todos os campos obrigatórios, incluindo aditivos.
      </p>

      <h3>Quais informações estão disponíveis nos contratos públicos?</h3>
      <p>
        Os contratos públicos trazem: valor total e parcelas, nome do fornecedor e CNPJ, órgão
        contratante, objeto (descrição do bem ou serviço), datas de vigência, modalidade de
        licitação, número do processo e eventuais aditivos com justificativas e novos valores.
        No nível federal, o Portal da Transparência ainda disponibiliza o detalhamento de
        empenhos e pagamentos realizados.
      </p>

      <h3>Como interpretar aditivos em contratos governamentais?</h3>
      <p>
        Aditivos são alterações formais ao contrato original. Podem prorrogar prazo, acrescentar
        ou reduzir valor (limitado a 25% para obras e serviços, conforme a Lei 14.133/2021,
        art. 125), ou alterar o objeto. Contratos com muitos aditivos de valor merecem atenção:
        pode indicar subprecificação inicial ou dificuldades na execução. Por outro lado, aditivos
        de prazo em serviços continuados são plenamente normais e previstos em lei.
      </p>

      <h3>Por que verificar contratos públicos de um concorrente ou parceiro?</h3>
      <p>
        A verificação de contratos públicos serve a múltiplos fins: due diligence antes de
        parcerias (validar experiência comprovada), inteligência competitiva (identificar em quais
        órgãos e com quais valores o concorrente atua), qualificação de leads B2G, auditorias de
        conformidade e avaliação de capacidade técnica e financeira de fornecedores. Como os dados
        são públicos e gratuitos, seu uso é irrestrito por qualquer interessado.
      </p>
    </>
  );
}
