import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * STORY-263 CONS-11: Escalar Consultoria sem Depender de Horas Técnicas
 *
 * Content cluster: inteligência em licitações para consultorias
 * Target: 2,500-3,000 words | Primary KW: escalar consultoria de licitação
 */
export default function EscalarConsultoriaSemDependerHorasTecnicas() {
  return (
    <>
      {/* FAQPage JSON-LD — STORY-263 AC5/AC11 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: [
              {
                '@type': 'Question',
                name: 'Por que o modelo de horas técnicas limita o crescimento de consultorias de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O modelo de horas técnicas impõe um teto matemático: a receita máxima é limitada pelo número de horas disponíveis multiplicado pelo valor cobrado por hora. Para crescer, a consultoria precisa contratar mais analistas, o que eleva custos fixos proporcionalmente à receita. Uma consultoria com 3 analistas que cobram R$ 150/hora tem receita máxima teórica de R$ 79.200/mês (3 x 176h x R$ 150), mas na prática fatura 50% a 65% disso devido a horas não faturáveis — resultando em um teto de R$ 40.000 a R$ 51.000/mês.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais são os modelos de escala alternativos para consultorias de licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Existem quatro modelos principais: (1) Produtização — transformar serviços em pacotes pré-definidos com preço fixo, desvinculando receita de horas; (2) Tecnologia como multiplicador — usar ferramentas de IA para atender mais clientes com a mesma equipe; (3) Modelo híbrido de assinatura + consultoria — receita recorrente base complementada por projetos; (4) White-label e parcerias — licenciar metodologia ou operar sob marca de terceiros para ampliar alcance sem proporcionalmente ampliar equipe.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o ticket médio de uma consultoria de licitação produtizada versus por hora?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Consultorias que operam por hora técnica praticam tickets mensais entre R$ 3.000 e R$ 8.000 por cliente, dependendo do volume de horas contratadas. Consultorias produtizadas, com pacotes pré-definidos de monitoramento + triagem + análise, praticam tickets entre R$ 2.500 e R$ 6.000 por cliente, mas com custo de entrega 40% a 60% menor por conta da automação. O resultado é margem líquida superior mesmo com ticket nominal similar ou inferior.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto tempo leva para migrar uma consultoria de horas técnicas para um modelo escalável?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A migração gradual leva de 4 a 6 meses, em três fases: (1) Meses 1-2 — definição de pacotes e adoção de ferramenta de automação de triagem; (2) Meses 3-4 — migração dos primeiros 3-5 clientes para o novo modelo, mantendo o modelo anterior para os demais; (3) Meses 5-6 — expansão do modelo produtizado para a base completa e início de prospecção com a nova proposta de valor. A recomendação é não migrar todos os clientes simultaneamente.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword: escalar consultoria de licitação */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O modelo dominante de consultoria de licitação no Brasil é baseado em
        horas técnicas: o cliente contrata um pacote mensal de horas, e a
        consultoria aloca analistas para monitoramento, triagem e análise de
        editais. Esse modelo funciona até o ponto em que a consultoria bate no
        teto — e toda consultoria bate. A equação é simples:{' '}
        <strong>escalar consultoria de licitação</strong> por horas técnicas
        exige contratar mais analistas na mesma proporção em que se captam
        novos clientes. Custos fixos sobem linearmente. Margem permanece
        constante, ou cai. Este artigo apresenta quatro modelos alternativos
        que permitem à consultoria crescer sem que a receita fique refém da
        capacidade-hora da equipe.
      </p>

      {/* Section 1 */}
      <h2>O teto de vidro: hora técnica vezes capacidade igual a limite de receita</h2>

      <p>
        O modelo de horas técnicas tem uma limitação estrutural que se torna
        visível quando a consultoria tenta crescer além de 8 a 12 clientes
        ativos. Cada analista dedicado a operações de licitação consegue
        gerenciar, com qualidade, de 4 a 6 clientes simultaneamente —
        dependendo da complexidade setorial e do volume de editais de cada
        cliente. Acima desse limite, a qualidade da triagem cai, prazos são
        perdidos, e a consultoria começa a operar em modo reativo.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência — Limites do modelo de horas técnicas
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Capacidade por analista:</strong> Um analista de licitações
            em tempo integral (176 horas/mês) aloca em média 65% a 75% do tempo
            em atividades diretamente faturáveis. As demais 25% a 35% são
            consumidas por atividades administrativas, reuniões internas e
            atualização de documentação (Fonte: pesquisa ABES, Benchmark de
            Produtividade em Serviços B2B, 2024).
          </li>
          <li>
            <strong>Ticket médio por hora:</strong> Consultorias de licitação no
            Brasil praticam valores entre R$ 100 e R$ 200/hora para analistas
            sênior, e R$ 60 a R$ 120/hora para analistas pleno. O ticket médio
            mensal por cliente varia de R$ 3.000 a R$ 8.000 (Fonte: levantamento
            setorial Consultoria.org, 2024).
          </li>
          <li>
            <strong>Teto de receita:</strong> Uma consultoria com 3 analistas
            (média de R$ 130/hora) e taxa de utilização de 70% fatura, no
            máximo, R$ 48.048/mês (3 x 176h x 0,70 x R$ 130). Para atingir
            R$ 100.000/mês, precisa de 6 a 7 analistas — dobrando custos
            fixos com folha, encargos e infraestrutura.
          </li>
        </ul>
      </div>

      <p>
        O diagnóstico é claro: o modelo de horas não é escalável. Cada real
        adicional de receita exige alocação proporcional de custo. A margem é
        fixa, o crescimento é linear, e qualquer perda de cliente impacta
        imediatamente o resultado. Para a consultoria que deseja sair desse
        ciclo, existem quatro modelos alternativos — e nenhum exige abandonar
        completamente o modelo atual de uma vez.
      </p>

      {/* Section 2 */}
      <h2>Modelo 1: Produtização — pacotes pré-definidos de serviço</h2>

      <p>
        A produtização consiste em transformar o serviço consultivo em pacotes
        padronizados com escopo definido e preço fixo. Em vez de vender horas,
        a consultoria vende um resultado: monitoramento de X setores em Y estados,
        triagem de oportunidades com análise de viabilidade, e relatório mensal
        com recomendações.
      </p>

      <p>
        A vantagem estrutural da produtização é que ela desvincula receita de
        horas. Um pacote que custa R$ 4.500/mês pode exigir 15 horas de trabalho
        para o primeiro cliente e 8 horas para o décimo cliente do mesmo perfil,
        porque os processos são padronizados e reutilizáveis. A margem melhora
        com a escala.
      </p>

      <h3>Como estruturar pacotes para licitação</h3>

      <p>
        A prática mais eficaz é criar três níveis de pacote, diferenciados por
        escopo e não por horas:
      </p>

      <p>
        <strong>Pacote Monitoramento:</strong> A consultoria monitora portais,
        classifica editais por setor e entrega uma lista semanal de oportunidades
        relevantes. Não inclui análise detalhada de edital nem elaboração de
        proposta. Ticket típico: R$ 1.500 a R$ 3.000/mês.
      </p>

      <p>
        <strong>Pacote Triagem + Análise:</strong> Inclui tudo do pacote anterior,
        mais análise de viabilidade detalhada e resumo executivo dos editais
        prioritários. A consultoria recomenda quais editais disputar e quais
        descartar, com justificativa. Ticket típico: R$ 3.500 a R$ 6.000/mês.
      </p>

      <p>
        <strong>Pacote Completo:</strong> Inclui monitoramento, triagem, análise
        e suporte na elaboração de propostas para até X editais por mês.
        Ticket típico: R$ 6.000 a R$ 12.000/mês.
      </p>

      <p>
        A chave é que o custo de entrega do Pacote Monitoramento pode ser quase
        totalmente automatizado com ferramentas de inteligência em licitações.
        Isso transforma o primeiro pacote em uma fonte de receita recorrente
        de alta margem, enquanto os pacotes superiores preservam o componente
        consultivo que diferencia a operação.{' '}
        <Link href="/blog/entregar-mais-resultado-clientes-sem-aumentar-equipe" className="text-brand-navy dark:text-brand-blue hover:underline">
          Entenda como entregar mais resultado aos clientes sem aumentar a equipe
        </Link>.
      </p>

      <BlogInlineCTA slug="escalar-consultoria-sem-depender-horas-tecnicas" campaign="consultorias" />

      {/* Section 3 */}
      <h2>Modelo 2: Tecnologia como multiplicador de capacidade</h2>

      <p>
        O segundo modelo não substitui o serviço — amplifica a capacidade da
        equipe existente. A lógica é direta: se um analista gasta 3 horas por
        dia em triagem manual e uma ferramenta de IA reduz esse tempo para 40
        minutos, o mesmo analista pode atender o dobro de clientes com a mesma
        qualidade.
      </p>

      <p>
        Na prática, a adoção de tecnologia como multiplicador segue três estágios:
      </p>

      <p>
        <strong>Estágio 1 — Automação de busca:</strong> Em vez de acessar PNCP,
        ComprasGov e Portal de Compras Públicas manualmente, a consultoria usa
        uma ferramenta que consolida as três fontes e aplica filtros de setor,
        UF e período automaticamente. Economia: 60% a 70% do tempo de busca.
      </p>

      <p>
        <strong>Estágio 2 — Classificação por IA:</strong> A ferramenta
        classifica cada edital por relevância setorial e calcula um score de
        viabilidade. O analista recebe editais já ranqueados, eliminando o
        trabalho de ler publicações irrelevantes. Economia adicional: 40% a 50%
        do tempo de triagem restante.
      </p>

      <p>
        <strong>Estágio 3 — Relatórios automatizados:</strong> Resumos
        executivos, relatórios semanais e dashboards de pipeline são gerados
        automaticamente, reduzindo o tempo de comunicação com o cliente.
        Economia adicional: 30% a 40% do tempo de reporting.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência — Impacto da tecnologia na capacidade operacional
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Clientes por analista (sem tecnologia):</strong> 4 a 6
            clientes com qualidade satisfatória. Acima de 6, a qualidade de
            triagem cai e prazos são comprometidos.
          </li>
          <li>
            <strong>Clientes por analista (com automação):</strong> 10 a 15
            clientes, dependendo da complexidade setorial. A triagem
            automatizada elimina o gargalo de busca e classificação,
            permitindo que o analista foque na análise qualitativa.
          </li>
          <li>
            <strong>Custo incremental por cliente:</strong> No modelo manual, o
            custo de atender um cliente adicional é de R$ 6.000 a R$ 10.000/mês
            (alocação de analista). No modelo com automação, o custo incremental
            é de R$ 800 a R$ 2.000/mês (horas residuais de validação + custo
            proporcional da ferramenta).
          </li>
        </ul>
      </div>

      {/* Section 4 */}
      <h2>Modelo 3: Assinatura recorrente + consultoria sob demanda</h2>

      <p>
        O terceiro modelo combina receita recorrente previsível com projetos de
        maior valor. A consultoria oferece um plano de assinatura mensal que
        cobre monitoramento, triagem e análise de viabilidade — a camada
        operacional que pode ser largamente automatizada. Sobre essa base, vende
        serviços consultivos avulsos: análise detalhada de edital específico,
        elaboração de proposta técnica, recurso administrativo, impugnação.
      </p>

      <p>
        A vantagem é dupla. Primeiro, a assinatura gera receita previsível e
        recorrente que cobre os custos fixos da operação. Segundo, os serviços
        avulsos geram margem elevada porque são demandados pontualmente — o
        cliente paga pelo valor da entrega, não pelo tempo consumido.
      </p>

      <h3>Estrutura de assinatura recomendada</h3>

      <p>
        <strong>Base (assinatura):</strong> R$ 2.000 a R$ 4.000/mês —
        monitoramento contínuo, lista de oportunidades qualificadas, score de
        viabilidade, acesso a dashboard de pipeline. Custo de entrega: baixo
        (80% automatizado).
      </p>

      <p>
        <strong>Serviços avulsos (sob demanda):</strong> Análise de edital
        completa (R$ 1.500 a R$ 4.000 por edital), elaboração de proposta técnica
        (R$ 3.000 a R$ 12.000 por proposta), recurso/impugnação (R$ 2.000 a
        R$ 6.000 por peça). Margem: alta (70% a 85%).
      </p>

      <p>
        Para o consultor que deseja aprofundar como o diagnóstico de eficiência
        pode ser oferecido como serviço premium ao cliente, recomendamos{' '}
        <Link href="/blog/diagnostico-eficiencia-licitacao-servico-premium" className="text-brand-navy dark:text-brand-blue hover:underline">
          o diagnóstico de eficiência em licitação como serviço premium
        </Link>.
      </p>

      {/* Section 5 */}
      <h2>Modelo 4: White-label e parcerias estratégicas</h2>

      <p>
        O quarto modelo é o mais agressivo em termos de escala: a consultoria
        licencia sua metodologia, processos e ferramentas para parceiros —
        escritórios de contabilidade, assessorias empresariais, advogados
        especializados — que atendem seus próprios clientes usando a estrutura
        da consultoria como motor operacional.
      </p>

      <p>
        Nesse modelo, a consultoria não atende diretamente o cliente final. Ela
        fornece a inteligência (triagem, classificação, análise de viabilidade)
        e o parceiro adiciona a camada de atendimento e relacionamento. A receita
        vem de uma taxa por cliente gerenciado ou de uma assinatura fixa do
        parceiro.
      </p>

      <p>
        A viabilidade desse modelo depende de dois fatores: a consultoria precisa
        ter processos suficientemente maduros para serem replicados por terceiros,
        e precisa de uma plataforma tecnológica que suporte múltiplos perfis de
        acesso. Consultorias que já operam com ferramentas de inteligência em
        licitações têm vantagem natural nessa transição.
      </p>

      {/* Section 6 */}
      <h2>Comparação: receita por modelo com 5 clientes versus 20 clientes</h2>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Framework — Projeção de receita e margem por modelo
        </p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li className="font-semibold">Com 5 clientes:</li>
          <li>
            <strong>Horas técnicas:</strong> 5 x R$ 5.000 = R$ 25.000/mês.
            Custo: R$ 16.000 (1 analista sênior + overhead). Margem: 36%.
          </li>
          <li>
            <strong>Produtizado:</strong> 5 x R$ 4.500 = R$ 22.500/mês.
            Custo: R$ 11.000 (1 analista + ferramenta). Margem: 51%.
          </li>
          <li>
            <strong>Híbrido (assinatura + avulso):</strong> 5 x R$ 3.000
            (assinatura) + R$ 8.000 (avulsos) = R$ 23.000/mês.
            Custo: R$ 10.500. Margem: 54%.
          </li>
          <li>
            <strong>White-label:</strong> Não viável com apenas 5 clientes
            diretos — requer base mínima de parceiros.
          </li>
          <li className="pt-3 font-semibold">Com 20 clientes:</li>
          <li>
            <strong>Horas técnicas:</strong> 20 x R$ 5.000 = R$ 100.000/mês.
            Custo: R$ 64.000 (4 analistas + overhead). Margem: 36%.
          </li>
          <li>
            <strong>Produtizado:</strong> 20 x R$ 4.500 = R$ 90.000/mês.
            Custo: R$ 32.000 (2 analistas + ferramenta). Margem: 64%.
          </li>
          <li>
            <strong>Híbrido:</strong> 20 x R$ 3.000 + R$ 25.000 (avulsos) =
            R$ 85.000/mês. Custo: R$ 28.000. Margem: 67%.
          </li>
          <li>
            <strong>White-label (5 parceiros, 4 clientes cada):</strong>
            5 x R$ 6.000 = R$ 30.000/mês + 20 x R$ 800 (taxa por cliente) =
            R$ 16.000. Total: R$ 46.000/mês. Custo: R$ 14.000. Margem: 70%.
          </li>
        </ul>
      </div>

      <p>
        A tabela evidencia o efeito de escala: nos modelos produtizado e híbrido,
        quadruplicar a base de clientes (de 5 para 20) não quadruplica o custo.
        A margem salta de 51% para 64% (produtizado) e de 54% para 67% (híbrido).
        No modelo de horas, a margem permanece fixa em 36% independentemente do
        volume — porque cada novo cliente exige alocação proporcional de
        analista.
      </p>

      {/* Section 7 */}
      <h2>Como migrar gradualmente: roadmap de 6 meses</h2>

      <p>
        A transição de um modelo de horas para um modelo escalável não precisa
        ser uma ruptura. A abordagem mais segura é uma migração gradual que
        preserva a receita existente enquanto testa o novo modelo.
      </p>

      <p>
        <strong>Meses 1-2 — Fundação:</strong> Definir os pacotes de serviço
        (produtizados ou híbridos). Adotar uma ferramenta de inteligência em
        licitações para automatizar a triagem. Calcular o custo de entrega de
        cada pacote. Documentar processos para que possam ser replicados. Para
        contextualizar como a análise de edital se torna um diferencial nesse
        novo modelo, consulte{' '}
        <Link href="/blog/analise-edital-diferencial-competitivo-consultoria" className="text-brand-navy dark:text-brand-blue hover:underline">
          a análise de edital como diferencial competitivo da consultoria
        </Link>.
      </p>

      <p>
        <strong>Meses 3-4 — Piloto:</strong> Migrar 3 a 5 clientes existentes
        para o novo modelo, preferencialmente clientes com perfil de
        monitoramento (que consomem mais horas de triagem). Manter os demais
        clientes no modelo de horas. Comparar margem e satisfação entre os dois
        grupos.
      </p>

      <p>
        <strong>Meses 5-6 — Expansão:</strong> Com base nos resultados do piloto,
        expandir o modelo produtizado para a base completa. Iniciar prospecção de
        novos clientes já com a proposta de valor escalável. Avaliar viabilidade
        de parcerias white-label com escritórios complementares.
      </p>

      <p>
        O risco de não migrar é ficar preso em um modelo onde o crescimento
        depende exclusivamente de contratar mais analistas — um recurso escasso,
        caro e com curva de aprendizado longa. A tecnologia já existe para
        quebrar essa dependência. O que falta, na maioria das consultorias, é
        a decisão estratégica de mudar. Para quem quer entender a estrutura
        operacional que suporta esse crescimento, vale ler{' '}
        <Link href="/blog/estruturar-setor-licitacao-5-milhoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          como estruturar um setor de licitação enxuto para faturar R$ 5 milhões por ano
        </Link>.
      </p>

      {/* CTA Section — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Use o SmartLic como motor da sua operação escalável — plano para consultorias
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          Triagem automatizada por IA, análise de viabilidade em 4 fatores e
          pipeline de oportunidades. Sua consultoria atende mais clientes sem
          proporcionalmente ampliar a equipe.
        </p>
        <Link
          href="/signup?source=blog&article=escalar-consultoria-sem-depender-horas-tecnicas&utm_source=blog&utm_medium=cta&utm_content=escalar-consultoria-sem-depender-horas-tecnicas&utm_campaign=consultorias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          <Link href="/features" className="underline hover:text-ink">
            Veja todas as funcionalidades
          </Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Por que o modelo de horas técnicas limita o crescimento de consultorias de licitação?</h3>
      <p>
        O modelo de horas técnicas impõe um teto matemático: a receita máxima é
        limitada pelo número de horas disponíveis multiplicado pelo valor cobrado
        por hora. Para crescer, a consultoria precisa contratar mais analistas,
        o que eleva custos fixos proporcionalmente à receita. Uma consultoria com
        3 analistas que cobram R$ 150/hora tem receita máxima teórica de
        R$ 79.200/mês, mas na prática fatura 50% a 65% disso devido a horas não
        faturáveis — resultando em um teto de R$ 40.000 a R$ 51.000/mês.
      </p>

      <h3>Quais são os modelos de escala alternativos para consultorias de licitação?</h3>
      <p>
        Existem quatro modelos principais: produtização (transformar serviços em
        pacotes pré-definidos com preço fixo, desvinculando receita de horas),
        tecnologia como multiplicador (usar ferramentas de IA para atender mais
        clientes com a mesma equipe), modelo híbrido de assinatura mais
        consultoria (receita recorrente base complementada por projetos), e
        white-label com parcerias (licenciar metodologia para ampliar alcance sem
        proporcionalmente ampliar equipe).
      </p>

      <h3>Qual o ticket médio de uma consultoria produtizada versus por hora?</h3>
      <p>
        Consultorias que operam por hora técnica praticam tickets mensais entre
        R$ 3.000 e R$ 8.000 por cliente, dependendo do volume de horas
        contratadas. Consultorias produtizadas, com pacotes pré-definidos de
        monitoramento mais triagem mais análise, praticam tickets entre R$ 2.500
        e R$ 6.000 por cliente, mas com custo de entrega 40% a 60% menor por
        conta da automação. O resultado é margem líquida superior mesmo com
        ticket nominal similar ou inferior.
      </p>

      <h3>Quanto tempo leva para migrar uma consultoria para um modelo escalável?</h3>
      <p>
        A migração gradual leva de 4 a 6 meses, em três fases: meses 1-2,
        definição de pacotes e adoção de ferramenta de automação de triagem;
        meses 3-4, migração dos primeiros 3 a 5 clientes para o novo modelo
        mantendo o modelo anterior para os demais; meses 5-6, expansão do
        modelo produtizado para a base completa e início de prospecção com a
        nova proposta de valor. A recomendação é não migrar todos os clientes
        simultaneamente para preservar a receita durante a transição.
      </p>

      <h3>É possível combinar mais de um modelo de escala na mesma consultoria?</h3>
      <p>
        Sim, e na prática é o cenário mais comum em consultorias de licitação
        maduras. A combinação mais eficaz é o modelo híbrido: assinatura mensal
        para a camada operacional (monitoramento e triagem), complementada por
        serviços avulsos de alto valor (análise detalhada, elaboração de
        proposta, recursos). Essa combinação garante receita recorrente
        previsível enquanto preserva a margem elevada dos projetos consultivos.
      </p>
      {/* TODO: Link para página programática de setor — MKT-003 */}
      {/* TODO: Link para página programática de cidade — MKT-005 */}
    </>
  );
}
