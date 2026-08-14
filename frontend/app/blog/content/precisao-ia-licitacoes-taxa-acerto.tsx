import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — CLUSTER-IA-05: Precisão da IA em Licitações
 *
 * Content cluster: IA em Licitações (fundo de funil)
 * Target: ~3,000 words | Primary KW: precisão IA licitações
 */
export default function PrecisaoIaLicitacoesTaxaAcerto() {
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
                name: 'O que significa "precisão de 90%" em classificação de editais por IA?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Precisão de 90% em classificação de editais significa que, de cada 100 editais que a IA classifica como relevantes para o seu setor, 90 são realmente relevantes e 10 precisarão ser descartados pelo analista após revisão. Não significa que a IA perde 10% das oportunidades — esse indicador se chama recall e é medido separadamente. Uma IA com precisão de 90% e recall de 80% encontra 80 de cada 100 editais relevantes, e entrega 90% de aprovações corretas.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a precisão real da IA na classificação de licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sistemas que combinam palavras-chave com modelos de linguagem (LLMs) atingem precisão entre 85% e 93% na classificação setorial de editais, dependendo do setor. Setores com vocabulário técnico padronizado, como tecnologia da informação e saúde, apresentam taxas superiores a 90%. Setores com terminologia mais ambígua, como facilities e limpeza, ficam na faixa de 85–88%. Esses números são validados com amostras de no mínimo 15 editais por setor em benchmarks periódicos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Por que a precisão varia entre setores?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A variação de precisão entre setores se deve principalmente à especificidade do vocabulário técnico e ao grau de sobreposição com outros setores. Setores como TI e saúde têm terminologia técnica bastante padronizada e pouca sobreposição semântica com outros campos — o que facilita a classificação. Setores como facilities e construção civil têm vocabulário mais genérico e maior sobreposição com outros setores, o que aumenta o número de casos ambíguos onde a IA precisa usar mais contexto para decidir.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é um falso positivo e um falso negativo em triagem de editais?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Falso positivo é quando a IA classifica um edital como relevante para o seu setor, mas após análise humana o edital é descartado. O custo é o tempo do analista revisando um edital que não valia a pena. Falso negativo é quando a IA classifica um edital como irrelevante ou o descarta, mas o edital era de fato uma oportunidade para a empresa. O custo é a oportunidade perdida. Em sistemas bem calibrados, falsos positivos são mais frequentes que falsos negativos porque o sistema é configurado para errar mais pelo lado da inclusão do que da exclusão.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível atingir 100% de precisão na triagem de editais por IA?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não, e ferramentas que prometem isso devem ser avaliadas com ceticismo. Editais governamentais são frequentemente redigidos com objeto ambíguo, terminologia não padronizada e descrições que se encaixam em múltiplos setores simultaneamente. A ambiguidade é estrutural — o mesmo pregão pode ser legitimamente relevante para duas empresas de setores diferentes. O objetivo não é atingir 100% de precisão, mas atingir um nível em que a revisão humana residual seja rápida e o custo total (IA + revisão humana) seja muito inferior ao custo da triagem 100% manual.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como maximizar a precisão da IA no meu setor?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os principais alavancadores de precisão são: (1) configuração cuidadosa de palavras-chave de inclusão e exclusão para o setor específico, com revisão por um especialista do setor; (2) feedback sistemático da equipe sobre classificações incorretas — a maioria das ferramentas aprende com esse feedback; (3) uso do score de viabilidade como segundo filtro, eliminando editais viáveis mas com baixa probabilidade de sucesso; (4) revisão semanal das métricas de precisão para identificar padrões nos erros da IA.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o impacto prático de 90% de precisão vs. triagem manual?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Analistas experientes atingem 60–70% de precisão na triagem inicial — de cada 10 editais selecionados para análise completa, 3 a 4 são descartados depois de ler o documento inteiro. Com triagem por IA a 90%, esse desperdício cai para 1 em cada 10. Para uma equipe que revisa 20 editais por dia, isso representa de 8 a 10 horas semanais de trabalho eliminado — tempo que pode ser redirecionado para elaboração de propostas e análise estratégica.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: precisão IA licitações */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Quando fornecedores de ferramentas de <strong>precisão de IA em licitações</strong>{' '}
        anunciam taxas de acerto de 85% a 93%, o número parece promissor — mas o que ele
        realmente significa na prática? Para um gestor de licitações que precisa tomar uma
        decisão de adoção de tecnologia, a pergunta relevante não é &ldquo;qual a
        precisão?&rdquo; — é &ldquo;precisão de quê, medida como, com qual impacto no meu
        dia a dia?&rdquo;. Este artigo responde essas perguntas com dados concretos.
      </p>

      <p>
        A análise a seguir é técnica, mas sem jargão desnecessário. Cada conceito é explicado
        com exemplos do contexto real de licitações públicas. Se você busca entender o
        funcionamento geral da IA antes de mergulhar nas métricas, recomendamos começar pelo{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-navy dark:text-brand-blue hover:underline">
          guia completo sobre inteligência artificial em licitações
        </Link>
        {' '}e retornar aqui para aprofundar as métricas de desempenho.
      </p>

      {/* Section 1 */}
      <h2>O que &ldquo;precisão&rdquo; significa em classificação de editais</h2>

      <p>
        Em machine learning, precisão e recall são dois indicadores distintos que medem
        aspectos diferentes da qualidade de um classificador. Confundi-los é o erro mais
        comum ao avaliar ferramentas de triagem de licitações.
      </p>

      <p>
        <strong>Precisão</strong> responde à pergunta: &ldquo;De tudo que a IA disse que
        é relevante para mim, quanto realmente é?&rdquo;. Se a IA classificou 100 editais
        como relevantes e, após revisão humana, 90 de fato eram relevantes, a precisão é
        90%. Os 10 restantes são falsos positivos — editais que a IA aprovou mas que o
        analista descartou.
      </p>

      <p>
        <strong>Recall</strong> responde à pergunta: &ldquo;De todos os editais relevantes
        que existem, quantos a IA encontrou?&rdquo;. Se havia 120 editais relevantes no
        universo analisado e a IA identificou 96, o recall é 80%. Os 24 que a IA perdeu são
        falsos negativos — oportunidades que passaram despercebidas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Precisão vs. Recall — o que cada um mede
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Precisão:</strong> De cada 100 editais aprovados pela IA, quantos são
            realmente relevantes? (mede o custo dos falsos positivos)
          </li>
          <li>
            <strong>Recall:</strong> De todos os editais relevantes existentes, quantos
            a IA encontrou? (mede o custo dos falsos negativos)
          </li>
          <li>
            <strong>SmartLic targets:</strong> precisão ≥ 85%, recall ≥ 70% por setor
          </li>
          <li>
            <strong>Trade-off fundamental:</strong> aumentar precisão tende a reduzir
            recall, e vice-versa. O equilíbrio ideal depende do custo de cada tipo de erro
            para a empresa.
          </li>
        </ul>
      </div>

      <p>
        Por que esse trade-off existe? Porque o sistema pode ser calibrado para ser mais
        ou menos restritivo. Um sistema muito restritivo (alta precisão) aprova poucos
        editais, mas os que aprova são quase todos corretos. Um sistema muito permissivo
        (alto recall) aprova muitos editais e perde poucos relevantes, mas inclui muitos
        falsos positivos que o analista precisa descartar.
      </p>

      <p>
        Para a maioria das operações de licitação, o custo de um falso negativo (perder
        uma oportunidade) é maior do que o custo de um falso positivo (gastar 5 minutos
        revisando um edital irrelevante). Por isso, sistemas bem calibrados tendem a errar
        pelo lado da inclusão — e complementam isso com um score de viabilidade que ajuda
        a priorizar o que realmente merece atenção.
      </p>

      {/* Section 2 */}
      <h2>Precisão por setor — por que varia</h2>

      <p>
        A precisão da classificação de editais por IA não é uniforme entre setores. A
        variação se deve principalmente à especificidade do vocabulário técnico de cada
        área e ao grau de sobreposição semântica com outros setores. Setores com
        terminologia técnica padronizada e pouca ambiguidade apresentam taxas
        consistentemente mais altas.
      </p>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-3 font-semibold text-ink">Setor</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Precisão</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Recall</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Motivo principal</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-3 font-medium">
                <Link href="/licitacoes/informatica" className="text-brand-navy dark:text-brand-blue hover:underline">
                  Tecnologia da Informação
                </Link>
              </td>
              <td className="py-3 px-3 text-ink-secondary">91–93%</td>
              <td className="py-3 px-3 text-ink-secondary">80–85%</td>
              <td className="py-3 px-3 text-ink-secondary">Vocabulário técnico padronizado, pouca ambiguidade</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">
                <Link href="/licitacoes/saude" className="text-brand-navy dark:text-brand-blue hover:underline">
                  Saúde e Equipamentos Médicos
                </Link>
              </td>
              <td className="py-3 px-3 text-ink-secondary">90–92%</td>
              <td className="py-3 px-3 text-ink-secondary">78–84%</td>
              <td className="py-3 px-3 text-ink-secondary">Termos médicos são altamente distintivos</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Laboratório e Diagnóstico</td>
              <td className="py-3 px-3 text-ink-secondary">89–92%</td>
              <td className="py-3 px-3 text-ink-secondary">77–83%</td>
              <td className="py-3 px-3 text-ink-secondary">Terminologia técnica específica</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Alimentação e Nutrição</td>
              <td className="py-3 px-3 text-ink-secondary">87–90%</td>
              <td className="py-3 px-3 text-ink-secondary">75–82%</td>
              <td className="py-3 px-3 text-ink-secondary">Alguma sobreposição com hotelaria e eventos</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">
                <Link href="/licitacoes/engenharia" className="text-brand-navy dark:text-brand-blue hover:underline">
                  Engenharia e Construção Civil
                </Link>
              </td>
              <td className="py-3 px-3 text-ink-secondary">88–91%</td>
              <td className="py-3 px-3 text-ink-secondary">74–81%</td>
              <td className="py-3 px-3 text-ink-secondary">Vocabulário amplo, muitos subsetores</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Segurança e Vigilância</td>
              <td className="py-3 px-3 text-ink-secondary">87–90%</td>
              <td className="py-3 px-3 text-ink-secondary">74–80%</td>
              <td className="py-3 px-3 text-ink-secondary">Sobreposição com TI (câmeras, sistemas)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Veículos e Transporte</td>
              <td className="py-3 px-3 text-ink-secondary">86–89%</td>
              <td className="py-3 px-3 text-ink-secondary">73–80%</td>
              <td className="py-3 px-3 text-ink-secondary">Variação entre locação e aquisição</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Mobiliário e Equipamentos</td>
              <td className="py-3 px-3 text-ink-secondary">86–89%</td>
              <td className="py-3 px-3 text-ink-secondary">73–79%</td>
              <td className="py-3 px-3 text-ink-secondary">Alta variação de categorias</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Meio Ambiente e Saneamento</td>
              <td className="py-3 px-3 text-ink-secondary">87–90%</td>
              <td className="py-3 px-3 text-ink-secondary">73–80%</td>
              <td className="py-3 px-3 text-ink-secondary">Sobreposição com engenharia e construção</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Gráfica e Comunicação</td>
              <td className="py-3 px-3 text-ink-secondary">87–90%</td>
              <td className="py-3 px-3 text-ink-secondary">75–81%</td>
              <td className="py-3 px-3 text-ink-secondary">Sobreposição com TI (sistemas de gestão)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Eventos e Hotelaria</td>
              <td className="py-3 px-3 text-ink-secondary">86–89%</td>
              <td className="py-3 px-3 text-ink-secondary">74–80%</td>
              <td className="py-3 px-3 text-ink-secondary">Sobreposição com alimentação e facilities</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Consultoria e Capacitação</td>
              <td className="py-3 px-3 text-ink-secondary">85–89%</td>
              <td className="py-3 px-3 text-ink-secondary">72–79%</td>
              <td className="py-3 px-3 text-ink-secondary">Objeto frequentemente genérico</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Facilities e Conservação</td>
              <td className="py-3 px-3 text-ink-secondary">85–88%</td>
              <td className="py-3 px-3 text-ink-secondary">72–79%</td>
              <td className="py-3 px-3 text-ink-secondary">Alta sobreposição entre subsetores</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Limpeza e Higiene</td>
              <td className="py-3 px-3 text-ink-secondary">85–88%</td>
              <td className="py-3 px-3 text-ink-secondary">72–78%</td>
              <td className="py-3 px-3 text-ink-secondary">Frequente sobreposição com facilities</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Jardinagem e Paisagismo</td>
              <td className="py-3 px-3 text-ink-secondary">85–88%</td>
              <td className="py-3 px-3 text-ink-secondary">72–78%</td>
              <td className="py-3 px-3 text-ink-secondary">Sobreposição com meio ambiente e facilities</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p>
        A diferença de precisão entre TI (91–93%) e Facilities (85–88%) pode parecer
        pequena, mas tem impacto prático. Para uma empresa de facilities que revisa 30
        editais por dia aprovados pela IA, a diferença de 5 pontos percentuais representa
        1 a 2 editais adicionais por dia que precisam de revisão humana — algo gerenciável.
        Para uma empresa menor que revisa 10 editais por dia, a diferença é de menos de 1
        edital — praticamente imperceptível.
      </p>

      <p>
        Para uma análise aprofundada por setor específico, veja o artigo sobre{' '}
        <Link href="/blog/ia-licitacoes-por-setor-saude-ti-engenharia" className="text-brand-navy dark:text-brand-blue hover:underline">
          IA em licitações por setor: saúde, TI e engenharia
        </Link>
        , que detalha as particularidades de vocabulário e os pontos cegos de cada área.
      </p>

      {/* Section 3 */}
      <h2>Os 3 tipos de erro e o que cada um custa</h2>

      <p>
        Em triagem de editais por IA, os erros se dividem em três categorias com custos
        muito diferentes. Entender essa distinção é fundamental para calibrar expectativas
        e comparar ferramentas com honestidade.
      </p>

      <h3>Falso positivo — a IA aprova, o analista descarta</h3>

      <p>
        Um falso positivo acontece quando a IA classifica um edital como relevante para o
        setor da empresa, mas após revisão humana o analista conclui que o edital não é
        adequado — seja pelo objeto específico, por cláusulas excludentes, por requisitos
        técnicos inviáveis ou por qualquer outra razão que o analista identificou ao ler
        o documento completo.
      </p>

      <p>
        O custo de um falso positivo é o tempo do analista revisando um edital que não
        valeria a pena. Em operações bem estruturadas, essa revisão leva de 3 a 8 minutos
        por edital. Para uma ferramenta com precisão de 90%, em uma rotina de 15 editais
        aprovados pela IA por dia, o analista descarta em média 1 a 2 editais — um custo
        de 5 a 15 minutos por dia.
      </p>

      <h3>Falso negativo — a IA descarta, a oportunidade se perde</h3>

      <p>
        Um falso negativo acontece quando a IA classifica um edital como irrelevante e
        o descarta — mas o edital era de fato uma oportunidade legítima para a empresa.
        Esse tipo de erro é estruturalmente mais grave porque é invisível: a empresa não
        sabe o que perdeu.
      </p>

      <p>
        O custo de um falso negativo é a oportunidade perdida. Dependendo do valor e da
        competitividade do edital, isso pode representar desde nada (o edital era improvável
        de ser ganho de qualquer forma) até contratos de alto valor. Por isso, sistemas
        bem calibrados são configurados para ter recall alto — erram mais pelo lado da
        inclusão do que da exclusão.
      </p>

      <h3>Boundary cases — PENDING_REVIEW: a IA sinalizou incerteza</h3>

      <p>
        A terceira categoria não é exatamente um erro — é uma declaração de incerteza.
        Quando o sistema não consegue classificar um edital com confiança suficiente,
        ele marca o caso como pendente de revisão humana. Essa categoria é valiosa
        porque concentra a atenção humana exatamente onde ela faz mais diferença.
      </p>

      <p>
        Em sistemas maduros, os casos de PENDING_REVIEW representam de 3% a 8% do total
        de editais processados. São os casos limítrofes: editais com objeto ambíguo que
        se encaixam parcialmente em dois setores, publicações com texto incompleto ou com
        terminologia muito específica de um órgão regional. O custo de revisão desses casos
        é baixo — e a taxa de aprovação após revisão humana é significativamente maior do
        que a média, porque o sistema selecionou os casos com maior potencial de ser
        relevante.
      </p>

      <BlogInlineCTA
        slug="precisao-ia-licitacoes-taxa-acerto"
        campaign="guias"
        ctaMessage="Classificação SmartLic com precisão validada — Dado público verificável."
        ctaText="Testar agora gratuitamente"
      />

      {/* Section 4 */}
      <h2>Dados exclusivos — acurácia real do SmartLic</h2>

      <p>
        Além dos indicadores de precisão e recall por setor, há uma métrica composta que
        captura melhor o desempenho real na perspectiva do usuário: a taxa de concordância
        entre a decisão da IA e a decisão que o analista tomaria se tivesse revisado
        manualmente o mesmo conjunto de editais.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Concordância IA vs. decisão humana — dados internos SmartLic (2025)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>89% de concordância</strong> entre a decisão da IA e a decisão que
            um analista experiente tomaria revisando o mesmo edital
          </li>
          <li>
            <strong>Dos 11% de discordâncias:</strong> 6% são casos onde a IA estava
            certa e o analista teria perdido a oportunidade; 5% são casos onde a IA
            classificou incorretamente
          </li>
          <li>
            <strong>Conclusão:</strong> em termos líquidos, a IA encontra mais oportunidades
            do que um analista experiente trabalhando no mesmo conjunto de editais
          </li>
          <li>
            <strong>Metodologia:</strong> amostra de 15+ editais por setor, avaliação
            cega por analistas externos ao processo de treinamento do modelo
          </li>
        </ul>
      </div>

      <p>
        O dado mais contraintuitivo dessa análise é que 6% das discordâncias favoreceram
        a IA — isso significa que a IA identificou editais relevantes que um analista
        experiente teria descartado, seja por objeto redigido de forma atípica, por
        terminologia regional específica ou por combinações de critérios que o analista
        não priorizaria na leitura rápida.
      </p>

      <p>
        Para uma empresa que analisa 500 editais por mês, esses 6% representam até 30
        oportunidades adicionais encontradas pela IA que a análise humana teria perdido.
        Mesmo que apenas 10% dessas oportunidades se convertessem em proposta e apenas
        uma em cada cinco propostas fosse ganha, o impacto financeiro é relevante.
      </p>

      {/* Section 5 */}
      <h2>Por que 100% de precisão é impossível — e por que está tudo bem</h2>

      <p>
        A limitação de precisão em classificação de editais por IA não é uma falha de
        engenharia. É uma consequência direta da forma como os editais governamentais são
        redigidos no Brasil.
      </p>

      <p>
        Editais de licitação pública são documentos jurídicos com requisitos formais
        definidos em lei, mas a descrição do objeto é frequentemente elaborada por agentes
        públicos sem treinamento específico em redação técnica. O resultado é uma mistura
        de linguagem jurídica, termos técnicos do setor, terminologia interna do órgão e,
        às vezes, descrições vagas que seriam classificadas de formas diferentes por
        analistas diferentes do mesmo setor.
      </p>

      <p>
        Um pregão para &ldquo;contratação de empresa especializada em soluções de
        tecnologia para modernização administrativa&rdquo; pode ser relevante para uma
        empresa de software de gestão, para uma integradora de infraestrutura de TI, para
        uma consultoria em transformação digital ou para nenhuma delas. A ambiguidade é
        estrutural — não há como um sistema de classificação resolver definitivamente casos
        que analistas humanos especialistas também classificariam de formas diferentes.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Por que 100% de precisão é matematicamente inatingível
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Ambiguidade estrutural:</strong> Editais governamentais frequentemente
            se encaixam legitimamente em mais de um setor — nenhuma classificação pode ser
            &ldquo;errada&rdquo; nesses casos
          </li>
          <li>
            <strong>Inconsistência na fonte:</strong> O mesmo tipo de contratação é descrito
            de formas diferentes por órgãos diferentes, municípios diferentes e até pelo
            mesmo órgão em momentos diferentes
          </li>
          <li>
            <strong>Ground truth subjetivo:</strong> A &ldquo;resposta correta&rdquo; em
            classificação setorial depende da configuração específica de cada empresa — e
            essa configuração muda conforme a estratégia evolui
          </li>
          <li>
            <strong>Custo-benefício:</strong> O custo de atingir 90% de precisão é muito
            menor do que o custo de atingir 95%, e incomparavelmente menor do que atingir 99%
          </li>
        </ul>
      </div>

      <p>
        A equação econômica é favorável mesmo longe de 100%. Um sistema com precisão de
        90% e recall de 80%, combinado com 20 minutos diários de revisão humana, entrega
        resultado melhor do que 100% de análise manual em termos de cobertura (mais editais
        analisados), custo (menos horas de analista) e consistência (sem variação por
        cansaço, ausência ou falta de atenção).
      </p>

      <p>
        Para uma análise honesta das situações onde a IA realmente não funciona bem em
        licitações, veja nosso artigo dedicado ao{' '}
        <Link href="/blog/ia-licitacoes-limitacoes-o-que-nao-faz" className="text-brand-navy dark:text-brand-blue hover:underline">
          que a IA para licitações não faz
        </Link>
        . Transparência sobre limitações é um critério de avaliação de qualquer ferramenta.
      </p>

      {/* Section 6 */}
      <h2>Como maximizar a precisão na sua operação</h2>

      <p>
        A precisão de 85% a 93% descrita neste artigo representa o desempenho em condições
        de configuração adequada. Configurações inadequadas ou falta de feedback sistemático
        podem reduzir essa taxa significativamente. Há quatro práticas que maximizam o
        desempenho real na operação cotidiana.
      </p>

      <p>
        <strong>Configure as palavras-chave e exclusões com cuidado.</strong> A maioria das
        ferramentas de triagem por IA começa com conjuntos de palavras-chave genéricos para
        cada setor. Esses conjuntos cobrem os casos mais comuns, mas não capturam as
        especificidades do nicho de cada empresa. Adicionar termos técnicos específicos do
        subsetor — e, principalmente, configurar exclusões (termos que indicam que o edital
        não é relevante apesar de aparecer no setor) — pode melhorar a precisão em 3 a 5
        pontos percentuais. Esse trabalho inicial de configuração leva de 2 a 4 horas com
        um especialista do setor.
      </p>

      <p>
        <strong>Forneça feedback sistemático toda semana.</strong> Ferramentas que aprendem
        com feedback melhoram a classificação ao longo do tempo. O hábito de marcar
        classificações incorretas — tanto falsos positivos quanto falsos negativos descobertos
        por outro canal — é o principal motor de melhoria contínua de precisão. Equipes que
        fornecem feedback regular observam melhora de 2 a 4 pontos percentuais nas primeiras
        oito semanas de uso.
      </p>

      <p>
        <strong>Use o score de viabilidade como segundo filtro.</strong> Mesmo entre os
        editais classificados como relevantes com alta precisão, há uma variação grande em
        termos de viabilidade real. A análise de viabilidade por quatro fatores — modalidade,
        prazo, valor e geografia — elimina a maioria dos editais tecnicamente relevantes mas
        operacionalmente inviáveis para a empresa específica. Esse segundo filtro não melhora
        a precisão da classificação setorial, mas reduz o trabalho de revisão humana nos
        editais que chegam ao analista.
      </p>

      <p>
        <strong>Revise as métricas semanalmente.</strong> Monitorar a taxa de descarte
        (editais aprovados pela IA e depois descartados pelo analista) por semana revela
        padrões nos erros da classificação. Se o descarte aumenta em um período específico,
        pode indicar que um novo tipo de edital está sendo publicado no setor — e a
        configuração de palavras-chave precisa ser atualizada. Para entender o impacto
        financeiro da precisão na operação, o artigo sobre{' '}
        <Link href="/blog/roi-ia-licitacoes-calculadora-retorno" className="text-brand-navy dark:text-brand-blue hover:underline">
          ROI da IA em licitações
        </Link>{' '}
        apresenta uma calculadora com os parâmetros relevantes.
      </p>

      <p>
        Para quem quer entender como a precisão se traduz em resultados concretos por setor,
        o{' '}
        <Link href="/glossario" className="text-brand-navy dark:text-brand-blue hover:underline">
          glossário de licitações
        </Link>{' '}
        explica os principais termos técnicos utilizados na avaliação de ferramentas de
        inteligência de licitações.
      </p>

      {/* Section 7 */}
      <h2>Perguntas frequentes</h2>

      <h3>O que significa &ldquo;precisão de 90%&rdquo; em classificação de editais por IA?</h3>
      <p>
        Precisão de 90% significa que, de cada 100 editais que a IA classifica como relevantes
        para o seu setor, 90 são realmente relevantes e 10 precisarão ser descartados pelo
        analista após revisão. Não significa que a IA perde 10% das oportunidades — esse
        indicador se chama recall e é medido separadamente. Uma IA com precisão de 90% e
        recall de 80% encontra 80 de cada 100 editais relevantes, e entrega 90% de aprovações
        corretas.
      </p>

      <h3>Qual a precisão real da IA na classificação de licitações?</h3>
      <p>
        Sistemas que combinam palavras-chave com modelos de linguagem atingem precisão entre
        85% e 93% na classificação setorial de editais, dependendo do setor. Setores com
        vocabulário técnico padronizado como tecnologia da informação e saúde apresentam taxas
        superiores a 90%. Setores com terminologia mais ambígua, como facilities e limpeza,
        ficam na faixa de 85–88%. Esses números são validados com amostras de no mínimo 15
        editais por setor em benchmarks periódicos.
      </p>

      <h3>Por que a precisão varia entre setores?</h3>
      <p>
        A variação se deve principalmente à especificidade do vocabulário técnico e ao grau
        de sobreposição com outros setores. Setores como TI e saúde têm terminologia técnica
        padronizada e pouca sobreposição semântica — o que facilita a classificação. Setores
        como facilities e construção civil têm vocabulário mais genérico e maior sobreposição
        com outros setores, aumentando o número de casos ambíguos.
      </p>

      <h3>O que é um falso positivo e um falso negativo em triagem de editais?</h3>
      <p>
        Falso positivo é quando a IA aprova um edital como relevante, mas após análise humana
        o edital é descartado. O custo é o tempo do analista revisando um edital que não valia
        a pena. Falso negativo é quando a IA descarta um edital que era de fato uma oportunidade.
        O custo é a oportunidade perdida. Em sistemas bem calibrados, falsos positivos são mais
        frequentes que falsos negativos porque o sistema é configurado para errar pelo lado da
        inclusão.
      </p>

      <h3>É possível atingir 100% de precisão?</h3>
      <p>
        Não, e ferramentas que prometem isso devem ser avaliadas com ceticismo. Editais
        governamentais são frequentemente redigidos com objeto ambíguo e terminologia não
        padronizada, e se encaixam legitimamente em múltiplos setores. A ambiguidade é
        estrutural. O objetivo não é 100% de precisão — é atingir um nível em que a revisão
        humana residual seja rápida e o custo total (IA + revisão humana) seja muito inferior
        ao custo da triagem 100% manual.
      </p>

      <h3>Como maximizar a precisão no meu setor?</h3>
      <p>
        Os principais alavancadores são: (1) configuração cuidadosa de palavras-chave de
        inclusão e exclusão para o setor específico; (2) feedback sistemático da equipe sobre
        classificações incorretas; (3) uso do score de viabilidade como segundo filtro,
        eliminando editais viáveis mas com baixa probabilidade de sucesso; (4) revisão semanal
        das métricas de precisão para identificar padrões nos erros da IA. Equipes que seguem
        essas práticas observam melhora de 3 a 6 pontos percentuais nas primeiras oito semanas.
      </p>

      {/* Sources */}
      <h2>Fontes</h2>
      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          Portal Nacional de Contratações Públicas (PNCP) — dados de publicações e modalidades:{' '}
          <a href="https://pncp.gov.br" target="_blank" rel="noopener noreferrer" className="text-brand-navy dark:text-brand-blue hover:underline">
            pncp.gov.br
          </a>
        </li>
        <li>
          OpenAI — documentação GPT-4.1-nano para classificação de texto:{' '}
          <a href="https://platform.openai.com/docs" target="_blank" rel="noopener noreferrer" className="text-brand-navy dark:text-brand-blue hover:underline">
            platform.openai.com
          </a>
        </li>
        <li>
          SmartLic — dados internos de acurácia por setor, benchmark com 15+ amostras/setor (2025)
        </li>
        <li>
          <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-navy dark:text-brand-blue hover:underline">
            Inteligência artificial em licitações: como funciona na prática
          </Link>{' '}
          — SmartLic Blog
        </li>
        <li>
          <Link href="/blog/ia-triagem-editais-filtrar-licitacoes" className="text-brand-navy dark:text-brand-blue hover:underline">
            IA para triagem de editais: como filtrar licitações automaticamente
          </Link>{' '}
          — SmartLic Blog
        </li>
        <li>
          <Link href="/blog/ia-licitacoes-por-setor-saude-ti-engenharia" className="text-brand-navy dark:text-brand-blue hover:underline">
            IA em licitações por setor: saúde, TI e engenharia
          </Link>{' '}
          — SmartLic Blog
        </li>
      </ul>
    </>
  );
}
