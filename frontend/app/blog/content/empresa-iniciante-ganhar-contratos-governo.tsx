import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-09: Como uma empresa iniciante pode ganhar contratos com o governo
 * Content cluster: contratos públicos
 * Target: ~3,000 words | Primary KW: empresa iniciante contratos governo
 */
export default function EmpresaInicianteGanharContratosGoverno() {
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
                name: 'Uma empresa recém-aberta pode participar de licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. A legislação brasileira não exige tempo mínimo de existência para participar de licitações. O que se exige é regularidade fiscal e trabalhista: CNPJ ativo, certidão negativa de débitos federais (CND), FGTS regularizado, certidão de regularidade estadual e municipal, e inexistência de falência decretada. Empresas com CNPJ aberto há menos de 30 dias já podem participar de pregões eletrônicos, desde que atendam à documentação de habilitação. Para dispensa de licitação (compras até R$ 50 mil em bens ou R$ 100 mil em serviços), o processo é ainda mais simples.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais são as vantagens de ME e EPP em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei Complementar 123/2006 (Estatuto da ME/EPP) garante quatro vantagens principais para microempresas e empresas de pequeno porte em licitações públicas: (1) tratamento diferenciado em certidões com irregularidade fiscal — a empresa tem prazo de 5 dias úteis para regularizar antes de ser desclassificada; (2) direito de preferência — se uma ME/EPP ofertar preço até 5% superior ao menor lance de empresa grande, pode apresentar nova proposta e vencer; (3) licitações exclusivas — compras até R$ 80 mil são obrigatoriamente reservadas para ME/EPP; (4) subcontratação obrigatória — em alguns contratos, grandes empresas devem subcontratar ME/EPP para partes do objeto.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é SICAF e como se cadastrar?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O SICAF (Sistema de Cadastramento Unificado de Fornecedores) é o cadastro eletrônico do governo federal para fornecedores que querem vender para órgãos federais. O cadastro é feito no Portal de Compras do Governo Federal (compras.gov.br) e exige: CNPJ ativo na Receita Federal, certificados de regularidade fiscal (federal, estadual, municipal), regularidade junto ao FGTS e à Justiça do Trabalho, e os dados bancários da empresa. O SICAF é gratuito e obrigatório para participar de pregões eletrônicos de órgãos federais. Estados e municípios têm cadastros próprios (CRC — Certificado de Registro Cadastral).',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é dispensa de licitação e como funciona para iniciantes?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Dispensa de licitação é a contratação direta pelo governo, sem processo licitatório formal, para valores abaixo dos limites estabelecidos na Lei 14.133/2021: até R$ 50.000 para compra de bens e serviços de engenharia comuns, e até R$ 100.000 para outros serviços. Para empresas iniciantes, a dispensa é o caminho mais acessível: o processo é mais simples, o prazo de avaliação é menor e exige menos documentação. Desde abril de 2021, dispensas acima de R$ 10.000 devem ser publicadas no Portal de Compras do Governo ou sistemas equivalentes, o que aumenta a transparência e a possibilidade de empresas novas serem cotadas.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quanto tempo leva para uma empresa iniciante fechar o primeiro contrato com o governo?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O tempo varia conforme a estratégia. Por dispensa de licitação, o ciclo pode ser de 2 a 4 semanas: a empresa recebe a cotação, apresenta proposta e, se aceita, assina o contrato. Por pregão eletrônico, o ciclo típico é de 30 a 60 dias entre a abertura do edital e a assinatura do contrato. Para uma empresa iniciante sem experiência prévia, o recomendado é começar por dispensas e contratos de menor valor, construindo os primeiros atestados de capacidade técnica antes de disputar pregões mais complexos. Com estratégia clara e documentação em ordem, é possível fechar o primeiro contrato em até 60 dias após o cadastro no SICAF.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph — primary keyword */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Vender para o governo sendo uma <strong>empresa iniciante</strong> parece,
        à primeira vista, território exclusivo de grandes corporações com
        histórico consolidado, equipe jurídica e relacionamento com órgãos
        públicos. Essa percepção está errada — e entender por que ela está
        errada é o primeiro passo para construir uma trajetória real de{' '}
        <strong>contratos com o governo</strong>.
      </p>

      <p>
        O mercado público brasileiro movimentou mais de R$ 198 bilhões em
        compras e contratações em 2024, segundo o Portal Nacional de
        Contratações Públicas (PNCP). Uma fração relevante desse volume
        vai para pequenas empresas — e a legislação brasileira cria
        vantagens estruturais para microempresas e empresas de pequeno
        porte que precisam ser aproveitadas de forma estratégica.
      </p>

      <p>
        Este artigo é um roteiro prático: desde os pré-requisitos legais
        até o primeiro pregão eletrônico, passando pelos erros mais
        comuns de iniciantes e por como construir uma trajetória de receita
        recorrente com o setor público.
      </p>

      <h2>Mitos e realidades sobre vender para o governo</h2>

      <p>
        Antes de entrar no passo a passo, vale desmistificar algumas
        crenças que afastam empresas iniciantes do mercado público.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Mitos frequentes sobre licitações para iniciantes</p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li>
            <strong>Mito 1: &ldquo;Só empresa grande ganha licitação.&rdquo;</strong>{' '}
            Realidade: a Lei Complementar 123/2006 reserva compras de até R$ 80 mil
            exclusivamente para ME e EPP. Além disso, o critério de julgamento em
            pregões é o menor preço — não o tamanho da empresa.
          </li>
          <li>
            <strong>Mito 2: &ldquo;Preciso de relacionamento com servidores.&rdquo;</strong>{' '}
            Realidade: pregões eletrônicos são processos anônimos e objetivos. A
            proposta vence pelo preço, não pelo relacionamento. O envolvimento pessoal
            antes da adjudicação pode inclusive configurar irregularidade.
          </li>
          <li>
            <strong>Mito 3: &ldquo;O processo é burocrático demais.&rdquo;</strong>{' '}
            Realidade: a Lei 14.133/2021 simplificou procedimentos e criou a dispensa
            eletrônica para valores menores. O registro no SICAF é feito online, sem
            visitas presenciais, e certidões são obtidas digitalmente.
          </li>
          <li>
            <strong>Mito 4: &ldquo;Licitação paga devagar.&rdquo;</strong>{' '}
            Realidade: o governo federal tem prazo de 30 dias para pagamento após
            liquidação da despesa (Lei 9.430/1996 e LC 123/2006 para ME/EPP). Muitos
            órgãos pagam antes. O risco de inadimplência é estruturalmente menor do
            que no mercado privado.
          </li>
          <li>
            <strong>Mito 5: &ldquo;Preciso de advogado para participar.&rdquo;</strong>{' '}
            Realidade: pregões eletrônicos não exigem representação jurídica. O
            próprio sócio-administrador pode cadastrar a empresa, enviar propostas e
            assinar contratos. Assessoria jurídica é útil para contratos complexos,
            mas não obrigatória no início.
          </li>
        </ul>
      </div>

      <p>
        Com esses mitos afastados, o caminho fica mais claro. O mercado
        público é acessível para empresas iniciantes — desde que a
        abordagem seja estruturada e os pré-requisitos estejam em ordem.
      </p>

      <h2>Pré-requisitos: o que sua empresa precisa ter</h2>

      <p>
        A participação em licitações exige documentação de habilitação.
        Não é complexa, mas precisa estar rigorosamente regularizada.
        Um único documento vencido elimina a empresa do processo,
        independentemente do preço ofertado.
      </p>

      <p>
        Os documentos exigidos na maioria dos pregões e processos de
        compra pública são:
      </p>

      <ul>
        <li>
          <strong>CNPJ ativo</strong> na Receita Federal, sem inconsistências
          cadastrais
        </li>
        <li>
          <strong>Certidão Negativa de Débitos Federais (CND)</strong> ou
          Certidão Positiva com Efeitos de Negativa — emitida pela Receita
          Federal e pela PGFN, conjuntamente
        </li>
        <li>
          <strong>Regularidade junto ao FGTS</strong> — Certificado de
          Regularidade do FGTS (CRF), emitido pela Caixa Econômica Federal
        </li>
        <li>
          <strong>Certidão Negativa de Débitos Trabalhistas (CNDT)</strong> —
          emitida pelo Tribunal Superior do Trabalho, gratuita e obtida online
        </li>
        <li>
          <strong>Certidão Estadual</strong> — regularidade com a Fazenda do
          estado onde a empresa é domiciliada
        </li>
        <li>
          <strong>Certidão Municipal</strong> — regularidade com o município
          sede da empresa
        </li>
        <li>
          <strong>Contrato Social ou Requerimento de Empresário</strong> —
          para comprovação da constituição e dos poderes dos representantes
        </li>
      </ul>

      <p>
        Para MEI, o processo é ainda mais simplificado: o CCMEI
        (Certificado da Condição de Microempreendedor Individual) substitui
        o contrato social, e as certidões são as mesmas. MEIs podem
        participar de dispensas de licitação e, com algumas limitações,
        de pregões para objetos compatíveis com o CNAE registrado.
      </p>

      <h2>Passo 1: cadastro nos sistemas do governo</h2>

      <p>
        O primeiro registro necessário é no SICAF — Sistema de
        Cadastramento Unificado de Fornecedores, administrado pela
        Secretaria de Gestão do Ministério da Gestão e da Inovação.
        O SICAF habilita a empresa a participar de pregões eletrônicos
        de órgãos do governo federal.
      </p>

      <p>
        O cadastro no SICAF é feito no Portal de Compras Governamentais
        (compras.gov.br) e é gratuito. O processo exige certificado
        digital (e-CNPJ ou procuração eletrônica) e as certidões
        listadas acima. Uma vez cadastrado, o SICAF precisa ser mantido
        atualizado — certidões vencidas suspendem automaticamente o
        cadastro e impedem participação em novos processos.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Prazos de validade das certidões — referência rápida</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>&bull; <strong>CND Federal (Receita + PGFN):</strong> 180 dias</li>
          <li>&bull; <strong>CRF/FGTS:</strong> 30 dias</li>
          <li>&bull; <strong>CNDT (Trabalhista):</strong> 180 dias</li>
          <li>&bull; <strong>Certidão Estadual:</strong> varia por estado (60 a 180 dias)</li>
          <li>&bull; <strong>Certidão Municipal:</strong> varia por município (60 a 180 dias)</li>
        </ul>
        <p className="text-xs text-ink-secondary mt-3">
          Recomendação: monitore as datas de vencimento em planilha e renove com pelo menos
          15 dias de antecedência. Uma certidão vencida no dia do pregão elimina a empresa.
          Fonte: Instrução Normativa SEGES/ME n.º 3/2018 e legislação correlata.
        </p>
      </div>

      <p>
        Para órgãos estaduais e municipais, o cadastro varia. Muitos
        estados têm seu próprio CRC (Certificado de Registro Cadastral),
        obtido junto à Secretaria da Fazenda ou à central de compras do
        estado. Municípios de médio e grande porte também têm portais
        próprios. O{' '}
        <Link href="/licitacoes" className="text-brand-navy dark:text-brand-blue hover:underline">
          portal de licitações do SmartLic
        </Link>{' '}
        agrega oportunidades de múltiplas esferas — federal, estadual e
        municipal — o que facilita identificar em quais sistemas é
        prioritário cadastrar-se primeiro.
      </p>

      <h2>Passo 2: entenda seu mercado dentro do setor público</h2>

      <p>
        Não existe &ldquo;o governo&rdquo; como um comprador único.
        Existem mais de 5.000 órgãos contratantes no Brasil —
        ministérios, autarquias, fundações, secretarias estaduais,
        prefeituras, câmaras, hospitais públicos, universidades federais,
        tribunais. Cada um tem perfil de compra, sazonalidade e objetos
        frequentes distintos.
      </p>

      <p>
        A estratégia de uma empresa iniciante deve começar com a
        identificação dos órgãos que compram o que ela vende. Esse
        mapeamento pode ser feito analisando o histórico de contratos
        públicos disponível no PNCP e no Portal da Transparência:
        quais órgãos contrataram produtos ou serviços similares nos
        últimos 12 meses, em quais valores e com qual frequência.
      </p>

      <p>
        Para esse mapeamento, ferramentas como o{' '}
        <Link href="/contratos" className="text-brand-navy dark:text-brand-blue hover:underline">
          hub de contratos publicos
        </Link>{' '}
        e a visualização de{' '}
        <Link href="/fornecedores/ti/SP" className="text-brand-navy dark:text-brand-blue hover:underline">
          fornecedores por setor e estado
        </Link>{' '}
        ajudam a identificar quem são os players do seu segmento,
        quais contratos foram adjudicados e em que faixa de valor.
        Você pode até analisar o perfil de um concorrente específico
        pelo CNPJ, como neste{' '}
        <Link href="/cnpj/33000167000101" className="text-brand-navy dark:text-brand-blue hover:underline">
          exemplo de consulta de CNPJ
        </Link>.
      </p>

      <p>
        Com esse diagnóstico inicial, defina um nicho de atuação:
        dois ou três segmentos de órgãos onde sua empresa tem vantagem
        competitiva real (capacidade técnica, localização, preço ou
        especialização). Tentar atender a todos os segmentos ao mesmo
        tempo dilui esforço e dificulta a construção de um histórico coerente.
      </p>

      <h2>Passo 3: comece pequeno — dispensa de licitação</h2>

      <p>
        O caminho mais acessível para o primeiro contrato público é a
        <strong> dispensa de licitação</strong> — contratação direta sem
        processo licitatório formal, prevista nos artigos 75 e 76 da
        Lei 14.133/2021 para valores menores.
      </p>

      <p>
        Os limites vigentes para dispensa são:
      </p>

      <ul>
        <li>
          Até <strong>R$ 50.000</strong> para obras e serviços de engenharia
          comuns e para compra de bens
        </li>
        <li>
          Até <strong>R$ 100.000</strong> para outros serviços (consultoria,
          tecnologia, limpeza, vigilância, logística, entre outros)
        </li>
      </ul>

      <p>
        Na prática, isso significa que uma empresa que presta serviços
        de TI, consultoria, treinamento, design, comunicação ou qualquer
        outro serviço intelectual pode ser contratada diretamente por
        um órgão por até R$ 100.000 sem necessidade de disputa pública.
        Para bens e insumos de valor baixo — equipamentos, materiais de
        escritório, mobiliário — o limite é de R$ 50.000 por contratação.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Como órgãos realizam dispensas na prática</p>
        <p className="text-sm text-ink-secondary mb-2">
          Desde a Instrução Normativa SEGES n.º 67/2021, dispensas de valor acima de
          R$ 10.000 no âmbito federal devem ser publicadas no Sistema de Dispensa Eletrônica
          (SDE), parte do Portal de Compras do Governo. O processo funciona assim:
        </p>
        <ol className="space-y-1.5 text-sm text-ink-secondary list-decimal list-inside">
          <li>O órgão publica a cotação no SDE com descrição do objeto e prazo de resposta (mínimo 3 dias úteis).</li>
          <li>Fornecedores cadastrados no SICAF recebem aviso e enviam propostas pela plataforma.</li>
          <li>O órgão seleciona a proposta mais vantajosa e notifica o vencedor.</li>
          <li>Assinatura do contrato ou emissão de nota de empenho — muitas vezes em menos de 10 dias.</li>
        </ol>
        <p className="text-xs text-ink-secondary mt-3">
          Fonte: Instrução Normativa SEGES/ME n.º 67/2021 e Lei 14.133/2021, art. 75.
        </p>
      </div>

      <p>
        A dispensa de licitação é o laboratório ideal para o iniciante:
        ciclo curto, documentação mais simples, menor risco de ser
        eliminado por formalidades processuais. O primeiro atestado de
        capacidade técnica — documento fundamental para contratos maiores
        — costuma vir de uma dispensa bem executada.
      </p>

      <BlogInlineCTA slug="empresa-iniciante-ganhar-contratos-governo" campaign="contratos" />

      <h2>Passo 4: aproveite as vantagens de ME, EPP e MEI</h2>

      <p>
        A Lei Complementar 123/2006 — Estatuto da ME e EPP — cria um
        regime diferenciado para microempresas (receita bruta anual até
        R$ 360 mil), empresas de pequeno porte (receita até R$ 4,8 milhões)
        e MEIs (receita até R$ 81 mil). Esse regime diferenciado é uma
        vantagem competitiva real que deve ser conhecida e explorada.
      </p>

      <p>
        As principais vantagens em licitações são:
      </p>

      <h3>Licitações exclusivas para ME e EPP</h3>

      <p>
        Compras de valor estimado até R$ 80.000 devem ser realizadas
        exclusivamente com ME e EPP, salvo quando não houver fornecedores
        no segmento ou houver restrição de competitividade. Isso significa
        que uma parte relevante do mercado público está legalmente
        reservada para empresas pequenas — e empresas grandes não podem
        competir nessas licitações.
      </p>

      <h3>Direito de preferência (empate ficto)</h3>

      <p>
        Em licitações abertas a todas as empresas, se uma ME ou EPP
        oferecer proposta com valor até 5% superior ao menor lance de
        uma empresa de grande porte, ela tem o direito de apresentar
        nova proposta com preço igual ou inferior ao da empresa grande.
        Se a ME/EPP aceitar esse empate, ela vence a licitação mesmo
        tendo ofertado preço maior no lance original.
      </p>

      <h3>Regularização fiscal diferenciada</h3>

      <p>
        ME e EPP com irregularidade fiscal têm prazo de 5 dias úteis
        (prorrogáveis por mais 5 dias em casos justificados) para
        regularizar a pendência e apresentar certidão válida antes de
        serem desclassificadas. Para empresas grandes, a certidão
        inválida no momento da habilitação é causa de eliminação imediata.
      </p>

      <h3>Subcontratação obrigatória</h3>

      <p>
        Em contratos de maior vulto com empresas de grande porte, o
        edital pode exigir que parte do objeto seja subcontratada a
        ME ou EPP. Isso abre oportunidades para empresas iniciantes
        funcionarem como subcontratadas antes de disputar contratos
        diretos — e acumularem histórico e atestados no processo.
      </p>

      <h2>Passo 5: o primeiro pregão eletrônico — guia prático</h2>

      <p>
        O <strong>pregão eletrônico</strong> é a modalidade mais utilizada
        em licitações públicas: responde por mais de 70% dos processos
        licitatórios no Brasil. É conduzido pela internet, com lances em
        tempo real, e a disputa é anônima até a fase de habilitação.
        Para empresas iniciantes, o pregão é o principal canal de acesso
        ao mercado público depois da dispensa.
      </p>

      <p>
        O fluxo básico de um pregão eletrônico é:
      </p>

      <ol>
        <li>
          <strong>Publicação do edital</strong> — O órgão publica o edital
          no PNCP e na plataforma de pregão (normalmente o Portal de Compras
          do Governo, para esfera federal). O edital define o objeto, os
          critérios de habilitação, as datas e as regras do processo.
        </li>
        <li>
          <strong>Leitura do edital</strong> — Passo mais importante e mais
          subestimado. Leia o edital completo, incluindo o termo de referência,
          a planilha de composição de preços (quando houver) e os anexos de
          habilitação. Identifique exigências específicas de capacidade técnica,
          certidões complementares ou amostras.
        </li>
        <li>
          <strong>Impugnação (se necessário)</strong> — Se o edital contiver
          cláusulas restritivas ou ilegais, qualquer interessado pode impugnar
          antes da abertura da sessão. Para iniciantes, a impugnação é raramente
          necessária, mas é um direito legal.
        </li>
        <li>
          <strong>Cadastro de proposta</strong> — Antes da sessão, a empresa
          envia sua proposta com o valor ofertado na plataforma. A proposta
          fica sigilosa até a abertura da fase de lances.
        </li>
        <li>
          <strong>Sessão de lances</strong> — Na data e hora marcadas, o
          sistema abre a fase de lances. As empresas veem apenas sua posição
          (colocação) e o menor lance atual, sem saber quem são os concorrentes.
          Os lances são em tempo real, e o pregoeiro pode encerrar a sessão a
          qualquer momento após o prazo mínimo.
        </li>
        <li>
          <strong>Negociação</strong> — O pregoeiro pode convocar o vencedor
          provisório para negociar redução adicional antes da habilitação.
        </li>
        <li>
          <strong>Habilitação</strong> — O vencedor provisório envia os documentos
          de habilitação. Se algum documento estiver vencido ou ausente, a empresa
          é desclassificada e o segundo colocado é convocado.
        </li>
        <li>
          <strong>Adjudicação e homologação</strong> — O pregoeiro adjudica
          o objeto ao vencedor. A autoridade competente homologa o resultado.
          O contrato pode ser assinado.
        </li>
      </ol>

      <p>
        Para identificar pregões adequados ao perfil de uma empresa
        iniciante — sem exigências de capacidade técnica muito restritivas,
        com valores compatíveis e modalidades acessíveis — a{' '}
        <Link href="/blog/contratos/saude" className="text-brand-navy dark:text-brand-blue hover:underline">
          análise setorial de contratos públicos
        </Link>{' '}
        e o histórico de licitações em estados específicos, como os{' '}
        <Link href="/contratos/saude/SP" className="text-brand-navy dark:text-brand-blue hover:underline">
          contratos de saúde em São Paulo
        </Link>,
        oferecem uma base concreta para a prospecção.
      </p>

      <h2>Passo 6: construa seu histórico — atestados de capacidade técnica</h2>

      <p>
        O atestado de capacidade técnica é o documento que comprova que
        a empresa já prestou serviço ou forneceu bem equivalente ao objeto
        licitado. Em licitações de maior complexidade, o edital exige que
        a empresa apresente um ou mais atestados compatíveis com a natureza
        e o volume do objeto.
      </p>

      <p>
        Para uma empresa sem histórico, essa exigência pode parecer um
        círculo vicioso: para ganhar um contrato, é preciso ter atestado,
        mas para ter atestado, é preciso ter ganhado um contrato. Existem
        três formas de romper esse ciclo:
      </p>

      <h3>1. Começar por dispensas e contratos menores</h3>

      <p>
        Dispensas de licitação e pregões de menor valor costumam não exigir
        atestados ou exigem atestados de volume muito menor. O primeiro
        contrato — mesmo que pequeno — gera o primeiro atestado. Guarde
        todos os termos de recebimento, notas de empenho e declarações
        de satisfação do órgão: esses documentos são a base do seu
        portfólio.
      </p>

      <h3>2. Subcontratação por empresas maiores</h3>

      <p>
        Atuar como subcontratada de uma empresa maior em um contrato público
        gera atestado da empresa contratante principal (não do governo
        diretamente, mas equivalente para muitos editais). É uma forma de
        acumular experiência e histórico sem disputar licitações diretamente.
      </p>

      <h3>3. Qualificação técnica dos sócios</h3>

      <p>
        Em contratos de natureza técnica (engenharia, TI, saúde, arquitetura),
        muitos editais aceitam a comprovação de capacidade técnica por
        meio de certidões e atestados dos responsáveis técnicos da empresa
        — os sócios ou funcionários com formação na área — mesmo que sejam
        de experiência anterior ao CNPJ atual.
      </p>

      <h2>Erros comuns de empresas iniciantes em licitações</h2>

      <p>
        A maioria dos insucessos de empresas iniciantes em licitações não
        vem de preço inadequado ou produto inferior — vem de erros
        processuais que poderiam ter sido evitados com preparação básica.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Os 6 erros mais frequentes de empresas iniciantes</p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li>
            <strong>1. Certidão vencida na habilitação.</strong> O erro mais comum e o mais
            evitável. A CRF/FGTS tem validade de 30 dias — emita na véspera do pregão. Crie
            um calendário de renovação de certidões com alertas automáticos.
          </li>
          <li>
            <strong>2. Proposta sem composição de custos.</strong> Muitos editais exigem que
            o fornecedor apresente planilha de composição de preços, especialmente em contratos
            de serviços contínuos. Proposta sem a planilha é desclassificada por vício formal.
          </li>
          <li>
            <strong>3. Não ler o edital completo.</strong> Especificações no termo de referência
            que a empresa não consegue atender, prazos de entrega impossíveis ou exigências de
            capacidade técnica incompatíveis com o porte da empresa são detectáveis só com
            leitura cuidadosa do edital — antes de investir tempo na proposta.
          </li>
          <li>
            <strong>4. Preço abaixo do custo.</strong> A pressão por ganhar o primeiro contrato
            leva muitas empresas a propor preços insustentáveis. Um contrato com margem negativa
            gera inadimplência, quebra de contrato e sanções — o oposto de construir reputação.
          </li>
          <li>
            <strong>5. Perder o prazo de recurso.</strong> Em pregões eletrônicos, o prazo para
            interpor recurso após a fase de lances é de 3 dias úteis. Se a empresa for
            indevidamente desclassificada e não recorrer no prazo, perde o direito.
          </li>
          <li>
            <strong>6. Não monitorar editais sistematicamente.</strong> A maior parte das
            oportunidades passa despercebida porque a empresa só busca quando lembra. Um
            sistema de monitoramento contínuo — manual ou com ferramenta dedicada — é o
            que separa empresas que acumulam contratos das que ficam no primeiro.
          </li>
        </ul>
      </div>

      <h2>Como o SmartLic ajuda empresas iniciantes a encontrar as oportunidades certas</h2>

      <p>
        Uma das maiores dificuldades de empresas iniciantes não é disputar
        licitações — é saber quais disputar. O mercado público publica
        dezenas de milhares de editais por mês. Sem uma forma estruturada
        de filtrar e classificar essas oportunidades, a empresa perde tempo
        analisando editais incompatíveis e deixa passar os que seriam
        ideais.
      </p>

      <p>
        O SmartLic foi desenvolvido para resolver exatamente esse problema.
        A plataforma agrega licitações do PNCP, Portal de Compras Públicas
        e ComprasGov em uma busca consolidada, classifica as oportunidades
        por setor com IA e aplica análise de viabilidade em quatro fatores:
        modalidade, prazo, valor estimado e localização. Para uma empresa
        iniciante, isso significa receber um conjunto curado de oportunidades
        compatíveis com seu perfil — não uma lista bruta de centenas de
        editais para triagem manual.
      </p>

      <p>
        Além da busca inteligente, o SmartLic oferece um{' '}
        <strong>pipeline de oportunidades</strong> — um kanban onde é
        possível organizar os editais em estágios (identificado, analisando,
        proposta enviada, adjudicado) e acompanhar o funil de contratos
        em tempo real. Para uma empresa construindo seus primeiros contratos,
        essa visibilidade do processo é fundamental para não perder prazos
        e priorizar o esforço comercial.
      </p>

      <p>
        Veja como funciona o ecossistema de contratos públicos que o
        SmartLic monitora:
      </p>

      <ul>
        <li>
          <Link href="/contratos" className="text-brand-navy dark:text-brand-blue hover:underline">
            Hub de contratos públicos
          </Link>{' '}
          — visão consolidada do mercado por órgão, setor e modalidade
        </li>
        <li>
          <Link href="/licitacoes" className="text-brand-navy dark:text-brand-blue hover:underline">
            Licitações ativas
          </Link>{' '}
          — editais em aberto classificados por setor e viabilidade
        </li>
        <li>
          <Link href="/fornecedores/ti/SP" className="text-brand-navy dark:text-brand-blue hover:underline">
            Fornecedores por setor
          </Link>{' '}
          — quem já vende para o governo no seu segmento e em que valores
        </li>
      </ul>

      <h2>Trajetória de crescimento: do primeiro contrato à receita recorrente</h2>

      <p>
        A trajetória típica de uma empresa que constrói presença sólida
        no mercado público segue fases previsíveis. Entender essa trajetória
        ajuda a calibrar expectativas e a planejar o crescimento de forma
        realista.
      </p>

      <h3>Fase 1 (meses 1-6): primeiros atestados</h3>

      <p>
        Foco em dispensas de licitação e pregões de menor valor, com
        objetos simples e sem exigência de atestados. O objetivo não
        é maximizar a margem do contrato — é executar com excelência
        e obter declarações de satisfação e atestados dos órgãos.
        Nessa fase, o ticket médio tende a ser menor, mas o aprendizado
        operacional é o ativo mais valioso.
      </p>

      <h3>Fase 2 (meses 6-18): primeira ata de registro de preços</h3>

      <p>
        Com dois ou três atestados na carteira, a empresa passa a
        qualificar para pregões maiores. Uma ata de registro de preços
        — modalidade em que o órgão registra o preço da empresa e pode
        contratar dela ao longo de 12 meses sem novo processo licitatório
        — é o primeiro passo para receita recorrente. Uma ata bem
        gerenciada pode representar múltiplos pedidos do mesmo órgão
        durante sua vigência.
      </p>

      <h3>Fase 3 (a partir do mês 18): contrato de prestação contínua</h3>

      <p>
        Contratos de serviços contínuos — limpeza, vigilância, TI,
        manutenção, saúde, logística — têm prazo de 12 meses renováveis
        por até 5 anos (ou 10 anos em alguns casos, pela Lei 14.133/2021).
        Uma empresa com dois ou três contratos de serviços contínuos tem
        receita previsível, base para crescimento da equipe e portfólio
        para disputar contratos ainda maiores.
      </p>

      <p>
        A cada fase, o portfólio de atestados cresce, o relacionamento
        com os órgãos se consolida e a empresa aprende a otimizar preços
        e processos. O mercado público não é uma corrida de velocidade
        — é uma corrida de resistência. As empresas que chegam à Fase 3
        raramente saem do mercado público: a previsibilidade de receita
        e o volume de oportunidades são difíceis de replicar no privado.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">Referências legais e institucionais</p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            &bull; <strong>Lei 14.133/2021</strong> — Nova Lei de Licitações e Contratos
            Administrativos. Define modalidades, limites para dispensa, habilitação e sanções.
            Disponível em <strong>planalto.gov.br</strong>.
          </li>
          <li>
            &bull; <strong>Lei Complementar 123/2006</strong> — Estatuto da ME e EPP. Define
            o tratamento diferenciado em licitações, limites de exclusividade e direito de
            preferência. Disponível em <strong>planalto.gov.br</strong>.
          </li>
          <li>
            &bull; <strong>SICAF</strong> — Sistema de Cadastramento Unificado de Fornecedores.
            Cadastro obrigatório para pregões federais. Acesso em <strong>compras.gov.br</strong>.
          </li>
          <li>
            &bull; <strong>PNCP</strong> — Portal Nacional de Contratações Públicas. Repositório
            oficial de editais e contratos públicos. Acesso em <strong>pncp.gov.br</strong>.
          </li>
          <li>
            &bull; <strong>Sebrae</strong> — Guias e capacitações para ME e EPP em licitações,
            incluindo cursos gratuitos sobre pregão eletrônico. Acesso em <strong>sebrae.com.br</strong>.
          </li>
          <li>
            &bull; <strong>SmartLic</strong> — Plataforma de inteligência em licitações:
            busca multi-fonte, classificação setorial por IA e análise de viabilidade.
            Acesso em <strong>smartlic.tech</strong>.
          </li>
        </ul>
      </div>

      {/* CTA Section — BEFORE FAQ */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Encontre as oportunidades certas para o perfil da sua empresa
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic classifica licitações por setor, viabilidade e modalidade — e
          filtra as que fazem sentido para o porte e a capacidade da sua empresa.
          Sem garimpar manualmente centenas de editais.
        </p>
        <Link
          href="/signup?source=blog&article=empresa-iniciante-ganhar-contratos-governo&utm_source=blog&utm_medium=cta&utm_content=empresa-iniciante-ganhar-contratos-governo&utm_campaign=contratos"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito.{' '}
          Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">página de recursos</Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Uma empresa recém-aberta pode participar de licitações?</h3>
      <p>
        Sim. A legislação brasileira não exige tempo mínimo de existência
        para participar de licitações. O que se exige é regularidade fiscal
        e trabalhista: CNPJ ativo, certidão negativa de débitos federais
        (CND), FGTS regularizado, certidão de regularidade estadual e
        municipal, e inexistência de falência decretada. Empresas com CNPJ
        aberto há menos de 30 dias já podem participar de pregões eletrônicos,
        desde que atendam à documentação de habilitação. Para dispensa de
        licitação (compras até R$ 50 mil em bens ou R$ 100 mil em serviços),
        o processo é ainda mais simples.
      </p>

      <h3>Quais são as vantagens de ME e EPP em licitações?</h3>
      <p>
        A Lei Complementar 123/2006 (Estatuto da ME/EPP) garante quatro
        vantagens principais para microempresas e empresas de pequeno porte
        em licitações públicas: (1) tratamento diferenciado em certidões com
        irregularidade fiscal — a empresa tem prazo de 5 dias úteis para
        regularizar antes de ser desclassificada; (2) direito de preferência
        — se uma ME/EPP ofertar preço até 5% superior ao menor lance de
        empresa grande, pode apresentar nova proposta e vencer; (3) licitações
        exclusivas — compras até R$ 80 mil são obrigatoriamente reservadas
        para ME/EPP; (4) subcontratação obrigatória — em alguns contratos,
        grandes empresas devem subcontratar ME/EPP para partes do objeto.
      </p>

      <h3>O que é SICAF e como se cadastrar?</h3>
      <p>
        O SICAF (Sistema de Cadastramento Unificado de Fornecedores) é o
        cadastro eletrônico do governo federal para fornecedores que querem
        vender para órgãos federais. O cadastro é feito no Portal de Compras
        do Governo Federal (compras.gov.br) e é gratuito. O SICAF é
        obrigatório para participar de pregões eletrônicos de órgãos federais.
        Estados e municípios têm cadastros próprios (CRC — Certificado de
        Registro Cadastral).
      </p>

      <h3>O que é dispensa de licitação e como funciona para iniciantes?</h3>
      <p>
        Dispensa de licitação é a contratação direta pelo governo, sem
        processo licitatório formal, para valores abaixo dos limites
        estabelecidos na Lei 14.133/2021: até R$ 50.000 para compra de bens
        e serviços de engenharia comuns, e até R$ 100.000 para outros
        serviços. Para empresas iniciantes, a dispensa é o caminho mais
        acessível: o processo é mais simples, o prazo de avaliação é menor
        e exige menos documentação. Desde abril de 2021, dispensas acima de
        R$ 10.000 devem ser publicadas no Portal de Compras do Governo ou
        sistemas equivalentes.
      </p>

      <h3>Quanto tempo leva para uma empresa iniciante fechar o primeiro contrato com o governo?</h3>
      <p>
        O tempo varia conforme a estratégia. Por dispensa de licitação,
        o ciclo pode ser de 2 a 4 semanas: a empresa recebe a cotação,
        apresenta proposta e, se aceita, assina o contrato. Por pregão
        eletrônico, o ciclo típico é de 30 a 60 dias entre a abertura do
        edital e a assinatura do contrato. Para uma empresa iniciante sem
        experiência prévia, o recomendado é começar por dispensas e
        contratos de menor valor, construindo os primeiros atestados de
        capacidade técnica antes de disputar pregões mais complexos. Com
        estratégia clara e documentação em ordem, é possível fechar o
        primeiro contrato em até 60 dias após o cadastro no SICAF.
      </p>
    </>
  );
}
