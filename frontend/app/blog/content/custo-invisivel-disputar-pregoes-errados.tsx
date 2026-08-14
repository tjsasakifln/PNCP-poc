import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-262 B2G-08: O Custo Invisivel de Disputar Pregoes Errados
 * Target: 2,000–2,500 words
 */
export default function CustoInvisivelDisputarPregoesErrados() {
  return (
    <>
      {/* FAQPage JSON-LD — STORY-262 AC5/AC11 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: [
              {
                '@type': 'Question',
                name: 'Quanto custa participar de um pregão eletrônico do início ao fim?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo total de participação em um pregão eletrônico inclui horas de análise do edital (8 a 24 horas de trabalho qualificado), emissão e renovação de certidões (R$ 200 a R$ 1.500 por processo), elaboração da proposta (4 a 16 horas), acompanhamento da sessão pública e eventuais recursos. Considerando o custo-hora de profissionais de licitação (R$ 45 a R$ 80/hora), cada participação custa entre R$ 1.800 e R$ 6.500 em recursos diretos, antes de considerar custos de garantia e custo de oportunidade.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a taxa média de vitória em pregões eletrônicos no Brasil?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A taxa média de adjudicação em pregões eletrônicos no Brasil situa-se entre 8% e 15%, segundo dados de mercado e análises do Painel de Compras Governamentais. Isso significa que uma empresa que participa de 20 pregões por ano pode esperar vencer entre 1 e 3, dependendo do setor e da qualidade da sua seleção de editais. Empresas com processos estruturados de triagem alcançam taxas entre 20% e 35%.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como identificar um pregão que não vale a pena disputar?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os principais indicadores de um pregão de baixa viabilidade são: objeto com baixo alinhamento setorial (a empresa atende apenas parcialmente o escopo), valor estimado fora da faixa de competitividade da empresa, requisitos de habilitação que exigem atestados ou qualificações que a empresa não possui, prazo de entrega incompatível com a capacidade operacional, e histórico do órgão contratante com atraso de pagamento. Ferramentas de análise de viabilidade podem avaliar esses critérios automaticamente.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o custo de oportunidade de disputar pregões errados?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo de oportunidade é o custo mais significativo e mais difícil de mensurar. Cada hora investida em um pregão sem viabilidade é uma hora que poderia ser dedicada a um edital com alta probabilidade de vitória. Em termos práticos, uma empresa que desperdiçou 200 horas anuais em pregões que perdeu poderia ter alocado esse tempo para elaborar propostas mais competitivas para editais com maior alinhamento, potencialmente gerando 2 a 4 contratos adicionais.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Participar de licitações públicas tem um custo. Esse custo é evidente quando
        se ganha — a margem operacional do contrato absorve o investimento em prospecção,
        análise e elaboração. Mas quando se perde, o custo não desaparece. Ele apenas
        deixa de ser contabilizado. A maioria das empresas B2G não mensura quanto gasta
        por ano em pregões que nunca tinham viabilidade real de vitória — e o valor é
        significativamente maior do que a intuição sugere.
      </p>

      <h2>Os custos que ninguém contabiliza</h2>

      <p>
        Quando uma empresa decide participar de um pregão, uma cadeia de custos se inicia.
        Cada etapa consome recursos — humanos, financeiros e de tempo — que só são
        recuperados em caso de adjudicação. O problema é que, com uma taxa média de
        adjudicação entre 8% e 15% no mercado brasileiro (fonte: Painel de Compras
        Governamentais, dados consolidados 2023-2024), a maior parte desses investimentos
        nunca gera retorno.
      </p>

      <p>
        O que torna esses custos particularmente danosos é sua invisibilidade contábil. Eles
        não aparecem em uma linha separada do demonstrativo financeiro. Estão diluídos em
        salários, despesas administrativas e custos gerais de operação. Para enxergá-los, é
        preciso decompor o custo de cada participação em seus componentes.
      </p>

      <h2>Custo 1: Horas de análise de edital</h2>

      <p>
        Antes de decidir participar, alguém precisa ler o edital. Um edital de pregão
        eletrônico tem, em média, entre 30 e 80 páginas, incluindo anexos, termos de
        referência e minutas de contrato. A leitura qualificada — aquela que identifica
        requisitos de habilitação, condições de execução, prazos e riscos — consome entre
        2 e 6 horas de trabalho de um profissional experiente.
      </p>

      <p>
        Considerando o custo-hora de um analista de licitações pleno (R$ 45 a R$ 80/hora,
        incluindo encargos, segundo dados salariais da Glassdoor Brasil, 2025), cada análise
        de edital custa entre R$ 90 e R$ 480 em trabalho qualificado. Se a empresa analisa
        10 editais para decidir participar de 3, são de R$ 900 a R$ 4.800 apenas na fase
        de avaliação — antes de redigir uma única proposta.
      </p>

      <h2>Custo 2: Documentação e certidões</h2>

      <p>
        A habilitação em pregões eletrônicos exige um conjunto de documentos que precisam
        estar atualizados: certidões negativas de débitos (federal, estadual, municipal,
        trabalhista, FGTS), atestados de capacidade técnica, balanço patrimonial, e em
        alguns casos, certidões específicas do setor de atuação. O custo direto de
        emissão e renovação desse pacote documental varia entre R$ 200 e R$ 1.500 por
        processo, dependendo do número de certidões exigidas e da necessidade de
        autenticação ou reconhecimento de firma.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Dados de referência: custos documentais por processo</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>• Certidões negativas de débitos (CND federal, estadual, municipal, FGTS, trabalhista): R$ 0 a R$ 150 em taxas (variam por UF e cartório)</li>
          <li>• Autenticação e reconhecimento de firma: R$ 50 a R$ 200 por conjunto documental (fonte: tabela de custas cartórias, 2024)</li>
          <li>• Atestados de capacidade técnica (quando exigem registro no CREA/CRA): R$ 150 a R$ 400 por atestado registrado</li>
          <li>• Tempo de organização do pacote documental: 4 a 8 horas de trabalho administrativo</li>
          <li>• Custo total por participação (documentação): R$ 200 a R$ 1.500 em custos diretos + 4 a 8 horas de trabalho</li>
        </ul>
      </div>

      <p>
        O custo documental não é trivial quando multiplicado pelo número de pregões disputados
        ao longo do ano. Uma empresa que participa de 30 pregões/ano investe entre R$ 6.000 e
        R$ 45.000 apenas em documentação — independentemente do resultado.
      </p>

      <h2>Custo 3: Oportunidades perdidas (custo de oportunidade)</h2>

      <p>
        Esse é, possivelmente, o custo mais significativo e o mais difícil de mensurar. Cada
        hora que o analista de editais ou o especialista em propostas dedica a um pregão de
        baixa viabilidade é uma hora que não está sendo investida em um edital com alta
        probabilidade de vitória.
      </p>

      <p>
        O custo de oportunidade se manifesta de duas formas: editais com bom potencial que
        não foram analisados a tempo porque a equipe estava ocupada com pregões errados, e
        propostas que poderiam ter sido mais competitivas se a equipe tivesse dedicado mais
        tempo à elaboração. Em ambos os casos, o resultado é receita que deixou de existir.
        Para entender como evitar esse ciclo,{' '}
        <Link href="/blog/erro-operacional-perder-contratos-publicos">
          leia nossa análise sobre erros operacionais que custam contratos
        </Link>. Uma perspectiva complementar vem de{' '}
        <Link href="/blog/usar-dados-provar-eficiencia-licitacoes">
          como usar dados para comprovar eficiência em licitações
        </Link>{' '}
        — mensurar o custo do esforço desperdiçado é o primeiro passo para
        demonstrar o valor de uma triagem mais inteligente.
      </p>

      <BlogInlineCTA slug="custo-invisivel-disputar-pregoes-errados" campaign="b2g" />

      <h2>Custo 4: Desgaste da equipe e turnover</h2>

      <p>
        Profissionais de licitação que passam semanas elaborando propostas para pregões
        que sistematicamente perdem experimentam um efeito cumulativo de frustração. O
        desgaste é real e mensurável: segundo pesquisa do Instituto Brasileiro de
        Governança Corporativa (IBGC, 2023), a taxa de turnover em funções administrativas
        ligadas a processos repetitivos e burocráticos é 30% superior à média do mercado.
      </p>

      <p>
        O custo de substituição de um profissional qualificado em licitações — incluindo
        recrutamento, treinamento e período de ramp-up — equivale a 3 a 5 meses de
        salário. Para um analista pleno que recebe R$ 5.500/mês, isso representa entre
        R$ 16.500 e R$ 27.500 por substituição.
      </p>

      <h2>Custo 5: Garantias e cauções bloqueadas</h2>

      <p>
        Determinadas modalidades de licitação exigem garantia de proposta (geralmente 1%
        a 5% do valor estimado) ou caução para participação. Enquanto a empresa está
        participando do processo, esses valores ficam bloqueados — indisponíveis para
        capital de giro ou investimento em outras oportunidades.
      </p>

      <p>
        Para uma empresa que participa de múltiplos pregões simultaneamente com garantias,
        o montante bloqueado pode comprometer a liquidez. A título de exemplo: garantias
        de 1% em 5 pregões de R$ 500.000 representam R$ 25.000 imobilizados, que em
        alguns casos ficam retidos por 60 a 90 dias após o encerramento do processo.
      </p>

      <h2>Custo 6: Risco reputacional em desistências</h2>

      <p>
        Quando uma empresa vence um pregão e depois desiste — porque percebeu tardiamente
        que o preço não é viável ou que não atende aos requisitos de execução —, o dano
        reputacional junto ao órgão contratante é concreto. A Lei 14.133/2021 prevê
        sanções que incluem impedimento de licitar e contratar com a administração pública
        por período de até 3 anos (Art. 156), além de multas.
      </p>

      <p>
        Mesmo sem sanção formal, a desistência gera um registro negativo no SICAF (Sistema
        de Cadastramento Unificado de Fornecedores) que pode ser consultado por outros
        órgãos. O custo indireto é a perda de confiança de órgãos contratantes que, em
        processos futuros, podem questionar a capacidade da empresa.
      </p>

      <h2>O cálculo consolidado: quanto custa errar 10 pregões por ano</h2>

      <p>
        Para tangibilizar o impacto, vamos consolidar os custos de participar de 10
        pregões sem viabilidade real de vitória ao longo de um ano. Esse é um cenário
        conservador — muitas empresas B2G participam de 20 a 40 pregões anuais com
        taxa de adjudicação inferior a 10%.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Exemplo prático: custo consolidado de 10 pregões perdidos por ano</p>
        <div className="text-sm text-ink-secondary space-y-3">
          <p><strong>Premissas:</strong></p>
          <ul className="space-y-1 ml-4">
            <li>• 10 pregões disputados sem viabilidade adequada</li>
            <li>• Custo-hora do analista: R$ 55/hora (média pleno, com encargos)</li>
            <li>• Tempo médio de análise por edital: 4 horas</li>
            <li>• Tempo médio de elaboração de proposta: 12 horas</li>
            <li>• Custo documental médio: R$ 600 por processo</li>
          </ul>
          <p><strong>Custos diretos:</strong></p>
          <ul className="space-y-1 ml-4">
            <li>• Análise de editais: 10 x 4h x R$ 55 = <strong>R$ 2.200</strong></li>
            <li>• Elaboração de propostas: 10 x 12h x R$ 55 = <strong>R$ 6.600</strong></li>
            <li>• Documentação: 10 x R$ 600 = <strong>R$ 6.000</strong></li>
            <li>• Acompanhamento de sessões: 10 x 3h x R$ 55 = <strong>R$ 1.650</strong></li>
          </ul>
          <p><strong>Subtotal direto: R$ 16.450</strong></p>
          <p><strong>Custos indiretos estimados:</strong></p>
          <ul className="space-y-1 ml-4">
            <li>• Custo de oportunidade (190 horas desviadas): equivalente a 2-3 propostas para editais viáveis = <strong>R$ 500.000 a R$ 750.000 em contratos potenciais não perseguidos</strong></li>
            <li>• Impacto no turnover (estimativa conservadora): <strong>R$ 5.000 a R$ 10.000/ano</strong></li>
          </ul>
          <p><strong>Custo total estimado: R$ 21.450 a R$ 26.450 em custos diretos + R$ 500.000 a R$ 750.000 em receita potencial perdida.</strong></p>
        </div>
      </div>

      <p>
        O custo direto de R$ 21.000 a R$ 26.000 por ano pode parecer gerenciável para uma
        empresa de médio porte. Mas o custo de oportunidade — a receita que deixou de ser
        buscada — é o que realmente impacta o faturamento. Se metade das 190 horas
        desperdiçadas tivesse sido redirecionada para editais de alta viabilidade, o
        retorno potencial superaria em ordens de grandeza o custo direto.{' '}
        <Link href="/blog/disputar-todas-licitacoes-matematica-real">
          Veja a matemática completa de por que disputar todas as licitações gera prejuízo
        </Link>.
      </p>

      <h2>Como reduzir esses custos estruturalmente</h2>

      <p>
        A solução não é participar de menos licitações — é participar das licitações certas.
        A diferença está na qualidade da triagem. Empresas que implementam processos
        estruturados de análise de viabilidade antes de decidir participar conseguem
        redirecionar recursos dos pregões de baixa probabilidade para os de alta
        probabilidade.
      </p>

      <p>
        Três ações concretas reduzem o custo de participação em pregões errados: primeiro,
        definir critérios objetivos de triagem (alinhamento setorial, faixa de valor,
        requisitos de habilitação, histórico do órgão); segundo, automatizar a fase de
        prospecção e triagem inicial para que a equipe humana avalie apenas editais
        pré-qualificados; terceiro, acompanhar métricas de eficiência (taxa de
        adjudicação, custo por proposta) para identificar e corrigir desvios
        rapidamente. Para entender como equipes gastam 40 horas por mês em editais
        que descartam,{' '}
        <Link href="/blog/equipe-40-horas-mes-editais-descartados">
          leia nosso diagnóstico sobre triagem manual
        </Link>.
      </p>

      {/* CTA — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Elimine pregões de baixa viabilidade automaticamente
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic analisa cada edital com base em 4 critérios de viabilidade e classifica
          relevância setorial por IA — para que sua equipe invista tempo apenas em pregões
          com chance real de retorno.
        </p>
        <Link
          href="/consultoria-b2g?source=blog&article=custo-invisivel-disputar-pregoes-errados&utm_source=blog&utm_medium=cta&utm_content=custo-invisivel-disputar-pregoes-errados&utm_campaign=b2g"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Pedir um diagnóstico à CONFENGE
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/consultoria-b2g" className="underline hover:text-ink">
            Ver planos
          </Link>
        </p>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Quanto custa participar de um pregão eletrônico do início ao fim?</h3>
      <p>
        O custo total de participação em um pregão eletrônico inclui horas de análise do edital
        (8 a 24 horas de trabalho qualificado), emissão e renovação de certidões (R$ 200 a
        R$ 1.500 por processo), elaboração da proposta (4 a 16 horas), acompanhamento da sessão
        pública e eventuais recursos. Considerando o custo-hora de profissionais de licitação
        (R$ 45 a R$ 80/hora), cada participação custa entre R$ 1.800 e R$ 6.500 em recursos
        diretos, antes de considerar custos de garantia e custo de oportunidade.
      </p>

      <h3>Qual a taxa média de vitória em pregões eletrônicos no Brasil?</h3>
      <p>
        A taxa média de adjudicação em pregões eletrônicos no Brasil situa-se entre 8% e 15%,
        segundo dados de mercado e análises do Painel de Compras Governamentais. Isso significa
        que uma empresa que participa de 20 pregões por ano pode esperar vencer entre 1 e 3,
        dependendo do setor e da qualidade da sua seleção de editais. Empresas com processos
        estruturados de triagem alcançam taxas entre 20% e 35%.
      </p>

      <h3>Como identificar um pregão que não vale a pena disputar?</h3>
      <p>
        Os principais indicadores de um pregão de baixa viabilidade são: objeto com baixo
        alinhamento setorial, valor estimado fora da faixa de competitividade da empresa,
        requisitos de habilitação que exigem atestados ou qualificações que a empresa não
        possui, prazo de entrega incompatível com a capacidade operacional, e histórico do
        órgão contratante com atraso de pagamento. Ferramentas de análise de viabilidade
        podem avaliar esses critérios automaticamente.
      </p>

      <h3>Qual o custo de oportunidade de disputar pregões errados?</h3>
      <p>
        O custo de oportunidade é o custo mais significativo e mais difícil de mensurar. Cada
        hora investida em um pregão sem viabilidade é uma hora que poderia ser dedicada a um
        edital com alta probabilidade de vitória. Em termos práticos, uma empresa que
        desperdiçou 200 horas anuais em pregões que perdeu poderia ter alocado esse tempo
        para elaborar propostas mais competitivas para editais com maior alinhamento,
        potencialmente gerando 2 a 4 contratos adicionais.
      </p>

      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
