import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — CLUSTER-IA-06: IA em Licitações por Setor
 *
 * Content cluster: IA em Licitações (fundo de funil)
 * Target: ~3,200 words | Primary KW: IA licitações saúde TI engenharia
 */
export default function IaLicitacoesPorSetorSaudeTiEngenharia() {
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
                name: 'Qual setor tem maior precisão na classificação de editais por IA?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Tecnologia da Informação (TI) é o setor com maior precisão de classificação por IA, atingindo entre 91% e 93%. O vocabulário técnico é altamente específico — "licença de software", "infraestrutura de rede", "solução em nuvem" raramente aparecem fora de editais de TI. Saúde vem em segundo lugar, com 90% a 92% de precisão, também devido à terminologia técnica padronizada.',
                },
              },
              {
                '@type': 'Question',
                name: 'Por que editais de facilities são mais difíceis para a IA classificar?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Editais de facilities e limpeza têm vocabulário que se sobrepõe a três ou mais outros setores. Um edital de "manutenção predial" pode incluir serviços elétricos (engenharia), limpeza (facilities), controle de pragas (saúde ambiental) e segurança patrimonial. Essa ambiguidade estrutural reduz a precisão de classificação para 85%-88%, mas é justamente por isso que a IA agrega mais valor — a classificação manual é ainda mais imprecisa dado o volume.',
                },
              },
              {
                '@type': 'Question',
                name: 'A IA consegue identificar editais de TI descritos como "modernização"?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. Sistemas de IA com classificação por LLM (zero-match) conseguem identificar editais de TI mesmo quando não contêm palavras-chave explícitas. Um edital descrito como "transformação digital da administração pública" ou "modernização dos processos" é classificado corretamente por modelos de linguagem que entendem contexto semântico, não apenas correspondência de palavras.',
                },
              },
              {
                '@type': 'Question',
                name: 'Editais de engenharia têm muitos falsos positivos na classificação por IA?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Engenharia civil tem taxa de falsos positivos um pouco maior do que TI ou saúde, principalmente pela sobreposição com manutenção predial, construção e reformas. A precisão gira entre 88% e 91%. Subsetores com vocabulário mais específico — engenharia ambiental, elétrica de alta tensão, geotecnia — tendem a ter classificação mais precisa. Sistemas multicamada (keywords + NLP + LLM) reduzem significativamente falsos positivos nesses casos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como a IA trata editais mistos, como saúde + TI?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Editais mistos são um desafio real. Um edital de "sistema de informação hospitalar" ou "prontuário eletrônico" pode ser relevante tanto para empresas de saúde quanto de TI. Sistemas avançados permitem que a empresa configure múltiplos perfis setoriais simultaneamente, classificando o edital em ambos. Isso aumenta o recall (menos oportunidades perdidas) ao custo de um leve aumento nos falsos positivos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o volume típico de editais por setor no PNCP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os volumes variam significativamente. Tecnologia da Informação e saúde estão consistentemente entre os setores de maior volume, com milhares de publicações mensais. Engenharia e construção têm alta sazonalidade — picos no segundo semestre quando orçamentos precisam ser executados. Facilities tem volume alto e distribuído ao longo do ano, com concentração em pregões de menor valor unitário. O PNCP processa mais de 800 mil publicações anuais no total.',
                },
              },
              {
                '@type': 'Question',
                name: 'Vale a pena usar IA para monitorar apenas um setor?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, mesmo para um único setor. O volume de publicações no PNCP — somando estados e municípios de todas as 27 UFs — é suficientemente alto para justificar a triagem automatizada mesmo em nichos específicos. Uma empresa de equipamentos médicos que monitora apenas saúde em 5 estados ainda lida com centenas de editais por mês. A IA elimina o tempo gasto analisando editais irrelevantes, mesmo dentro de um único setor.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A precisão da <strong>IA em licitações de saúde, TI e engenharia</strong> não é
        uniforme. Cada setor tem um perfil de vocabulário, nível de ambiguidade e volume
        de publicações que afeta diretamente o desempenho dos sistemas de classificação
        automática. Empresas que entendem essas diferenças configuram suas ferramentas de
        forma mais inteligente — e perdem menos tempo com falsos positivos ou oportunidades
        perdidas. Este artigo apresenta dados setoriais concretos sobre como a IA classifica
        editais em quatro grandes áreas: saúde, tecnologia da informação, engenharia e
        facilities.
      </p>

      <p>
        Os dados apresentados são baseados em análise do pipeline de classificação do
        SmartLic, que processa publicações do PNCP, PCP v2 e ComprasGov v3. Os índices
        de precisão são estimativas consolidadas — variam conforme configuração de setor,
        especificidade dos termos e granularidade do perfil de busca.
      </p>

      <h2>Por que o setor muda tudo na classificação por IA</h2>

      <p>
        A maioria das pessoas assume que um sistema de IA em licitações funciona como uma
        busca sofisticada: você informa palavras-chave e ele retorna os editais correspondentes.
        Essa visão subestima o problema central da classificação setorial: a maioria dos
        editais não descreve seu setor de forma explícita.
      </p>

      <p>
        Um edital de saúde pode ser descrito como &ldquo;aquisição de insumos laboratoriais&rdquo;,
        &ldquo;contratação de serviços de terapia ocupacional&rdquo; ou &ldquo;fornecimento
        de equipamentos para UPA&rdquo;. Cada uma dessas descrições exige que o sistema
        entenda contexto, não apenas palavras. É aqui que o vocabulário setorial faz a
        diferença.
      </p>

      <p>
        Setores com terminologia técnica padronizada — como TI e saúde — são classificados
        com alta precisão porque seus termos raramente aparecem em outros contextos.
        &ldquo;Hemoglobina glicada&rdquo; só aparece em licitações de saúde. &ldquo;Licença
        de software ERP&rdquo; só aparece em licitações de TI. Já setores como facilities
        e manutenção predial usam linguagem genérica que se sobrepõe com construção civil,
        limpeza, segurança e infraestrutura simultaneamente.
      </p>

      <p>
        Sistemas de IA de alta qualidade usam três camadas de classificação para lidar com
        essa variação: análise de densidade de palavras-chave (para setores com vocabulário
        específico), classificação semântica por NLP (para termos relacionados mas não exatos)
        e classificação por LLM em modo <em>zero-match</em> (para editais sem nenhuma
        palavra-chave explícita do setor). A eficácia de cada camada depende diretamente
        da especificidade do vocabulário setorial.
      </p>

      <h2>Saúde — vocabulário técnico padronizado, alta precisão</h2>

      <h3>Volume e perfil dos editais de saúde</h3>

      <p>
        Saúde é um dos setores de maior volume no PNCP. Municípios, estados e o governo
        federal publicam diariamente milhares de licitações para medicamentos, equipamentos
        médicos, insumos laboratoriais, serviços hospitalares, saneamento e saúde mental.
        O volume é alto e distribuído ao longo do ano — sem sazonalidade pronunciada, porque
        a demanda por insumos e serviços de saúde é contínua.
      </p>

      <p>
        Os valores contratuais variam enormemente: de pequenas compras de consumíveis
        (luvas, seringas, máscaras) com valores de R$ 5 mil a R$ 50 mil, até contratos
        de equipamentos de diagnóstico por imagem ou sistemas de informação hospitalar
        na faixa de R$ 500 mil a R$ 10 milhões. Esse espectro amplo significa que empresas
        de diferentes portes encontram oportunidades relevantes no setor.
      </p>

      <p>
        Secretarias municipais de saúde respondem pela maior fatia de publicações — e
        também pela maior variabilidade de qualidade na redação dos editais. Quanto menor
        o município, mais genérica tende a ser a descrição do objeto. Esse fator afeta
        diretamente a classificação por IA.
      </p>

      <h3>Como a IA classifica editais de saúde</h3>

      <p>
        A terminologia médica é naturalmente específica. Termos como &ldquo;ventilador
        pulmonar&rdquo;, &ldquo;hemoglobina glicada&rdquo;, &ldquo;dialysate concentrado&rdquo;,
        &ldquo;curativo alginato&rdquo; ou &ldquo;tomógrafo computadorizado&rdquo; não
        aparecem fora do contexto de saúde. Isso permite que o sistema de classificação
        por palavras-chave resolva a maioria dos casos na primeira camada — sem necessidade
        de LLM.
      </p>

      <p>
        A precisão de classificação em saúde fica na faixa de <strong>90% a 92%</strong>.
        Os erros residuais ocorrem principalmente em editais de saúde ambiental (que
        cruzam com meio ambiente), vigilância sanitária de alimentos (que cruzam com
        alimentação) e equipamentos de saúde ocupacional (que cruzam com segurança do
        trabalho e engenharia).
      </p>

      <p>
        Para empresas cujo foco é saúde pública hospitalar — medicamentos, equipamentos,
        serviços clínicos — a precisão tende a ficar no limite superior dessa faixa. Para
        empresas com portfólio híbrido (saúde + bem-estar + alimentação), configurar
        perfis setoriais específicos e excluir termos de sobreposição é essencial para
        reduzir ruído.
      </p>

      <h3>Desafios específicos: editais mistos saúde + TI, saúde + engenharia</h3>

      <p>
        O setor de saúde tem um número crescente de editais que combinam objeto técnico
        com infraestrutura tecnológica. Licitações de sistemas de prontuário eletrônico,
        telemedicina, plataformas de gestão hospitalar e equipamentos com componentes de
        software representam uma zona cinzenta relevante.
      </p>

      <p>
        Para empresas de TI que atendem o setor de saúde, esse é um segmento de alta
        oportunidade — e também de alta ambiguidade na classificação. Um edital de
        &ldquo;plataforma de gestão de leitos hospitalares&rdquo; é saúde ou TI? A resposta
        depende do perfil da empresa. Sistemas avançados permitem capturar esse tipo de
        edital em múltiplos perfis setoriais simultaneamente, com o analista fazendo a
        triagem final.
      </p>

      <h2>Tecnologia da Informação — o setor com maior precisão</h2>

      <h3>O domínio digital do pregão eletrônico em TI</h3>

      <p>
        Não é coincidência que TI seja o setor com maior precisão de classificação por IA.
        Tecnologia da informação é também um dos setores onde o pregão eletrônico domina
        — mais de 85% das licitações de TI acontecem via pregão eletrônico, o que resulta
        em editais mais padronizados, com objetos melhor descritos e linguagem mais técnica.
      </p>

      <p>
        O volume de licitações de TI no setor público cresceu significativamente após a
        pandemia e a aceleração de iniciativas de governo digital. Servidores, licenças de
        software, infraestrutura de rede, soluções em nuvem, desenvolvimento de sistemas,
        suporte técnico especializado — são categorias com alta demanda e publicações
        frequentes em todas as esferas de governo.
      </p>

      <p>
        Empresas de TI que operam no mercado B2G enfrentam uma concorrência mais
        estruturada do que outros setores: há um conjunto consolidado de fornecedores
        com experiência em atas de registro de preços federais, o que torna a velocidade
        de identificação de oportunidades em estados e municípios um diferencial competitivo.
      </p>

      <h3>Precisão de classificação: 91% a 93%</h3>

      <p>
        TI registra a maior precisão de classificação setorial por IA no mercado de
        licitações. A faixa de <strong>91% a 93%</strong> é sustentada pela especificidade
        extrema do vocabulário técnico. &ldquo;Licença de software&rdquo;, &ldquo;solução
        SaaS&rdquo;, &ldquo;infraestrutura de rede&rdquo;, &ldquo;banco de dados relacional&rdquo;,
        &ldquo;segurança da informação&rdquo; são termos com ocorrência praticamente
        exclusiva em editais de TI.
      </p>

      <p>
        Os casos de erro residual concentram-se em três situações: (1) editais de
        treinamento em informática para servidores, que podem cruzar com educação; (2)
        sistemas de controle de acesso físico, que cruzam com segurança patrimonial; e
        (3) equipamentos de impressão e digitalização, que às vezes aparecem em contextos
        administrativos amplos. Esses casos são tratados com configuração de exclusões
        específicas no perfil setorial.
      </p>

      <h3>Oportunidades que só a IA encontra em TI</h3>

      <p>
        Um padrão relevante identificado na análise de licitações de TI: uma parcela
        significativa dos editais relevantes não contém as palavras-chave óbvias do setor.
        Editais descritos como &ldquo;modernização administrativa&rdquo;, &ldquo;transformação
        digital&rdquo;, &ldquo;plataforma integrada de serviços ao cidadão&rdquo; ou
        &ldquo;automatização de processos de governo&rdquo; são, na prática, licitações
        de software e TI — mas passariam invisíveis em uma busca por palavras-chave
        simples.
      </p>

      <p>
        Sistemas que usam classificação por LLM em modo <em>zero-match</em> identificam
        esses editais com base em compreensão semântica, não em correspondência textual.
        Para empresas de desenvolvimento de software, consultoria em TI ou serviços de
        nuvem que atendem o setor público, essa capacidade representa acesso a um conjunto
        de oportunidades que competidores sem IA sistematicamente ignoram.
      </p>

      <BlogInlineCTA
        slug="ia-licitacoes-por-setor-saude-ti-engenharia"
        campaign="guias"
        ctaMessage="Editais do seu setor classificados por IA — Dado público verificável."
        ctaText="Testar Grátis"
      />

      <h2>Engenharia — vocabulário amplo, precisão moderada</h2>

      <h3>A complexidade da engenharia em licitações</h3>

      <p>
        Engenharia é um dos setores mais heterogêneos no mercado de licitações públicas.
        Sob essa denominação ampla estão licitações de construção civil, engenharia elétrica,
        engenharia mecânica, engenharia ambiental, geotecnia, topografia, projetos de
        arquitetura, restauração de obras históricas e engenharia de software industrial.
        Cada subsetor tem seu próprio vocabulário — e a sobreposição entre eles é considerável.
      </p>

      <p>
        Ao contrário de TI ou saúde, onde o léxico técnico é relativamente uniforme e
        padronizado por normas internacionais, a engenharia civil brasileira usa terminologia
        que varia por região, por tipo de obra e por porte do contrato. Um edital de
        &ldquo;pavimentação asfáltica&rdquo; no Nordeste e um de &ldquo;recapeamento
        de vias urbanas&rdquo; no Sul descrevem o mesmo objeto com vocabulário diferente.
      </p>

      <h3>88% a 91% de acurácia — e por que não é mais</h3>

      <p>
        A precisão de classificação em engenharia fica na faixa de <strong>88% a 91%</strong>,
        dependendo do subsetor. A razão para não alcançar os índices de TI e saúde é a
        sobreposição de vocabulário com outros setores.
      </p>

      <p>
        &ldquo;Manutenção de instalações&rdquo; pode ser engenharia ou facilities.
        &ldquo;Obras de saneamento&rdquo; pode ser engenharia civil ou saúde ambiental.
        &ldquo;Instalação de equipamentos&rdquo; pode ser engenharia mecânica ou
        fornecimento direto de produtos. Essas ambiguidades estruturais criam zonas cinzentas
        que exigem revisão humana — nenhum sistema de IA as elimina completamente.
      </p>

      <p>
        O que sistemas avançados fazem é reduzir essa zona cinzenta a um volume gerenciável.
        Em vez de revisar 200 editais por semana, o analista revisa 15 a 25 casos limítrofes.
        O ganho de produtividade é real mesmo com precisão de 89% — porque o baseline
        da classificação manual em engenharia, dado o volume, é próximo de 70% de eficiência
        (fadiga de análise, sobreposição de portais, descrições incompletas).
      </p>

      <h3>Subsetores que a IA diferencia</h3>

      <p>
        Dentro de engenharia, os subsetores com maior precisão de classificação são os
        que têm vocabulário mais específico: engenharia ambiental (termos como &ldquo;EIA/RIMA&rdquo;,
        &ldquo;passivo ambiental&rdquo;, &ldquo;licenciamento ambiental&rdquo; são
        exclusivos), geotecnia e topografia (&ldquo;levantamento planialtimétrico&rdquo;,
        &ldquo;sondagem SPT&rdquo;) e engenharia elétrica de alta tensão (&ldquo;subestação
        de energia&rdquo;, &ldquo;cabine primária&rdquo;).
      </p>

      <p>
        Construção civil genérica — reformas, ampliações, obras de menor porte — tem
        precisão ligeiramente inferior porque a linguagem dos editais é mais casual e
        variável. Para empresas focadas nesses subsetores, configurar listas de exclusão
        detalhadas (por exemplo, excluir editais que contenham &ldquo;limpeza&rdquo; ou
        &ldquo;manutenção de jardins&rdquo; junto com &ldquo;obras&rdquo;) melhora
        significativamente o sinal-ruído.
      </p>

      <h2>Facilities e Limpeza — o setor mais desafiador</h2>

      <p>
        Facilities e limpeza corporativa representam um paradoxo interessante no contexto
        da IA para licitações: é o setor mais difícil de classificar automaticamente —
        e ao mesmo tempo aquele onde a IA agrega mais valor.
      </p>

      <p>
        A precisão de classificação em facilities fica na faixa de <strong>85% a 88%</strong>,
        a mais baixa entre os grandes setores. A razão é estrutural: a descrição de um
        edital de facilities inevitavelmente cruza com construção civil (quando inclui
        manutenção predial), com saúde (quando inclui controle de vetores ou higienização
        hospitalar), com segurança (quando inclui vigilância e portaria) e com alimentação
        (quando inclui copa e cozinha).
      </p>

      <p>
        Um edital de &ldquo;terceirização de serviços gerais&rdquo; pode incluir limpeza,
        recepção, manutenção elétrica, jardinagem, controle de pragas e vigilância
        patrimonial no mesmo processo licitatório. Classificar isso em um único setor
        é, em certo sentido, a pergunta errada — o edital é genuinamente multissetorial.
      </p>

      <p>
        O paradoxo: é exatamente por essa complexidade que a IA agrega mais valor em
        facilities. A classificação manual em portais de licitação, sem ferramentas, é
        ainda menos precisa do que a classificação automática — porque o analista humano
        enfrenta o mesmo problema de sobreposição, com o agravante do volume. Há centenas
        de editais de &ldquo;serviços gerais&rdquo; publicados por semana em todo o Brasil.
        Nenhuma empresa de facilities consegue revisar tudo manualmente de forma sistemática.
        A IA, mesmo com 86% de precisão, filtra o volume de forma muito mais eficiente do
        que qualquer equipe humana sem ferramentas.
      </p>

      <h2>Tabela comparativa — IA por setor</h2>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-3 font-semibold text-ink">Setor</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Volume mensal (PNCP)</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Valor médio estimado</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Precisão IA</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Principal desafio</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-3 font-medium">
                <Link href="/licitacoes/informatica" className="text-brand-blue hover:underline">
                  Tecnologia da Informação
                </Link>
              </td>
              <td className="py-3 px-3 text-ink-secondary">Alto (entre os maiores)</td>
              <td className="py-3 px-3 text-ink-secondary">R$ 80K – R$ 2M</td>
              <td className="py-3 px-3"><strong>91%–93%</strong></td>
              <td className="py-3 px-3 text-ink-secondary">Editais de "modernização" sem palavras-chave explícitas</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">
                <Link href="/licitacoes/saude" className="text-brand-blue hover:underline">
                  Saúde
                </Link>
              </td>
              <td className="py-3 px-3 text-ink-secondary">Muito alto (maior volume)</td>
              <td className="py-3 px-3 text-ink-secondary">R$ 5K – R$ 10M</td>
              <td className="py-3 px-3"><strong>90%–92%</strong></td>
              <td className="py-3 px-3 text-ink-secondary">Editais mistos saúde + TI, saúde ambiental</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">
                <Link href="/licitacoes/engenharia" className="text-brand-blue hover:underline">
                  Engenharia Civil
                </Link>
              </td>
              <td className="py-3 px-3 text-ink-secondary">Alto (sazonalidade no 2º sem.)</td>
              <td className="py-3 px-3 text-ink-secondary">R$ 50K – R$ 5M</td>
              <td className="py-3 px-3"><strong>88%–91%</strong></td>
              <td className="py-3 px-3 text-ink-secondary">Sobreposição com facilities e manutenção predial</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">
                <Link href="/licitacoes/limpeza-e-facilities" className="text-brand-blue hover:underline">
                  Facilities e Limpeza
                </Link>
              </td>
              <td className="py-3 px-3 text-ink-secondary">Alto (distribuído no ano)</td>
              <td className="py-3 px-3 text-ink-secondary">R$ 30K – R$ 500K</td>
              <td className="py-3 px-3"><strong>85%–88%</strong></td>
              <td className="py-3 px-3 text-ink-secondary">Editais multissetoriais de "serviços gerais"</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Alimentação</td>
              <td className="py-3 px-3 text-ink-secondary">Médio</td>
              <td className="py-3 px-3 text-ink-secondary">R$ 10K – R$ 300K</td>
              <td className="py-3 px-3"><strong>89%–91%</strong></td>
              <td className="py-3 px-3 text-ink-secondary">Serviços de copa vs. fornecimento de refeições</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Segurança Patrimonial</td>
              <td className="py-3 px-3 text-ink-secondary">Médio</td>
              <td className="py-3 px-3 text-ink-secondary">R$ 100K – R$ 2M</td>
              <td className="py-3 px-3"><strong>90%–92%</strong></td>
              <td className="py-3 px-3 text-ink-secondary">Vigilância + sistemas eletrônicos (cruzamento com TI)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Meio Ambiente</td>
              <td className="py-3 px-3 text-ink-secondary">Baixo-médio</td>
              <td className="py-3 px-3 text-ink-secondary">R$ 50K – R$ 1M</td>
              <td className="py-3 px-3"><strong>89%–92%</strong></td>
              <td className="py-3 px-3 text-ink-secondary">Sobreposição com saúde ambiental e engenharia</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p>
        <em>Nota: os índices de precisão são estimativas baseadas em análise do pipeline
        do SmartLic. Variam conforme configuração de perfil, granularidade das exclusões
        e qualidade da descrição nos editais originais.</em>
      </p>

      <h2>Dados exclusivos da base de dados SmartLic</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Métricas setoriais — Pipeline SmartLic (PNCP + PCP v2 + ComprasGov v3)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>Cobertura total:</strong> 800K+ publicações/ano processadas via 3 fontes</li>
          <li><strong>TI — editais zero-match identificados por LLM:</strong> ~12% do total classificado no setor (sem palavras-chave explícitas)</li>
          <li><strong>Saúde — editais por municípios pequenos (&lt;50K hab.):</strong> 41% do volume, com maior variabilidade de redação</li>
          <li><strong>Engenharia — concentração 2º semestre:</strong> ~58% do volume anual publicado entre julho e dezembro</li>
          <li><strong>Facilities — média de sobreposição com outros setores:</strong> 3,2 setores por edital (dado estrutural do objeto)</li>
          <li><strong>Camadas de classificação ativadas por setor:</strong> TI 2,1 em média; Facilities 2,8 em média (mais camadas = mais ambiguidade)</li>
        </ul>
      </div>

      <p>
        Esses dados revelam um padrão importante: a complexidade da classificação por IA
        está diretamente correlacionada com a heterogeneidade do objeto licitado. Setores
        com objetos bem definidos e padronizados (TI, saúde especializada) são classificados
        com menos camadas e maior precisão. Setores com objetos amplos e variáveis (facilities,
        construção civil genérica) exigem mais camadas de análise e resultam em mais casos
        que precisam de revisão humana.
      </p>

      <p>
        A implicação prática: empresas de TI e saúde podem operar com menor intervenção
        humana na triagem — a IA resolve mais casos de forma autônoma. Empresas de facilities
        e construção civil se beneficiam igualmente da IA, mas precisam configurar seus
        perfis com mais cuidado e reservar tempo para revisar os casos limítrofes.
      </p>

      <p>
        Para ver como esses dados se aplicam ao seu setor específico, os artigos de
        <Link href="/blog/licitacoes-saude-2026" className="text-brand-blue hover:underline"> licitações de saúde em 2026</Link>,{' '}
        <Link href="/blog/licitacoes-ti-software-2026" className="text-brand-blue hover:underline">licitações de TI e software</Link> e{' '}
        <Link href="/blog/licitacoes-engenharia-2026" className="text-brand-blue hover:underline">licitações de engenharia</Link>{' '}
        apresentam análises verticais de cada setor com dados de volume, sazonalidade e
        oportunidades específicas.
      </p>

      <p>
        Para entender como a classificação por IA funciona do ponto de vista técnico —
        as três camadas, o modelo LLM usado e como os casos limítrofes são tratados —
        o artigo{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-blue hover:underline">
          Inteligência Artificial em Licitações: Como Funciona na Prática
        </Link>{' '}
        cobre o mecanismo completo.
      </p>

      <p>
        Para dados específicos sobre taxas de acerto e como avaliar a qualidade de um
        sistema de IA para licitações, veja o artigo sobre{' '}
        <Link href="/blog/ia-triagem-editais-filtrar-licitacoes" className="text-brand-blue hover:underline">
          triagem automática de editais por IA
        </Link>{' '}
        e sobre a{' '}
        <Link href="/blog/precisao-ia-licitacoes-taxa-acerto" className="text-brand-blue hover:underline">
          taxa de acerto da IA em licitações
        </Link>.
      </p>

      <h2>Perguntas frequentes</h2>

      <h3>Qual setor tem maior precisão na classificação de editais por IA?</h3>
      <p>
        Tecnologia da Informação (TI) é o setor com maior precisão de classificação por
        IA, atingindo entre 91% e 93%. O vocabulário técnico é altamente específico —
        termos como &ldquo;licença de software&rdquo;, &ldquo;infraestrutura de rede&rdquo;,
        &ldquo;solução em nuvem&rdquo; raramente aparecem fora de editais de TI. Saúde
        vem em segundo lugar, com 90% a 92%, também pela terminologia técnica padronizada.
      </p>

      <h3>Por que editais de facilities são mais difíceis para a IA classificar?</h3>
      <p>
        Editais de facilities e limpeza têm vocabulário que se sobrepõe a três ou mais
        outros setores simultaneamente. Um edital de &ldquo;manutenção predial e serviços
        gerais&rdquo; pode incluir limpeza, portaria, jardinagem, controle de pragas e
        manutenção elétrica — cada um pertencente a um setor diferente. Essa ambiguidade
        estrutural reduz a precisão de classificação para 85%–88%, mas a IA ainda supera
        a classificação manual dado o volume de publicações.
      </p>

      <h3>A IA consegue identificar editais de TI descritos como &ldquo;modernização&rdquo;?</h3>
      <p>
        Sim. Sistemas com classificação por LLM em modo <em>zero-match</em> identificam
        editais de TI mesmo quando não contêm palavras-chave explícitas. Um edital de
        &ldquo;transformação digital da administração pública&rdquo; é classificado
        corretamente por modelos de linguagem que entendem contexto semântico. Cerca de
        12% dos editais de TI identificados pelo SmartLic não contêm palavras-chave
        óbvias do setor.
      </p>

      <h3>Editais de engenharia têm muitos falsos positivos?</h3>
      <p>
        A taxa de falsos positivos em engenharia é ligeiramente maior do que em TI ou
        saúde, principalmente pela sobreposição com manutenção predial, construção e
        reformas. A precisão de 88%–91% significa que, em média, 1 em cada 10 editais
        classificados como engenharia pode não ser relevante para o perfil específico da
        empresa. Configurar exclusões específicas (termos que indicam outros setores)
        melhora significativamente esse índice.
      </p>

      <h3>Como a IA trata editais mistos, como saúde + TI?</h3>
      <p>
        Editais mistos — como sistemas de prontuário eletrônico ou equipamentos médicos
        com software embarcado — são classificados em múltiplos perfis setoriais quando
        o sistema suporta essa configuração. Isso aumenta o recall (menos oportunidades
        perdidas) ao custo de um leve aumento nos casos que precisam de revisão humana.
        Para empresas com portfólio híbrido, essa configuração é recomendada.
      </p>

      <h3>Vale a pena usar IA para monitorar apenas um setor?</h3>
      <p>
        Sim. O volume de publicações no PNCP — somando estados e municípios das 27 UFs
        — é alto o suficiente para justificar triagem automatizada mesmo em nichos
        específicos. Uma empresa de equipamentos médicos que monitora apenas saúde em
        5 estados ainda lida com centenas de editais por mês. A IA elimina o tempo
        gasto analisando editais irrelevantes e descobre oportunidades que passariam
        despercebidas — mesmo dentro de um único setor.
      </p>

      <h2>Fontes</h2>
      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          Portal Nacional de Contratações Públicas (PNCP) —{' '}
          <a href="https://pncp.gov.br" target="_blank" rel="noopener noreferrer" className="text-brand-blue hover:underline">
            pncp.gov.br
          </a>
        </li>
        <li>
          Lei nº 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos
        </li>
        <li>
          SmartLic — Pipeline de classificação setorial: PNCP + PCP v2 + ComprasGov v3
          (dados internos, 27 UFs × 15 setores)
        </li>
        <li>
          Ministério da Gestão e da Inovação em Serviços Públicos — Relatório de
          Compras Governamentais 2024
        </li>
        <li>
          Lei Complementar nº 123/2006 — Estatuto da Microempresa e Empresa de
          Pequeno Porte (benefícios ME/EPP em licitações)
        </li>
      </ul>
    </>
  );
}
