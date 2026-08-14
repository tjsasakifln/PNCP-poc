import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * Ata de Registro de Preços: Estratégia para Fornecedores em Licitações Públicas
 *
 * Target: ~2800 words | Cluster: guias transversais
 * Primary keyword: ata de registro de preços estratégia
 */
export default function AtaRegistroPrecosEstrategiaLicitacao() {
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
                name: 'O que é carona em ata de registro de preços?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Carona é o mecanismo pelo qual órgãos públicos que não participaram da licitação original podem aderir à Ata de Registro de Preços e adquirir os produtos ou serviços registrados nas mesmas condições de preço. O Decreto 11.462/2023 regulamenta a carona no âmbito federal, estabelecendo limites: cada órgão aderente pode contratar até 50% das quantidades registradas, e o total de adesões não pode exceder o dobro da quantidade original para serviços ou o triplo para bens.',
                },
              },
              {
                '@type': 'Question',
                name: 'Posso recusar uma carona se não quiser atender?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O fornecedor registrado não é obrigado a aceitar adesões por carona. A ARP obriga o fornecedor a fornecer nas condições registradas apenas ao órgão gerenciador e aos órgãos participantes originais. Adesões por carona dependem de concordância do fornecedor e do órgão gerenciador. Se a demanda extra comprometer sua capacidade de atendimento ou margem, você pode recusar fundamentando a limitação operacional.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a diferença entre ARP e licitação convencional?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Na licitação convencional, o contrato obriga o fornecedor a entregar e o governo a comprar quantidades definidas. Na ARP, o governo registra o preço mas não assume obrigação de compra — pode comprar zero. Em contrapartida, o fornecedor tem o preço garantido pelo período de vigência (até 2 anos), potencial de vendas para múltiplos órgãos via carona, e visibilidade antecipada da demanda governamental. É um trade-off: menos segurança de volume, maior alcance geográfico e diversificação de clientes.',
                },
              },
              {
                '@type': 'Question',
                name: 'Por quanto tempo uma ata de registro de preços é válida?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A vigência padrão da ARP é de 1 ano, prorrogável por igual período quando previsto no edital e comprovada a vantajosidade da manutenção (art. 84 da Lei 14.133/2021). O total máximo é, portanto, 2 anos. Diferente dos contratos de serviço contínuo, não há prorrogações sucessivas até 5 ou 10 anos — o limite é inflexível. Após o vencimento, nova licitação deve ser realizada para renovar o registro.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível renegociar o preço durante a vigência da ARP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, via pedido de reequilíbrio econômico-financeiro (art. 124 da Lei 14.133/2021) quando comprovado desequilíbrio por fato imprevisível superveniente. O fornecedor deve documentar a variação com notas fiscais de insumos, cotações e demonstrativos contábeis. Se o órgão reconhecer o desequilíbrio mas não aceitar o novo preço, o fornecedor pode solicitar o cancelamento do seu registro — saindo da ARP sem penalidade. A renegociação não é automática: deve ser formalizada por termo aditivo.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O Sistema de Registro de Preços é o único mecanismo de compras públicas em que o governo
        formaliza a intenção de comprar sem a obrigação de comprar. Para o fornecedor, isso é ao
        mesmo tempo a maior oportunidade e o maior risco das licitações públicas:{' '}
        <strong>você garante o preço e abre a porta para dezenas de órgãos</strong>, mas pode
        entregar zero durante meses e ter o preço corroído pela inflação. Entender a lógica do
        SRP — seus limites, suas vantagens e as armadilhas da carona — é condição para usar esse
        instrumento estrategicamente em vez de ser usado por ele. Este guia cobre a{' '}
        <Link href="/blog/lei-14133-guia-fornecedores">Lei 14.133/2021</Link>, arts. 82 a 86, e
        o Decreto 11.462/2023, que reformulou as regras da carona no governo federal.
      </p>

      <h2>O que é o Sistema de Registro de Preços (SRP)</h2>
      <p>
        O Sistema de Registro de Preços é um conjunto de procedimentos para contratações
        futuras. Em vez de licitar toda vez que precisa comprar, a Administração Pública realiza
        uma licitação de registro de preços, seleciona o fornecedor e registra o preço ofertado
        em uma <strong>Ata de Registro de Preços (ARP)</strong> — documento formal que vincula o
        fornecedor às condições negociadas pelo prazo de vigência.
      </p>
      <p>
        A base legal no regime atual está nos <strong>arts. 82 a 86 da Lei 14.133/2021</strong>{' '}
        e no <strong>Decreto 11.462/2023</strong> (que regulamentou o SRP para o Poder Executivo
        Federal, revogando o antigo Decreto 7.892/2013). Estados e municípios têm seus próprios
        regulamentos, mas devem obrigatoriamente observar os limites estabelecidos pela lei federal.
      </p>
      <p>
        O SRP é especialmente indicado para objetos de demanda frequente mas imprevisível em
        quantidade: materiais de escritório, medicamentos, equipamentos de TI, serviços de
        manutenção, produtos alimentícios, combustíveis. Para obras com escopo definido ou
        serviços com volume fixo contratual, a licitação convencional costuma ser mais adequada.
      </p>
      <p>
        Uma característica determinante: <strong>o governo não assume obrigação de compra</strong>.
        O art. 82, §4º da Lei 14.133 é claro: a existência de preços registrados não obriga a
        Administração a firmar as contratações. Isso tem implicações diretas para o planejamento
        financeiro do fornecedor.
      </p>

      <h2>Por que SRP É Estratégico para Fornecedores</h2>
      <p>
        Apesar da ausência de obrigação de compra, o SRP oferece vantagens competitivas
        significativas para fornecedores bem preparados:
      </p>

      <h3>Preço Garantido por até 2 Anos</h3>
      <p>
        Uma vez registrado, seu preço é o preço de referência para todos os órgãos que acessarem
        a ata. Não há relicitação para cada compra — o órgão simplesmente emite um pedido de
        fornecimento (ordem de compra) com base na ARP vigente. Isso elimina o custo de
        participar de múltiplos pregões para o mesmo tipo de produto, reduzindo drasticamente o
        custo de aquisição de clientes governamentais.
      </p>

      <h3>Alcance Multiorgânico via Carona</h3>
      <p>
        Órgãos que não participaram da licitação original podem aderir à sua ARP e comprar nas
        mesmas condições. Uma única vitória em licitação federal pode se transformar em demanda
        de 10, 20 ou 50 órgãos diferentes. Para empresas com capacidade produtiva ociosa, a
        carona representa receita incremental com custo comercial zero — o cliente chega até você.
      </p>

      <h3>Visibilidade Antecipada da Demanda</h3>
      <p>
        As ARPs registradas no PNCP (Portal Nacional de Contratações Públicas) são públicas. Isso
        significa que você pode monitorar os preços que seus concorrentes registraram, identificar
        categorias com alta demanda via carona, e calibrar sua estratégia para a próxima rodada
        de licitações. A{' '}
        <Link href="/blog/ata-registro-precos-como-escolher">
          escolha de quais ARPs disputar
        </Link>{' '}
        é, em si, uma decisão estratégica.
      </p>

      <h3>Pipeline de Receita Previsível</h3>
      <p>
        Empresas com múltiplas ARPs ativas — em diferentes órgãos, categorias e regiões — criam
        um portfólio de receita recorrente que funciona como anuidade governamental. Mesmo sem
        garantia de volume, a presença simultânea em várias atas dilui o risco de zero pedidos
        em qualquer período específico. É o equivalente B2G de diversificação de carteira.
      </p>

      <h2>Como Funciona a Carona</h2>
      <p>
        A carona (adesão à ARP por órgão não participante) está prevista no{' '}
        <strong>art. 86 da Lei 14.133/2021</strong> e detalhada no Decreto 11.462/2023. O
        processo envolve três partes: o órgão gerenciador (que realizou a licitação), o órgão
        aderente (que quer "pegar carona") e o fornecedor registrado.
      </p>
      <p>
        O órgão aderente deve: demonstrar vantajosidade da adesão (preço menor que o praticado em
        compras diretas), obter concordância do fornecedor, obter autorização do órgão gerenciador,
        e observar os limites quantitativos estabelecidos.
      </p>

      {/* Comparison table */}
      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-4">ARP vs. Licitação Convencional — Comparativo</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left py-2 pr-4 font-semibold">Critério</th>
                <th className="text-left py-2 pr-4 font-semibold">ARP (SRP)</th>
                <th className="text-left py-2 font-semibold">Licitação Convencional</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              <tr>
                <td className="py-2 pr-4 font-medium">Obrigação de compra</td>
                <td className="py-2 pr-4 text-amber-700 dark:text-amber-400">Não (governo pode comprar zero)</td>
                <td className="py-2 text-green-700 dark:text-green-400">Sim (quantidade contratada)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Obrigação de entrega</td>
                <td className="py-2 pr-4">Apenas quando solicitado</td>
                <td className="py-2">Sim, conforme cronograma</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Prazo máximo</td>
                <td className="py-2 pr-4">2 anos (1 + prorrogação)</td>
                <td className="py-2">Variável (serviços: até 10 anos)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Outros órgãos podem comprar?</td>
                <td className="py-2 pr-4 text-green-700 dark:text-green-400">Sim, via carona (art. 86)</td>
                <td className="py-2 text-red-700 dark:text-red-400">Não</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Risco de volume</td>
                <td className="py-2 pr-4 text-red-700 dark:text-red-400">Alto (sem garantia)</td>
                <td className="py-2 text-green-700 dark:text-green-400">Baixo (quantidade definida)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Risco de preço (inflação)</td>
                <td className="py-2 pr-4 text-red-700 dark:text-red-400">Médio-Alto (preço fixo 1-2 anos)</td>
                <td className="py-2 text-amber-700 dark:text-amber-400">Médio (reajuste anual permitido)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium">Custo de aquisição</td>
                <td className="py-2 pr-4 text-green-700 dark:text-green-400">Baixo (uma licitação, múltiplos clientes)</td>
                <td className="py-2">Por contrato</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p>
        Os limites da carona no Decreto 11.462/2023 são cruciais para o planejamento de capacidade:
      </p>
      <ul>
        <li>
          Cada órgão aderente pode contratar até <strong>50% das quantidades registradas</strong>{' '}
          para cada item.
        </li>
        <li>
          O total de adesões (carona) não pode exceder <strong>o dobro da quantidade original</strong>{' '}
          para serviços, ou o <strong>triplo</strong> para bens.
        </li>
        <li>
          O órgão gerenciador pode estabelecer limites mais restritivos no edital.
        </li>
      </ul>
      <p>
        Na prática: se uma ARP registrou 1.000 unidades de um produto, o total de caronas não
        pode superar 3.000 unidades adicionais (limite de 3× para bens). Para serviços, o limite
        é mais conservador (2×). Esses limites protegem o fornecedor de demanda impossível de
        atender e protegem o mercado de distorções por uma única ARP que monopolize toda a compra
        governamental do setor.
      </p>

      <BlogInlineCTA slug="ata-registro-precos-estrategia-licitacao" campaign="guias" />

      <h2>Vigência da ARP</h2>
      <p>
        O <strong>art. 84 da Lei 14.133/2021</strong> estabelece prazo máximo de{' '}
        <strong>1 ano</strong> de vigência para a ARP, com possibilidade de prorrogação por igual
        período — chegando a 2 anos totais — desde que: (a) o edital preveja a possibilidade de
        prorrogação, (b) seja comprovada a vantajosidade da manutenção do preço para a
        Administração, e (c) o fornecedor concorde expressamente.
      </p>
      <p>
        Diferente dos contratos de prestação de serviços contínuos (que podem ser prorrogados
        até 10 anos nos casos do art. 106), a ARP tem limite estrito de 2 anos sem exceção.
        Após esse prazo, uma nova licitação de registro de preços deve ser realizada.
      </p>

      <h3>Reequilíbrio de Preços</h3>
      <p>
        Durante a vigência, o fornecedor pode solicitar revisão de preços quando comprovado
        desequilíbrio econômico-financeiro por fato superveniente imprevisível (art. 124 da Lei
        14.133). O pedido deve ser documentado com notas fiscais de insumos, índices de mercado
        e demonstração objetiva da variação de custos.
      </p>
      <p>
        Se a revisão for negada pelo órgão gerenciador e o preço tornar o fornecimento
        antieconômico, o fornecedor pode solicitar o <strong>cancelamento do seu registro</strong>{' '}
        sem penalidade, desde que comprove que as condições se tornaram insuportáveis. Esse
        cancelamento deve ser formal e fundamentado — simplesmente parar de atender pedidos sem
        rescisão formal gera multas e sanções.
      </p>

      <h2>Riscos para o Fornecedor</h2>
      <p>
        O SRP não é isento de riscos. Empresas que não os mapeiam previamente enfrentam
        prejuízos operacionais e financeiros:
      </p>

      <h3>Congelamento de Preço em Cenário Inflacionário</h3>
      <p>
        Quando a inflação supera o preço registrado, cada pedido de compra gera uma perda
        unitária. Em ARPs de 2 anos com insumos voláteis — combustíveis, matérias-primas
        agrícolas, componentes eletrônicos —, o desequilíbrio pode eliminar toda a margem
        prevista. A estratégia de precificação deve incorporar uma margem de segurança explícita
        para o risco inflacionário, especialmente para ARPs com prazo de vigência longo.
        Veja mais sobre esse cálculo em{' '}
        <Link href="/blog/como-calcular-preco-proposta-licitacao">
          como calcular o preço de proposta em licitações
        </Link>
        .
      </p>

      <h3>Picos de Demanda por Carona</h3>
      <p>
        Uma ARP federal pode atrair caronas de órgãos em múltiplos estados simultaneamente. Se
        sua estrutura de produção ou distribuição não suporta entregas em Manaus, Recife e Porto
        Alegre ao mesmo tempo, o problema não é comercial — é operacional. A penalidade por
        inexecução contratual pode incluir multa, suspensão e inclusão em cadastro de
        fornecedores impedidos.
      </p>

      <h3>Dispersão Geográfica não Planejada</h3>
      <p>
        ARPs nacionais (sem delimitação de UF) expõem o fornecedor a pedidos de qualquer ponto
        do país. Se você não consegue atender determinadas regiões com margem positiva, é mais
        estratégico disputar ARPs regionalizadas ou garantir no edital uma delimitação geográfica
        compatível com sua operação.
      </p>

      {/* Warning box */}
      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">
          Abuso de carona e como se proteger
        </p>
        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
          Antes do Decreto 11.462/2023, o abuso de carona era uma das maiores distorções do SRP:
          órgãos aderentes chegavam a contratar volumes 10 vezes superiores ao original. Com as
          novas regras, os limites são mais rígidos, mas ainda exigem atenção. Estratégias de
          proteção: (1) negocie com o órgão gerenciador um limite máximo de adesões no edital;
          (2) inclua em sua proposta um teto de fornecimento mensal por região; (3) monitore as
          adesões pelo PNCP e exerça o direito de recusa quando a capacidade operacional estiver
          comprometida. O Decreto permite a recusa desde que devidamente fundamentada — documente
          sempre.
        </p>
      </div>

      <h2>Quando Participar de SRP vs. Licitação Convencional</h2>
      <p>
        A decisão entre disputar uma ARP ou uma licitação convencional depende do perfil do
        objeto, da sua estrutura operacional e do seu objetivo estratégico:
      </p>

      <h3>Prefira o SRP quando</h3>
      <ul>
        <li>
          O objeto é padronizado, recorrente e com demanda distribuída entre vários órgãos
          (materiais de consumo, TI básica, serviços de impressão, medicamentos genéricos).
        </li>
        <li>
          Você tem capacidade ociosa que pode ser preenchida por caronas sem custo adicional
          significativo de logística.
        </li>
        <li>
          Seu objetivo é construir presença em múltiplos órgãos com investimento único em
          processo licitatório.
        </li>
        <li>
          O mercado tem alta volatilidade de demanda e o governo prefere contratar de forma
          fracionada ao longo do ano.
        </li>
      </ul>

      <h3>Prefira a licitação convencional quando</h3>
      <ul>
        <li>
          O objeto tem quantidade definida e execução concentrada no tempo (obras, eventos,
          fornecimento único).
        </li>
        <li>
          Você precisa de certeza de receita para planejar produção, contratações e fluxo de caixa.
        </li>
        <li>
          A margem já é estreita e o risco de variação de volume tornaria o negócio inviável
          sem garantia mínima de absorção.
        </li>
        <li>
          O objeto envolve execução personalizada que não pode ser reaproveitada por caronas
          (software sob medida, projetos de engenharia únicos).
        </li>
      </ul>
      <p>
        A{' '}
        <Link href="/blog/analise-viabilidade-editais-guia">análise de viabilidade de editais</Link>{' '}
        deve considerar explicitamente o tipo de instrumento (ARP ou contrato convencional) como
        um dos fatores de decisão — não apenas o valor e a modalidade.
      </p>

      <h2>Estratégias de Precificação em ARPs</h2>
      <p>
        A precificação para SRP tem uma dimensão temporal que licitações convencionais não têm:
        você está definindo hoje o preço que valerá por até 2 anos. A estratégia de preço deve
        refletir isso.
      </p>

      <h3>Margem de Proteção Inflacionária</h3>
      <p>
        Para ARPs com prazo máximo de 2 anos, calcule o custo dos principais insumos projetando
        a inflação esperada do setor específico (não o IPCA geral, que subestima a inflação de
        insumos industriais). Uma margem de proteção de 8% a 15% sobre o custo atual é razoável
        para a maioria dos setores industriais em cenário de inflação moderada.
      </p>
      <p>
        Use a <Link href="/calculadora">calculadora de preço para licitações</Link> para estimar
        o impacto da inflação sobre sua margem ao longo do prazo da ARP, considerando
        diferentes cenários de demanda.
      </p>

      <h3>Precificação para Carona Geográfica</h3>
      <p>
        Se a ARP é nacional, seu preço deve ser viável para entrega em qualquer região do país.
        Isso geralmente implica usar um preço base correspondente à região mais cara de atender
        (Norte ou Centro-Oeste, em geral), o que pode tornar sua proposta menos competitiva para
        regiões próximas à sua sede. Uma alternativa é disputar ARPs regionalizadas com preços
        otimizados por território.
      </p>

      <h3>Estratégia de Múltiplos Registros</h3>
      <p>
        Fornecedores experientes constroem portfólios de ARPs: algumas nacionais de alto volume
        (âncoras), algumas regionais de margem superior (complementares) e algumas em categorias
        adjacentes (expansão). A distribuição dilui o risco de qualquer ARP individual não gerar
        pedidos. O monitoramento sistemático de novas licitações de registro de preços —{' '}
        <Link href="/blog/checklist-habilitacao-licitacao-2026">
          com documentação de habilitação sempre atualizada
        </Link>{' '}
        — é o que permite essa estratégia de portfólio.
      </p>

      {/* Blue CTA */}
      <div className="not-prose my-8 sm:my-10 bg-brand/5 border border-brand/20 rounded-lg p-6 sm:p-8 text-center">
        <h3 className="text-xl font-bold mb-2">
          Monitore novas ARPs do seu setor em tempo real
        </h3>
        <p className="text-ink-secondary mb-4">
          O SmartLic identifica automaticamente licitações de registro de preços relevantes para
          o seu perfil — com classificação de viabilidade e alertas de prazo. Construa seu
          portfólio de ARPs com inteligência, não com volume.
        </p>
        <Link
          href="/consultoria-b2g?ref=blog-ata-registro-precos"
          className="inline-block bg-brand text-white font-semibold px-6 py-3 rounded-lg hover:bg-brand/90 transition-colors"
        >
          Testar grátis por 14 dias →
        </Link>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>O que é carona em ata de registro de preços?</h3>
      <p>
        Carona é o mecanismo pelo qual órgãos públicos que não participaram da licitação original
        podem aderir à Ata de Registro de Preços e adquirir os produtos ou serviços registrados
        nas mesmas condições de preço. O Decreto 11.462/2023 estabelece limites no âmbito federal:
        cada órgão aderente pode contratar até 50% das quantidades registradas, e o total de
        adesões não pode exceder o dobro da quantidade original para serviços ou o triplo para
        bens. O fornecedor precisa concordar com cada adesão por carona.
      </p>

      <h3>Posso recusar uma carona se não quiser atender?</h3>
      <p>
        Sim. O fornecedor registrado não é obrigado a aceitar adesões por carona. A ARP obriga o
        fornecedor a fornecer nas condições registradas apenas ao órgão gerenciador e aos órgãos
        participantes originais. Adesões por carona dependem de concordância expressa do
        fornecedor. Se a demanda extra comprometer sua capacidade operacional ou tornar a entrega
        antieconômica, você pode recusar, documentando a limitação. A recusa de carona não
        configura inexecução contratual.
      </p>

      <h3>Qual a diferença entre ARP e licitação convencional?</h3>
      <p>
        Na licitação convencional, o contrato obriga o fornecedor a entregar e o governo a comprar
        quantidades definidas no objeto. Na ARP, o governo registra o preço mas não assume
        obrigação de compra — pode comprar zero durante toda a vigência. Em contrapartida, o
        fornecedor tem o preço garantido por até 2 anos, potencial de vendas para múltiplos órgãos
        via carona, e visibilidade antecipada da demanda governamental. É um trade-off: menos
        segurança de volume, maior alcance e diversificação de clientes.
      </p>

      <h3>Por quanto tempo uma ata de registro de preços é válida?</h3>
      <p>
        A vigência padrão da ARP é de 1 ano, prorrogável por igual período quando previsto no
        edital e comprovada a vantajosidade da manutenção (art. 84 da Lei 14.133/2021). O total
        máximo é, portanto, 2 anos. Não há prorrogações sucessivas além desse limite — diferente
        dos contratos de serviço contínuo. Após o vencimento, nova licitação deve ser realizada.
      </p>

      <h3>É possível renegociar o preço durante a vigência da ARP?</h3>
      <p>
        Sim, via pedido de reequilíbrio econômico-financeiro (art. 124 da Lei 14.133/2021) quando
        comprovado desequilíbrio por fato imprevisível superveniente. O fornecedor deve documentar
        a variação com notas fiscais, cotações e demonstrativos. Se o órgão não aceitar o novo
        preço, o fornecedor pode solicitar o cancelamento do seu registro sem penalidade — desde
        que comprove que as condições tornaram o fornecimento inviável. A renegociação deve ser
        formalizada por termo aditivo e não ocorre automaticamente.
      </p>
    </>
  );
}
