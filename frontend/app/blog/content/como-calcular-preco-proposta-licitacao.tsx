import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * Como Calcular o Preço de Proposta em Licitação — Guia Completo
 *
 * Target: ~2800 words | Cluster: guias transversais
 * Primary keyword: como calcular preço proposta licitação
 */
export default function ComoCalcularPrecoPropostaLicitacao() {
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
                name: 'O que é BDI em licitação e como calcular?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'BDI (Benefício e Despesas Indiretas) é o percentual acrescido ao custo direto para cobrir despesas administrativas, tributos, seguros, riscos e lucro. A fórmula é: BDI (%) = [(1 + AC/100) × (1 + S/100) × (1 + R/100) × (1 + DF/100) / (1 - L/100) - 1] × 100. Em serviços, o BDI típico fica entre 20% e 30%; em obras civis, entre 25% e 35%. O TCU e o SINAPI divulgam referenciais por tipo de contratação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como saber o preço de referência do governo antes de licitar?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O preço de referência do governo pode ser consultado via: (1) PNCP (pncp.gov.br) — buscando contratos anteriores para o mesmo objeto; (2) Painel de Preços do Governo Federal (paineldeprecos.economia.gov.br) com valores médios de compras federais; (3) SINAPI (CEF) para obras de engenharia; (4) SICRO (DNIT) para obras rodoviárias; (5) Planilhas de estimativa no próprio edital, que o órgão é obrigado a divulgar por força do art. 23 da Lei 14.133/2021 em contratações acima de determinados valores.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o limite para proposta ser considerada inexequível?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Pela Lei 14.133/2021 (art. 59, §2º), presume-se inexequível a proposta cujo valor global seja inferior a 75% do valor orçado pela Administração para obras e serviços de engenharia. Para serviços em geral, o critério de inexequibilidade deve constar no edital, mas a referência usual de mercado é o mesmo patamar de 75% da mediana ou do menor preço de referência. O licitante pode ilidir a presunção demonstrando que os custos são exequíveis com planilha detalhada.',
                },
              },
              {
                '@type': 'Question',
                name: 'Posso ganhar licitação com preço igual ao da concorrência?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. Em caso de empate entre propostas, a Lei 14.133/2021 (art. 60) prevê critérios de desempate na seguinte ordem: (1) proposta apresentada por ME/EPP no caso de empate ficto da LC 123/2006; (2) maior percentual de bens e serviços nacionais; (3) empresa que comprove cumprimento de reserva de cargos para PCDs; (4) empresa com melhor histórico de desempenho; (5) sorteio. O empate ficto beneficia ME/EPP mesmo quando o preço é até 5% superior ao primeiro colocado em pregão.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como precificar proposta em pregão eletrônico para não perder por centavos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Em pregão eletrônico, o preço inicial da proposta deve ser competitivo mas não o seu piso. Reserve margem para a fase de lances (geralmente 3% a 8% acima do preço mínimo aceitável). Calcule com precisão o seu custo real, some o BDI e defina um preço mínimo abaixo do qual você não opera. Nunca lance abaixo desse piso — proposta inexequível gera desclassificação e possíveis sanções. Acompanhe em tempo real via plataforma e defina a estratégia de lances antes de começar a sessão.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Em licitações públicas, o preço é onde o dinheiro realmente é ganho ou perdido. Oferte alto
        demais e a concorrência te derruba na fase de lances. Oferte baixo demais e sua proposta é
        desclassificada por inexequibilidade — pior: você pode ganhar, assinar o contrato e quebrar
        na execução. Saber calcular o preço correto da proposta não é opcional; é a diferença entre
        um negócio lucrativo com o governo e um prejuízo que pode comprometer toda a empresa.
      </p>

      <h2>Por que Precificação é Diferente em Licitação</h2>
      <p>
        No mercado privado, você negocia. No mercado público, você oferta uma vez (ou disputa lances
        em sessão pública) e vive com aquele preço por toda a vigência do contrato — que pode durar
        de 12 meses a 5 anos com prorrogações (art. 107 da Lei 14.133/2021). Não existe renegociação
        informal. Não existe margem para erro de precificação.
      </p>
      <p>
        Três particularidades tornam a precificação em licitação única:
      </p>
      <ul>
        <li>
          <strong>Preço de referência:</strong> O governo já estimou o quanto o objeto vale antes de
          publicar o edital. Esse valor é calculado com base em pesquisa de mercado, contratos
          anteriores e tabelas referenciais (SINAPI, SICRO, Painel de Preços). Sua proposta será
          comparada a esse valor.
        </li>
        <li>
          <strong>Exequibilidade:</strong> Propostas abaixo de determinado percentual do preço de
          referência são presumidas inexequíveis pela lei. O órgão pode exigir que você prove que
          seus custos cobrem a execução.
        </li>
        <li>
          <strong>Irrevogabilidade:</strong> Ao enviar a proposta e assinar a declaração de
          habilitação, você está se comprometendo legalmente. Desistir após ser declarado vencedor
          gera multa e pode resultar em impedimento de licitar por até 3 anos (art. 156 da Lei
          14.133/2021).
        </li>
      </ul>

      <h2>O que é o Preço de Referência</h2>
      <p>
        O preço de referência (ou preço estimado) é o valor que a Administração apurou como
        razoável para a contratação. Pela Lei 14.133/2021 (art. 23), o órgão é obrigado a elaborar
        estudo técnico preliminar e orçamento detalhado com metodologia clara. Para contratações
        acima de R$ 100 mil, esse orçamento deve ser publicado no PNCP.
      </p>
      <p>
        Como o governo calcula o preço de referência? Existem três metodologias principais:
      </p>
      <ul>
        <li>
          <strong>Pesquisa de mercado direta:</strong> Ao menos 3 orçamentos de fornecedores
          diferentes, coletados com no máximo 6 meses de antecedência (Instrução Normativa SGD/ME
          nº 65/2021 para compras TI; IN 3/2017 e IN 73/2022 para bens e serviços em geral).
        </li>
        <li>
          <strong>Preços históricos:</strong> Contratos anteriores para o mesmo objeto, consultados
          no PNCP ou no Painel de Preços do Governo Federal (paineldeprecos.economia.gov.br), com
          atualização pelo IPCA.
        </li>
        <li>
          <strong>Tabelas referenciais oficiais:</strong> SINAPI (Caixa Econômica Federal) para obras
          civis e instalações, SICRO (DNIT) para obras rodoviárias, CMED (ANVISA) para medicamentos.
          Essas tabelas são atualizadas mensalmente.
        </li>
      </ul>
      <p>
        Antes de calcular seu preço, pesquise o preço de referência. Consulte o PNCP com a{' '}
        <Link href="/calculadora">calculadora de estimativa de preços do SmartLic</Link> ou acesse
        diretamente o Painel de Preços. Isso te dá o teto informal — a região em que sua proposta
        precisa estar para ser competitiva sem levantar suspeitas de sobrepreço.
      </p>

      <h2>Componentes do Preço: Custos Diretos e Indiretos</h2>
      <p>
        O preço final de uma proposta tem dois grandes blocos: custos diretos e custos indiretos
        (que incluem o lucro). Entender essa estrutura é fundamental para não esquecer itens e não
        precificar errado.
      </p>
      <p>
        <strong>Custos diretos</strong> são aqueles claramente atribuíveis à execução do objeto:
      </p>
      <ul>
        <li>Mão de obra direta (salários, encargos sociais, benefícios, EPIs, uniformes)</li>
        <li>Materiais e insumos consumidos na execução</li>
        <li>Equipamentos e ferramentas (aluguel ou depreciação)</li>
        <li>Subcontratações necessárias</li>
        <li>Transporte e logística ligados diretamente ao serviço</li>
        <li>Treinamentos obrigatórios por lei ou exigidos no edital</li>
      </ul>
      <p>
        <strong>Custos indiretos</strong> são rateados sobre a estrutura e devem ser cobertos pelo
        BDI (Benefício e Despesas Indiretas). Veja a seção seguinte para o detalhamento.
      </p>
      <p>
        Um erro comum de empresas iniciantes é calcular apenas os custos diretos e ignorar os
        indiretos. O resultado é uma proposta que até ganha a licitação — mas que opera no vermelho
        desde o primeiro mês de contrato. Para contratos de limpeza, segurança ou manutenção com
        mão de obra dedicada, os encargos trabalhistas por si só costumam elevar o custo nominal em
        70% a 90% sobre o salário base.
      </p>

      <h2>Como Calcular o BDI</h2>
      <p>
        O BDI (Benefício e Despesas Indiretas) é o percentual acrescido ao custo direto para cobrir
        tudo o que não é diretamente alocado na execução mas é real e necessário para o negócio
        existir. A fórmula mais utilizada — e aceita pelo TCU — é:
      </p>
      <div className="not-prose my-4 sm:my-6 bg-surface-1 border border-[var(--border)] rounded-lg p-4 font-mono text-sm overflow-x-auto">
        <p className="mb-2 font-semibold not-mono">Fórmula do BDI:</p>
        <p>BDI (%) = [(1 + AC/100) × (1 + S/100) × (1 + R/100) × (1 + DF/100) / (1 − L/100) − 1] × 100</p>
        <p className="mt-2 text-xs text-ink-secondary">Onde: AC = Administração Central; S = Seguros; R = Risco; DF = Despesas Financeiras; L = Lucro</p>
      </div>
      <p>
        Na prática, a maioria das empresas trabalha com uma composição simplificada — mas transparente.
        O TCU (Acórdão 2.369/2011 e atualizações) exige que o BDI apresentado em obras seja
        detalhado e justificado.
      </p>

      {/* BDI Components Data Box */}
      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Componentes típicos do BDI</h3>
        <ul className="space-y-2 text-sm">
          <li>• <strong>Administração central (AC):</strong> 3% a 6% — aluguel, energia, pessoal administrativo, contabilidade, TI, jurídico</li>
          <li>• <strong>Seguros e garantias (S):</strong> 0,5% a 1,5% — seguro de vida, seguro de obra, garantia contratual (até 5% do contrato, art. 96 da Lei 14.133/2021)</li>
          <li>• <strong>Risco (R):</strong> 1% a 3% — imprevistos, variações de produtividade, riscos não cobertos por reajuste</li>
          <li>• <strong>Despesas financeiras (DF):</strong> 1% a 2,5% — capital de giro, antecipação de fornecedores antes do primeiro faturamento</li>
          <li>• <strong>Tributos (T):</strong> ISS (2% a 5% conforme município), PIS (0,65%), COFINS (3%) para Lucro Presumido — ou regime Simples Nacional (tabela própria)</li>
          <li>• <strong>Lucro (L):</strong> 5% a 12% — margem líquida desejada sobre o custo direto</li>
        </ul>
        <p className="mt-3 text-xs text-ink-secondary">BDI resultante típico: serviços 20%–30% | obras civis 25%–35% | fornecimento de bens 10%–18%</p>
      </div>

      <p>
        O BDI incide sobre o custo direto total. Exemplo prático: se seus custos diretos somam
        R$ 80.000 e você aplica um BDI de 25%, o preço da proposta será R$ 100.000. Esse spread
        de R$ 20.000 cobre tudo acima descrito — e sobra o lucro.
      </p>
      <p>
        Para compras de bens e serviços de TI, a{' '}
        <Link href="/blog/pregao-eletronico-guia-passo-a-passo">metodologia de precificação em pregão eletrônico</Link>{' '}
        tem particularidades: os tributos variam conforme o regime tributário, e empresas do Simples
        Nacional não destacam PIS/COFINS separadamente — o que pode ser uma vantagem ou desvantagem
        dependendo do contexto.
      </p>

      <BlogInlineCTA slug="como-calcular-preco-proposta-licitacao" campaign="guias" />

      <h2>Preço Inexequível: O Que É e Como Evitar</h2>
      <p>
        A inexequibilidade é o pesadelo de qualquer empresa que quer ganhar a licitação a qualquer
        custo. O art. 59, §2º da Lei 14.133/2021 estabelece que, para obras e serviços de engenharia,
        presume-se inexequível a proposta com valor global inferior a 75% do valor orçado pela
        Administração. Para serviços em geral, o critério deve estar definido no edital.
      </p>
      <p>
        O que acontece quando sua proposta é considerada inexequível:
      </p>
      <ol>
        <li>
          O pregoeiro ou a comissão notifica o licitante para apresentar planilha de composição de
          custos que demonstre a viabilidade do preço ofertado (art. 59, §3º).
        </li>
        <li>
          Se a empresa não conseguir demonstrar exequibilidade, é desclassificada — mesmo que tenha
          apresentado o menor preço.
        </li>
        <li>
          Se a empresa for contratada com preço inexequível, provavelmente terá problemas para
          executar o contrato. O inadimplemento gera multa, rescisão unilateral e possível
          impedimento de licitar por até 3 anos.
        </li>
      </ol>
      <p>
        A regra dos 75% é um <em>piso de presunção</em>, não uma proteção garantida. O órgão pode
        questionar sua proposta mesmo acima desse limite se houver evidência de superfaturamento
        disfarçado (preço global adequado, mas itens unitários desproporcionais). Leia também o nosso
        guia sobre{' '}
        <Link href="/blog/erros-desclassificam-propostas-licitacao">erros que desclassificam propostas</Link>{' '}
        para entender todas as armadilhas.
      </p>

      <h2>5 Erros Fatais na Precificação de Licitações</h2>

      <h3>1. Não calcular os encargos trabalhistas corretamente</h3>
      <p>
        Em contratos de mão de obra intensiva (limpeza, segurança, manutenção predial), os encargos
        sobre o salário nominal chegam a 70%–90% (INSS patronal 20%, FGTS 8%, férias 11,11%,
        13º salário 8,33%, aviso prévio, SESI/SESC/SESC 1,5%, SENAI/SENAC 1% e adicionais). Ignorar
        qualquer desses itens gera buraco de caixa desde o primeiro pagamento.
      </p>

      <h3>2. Usar preço de mercado spot como referência</h3>
      <p>
        Preço de mercado spot é o que você paga hoje por insumos. Contratos públicos duram 12 a 60
        meses. Use índices de reajuste contratuais (IPCA, INPC ou índice setorial) na projeção e
        considere uma margem de risco para itens sem reajuste automático — como mão de obra entre
        uma convenção coletiva e outra.
      </p>

      <h3>3. Esquecer o capital de giro inicial</h3>
      <p>
        Contratos públicos tipicamente pagam em 30 dias após a nota fiscal. Mas você começa a
        executar no dia 1 — comprando materiais, pagando salários, faturando fornecedores. O custo
        financeiro desse capital de giro deve estar no BDI. Em contratos de R$ 500 mil/mês, o custo
        de carregamento de 30 dias pode representar R$ 3.000 a R$ 6.000 só de juros.
      </p>

      <h3>4. Ignorar a garantia contratual</h3>
      <p>
        O art. 96 da Lei 14.133/2021 permite ao órgão exigir garantia de até 5% do valor do contrato
        (podendo chegar a 10% em casos complexos). Essa garantia — em dinheiro, fiança bancária,
        seguro-garantia ou títulos — tem custo: fiança bancária custa 1%–3% ao ano sobre o valor
        garantido; seguro-garantia custa 0,8%–2,5% ao ano. Esse custo deve entrar no BDI.
      </p>

      <h3>5. Não analisar o histórico de contratos similares</h3>
      <p>
        O PNCP concentra todos os contratos públicos federais desde 2021 e parte dos estaduais e
        municipais. Antes de precificar, pesquise contratos para o mesmo objeto, na mesma UF, e
        compare os preços unitários. Isso te diz quanto o mercado aceita — e quanto os concorrentes
        habituais costumam ofertar. Use a{' '}
        <Link href="/calculadora">calculadora de benchmark do SmartLic</Link>{' '}
        para automatizar essa pesquisa.
      </p>

      {/* Warning box */}
      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">⚠ Atenção: A armadilha da inexequibilidade</p>
        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
          Ganhar um contrato público com preço inviável é pior do que perder a licitação. Contratos
          mal precificados geram inadimplência, multas contratuais (5%–20% do valor), rescisão
          unilateral e impedimento de licitar por até 3 anos (art. 156, Lei 14.133/2021). Defina
          sempre um preço mínimo aceitável antes de entrar em qualquer pregão — e não ceda abaixo
          dele, independente da pressão da fase de lances.
        </p>
      </div>

      <h2>Planilha de Custos: Como Estruturar para o Governo</h2>
      <p>
        Em contratos de serviços contínuos (vigilância, limpeza, TI, manutenção), o edital
        geralmente exige o preenchimento de uma planilha de custos e formação de preços. Essa
        planilha é um instrumento de transparência — e também de auditoria. O Tribunal de Contas da
        União tem súmulas e acórdãos que estabelecem o que pode e o que não pode estar em cada
        componente.
      </p>
      <p>
        Uma planilha de custos bem estruturada para contratos de serviços com mão de obra deve conter:
      </p>
      <ul>
        <li><strong>Módulo 1 — Composição da remuneração:</strong> Salário base, adicionais legais (insalubridade, periculosidade, noturno), horas extras previstas</li>
        <li><strong>Módulo 2 — Encargos sociais e trabalhistas:</strong> Grupo A (INSS, FGTS, SAT), Grupo B (férias, 13º, aviso prévio), Grupo C (afastamentos), Grupo D (provisões rescisórias)</li>
        <li><strong>Módulo 3 — Insumos de trabalho:</strong> Uniformes, EPIs, ferramentas, vale-transporte, vale-refeição, plano de saúde</li>
        <li><strong>Módulo 4 — Custos indiretos, tributos e lucro (BDI)</strong></li>
      </ul>
      <p>
        Auditores do TCU e controladorias estaduais verificam particularmente: (1) se o salário
        base respeita o piso da convenção coletiva da categoria; (2) se os percentuais de encargos
        batem com as alíquotas legais; (3) se os tributos são coerentes com o regime tributário
        declarado. Uma inconsistência pode gerar impugnação ou questionamento pós-contrato. Para
        aprender mais sobre a análise do edital antes de precificar, confira o guia de{' '}
        <Link href="/blog/analise-viabilidade-editais-guia">análise de viabilidade de editais</Link>.
      </p>

      <h2>Estratégia de Preço por Modalidade de Licitação</h2>

      <h3>Pregão Eletrônico — Estratégia Agressiva</h3>
      <p>
        O pregão é a modalidade que mais usa o critério de menor preço. A disputa acontece em
        tempo real, com lances decrescentes visíveis. A estratégia típica: apresente uma proposta
        inicial competitiva mas não o seu piso, reserve margem para a fase de lances e mantenha
        o controle rigoroso do seu preço mínimo. Em pregões muito disputados, a diferença entre
        ganhar e perder pode ser de R$ 0,01 no preço unitário.
      </p>

      <h3>Concorrência — Estratégia Equilibrada</h3>
      <p>
        A concorrência (art. 29 da Lei 14.133/2021) pode combinar critérios técnicos e de preço.
        Quando o critério é técnica e preço, a nota técnica pode compensar um preço levemente
        superior. Quando é menor preço ou maior desconto, o cálculo é semelhante ao pregão —
        mas sem a fase de lances interativos. Seja mais conservador na proposta inicial porque não
        há segunda chance de reduzir.
      </p>

      <h3>Ata de Registro de Preços — Estratégia de Volume</h3>
      <p>
        Na ARP (art. 82 e seguintes da Lei 14.133/2021), você registra um preço que pode ser
        acionado por múltiplos órgãos sem nova licitação. O volume esperado é estimado — não
        garantido. Precifique considerando o cenário de volume mínimo (pior caso) e volume máximo
        (melhor caso) e verifique se você tem capacidade operacional para atender
        múltiplos órgãos simultaneamente. Leia mais em nosso guia sobre{' '}
        <Link href="/blog/ata-registro-precos-como-escolher">como escolher atas de registro de preços</Link>.
      </p>

      {/* Blue CTA box */}
      <div className="not-prose my-8 sm:my-10 bg-brand/5 border border-brand/20 rounded-lg p-6 sm:p-8 text-center">
        <h3 className="text-xl font-bold mb-2">Pesquise preços de referência em segundos</h3>
        <p className="text-ink-secondary mb-4">
          O SmartLic agrega contratos do PNCP e calcula benchmarks de preço por objeto, UF e
          modalidade — direto no painel, sem precisar garimpar portal por portal.
        </p>
        <Link
          href="/consultoria-b2g?ref=blog-preco-proposta"
          className="inline-block bg-brand text-white font-semibold px-6 py-3 rounded-lg hover:bg-brand/90 transition-colors"
        >
          Testar grátis por 14 dias →
        </Link>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>O que é BDI em licitação e como calcular?</h3>
      <p>
        BDI significa Benefício e Despesas Indiretas. É o percentual acrescido ao custo direto
        para cobrir despesas administrativas, tributos, seguros, riscos e lucro. A fórmula
        consagrada pelo TCU envolve os componentes: Administração Central (AC), Seguros (S), Risco
        (R), Despesas Financeiras (DF) e Lucro (L). Para serviços, o BDI típico varia de 20% a 30%;
        para obras civis, de 25% a 35%. O Acórdão TCU 2.369/2011 é a referência mais citada.
      </p>

      <h3>Como saber o preço de referência antes de licitar?</h3>
      <p>
        Consulte o PNCP (pncp.gov.br) pesquisando contratos anteriores para o mesmo objeto, o
        Painel de Preços do Governo Federal para compras recentes, o SINAPI (Caixa) para
        engenharia e o SICRO (DNIT) para obras rodoviárias. O próprio edital, por força do art.
        23 da Lei 14.133/2021, deve trazer o orçamento estimativo para contratações acima de
        determinados valores. A ferramenta de busca do{' '}
        <Link href="/calculadora">SmartLic</Link> automatiza essa pesquisa.
      </p>

      <h3>Qual o limite para proposta inexequível?</h3>
      <p>
        Para obras e serviços de engenharia, presume-se inexequível a proposta abaixo de 75% do
        valor orçado pela Administração (art. 59, §2º, Lei 14.133/2021). Para serviços em geral,
        o critério deve estar definido no edital. O licitante pode ilidir a presunção apresentando
        planilha de custos detalhada que demonstre a viabilidade do preço ofertado.
      </p>

      <h3>Como precificar sem ter experiência anterior no setor público?</h3>
      <p>
        Comece com objetos simples e de menor valor — licitações até R$ 80 mil são exclusivas para
        ME/EPP (LC 123/2006, art. 48) e têm menor concorrência. Pesquise sistematicamente contratos
        similares no PNCP antes de cada proposta. Use planilhas de composição de custos detalhadas
        e valide com um contador os encargos trabalhistas e tributos aplicáveis ao seu regime.
        Considere também se vale a pena participar de uma{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao">análise de go/no-go</Link>{' '}
        antes de comprometer tempo e recursos.
      </p>

      <h3>Posso subcontratar parte do serviço para reduzir custos?</h3>
      <p>
        Sim, mas com restrições. O art. 122 da Lei 14.133/2021 permite subcontratação parcial desde
        que autorizada pelo edital e que a empresa subcontratada atenda os requisitos de habilitação
        do objeto subcontratado. A responsabilidade perante a Administração permanece integralmente
        com o contratado principal. Subcontratações não previstas no edital exigem autorização
        expressa do órgão.
      </p>
    </>
  );
}
