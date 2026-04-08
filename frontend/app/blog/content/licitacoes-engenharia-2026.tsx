import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Sector Guide S1: Licitações de Engenharia e Construção 2026
 *
 * Content cluster: guias setoriais de licitações
 * Target: 3,000-3,500 words | Primary KW: licitações engenharia
 */
export default function LicitacoesEngenharia2026() {
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
                name: 'Qual a modalidade mais comum para obras de engenharia?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Para obras acima de R$ 3,3 milhões, a modalidade obrigatória é a concorrência (Lei 14.133/2021, art. 29, I). Para serviços de engenharia de menor complexidade e valores até R$ 3,3 milhões, o pregão eletrônico é a modalidade mais frequente, representando cerca de 60% dos processos no PNCP. O diálogo competitivo é usado em projetos de alta complexidade técnica onde a administração precisa discutir soluções antes de definir o objeto.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais documentos de habilitação técnica são obrigatórios?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os documentos obrigatórios incluem: atestados de capacidade técnica emitidos por órgãos públicos ou privados, Certidão de Acervo Técnico (CAT) emitida pelo CREA ou CAU, registro da empresa no CREA/CAU da jurisdição, comprovação de equipe técnica mínima (vínculo via CTPS, contrato social ou contrato de prestação de serviços), e certidões negativas de débito (federal, estadual, municipal, FGTS, trabalhista).',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto custa participar de uma licitação de engenharia?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O custo médio por licitação de engenharia varia entre R$ 8.000 e R$ 25.000, incluindo: elaboração de orçamento detalhado (composições SINAPI/SICRO), cronograma físico-financeiro, visita técnica ao local da obra, certidões e garantias (caução ou seguro-garantia de 1% a 5% do valor), e horas de engenheiro responsável técnico. Para obras de grande porte (acima de R$ 10 milhões), o custo pode superar R$ 50.000 por proposta.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é BDI e como calcular para obras públicas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'BDI (Benefícios e Despesas Indiretas) é o percentual adicionado ao custo direto da obra para cobrir despesas indiretas, tributos e lucro. O Acórdão 2.622/2013 do TCU estabelece faixas de referência: para obras de edificação, o BDI médio é de 22,12% (1º quartil 20,34%, 3º quartil 25,00%). O cálculo inclui: administração central (3-5%), seguro e garantia (0,5-1%), risco (0,5-1,5%), despesas financeiras (0,5-1%), lucro (5-8%) e tributos (PIS, COFINS, ISS, totalizando 6-8%). Valores de BDI fora das faixas do TCU podem levar a questionamento pelo tribunal.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais os prazos típicos de um edital de engenharia?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os prazos variam por modalidade: concorrência tem prazo mínimo de 35 dias úteis entre publicação e abertura (Lei 14.133, art. 55, I); pregão eletrônico tem prazo mínimo de 8 dias úteis. O período de esclarecimentos encerra normalmente 3 dias úteis antes da abertura. Após a adjudicação, a assinatura do contrato ocorre em até 60 dias, e a ordem de serviço é emitida em até 30 dias após a assinatura. O ciclo completo — da publicação do edital ao início efetivo da obra — leva tipicamente de 90 a 180 dias.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como empresas pequenas podem participar de obras grandes?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 permite três mecanismos: (1) Consórcio — empresas podem se associar para somar atestados técnicos e capacidade financeira, com limite de até 5 consorciadas; (2) Subcontratação parcial — a vencedora pode subcontratar até 25% da obra (art. 122), permitindo que empresas menores executem parcelas específicas; (3) Reserva para ME/EPP — editais até R$ 80.000 podem ser exclusivos para microempresas e empresas de pequeno porte (art. 48, LC 123/2006). Além disso, licitações com exigência de parcela de maior relevância permitem que a empresa comprove capacidade técnica apenas na parcela principal, não na totalidade da obra.',
                },
              },
            ],
          }),
        }}
      />

      {/* HowTo JSON-LD — steps to participate in engineering bids */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'HowTo',
            name: 'Como participar de licitações de engenharia e construção',
            description:
              'Passo a passo para empresas de engenharia participarem de licitações públicas no Brasil, da habilitação ao contrato.',
            step: [
              {
                '@type': 'HowToStep',
                name: 'Registrar a empresa no CREA/CAU',
                text: 'Obtenha o registro da empresa no Conselho Regional de Engenharia ou Arquitetura da jurisdição. Vincule os responsáveis técnicos com ART/RRT ativa.',
              },
              {
                '@type': 'HowToStep',
                name: 'Montar acervo técnico',
                text: 'Reúna atestados de capacidade técnica e registre as Certidões de Acervo Técnico (CAT) no CREA. Priorize atestados que cubram as parcelas de maior relevância exigidas em editais.',
              },
              {
                '@type': 'HowToStep',
                name: 'Manter certidões atualizadas',
                text: 'Mantenha em dia: CND federal (Receita + PGFN), certidão estadual, municipal, FGTS (CRF), certidão trabalhista (CNDT) e balanço patrimonial do último exercício.',
              },
              {
                '@type': 'HowToStep',
                name: 'Identificar e analisar editais',
                text: 'Monitore o PNCP e portais estaduais diariamente. Analise cada edital verificando: modalidade, valor estimado, prazo, exigências de habilitação e local de execução.',
              },
              {
                '@type': 'HowToStep',
                name: 'Elaborar proposta técnica e comercial',
                text: 'Monte o orçamento com composições SINAPI/SICRO, cronograma físico-financeiro, BDI conforme faixas do TCU, e proposta técnica detalhando metodologia e equipe.',
              },
              {
                '@type': 'HowToStep',
                name: 'Participar da sessão e fase de lances',
                text: 'Na data de abertura, envie a documentação de habilitação e proposta. Em pregões, participe da fase de lances com estratégia de preços previamente definida.',
              },
              {
                '@type': 'HowToStep',
                name: 'Assinar contrato e iniciar obra',
                text: 'Após adjudicação e homologação, assine o contrato dentro do prazo estipulado, apresente a garantia contratual e aguarde a ordem de serviço para mobilização.',
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O setor de engenharia e construção movimenta o maior volume financeiro
        entre todas as categorias de{' '}
        <strong>licitações públicas no Brasil</strong>. Em 2025, o PNCP
        registrou mais de 85.000 publicações relacionadas a obras, serviços de
        engenharia e reformas, com valor estimado agregado superior a R$ 180
        bilhões. Com o avanço do Novo PAC e os investimentos em infraestrutura
        previstos para 2026, a expectativa é de crescimento de 12% a 18% no
        volume de editais do setor. Este guia apresenta um panorama completo
        para empresas que atuam ou pretendem atuar em{' '}
        <strong>licitações de engenharia</strong> — modalidades, faixas de
        valor, requisitos de habilitação, erros frequentes e estratégia de
        priorização.
      </p>

      {/* Section 1 */}
      <h2>Panorama do setor de engenharia em licitações 2026</h2>

      <p>
        O investimento público em infraestrutura no Brasil passa por um ciclo
        de expansão. O Novo PAC, lançado em agosto de 2023 e ampliado em 2024,
        previu R$ 1,7 trilhão em investimentos até 2026, com R$ 371 bilhões
        destinados a infraestrutura social e urbana (saneamento, habitação,
        mobilidade) e R$ 349 bilhões para infraestrutura de transporte
        (rodovias, ferrovias, portos). Esses recursos se traduzem em editais
        nos três níveis federativos — federal, estadual e municipal.
      </p>

      <p>
        No âmbito municipal, o crescimento é ainda mais pronunciado. Municípios
        de médio porte (100 a 500 mil habitantes) aumentaram em 23% o volume
        de licitações de obras entre 2023 e 2025, impulsionados por transferências
        voluntárias e emendas parlamentares. Para empresas de engenharia, isso
        significa que o mercado não está concentrado apenas em grandes obras
        federais — há volume expressivo em pavimentação urbana, construção de
        unidades básicas de saúde, escolas e infraestrutura de saneamento.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Números do setor — Engenharia e Construção em licitações (2025)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Volume de publicações no PNCP:</strong> ~85.000 processos
            relacionados a obras e serviços de engenharia
          </li>
          <li>
            <strong>Valor estimado agregado:</strong> superior a R$ 180 bilhões
            (todas as esferas)
          </li>
          <li>
            <strong>Crescimento previsto 2026:</strong> 12% a 18% em volume,
            impulsionado pelo Novo PAC e emendas parlamentares
          </li>
          <li>
            <strong>Modalidade predominante:</strong> concorrência para obras
            acima de R$ 3,3M; pregão eletrônico para serviços de engenharia
          </li>
          <li>
            <strong>Prazo médio até contrato:</strong> 90 a 180 dias (da
            publicação ao início da obra)
          </li>
        </ul>
      </div>

      <p>
        O{' '}
        <Link href="/blog/pncp-guia-completo-empresas" className="text-brand-navy dark:text-brand-blue hover:underline">
          PNCP (Portal Nacional de Contratações Públicas)
        </Link>{' '}
        é a fonte primária para monitorar esses editais. Desde janeiro de 2024,
        todos os órgãos federais e a maioria dos estaduais são obrigados a
        publicar no portal, tornando-o o ponto de partida para qualquer
        estratégia de monitoramento setorial.
      </p>

      {/* Section 2 */}
      <h2>Modalidades mais comuns em licitações de engenharia</h2>

      <p>
        A Lei 14.133/2021 (Nova Lei de Licitações) redefiniu as modalidades
        aplicáveis a obras e serviços de engenharia. Compreender cada uma é
        essencial para decidir em quais editais investir esforço.
      </p>

      <h3>
        <Link href="/glossario#concorrência" className="text-brand-navy dark:text-brand-blue hover:underline">
          Concorrência
        </Link>
      </h3>

      <p>
        Obrigatória para obras com valor estimado acima de R$ 3.299.000,00
        (atualizado pelo Decreto 11.871/2023). É a modalidade que concentra o
        maior valor financeiro no setor de engenharia. O critério de julgamento
        pode ser menor preço, melhor técnica, ou técnica e preço. Para obras
        de maior complexidade técnica (hospitais, pontes, barragens), o
        julgamento por técnica e preço é mais frequente, o que favorece
        empresas com acervo técnico robusto em detrimento de concorrentes que
        competem exclusivamente por preço.
      </p>

      <h3>Pregão eletrônico</h3>

      <p>
        Aplicável a serviços comuns de engenharia — aqueles cujos padrões de
        desempenho e qualidade podem ser objetivamente definidos pelo edital
        (art. 6º, XIII, Lei 14.133). Na prática, isso inclui serviços de
        manutenção predial, reformas de pequeno porte, instalações elétricas e
        hidráulicas padronizadas, e projetos com especificação técnica
        detalhada. O{' '}
        <Link href="/glossario#pregao-eletrônico" className="text-brand-navy dark:text-brand-blue hover:underline">
          pregão eletrônico
        </Link>{' '}
        representa aproximadamente 60% dos processos de engenharia no PNCP em
        número de editais (embora não em valor agregado, pois obras de grande
        porte usam concorrência).
      </p>

      <h3>Regime Diferenciado de Contratações (RDC)</h3>

      <p>
        Embora criado pela Lei 12.462/2011, o RDC continua vigente e é
        utilizado em obras associadas a programas específicos (PAC, obras de
        educação, saúde e segurança pública). O RDC permite contratação
        integrada (projeto + execução pelo mesmo contratado), o que simplifica
        o processo para empresas com capacidade de projeto. Em 2025, cerca de
        8% dos editais de grandes obras federais ainda utilizaram o RDC.
      </p>

      <h3>Diálogo competitivo</h3>

      <p>
        Modalidade introduzida pela Lei 14.133 para objetos de inovação
        tecnológica ou técnica, ou quando a administração não consegue definir
        a solução sem diálogo prévio. Embora ainda pouco frequente em
        engenharia (menos de 2% dos editais), o diálogo competitivo tende a
        crescer em projetos de infraestrutura inteligente, cidades digitais e
        edificações sustentáveis. Para empresas com capacidade de propor
        soluções inovadoras, é uma oportunidade de diferenciação.
      </p>

      {/* Section 3 */}
      <h2>Faixas de valor típicas em licitações de engenharia</h2>

      <p>
        O valor estimado de um edital de engenharia determina não apenas a
        modalidade, mas também o perfil de concorrência e os requisitos de
        habilitação. Compreender as faixas permite que a empresa foque nos
        segmentos onde tem maior competitividade.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Segmentação por faixa de valor — Obras públicas
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Pequenas obras municipais (R$ 100K - R$ 500K):</strong>{' '}
            Pavimentação de ruas, reformas de prédios públicos, construção de
            calçadas e praças. Maior volume de editais, menor concorrência por
            edital individual. Habilitação técnica menos exigente — atestados
            de obras similares de menor porte são aceitos.
          </li>
          <li>
            <strong>Obras médias (R$ 500K - R$ 5M):</strong>{' '}
            Construção de UBS, escolas, quadras esportivas, redes de
            saneamento. Exigem atestados de capacidade técnica compatíveis
            (normalmente 50% do quantitativo principal). Concorrência moderada
            — 5 a 12 empresas por edital.
          </li>
          <li>
            <strong>Grandes obras (R$ 5M - R$ 50M):</strong>{' '}
            Hospitais, terminais rodoviários, sistemas de esgotamento
            sanitário, pontes. Exigem acervo técnico significativo, equipe
            qualificada e capacidade financeira comprovada (patrimônio líquido
            mínimo de 10% do valor estimado). Concorrência reduzida — 3 a 7
            empresas qualificadas.
          </li>
          <li>
            <strong>Megaprojetos (acima de R$ 50M):</strong>{' '}
            Rodovias, ferrovias, barragens, aeroportos. Frequentemente
            executados por consórcios. Exigem garantia de proposta (1% a 5%
            do valor estimado) e seguro-garantia de execução. Menos de 10
            grupos empresariais competem nessa faixa no Brasil.
          </li>
        </ul>
      </div>

      <p>
        A recomendação estratégica é que empresas identifiquem a faixa onde
        historicamente obtiveram melhor taxa de adjudicação e concentrem
        esforços nela. Uma construtora de médio porte com acervo técnico em
        edificações de até R$ 3 milhões não deveria investir recursos em
        editais de R$ 30 milhões que exigem atestados fora do seu portfólio —
        o custo de elaboração da proposta não se justifica quando a
        probabilidade de habilitação é baixa.
      </p>

      {/* Section 4 */}
      <h2>UFs com maior volume de licitações de engenharia</h2>

      <p>
        A distribuição geográfica dos editais de engenharia não é uniforme.
        Cinco estados concentram aproximadamente 55% do volume total de
        publicações no PNCP para o setor.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Ranking de UFs por volume de editais de engenharia (dados PNCP 2025)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>1. São Paulo (SP):</strong> ~18% do volume total.
            Maior número de municípios com capacidade de investimento próprio.
            Forte presença de obras de infraestrutura urbana e saneamento.
          </li>
          <li>
            <strong>2. Minas Gerais (MG):</strong> ~12% do volume.
            853 municípios geram volume pulverizado. Destaque para obras de
            estradas vicinais e equipamentos de saúde.
          </li>
          <li>
            <strong>3. Rio de Janeiro (RJ):</strong> ~9% do volume.
            Concentrado na região metropolitana e Niterói. Grandes obras de
            mobilidade e revitalização urbana.
          </li>
          <li>
            <strong>4. Paraná (PR):</strong> ~8% do volume.
            Forte investimento estadual em pavimentação e saneamento.
            Municípios de médio porte com boa capacidade de contratação.
          </li>
          <li>
            <strong>5. Bahia (BA):</strong> ~7% do volume.
            Maior volume do Nordeste. Obras de saneamento básico e
            infraestrutura hídrica predominam.
          </li>
        </ul>
      </div>

      <p>
        Para empresas com atuação regional, a estratégia mais eficiente é
        concentrar monitoramento nos estados onde já possuem estrutura
        logística. O custo de mobilização para obras em estados distantes pode
        consumir toda a margem, especialmente em contratos abaixo de
        R$ 1 milhão. A{' '}
        <Link href="/blog/análise-viabilidade-editais-guia" className="text-brand-navy dark:text-brand-blue hover:underline">
          análise de viabilidade por geografia
        </Link>{' '}
        é um dos quatro fatores que determinam se vale a pena investir na
        elaboração de uma proposta.
      </p>

      {/* Section 5 */}
      <h2>Requisitos de habilitação técnica em licitações de engenharia</h2>

      <p>
        A habilitação técnica é a fase que mais elimina empresas em licitações
        de engenharia. Segundo dados do TCU (Acórdão 1.214/2023), cerca de 35%
        das inabilitações em concorrências de obras decorrem de falhas na
        documentação técnica — atestados insuficientes, CATs não registradas,
        ou equipe técnica sem vínculo comprovado.
      </p>

      <h3>
        <Link href="/glossario#atestado-de-capacidade-técnica" className="text-brand-navy dark:text-brand-blue hover:underline">
          Atestados de capacidade técnica
        </Link>
      </h3>

      <p>
        São documentos emitidos por contratantes (públicos ou privados)
        atestando que a empresa executou serviços compatíveis com o objeto da
        licitação. A Lei 14.133 permite que o edital exija atestados que
        comprovem execução de parcelas de maior relevância, com quantitativos
        mínimos. O limite legal é de até 50% do quantitativo de cada parcela
        relevante (art. 67, §1º). Atestados de obras privadas são aceitos,
        desde que acompanhados de ART/RRT e, preferencialmente, com nota
        fiscal comprovando a execução.
      </p>

      <h3>Certidão de Acervo Técnico (CAT)</h3>

      <p>
        A CAT é emitida pelo CREA ou CAU e vincula a responsabilidade técnica
        de um profissional a uma obra ou serviço específico. É o documento que
        comprova que o responsável técnico da empresa efetivamente dirigiu ou
        coordenou a execução de um serviço similar ao licitado. Sem a CAT
        registrada, o atestado de capacidade técnica da empresa não tem
        validade plena para fins de habilitação.
      </p>

      <h3>Equipe técnica mínima</h3>

      <p>
        Editais de obras frequentemente exigem comprovação de equipe técnica
        mínima — engenheiro civil responsável, engenheiro eletricista,
        técnico em segurança do trabalho, entre outros, dependendo do objeto.
        O vínculo pode ser comprovado por CTPS (empregado), contrato social
        (sócio), ou contrato de prestação de serviços com cláusula de
        exclusividade. A equipe deve estar disponível na data de abertura das
        propostas, não apenas na data de assinatura do contrato.
      </p>

      <h3>Certidões e qualificação econômico-financeira</h3>

      <p>
        Além dos documentos técnicos, a habilitação exige: CND federal
        (Receita + PGFN), CRF do FGTS, CNDT (certidão trabalhista), certidões
        estadual e municipal, balanço patrimonial do último exercício social,
        e índices contábeis (liquidez geral, liquidez corrente, solvência
        geral). Para obras acima de R$ 3,3 milhões, é comum a exigência de
        patrimônio líquido mínimo de 10% do valor estimado.
      </p>

      {/* BlogInlineCTA at ~40% of content */}
      <BlogInlineCTA
        slug="licitações-engenharia-2026"
        campaign="guias"
        ctaHref="/explorar"
        ctaText="Explorar licitações grátis"
        ctaMessage="Descubra editais abertos no seu setor — busca gratuita"
      />

      {/* Section 6 */}
      <h2>Erros frequentes em licitações de engenharia</h2>

      <p>
        A experiência acumulada em milhares de processos revela padrões de
        erro que se repetem com frequência preocupante. Evita-los é tão
        importante quanto acertar a precificação.
      </p>

      <h3>Subestimar o BDI</h3>

      <p>
        O{' '}
        <Link href="/glossario#bdi" className="text-brand-navy dark:text-brand-blue hover:underline">
          BDI (Benefícios e Despesas Indiretas)
        </Link>{' '}
        é frequentemente calculado de forma superficial, sem considerar as
        particularidades do projeto. Empresas que aplicam um BDI padrão de
        25% para qualquer obra ignoram que obras com prazo longo exigem maior
        provisão para despesas financeiras, que obras em localidades remotas
        tem custo de administração central mais elevado, e que o regime
        tributário da empresa impacta diretamente a composição. O Acórdão
        2.622/2013 do TCU é a referência obrigatória — valores fora das
        faixas ali definidas serão questionados.
      </p>

      <h3>Ignorar a convenção coletiva regional</h3>

      <p>
        Os custos de mão de obra em orçamentos de obras públicas devem
        refletir os pisos salariais da convenção coletiva vigente na região
        de execução, não a convenção da sede da empresa. Uma construtora
        de SP que orça uma obra na BA utilizando pisos salariais paulistas
        terá custos inflados e perderá competitividade. Por outro lado,
        utilizar pisos inferiores ao da convenção local configura proposta
        inexequível, sujeita a desclassificação (art. 59, Lei 14.133).
      </p>

      <h3>Não visitar o local da obra</h3>

      <p>
        Embora a Lei 14.133 tenha substituído a obrigatoriedade de visita
        técnica pela declaração de conhecimento das condições locais (art. 63,
        §2o), a visita continua sendo crítica para a elaboração de uma
        proposta competitiva. Condições de solo, acesso ao canteiro,
        disponibilidade de materiais na região e infraestrutura existente são
        fatores que impactam diretamente o custo e que não estão
        necessariamente detalhados no projeto básico.
      </p>

      <h3>Prazo inexequível na proposta</h3>

      <p>
        Propor um cronograma agressivo para parecer mais competitivo é uma
        estratégia que invariavelmente resulta em aditivos de prazo,
        penalidades contratuais e desgaste com o órgão contratante. O prazo
        proposto deve considerar: mobilização de equipe e equipamentos,
        sazonalidade climática (período de chuvas), prazos de importação de
        materiais especiais, e curvas de aprendizado em técnicas construtivas
        específicas.
      </p>

      <h3>Documentação de habilitação vencida</h3>

      <p>
        Certidões têm prazo de validade (normalmente 30 a 180 dias). Empresas
        que monitoram editais e decidem participar no último momento
        frequentemente descobrem que uma certidão expirou entre a publicação
        do edital e a data de abertura. A prática recomendada é manter um
        calendário de renovação com antecedência mínima de 15 dias para cada
        documento.
      </p>

      {/* Section 7 */}
      <h2>Como analisar viabilidade de um edital de engenharia</h2>

      <p>
        Antes de investir as 40 a 80 horas necessárias para elaborar uma
        proposta completa de obra, é fundamental avaliar se o edital tem
        viabilidade para o perfil da empresa. A{' '}
        <Link href="/blog/análise-viabilidade-editais-guia" className="text-brand-navy dark:text-brand-blue hover:underline">
          análise de viabilidade
        </Link>{' '}
        usa quatro fatores com pesos calibrados para o setor de engenharia.
      </p>

      <h3>Fator 1: Modalidade (peso 30%)</h3>

      <p>
        A modalidade indica o perfil de competição. Em concorrências por
        técnica e preço, empresas com acervo técnico diferenciado têm
        vantagem. Em pregões de menor preço, a competição é acirrada e a
        margem é comprimida. A empresa deve avaliar em qual modalidade seu
        perfil gera maior taxa de adjudicação histórica.
      </p>

      <h3>Fator 2: Timeline (peso 25%)</h3>

      <p>
        O prazo entre publicação e abertura determina se há tempo para
        elaborar uma proposta competitiva. Para obras, o prazo mínimo legal
        em concorrência é 35 dias úteis, mas propostas de qualidade exigem
        frequentemente o dobro desse tempo. Adicionalmente, o prazo de
        execução contratual deve ser compatível com a capacidade operacional
        da empresa — uma construtora com três obras em andamento pode não
        ter equipamentos disponíveis para uma quarta no mesmo período.
      </p>

      <h3>Fator 3: Valor estimado (peso 25%)</h3>

      <p>
        O valor deve estar dentro da faixa onde a empresa historicamente é
        competitiva. Além do valor absoluto, é importante verificar se o
        orçamento de referência utiliza tabelas atualizadas (SINAPI, SICRO)
        e se os quantitativos estão compatíveis com o projeto básico. Editais
        com orçamentos defasados em mais de 6 meses podem ter valores
        estimados irrealistas.
      </p>

      <h3>Fator 4: Geografia (peso 20%)</h3>

      <p>
        O custo de mobilização (transporte de equipamentos, alojamento de
        equipe, frete de materiais) pode representar de 3% a 12% do custo
        total da obra. Editais em regiões onde a empresa já possui canteiro
        ou base operacional têm vantagem natural. Para obras em localidades
        remotas, o acréscimo logístico deve ser calculado antes da decisão
        de participar.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático — Viabilidade de edital de engenharia
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          Construtora de médio porte em MG avalia uma concorrência para
          construção de escola em município do interior de MG, valor estimado
          R$ 2,8 milhões, prazo de 45 dias para proposta:
        </p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>Modalidade (30%):</strong> Concorrência, empresa tem
            histórico de adjudicação nesta modalidade = 8/10 x 0,30 = 2,40
          </li>
          <li>
            <strong>Timeline (25%):</strong> 45 dias úteis, prazo confortável
            para orçamento e visita técnica = 8/10 x 0,25 = 2,00
          </li>
          <li>
            <strong>Valor (25%):</strong> R$ 2,8M dentro da faixa histórica
            de adjudicação (R$ 1M - R$ 5M) = 9/10 x 0,25 = 2,25
          </li>
          <li>
            <strong>Geografia (20%):</strong> Interior de MG, 180 km da sede,
            região conhecida = 7/10 x 0,20 = 1,40
          </li>
          <li className="pt-2 font-semibold">
            Pontuação total: 8,05/10 — Viabilidade alta. Recomendado
            prosseguir com elaboração de proposta.
          </li>
        </ul>
      </div>

      <p>
        Esse modelo de avaliação permite comparar múltiplos editais
        simultaneamente e alocar os recursos de elaboração de proposta nas
        oportunidades com maior probabilidade de retorno. Para entender o
        modelo em profundidade e aplicar a outros setores, consulte{' '}
        <Link href="/blog/como-participar-primeira-licitação-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          como participar da sua primeira licitação em 2026
        </Link>.
      </p>

      {/* Section 8 */}
      <h2>Timeline típico de uma licitação de engenharia</h2>

      <p>
        O ciclo completo de uma licitação de obra pública é mais longo do que
        em outros setores, devido à complexidade técnica e aos requisitos
        legais. Compreender cada etapa evita surpresas e permite planejamento
        adequado de recursos.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Cronologia típica — Da publicação ao início da obra
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Dia 0:</strong> Publicação do edital no PNCP e diário
            oficial. Início do prazo de publicidade.
          </li>
          <li>
            <strong>Dias 1-25:</strong> Período para análise do edital,
            visita ao local da obra, elaboração de orçamento e proposta.
            Pedidos de esclarecimento devem ser enviados até o prazo definido
            (geralmente 10-15 dias antes da abertura).
          </li>
          <li>
            <strong>Dias 20-30:</strong> Sessão de esclarecimentos e
            respostas da comissão. Eventuais impugnações ao edital devem ser
            apresentadas até 3 dias úteis antes da abertura (concorrência).
          </li>
          <li>
            <strong>Dia 35+:</strong> Abertura das propostas e documentação
            de habilitação. Em concorrência, as propostas são analisadas
            pela comissão em sessão pública.
          </li>
          <li>
            <strong>Dias 35-65:</strong> Análise das propostas pela comissão,
            diligências, parecer técnico. Prazo para recursos (5 dias úteis
            após decisão de habilitação e após julgamento).
          </li>
          <li>
            <strong>Dias 65-90:</strong> Adjudicação e homologação. Convocação
            do vencedor para assinatura do contrato (até 60 dias da
            homologação, prorrogáveis por igual período).
          </li>
          <li>
            <strong>Dias 90-120:</strong> Assinatura do contrato, apresentação
            de garantia contratual e seguro, emissão da ordem de serviço.
          </li>
          <li>
            <strong>Dia 120+:</strong> Mobilização do canteiro e início
            efetivo da obra.
          </li>
        </ul>
      </div>

      <p>
        Esse cronograma assume uma licitação sem recursos ou impugnações
        complexas. Na prática, recursos ao TCU ou judicialização podem
        estender o processo em 60 a 180 dias adicionais. Por isso, empresas
        de engenharia devem manter um pipeline com pelo menos 3 a 5 editais
        simultâneos para garantir fluxo contínuo de contratos. Para aprender
        como organizar esse fluxo, veja{' '}
        <Link href="/blog/lei-14133-guia-fornecedores" className="text-brand-navy dark:text-brand-blue hover:underline">
          o guia completo da Lei 14.133 para fornecedores
        </Link>.
      </p>

      {/* Section 9 - Setores correlatos */}
      <h2>Conexões com outros setores em licitações</h2>

      <p>
        O setor de engenharia frequentemente se conecta com outros segmentos
        em editais multisserviço. Obras de hospitais incluem componentes de{' '}
        <Link href="/blog/licitações-saúde-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          equipamentos e serviços de saúde
        </Link>. Projetos de cidades inteligentes combinam infraestrutura civil com{' '}
        <Link href="/blog/licitações-ti-software-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          soluções de TI e software
        </Link>{' '}
        — sistemas de monitoramento, automação predial, redes de dados. Empresas
        que atuam na interseção entre engenharia e tecnologia têm acesso a um
        nicho de editais com menor concorrência e margens mais atrativas.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Monitore editais de engenharia com inteligência — 14 dias grátis
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic classifica editais por relevância setorial e analisa
          viabilidade automaticamente. Sua equipe recebe apenas as obras que
          fazem sentido para o perfil da empresa.
        </p>
        <Link
          href="/signup?source=blog&article=licitações-engenharia-2026&utm_source=blog&utm_medium=cta&utm_content=licitações-engenharia-2026&utm_campaign=guias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito. Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">
            página de recursos
          </Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Qual a modalidade mais comum para obras de engenharia?</h3>
      <p>
        Para obras acima de R$ 3,3 milhões, a modalidade obrigatória é a{' '}
        <Link href="/glossario#concorrência" className="text-brand-navy dark:text-brand-blue hover:underline">
          concorrência
        </Link>{' '}
        (Lei 14.133/2021, art. 29, I). Para serviços de engenharia de menor
        complexidade e valores até R$ 3,3 milhões, o pregão eletrônico é a
        modalidade mais frequente, representando cerca de 60% dos processos no
        PNCP. O diálogo competitivo é usado em projetos de alta complexidade
        técnica onde a administração precisa discutir soluções antes de definir
        o objeto. A escolha da modalidade impacta diretamente o critério de
        julgamento e o perfil de concorrentes.
      </p>

      <h3>Quais documentos de habilitação técnica são obrigatórios?</h3>
      <p>
        Os documentos obrigatórios incluem:{' '}
        <Link href="/glossario#atestado-de-capacidade-técnica" className="text-brand-navy dark:text-brand-blue hover:underline">
          atestados de capacidade técnica
        </Link>{' '}
        emitidos por contratantes anteriores, Certidão de Acervo Técnico (CAT)
        emitida pelo CREA ou CAU, registro da empresa no conselho profissional
        da jurisdição, comprovação de equipe técnica mínima com vínculo
        profissional, e certidões negativas de débito (federal, estadual,
        municipal, FGTS, trabalhista). Além disso, editais de maior valor
        exigem balanço patrimonial e índices contábeis que comprovem capacidade
        econômico-financeira.
      </p>

      <h3>Quanto custa participar de uma licitação de engenharia?</h3>
      <p>
        O custo médio varia entre R$ 8.000 e R$ 25.000 por licitação,
        incluindo: elaboração de orçamento detalhado com composições
        SINAPI/SICRO (20 a 60 horas de engenheiro orçamentista), cronograma
        físico-financeiro, visita técnica ao local da obra (transporte e
        diárias), certidões e documentação de habilitação, e garantia de
        proposta quando exigida (caução de 1% a 5% do valor). Para obras de
        grande porte (acima de R$ 10 milhões), o custo pode superar R$ 50.000,
        incluindo elaboração de proposta técnica detalhada e mobilização de
        equipe multidisciplinar.
      </p>

      <h3>O que é BDI e como calcular para obras públicas?</h3>
      <p>
        O{' '}
        <Link href="/glossario#bdi" className="text-brand-navy dark:text-brand-blue hover:underline">
          BDI
        </Link>{' '}
        (Benefícios e Despesas Indiretas) é o percentual adicionado ao custo
        direto da obra para cobrir despesas indiretas, tributos e lucro. O
        Acórdão 2.622/2013 do TCU estabelece faixas de referência: para
        edificações, o BDI médio é de 22,12% (primeiro quartil 20,34%,
        terceiro quartil 25,00%). Para obras de infraestrutura rodoviária,
        a faixa é de 18% a 23%. O cálculo deve considerar: administração
        central (3% a 5%), seguro e garantia (0,5% a 1%), risco (0,5% a 1,5%),
        despesas financeiras (0,5% a 1%), lucro (5% a 8%) e tributos
        (PIS + COFINS + ISS, totalizando 6% a 8%). Valores de BDI fora das
        faixas do TCU podem motivar questionamento pelo tribunal de contas.
      </p>

      <h3>Quais os prazos típicos de um edital de engenharia?</h3>
      <p>
        Os prazos variam por modalidade: concorrência tem prazo mínimo de 35
        dias úteis entre publicação e abertura (Lei 14.133, art. 55, I);
        pregão eletrônico tem prazo mínimo de 8 dias úteis. O período de
        esclarecimentos encerra normalmente 3 dias úteis antes da abertura.
        Após adjudicação, a assinatura do contrato ocorre em até 60 dias.
        O ciclo completo — da publicação ao início efetivo da obra — leva
        tipicamente de 90 a 180 dias em processos sem impugnação.
        Judicialização ou recursos ao TCU podem estender em 60 a 180 dias
        adicionais.
      </p>

      <h3>Como empresas pequenas podem participar de obras grandes?</h3>
      <p>
        A Lei 14.133/2021 oferece três mecanismos principais: (1) Consórcio —
        empresas podem se associar para somar atestados técnicos e capacidade
        financeira, com até 5 consorciadas; (2) Subcontratação parcial — a
        vencedora pode subcontratar até 25% do valor da obra (art. 122),
        permitindo que empresas menores executem parcelas específicas; (3)
        Reserva para ME/EPP — licitações até R$ 80.000 podem ser exclusivas
        para microempresas e empresas de pequeno porte (art. 48, LC 123/2006).
        Adicionalmente, a exigência de parcela de maior relevância permite que
        a empresa comprove capacidade técnica apenas na parcela principal, não
        na totalidade da obra, facilitando o acesso de empresas em crescimento.
      </p>
    </>
  );
}
