import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * MEI e Microempresa: Todas as Vantagens em Licitações — Guia Completo
 *
 * Target: ~2800 words | Cluster: guias transversais
 * Primary keyword: vantagens microempresa licitação / MEI pode participar licitação
 */
export default function MeiMicroempresaVantagensLicitacoes() {
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
                name: 'MEI pode participar de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O MEI (Microempreendedor Individual) pode participar de licitações públicas desde que o objeto da contratação seja compatível com as atividades permitidas ao MEI (CNAEs registrados) e o valor do contrato não comprometa o limite anual de faturamento de R$ 81.000. O MEI tem as mesmas vantagens de ME/EPP garantidas pela Lei Complementar 123/2006, como empate ficto e regularização fiscal tardia. A principal limitação é a restrição de atestados técnicos em serviços complexos.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é empate ficto em licitação para ME e EPP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Empate ficto é um mecanismo da Lei Complementar 123/2006 (art. 44) que permite a ME/EPP/MEI apresentar nova proposta, com valor menor, mesmo que sua proposta original não seja a mais baixa — desde que a diferença seja de até 5% em pregão eletrônico ou até 10% nas demais modalidades. Na prática, se a empresa de grande porte ofertou R$ 100.000 e a ME ofertou R$ 104.900 (até 5% acima), a ME pode reduzir sua proposta para qualquer valor abaixo de R$ 100.000 e vencer a licitação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o limite de faturamento para ser considerada ME ou EPP?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Pela Lei Complementar 123/2006 (art. 3º), são consideradas: MEI — faturamento anual até R$ 81.000; Microempresa (ME) — faturamento anual até R$ 360.000; Empresa de Pequeno Porte (EPP) — faturamento anual de R$ 360.001 até R$ 4.800.000. Esses limites valem para o exercício fiscal anterior à licitação. A empresa deve declarar seu enquadramento na proposta e pode ser questionada pelo órgão se houver indício de enquadramento incorreto.',
                },
              },
              {
                '@type': 'Question',
                name: 'Licitações exclusivas para ME/EPP: onde encontrar?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Licitações exclusivas para ME/EPP são aquelas com valor estimado de até R$ 80 mil (art. 48, I, da LC 123/2006). Para encontrá-las, acesse o PNCP (pncp.gov.br) e filtre por "benefício ME/EPP" ou valor estimado. O ComprasNet e portais estaduais também permitem esse filtro. Plataformas de inteligência como o SmartLic consolidam editais de múltiplas fontes e aplicam esse filtro automaticamente, reduzindo o tempo de prospecção.',
                },
              },
              {
                '@type': 'Question',
                name: 'ME/EPP precisa de certidão negativa para licitar?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, mas com vantagem importante. A ME/EPP/MEI deve apresentar as certidões de regularidade fiscal e trabalhista exigidas no edital — mas pode apresentá-las mesmo com restrições, desde que sane a irregularidade em até 5 dias úteis após ser declarada vencedora (art. 43, §1º, LC 123/2006). Esse prazo pode ser prorrogado uma vez por igual período. Grandes empresas são imediatamente desclassificadas se apresentarem certidão com restrição.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        MEI, microempresas e empresas de pequeno porte representam mais de 90% do total de empresas
        brasileiras — mas respondem por menos de 15% da participação em licitações públicas. O motivo
        não é falta de oportunidade: é falta de informação. A Lei Complementar 123/2006, mantida e
        expandida pela Lei 14.133/2021, criou um conjunto de vantagens concretas para esse segmento
        que, se bem utilizadas, tornam o mercado público uma das fontes de receita mais acessíveis
        e previsíveis para empresas de todos os portes.
      </p>

      <h2>Quem é ME, EPP e MEI para Efeito de Licitação</h2>
      <p>
        Antes de falar em vantagens, é preciso entender o enquadramento. A Lei Complementar 123/2006
        (art. 3º) define:
      </p>
      <ul>
        <li>
          <strong>MEI — Microempreendedor Individual:</strong> faturamento anual bruto até R$ 81.000.
          Uma única pessoa, sem sócios, com no máximo 1 empregado. CNAE limitado à lista oficial
          do MEI.
        </li>
        <li>
          <strong>ME — Microempresa:</strong> faturamento anual bruto até R$ 360.000. Sem restrição
          de sócios ou CNAE (desde que não exerça atividade vedada ao Simples).
        </li>
        <li>
          <strong>EPP — Empresa de Pequeno Porte:</strong> faturamento anual bruto entre R$ 360.001
          e R$ 4.800.000.
        </li>
      </ul>
      <p>
        O enquadramento é verificado com base no faturamento do exercício fiscal imediatamente
        anterior à licitação. Se você faturou R$ 350.000 no ano passado, é ME — mesmo que já tenha
        grandes contratos em carteira para o ano corrente. A declaração de ME/EPP deve ser feita na
        proposta, e o órgão pode solicitar comprovação (Declaração de Enquadramento assinada pelo
        contador ou DEFIS — Declaração de Informações Socioeconômicas e Fiscais).
      </p>
      <p>
        Importante: o enquadramento como ME/EPP para fins licitatórios é independente do regime
        tributário. Uma EPP que optou pelo Lucro Presumido ainda tem direito a todos os benefícios
        da LC 123/2006 em licitações — o que muitas empresas não sabem.
      </p>

      <h2>As 5 Vantagens Legais de ME/EPP em Licitações</h2>

      <h3>1. Empate Ficto — A Mais Poderosa</h3>
      <p>
        O empate ficto (art. 44 da LC 123/2006) é o benefício mais impactante para ME/EPP. Ele
        funciona assim: mesmo que a ME/EPP não tenha apresentado o melhor preço, se a diferença
        entre o seu preço e o do vencedor provisório for de até 5% em pregão eletrônico (ou 10%
        nas demais modalidades), a empresa pode apresentar nova proposta inferior à do vencedor.
      </p>
      <p>
        Em pregão eletrônico, essa oportunidade é automática — o sistema convoca a ME/EPP para
        nova proposta antes de declarar o vencedor. A empresa tem 5 minutos para manifestar
        interesse e 5 minutos adicionais para enviar o novo valor.
      </p>

      <h3>2. Licitações Exclusivas até R$ 80 Mil</h3>
      <p>
        O art. 48, inciso I, da LC 123/2006 obriga a Administração a realizar licitações exclusivas
        para ME/EPP quando o valor estimado é de até R$ 80 mil. Grandes empresas simplesmente não
        podem participar. Esse é o mercado com menor competição e maior acessibilidade para
        iniciantes.
      </p>

      <h3>3. Subcontratação Obrigatória de 25%</h3>
      <p>
        Para licitações acima de R$ 80 mil, o art. 48, inciso II, da LC 123/2006 permite ao edital
        exigir que o vencedor (mesmo sendo uma grande empresa) subcontrate ME/EPP em pelo menos 25%
        do valor total. Isso cria uma via indireta de participação para empresas menores.
      </p>

      <h3>4. Regularização Fiscal Tardia</h3>
      <p>
        Uma das barreiras mais comuns para ME/EPP é a irregularidade fiscal temporária — uma guia
        vencida, uma certidão negativa que não saiu a tempo. O art. 43, §1º da LC 123/2006 resolve
        isso: a ME/EPP pode apresentar a proposta mesmo com certidão restritiva, e tem até 5 dias
        úteis após ser declarada vencedora para regularizar a situação. O prazo pode ser prorrogado
        uma vez por igual período.
      </p>

      <h3>5. Cota Reservada de 25% em Itens Divisíveis</h3>
      <p>
        Quando a licitação envolve bens ou serviços divisíveis (ex: 1.000 unidades de um mesmo
        produto), o art. 48, inciso III, da LC 123/2006 estabelece cota reservada de no mínimo
        25% exclusivamente para ME/EPP. Isso garante acesso mesmo quando o volume total é grande
        demais para uma empresa pequena.
      </p>

      <h2>Empate Ficto na Prática: Exemplo com Números</h2>
      <p>
        Vamos ver como o empate ficto funciona num pregão eletrônico real:
      </p>
      <p>
        Após a fase de lances, a classificação ficou assim:
      </p>
      <ul>
        <li>1º lugar — Empresa X (Grande Porte): R$ 95.000</li>
        <li>2º lugar — Empresa Y (EPP): R$ 99.200 (4,4% acima — dentro do limite de 5%)</li>
        <li>3º lugar — Empresa Z (ME): R$ 99.800 (5,05% acima — fora do limite de 5%)</li>
      </ul>
      <p>
        O sistema identifica que a Empresa Y (EPP) está em situação de empate ficto. Ela é
        convocada para apresentar nova proposta inferior a R$ 95.000. Se fizer isso — por exemplo,
        ofertando R$ 94.800 — vence a licitação mesmo tendo começado com preço maior.
      </p>
      <p>
        A Empresa Z (ME) está fora do limite de 5%, portanto não é convocada para o empate ficto.
        Se houvesse mais de uma ME/EPP em situação de empate ficto, a ordem de convocação seria
        determinada por sorteio.
      </p>
      <p>
        Essa mecânica muda completamente a estratégia de precificação para ME/EPP. Você não precisa
        ser o mais barato desde o início — precisa estar dentro da faixa de 5% do melhor preço
        ao final dos lances. Leia mais sobre estratégia de preços em nosso guia completo de{' '}
        <Link href="/blog/pregao-eletronico-guia-passo-a-passo">pregão eletrônico passo a passo</Link>.
      </p>

      <h2>Licitações Exclusivas até R$ 80 Mil: Onde Estão e Qual o Volume</h2>
      <p>
        As licitações exclusivas para ME/EPP são o segmento mais estratégico para quem está
        começando. Segundo dados do PNCP, em 2024 foram publicadas mais de 180.000 contratações
        com valor estimado até R$ 80 mil por órgãos federais — número que aumenta significativamente
        quando incluímos estados e municípios.
      </p>
      <p>
        Onde encontrar essas licitações:
      </p>
      <ul>
        <li>
          <strong>PNCP (pncp.gov.br):</strong> Portal Nacional de Contratações Públicas. Busque por
          valor estimado máximo de R$ 80.000 e marque o filtro "Benefício ME/EPP". Concentra
          obrigatoriamente toda contratação federal e, cada vez mais, estados e municípios.
        </li>
        <li>
          <strong>ComprasNet (comprasnet.gov.br):</strong> Para compras federais via SIASG.
          Filtro "Itens exclusivos para ME/EPP".
        </li>
        <li>
          <strong>Portais estaduais e municipais:</strong> Cada estado tem sua plataforma (BEC-SP,
          LICITANET, etc.). Muitos municípios usam plataformas privadas como ComprasNet, Licitanet
          e Portal de Compras Públicas.
        </li>
      </ul>
      <p>
        O volume de licitações exclusivas para ME/EPP é enorme — e a competição é menor porque
        grandes empresas estão legalmente excluídas. Para monitorar esses editais sem precisar
        acessar portal por portal, use uma ferramenta como o{' '}
        <Link href="/consultoria-b2g?ref=blog-mei-me-epp">SmartLic</Link>, que agrega múltiplas fontes e
        aplica filtros automaticamente.
      </p>

      <BlogInlineCTA slug="mei-microempresa-vantagens-licitacoes" campaign="guias" />

      <h2>Limitações Práticas: O que ME/EPP Não Pode Fazer</h2>
      <p>
        As vantagens são reais — mas existem limitações igualmente reais que precisam ser
        consideradas antes de entrar num edital.
      </p>

      <h3>MEI: Faturamento Anual de R$ 81 Mil</h3>
      <p>
        O limite anual de R$ 81.000 para o MEI é o mais crítico. Um contrato de serviços de
        limpeza para uma escola municipal pode facilmente superar R$ 5.000/mês — R$ 60.000/ano.
        Isso ainda está dentro do limite, mas um segundo contrato simultâneo ou qualquer receita
        adicional ultrapassaria o teto. Exceder o limite obriga o MEI a migrar para ME, com
        impactos tributários imediatos.
      </p>

      <h3>MEI: Sócio Único Sem Outros Vínculos Societários</h3>
      <p>
        O MEI não pode ter sócios e o titular não pode ser sócio de outra empresa. Essa restrição
        é automática: se o empreendedor for sócio de qualquer pessoa jurídica (exceto cooperativas),
        perde o enquadramento como MEI. Para contratos que exigem atestado de capacidade técnica
        emitido por pessoa jurídica diferente, o MEI pode ter dificuldades.
      </p>

      <h3>Atestados de Capacidade Técnica</h3>
      <p>
        Para licitações que exigem atestado de capacidade técnica — comprovação de execução
        anterior de objeto similar — empresas novas ou MEI com histórico limitado enfrentam
        dificuldade. A Lei 14.133/2021 (art. 67) manteve a exigência de atestados, mas proibiu
        exigências desproporcionais (ex: exigir atestado de 100% do volume quando a licitação é
        para 40%). Verifique se o edital respeita essa proporcionalidade antes de decidir participar.
        Nosso guia sobre{' '}
        <Link href="/blog/checklist-habilitacao-licitacao-2026">checklist de habilitação</Link>{' '}
        detalha todos os documentos exigíveis.
      </p>

      <h3>CNAEs Limitados para MEI</h3>
      <p>
        O MEI só pode exercer as atividades listadas na Resolução CGSN nº 140/2018 e atualizações.
        Serviços de engenharia completos, atividades financeiras reguladas e diversas atividades
        intelectuais de nível superior não constam da lista. Se o objeto da licitação não estiver
        no CNAE do MEI, a participação é inviável — não é questão de escolha.
      </p>

      {/* Comparison table box */}
      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Comparativo: MEI vs ME vs EPP em Licitações</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left py-2 pr-4 font-semibold">Critério</th>
                <th className="text-left py-2 pr-4 font-semibold">MEI</th>
                <th className="text-left py-2 pr-4 font-semibold">ME</th>
                <th className="text-left py-2 font-semibold">EPP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              <tr>
                <td className="py-2 pr-4">Faturamento anual</td>
                <td className="py-2 pr-4">Até R$ 81 mil</td>
                <td className="py-2 pr-4">Até R$ 360 mil</td>
                <td className="py-2">Até R$ 4,8 milhões</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">Empate ficto (pregão)</td>
                <td className="py-2 pr-4">Sim (5%)</td>
                <td className="py-2 pr-4">Sim (5%)</td>
                <td className="py-2">Sim (5%)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">Licitação exclusiva &lt; R$ 80k</td>
                <td className="py-2 pr-4">Sim</td>
                <td className="py-2 pr-4">Sim</td>
                <td className="py-2">Sim</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">Regularização fiscal tardia</td>
                <td className="py-2 pr-4">Sim</td>
                <td className="py-2 pr-4">Sim</td>
                <td className="py-2">Sim</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">Sócios permitidos</td>
                <td className="py-2 pr-4">Não</td>
                <td className="py-2 pr-4">Sim</td>
                <td className="py-2">Sim</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">CNAEs</td>
                <td className="py-2 pr-4">Lista restrita</td>
                <td className="py-2 pr-4">Qualquer (exceto vedados)</td>
                <td className="py-2">Qualquer (exceto vedados)</td>
              </tr>
              <tr>
                <td className="py-2 pr-4">Contratos simultâneos</td>
                <td className="py-2 pr-4">Limitado pelo teto de R$ 81k/ano</td>
                <td className="py-2 pr-4">Ilimitado (dentro do faturamento)</td>
                <td className="py-2">Ilimitado</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <h2>MEI Pode Participar de Licitação? A Resposta Completa</h2>
      <p>
        Sim — mas com clareza sobre as restrições. O MEI é pessoa jurídica, tem CNPJ e pode
        participar de qualquer licitação compatível com seu CNAE, desde que o contrato não
        resulte em faturamento anual acima de R$ 81.000.
      </p>
      <p>
        Na prática, o MEI encontra boas oportunidades em:
      </p>
      <ul>
        <li>Fornecimento de pequenas quantidades de produtos (artesanato, alimentação, materiais de escritório)</li>
        <li>Serviços pontuais de manutenção, jardinagem, limpeza de eventos</li>
        <li>Serviços de informática, design, fotografia e comunicação visual (quando no CNAE)</li>
        <li>Serviços de transporte de pequeno porte (mototaxistas, pequenos fretes)</li>
        <li>Serviços de alimentação (buffet, marmitas, fornecimento a cantinas)</li>
      </ul>
      <p>
        O MEI encontra dificuldades em:
      </p>
      <ul>
        <li>Contratos de valor mensal acima de R$ 6.750 (que, em 12 meses, ultrapassariam o teto anual)</li>
        <li>Serviços que exigem atestado de capacidade técnica de pessoa jurídica</li>
        <li>Licitações com exigência de visita técnica presencial complexa</li>
        <li>Objetos fora da lista de CNAEs do MEI</li>
      </ul>
      <p>
        Se o negócio está crescendo e os limites do MEI estão ficando apertados, pode ser o
        momento de migrar para ME. A migração mantém todos os benefícios da LC 123/2006 e
        abre portas para contratos de maior valor. Confira nosso guia sobre{' '}
        <Link href="/blog/lei-14133-guia-fornecedores">Lei 14.133/2021 para fornecedores</Link>{' '}
        para entender o cenário completo.
      </p>

      {/* Warning box */}
      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">⚠ Atenção: Armadilhas do MEI em Licitações</p>
        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
          1. <strong>Faturamento:</strong> Vencer uma licitação que, somada a outras receitas, faça
          o MEI ultrapassar R$ 81.000/ano obriga a migração para ME com retroatividade fiscal —
          podendo gerar autuação. Controle rigoroso do faturamento acumulado é indispensável.<br />
          2. <strong>Sem atestado técnico de terceiros:</strong> O MEI não pode usar contratos
          executados como pessoa física para comprovar capacidade técnica. Se não tiver histórico
          como PJ, evite editais com exigência de atestado para objetos complexos.<br />
          3. <strong>Sem funcionários qualificados:</strong> O MEI permite apenas 1 empregado.
          Contratos que exijam equipe técnica composta são inviáveis.
        </p>
      </div>

      <h2>Como Começar: Passos Práticos para ME/EPP/MEI</h2>

      <h3>Passo 1: Regularize a documentação fiscal</h3>
      <p>
        Certidões exigidas na maioria dos editais: CND Federal (Receita + PGFN), CRF (FGTS/Caixa),
        CNDT (Débitos Trabalhistas), Certidão Estadual e Municipal de tributos. Todas gratuitas
        nos portais dos respectivos órgãos. Validade: 180 dias (federal), variável (estados/municípios).
        Crie uma rotina mensal de renovação preventiva — certidão vencida no dia do pregão é
        eliminação imediata, mesmo para ME/EPP (a vantagem é regularizar <em>depois</em> de
        vencer, não de participar sem certidão).
      </p>

      <h3>Passo 2: Obtenha o certificado digital e-CNPJ</h3>
      <p>
        Pregões eletrônicos exigem certificado digital e-CNPJ (tipo A1 ou A3) para assinar
        propostas e documentos. Custo: R$ 150 a R$ 500 dependendo da validade e da certificadora.
        Emissão em 1 a 3 dias úteis com agendamento presencial. Prioritário: faça isso antes de
        tudo.
      </p>

      <h3>Passo 3: Cadastre-se no SICAF e nos portais</h3>
      <p>
        O SICAF (Sistema de Cadastramento Unificado de Fornecedores) é o cadastro federal central.
        O cadastro é gratuito e obrigatório para fornecimentos federais. Além dele, cadastre-se
        nas plataformas estaduais e municipais relevantes para seu mercado. Cada um tem processo
        próprio — reserve de 1 a 2 semanas para completar todos.
      </p>

      <h3>Passo 4: Monitore editais sistematicamente</h3>
      <p>
        Garimpar editais portal por portal é inviável. Use o PNCP como fonte primária e considere
        plataformas de inteligência em licitações para automatizar a busca. O SmartLic, por
        exemplo, agrega PNCP e outras fontes, aplica filtros por setor e UF e calcula viabilidade
        — ajudando a focar nos editais com maior probabilidade de vitória. Leia nossa análise
        sobre{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao">quando vale a pena disputar um pregão</Link>{' '}
        para entender o critério de seleção.
      </p>

      <h3>Passo 5: Comece pequeno e aprenda</h3>
      <p>
        A primeira licitação raramente é vencida. Mas a experiência operacional — navegar no
        sistema, entender o fluxo de lances, montar a documentação — é inestimável. Comece com
        editais de R$ 10.000 a R$ 30.000, objetos simples, onde o risco de erro é baixo. Aumente
        progressivamente conforme ganha confiança. Consulte também o guia completo de{' '}
        <Link href="/blog/como-participar-primeira-licitacao-2026">como participar da primeira licitação</Link>.
      </p>

      {/* Blue CTA box */}
      <div className="not-prose my-8 sm:my-10 bg-brand/5 border border-brand/20 rounded-lg p-6 sm:p-8 text-center">
        <h3 className="text-xl font-bold mb-2">Encontre editais exclusivos para ME/EPP agora</h3>
        <p className="text-ink-secondary mb-4">
          O SmartLic filtra automaticamente licitações exclusivas para microempresas e EPP,
          aplica IA para classificar relevância e calcula viabilidade — tudo em uma busca.
          sem login, dado verificável.
        </p>
        <Link
          href="/consultoria-b2g?ref=blog-mei-me-epp"
          className="inline-block bg-brand text-white font-semibold px-6 py-3 rounded-lg hover:bg-brand/90 transition-colors"
        >
          Começar gratuitamente →
        </Link>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>MEI pode participar de licitação?</h3>
      <p>
        Sim. O MEI tem CNPJ, é pessoa jurídica e pode participar de licitações públicas. As
        condições são: o objeto deve estar dentro dos CNAEs do MEI, o valor do contrato não pode
        comprometer o teto anual de R$ 81.000 e a licitação deve ser compatível com a capacidade
        operacional (sem exigência de equipe ou atestados que o MEI não possa atender). O MEI
        tem os mesmos benefícios de ME/EPP garantidos pela LC 123/2006.
      </p>

      <h3>O que é empate ficto e como funciona na prática?</h3>
      <p>
        Empate ficto (art. 44 da LC 123/2006) é o direito de ME/EPP/MEI apresentar nova proposta
        quando sua oferta estiver dentro de 5% acima do melhor preço em pregão eletrônico (ou 10%
        nas demais modalidades). Se você ofertou R$ 104.000 e o líder ofertou R$ 100.000 (diferença
        de 4%), você é convocado para reduzir sua proposta abaixo de R$ 100.000. Se fizer isso,
        vence — mesmo tendo começado com preço maior.
      </p>

      <h3>Empresa com dívida fiscal pode participar de licitação sendo ME/EPP?</h3>
      <p>
        Sim — mas com condição. A ME/EPP pode apresentar certidão com restrição (dívida ativa,
        FGTS pendente, débito trabalhista) desde que, ao ser declarada vencedora, regularize a
        situação em até 5 dias úteis (prorrogáveis por mais 5 dias úteis, art. 43, §1º, LC
        123/2006). Se não regularizar nesse prazo, perde a contratação e pode responder por multa.
        Grandes empresas não têm esse prazo: certidão irregular = desclassificação imediata.
      </p>

      <h3>ME/EPP tem desconto nos preços de habilitação?</h3>
      <p>
        A maioria das taxas e certidões exigidas em licitações é gratuita (SICAF, certidões
        federais, CNDT). Onde há cobranças — como registros no CREA, CRC ou outros conselhos —
        ME/EPP geralmente têm anuidades reduzidas por lei, o que indiretamente beneficia o custo
        de manutenção da habilitação. Confirme as tabelas de anuidades do conselho específico
        do seu setor.
      </p>

      <h3>Como declarar ser ME/EPP na proposta?</h3>
      <p>
        Na maioria das plataformas de pregão eletrônico (ComprasNet, BLL, Portal de Compras
        Públicas), há um campo específico para declarar o porte da empresa no momento do cadastro
        ou envio da proposta. É obrigatório marcar ME/EPP para ter acesso aos benefícios — se não
        declarar, o sistema não aplica o empate ficto automaticamente. Fora das plataformas, inclua
        a Declaração de Enquadramento ME/EPP assinada pelo contador na documentação de habilitação.
      </p>
    </>
  );
}
