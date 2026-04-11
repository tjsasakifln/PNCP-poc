import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO Sector Guide S2: Licitações de TI e Software 2026
 *
 * Content cluster: guias setoriais de licitações
 * Target: 3,000-3,500 words | Primary KW: licitações tecnologia
 */
export default function LicitacoesTISoftware2026() {
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
                name: 'Qual a modalidade mais usada para licitações de TI?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O pregão eletrônico é a modalidade dominante, utilizada em mais de 80% dos editais de TI publicados no PNCP. A Lei 14.133/2021 classifica a maioria dos serviços de TI como "serviços comuns" (art. 6o, XIII), o que torna o pregão obrigatório. Exceções incluem: desenvolvimento de software sob medida de alta complexidade (que pode usar concorrência por técnica e preço) e aquisição de licenças de software proprietário sem concorrente (que pode ser contratada por inexigibilidade, art. 74, I).',
                },
              },
              {
                '@type': 'Question',
                name: 'Posso participar de licitação de software sendo startup ou MEI?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. A Lei Complementar 123/2006 garante tratamento diferenciado para ME e EPP em licitações: empate ficto (até 5% acima do menor preço em pregão), prazo adicional para regularização fiscal (5 dias úteis), e licitações exclusivas para valores até R$ 80.000. Para startups constituídas como ME/EPP, esses benefícios se aplicam integralmente. A principal barreira não é jurídica, mas documental: editais de TI frequentemente exigem atestados de capacidade técnica com quantitativos mínimos, o que pode ser desafiador para empresas novas.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais certificações são exigidas em editais de TI?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'As certificações mais frequentes em editais de TI são: ISO 27001 (segurança da informação, exigida em ~15% dos editais de TI), ISO 9001 (gestão da qualidade), CMMI nível 2 ou 3 (maturidade de processos de software, exigida em ~8% dos editais), e MPS.BR (modelo brasileiro de melhoria de processos). Para profissionais individuais da equipe técnica, são comuns: PMP (gerente de projetos), ITIL (gestão de serviços), AWS/Azure/GCP (cloud), e LGPD/DPO (proteção de dados). A exigência de certificações específicas como único critério de habilitação pode ser questionada quando restringe a competitividade.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é prova de conceito (POC) em licitações de software?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A prova de conceito (POC) é um procedimento previsto na Lei 14.133 (art. 17, §3o) que permite ao órgão contratante verificar se a solução ofertada atende aos requisitos técnicos do edital antes da adjudicação. Em editais de TI, a POC normalmente envolve: demonstração funcional do software em ambiente controlado, validação de requisitos técnicos específicos (integração, performance, segurança), e execução de casos de teste predefinidos. O prazo típico é de 5 a 15 dias úteis. A POC é eliminatória — se a solução não for aprovada, a empresa é desclassificada e o próximo colocado é convocado.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como funciona o modelo de fábrica de software em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O modelo de fábrica de software é a forma predominante de contratação de desenvolvimento no governo. O órgão contrata um volume de Pontos de Função (PF) ou UST (Unidades de Serviço Técnico) por período, e demanda entregas conforme necessidade. Valores típicos: R$ 400 a R$ 900 por Ponto de Função, dependendo da complexidade e da região. Contratos variam de 5.000 PF/ano (órgãos menores) a 100.000+ PF/ano (grandes ministérios). A métrica de PF segue a metodologia IFPUG/NESMA, e a contagem é frequentemente fonte de disputas contratuais.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais UFs publicam mais editais de TI?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O Distrito Federal (DF) lidera com folga, concentrando aproximadamente 25% do valor total de editais de TI, devido à concentração de órgãos federais em Brasília. Em seguida: São Paulo (SP) com ~18% (governo estadual + prefeituras de grande porte), Rio de Janeiro (RJ) com ~12%, e Minas Gerais (MG) com ~8%. Para o governo federal especificamente, praticamente todos os grandes contratos de TI têm execução em Brasília, mesmo quando o órgão tem presença nacional.',
                },
              },
            ],
          }),
        }}
      />

      {/* HowTo JSON-LD — steps to participate in IT bids */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'HowTo',
            name: 'Como participar de licitações de TI e software',
            description:
              'Passo a passo para empresas de tecnologia participarem de licitações públicas no Brasil, do cadastro à adjudicação.',
            step: [
              {
                '@type': 'HowToStep',
                name: 'Obter SICAF e certificações',
                text: 'Cadastre a empresa no SICAF (Sistema de Cadastramento Unificado de Fornecedores) e obtenha certificações relevantes (ISO 27001, ISO 9001, MPS.BR) conforme o perfil de editais pretendido.',
              },
              {
                '@type': 'HowToStep',
                name: 'Montar portfólio de atestados técnicos',
                text: 'Reuna atestados de capacidade técnica de clientes anteriores (públicos e privados) que comprovem experiência em serviços similares aos licitados. Priorize atestados com quantitativos mensuráveis.',
              },
              {
                '@type': 'HowToStep',
                name: 'Monitorar editais no PNCP e portais estaduais',
                text: 'Acompanhe diariamente o PNCP, ComprasGov e portais estaduais de licitação. Filtre por palavras-chave do setor: desenvolvimento de software, outsourcing de TI, cloud, cibersegurança.',
              },
              {
                '@type': 'HowToStep',
                name: 'Analisar viabilidade técnica e comercial',
                text: 'Avalie cada edital nos 4 fatores de viabilidade: modalidade, timeline, valor estimado e geografia. Para TI, verifique também: stack tecnológica exigida, métricas de SLA e equipe mínima.',
              },
              {
                '@type': 'HowToStep',
                name: 'Elaborar proposta técnica e de preços',
                text: 'Monte a proposta técnica (metodologia, equipe, cronograma, ferramentas) e a planilha de preços (por PF, UST ou hora técnica). Atenda a todos os requisitos do termo de referência.',
              },
              {
                '@type': 'HowToStep',
                name: 'Participar do pregão e fase de lances',
                text: 'No dia do pregão eletrônico, participe da fase de lances com limite de preço previamente calculado. Após encerramento, esteja preparado para enviar documentação de habilitação no prazo (geralmente 2-4 horas).',
              },
              {
                '@type': 'HowToStep',
                name: 'Executar POC se exigida',
                text: 'Se o edital preve prova de conceito, demonstre a solução conforme os critérios definidos. Prepare ambiente, dados de teste e equipe técnica com antecedência.',
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O governo brasileiro é o maior comprador de tecnologia do país. Em
        2025, o PNCP registrou mais de 62.000 publicações relacionadas a{' '}
        <strong>tecnologia da informação, software e serviços digitais</strong>,
        com valor estimado agregado superior a R$ 45 bilhões. A transformação
        digital do setor público — impulsionada pela Estratégia Nacional de
        Governo Digital, pela LGPD e pela obrigatoriedade do PNCP — gerou um
        crescimento de 22% no volume de editais de TI entre 2023 e 2025. Para
        empresas de tecnologia, o mercado B2G representa uma oportunidade
        concreta e recorrente, mas exige compreensão das regras específicas de{' '}
        <strong>licitações de tecnologia</strong>. Este guia cobre modalidades,
        tipos de objeto, faixas de valor, requisitos e estratégias para o
        setor.
      </p>

      {/* Section 1 */}
      <h2>Panorama do setor de TI em licitações 2026</h2>

      <p>
        Três forças estruturais estão expandindo o mercado de TI governamental
        em 2026. A primeira é a continuidade da Estratégia Nacional de Governo
        Digital (Decreto 10.332/2020, atualizado em 2024), que determina a
        digitalização de 100% dos serviços públicos federais até 2026 e
        impulsiona contratações de plataformas digitais, cloud e integração
        de sistemas.
      </p>

      <p>
        A segunda é a LGPD (Lei 13.709/2018), cuja fiscalização intensificada
        pela ANPD a partir de 2024 forçou órgãos públicos a contratar serviços
        de adequação, auditoria de dados, implementação de controles de acesso
        e nomeação de encarregados (DPOs). Editais com componente LGPD
        cresceram 45% entre 2024 e 2025.
      </p>

      <p>
        A terceira é a migração para cloud. O governo federal publicou a
        Portaria SGD/ME 778/2019 (atualizada em 2023), que estabelece a
        contratação de serviços de computação em nuvem como modelo preferencial.
        Grandes órgãos como Serpro, Dataprev e ministérios estão migrando
        datacenters on-premises para AWS GovCloud, Azure Government e nuvem
        privada, gerando demanda por serviços de migração, arquitetura cloud
        e operação (CloudOps/DevOps).
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Números do setor — TI e Software em licitações (2025)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Volume de publicações no PNCP:</strong> ~62.000 processos
            relacionados a TI, software e serviços digitais
          </li>
          <li>
            <strong>Valor estimado agregado:</strong> superior a R$ 45 bilhões
            (todas as esferas)
          </li>
          <li>
            <strong>Crescimento 2023-2025:</strong> +22% em volume de editais,
            +35% em valor agregado
          </li>
          <li>
            <strong>Modalidade predominante:</strong> pregão eletrônico (80%+
            dos processos)
          </li>
          <li>
            <strong>UF com maior concentração:</strong> DF (governo federal),
            seguido de SP, RJ e MG
          </li>
          <li>
            <strong>Segmentos em alta:</strong> cloud migration, cibersegurança,
            adequação LGPD, IA/ML, RPA (automação de processos)
          </li>
        </ul>
      </div>

      <p>
        O monitoramento desses editais no{' '}
        <Link href="/blog/pncp-guia-completo-empresas" className="text-brand-navy dark:text-brand-blue hover:underline">
          PNCP
        </Link>{' '}
        e no ComprasGov é essencial. A classificação setorial por{' '}
        <Link href="/blog/inteligencia-artificial-licitacoes-como-funciona" className="text-brand-navy dark:text-brand-blue hover:underline">
          inteligência artificial
        </Link>{' '}
        permite filtrar o volume massivo de publicações e identificar apenas
        os editais alinhados ao perfil técnico da empresa.
      </p>

      {/* Section 2 */}
      <h2>Modalidades mais comuns em licitações de TI</h2>

      <h3>
        <Link href="/glossario#pregao-eletrônico" className="text-brand-navy dark:text-brand-blue hover:underline">
          Pregão eletrônico
        </Link>{' '}
        — o padrão do setor
      </h3>

      <p>
        O pregão eletrônico é utilizado em mais de 80% dos editais de TI. A
        Lei 14.133 classifica serviços de TI como &ldquo;serviços comuns&rdquo;
        quando os padrões de desempenho e qualidade podem ser objetivamente
        definidos no edital. Na prática, isso abrange: outsourcing de TI,
        licenciamento de software padrão, serviços de infraestrutura (hosting,
        cloud), suporte técnico, help desk e desenvolvimento de software com
        especificação funcional detalhada.
      </p>

      <p>
        O critério de julgamento é predominantemente menor preço por item ou
        por lote. A fase de lances é competitiva e exige que a empresa tenha
        calculado previamente o preço mínimo sustentável — preço abaixo do
        custo operacional leva a contratos deficitários que comprometem a
        qualidade da entrega e a reputação da empresa.
      </p>

      <h3>
        <Link href="/glossario#ata-de-registro-de-preços" className="text-brand-navy dark:text-brand-blue hover:underline">
          Ata de registro de preços (ARP)
        </Link>
      </h3>

      <p>
        A ARP é uma ferramenta estratégica no setor de TI. O órgão gerenciador
        realiza o pregão, registra preços unitários (por hora técnica, por
        ponto de função, por licença), e demanda conforme necessidade ao longo
        de 12 meses (prorrogável por mais 12). Outros órgãos podem aderir à
        ata mediante autorização.
      </p>

      <p>
        Para empresas de TI, a ARP tem vantagens concretas: volume garantido
        (o órgão se compromete com quantidade mínima), previsibilidade de
        receita, e possibilidade de atender múltiplos órgãos com uma única
        licitação vencida. Em contrapartida, o preço registrado deve ser
        competitivo o suficiente para vencer o pregão, mas com margem
        suficiente para sustentar a operação por 12 a 24 meses sem reajuste.
      </p>

      <h3>
        <Link href="/glossario#inexigibilidade" className="text-brand-navy dark:text-brand-blue hover:underline">
          Inexigibilidade
        </Link>
      </h3>

      <p>
        A inexigibilidade (art. 74, I, Lei 14.133) é aplicável quando a
        contratação envolve software proprietário com fornecedor exclusivo.
        Se a empresa desenvolve um produto próprio que não tem concorrente
        direto para atender a necessidade do órgão, a contratação pode ser
        direta, sem licitação. É necessário comprovar a exclusividade por
        meio de declaração do fabricante ou atestado de entidade representativa.
        Aproximadamente 12% das contratações de TI no governo federal utilizam
        inexigibilidade, especialmente para renovação de licenças e contratos
        de manutenção de sistemas legados.
      </p>

      {/* Section 3 */}
      <h2>Tipos de objeto em licitações de TI</h2>

      <p>
        O universo de editais de TI é diverso. Compreender os tipos de objeto
        ajuda a identificar os nichos onde a empresa tem maior competitividade.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Principais tipos de objeto em editais de TI
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Fábrica de software (desenvolvimento):</strong> contratação
            por Pontos de Função (PF) ou UST. Inclui análise, codificação,
            testes e implantação. Contratos típicos: 12-60 meses, R$ 500K a
            R$ 50M+.
          </li>
          <li>
            <strong>Licenciamento de software:</strong> aquisição de licenças
            (Microsoft, Oracle, SAP, Red Hat, etc.) ou subscrição SaaS.
            Frequentemente via ARP. Valores: R$ 50K a R$ 20M.
          </li>
          <li>
            <strong>Outsourcing / service desk:</strong> alocação de
            profissionais de TI (desenvolvedores, DBAs, analistas de infra).
            Contratação por posto de trabalho ou por UST. Mercado de alto
            volume.
          </li>
          <li>
            <strong>Infraestrutura cloud:</strong> migração para nuvem,
            arquitetura cloud-native, serviços gerenciados (IaaS/PaaS/SaaS).
            Segmento em crescimento acelerado desde 2023.
          </li>
          <li>
            <strong>Cibersegurança:</strong> SOC (Security Operations Center),
            pentest, análise de vulnerabilidades, gestão de identidades (IAM),
            DLP. Demanda impulsionada por LGPD e ataques a órgãos públicos.
          </li>
          <li>
            <strong>Manutenção e sustentação:</strong> suporte a sistemas
            legados, correção de bugs, evoluções menores. Contratos de 12-24
            meses. Menor margem, porém receita recorrente e estável.
          </li>
          <li>
            <strong>Consultoria e governanca de TI:</strong> PDTIC (Plano
            Diretor de TI), mapeamento de processos, adequação LGPD, auditoria.
            Valores menores (R$ 100K-R$ 1M), mas exigem qualificação técnica
            específica.
          </li>
        </ul>
      </div>

      {/* Section 4 */}
      <h2>Faixas de valor em licitações de TI</h2>

      <p>
        O setor de TI tem amplitude de valor que vai de contratos de
        R$ 20.000 (dispensa para microsserviços) a contratos de centenas de
        milhões (outsourcing de grandes ministérios). A segmentação por faixa
        permite foco estratégico.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Segmentação por faixa de valor — TI e Software
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Microsserviços e dispensas (R$ 20K - R$ 200K):</strong>{' '}
            Desenvolvimento de módulos, integração de APIs, consultoria pontual.
            Baixa barreira de entrada. Ideal para startups e ME/EPP. Volume
            alto, mas valor individual baixo.
          </li>
          <li>
            <strong>Projetos médios (R$ 200K - R$ 2M):</strong>{' '}
            Desenvolvimento de sistemas, implantação de ERP/CRM, migração de
            plataforma. Exigem atestados de projetos similares. Concorrência
            moderada: 6 a 15 empresas por edital.
          </li>
          <li>
            <strong>Grandes contratos (R$ 2M - R$ 20M):</strong>{' '}
            Fábrica de software, outsourcing completo, infraestrutura cloud
            de grande porte. Exigem certificações (ISO, CMMI), equipe técnica
            robusta e capacidade financeira comprovada. Concorrência: 3 a 8
            empresas.
          </li>
          <li>
            <strong>Megacontratos (acima de R$ 20M):</strong>{' '}
            Outsourcing ministerial, datacenter completo, plataformas
            nacionais. Dominados por grandes integradoras. Frequentemente
            exigem consórcio.
          </li>
        </ul>
      </div>

      {/* Section 5 */}
      <h2>UFs com maior volume de editais de TI</h2>

      <p>
        A geografia dos editais de TI é fortemente concentrada no Distrito
        Federal, reflexo da centralização administrativa do governo federal.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Ranking de UFs por volume e valor de editais de TI (dados PNCP 2025)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>1. Distrito Federal (DF):</strong> ~25% do valor total.
            Ministérios, autarquias, tribunais. Maiores contratos do país
            (Serpro, Dataprev, STF, TSE). Execução presencial frequentemente
            exigida em Brasília.
          </li>
          <li>
            <strong>2. São Paulo (SP):</strong> ~18% do valor. Governo
            estadual (Prodesp), prefeitura da capital, municípios de grande
            porte (Campinas, Santos, Guarulhos). Forte demanda por cibersegurança
            e cloud.
          </li>
          <li>
            <strong>3. Rio de Janeiro (RJ):</strong> ~12% do valor. Petrobras,
            BNDES, Marinha, Fiocruz. Concentração em grandes órgãos federais
            com sede no RJ.
          </li>
          <li>
            <strong>4. Minas Gerais (MG):</strong> ~8% do valor. Governo
            estadual (Prodemge), universidades federais (UFMG, UFU, UFJF).
            Volume diversificado entre capital e interior.
          </li>
          <li>
            <strong>5. Rio Grande do Sul (RS):</strong> ~5% do valor. Banrisul,
            PROCERGS, universidades. Histórico de investimento em TI acima
            da média regional.
          </li>
        </ul>
      </div>

      <p>
        Para empresas fora do DF, uma estratégia válida é começar por editais
        estaduais e municipais da própria região, onde a presença local é
        vantagem competitiva, e expandir para o governo federal conforme o
        portfólio de atestados cresce.
      </p>

      {/* Section 6 */}
      <h2>Requisitos técnicos em licitações de TI</h2>

      <p>
        A habilitação técnica em editais de TI combina exigências
        institucionais (certificações da empresa) com exigências individuais
        (qualificação da equipe).
      </p>

      <h3>Atestados de capacidade técnica</h3>

      <p>
        Atestados são o principal documento de habilitação. Devem comprovar
        experiência em serviços compatíveis em natureza e quantidade. Para
        fábrica de software, o edital pode exigir atestado de execução de,
        por exemplo, 5.000 Pontos de Função em 12 meses. Para outsourcing,
        atestado de alocação de 20+ profissionais de TI simultaneamente.
        O limite legal é de 50% do quantitativo licitado (art. 67, §1o,
        Lei 14.133).
      </p>

      <h3>Certificações da empresa</h3>

      <p>
        As certificações mais frequentes em editais de TI incluem: ISO 27001
        (segurança da informação, exigida em ~15% dos editais), ISO 9001
        (gestão da qualidade, ~12%), CMMI nível 2 ou 3 (maturidade de
        processos, ~8%), e MPS.BR (modelo brasileiro, aceito como alternativa
        ao CMMI). A obtenção de ISO 27001 leva tipicamente de 6 a 12 meses
        e custa entre R$ 30.000 e R$ 80.000 — é um investimento que amplia
        significativamente o universo de editais disputáveis.
      </p>

      <h3>Equipe técnica mínima</h3>

      <p>
        Editais de TI frequentemente exigem comprovação de equipe com perfis
        específicos: gerente de projetos (PMP ou PRINCE2), arquiteto de
        software (experiência em microsserviços, cloud), DBA (certificação
        Oracle/PostgreSQL), analista de segurança (CEH, CISSP, CompTIA
        Security+), especialista LGPD (DPO certificado). O vinculo pode ser
        por CLT, contrato de prestação de serviços ou declaração de
        compromisso de contratação futura.
      </p>

      {/* BlogInlineCTA at ~40% */}
      <BlogInlineCTA
        slug="licitações-ti-software-2026"
        campaign="guias"
        ctaHref="/explorar"
        ctaText="Explorar licitações grátis"
        ctaMessage="Descubra editais abertos no seu setor — busca gratuita"
      />

      {/* Section 7 */}
      <h2>Armadilhas comuns em editais de TI</h2>

      <p>
        O setor de TI possui armadilhas específicas que, se não identificadas
        na análise do edital, podem comprometer a execução do contrato ou
        inviabilizar a participação.
      </p>

      <h3>Descrição genérica do objeto</h3>

      <p>
        Termos de referência vagos como &ldquo;contratação de serviços de
        desenvolvimento de sistemas&rdquo; sem especificação de tecnologias,
        volumetria, ambiente ou integração criam risco para o contratado. O
        órgão pode demandar qualquer tipo de desenvolvimento, em qualquer
        linguagem, com qualquer nível de complexidade, dentro do preço
        contratado. Antes de participar, verifique se o edital detalha: stack
        tecnológica, estimativa de Pontos de Função ou UST, ambiente de
        produção (on-premises vs cloud), integração com sistemas existentes,
        e níveis de serviço mensuráveis (SLA).
      </p>

      <h3>Métricas de SLA irreais</h3>

      <p>
        Editais que exigem disponibilidade de 99,99% (4,38 minutos de
        downtime por mes) para sistemas que rodam em infraestrutura on-premises
        do próprio órgão são tecnicamente impraticáveis. Da mesma forma,
        SLAs de tempo de resposta de 30 minutos para suporte 24x7 em
        municípios remotos geram custo operacional desproporcional. A
        recomendação e calcular o custo real de atender cada SLA exigido
        antes de formular o preço — SLAs agressivos frequentemente são a
        fonte de prejuízo em contratos de TI.
      </p>

      <h3>Exigência de certificações como barreira</h3>

      <p>
        Editais que exigem certificações de nicho altamente específicas (por
        exemplo, certificação de um único fornecedor para um módulo
        específico) como critério eliminatório de habilitação podem estar
        direcionados para um concorrente específico. A Lei 14.133 permite
        impugnação quando as exigências de habilitação restringem
        indevidamente a competitividade (art. 164). Se a empresa identifica
        que uma exigência de certificação é desproporcional ao objeto,
        pode apresentar impugnação fundamentada até 3 dias úteis antes da
        abertura.
      </p>

      <h3>Lock-in tecnológico não declarado</h3>

      <p>
        Sistemas legados do órgão em tecnologias proprietárias (Oracle Forms,
        SAP ABAP, plataformas low-code específicas) podem exigir
        conhecimento altamente especializado que não está explícito no edital.
        Antes de participar, pesquise o histórico de contratações do órgão
        no PNCP para identificar quais tecnologias estão em uso e se a
        sua equipe tem capacidade de absorver a curva de aprendizado.
      </p>

      {/* Section 8 */}
      <h2>Atas de registro de preço como porta de entrada</h2>

      <p>
        Para empresas que estão iniciando no mercado B2G de TI, as atas de
        registro de preço (ARP) oferecem uma rota de entrada com risco
        controlado.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Vantagens da ARP para empresas de TI
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Volume sem compromisso imediato:</strong> a ARP registra
            preços, mas a demanda é gradual. A empresa não precisa mobilizar
            toda a equipe no dia seguinte ao registro — o órgão faz ordens
            de serviço conforme necessidade.
          </li>
          <li>
            <strong>Múltiplos órgãos com uma licitação:</strong> outros órgãos
            podem aderir à ata (carona), multiplicando o potencial de receita
            sem novo processo licitatório.
          </li>
          <li>
            <strong>Construção de portfólio:</strong> cada ordem de serviço
            executada gera um atestado de capacidade técnica que pode ser
            usado em futuras licitações de maior porte.
          </li>
          <li>
            <strong>Previsibilidade:</strong> preços fixos por 12-24 meses
            permitem planejamento financeiro. O risco é conhecido.
          </li>
          <li>
            <strong>Fato gerador sob demanda:</strong> a empresa só aloca
            recursos quando há ordem de serviço efetiva. Diferente de
            contratos de outsourcing onde a equipe é fixa.
          </li>
        </ul>
      </div>

      <p>
        A estratégia recomendada para empresas em crescimento é: começar por
        ARPs de menor valor em órgãos municipais ou estaduais, construir
        atestados técnicos, e progressivamente disputar contratos de maior
        porte. Um ciclo típico de 18 a 24 meses leva uma empresa de micro
        porte a disputar editais na faixa de R$ 500K a R$ 2M com atestados
        próprios.
      </p>

      {/* Section 9 */}
      <h2>Como analisar viabilidade de um edital de TI</h2>

      <p>
        A{' '}
        <Link href="/blog/analise-viabilidade-editais-guia" className="text-brand-navy dark:text-brand-blue hover:underline">
          análise de viabilidade
        </Link>{' '}
        aplicada ao setor de TI usa os mesmos 4 fatores (modalidade, timeline,
        valor, geografia) com calibração específica para as particularidades
        do setor.
      </p>

      <h3>Fator 1: Modalidade (peso 30%)</h3>

      <p>
        Em TI, o pregão eletrônico é dominante e favorece empresas ágeis em
        lances e documentação. Concorrências por técnica e preço aparecem em
        projetos complexos e favorecem empresas com certificações e acervo
        diferenciado. Inexigibilidade beneficia exclusivamente fabricantes de
        software proprietário. A empresa deve identificar em qual modalidade
        sua taxa de adjudicação histórica é maior.
      </p>

      <h3>Fator 2: Timeline (peso 25%)</h3>

      <p>
        Para pregões eletrônicos de TI, o prazo mínimo é de 8 dias úteis, mas
        propostas técnicas de qualidade exigem 15 a 25 dias. O fator crítico
        em TI é a disponibilidade de equipe: se o edital exige alocação de
        profissionais específicos, a empresa precisa confirmar disponibilidade
        antes de participar. Prometer profissionais alocados em outro contrato
        é fonte comum de inadimplência.
      </p>

      <h3>Fator 3: Valor estimado (peso 25%)</h3>

      <p>
        Valores de referência em editais de TI frequentemente são baseados em
        pesquisas de mercado ou em contratos anteriores. Quando o valor de
        referência está defasado (preço por PF de 3 anos atrás sem reajuste),
        a margem pode ser insuficiente. Verifique se o preço unitário de
        referência é compatível com o custo operacional da sua empresa
        (incluindo encargos, impostos, overhead e margem mínima).
      </p>

      <h3>Fator 4: Geografia (peso 20%)</h3>

      <p>
        Em TI, a geografia tem peso menor que em engenharia, pois muitos
        serviços podem ser executados remotamente. Porém, editais que exigem
        presença física da equipe em Brasília (governo federal) ou no município
        contratante geram custo de deslocamento e alojamento que deve ser
        computado. A pandemia acelerou a aceitação de trabalho remoto no
        governo, mas muitos editais ainda exigem presencialidade parcial
        (3 dias/semana no órgão).
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático — Viabilidade de edital de TI
        </p>
        <p className="text-sm text-ink-secondary mb-3">
          Empresa de software em SP avalia um pregão eletrônico para fábrica
          de software de um tribunal em Brasília, 8.000 PF em 24 meses,
          valor estimado R$ 5,6M, execução híbrida (60% remoto):
        </p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>Modalidade (30%):</strong> Pregão eletrônico, empresa
            tem experiência e agilidade nesta modalidade = 8/10 x 0,30 = 2,40
          </li>
          <li>
            <strong>Timeline (25%):</strong> 15 dias úteis para proposta,
            equipe disponível para alocação = 7/10 x 0,25 = 1,75
          </li>
          <li>
            <strong>Valor (25%):</strong> R$ 700/PF, margem compatível com
            custo operacional da empresa = 8/10 x 0,25 = 2,00
          </li>
          <li>
            <strong>Geografia (20%):</strong> Execução híbrida, 40%
            presencial em Brasília, empresa tem profissionais no DF =
            7/10 x 0,20 = 1,40
          </li>
          <li className="pt-2 font-semibold">
            Pontuação total: 7,55/10 — Viabilidade alta. Recomendado
            prosseguir com análise detalhada do termo de referência.
          </li>
        </ul>
      </div>

      <p>
        Para outros setores que frequentemente se conectam com TI em editais
        multisserviço, consulte os guias de{' '}
        <Link href="/blog/licitacoes-engenharia-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          licitações de engenharia
        </Link>{' '}
        (obras com componente de automação/TI) e{' '}
        <Link href="/blog/licitacoes-saude-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          licitações de saúde
        </Link>{' '}
        (sistemas hospitalares, prontuário eletrônico).
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Monitore editais de TI com inteligência — 14 dias grátis
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic filtra editais de tecnologia por relevância e analisa
          viabilidade automaticamente. Pare de ler editais irrelevantes --
          receba apenas os que fazem sentido para o seu perfil.
        </p>
        <Link
          href="/signup?source=blog&article=licitações-ti-software-2026&utm_source=blog&utm_medium=cta&utm_content=licitações-ti-software-2026&utm_campaign=guias"
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

      <h3>Qual a modalidade mais usada para licitações de TI?</h3>
      <p>
        O{' '}
        <Link href="/glossario#pregao-eletrônico" className="text-brand-navy dark:text-brand-blue hover:underline">
          pregão eletrônico
        </Link>{' '}
        é a modalidade dominante, utilizado em mais de 80% dos editais de TI
        publicados no PNCP. A Lei 14.133/2021 classifica a maioria dos
        serviços de TI como &ldquo;serviços comuns&rdquo; (art. 6o, XIII),
        tornando o pregão obrigatório. Exceções incluem: desenvolvimento de
        software de alta complexidade (concorrência por técnica e preço) e
        software proprietário sem concorrente (inexigibilidade, art. 74, I).
        Para a maioria das empresas de TI, dominar o processo de pregão
        eletrônico é pré-requisito para atuar no mercado B2G.
      </p>

      <h3>Posso participar de licitação de software sendo startup ou MEI?</h3>
      <p>
        Sim. A Lei Complementar 123/2006 garante tratamento diferenciado para
        ME e EPP: empate ficto (até 5% acima do menor preço em pregão), prazo
        adicional para regularização fiscal (5 dias úteis), e licitações
        exclusivas para valores até R$ 80.000. A principal barreira é
        documental: editais de TI frequentemente exigem atestados com
        quantitativos mínimos. A estratégia recomendada para startups é
        começar por dispensas de licitação (até R$ 50.000 para serviços) e
        ARPs de menor porte para construir portfólio de atestados.
      </p>

      <h3>Quais certificações são exigidas em editais de TI?</h3>
      <p>
        As mais frequentes são: ISO 27001 (segurança da informação, ~15% dos
        editais), ISO 9001 (qualidade, ~12%), CMMI nível 2/3 (~8%), e MPS.BR
        (alternativa brasileira ao CMMI). Para profissionais da equipe: PMP
        (gestão de projetos), ITIL (gestão de serviços), certificações cloud
        (AWS, Azure, GCP), e LGPD/DPO. Nem todos os editais exigem todas as
        certificações — a frequência varia por tipo de objeto e órgão
        contratante. ISO 27001 é o investimento com maior retorno, pois
        abre portas para editais de cibersegurança e dados sensíveis.
      </p>

      <h3>O que é prova de conceito (POC) em licitações de software?</h3>
      <p>
        A POC é um procedimento previsto na Lei 14.133 (art. 17, §3o) que
        permite ao órgão verificar se a solução ofertada atende aos requisitos
        técnicos antes da adjudicação. O licitante melhor classificado é
        convocado a demonstrar a solução em ambiente controlado, executando
        casos de teste predefinidos no edital. O prazo típico é de 5 a 15
        dias úteis. A POC é eliminatória: se não aprovada, a empresa é
        desclassificada e o próximo colocado é convocado. Para se preparar,
        mantenha um ambiente de demonstração atualizado e equipe técnica
        disponível para configuração rápida.
      </p>

      <h3>Como funciona o modelo de fábrica de software em licitações?</h3>
      <p>
        O modelo de fábrica de software é a forma predominante de contratação
        de desenvolvimento no governo. O órgão contrata um volume de Pontos
        de Função (PF) ou Unidades de Serviço Técnico (UST) por período e
        demanda entregas conforme necessidade. Valores típicos: R$ 400 a
        R$ 900 por Ponto de Função, dependendo da complexidade e região.
        A métrica segue a metodologia IFPUG/NESMA. Os contratos variam de
        5.000 PF/ano (órgãos menores) a 100.000+ PF/ano (grandes
        ministérios). É fundamental que a empresa domine a contagem de PF,
        pois discrepâncias entre a contagem do órgão e a do contratado são
        a principal fonte de conflitos contratuais.
      </p>

      <h3>Quais UFs publicam mais editais de TI?</h3>
      <p>
        O Distrito Federal (DF) lidera com aproximadamente 25% do valor total
        de editais de TI, devido à concentração de órgãos federais. Em
        seguida: São Paulo (SP) com ~18%, Rio de Janeiro (RJ) com ~12%, e
        Minas Gerais (MG) com ~8%. Para empresas que buscam volume sem se
        deslocar para Brasília, os governos estaduais de SP e RJ oferecem
        oportunidades significativas com execução local. Municípios de grande
        porte (acima de 500 mil habitantes) também publicam editais de TI com
        frequência crescente, especialmente para cidades inteligentes e
        digitalização de serviços públicos.
      </p>
    </>
  );
}
