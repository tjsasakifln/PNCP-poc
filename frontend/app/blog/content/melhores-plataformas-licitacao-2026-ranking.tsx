import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — BOFU-02: Melhores Plataformas de Licitação 2026
 *
 * Content cluster: comparação BOFU (fundo de funil)
 * Target: ~3,000 words | Primary KW: melhores plataformas de licitação 2026
 */
export default function MelhoresPlataformasLicitacao2026Ranking() {
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
                name: 'Quais são as melhores plataformas de licitação em 2026?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'As principais plataformas de inteligência em licitações em 2026 são: SmartLic (foco em IA de classificação setorial e análise de viabilidade), Effecti (maior base instalada, foco em automação de documentos), Licitanet (foco em pregão eletrônico e disputa online), LicitaWeb (foco em gestão interna de processos) e Portal de Compras Públicas (plataforma pública de pregão eletrônico). A escolha depende do porte da empresa, setores de atuação e fase do processo licitatório.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto custa uma plataforma de licitação por mês?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os preços variam de R$ 0 (portais públicos como PNCP e ComprasGov) a R$ 2.000+/mês para soluções enterprise. Plataformas de inteligência como SmartLic custam entre R$ 297 e R$ 397/mês. Plataformas de gestão documental como Effecti variam de R$ 500 a R$ 1.500/mês dependendo do plano. Ferramentas de disputa como Licitanet cobram por sessão ou mensalidade fixa.',
                },
              },
              {
                '@type': 'Question',
                name: 'Preciso de plataforma se já uso o PNCP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O PNCP é um portal de publicação, não uma plataforma de inteligência. Ele lista editais, mas não oferece classificação setorial, análise de viabilidade, consolidação multi-fonte ou pipeline de oportunidades. Plataformas complementam o PNCP adicionando camadas de triagem, monitoramento e análise que o portal público não oferece.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual plataforma de licitação tem inteligência artificial?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Em abril de 2026, o SmartLic é a principal plataforma com IA integrada para classificação setorial (GPT-4.1-nano) e análise de viabilidade automática com 4 fatores. Effecti utiliza automação baseada em regras para documentos, mas não tem classificação por IA. Licitanet e LicitaWeb não oferecem classificação automática de editais.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como escolher a plataforma de licitação certa para minha empresa?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Avalie três critérios: (1) em que fase do processo licitatório você precisa de ajuda — descoberta de editais, análise, elaboração de proposta ou disputa; (2) quantas UFs e setores você monitora — plataformas com maior cobertura geográfica fazem diferença acima de 3 UFs; (3) volume mensal de editais disputados — abaixo de 5/mês, ferramentas gratuitas podem ser suficientes.',
                },
              },
              {
                '@type': 'Question',
                name: 'Vale a pena pagar por plataforma de licitação sendo MEI ou microempresa?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Depende do faturamento B2G. Se licitações representam mais de 30% da receita e o volume ultrapassa 10 editais/mês, o investimento se paga em economia de tempo. Para MEIs com faturamento B2G inferior a R$ 50.000/ano, ferramentas gratuitas (PNCP + planilha) são mais adequadas. O SmartLic oferece trial de 14 dias sem cartão para avaliar o retorno antes de comprometer orçamento.',
                },
              },
              {
                '@type': 'Question',
                name: 'Effecti ou SmartLic: qual é melhor?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'São plataformas com focos diferentes. A Effecti tem maior base instalada e foco em automação de documentos para a fase de proposta. O SmartLic foca em inteligência na fase de descoberta e triagem, com classificação por IA e análise de viabilidade. Se o gargalo da empresa é encontrar os editais certos, SmartLic. Se é montar a documentação, Effecti. Muitas empresas usam ambas em etapas complementares.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O mercado de <strong>plataformas de licitação</strong> no Brasil cresceu
        significativamente após a Lei 14.133/2021 consolidar o PNCP como portal
        único. Com mais de 800.000 publicações por ano no PNCP, somadas às
        fontes secundárias (PCP, ComprasGov), nenhuma empresa B2G de médio ou
        grande porte consegue operar eficientemente apenas com busca manual.
        Este ranking compara as principais plataformas disponíveis em 2026,
        com critérios objetivos e dados verificáveis.
      </p>

      <h2>Critérios do ranking</h2>

      <p>
        Cada plataforma foi avaliada em 6 dimensões relevantes para a operação
        diária de uma empresa que participa de licitações:
      </p>

      <ol className="list-decimal pl-6 space-y-2">
        <li>
          <strong>Cobertura de fontes:</strong> quantos portais de licitação a
          plataforma consolida (PNCP, PCP, ComprasGov, Diários Oficiais, etc.).
        </li>
        <li>
          <strong>Inteligência/IA:</strong> se oferece classificação automática,
          análise de viabilidade ou scoring de editais — ou apenas busca por
          palavras-chave.
        </li>
        <li>
          <strong>Cobertura geográfica:</strong> quantas UFs e esferas
          (federal, estadual, municipal) são cobertas.
        </li>
        <li>
          <strong>Fase do processo atendida:</strong> descoberta, análise,
          proposta, disputa, ou todas.
        </li>
        <li>
          <strong>Preço e modelo de cobrança:</strong> mensalidade fixa, por
          sessão, por usuário, ou por módulo.
        </li>
        <li>
          <strong>Facilidade de uso:</strong> tempo até valor (time-to-value)
          para um novo usuário.
        </li>
      </ol>

      <p>
        Este ranking reflete o estado do mercado em abril de 2026. Preços e
        funcionalidades podem ter mudado após a publicação. Recomendamos
        verificar diretamente nos sites oficiais antes de contratar.
      </p>

      <h2>Ranking comparativo: 5 plataformas de licitação em 2026</h2>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-2 font-semibold text-ink">Critério</th>
              <th className="text-left py-3 px-2 font-semibold text-ink">SmartLic</th>
              <th className="text-left py-3 px-2 font-semibold text-ink">Effecti</th>
              <th className="text-left py-3 px-2 font-semibold text-ink">Licitanet</th>
              <th className="text-left py-3 px-2 font-semibold text-ink">LicitaWeb</th>
              <th className="text-left py-3 px-2 font-semibold text-ink">PCP</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-2 font-medium">Foco principal</td>
              <td className="py-3 px-2">Inteligência + triagem</td>
              <td className="py-3 px-2">Automação documental</td>
              <td className="py-3 px-2">Disputa online</td>
              <td className="py-3 px-2">Gestão interna</td>
              <td className="py-3 px-2">Pregão eletrônico</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Fontes consolidadas</td>
              <td className="py-3 px-2">PNCP + PCP + ComprasGov</td>
              <td className="py-3 px-2">PNCP + Diários Oficiais</td>
              <td className="py-3 px-2">PCP (operação direta)</td>
              <td className="py-3 px-2">PNCP</td>
              <td className="py-3 px-2">PCP (portal próprio)</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Classificação por IA</td>
              <td className="py-3 px-2">Sim (GPT-4.1-nano)</td>
              <td className="py-3 px-2">Não (regras)</td>
              <td className="py-3 px-2">Não</td>
              <td className="py-3 px-2">Não</td>
              <td className="py-3 px-2">Não</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Análise de viabilidade</td>
              <td className="py-3 px-2">4 fatores automáticos</td>
              <td className="py-3 px-2">Manual/checklist</td>
              <td className="py-3 px-2">Não</td>
              <td className="py-3 px-2">Básica</td>
              <td className="py-3 px-2">Não</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Cobertura UFs</td>
              <td className="py-3 px-2">27 UFs</td>
              <td className="py-3 px-2">27 UFs</td>
              <td className="py-3 px-2">27 UFs</td>
              <td className="py-3 px-2">Variável</td>
              <td className="py-3 px-2">27 UFs</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Setores pré-configurados</td>
              <td className="py-3 px-2">15 setores</td>
              <td className="py-3 px-2">Customizável</td>
              <td className="py-3 px-2">N/A</td>
              <td className="py-3 px-2">Customizável</td>
              <td className="py-3 px-2">N/A</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Pipeline visual</td>
              <td className="py-3 px-2">Kanban drag-and-drop</td>
              <td className="py-3 px-2">Sim</td>
              <td className="py-3 px-2">Não</td>
              <td className="py-3 px-2">Sim</td>
              <td className="py-3 px-2">Não</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Exportação Excel</td>
              <td className="py-3 px-2">Sim (com resumo IA)</td>
              <td className="py-3 px-2">Sim</td>
              <td className="py-3 px-2">Limitada</td>
              <td className="py-3 px-2">Sim</td>
              <td className="py-3 px-2">Limitada</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Elaboração de propostas</td>
              <td className="py-3 px-2">Não (foco em triagem)</td>
              <td className="py-3 px-2">Sim (diferencial)</td>
              <td className="py-3 px-2">Parcial</td>
              <td className="py-3 px-2">Sim</td>
              <td className="py-3 px-2">Não</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Preço mensal (ref.)</td>
              <td className="py-3 px-2">R$ 297-397</td>
              <td className="py-3 px-2">R$ 500-1.500</td>
              <td className="py-3 px-2">Por sessão</td>
              <td className="py-3 px-2">R$ 300-800</td>
              <td className="py-3 px-2">Gratuito (órgãos)</td>
            </tr>
            <tr>
              <td className="py-3 px-2 font-medium">Trial gratuito</td>
              <td className="py-3 px-2">14 dias, sem cartão</td>
              <td className="py-3 px-2">Demo agendada</td>
              <td className="py-3 px-2">Não informado</td>
              <td className="py-3 px-2">Variável</td>
              <td className="py-3 px-2">N/A</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="text-sm text-ink-secondary italic">
        Nota: preços são referências de abril/2026, obtidos em sites públicos
        das respectivas plataformas. Verifique diretamente para valores
        atualizados.
      </p>

      <BlogInlineCTA
        slug="melhores-plataformas-licitacao-2026-ranking"
        campaign="guias"
        ctaMessage="Plataforma com IA de classificação setorial — Dado público verificável."
        ctaText="Começar Trial Gratuito"
      />

      <h2>Análise detalhada por plataforma</h2>

      <h3>SmartLic — Inteligência na descoberta de editais</h3>

      <p>
        O SmartLic é uma plataforma focada na fase de <strong>descoberta e
        triagem</strong> de licitações. Seu diferencial é a classificação
        setorial por IA (GPT-4.1-nano), que categoriza automaticamente cada
        edital em 1 de 15 setores pré-configurados — mesmo quando o objeto
        do edital usa terminologia incomum ou genérica.
      </p>

      <p>
        Além da classificação, oferece análise de viabilidade com 4 fatores
        (modalidade, prazo, valor estimado e geografia), consolidação de 3
        fontes (PNCP, PCP v2, ComprasGov v3) com deduplicação automática,
        pipeline Kanban para gestão de oportunidades, e exportação Excel
        com resumo gerado por IA.
      </p>

      <p>
        <strong>Ponto forte:</strong> único com IA integrada para classificação
        e viabilidade. Elimina editais irrelevantes antes de chegarem ao
        analista.
      </p>
      <p>
        <strong>Ponto fraco:</strong> não oferece elaboração de propostas nem
        disputa online. Focado na etapa de inteligência, não na execução.
      </p>

      <h3>Effecti — Automação documental para propostas</h3>

      <p>
        A Effecti é a plataforma com maior base instalada no mercado B2G
        brasileiro. Seu foco é a <strong>automação de documentos</strong> para
        elaboração de propostas: templates, checklist de habilitação, controle
        de certidões e montagem automatizada de documentação técnica.
      </p>

      <p>
        Também oferece monitoramento de editais via PNCP e Diários Oficiais,
        mas sem classificação por IA — a triagem é baseada em
        palavras-chave e regras configuráveis.
      </p>

      <p>
        <strong>Ponto forte:</strong> maturidade do produto e foco na fase de
        proposta (onde muitas empresas perdem mais tempo).
      </p>
      <p>
        <strong>Ponto fraco:</strong> preço mais elevado; triagem sem IA pode
        gerar mais ruído em setores com terminologia variada. Para uma
        comparação detalhada, veja{' '}
        <Link href="/blog/smartlic-vs-effecti-comparacao-2026">
          SmartLic vs Effecti: comparação completa
        </Link>
        .
      </p>

      <h3>Licitanet — Foco na disputa eletrônica</h3>

      <p>
        A Licitanet opera como plataforma de <strong>pregão
        eletrônico</strong> — é o ambiente onde a disputa acontece, não uma
        ferramenta de inteligência. Órgãos públicos usam a Licitanet para
        realizar pregões, e fornecedores se cadastram para participar.
      </p>

      <p>
        <strong>Ponto forte:</strong> acesso direto a pregões que acontecem
        na plataforma (sem precisar do PNCP).
      </p>
      <p>
        <strong>Ponto fraco:</strong> não oferece triagem, análise de
        viabilidade, pipeline ou exportação. É complementar a uma ferramenta
        de inteligência, não substituta.
      </p>

      <h3>LicitaWeb — Gestão interna de processos</h3>

      <p>
        A LicitaWeb é voltada para a <strong>gestão interna do setor de
        licitações</strong>: controle de prazos, documentos, responsáveis e
        status de cada processo. Funciona como um ERP simplificado para
        equipes que precisam organizar muitos processos simultâneos.
      </p>

      <p>
        <strong>Ponto forte:</strong> organização interna e controle de
        workflows para equipes com 3+ analistas.
      </p>
      <p>
        <strong>Ponto fraco:</strong> cobertura de fontes limitada; sem IA
        para triagem; melhor como complemento do que como ferramenta única.
      </p>

      <h3>Portal de Compras Públicas (PCP) — Plataforma pública gratuita</h3>

      <p>
        O PCP é uma plataforma de <strong>pregão eletrônico</strong> utilizada
        por órgãos públicos como alternativa ao ComprasGov. É gratuito para
        fornecedores no acesso básico. Processa milhares de sessões de
        pregão por mês.
      </p>

      <p>
        <strong>Ponto forte:</strong> custo zero; acesso direto a editais do
        portal; volume relevante de oportunidades.
      </p>
      <p>
        <strong>Ponto fraco:</strong> é um portal de operação, não de
        inteligência. Sem classificação, sem viabilidade, sem pipeline.
        Complementar, não substituto.
      </p>

      <h2>Qual plataforma escolher: guia por perfil de empresa</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Recomendação por perfil
        </p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li>
            <strong>PME que está começando em B2G ({"<"}10 editais/mês):</strong>{' '}
            PNCP gratuito + planilha Excel. Não precisa investir em plataforma
            ainda.{' '}
            <Link href="/blog/smartlic-vs-planilha-excel-quando-automatizar">
              Quando automatizar vale a pena
            </Link>
            .
          </li>
          <li>
            <strong>Empresa B2G em crescimento (10-50 editais/mês):</strong>{' '}
            SmartLic para triagem inteligente + Excel para propostas. ROI
            positivo a partir do primeiro mês.
          </li>
          <li>
            <strong>Empresa B2G consolidada (50+ editais/mês):</strong>{' '}
            SmartLic (triagem) + Effecti (propostas). As duas plataformas
            cobrem etapas complementares do processo.
          </li>
          <li>
            <strong>Consultoria de licitações:</strong>{' '}
            SmartLic para inteligência sobre múltiplos clientes e setores
            simultaneamente. Volume justifica o investimento.{' '}
            <Link href="/blog/escalar-consultoria-sem-depender-horas-tecnicas">
              Como escalar consultoria com automação
            </Link>
            .
          </li>
          <li>
            <strong>Empresa que já participa de pregão no PCP/Licitanet:</strong>{' '}
            Complementar com SmartLic ou Effecti para a fase de
            descoberta/análise que precede a disputa.
          </li>
        </ul>
      </div>

      <h2>O papel da IA no futuro das plataformas de licitação</h2>

      <p>
        A Lei 14.133/2021 e a consolidação do PNCP criaram um volume de dados
        públicos estruturados sem precedente no Brasil — mais de 2 milhões de
        publicações indexáveis. Esse volume é grande demais para análise humana
        e estruturado demais para não ser processado por IA.
      </p>

      <p>
        Em 2026, o SmartLic é a única plataforma com classificação por LLM
        (large language model) integrada ao fluxo de busca. A tendência é que
        concorrentes adotem abordagens similares nos próximos 12-18 meses.
        Para o usuário, isso significa que a{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona">
          inteligência artificial em licitações
        </Link>{' '}
        deixará de ser diferencial competitivo e passará a ser requisito
        básico — como aconteceu com busca por palavras-chave nos anos 2010.
      </p>

      <p>
        A vantagem de adotar cedo é dupla: economia imediata de tempo e
        construção de histórico de dados que alimentam decisões futuras
        cada vez mais precisas.
      </p>

      <h2>Dados do mercado: volume do PNCP por modalidade</h2>

      <p>
        Para contextualizar o tamanho do mercado que essas plataformas atendem,
        o PNCP registrou em 2025 a seguinte distribuição por modalidade de
        contratação:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Pregão Eletrônico:</strong> ~65% das publicações — maior volume,
            principal modalidade para compras e serviços comuns.
          </li>
          <li>
            <strong>Dispensa de licitação (art. 75):</strong> ~20% — volume
            crescente após a Lei 14.133/2021 ampliar as hipóteses de dispensa.
          </li>
          <li>
            <strong>Concorrência:</strong> ~8% — obras e serviços de maior
            complexidade técnica.
          </li>
          <li>
            <strong>Inexigibilidade:</strong> ~5% — contratação direta para
            serviços com fornecedor exclusivo.
          </li>
          <li>
            <strong>Outras (leilão, diálogo competitivo):</strong> ~2%
          </li>
        </ul>
        <p className="text-xs text-ink-secondary mt-3">
          Fonte: PNCP, dados agregados 2025. Percentuais aproximados baseados
          em volume de publicações (não valor).
        </p>
      </div>

      <h2>Veredito honesto</h2>

      <p>
        Não existe &ldquo;a melhor plataforma&rdquo; — existe a mais adequada
        para o perfil e a fase da empresa. O mercado tem soluções
        complementares, não substitutas.
      </p>

      <p>
        <strong>Para inteligência e triagem:</strong> SmartLic é a opção com
        maior diferenciação em 2026, pela classificação por IA e análise de
        viabilidade automática. É ideal para quem perde mais tempo
        encontrando e filtrando editais do que elaborando propostas.
      </p>

      <p>
        <strong>Para automação de propostas:</strong> Effecti é a referência
        com maior maturidade. Se o gargalo é montar documentação, não
        encontrar editais, é a escolha mais prática.
      </p>

      <p>
        <strong>Para operação de disputa:</strong> PCP e Licitanet são
        plataformas de execução. Não substituem ferramentas de inteligência,
        mas são onde o pregão efetivamente acontece.
      </p>

      <p>
        <strong>Para quem está começando:</strong> PNCP + planilha.{' '}
        <Link href="/blog/como-participar-primeira-licitacao-2026">
          Guia de como participar da primeira licitação
        </Link>{' '}
        sem investimento em ferramentas.
      </p>

      <h2>Perguntas frequentes</h2>

      <h3>Quais são as melhores plataformas de licitação em 2026?</h3>
      <p>
        As principais são SmartLic (IA de classificação setorial e viabilidade),
        Effecti (automação de documentos), Licitanet (disputa eletrônica),
        LicitaWeb (gestão interna) e Portal de Compras Públicas (pregão
        eletrônico gratuito). A escolha depende do porte, setores e fase do
        processo.
      </p>

      <h3>Quanto custa uma plataforma de licitação por mês?</h3>
      <p>
        De R$ 0 (portais públicos) a R$ 2.000+/mês (soluções enterprise).
        SmartLic custa R$ 297-397/mês. Effecti varia de R$ 500 a R$ 1.500/mês.
        Licitanet cobra por sessão. Verifique preços atualizados nos sites
        oficiais.
      </p>

      <h3>Preciso de plataforma se já uso o PNCP?</h3>
      <p>
        O PNCP é um portal de publicação, não de inteligência. Plataformas
        complementam adicionando classificação, viabilidade, consolidação
        multi-fonte e pipeline — funcionalidades que o portal público não
        oferece.
      </p>

      <h3>Qual plataforma de licitação tem inteligência artificial?</h3>
      <p>
        Em abril de 2026, o SmartLic é a principal com IA integrada (GPT-4.1-nano)
        para classificação setorial e viabilidade automática. Effecti usa
        automação baseada em regras. Licitanet e LicitaWeb não oferecem
        classificação automática.
      </p>

      <h3>Como escolher a plataforma certa para minha empresa?</h3>
      <p>
        Avalie: (1) em que fase do processo precisa de ajuda — descoberta,
        análise, proposta ou disputa; (2) quantas UFs e setores monitora; (3)
        volume mensal de editais. Abaixo de 5/mês, ferramentas gratuitas podem
        ser suficientes.
      </p>

      <h3>Vale a pena pagar por plataforma sendo MEI ou microempresa?</h3>
      <p>
        Se licitações representam mais de 30% da receita e o volume ultrapassa
        10 editais/mês, sim. Para MEIs com faturamento B2G inferior a
        R$ 50.000/ano, PNCP + planilha são mais adequados.{' '}
        <Link href="/blog/mei-microempresa-vantagens-licitacoes">
          Vantagens de MEI/ME em licitações
        </Link>
        .
      </p>

      <h3>Effecti ou SmartLic: qual é melhor?</h3>
      <p>
        São complementares, não substitutas. Effecti foca em automação de
        documentos (proposta). SmartLic foca em inteligência na descoberta
        e triagem. Se o gargalo é encontrar editais certos, SmartLic.
        Se é montar documentação, Effecti.
      </p>

      <h2>Fontes</h2>

      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br) — dados agregados 2025-2026
        </li>
        <li>
          Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos
        </li>
        <li>
          Sites oficiais das plataformas citadas — preços e funcionalidades verificados em abril/2026
        </li>
        <li>
          SmartLic base de dados — dados de processamento e classificação, 800K+ publicações analisadas
        </li>
        <li>
          Painel de Compras do Governo Federal — distribuição por modalidade 2024-2025
        </li>
      </ul>
    </>
  );
}
