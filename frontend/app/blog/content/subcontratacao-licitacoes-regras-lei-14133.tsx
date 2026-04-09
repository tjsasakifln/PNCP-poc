import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-07: Subcontratação em licitações: Regras da Lei 14.133
 * Content cluster: contratos públicos
 * Target: ~2,500 words | Primary KW: subcontratação licitações Lei 14.133
 */
export default function SubcontratacaoLicitacoesRegrasLei14133() {
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
                name: 'O que é subcontratação em licitações públicas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Subcontratação em licitações públicas é o instrumento pelo qual o contratado principal (vencedor da licitação) transfere a execução de parcela do objeto contratual a uma terceira empresa, denominada subcontratada. Regulamentada pelo Art. 122 da Lei 14.133/2021, a subcontratação depende de previsão expressa no edital e autorização da Administração. O contratado principal permanece integralmente responsável perante a Administração pela execução do contrato, respondendo solidariamente pelos atos da subcontratada.',
                },
              },
              {
                '@type': 'Question',
                name: 'A subcontratação sempre é permitida em contratos públicos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não. A subcontratação somente é admitida quando expressamente prevista no edital licitatório. Se o edital for omisso ou proibir expressamente a subcontratação, o contratado não pode transferir a execução do objeto a terceiros. O Decreto 11.462/2023 regulamentou hipóteses em que a Administração pode vedar ou restringir a subcontratação a determinadas parcelas do objeto, especialmente quando envolvem expertise técnica que foi determinante para a qualificação da empresa vencedora.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o limite percentual para subcontratação em contratos públicos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 não fixa um percentual máximo único para subcontratação. O limite é definido pelo próprio edital, com base na natureza e complexidade do objeto. Na prática, editais de obras de engenharia costumam admitir subcontratação de até 30% do valor do contrato para itens especializados (instalações elétricas, climatização, fundações especiais). Editais de serviços contínuos geralmente permitem subcontratação de atividades-meio, vedando a de atividades-fim. O contratado nunca pode subcontratar a totalidade do objeto.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais requisitos a subcontratada deve cumprir?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A subcontratada deve satisfazer os requisitos de habilitação jurídica, regularidade fiscal e trabalhista, além das qualificações técnicas exigidas para a parcela que irá executar. A Administração pode exigir que o contratado apresente previamente os documentos de habilitação da subcontratada para aprovação. O contratado é responsável por verificar a regularidade da subcontratada e mantê-la durante toda a vigência do subcontrato, sob pena de rescisão do contrato principal.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como uma PME pode se tornar subcontratada em grandes contratos públicos?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Para se tornar subcontratada, a PME deve: (1) identificar contratos públicos de grande porte no PNCP em setores compatíveis com sua especialidade; (2) mapear as empresas contratadas via Portal da Transparência; (3) apresentar proposta direta ao contratado principal demonstrando capacidade técnica, regularidade fiscal e vantagem de custo; (4) manter regularidade documental (certidões, registros profissionais, atestados de capacidade técnica). O edital deve prever expressamente a possibilidade de subcontratação para que a parceria seja formalizada.',
                },
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        A <strong>subcontratação em licitações públicas</strong> é um instrumento
        estratégico regulamentado pela <strong>Lei 14.133/2021</strong> que permite
        ao contratado principal transferir a execução de parte do objeto a empresas
        especializadas — e que abre uma porta de entrada relevante para PMEs no
        mercado de contratos públicos. Compreender as regras, os limites e os
        requisitos previstos no <strong>Art. 122 da Nova Lei de Licitações</strong>{' '}
        é fundamental tanto para grandes empresas que pretendem subcontratar quanto
        para pequenas e médias que buscam posicionamento estratégico como
        subcontratadas em contratos de alta complexidade e valor.
      </p>

      <p>
        Este guia cobre o marco legal completo, os casos em que a subcontratação
        é admitida ou vedada, as responsabilidades das partes, como identificar
        oportunidades no{' '}
        <Link href="/contratos" className="underline decoration-1 underline-offset-2">
          Portal Nacional de Contratações Públicas (PNCP)
        </Link>{' '}
        e um roteiro prático para PMEs que desejam atuar como subcontratadas.
      </p>

      {/* Section 1 */}
      <h2>Subcontratação, Consórcio e Cessão: diferenças fundamentais</h2>

      <p>
        Antes de analisar as regras da Lei 14.133/2021, é necessário distinguir
        a subcontratação de outros institutos frequentemente confundidos com ela.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Comparativo: subcontratação vs consórcio vs cessão contratual
        </p>
        <ul className="space-y-3 text-sm text-ink-secondary">
          <li>
            <strong>Subcontratação (Art. 122, Lei 14.133/2021):</strong> O
            contratado principal vence a licitação e, após a celebração do
            contrato, contrata terceiro para executar parte do objeto. O
            subcontratado não tem relação jurídica direta com a Administração
            Pública. O contratado original permanece o único responsável perante
            o poder público. Depende de previsão no edital e autorização da
            Administração.
          </li>
          <li>
            <strong>Consórcio (Art. 15, Lei 14.133/2021):</strong> Duas ou mais
            empresas se unem antes da licitação para participar em conjunto.
            Todas as empresas consorciadas têm relação direta com a
            Administração e respondem solidariamente pelo contrato. A formação do
            consórcio deve ser declarada na fase de habilitação. Admitido quando
            o edital expressamente permitir.
          </li>
          <li>
            <strong>Cessão contratual (Art. 137 §1º, Lei 14.133/2021):</strong>{' '}
            O contratado transfere a terceiro a titularidade do contrato, não
            apenas a execução de uma parcela. É vedada pela regra geral — somente
            admitida em casos excepcionalíssimos, mediante autorização formal da
            Administração, e desde que a empresa cessionária cumpra todos os
            requisitos de habilitação exigidos no edital original. Não confundir
            com subcontratação.
          </li>
        </ul>
      </div>

      <p>
        A distinção prática mais relevante é que no consórcio todas as empresas
        estão visíveis para a Administração desde a licitação, enquanto na
        subcontratação a empresa subcontratada surge somente na fase de execução
        contratual, com vínculo jurídico apenas com o contratado principal.
      </p>

      {/* Section 2 */}
      <h2>Base legal: Art. 122 da Lei 14.133/2021</h2>

      <p>
        A Nova Lei de Licitações e Contratos Administrativos dedica o Art. 122 à
        disciplina da subcontratação. Os dispositivos centrais são:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Art. 122 da Lei 14.133/2021 — pontos essenciais
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Caput:</strong> O contratado somente pode subcontratar
            parcelas do objeto quando o edital expressamente admitir a
            subcontratação, até o limite fixado no contrato.
          </li>
          <li>
            <strong>§1º:</strong> O contratado é responsável pela execução do
            contrato perante a Administração, sendo-lhe vedado transferir a
            responsabilidade pela execução das parcelas subcontratadas. A
            responsabilidade solidária do contratado persiste integralmente.
          </li>
          <li>
            <strong>§2º:</strong> A empresa subcontratada deve satisfazer os
            requisitos de habilitação aplicáveis à parcela do objeto para a qual
            foi contratada.
          </li>
          <li>
            <strong>§3º:</strong> É vedada a subcontratação de empresa impedida
            de licitar e contratar com a Administração Pública.
          </li>
          <li>
            <strong>§4º:</strong> A Administração pode exigir a prévia aprovação
            da subcontratada e dos termos do subcontrato, sem que isso implique
            responsabilidade solidária da Administração.
          </li>
        </ul>
      </div>

      <p>
        O Decreto 11.462/2023, que regulamenta aspectos operacionais da Lei
        14.133/2021, reforça que editais de contratos de obras e serviços de
        engenharia devem indicar expressamente as parcelas passíveis de
        subcontratação, vedando-a para o núcleo técnico determinante da
        qualificação da empresa vencedora.
      </p>

      {/* Section 3 */}
      <h2>Quando a subcontratação é permitida</h2>

      <p>
        A subcontratação em contratos públicos regidos pela Lei 14.133/2021 é
        admitida quando cumpridas, cumulativamente, três condições:
      </p>

      <p>
        <strong>1. Previsão expressa no edital.</strong> O instrumento
        convocatório deve indicar se a subcontratação é admitida, para quais
        parcelas do objeto e qual o percentual máximo do valor contratual que
        pode ser subcontratado. Editais omissos vedam implicitamente a
        subcontratação. Licitantes que identificam contratos de alto valor no{' '}
        <Link href="/licitacoes" className="underline decoration-1 underline-offset-2">
          portal de licitações
        </Link>{' '}
        devem sempre verificar a cláusula de subcontratação antes de qualquer
        negociação com potenciais subcontratadas.
      </p>

      <p>
        <strong>2. Autorização prévia da Administração.</strong> Mesmo quando o
        edital admite a subcontratação, o contratado deve obter autorização
        formal do gestor do contrato antes de celebrar qualquer subcontrato. A
        Administração pode exigir apresentação dos documentos de habilitação da
        subcontratada, análise dos termos do subcontrato e, em alguns casos,
        prévia publicação de extrato.
      </p>

      <p>
        <strong>3. Habilitação da subcontratada.</strong> A empresa subcontratada
        deve comprovar todos os requisitos de habilitação jurídica, regularidade
        fiscal, trabalhista e previdenciária, além das qualificações técnicas
        pertinentes à parcela que irá executar. A documentação exigida é
        proporcional ao escopo subcontratado — não é necessário comprovar
        qualificações para parcelas não executadas pela subcontratada.
      </p>

      {/* Inline CTA at ~40% */}
      <BlogInlineCTA slug="subcontratacao-licitacoes-regras-lei-14133" campaign="contratos" />

      {/* Section 4 */}
      <h2>Limites: percentual máximo e vedação à subcontratação total</h2>

      <p>
        A Lei 14.133/2021 não estabelece um percentual máximo único de
        subcontratação aplicável a todos os contratos. O limite é definido caso
        a caso no edital, com base na natureza e na complexidade do objeto.
        Algumas balizas práticas observadas nas contratações públicas:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Limites de subcontratação mais comuns por tipo de objeto
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Obras de engenharia civil:</strong> 25% a 30% do valor
            global, admitindo subcontratação de especialidades como instalações
            elétricas, climatização (HVAC), fundações especiais, estruturas
            metálicas e paisagismo.
          </li>
          <li>
            <strong>Serviços de tecnologia da informação:</strong> Até 30% para
            atividades-meio (suporte, infraestrutura, hospedagem), vedada para
            atividades-fim (desenvolvimento do sistema principal, gestão do
            projeto).
          </li>
          <li>
            <strong>Serviços contínuos (limpeza, vigilância, facilities):</strong>{' '}
            Percentual baixo ou vedação total, dado que a própria Administração
            exige atestados de capacidade técnica compatíveis com o volume
            integral do contrato.
          </li>
          <li>
            <strong>Fornecimento de bens com instalação:</strong> Até 40% para
            o componente de instalação e integração, quando o edital separar
            fornecimento e instalação como parcelas distintas.
          </li>
        </ul>
      </div>

      <p>
        Uma regra que não admite exceção: <strong>é vedada a subcontratação
        integral do objeto</strong>. O contratado deve executar diretamente a
        parte principal do contrato — aquela que determinou sua habilitação
        técnica. O TCU firmou esse entendimento em diversos acórdãos,
        compreendendo a subcontratação total como desvio de finalidade que
        frauda a licitação (Acórdão 1.187/2013-TCU-Plenário).
      </p>

      {/* Section 5 */}
      <h2>Casos em que a subcontratação é vedada</h2>

      <p>
        Além da proibição geral de subcontratar quando o edital não prevê, há
        situações específicas em que a subcontratação é vedada mesmo que o
        edital a admita em tese:
      </p>

      <p>
        <strong>Parcelas determinantes da qualificação.</strong> Se a habilitação
        técnica do contratado foi comprovada por meio de atestados específicos
        de determinado tipo de serviço ou obra, é vedado subcontratar
        exatamente essa parcela. O princípio é lógico: a Administração
        selecionou a empresa em razão de sua capacidade técnica naquele item —
        transferi-lo a terceiro equivale a fraudar a licitação.
      </p>

      <p>
        <strong>Empresa impedida de licitar.</strong> O Art. 122 §3º veda
        expressamente a subcontratação de empresas que estejam suspensas,
        impedidas ou inidôneas para contratar com o poder público. O contratado
        tem o dever de verificar o cadastro do CEIS (Cadastro de Empresas
        Inidôneas e Suspensas) antes de formalizar qualquer subcontrato.
      </p>

      <p>
        <strong>Vedação expressa no edital.</strong> Alguns editais vedam
        integralmente a subcontratação para preservar a qualidade da execução ou
        para assegurar que a empresa vencedora execute pessoalmente o objeto.
        Contratos de consultoria especializada, assessoria jurídica e
        determinados serviços de saúde frequentemente contêm essa vedação.
      </p>

      <p>
        <strong>Conflito de interesse.</strong> A Administração pode negar a
        aprovação de subcontratada quando houver risco de conflito de interesse,
        especialmente em contratos de auditoria, avaliação de ativos públicos ou
        assessoria em processos licitatórios.
      </p>

      {/* Section 6 */}
      <h2>Responsabilidade do contratado principal (Art. 122 §1º)</h2>

      <p>
        O ponto mais crítico da subcontratação em contratos públicos é a
        manutenção integral da responsabilidade do contratado principal. O{' '}
        <strong>Art. 122 §1º da Lei 14.133/2021</strong> é categórico: o
        contratado não pode transferir a responsabilidade pela execução das
        parcelas subcontratadas. Isso significa, na prática:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Consequências práticas da responsabilidade solidária
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Inadimplemento da subcontratada:</strong> Se a subcontratada
            não entregar o serviço ou bem no prazo, o contratado principal
            responde pelos atrasos perante a Administração, inclusive com
            aplicação de multas contratuais.
          </li>
          <li>
            <strong>Vícios de qualidade:</strong> Defeitos na parcela executada
            pela subcontratada são imputáveis ao contratado principal. A
            Administração não aciona a subcontratada diretamente — exige a
            correção do contratado.
          </li>
          <li>
            <strong>Irregularidade fiscal da subcontratada:</strong> Embora o
            contratado deva verificar a regularidade da subcontratada, eventuais
            débitos trabalhistas ou previdenciários desta podem gerar retenção de
            pagamentos ao contratado principal em contratos com solidariedade
            legal (serviços com mão de obra).
          </li>
          <li>
            <strong>Rescisão:</strong> A inadimplência grave da subcontratada
            pode gerar rescisão do contrato principal por culpa do contratado,
            mesmo que este alegue fato de terceiro.
          </li>
        </ul>
      </div>

      <p>
        Por essa razão, a due diligence da subcontratada deve ser rigorosa: a
        empresa que vai subcontratar precisa avaliar a saúde financeira,
        histórico de execução e regularidade documental da subcontratada como
        se estivesse analisando um sócio de risco. O contratado não pode alegar
        desconhecimento dos problemas da subcontratada para se eximir de
        responsabilidade.
      </p>

      {/* Section 7 */}
      <h2>Requisitos para a empresa subcontratada</h2>

      <p>
        A subcontratada deve demonstrar qualificação compatível com a parcela do
        objeto que irá executar. Os documentos habitualmente exigidos pela
        Administração na aprovação de subcontratadas incluem:
      </p>

      <p>
        <strong>Habilitação jurídica:</strong> Contrato social atualizado,
        ato constitutivo com todas as alterações consolidadas, prova de
        inscrição no CNPJ. Empresas individuais e MEIs podem atuar como
        subcontratadas quando a escala e a natureza da parcela forem compatíveis.
      </p>

      <p>
        <strong>Regularidade fiscal e trabalhista:</strong> CND Federal (Receita
        Federal + PGFN), CRF (FGTS), CNDT (débitos trabalhistas), CND
        estadual e municipal quando aplicável. As certidões devem estar válidas
        na data da aprovação e mantidas durante toda a vigência do subcontrato.
      </p>

      <p>
        <strong>Qualificação técnica:</strong> Atestados de capacidade técnica
        emitidos por pessoa jurídica de direito público ou privado, comprovando
        execução anterior de objeto compatível com a parcela subcontratada.
        Para obras de engenharia, Certidão de Acervo Técnico (CAT) do
        responsável técnico emitida pelo CREA ou CAU competente.
      </p>

      <p>
        <strong>Vedação ao CEIS:</strong> Comprovação de que não está impedida,
        suspensa ou declarada inidônea. O contratado deve consultar o portal
        Transparência do Governo Federal e o CEIS antes de submeter a indicação
        à Administração.
      </p>

      {/* Section 8 */}
      <h2>Processo de aprovação e documentação</h2>

      <p>
        O fluxo típico de aprovação de subcontratada em contratos regidos pela
        Lei 14.133/2021 segue as seguintes etapas:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Fluxo de aprovação de subcontratada
        </p>
        <ol className="space-y-2 text-sm text-ink-secondary list-decimal list-inside">
          <li>
            <strong>Solicitação formal:</strong> O contratado encaminha ao gestor
            do contrato ofício indicando a subcontratada, descrevendo a parcela
            a ser subcontratada e o valor correspondente.
          </li>
          <li>
            <strong>Apresentação de documentação:</strong> Habilitação jurídica,
            regularidade fiscal, qualificação técnica e declaração de ausência de
            impedimentos da subcontratada.
          </li>
          <li>
            <strong>Análise pelo gestor:</strong> O gestor do contrato verifica
            a compatibilidade dos documentos, consulta o CEIS e pode solicitar
            documentação complementar. Prazo usual: 5 a 15 dias úteis.
          </li>
          <li>
            <strong>Autorização formal:</strong> Emissão de ofício ou despacho
            autorizando expressamente a subcontratação, com indicação da
            subcontratada aprovada, parcela e percentual.
          </li>
          <li>
            <strong>Formalização do subcontrato:</strong> O contratado celebra o
            subcontrato por escrito. O instrumento deve conter objeto, valor,
            prazo, obrigações de cada parte e cláusula de subordinação ao
            contrato principal.
          </li>
          <li>
            <strong>Comunicação à Administração:</strong> Encaminhamento de
            cópia do subcontrato ao gestor para integrar os autos do processo
            administrativo do contrato principal.
          </li>
        </ol>
      </div>

      {/* Section 9 */}
      <h2>Como identificar contratos abertos à subcontratação no PNCP</h2>

      <p>
        O{' '}
        <Link href="/contratos" className="underline decoration-1 underline-offset-2">
          Portal Nacional de Contratações Públicas (PNCP)
        </Link>{' '}
        publica os contratos celebrados pela Administração Federal, Estadual e
        Municipal. Para identificar contratos com potencial de subcontratação,
        o caminho mais eficiente é:
      </p>

      <p>
        <strong>Consulte contratos de grande porte no setor de interesse.</strong>{' '}
        Contratos de obras de engenharia acima de R$ 5 milhões, serviços de TI
        acima de R$ 3 milhões e contratos de facilities acima de R$ 2 milhões
        habitualmente preveem subcontratação. Por exemplo,{' '}
        <Link
          href="/contratos/engenharia/SP"
          className="underline decoration-1 underline-offset-2"
        >
          contratos de engenharia em São Paulo
        </Link>{' '}
        publicados no PNCP são um ponto de partida relevante para PMEs do setor.
      </p>

      <p>
        <strong>Leia o edital, não apenas o extrato do contrato.</strong> A
        permissão de subcontratação está no edital que originou o contrato, não
        no extrato publicado no PNCP. Acesse o processo licitatório vinculado ao
        contrato e localize a cláusula de subcontratação no edital original ou
        no termo de referência.
      </p>

      <p>
        <strong>Mapeie os contratados atuais.</strong> Identifique quais empresas
        detêm contratos de alto valor no seu setor. Essas são as potenciais
        tomadoras de subcontratação. Você pode encontrar{' '}
        <Link
          href="/fornecedores/engenharia/SP"
          className="underline decoration-1 underline-offset-2"
        >
          fornecedores e contratados de engenharia em SP
        </Link>{' '}
        como referência para mapear players do mercado.
      </p>

      <p>
        <strong>Monitore aditivos de prazo e valor.</strong> Contratos com
        aditivos de prazo recorrentes indicam projetos de longa duração — maior
        janela de tempo para negociar subcontratação de parcelas específicas
        com o contratado.
      </p>

      {/* Section 10 */}
      <h2>Guia prático para PMEs: como se tornar subcontratada</h2>

      <p>
        Para pequenas e médias empresas especializadas, a subcontratação é um
        caminho de entrada em contratos públicos de alto valor sem a necessidade
        de atender a todos os requisitos de habilitação do contrato principal.
        O roteiro a seguir organiza as etapas de posicionamento:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Roteiro para PMEs interessadas em subcontratação
        </p>
        <ol className="space-y-3 text-sm text-ink-secondary list-decimal list-inside">
          <li>
            <strong>Defina sua parcela de especialidade.</strong> Identifique com
            precisão quais serviços ou fornecimentos sua empresa executa com
            diferencial técnico e competitividade de custo. A especialização é
            o argumento central para o contratado principal te escolher como
            subcontratada em vez de executar internamente.
          </li>
          <li>
            <strong>Mantenha documentação sempre atualizada.</strong> Certidões
            vencidas são o maior obstáculo para aprovação rápida como
            subcontratada. Mantenha CND Federal, CRF, CNDT e certidões estaduais
            válidas. A Administração não aprova subcontratadas com irregularidades,
            independentemente da qualidade técnica.
          </li>
          <li>
            <strong>Construa atestados de capacidade técnica.</strong> Todo
            serviço prestado para pessoa jurídica de direito público é um atestado
            em potencial. Solicite atestados sistematicamente após a conclusão de
            cada projeto, mesmo que de pequeno porte. Para engenharia, providencie
            a CAT no CREA logo após a conclusão de cada obra.
          </li>
          <li>
            <strong>Mapeie os grandes contratados do setor.</strong> Identifique
            as 10 a 20 empresas que detêm os maiores contratos públicos no seu
            setor e UF de atuação. Essas são suas potenciais clientes como
            subcontratada. Consulte o{' '}
            <Link
              href="/blog/contratos/engenharia"
              className="underline decoration-1 underline-offset-2"
            >
              panorama de contratos de engenharia
            </Link>{' '}
            para referência setorial.
          </li>
          <li>
            <strong>Aborde diretamente com proposta técnica.</strong> Prepare um
            portfólio de subcontratação: apresentação da empresa, lista de
            atestados relevantes, capacidade instalada, referências, e uma
            proposta preliminar de custo para a parcela de especialidade.
            A abordagem direta ao gestor de contratos ou ao sócio técnico da
            empresa contratada é mais efetiva do que qualquer intermediário.
          </li>
          <li>
            <strong>Monitore licitações em andamento.</strong> Acompanhe editais
            de alto valor no seu setor pelo PNCP antes da adjudicação. Empresas
            finalistas precisam de subcontratadas para as parcelas especializadas
            — é o momento certo para negociar. Uma plataforma de monitoramento
            de licitações agiliza esse processo consideravelmente.
          </li>
        </ol>
      </div>

      <p>
        Uma vantagem importante para as empresas enquadradas como ME ou EPP: a
        Lei Complementar 123/2006, aplicável em conjunto com a Lei 14.133/2021,
        permite que editais exijam do contratado principal a subcontratação de
        percentual mínimo do objeto a ME e EPP. Quando esse dispositivo é
        aplicado, o edital cria uma reserva de mercado para pequenos negócios
        dentro do contrato, tornando a subcontratação uma exigência, não
        apenas uma possibilidade.
      </p>

      {/* Section 11 */}
      <h2>Subcontratação obrigatória de ME e EPP (LC 123/2006)</h2>

      <p>
        O Art. 48 da Lei Complementar 123/2006 autoriza a Administração a exigir
        do contratado principal a subcontratação de parcelas do objeto a
        microempresas e empresas de pequeno porte, desde que o edital preveja
        essa exigência e defina o percentual mínimo de subcontratação a ME/EPP.
      </p>

      <p>
        Para se qualificar à subcontratação obrigatória de ME/EPP, a empresa
        deve comprovar seu enquadramento como microempresa ou EPP mediante
        declaração firmada pelo contador responsável, além dos documentos de
        habilitação pertinentes à parcela. O contratado principal que não cumprir
        a exigência de subcontratação a ME/EPP incorre em inadimplemento
        contratual, sujeito às sanções previstas no contrato.
      </p>

      {/* Section 12 */}
      <h2>Jurisprudência do TCU sobre subcontratação</h2>

      <p>
        O Tribunal de Contas da União consolidou ao longo dos anos entendimentos
        relevantes sobre a subcontratação em contratos públicos:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Acórdãos TCU relevantes sobre subcontratação
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Acórdão 1.187/2013-TCU-Plenário:</strong> Firmou que a
            subcontratação total do objeto é vedada, mesmo quando o edital admite
            subcontratação sem fixar limite percentual. A omissão do edital não
            autoriza a transferência integral da execução.
          </li>
          <li>
            <strong>Acórdão 2.172/2019-TCU-Plenário:</strong> Reiterou que o
            contratado não pode se eximir de responsabilidade alegando falha da
            subcontratada. A responsabilidade é objetiva e integral perante a
            Administração.
          </li>
          <li>
            <strong>Acórdão 741/2016-TCU-Segunda Câmara:</strong> Determinou que
            a Administração verifique ativamente a habilitação da subcontratada,
            não se limitando à declaração do contratado. A aprovação formal da
            subcontratada implica dever de diligência por parte do gestor do
            contrato.
          </li>
          <li>
            <strong>Acórdão 3.005/2022-TCU-Plenário:</strong> Interpretou que,
            mesmo após a Lei 14.133/2021, os princípios consolidados na
            jurisprudência anterior sobre subcontratação permanecem aplicáveis
            como parâmetro de controle.
          </li>
        </ul>
      </div>

      <p>
        A jurisprudência do TCU reforça que a subcontratação é um instrumento
        legítimo e útil, mas que exige gestão rigorosa tanto do contratado
        principal quanto do fiscal do contrato. Irregularidades na subcontratação
        resultam em determinações de ressarcimento ao erário e aplicação de
        sanções às partes envolvidas.
      </p>

      {/* Section 13: FAQ */}
      <h2>Perguntas frequentes sobre subcontratação em licitações</h2>

      <h3>
        O que é subcontratação em licitações públicas?
      </h3>
      <p>
        Subcontratação em licitações públicas é o instrumento pelo qual o
        contratado principal (vencedor da licitação) transfere a execução de
        parcela do objeto contratual a uma terceira empresa, denominada
        subcontratada. Regulamentada pelo Art. 122 da Lei 14.133/2021, a
        subcontratação depende de previsão expressa no edital e autorização da
        Administração. O contratado principal permanece integralmente responsável
        perante a Administração pela execução do contrato, respondendo
        solidariamente pelos atos da subcontratada.
      </p>

      <h3>
        A subcontratação sempre é permitida em contratos públicos?
      </h3>
      <p>
        Não. A subcontratação somente é admitida quando expressamente prevista
        no edital licitatório. Se o edital for omisso ou proibir a
        subcontratação, o contratado não pode transferir a execução do objeto a
        terceiros. O Decreto 11.462/2023 regulamentou hipóteses em que a
        Administração pode vedar ou restringir a subcontratação a determinadas
        parcelas do objeto, especialmente quando envolvem expertise técnica que
        foi determinante para a qualificação da empresa vencedora.
      </p>

      <h3>
        Qual o limite percentual para subcontratação em contratos públicos?
      </h3>
      <p>
        A Lei 14.133/2021 não fixa um percentual máximo único. O limite é
        definido pelo edital, com base na natureza e complexidade do objeto.
        Editais de obras de engenharia costumam admitir subcontratação de até
        30% do valor do contrato para itens especializados. O contratado nunca
        pode subcontratar a totalidade do objeto — isso é vedado de forma
        absoluta, conforme jurisprudência consolidada do TCU.
      </p>

      <h3>
        Quais requisitos a subcontratada deve cumprir?
      </h3>
      <p>
        A subcontratada deve satisfazer os requisitos de habilitação jurídica,
        regularidade fiscal e trabalhista, além das qualificações técnicas
        exigidas para a parcela que irá executar. A Administração pode exigir
        que o contratado apresente previamente os documentos de habilitação da
        subcontratada para aprovação. O contratado é responsável por verificar
        a regularidade da subcontratada e mantê-la durante toda a vigência do
        subcontrato, sob pena de rescisão do contrato principal.
      </p>

      <h3>
        Como uma PME pode se tornar subcontratada em grandes contratos públicos?
      </h3>
      <p>
        Para se tornar subcontratada, a PME deve identificar contratos públicos
        de grande porte no PNCP em setores compatíveis com sua especialidade,
        mapear as empresas contratadas, apresentar proposta direta ao contratado
        principal demonstrando capacidade técnica e regularidade documental.
        O edital deve prever expressamente a possibilidade de subcontratação.
        Monitorar{' '}
        <Link href="/licitacoes" className="underline decoration-1 underline-offset-2">
          licitações em andamento
        </Link>{' '}
        de alto valor é fundamental para abordar potenciais tomadores antes da
        adjudicação.
      </p>

      {/* Sources */}
      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-2">Fontes e referências</p>
        <ul className="space-y-1 text-xs text-ink-secondary">
          <li>Lei 14.133/2021 — Nova Lei de Licitações e Contratos Administrativos (Art. 122)</li>
          <li>Decreto 11.462/2023 — Regulamentação de aspectos da Lei 14.133/2021</li>
          <li>Lei Complementar 123/2006 — Estatuto Nacional da Microempresa e da EPP (Art. 48)</li>
          <li>TCU — Acórdão 1.187/2013-Plenário (vedação à subcontratação total)</li>
          <li>TCU — Acórdão 2.172/2019-Plenário (responsabilidade do contratado)</li>
          <li>TCU — Acórdão 741/2016-Segunda Câmara (diligência na aprovação de subcontratadas)</li>
          <li>TCU — Acórdão 3.005/2022-Plenário (aplicação dos princípios à Nova Lei)</li>
          <li>
            PNCP — Portal Nacional de Contratações Públicas:{' '}
            <span className="font-mono">pncp.gov.br</span>
          </li>
        </ul>
      </div>
    </>
  );
}
