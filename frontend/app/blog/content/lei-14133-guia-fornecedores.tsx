import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * T2: Lei 14.133/2021: O que Mudou para Fornecedores — Guia Prático
 *
 * Target: 3,000+ words | Cluster: guias transversais
 * Primary keyword: lei 14133 fornecedores
 */
export default function Lei14133GuiaFornecedores() {
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
                name: 'A Lei 8.666 ainda está em vigor?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não. A Lei 8.666/1993 foi completamente revogada em 30 de dezembro de 2023, conforme o art. 193 da Lei 14.133/2021. Desde 1º de janeiro de 2024, todas as novas licitações devem seguir exclusivamente a Lei 14.133/2021. Contratos firmados sob a Lei 8.666 antes da revogação continuam válidos e são regidos pela legislação anterior até seu término. A Lei 10.520/2002 (Lei do Pregão) também foi revogada na mesma data.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que muda para microempresas na Lei 14.133?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 manteve e ampliou o tratamento diferenciado para microempresas (ME) e empresas de pequeno porte (EPP), nos arts. 4º e 42 a 49. Os benefícios incluem: licitações exclusivas até R$ 80 mil, cota reservada de 25% em bens divisíveis, preferência em empate ficto (até 5% em pregão, até 10% nas demais), regularização fiscal tardia em 5 dias úteis prorrogáveis e subcontratação compulsória de ME/EPP em contratos acima de determinados valores. A novidade é a possibilidade de licitações com margem de preferência regional para ME/EPP locais.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais as novas sanções para fornecedores?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 endureceu o regime de sanções nos arts. 155 a 163. As quatro sanções previstas são: advertência (para infrações leves), multa (sem limite percentual fixo na lei — definida em edital), impedimento de licitar e contratar por até 3 anos (substitui a suspensão da Lei 8.666) e declaração de inidoneidade por 3 a 6 anos (era indeterminada na Lei 8.666). A grande mudança é a obrigatoriedade de processo administrativo com ampla defesa antes de qualquer sanção e a criação do Cadastro Nacional de Empresas Punidas, integrado ao PNCP.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é diálogo competitivo e quando é usado?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O diálogo competitivo é uma nova modalidade introduzida pela Lei 14.133/2021 (arts. 32 e 36), inspirada no modelo europeu. É usado quando a Administração precisa de inovação tecnológica ou técnica, quando não consegue definir com precisão as especificações do objeto, ou quando a solução exige adaptação de soluções disponíveis no mercado. O processo funciona em duas fases: primeiro, diálogos com licitantes pré-selecionados para definir a solução; depois, apresentação de propostas finais com base na solução dialogada. É voltado para contratações complexas — TI, infraestrutura, saúde — e pouco aplicável a bens comuns.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como funciona o seguro-garantia na nova lei?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 ampliou significativamente o papel do seguro-garantia. O art. 98 permite exigência de garantia de até 5% do valor do contrato (regra geral) ou até 10% em obras, serviços e fornecimentos de grande vulto. A grande novidade é o seguro-garantia com cláusula de retomada (art. 102): em caso de inadimplência do contratado, a seguradora assume a execução do objeto e pode subcontratar terceiros para concluir a obra ou serviço. Essa modalidade é obrigatória em obras acima de R$ 200 milhões e muda radicalmente o perfil de risco para fornecedores de grande porte.',
                },
              },
              {
                '@type': 'Question',
                name: 'Preciso me recadastrar em algum sistema?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O SICAF (Sistema de Cadastramento Unificado de Fornecedores) continua sendo o cadastro central para compras federais e foi adaptado para a Lei 14.133/2021. Se já tinha cadastro ativo, não é necessário recadastrar — apenas manter os documentos atualizados. O PNCP (Portal Nacional de Contratações Públicas) é uma nova plataforma para publicação de editais e contratos, mas o cadastro de fornecedor no PNCP ainda não é obrigatório para participar de licitações. É recomendável acessar o PNCP para monitorar oportunidades.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais são os novos prazos de recursos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 unificou os prazos recursais no art. 165. O prazo para intenção de recurso é de 10 minutos após a declaração do vencedor (em pregão e concorrência eletrônica) ou imediato na sessão pública (modalidades presenciais). Aceita a intenção, o prazo para apresentar as razões do recurso é de 3 dias úteis. O prazo para contrarrazões é de 3 dias úteis após a intimação. A impugnação ao edital deve ser feita até 3 dias úteis antes da abertura do certame (art. 164).',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é o Portal Nacional de Contratações Públicas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O PNCP (Portal Nacional de Contratações Públicas) é a plataforma oficial criada pelo art. 174 da Lei 14.133/2021 para centralizar a publicação de editais, contratos, atas de registro de preços e demais documentos de contratações públicas de todos os entes federativos (União, estados, municípios e respectivas autarquias). O PNCP substituiu o Diário Oficial como meio principal de publicidade das licitações. Desde abril de 2023, todos os órgãos federais são obrigados a publicar no PNCP. A obrigatoriedade para estados e municípios está sendo implementada progressivamente.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — must contain primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A <strong>Lei 14.133/2021</strong> — a Nova Lei de Licitações e Contratos
        Administrativos — não é apenas uma atualização normativa. Para{' '}
        <strong>fornecedores</strong> do governo, ela representa a maior
        transformação no regime de contratações públicas desde 1993, quando a
        Lei 8.666 foi sancionada. A nova legislação alterou modalidades,
        endureceu sanções, criou o PNCP como plataforma central de publicidade,
        introduziu o seguro-garantia com cláusula de retomada e reformulou as
        regras de habilitação e julgamento. Este guia analisa cada mudança
        relevante sob a ótica de quem vende para o governo — com referências
        diretas aos artigos da lei, jurisprudência do TCU e orientações práticas
        para adaptação imediata.
      </p>

      <h2>O que é a Lei 14.133 e quando entrou em vigor</h2>

      <p>
        A Lei 14.133 foi sancionada em 1º de abril de 2021 e estabeleceu um
        período de transição de dois anos durante o qual os órgãos podiam optar
        entre a nova lei e a legislação anterior (Lei 8.666/1993 e Lei
        10.520/2002). Esse período transitório encerrou-se em 30 de dezembro de
        2023, conforme art. 193. Desde 1º de janeiro de 2024, todas as novas
        licitações devem seguir exclusivamente a Lei 14.133/2021.
      </p>

      <p>
        A lei revogou três diplomas legais de uma vez: a Lei 8.666/1993 (norma
        geral de licitações), a Lei 10.520/2002 (Lei do Pregão) e os artigos
        1º a 47-A da Lei 12.462/2011 (Regime Diferenciado de Contratações — RDC).
        Contratos firmados sob a legislação anterior continuam válidos e regidos
        pela lei vigente à época da contratação até seu encerramento.
      </p>

      <h2>Transição: Lei 8.666 vs Lei 14.133 — o que ainda vale</h2>

      <p>
        Uma dúvida recorrente entre fornecedores é sobre a coexistência das
        normas. A regra é simples: <strong>novas licitações seguem
        exclusivamente a Lei 14.133/2021</strong>. Contratos antigos seguem a lei
        sob a qual foram firmados. Isso significa que uma empresa pode ter
        contratos simultâneos sob regimes diferentes — um cenário que persistirá
        até o encerramento dos últimos contratos firmados sob a Lei 8.666,
        estimado para 2028-2029.
      </p>

      <p>
        Para fornecedores, as implicações práticas são: manter conhecimento
        sobre ambos os regimes durante a transição, especialmente em relação a
        penalidades, aditivos e reequilíbrio econômico-financeiro. As regras
        de execução contratual são diferentes em cada diploma — o que era
        permitido sob a Lei 8.666 pode não ser sob a Lei 14.133, e vice-versa.
      </p>

      <h2>10 mudanças práticas para fornecedores</h2>

      <p>
        A Lei 14.133/2021 tem 194 artigos, mas nem todos afetam diretamente
        o fornecedor. As dez mudanças a seguir são as mais relevantes para quem
        vende para o governo:
      </p>

      <h3>1. Cinco modalidades, não oito</h3>

      <p>
        A lei reduziu as modalidades de licitação de oito (na Lei 8.666 + Lei
        do Pregão) para cinco: pregão, <Link href="/glossario#concorrencia">
        concorrência</Link>, concurso, leilão e{' '}
        <Link href="/glossario#dialogo-competitivo">diálogo competitivo</Link>.
        A tomada de preços e o convite foram extintos. A concorrência absorveu
        os casos antes cobertos pela tomada de preços. O diálogo competitivo é
        a novidade mais significativa — voltado para contratações complexas onde
        a Administração precisa dialogar com o mercado antes de definir a
        solução (arts. 32 e 36).
      </p>

      <h3>2. Inversão de fases como regra geral</h3>

      <p>
        Na Lei 8.666, a habilitação ocorria antes do julgamento das propostas —
        todos os participantes precisavam apresentar documentos completos, mesmo
        que perdessem na fase de preços. A Lei 14.133 inverteu a lógica (art.
        17, §1º): o julgamento das propostas ocorre antes da habilitação. Apenas
        o vencedor provisório apresenta os documentos de habilitação. Para
        fornecedores, isso significa menos burocracia na fase inicial e
        concentração de esforço documental apenas quando há chance real de
        vencer.
      </p>

      <h3>3. Fim da obrigatoriedade de publicação em Diário Oficial</h3>

      <p>
        A publicação de editais e contratos agora é feita primariamente no PNCP
        (Portal Nacional de Contratações Públicas), conforme art. 174. O Diário
        Oficial da União continua existindo, mas o{' '}
        <Link href="/blog/pncp-guia-completo-empresas">PNCP</Link> é o meio
        oficial de publicidade. Para fornecedores, isso centraliza a busca de
        oportunidades em uma plataforma digital pesquisável — um avanço
        significativo em relação à era de PDFs publicados em diários oficiais
        de difícil acesso.
      </p>

      <h3>4. Critérios de julgamento ampliados</h3>

      <p>
        A Lei 14.133 define seis critérios de julgamento no art. 33: menor
        preço, maior desconto, melhor técnica ou conteúdo artístico, técnica e
        preço, maior lance (para leilão) e maior retorno econômico. A novidade
        é o &quot;maior retorno econômico&quot;, associado a contratos de
        eficiência — onde o fornecedor é remunerado pela economia que gera para
        a Administração. Para fornecedores de tecnologia e serviços de
        otimização, esse critério abre oportunidades antes inexistentes.
      </p>

      <h3>5. Habilitação proporcional ao objeto</h3>

      <p>
        O art. 67 da Lei 14.133 reforça que a habilitação deve ser proporcional
        e pertinente ao objeto da licitação. O art. 70, III, limita a exigência
        de quantitativos mínimos em atestados de capacidade técnica a 50% do
        objeto licitado — um avanço que favorece empresas de menor porte. Na
        prática, editais que exijam atestados superiores a 50% podem ser
        impugnados com base nesse dispositivo.
      </p>

      <h3>6. Matriz de riscos obrigatória em contratos de obras</h3>

      <p>
        O art. 103 introduziu a obrigatoriedade de matriz de riscos em contratos
        de obras e serviços de engenharia de grande vulto. A matriz define
        explicitamente quais riscos são do contratante (Administração) e quais
        são do contratado (fornecedor). Para fornecedores, isso oferece maior
        previsibilidade — eventos como variação cambial, atraso em licenças
        ambientais ou alterações regulatórias podem ser alocados à Administração,
        desde que previstos na matriz.
      </p>

      <h3>7. Pagamento antecipado regulamentado</h3>

      <p>
        A Lei 14.133 regulamentou o pagamento antecipado no art. 145, algo que
        era proibido pela interpretação dominante da Lei 8.666. O pagamento
        antecipado é permitido quando: representar condição indispensável para
        obter o bem ou serviço, houver previsão no edital e o fornecedor
        prestar garantia em valor equivalente. Para fornecedores de bens
        importados ou de fabricação sob encomenda, isso elimina o principal
        obstáculo financeiro à participação.
      </p>

      <h3>8. Portal de catálogo eletrônico</h3>

      <p>
        O art. 19 prevê a criação de catálogos eletrônicos de padronização de
        compras governamentais. Quando o item consta do catálogo, a Administração
        pode contratar diretamente — dispensando licitação — pelo preço de
        referência do catálogo. Para fornecedores com bens padronizados
        (material de escritório, equipamentos de informática, limpeza), a
        inclusão no catálogo eletrônico é uma porta de entrada importante que
        reduz o custo de participação a zero.
      </p>

      <h3>9. Orçamento sigiloso</h3>

      <p>
        O art. 24 permite que a Administração não divulgue o orçamento estimado
        até a fase de julgamento, tornando-o sigiloso. Essa mudança, que já
        existia no RDC, agora é regra geral. Para fornecedores, o impacto é
        direto: não é mais possível calibrar a proposta com base no preço de
        referência publicado. A estratégia precisa se basear em análise de
        mercado própria, histórico de preços praticados e cálculo de custo real.
      </p>

      <h3>10. Programa de integridade (compliance) como critério</h3>

      <p>
        O art. 60, §4º, permite que o edital exija programa de integridade
        (compliance) em contratações de grande vulto. Para fornecedores que
        já possuem programas de compliance estruturados, isso é uma vantagem
        competitiva. Para quem não tem, é um incentivo para implementar — o
        programa de integridade pode ser usado como critério de desempate (art.
        60, IV) e como atenuante em eventual processo sancionatório.
      </p>

      <h2>Novas modalidades: diálogo competitivo e leilão invertido</h2>

      <p>
        O diálogo competitivo (art. 32) é a modalidade mais inovadora da Lei
        14.133. Funciona em duas fases distintas. Na primeira, a Administração
        publica edital com descrição da necessidade (não da solução) e
        seleciona empresas para participar de diálogos individuais — cada
        empresa apresenta sua proposta de solução, e a Administração pode
        discutir aspectos técnicos sem divulgar informações confidenciais dos
        concorrentes. Na segunda fase, com base nos diálogos, a Administração
        define as especificações e solicita propostas finais.
      </p>

      <p>
        Para fornecedores de soluções tecnológicas e serviços complexos, o
        diálogo competitivo representa uma oportunidade de influenciar a
        especificação do objeto — algo impossível nas modalidades tradicionais.
        Na prática, essa modalidade ainda é pouco utilizada: segundo dados do
        PNCP, menos de 0,5% das licitações em 2025 adotaram o diálogo
        competitivo. A tendência é de crescimento à medida que os órgãos
        ganham familiaridade com o instrumento.
      </p>

      <h2>Mudanças no pregão eletrônico</h2>

      <p>
        O pregão, modalidade mais utilizada (mais de 70% das licitações em
        volume), sofreu ajustes relevantes na Lei 14.133. Os prazos mínimos
        de publicação foram alterados: 8 dias úteis para bens e serviços comuns
        (era 8 dias corridos na Lei 10.520) e 15 dias úteis para serviços
        especiais ou obras de engenharia. O modo de disputa continua sendo
        aberto, fechado ou combinado — mas o modo aberto (com lances
        sucessivos em sessão pública) permanece como o mais comum.
      </p>

      <p>
        Uma mudança relevante para fornecedores é o prazo para envio de
        documentação de habilitação: o pregoeiro pode conceder prazo de 2 a 4
        horas (antes era prática de 24 horas), embora muitos editais mantenham
        prazo mais elástico. A recomendação é manter toda a documentação
        digitalizada e pronta para upload imediato — conforme detalhamos em{' '}
        <Link href="/blog/como-participar-primeira-licitacao-2026">
          nosso guia para participar da primeira licitação em 2026
        </Link>.
      </p>

      <h2>Regime de sanções — mais severo e estruturado</h2>

      <p>
        O regime sancionatório da Lei 14.133 (arts. 155 a 163) é
        significativamente mais severo e estruturado do que o da Lei 8.666. As
        quatro sanções previstas são:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Sanções da Lei 14.133/2021
        </p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li>
            <strong>Advertência:</strong> Para infrações leves que não causem
            dano à Administração, ao funcionamento dos serviços ou prejuízo a
            terceiros.
          </li>
          <li>
            <strong>Multa:</strong> Sem percentual fixo na lei — o edital define
            o valor, que pode variar de 0,5% a 30% do valor do contrato. A multa
            pode ser cumulada com as demais sanções.
          </li>
          <li>
            <strong>Impedimento de licitar e contratar:</strong> Prazo de até 3
            anos. Substitui a &quot;suspensão do direito de licitar&quot; da Lei
            8.666. Abrange todos os entes federativos (alcance nacional via
            PNCP).
          </li>
          <li>
            <strong>Declaração de inidoneidade:</strong> Prazo de 3 a 6 anos
            (era indeterminado na Lei 8.666). Reservada para infrações graves
            como fraude, conluio e desvio.
          </li>
        </ul>
      </div>

      <p>
        A grande mudança para fornecedores é a obrigatoriedade de processo
        administrativo prévio com contraditório e ampla defesa (art. 158) antes
        de qualquer sanção — na Lei 8.666, isso nem sempre era observado.
        Além disso, as sanções são registradas no PNCP e no Cadastro Nacional
        de Empresas Punidas, com visibilidade nacional. Uma{' '}
        <Link href="/glossario#homologacao">homologação</Link> seguida de
        desistência do fornecedor, por exemplo, pode resultar em impedimento
        de 3 anos que afeta licitações em todo o Brasil — cenário que a Lei
        14.133 tornou mais provável.
      </p>

      <BlogInlineCTA
        slug="lei-14133-guia-fornecedores"
        campaign="guias"
        ctaHref="/explorar"
        ctaText="Explorar licitações grátis"
        ctaMessage="Descubra editais abertos no seu setor — busca gratuita"
      />

      <h2>Publicidade: tudo no PNCP</h2>

      <p>
        O art. 174 da Lei 14.133 criou o PNCP (Portal Nacional de Contratações
        Públicas) como sítio eletrônico oficial para publicação centralizada de
        atos relacionados a licitações e contratos. O portal reúne editais,
        contratos, atas de registro de preços, resultados de licitações e
        informações sobre sanções aplicadas. Para fornecedores, o PNCP é a
        principal fonte de busca de oportunidades — substituindo a navegação
        fragmentada por dezenas de Diários Oficiais.
      </p>

      <p>
        A obrigatoriedade de publicação no PNCP foi escalonada: órgãos federais
        desde abril de 2023, estados de grande porte desde 2024 e municípios
        menores com prazos estendidos até 2026. Na prática, a cobertura ainda
        é parcial — muitos municípios de pequeno porte não publicam no PNCP,
        utilizando apenas portais estaduais ou Diários Oficiais locais.
        Ferramentas como o <Link href="/features">SmartLic</Link> agregam
        múltiplas fontes (PNCP + Portal de Compras Públicas + ComprasGov) para
        compensar essa fragmentação. Para entender como usar o PNCP na prática,
        veja nosso{' '}
        <Link href="/blog/pncp-guia-completo-empresas">
          guia completo do PNCP para empresas
        </Link>.
      </p>

      <h2>Seguro-garantia e seguros novos</h2>

      <p>
        A Lei 14.133 transformou o seguro-garantia de um instrumento marginal em
        peça central das contratações de grande vulto. O art. 98 permite a
        exigência de garantia de até 5% do valor do contrato como regra geral,
        podendo chegar a 10% em obras, serviços e fornecimentos de grande vulto.
        As modalidades de garantia são: caução em dinheiro, seguro-garantia e
        fiança bancária.
      </p>

      <p>
        A grande novidade é o seguro-garantia com cláusula de retomada (art.
        102). Nessa modalidade, se o fornecedor se tornar inadimplente, a
        seguradora assume a execução do contrato — podendo subcontratar
        terceiros para concluir a obra ou o serviço. Essa modalidade é
        obrigatória para obras acima de R$ 200 milhões e opcional para valores
        menores. Para fornecedores, o impacto é duplo: maior custo de
        participação (o prêmio do seguro é mais caro quando inclui cláusula de
        retomada) e maior responsabilização — a seguradora faz diligência
        rigorosa antes de emitir a apólice.
      </p>

      <h2>ME/EPP: o que muda no tratamento diferenciado</h2>

      <p>
        A Lei 14.133 manteve integralmente o tratamento diferenciado para
        microempresas e empresas de pequeno porte, incorporando os dispositivos
        da Lei Complementar 123/2006 nos arts. 4º e 42 a 49. Os principais
        benefícios permanecem:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Benefícios para ME/EPP na Lei 14.133/2021
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • <strong>Licitações exclusivas:</strong> Contratações até R$ 80 mil
            são exclusivas para ME/EPP (art. 48, I)
          </li>
          <li>
            • <strong>Cota reservada:</strong> 25% em compras de bens divisíveis
            acima de R$ 80 mil (art. 48, III)
          </li>
          <li>
            • <strong>Empate ficto:</strong> Preferência quando a proposta for
            até 5% superior à melhor oferta em pregão (10% nas demais
            modalidades)
          </li>
          <li>
            • <strong>Regularização fiscal tardia:</strong> 5 dias úteis
            prorrogáveis para regularizar pendências fiscais após declaração de
            vencedor
          </li>
          <li>
            • <strong>Subcontratação compulsória:</strong> Editais podem exigir
            subcontratação de ME/EPP em contratos de maior valor
          </li>
          <li>
            • <strong>Margem de preferência regional:</strong> Novidade — editais
            podem estabelecer preferência para ME/EPP locais, quando
            justificado pelo desenvolvimento regional (art. 48, §3º)
          </li>
        </ul>
      </div>

      <p>
        A principal mudança para ME/EPP é positiva: a inversão de fases (art.
        17, §1º) reduz o custo de participação porque a documentação completa só
        é exigida do vencedor provisório. Para microempresas com recursos
        limitados, isso significa menos investimento em cada licitação disputada.
      </p>

      <h2>Prazos: o que o fornecedor precisa saber</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Prazos relevantes para fornecedores (Lei 14.133/2021)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • <strong>Impugnação ao edital:</strong> Até 3 dias úteis antes da
            abertura (art. 164)
          </li>
          <li>
            • <strong>Pedido de esclarecimento:</strong> Até 3 dias úteis antes
            da abertura (art. 164)
          </li>
          <li>
            • <strong>Intenção de recurso:</strong> 10 minutos após declaração
            do vencedor em pregão/concorrência eletrônica (art. 165)
          </li>
          <li>
            • <strong>Razões de recurso:</strong> 3 dias úteis após aceitação da
            intenção (art. 165, §1º)
          </li>
          <li>
            • <strong>Contrarrazões:</strong> 3 dias úteis após intimação (art.
            165, §3º)
          </li>
          <li>
            • <strong>Publicação mínima do pregão:</strong> 8 dias úteis (bens
            e serviços comuns) ou 15 dias úteis (serviços especiais)
          </li>
          <li>
            • <strong>Publicação mínima da concorrência:</strong> 15 dias úteis
            (menor preço) ou 35 dias úteis (técnica e preço)
          </li>
          <li>
            • <strong>Validade da proposta:</strong> Mínimo definido no edital
            (geralmente 60 a 90 dias)
          </li>
        </ul>
      </div>

      <h2>Como se adaptar: checklist prático para fornecedores</h2>

      <p>
        A transição para a Lei 14.133 não exige mudanças radicais na operação
        do fornecedor, mas demanda atenção a detalhes que, se ignorados, geram
        desclassificações e sanções. O checklist a seguir cobre os pontos
        principais:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Checklist de adaptação à Lei 14.133/2021
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            • Atualizar cadastro no SICAF com documentação vigente
          </li>
          <li>
            • Acessar e explorar o <Link href="/blog/pncp-guia-completo-empresas" className="text-brand-navy dark:text-brand-blue hover:underline">PNCP</Link> para
            busca de editais
          </li>
          <li>
            • Revisar modelo de proposta — adequar ao formato exigido pela nova
            lei
          </li>
          <li>
            • Treinar equipe sobre novos prazos recursais (10 minutos para
            intenção de recurso)
          </li>
          <li>
            • Avaliar necessidade de seguro-garantia para contratos de grande
            vulto
          </li>
          <li>
            • Implementar programa de integridade (compliance) se atua em
            contratações de grande vulto
          </li>
          <li>
            • Atualizar controle de certidões — novas regras de validade
          </li>
          <li>
            • Conhecer as novas sanções e ajustar gestão de risco contratual
          </li>
          <li>
            • Verificar se a empresa se enquadra como ME/EPP para benefícios
            diferenciados
          </li>
          <li>
            • Monitorar jurisprudência do TCU sobre a nova lei (Acórdãos 2023-2026)
          </li>
        </ul>
      </div>

      <p>
        Para fornecedores que atuam em volume — participando de dezenas ou
        centenas de licitações por mês — a automação da busca e triagem de
        editais é especialmente relevante sob a nova lei. Com a publicação
        centralizada no PNCP e a fragmentação residual em portais estaduais,
        ferramentas de inteligência que consolidam múltiplas fontes e
        classificam editais por setor e viabilidade economizam centenas de
        horas de trabalho manual. Para entender as{' '}
        <Link href="/blog/clausulas-escondidas-editais-licitacao">
          cláusulas que mais eliminam fornecedores
        </Link>{' '}
        sob a nova lei, consulte nosso guia detalhado.
      </p>

      {/* CTA final — before FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Monitore editais da Lei 14.133 em tempo real
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic busca editais no PNCP e portais complementares, classifica
          por setor com IA e avalia viabilidade em 4 fatores. Adaptado à nova lei.
        </p>
        <Link
          href="/consultoria-b2g?source=blog&article=lei-14133-guia-fornecedores&utm_source=blog&utm_medium=cta&utm_content=lei-14133-guia-fornecedores&utm_campaign=guias"
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

      <h2>Perguntas Frequentes</h2>

      <h3>A Lei 8.666 ainda está em vigor?</h3>
      <p>
        Não. A Lei 8.666/1993 foi completamente revogada em 30 de dezembro de
        2023. Desde 1º de janeiro de 2024, todas as novas licitações seguem
        exclusivamente a Lei 14.133/2021. Contratos firmados sob a Lei 8.666
        antes da revogação continuam regidos pela legislação anterior até seu
        encerramento.
      </p>

      <h3>O que muda para microempresas na Lei 14.133?</h3>
      <p>
        A Lei 14.133 manteve e ampliou os benefícios para ME/EPP: licitações
        exclusivas até R$ 80 mil, cota de 25% em bens divisíveis, empate ficto
        (até 5% em pregão), regularização fiscal tardia e possibilidade de
        margem de preferência regional. A inversão de fases reduz o custo de
        participação porque a documentação completa só é exigida do vencedor
        provisório.
      </p>

      <h3>Quais as novas sanções para fornecedores?</h3>
      <p>
        As quatro sanções são: advertência, multa (percentual definido em
        edital), impedimento de licitar por até 3 anos e declaração de
        inidoneidade por 3 a 6 anos. A principal mudança é a obrigatoriedade de
        processo administrativo prévio e o registro nacional de sanções no PNCP.
      </p>

      <h3>O que é diálogo competitivo e quando é usado?</h3>
      <p>
        Nova modalidade para contratações complexas (art. 32 da Lei 14.133).
        A Administração dialoga com empresas para definir a solução antes de
        solicitar propostas finais. Indicado para inovação tecnológica, soluções
        sob medida e objetos de difícil especificação. Ainda pouco utilizado
        (menos de 0,5% das licitações em 2025).
      </p>

      <h3>Como funciona o seguro-garantia na nova lei?</h3>
      <p>
        Garantia de até 5% do valor do contrato (10% em grande vulto). A
        novidade é o seguro-garantia com cláusula de retomada (art. 102): a
        seguradora assume a execução em caso de inadimplência do contratado.
        Obrigatório em obras acima de R$ 200 milhões.
      </p>

      <h3>Preciso me recadastrar em algum sistema?</h3>
      <p>
        O SICAF continua válido e foi adaptado à Lei 14.133. Se já tinha
        cadastro ativo, basta manter os documentos atualizados. O PNCP é uma
        nova plataforma para publicação de editais — o cadastro de fornecedor
        não é obrigatório, mas é recomendável para monitorar oportunidades.
      </p>

      <h3>Quais são os novos prazos de recursos?</h3>
      <p>
        Intenção de recurso: 10 minutos após declaração do vencedor em pregão
        eletrônico. Razões do recurso: 3 dias úteis após aceitação. Contrarrazões:
        3 dias úteis após intimação. Impugnação ao edital: até 3 dias úteis
        antes da abertura (art. 164).
      </p>

      <h3>O que é o Portal Nacional de Contratações Públicas?</h3>
      <p>
        O <Link href="/glossario#pncp">PNCP</Link> é a plataforma oficial criada
        pelo art. 174 da Lei 14.133 para centralizar editais, contratos e atas
        de todos os entes federativos. Substitui o Diário Oficial como meio
        principal de publicidade. Obrigatório para órgãos federais desde abril
        de 2023, com implementação progressiva para estados e municípios.
      </p>
    </>
  );
}
