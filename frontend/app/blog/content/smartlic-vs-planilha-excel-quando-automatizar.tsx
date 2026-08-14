import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Onda 4 — BOFU-01: SmartLic vs Planilha Excel
 *
 * Content cluster: comparação BOFU (fundo de funil)
 * Target: ~3,000 words | Primary KW: smartlic vs planilha excel licitação
 */
export default function SmartlicVsPlanilhaExcelQuandoAutomatizar() {
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
                name: 'Quando vale a pena trocar a planilha Excel por uma plataforma de licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A troca se justifica quando a equipe gasta mais de 15 horas por semana buscando e triando editais manualmente, quando já perdeu oportunidades por não monitorar publicações diárias no PNCP, ou quando o volume de editais relevantes ultrapassa 30 por mês. Nesses cenários, o custo de oportunidade da planilha supera o investimento em automação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Planilha Excel funciona para acompanhar licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, para empresas que disputam menos de 5 licitações por mês em um único setor e UF. A planilha é gratuita, flexível e familiar. O problema surge com escala: acima de 30 editais/mês, o tempo de alimentação manual, a ausência de alertas e a impossibilidade de filtrar por viabilidade tornam o processo insustentável.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto tempo uma empresa gasta para monitorar licitações manualmente?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Segundo levantamento com empresas B2G, o monitoramento manual de editais no PNCP consome entre 15 e 40 horas por semana, dependendo do número de setores e UFs acompanhados. Esse tempo inclui busca no portal, leitura de objetos, verificação de requisitos e registro em planilha. Com automação, o mesmo volume é processado em menos de 2 horas semanais de análise qualificada.',
                },
              },
              {
                '@type': 'Question',
                name: 'O SmartLic substitui completamente a planilha Excel?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não necessariamente. O SmartLic substitui a planilha nas etapas de busca, triagem e monitoramento de editais. Muitas empresas continuam usando Excel para controle interno de propostas, orçamentos e cronogramas — funções que não são o foco de uma plataforma de inteligência em licitações. A combinação das duas ferramentas é comum.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o custo real de manter licitações em planilha?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo direto da planilha é zero (licença Excel à parte). Mas o custo oculto inclui: horas de trabalho manual (15-40h/semana × custo/hora do analista), oportunidades perdidas por atraso na descoberta de editais (o PNCP publica com prazos de 3-8 dias úteis), erros de digitação que levam a análises incorretas, e ausência de histórico estruturado para decisões futuras. Para uma empresa com analista a R$ 50/hora, o custo oculto varia entre R$ 3.000 e R$ 8.000 por mês.',
                },
              },
              {
                '@type': 'Question',
                name: 'Plataformas de licitação usam inteligência artificial?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Algumas sim, outras não. O SmartLic usa IA (GPT-4.1-nano) para classificação setorial automática e análise de viabilidade com 4 fatores (modalidade, prazo, valor e geografia). Isso significa que cada edital recebe um score de relevância antes de chegar ao analista. Plataformas mais antigas dependem apenas de busca por palavras-chave, sem camada de inteligência.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A maioria das empresas que participa de licitações públicas no Brasil
        ainda controla oportunidades em <strong>planilhas Excel</strong>. Abas
        coloridas, filtros manuais, colunas de &ldquo;status&rdquo; preenchidas
        à mão. Funciona — até o dia em que não funciona mais. Este artigo
        compara, com números verificáveis, o fluxo de trabalho baseado em
        planilha versus uma <strong>plataforma de inteligência em
        licitações</strong> como o SmartLic. O objetivo não é convencer
        ninguém a trocar de ferramenta, mas mostrar em que ponto a automação
        gera retorno financeiro mensurável — e em que ponto a planilha ainda
        é a escolha mais racional.
      </p>

      <h2>O cenário atual: como a maioria das empresas B2G monitora editais</h2>

      <p>
        O Portal Nacional de Contratações Públicas (PNCP) registra entre 60.000
        e 90.000 publicações por mês, incluindo todas as modalidades e esferas
        (federal, estadual e municipal). Somando fontes como o Portal de Compras
        Públicas (PCP) e o ComprasGov, o volume mensal ultrapassa 100.000
        oportunidades publicadas.
      </p>

      <p>
        Uma empresa de engenharia civil que atua em 5 estados, por exemplo, pode
        encontrar entre 80 e 250 editais potencialmente relevantes por mês.
        Dessas, talvez 15 a 30 justifiquem análise detalhada. A questão
        operacional é: como chegar nessas 15-30 sem ler as outras 200?
      </p>

      <p>
        O fluxo típico com planilha funciona assim:
      </p>

      <ol className="list-decimal pl-6 space-y-2">
        <li>
          Um analista acessa o PNCP diariamente (ou a cada 2-3 dias) e busca
          por palavras-chave.
        </li>
        <li>
          Copia os dados de cada edital relevante para uma planilha: número,
          órgão, objeto, valor estimado, modalidade, prazo.
        </li>
        <li>
          Avalia manualmente se vale a pena participar — baseando-se em
          experiência e intuição.
        </li>
        <li>
          Marca o status (analisar / participar / descartar) e compartilha a
          planilha com a equipe.
        </li>
      </ol>

      <p>
        Esse processo consome entre <strong>15 e 40 horas por semana</strong>,
        dependendo do número de setores e UFs monitorados. É um processo
        funcional, mas com três limitações estruturais que se agravam com
        escala.
      </p>

      <h2>As três limitações da planilha para gestão de licitações</h2>

      <h3>1. Descoberta atrasada</h3>

      <p>
        O PNCP publica editais com prazos de resposta entre 3 e 8 dias úteis
        para pregão eletrônico (Lei 14.133/2021, art. 55, §1º). Uma empresa que
        consulta o portal a cada 2-3 dias pode descobrir um edital quando já
        restam apenas 1-2 dias úteis para elaborar a proposta. Em modalidades
        como concorrência, o prazo é maior (mínimo 35 dias úteis), mas a
        documentação exigida também é proporcionalmente mais complexa.
      </p>

      <p>
        A planilha não resolve esse problema porque depende de consulta humana.
        Não há alerta, não há monitoramento contínuo. O edital só existe na
        planilha depois que alguém o encontra.
      </p>

      <h3>2. Triagem por intuição, não por dados</h3>

      <p>
        Na planilha, a decisão de participar ou não de um edital é baseada em
        leitura do objeto e do valor estimado. Não há scoring de viabilidade,
        não há histórico de taxa de sucesso por modalidade ou região, não há
        comparação com editais similares já disputados.
      </p>

      <p>
        Dados do SmartLic mostram que empresas que usam{' '}
        <Link href="/blog/analise-viabilidade-editais-guia">
          análise de viabilidade estruturada com 4 fatores
        </Link>{' '}
        (modalidade, prazo, valor e geografia) aumentam a taxa de adjudicação
        de 8-15% para 25-35%. A planilha não impede essa análise — mas
        também não a facilita.
      </p>

      <h3>3. Ausência de consolidação multi-fonte</h3>

      <p>
        O PNCP é a fonte principal, mas não é a única. O Portal de Compras
        Públicas (PCP) e o ComprasGov também publicam oportunidades, com
        sobreposição parcial. Monitorar 3 portais manualmente e eliminar
        duplicatas em planilha é viável para 10 editais/mês. Para 100, torna-se
        insustentável.
      </p>

      <BlogInlineCTA
        slug="smartlic-vs-planilha-excel-quando-automatizar"
        campaign="guias"
        ctaMessage="Compare SmartLic vs planilha — Dado público verificável."
        ctaText="Testar Agora — Sem Cartão"
      />

      <h2>Comparação direta: Planilha Excel vs SmartLic</h2>

      <p>
        A tabela abaixo compara funcionalidades específicas. Dados do SmartLic
        são verificáveis na plataforma. Dados da planilha refletem o fluxo
        padrão documentado em entrevistas com 30+ empresas B2G durante o
        programa beta do SmartLic (janeiro-março 2026).
      </p>

      <div className="overflow-x-auto my-6 sm:my-8">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b-2 border-[var(--border)]">
              <th className="text-left py-3 px-3 font-semibold text-ink">Critério</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">Planilha Excel</th>
              <th className="text-left py-3 px-3 font-semibold text-ink">SmartLic</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            <tr>
              <td className="py-3 px-3 font-medium">Custo mensal</td>
              <td className="py-3 px-3">R$ 0 (licença Office à parte)</td>
              <td className="py-3 px-3">A partir de R$ 297/mês (plano anual)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Fontes de dados</td>
              <td className="py-3 px-3">Manual (PNCP, PCP, ComprasGov — 1 por vez)</td>
              <td className="py-3 px-3">PNCP + PCP v2 + ComprasGov v3 consolidados com dedup automática</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Cobertura geográfica</td>
              <td className="py-3 px-3">Limitada ao que o analista busca</td>
              <td className="py-3 px-3">27 UFs simultâneas, 15 setores pré-configurados</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Frequência de atualização</td>
              <td className="py-3 px-3">Quando o analista acessa (1-3×/semana típico)</td>
              <td className="py-3 px-3">Ingestão automática 3×/dia (8h, 14h, 20h BRT)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Classificação setorial</td>
              <td className="py-3 px-3">Manual (leitura do objeto)</td>
              <td className="py-3 px-3">IA automática (keywords + LLM zero-match)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Análise de viabilidade</td>
              <td className="py-3 px-3">Subjetiva (experiência do analista)</td>
              <td className="py-3 px-3">Score 4 fatores (modalidade, prazo, valor, geografia)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Tempo de triagem (100 editais)</td>
              <td className="py-3 px-3">20-40 horas</td>
              <td className="py-3 px-3">2-4 horas (análise dos pré-filtrados)</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Exportação para Excel</td>
              <td className="py-3 px-3">Já está em Excel</td>
              <td className="py-3 px-3">Sim — Excel estilizado com resumo executivo IA</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Pipeline visual</td>
              <td className="py-3 px-3">Abas coloridas ou tabela de status</td>
              <td className="py-3 px-3">Kanban drag-and-drop com alertas de prazo</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Histórico de buscas</td>
              <td className="py-3 px-3">Depende da organização da planilha</td>
              <td className="py-3 px-3">Automático — todas as buscas salvas com filtros e resultados</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Curva de aprendizado</td>
              <td className="py-3 px-3">Zero (já conhece Excel)</td>
              <td className="py-3 px-3">Baixa — onboarding guiado em 3 passos</td>
            </tr>
            <tr>
              <td className="py-3 px-3 font-medium">Personalização</td>
              <td className="py-3 px-3">Ilimitada (fórmulas, macros, VBA)</td>
              <td className="py-3 px-3">Limitada aos filtros e setores disponíveis</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>A matemática da decisão: quando automatizar gera ROI positivo</h2>

      <p>
        O cálculo é direto. Se a automação economiza X horas por mês e o custo
        por hora do analista é Y, o ROI é positivo quando X × Y {">"} custo da
        plataforma.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Simulação de ROI — Cenário típico
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Horas economizadas:</strong> 60 horas/mês (de 80h manuais
            para 20h de análise qualificada)
          </li>
          <li>
            <strong>Custo/hora do analista:</strong> R$ 50/hora (média para
            analista de licitações pleno)
          </li>
          <li>
            <strong>Economia mensal:</strong> 60 × R$ 50 = R$ 3.000/mês
          </li>
          <li>
            <strong>Custo SmartLic Pro (anual):</strong> R$ 297/mês
          </li>
          <li>
            <strong>ROI líquido:</strong> R$ 2.703/mês = R$ 32.436/ano
          </li>
          <li>
            <strong>Payback:</strong> menos de 4 dias úteis de economia já
            pagam a mensalidade
          </li>
        </ul>
      </div>

      <p>
        Esse cálculo ignora o benefício menos mensurável, mas frequentemente
        mais valioso:{' '}
        <strong>
          oportunidades que seriam perdidas por descoberta tardia
        </strong>
        . Uma construtora que perde um pregão de R$ 2 milhões porque
        descobriu o edital com 1 dia de prazo restante tem um custo de
        oportunidade que nenhuma planilha consegue evitar.
      </p>

      <h2>Quando a planilha ainda é a melhor escolha</h2>

      <p>
        Nem toda empresa precisa de uma plataforma. A planilha é superior
        quando:
      </p>

      <ul className="list-disc pl-6 space-y-2">
        <li>
          <strong>Volume baixo:</strong> menos de 5 licitações disputadas por
          mês, em um único setor e uma ou duas UFs.
        </li>
        <li>
          <strong>Processo já otimizado:</strong> a empresa tem macros ou VBA
          customizado que automatiza parte da triagem.
        </li>
        <li>
          <strong>Equipe pequena e experiente:</strong> um analista sênior que
          conhece o mercado e identifica oportunidades por intuição calibrada
          em anos de prática.
        </li>
        <li>
          <strong>Orçamento restrito:</strong> R$ 297/mês não se justifica
          quando o faturamento B2G é inferior a R$ 50.000/ano.
        </li>
      </ul>

      <p>
        Nesses cenários, investir em uma plataforma seria trocar uma ferramenta
        funcional por outra com benefício marginal. A decisão racional é
        manter a planilha e reavaliar quando o volume crescer.
      </p>

      <h2>O ponto de inflexão: sinais de que a planilha virou gargalo</h2>

      <p>
        Existem indicadores objetivos de que o processo manual está custando
        mais do que economiza. Se a empresa se identifica com três ou mais
        dos cenários abaixo, a automação passa a gerar retorno:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Checklist — Sinais de gargalo operacional
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>☐ A equipe gasta mais de 15 horas/semana buscando editais no PNCP</li>
          <li>☐ Já perdeu pelo menos 1 oportunidade relevante por descoberta tardia nos últimos 3 meses</li>
          <li>☐ Monitora mais de 3 UFs simultaneamente</li>
          <li>☐ Atua em mais de 1 setor (ex: engenharia + TI, ou saúde + facilities)</li>
          <li>☐ A planilha tem mais de 500 linhas e ficou difícil de manter</li>
          <li>
            ☐ A taxa de adjudicação está abaixo de 15% (
            <Link href="/blog/como-aumentar-taxa-vitoria-licitacoes">
              referência: taxa saudável por modalidade
            </Link>
            )
          </li>
          <li>☐ Mais de uma pessoa precisa acessar os mesmos dados simultaneamente</li>
        </ul>
      </div>

      <h2>O que muda na prática: fluxo com planilha vs fluxo com plataforma</h2>

      <h3>Fluxo com planilha (cenário real de construtora em SP)</h3>

      <ol className="list-decimal pl-6 space-y-2">
        <li>Segunda-feira, 8h: analista abre o PNCP, busca &ldquo;construção civil&rdquo; em SP.</li>
        <li>Encontra 47 resultados dos últimos 5 dias. Lê o objeto de cada um (~3 min/edital = 2h20).</li>
        <li>Descarta 35 (fora do perfil). Copia 12 para a planilha (~15 min).</li>
        <li>Terça-feira: repete para RJ e MG. Mais 3h30.</li>
        <li>Quarta-feira: analisa os 20 editais selecionados em detalhe. Decide participar de 4.</li>
        <li>Tempo total na semana: ~20 horas para chegar em 4 editais.</li>
      </ol>

      <h3>Fluxo com SmartLic (mesmo cenário)</h3>

      <ol className="list-decimal pl-6 space-y-2">
        <li>Segunda-feira, 8h: abre o SmartLic. Busca &ldquo;engenharia&rdquo; em SP + RJ + MG.</li>
        <li>Resultados filtrados por viabilidade em 30 segundos. 18 editais relevantes, já com score.</li>
        <li>Analisa os 18 (dados consolidados, sem precisar abrir cada edital no PNCP). ~3 horas.</li>
        <li>Move 5 para o pipeline. Exporta Excel com resumo para a diretoria.</li>
        <li>Tempo total na semana: ~4 horas para chegar em 5 editais (1 a mais que o fluxo manual).</li>
      </ol>

      <p>
        A diferença de 16 horas por semana (20 vs 4) equivale a 64 horas por
        mês — tempo que pode ser redirecionado para elaboração de propostas,{' '}
        <Link href="/blog/como-calcular-preco-proposta-licitacao">
          precificação
        </Link>
        , ou prospecção de novos mercados.
      </p>

      <h2>O que o SmartLic não faz (e a planilha faz)</h2>

      <p>
        Transparência é parte da análise. Existem cenários em que a planilha
        oferece mais flexibilidade:
      </p>

      <ul className="list-disc pl-6 space-y-2">
        <li>
          <strong>Cálculos customizados:</strong> fórmulas de BDI, composição
          de custos, simulações de preço — o Excel é imbatível para modelagem
          financeira.
        </li>
        <li>
          <strong>Integração com sistemas internos:</strong> ERPs e sistemas
          de gestão frequentemente exportam para Excel. Uma plataforma web
          não substitui essa integração sem API dedicada.
        </li>
        <li>
          <strong>Controle total:</strong> na planilha, o usuário define
          exatamente o que rastrear e como. Numa plataforma, as dimensões
          disponíveis são as que o produto oferece.
        </li>
      </ul>

      <p>
        Por isso, a maioria das empresas que adota uma plataforma de
        inteligência em licitações <strong>não abandona o Excel</strong> — usa
        os dois. A plataforma resolve busca, triagem e monitoramento. O Excel
        resolve precificação, orçamento e controle interno.
      </p>

      <h2>Dados exclusivos: o que a base de dados SmartLic revela sobre eficiência</h2>

      <p>
        Entre janeiro e março de 2026, o SmartLic processou dados de mais de
        800.000 publicações no PNCP. A análise do comportamento dos usuários
        beta mostrou padrões relevantes para quem está decidindo entre planilha
        e plataforma:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>73% de redução</strong> no tempo de triagem de editais
            irrelevantes quando a classificação setorial por IA é utilizada
            (vs. busca apenas por palavras-chave).
          </li>
          <li>
            <strong>89% dos editais descartados</strong> pela IA seriam
            descartados manualmente pelo analista — mas a IA faz em
            milissegundos.
          </li>
          <li>
            <strong>11% dos editais aprovados pela IA</strong> foram
            oportunidades que o analista não teria encontrado pela
            palavra-chave usual (classificação por contexto semântico).
          </li>
        </ul>
      </div>

      <p>
        Esse último dado é particularmente relevante: a{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona">
          classificação por IA
        </Link>{' '}
        não apenas economiza tempo — ela encontra oportunidades que a
        busca manual não encontraria, porque o objeto do edital usa
        terminologia diferente da palavra-chave esperada.
      </p>

      <h2>Veredito honesto</h2>

      <p>
        <strong>Se você disputa menos de 5 licitações por mês em 1-2 UFs</strong>
        , a planilha é suficiente. O custo de uma plataforma não se justifica
        e você provavelmente conhece o mercado bem o bastante para triar
        manualmente.
      </p>

      <p>
        <strong>Se você disputa mais de 10 licitações por mês, atua em 3+ UFs
        ou 2+ setores</strong>, a automação gera ROI mensurável. O tempo
        economizado paga a plataforma várias vezes, e a descoberta
        automatizada evita oportunidades perdidas.
      </p>

      <p>
        <strong>Se você está entre 5 e 10 licitações/mês</strong>, a decisão
        depende de quanto custa a hora do seu analista e quantas oportunidades
        você suspeita que está perdendo por atraso. O{' '}
        <Link href="/calculadora">
          calculador de economia em editais
        </Link>{' '}
        pode ajudar a quantificar.
      </p>

      <p>
        O SmartLic não é a única plataforma do mercado. Se quiser comparar
        opções, veja o{' '}
        <Link href="/blog/melhores-plataformas-licitacao-2026-ranking">
          ranking completo de plataformas de licitação em 2026
        </Link>
        .
      </p>

      <h2>Perguntas frequentes</h2>

      <h3>Quando vale a pena trocar a planilha Excel por uma plataforma de licitações?</h3>
      <p>
        A troca se justifica quando a equipe gasta mais de 15 horas por semana
        buscando e triando editais manualmente, quando já perdeu oportunidades
        por não monitorar publicações diárias no PNCP, ou quando o volume de
        editais relevantes ultrapassa 30 por mês. Nesses cenários, o custo de
        oportunidade da planilha supera o investimento em automação.
      </p>

      <h3>Planilha Excel funciona para acompanhar licitações?</h3>
      <p>
        Sim, para empresas que disputam menos de 5 licitações por mês em um
        único setor e UF. A planilha é gratuita, flexível e familiar. O
        problema surge com escala: acima de 30 editais/mês, o tempo de
        alimentação manual, a ausência de alertas e a impossibilidade de filtrar
        por viabilidade tornam o processo insustentável.
      </p>

      <h3>Quanto tempo uma empresa gasta para monitorar licitações manualmente?</h3>
      <p>
        Segundo levantamento com empresas B2G, o monitoramento manual de editais
        no PNCP consome entre 15 e 40 horas por semana, dependendo do número de
        setores e UFs acompanhados. Com automação, o mesmo volume é processado
        em menos de 2 horas semanais de análise qualificada.
      </p>

      <h3>O SmartLic substitui completamente a planilha Excel?</h3>
      <p>
        Não necessariamente. O SmartLic substitui a planilha nas etapas de
        busca, triagem e monitoramento. Muitas empresas continuam usando Excel
        para controle interno de propostas, orçamentos e cronogramas — funções
        que não são o foco de uma plataforma de inteligência em licitações.
      </p>

      <h3>Qual o custo real de manter licitações em planilha?</h3>
      <p>
        O custo direto é zero. Mas o custo oculto inclui horas de trabalho
        manual (15-40h/semana × custo/hora do analista), oportunidades perdidas
        por atraso na descoberta, e ausência de histórico estruturado. Para uma
        empresa com analista a R$ 50/hora, o custo oculto varia entre
        R$ 3.000 e R$ 8.000 por mês.
      </p>

      <h3>Plataformas de licitação usam inteligência artificial?</h3>
      <p>
        Algumas sim, outras não. O SmartLic usa IA (GPT-4.1-nano) para
        classificação setorial automática e análise de viabilidade com 4
        fatores. Plataformas mais antigas dependem apenas de busca por
        palavras-chave, sem camada de inteligência.
      </p>

      <h2>Fontes</h2>

      <ul className="list-disc pl-6 space-y-1 text-sm">
        <li>
          PNCP — Portal Nacional de Contratações Públicas (pncp.gov.br) — volume de publicações 2024-2026
        </li>
        <li>
          Lei 14.133/2021, art. 55, §1º — prazos mínimos por modalidade de contratação
        </li>
        <li>
          Painel de Compras do Governo Federal — dados agregados de taxa de adjudicação 2023-2024
        </li>
        <li>
          SmartLic base de dados — dados de processamento e classificação, janeiro-março 2026 (800K+ publicações analisadas)
        </li>
        <li>
          Programa beta SmartLic — entrevistas com 30+ empresas B2G, janeiro-março 2026
        </li>
      </ul>
    </>
  );
}
