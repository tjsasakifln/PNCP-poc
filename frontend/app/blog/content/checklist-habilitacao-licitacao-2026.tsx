import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * Checklist Completo de Habilitação para Licitação em 2026 (Lei 14.133)
 *
 * Target: ~3000 words | Cluster: guias transversais
 * Primary keyword: checklist habilitação licitação
 */
export default function ChecklistHabilitacaoLicitacao2026() {
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
                name: 'Com quanto tempo de antecedência devo começar a reunir a documentação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O ideal é iniciar a coleta de documentos pelo menos 15 dias antes da data de abertura das propostas. Certidões como a CND Federal (Receita + PGFN), o CRF do FGTS e a Certidão Negativa de Débitos Trabalhistas têm validade de 6 meses, então podem ser obtidas com antecedência. Documentos societários como o contrato social consolidado e procurações devem ser verificados com prazo suficiente para eventuais autenticações ou reconhecimentos de firma quando exigidos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Documentos digitais têm validade em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O art. 12, §1º da Lei 14.133/2021 reconhece documentos digitais assinados com certificado digital padrão ICP-Brasil como plenamente válidos, dispensando autenticação em cartório. Para pregões eletrônicos, todos os documentos são enviados digitalmente. A assinatura com certificado digital e-CNPJ ou e-CPF substitui reconhecimento de firma. Apenas editais de determinados órgãos estaduais e municipais ainda exigem apresentação física — verifique sempre o edital específico.',
                },
              },
              {
                '@type': 'Question',
                name: 'A documentação pode ser da matriz quando a participante é uma filial?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Em regra, as certidões devem corresponder ao CNPJ efetivamente participante. Se a licitante for uma filial (CNPJ com sufixo diferente de 0001), as certidões fiscais e trabalhistas precisam ser da filial, salvo quando o edital expressamente aceitar certidões da matriz ou quando a regularidade é consolidada (ex.: CND Federal que já consolida todas as inscrições do mesmo CNPJ raiz). A qualificação técnica e econômico-financeira, em geral, pode ser apresentada em nome da matriz. Confirme sempre no edital.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual a validade das certidões mais comuns exigidas em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'CND Federal (Receita Federal + PGFN): 6 meses. CRF do FGTS: 30 dias (renovação automática para empresas em dia). CNDT (Certidão Negativa de Débitos Trabalhistas): 180 dias. Certidão Negativa de Débitos Estaduais (ICMS): varia por estado, geralmente 6 meses. Certidão Negativa de Débitos Municipais (ISS): varia por município, geralmente 6 meses. Certidão Negativa de Falência e Recuperação Judicial: geralmente 90 dias, mas o edital pode especificar prazo diferente.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é o SICAF e como ele simplifica a habilitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O SICAF (Sistema de Cadastramento Unificado de Fornecedores) é o cadastro federal de fornecedores do governo. Empresas cadastradas e com linha completa habilitada não precisam apresentar fisicamente os documentos de habilitação jurídica, regularidade fiscal e qualificação econômica nas licitações federais — basta o pregoeiro consultar o sistema durante a sessão. O SICAF é organizado em níveis: Nível I (credenciamento básico), Nível II (habilitação jurídica), Nível III (regularidade fiscal e trabalhista), Nível IV (qualificação técnica) e Nível V (qualificação econômica). Manter o SICAF atualizado é uma das melhores práticas para reduzir o risco de desclassificação.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Aproximadamente <strong>40% das desclassificações em licitações públicas</strong> ocorrem
        na fase de habilitação — não por falta de competitividade do preço, mas por erros
        documentais que poderiam ter sido evitados. Uma certidão vencida, um documento assinado
        por quem não tem poderes, ou a ausência de uma declaração obrigatória são suficientes para
        eliminar uma empresa de um pregão que ela já havia tecnicamente vencido. Com a{' '}
        <Link href="/blog/lei-14133-guia-fornecedores">Lei 14.133/2021</Link> em plena vigência,
        os requisitos de habilitação foram reorganizados e ampliados. Este checklist cobre tudo
        que você precisa apresentar, organizado por tipo, com prazos de validade e os erros mais
        comuns em cada categoria.
      </p>

      <h2>O que mudou na habilitação com a Lei 14.133/2021</h2>
      <p>
        A Lei 14.133/2021 consolidou e modernizou as regras de habilitação, antes espalhadas pela
        Lei 8.666/1993 e pela Lei 10.520/2002. Os artigos 62 a 70 disciplinam os cinco tipos de
        habilitação que podem ser exigidos, individualmente ou em conjunto, conforme o objeto
        contratado. A principal mudança prática é que a lei passou a permitir que o edital exija{' '}
        <strong>somente os documentos estritamente necessários</strong> ao objeto (art. 62,
        §1º) — vedando exigências desnecessárias ou desproporcionais. Isso, na teoria, reduziria
        a burocracia. Na prática, os editais ainda tendem a exigir o conjunto completo, e a empresa
        precisa estar preparada.
      </p>
      <p>
        Outra mudança relevante é a <strong>habilitação após a proposta</strong>: no pregão
        eletrônico regido pela nova lei, o julgamento das propostas precede a habilitação. Ou seja,
        somente o licitante que apresentar a melhor proposta tem sua documentação verificada. Isso
        reduz o volume de documentos analisados, mas exige que a empresa já tenha tudo pronto no
        momento da sessão — pois o prazo para apresentação é curto.
      </p>

      <h2>Tipo 1 — Habilitação Jurídica (art. 66)</h2>
      <p>
        A habilitação jurídica comprova a existência legal da empresa e a legitimidade de seus
        representantes para contratar. É a base de qualquer processo: sem ela, nenhum outro
        documento tem validade.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Documentos de Habilitação Jurídica</h3>
        <ul className="space-y-2 text-sm">
          <li>• <strong>Contrato Social consolidado</strong> (ou estatuto, para S.A.) com última alteração que abranja a composição societária atual</li>
          <li>• <strong>CNPJ ativo</strong> — comprovante de inscrição e situação cadastral emitido pela Receita Federal (situação "Ativa")</li>
          <li>• <strong>Procuração</strong> ou ato societário que comprove os poderes do representante (quando o signatário não é sócio/administrador)</li>
          <li>• <strong>Documento de identidade</strong> do representante legal (RG, CNH ou outro documento oficial com foto)</li>
          <li>• <strong>Ato constitutivo registrado</strong> na Junta Comercial, Cartório de Registro de Pessoas Jurídicas ou órgão competente</li>
          <li>• Para MEI: <strong>Certificado de Condição de Microempreendedor Individual</strong> (CCMEI)</li>
        </ul>
      </div>

      <p>
        Atenção especial ao contrato social: ele deve estar <strong>consolidado</strong>, ou seja,
        conter todas as alterações em um único documento. Apresentar o contrato original com
        aditivos separados aumenta o risco de o pregoeiro não conseguir verificar os dados
        corretos. Se sua empresa passou por mudança societária nos últimos dois anos e ainda não
        consolidou o contrato, faça isso antes de participar de qualquer licitação de valor
        relevante.
      </p>

      <h2>Tipo 2 — Regularidade Fiscal e Trabalhista (art. 68)</h2>
      <p>
        Este é o conjunto de certidões que mais causa problemas, por uma razão simples: elas
        vencem. Uma empresa pode estar perfeitamente regular fiscalmente mas ter uma certidão
        emitida há seis meses e um dia — e isso é suficiente para desclassificação. O art. 68
        lista as certidões obrigatórias nas licitações federais; editais estaduais e municipais
        podem acrescentar certidões específicas.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Certidões de Regularidade — Prazos de Validade</h3>
        <ul className="space-y-2 text-sm">
          <li>• <strong>CND Federal</strong> (Certidão Conjunta RFB + PGFN) — <em>validade: 6 meses</em> — emitida em receita.fazenda.gov.br</li>
          <li>• <strong>CRF do FGTS</strong> (Certificado de Regularidade do FGTS) — <em>validade: 30 dias</em> — emitido em consulta-crf.caixa.gov.br</li>
          <li>• <strong>CNDT</strong> (Certidão Negativa de Débitos Trabalhistas) — <em>validade: 180 dias</em> — emitida em tst.jus.br</li>
          <li>• <strong>Certidão Estadual (ICMS)</strong> — validade varia por estado (geralmente 6 meses) — emitida na Secretaria de Fazenda do estado sede da empresa</li>
          <li>• <strong>Certidão Municipal (ISS/tributos municipais)</strong> — validade varia por município — emitida na prefeitura do município sede</li>
          <li>• <strong>Certidão de Regularidade Previdenciária (INSS)</strong> — coberta pela CND Federal desde 2014, não é documento separado</li>
        </ul>
      </div>

      <p>
        O CRF do FGTS merece atenção especial: sua validade é de apenas 30 dias, e empresas que
        têm empregados celetistas precisam garantir que os depósitos do FGTS estejam em dia.
        Empresas sem empregados (como MEI puro ou sociedades com apenas sócios) podem obter o
        CRF facilmente via portal da Caixa, mas é importante verificar a situação regularmente.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">⚠ Atenção: Regularidade Fiscal em Licitações de ME/EPP</p>
        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
          Microempresas e empresas de pequeno porte têm o benefício da regularização fiscal tardia
          (art. 4º, §1º da Lei 14.133 c/c art. 43 da LC 123/2006): mesmo com certidões com
          restrições, a ME/EPP pode ser declarada vencedora, tendo <strong>5 dias úteis
          prorrogáveis por mais 5</strong> para regularizar a situação. Se a regularização não
          ocorrer no prazo, a habilitação é revogada e convoca-se o segundo colocado.
        </p>
      </div>

      <h2>Tipo 3 — Qualificação Técnica (art. 67)</h2>
      <p>
        A qualificação técnica demonstra que a empresa tem capacidade operacional para executar o
        objeto contratado. É o tipo de habilitação com maior variação entre editais — cada objeto
        tem sua especificidade — e também onde ocorre o maior número de impugnações por parte dos
        concorrentes, já que as exigências podem ser questionadas se forem restritivas demais.
      </p>
      <p>
        Os documentos mais comuns de qualificação técnica são:
      </p>
      <ul>
        <li>
          <strong>Atestados de Capacidade Técnica (ACT)</strong> — emitidos por pessoas jurídicas
          de direito público ou privado, comprovando que a empresa executou objeto similar ao
          licitado. O art. 67, I da Lei 14.133 permite exigir atestados de até 50% da quantidade
          licitada (vedada a exigência de 100% como era comum na lei anterior).
        </li>
        <li>
          <strong>Certidão de Acervo Técnico (CAT)</strong> — emitida pelo CREA, CAU ou CFA,
          comprova que um profissional da empresa (ou vinculado a ela) executou obra ou serviço
          de engenharia específico. Exigível apenas em contratos de obras e serviços de engenharia.
        </li>
        <li>
          <strong>Registro em Conselho Profissional</strong> — CRC (contabilidade), CRA
          (administração), OAB (advocacia), CRM (medicina), conforme o objeto do contrato.
        </li>
        <li>
          <strong>Comprovação de aparelhamento</strong> — alguns editais exigem prova de que a
          empresa dispõe de equipamentos e instalações adequados (ex.: câmaras frias para
          fornecimento de alimentos, veículos para logística).
        </li>
        <li>
          <strong>Visita técnica</strong> — permitida pelo art. 67, VI, apenas quando a
          complexidade do objeto justificar. O edital deve prever prazo mínimo de 3 dias úteis
          antes da abertura para realização da visita.
        </li>
      </ul>

      <p>
        Quer entender como montar um dossiê de qualificação técnica para um edital específico?
        Veja nosso guia sobre{' '}
        <Link href="/blog/como-participar-primeira-licitacao-2026">
          como participar da primeira licitação
        </Link>{' '}
        e o artigo sobre{' '}
        <Link href="/blog/erros-desclassificam-propostas-licitacao">
          erros que desclassificam propostas
        </Link>
        .
      </p>

      <BlogInlineCTA slug="checklist-habilitacao-licitacao-2026" campaign="guias" />

      <h2>Tipo 4 — Qualificação Econômico-Financeira (art. 69)</h2>
      <p>
        A qualificação econômico-financeira verifica se a empresa tem saúde financeira suficiente
        para suportar a execução do contrato. Contratos de alto valor que demandam investimento
        inicial relevante (obras, fornecimento de grandes volumes, contratos de longa duração)
        costumam ter exigências mais rigorosas nesta fase.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Documentos de Qualificação Econômico-Financeira</h3>
        <ul className="space-y-2 text-sm">
          <li>• <strong>Balanço Patrimonial</strong> — do último exercício social, devidamente registrado na Junta Comercial ou publicado (para S.A.). Deve demonstrar índices de Liquidez Geral (LG), Liquidez Corrente (LC) e Solvência Geral (SG) conforme limites do edital</li>
          <li>• <strong>Demonstrativo de resultado</strong> — geralmente DRE do último exercício, quando exigido</li>
          <li>• <strong>Certidão Negativa de Falência, Recuperação Judicial e Extrajudicial</strong> — emitida pelo distribuidor da comarca da sede da empresa, validade geralmente de 90 dias</li>
          <li>• <strong>Capital Social mínimo ou Patrimônio Líquido mínimo</strong> — o edital pode exigir capital mínimo de até 10% do valor estimado do contrato (art. 69, §2º)</li>
          <li>• <strong>Garantia de proposta</strong> — em casos excepcionais previstos no edital, de até 1% do valor estimado (art. 58)</li>
        </ul>
      </div>

      <p>
        Empresas abertas há menos de um ano apresentam o balanço de abertura. Microempresas e
        EPPs optantes pelo Simples Nacional que adotam escrituração simplificada devem verificar
        com seu contador se o balanço produzido é suficiente para atender às exigências do edital.
        Alguns editais aceitam declaração de contador substituindo o balanço para contratos de
        baixo valor.
      </p>
      <p>
        Os índices financeiros mais comuns são calculados assim: <strong>Liquidez Geral</strong>{' '}
        = (AC + RLP) / (PC + PNC); <strong>Liquidez Corrente</strong> = AC / PC;{' '}
        <strong>Solvência Geral</strong> = AT / (PC + PNC). O edital deve especificar o índice
        mínimo aceitável (geralmente 1,00 ou superior).
      </p>

      <h2>Tipo 5 — Declarações Obrigatórias</h2>
      <p>
        Além dos documentos principais, os editais exigem declarações assinadas pelo representante
        legal da empresa. São autodeclarações — o licitante assume responsabilidade pela veracidade
        das informações, sujeito às penas previstas nos arts. 155 a 163 da Lei 14.133 em caso de
        falsidade. Na prática do pregão eletrônico, essas declarações são marcadas no sistema
        (ComprasNet, BEC etc.) durante o credenciamento, mas o edital pode exigir documentos
        separados.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Declarações Habitualmente Exigidas</h3>
        <ul className="space-y-2 text-sm">
          <li>• <strong>Declaração de inexistência de fato impeditivo</strong> — não estar suspenso ou impedido de licitar com o ente licitante (art. 155, III)</li>
          <li>• <strong>Declaração de cumprimento da Constituição Federal, art. 7º, XXXIII</strong> — não emprega menor de 16 anos (exceto aprendiz de 14 a 16) nem menor em trabalho noturno, perigoso ou insalubre</li>
          <li>• <strong>Declaração de enquadramento como ME/EPP</strong> — quando for solicitar os benefícios da LC 123/2006 (obrigatória para exercer preferências)</li>
          <li>• <strong>Declaração de elaboração independente de proposta</strong> — ausência de combinação prévia com outros licitantes (prevenção de cartel)</li>
          <li>• <strong>Declaração de cumprimento dos requisitos de habilitação</strong> — especialmente no pregão eletrônico, onde a habilitação é verificada após o lance</li>
          <li>• <strong>Declaração de sustentabilidade</strong> — quando o edital exige práticas sustentáveis (em contratos de obras, TI e serviços de copa/limpeza)</li>
        </ul>
      </div>

      <h2>Checklist Completo — Todos os Documentos por Categoria</h2>
      <p>
        Use a tabela abaixo como referência rápida antes de cada licitação. Marque cada item
        conforme for obtendo os documentos. Lembre-se de verificar sempre o edital específico,
        pois os requisitos variam por objeto e por ente licitante.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-4">Checklist Habilitação — Lei 14.133/2021</h3>

        <div className="mb-4">
          <p className="text-sm font-semibold text-ink-secondary uppercase tracking-wide mb-2">Habilitação Jurídica (art. 66)</p>
          <ul className="space-y-1 text-sm">
            <li>☐ Contrato social consolidado (ou estatuto + ata de eleição de diretores para S.A.)</li>
            <li>☐ Comprovante de inscrição no CNPJ — situação "Ativa"</li>
            <li>☐ Procuração ou ato societário (quando representante não é sócio/administrador)</li>
            <li>☐ Documento de identidade do representante legal</li>
            <li>☐ CCMEI (para MEI)</li>
          </ul>
        </div>

        <div className="mb-4">
          <p className="text-sm font-semibold text-ink-secondary uppercase tracking-wide mb-2">Regularidade Fiscal e Trabalhista (art. 68)</p>
          <ul className="space-y-1 text-sm">
            <li>☐ CND Federal conjunta RFB + PGFN (validade 6 meses)</li>
            <li>☐ CRF do FGTS (validade 30 dias)</li>
            <li>☐ CNDT — Certidão Negativa de Débitos Trabalhistas (validade 180 dias)</li>
            <li>☐ Certidão de regularidade estadual (ICMS) do estado sede</li>
            <li>☐ Certidão de regularidade municipal (ISS) do município sede</li>
          </ul>
        </div>

        <div className="mb-4">
          <p className="text-sm font-semibold text-ink-secondary uppercase tracking-wide mb-2">Qualificação Técnica (art. 67) — verificar edital</p>
          <ul className="space-y-1 text-sm">
            <li>☐ Atestado(s) de Capacidade Técnica (ACT) de pessoa jurídica</li>
            <li>☐ Certidão de Acervo Técnico (CAT) do CREA/CAU — obras e engenharia</li>
            <li>☐ Registro em conselho profissional (CRC, CRA, OAB etc.)</li>
            <li>☐ Declaração de aparelhamento técnico (equipamentos/instalações)</li>
            <li>☐ Comprovante de visita técnica (quando exigida pelo edital)</li>
          </ul>
        </div>

        <div className="mb-4">
          <p className="text-sm font-semibold text-ink-secondary uppercase tracking-wide mb-2">Qualificação Econômico-Financeira (art. 69)</p>
          <ul className="space-y-1 text-sm">
            <li>☐ Balanço Patrimonial do último exercício social (registrado na Junta Comercial)</li>
            <li>☐ Certidão Negativa de Falência e Recuperação Judicial (validade conforme edital)</li>
            <li>☐ Demonstrativo de índices de liquidez (quando exigido pelo edital)</li>
            <li>☐ Comprovante de capital social mínimo (quando exigido)</li>
          </ul>
        </div>

        <div>
          <p className="text-sm font-semibold text-ink-secondary uppercase tracking-wide mb-2">Declarações Obrigatórias</p>
          <ul className="space-y-1 text-sm">
            <li>☐ Declaração de inexistência de fato impeditivo</li>
            <li>☐ Declaração de não emprego de menor (CF art. 7º, XXXIII)</li>
            <li>☐ Declaração de ME/EPP (quando aplicável)</li>
            <li>☐ Declaração de elaboração independente de proposta</li>
            <li>☐ Declaração de cumprimento dos requisitos de habilitação</li>
            <li>☐ Declaração de sustentabilidade (quando exigida)</li>
          </ul>
        </div>
      </div>

      <h2>Armadilhas Comuns que Causam Desclassificação</h2>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">⚠ Os Erros Mais Frequentes na Fase de Habilitação</p>
        <ul className="text-sm text-amber-700 dark:text-amber-300 mt-2 space-y-2">
          <li>• <strong>Certidão vencida:</strong> Verificar validade de cada documento no dia da sessão, não apenas na data de obtenção</li>
          <li>• <strong>CNPJ errado:</strong> Conferir se o CNPJ na certidão corresponde ao CNPJ participante (matriz vs. filial)</li>
          <li>• <strong>Documento sem assinatura ou sem reconhecimento:</strong> Ler o edital para saber se exige assinatura manuscrita, digital ou reconhecimento de firma</li>
          <li>• <strong>Contrato social desatualizado:</strong> Sócio que saiu ainda aparece no documento — risco de impugnação</li>
          <li>• <strong>Atestado técnico sem dados suficientes:</strong> O ACT deve conter: objeto executado, quantidade, período de execução, dados do contratante e do responsável técnico</li>
          <li>• <strong>Balanço não registrado:</strong> Balanço sem carimbo da Junta Comercial não é aceito (exceto para optantes pelo Simples com escrituração simplificada)</li>
          <li>• <strong>Procuração vencida:</strong> Verificar prazo de validade da procuração quando utilizada</li>
        </ul>
      </div>

      <p>
        Para evitar esses erros de forma sistemática, recomendamos criar uma pasta digital
        organizada por tipo de documento, com a data de validade de cada certidão registrada.
        Atualize esse arquivo a cada licitação e configure alertas com 30 dias de antecedência
        para as certidões de validade mais curta (especialmente o CRF do FGTS, com 30 dias).
      </p>

      <h2>Como o SICAF Simplifica a Habilitação</h2>
      <p>
        Para licitações federais, o{' '}
        <Link href="/blog/sicaf-como-cadastrar-manter-ativo-2026">
          SICAF (Sistema de Cadastramento Unificado de Fornecedores)
        </Link>{' '}
        é o caminho mais eficiente para reduzir o trabalho documental. Empresas com SICAF ativo e
        linha de habilitação completa não precisam apresentar fisicamente os documentos de
        habilitação jurídica, regularidade fiscal e qualificação econômica nas licitações federais
        — o pregoeiro consulta o sistema em tempo real durante a sessão.
      </p>
      <p>
        O SICAF é organizado em cinco níveis de habilitação:
      </p>
      <ul>
        <li><strong>Nível I — Credenciamento:</strong> dados básicos de cadastro da empresa</li>
        <li><strong>Nível II — Habilitação Jurídica:</strong> ato constitutivo, CNPJ, representação legal</li>
        <li><strong>Nível III — Regularidade Fiscal e Trabalhista:</strong> certidões (CND, FGTS, CNDT, estadual, municipal)</li>
        <li><strong>Nível IV — Qualificação Técnica:</strong> atestados e registros profissionais</li>
        <li><strong>Nível V — Qualificação Econômico-Financeira:</strong> balanço e índices financeiros</li>
      </ul>
      <p>
        Mesmo com o SICAF ativo, a empresa deve manter as certidões atualizadas no sistema. O
        SICAF não renova documentos automaticamente — a empresa é responsável por fazer o upload
        das novas certidões antes do vencimento. Um SICAF com certidões vencidas é equivalente
        a não ter o cadastro.
      </p>
      <p>
        Licitações estaduais e municipais geralmente têm sistemas próprios de cadastro (ex.: CAUFESP
        em São Paulo, CAGEF em Minas Gerais). Para licitações nesses entes, verifique se há
        cadastro equivalente que simplifique a habilitação.
      </p>

      <h2>Habilitação em Consórcios e em Subcontratação</h2>
      <p>
        A Lei 14.133/2021 (art. 15) permite expressamente a participação de consórcios em
        licitações. No consórcio, cada integrante apresenta separadamente os documentos de
        habilitação jurídica e regularidade fiscal. A qualificação técnica e econômica pode ser
        somada entre os consorciados, o que é uma vantagem para empresas menores que não atingiriam
        individualmente os requisitos mínimos.
      </p>
      <p>
        Para contratos que admitem subcontratação, o edital pode — ou não — exigir habilitação
        prévia dos subcontratados. Verifique no edital se há cláusula específica sobre esse ponto,
        pois em alguns contratos de obras e serviços de engenharia isso é exigido.
      </p>

      <h2>Usando Inteligência de Dados para Antecipar Exigências</h2>
      <p>
        Além de preparar a documentação, identificar quais licitações valem o esforço é
        fundamental. Use o{' '}
        <Link href="/blog/pncp-guia-completo-empresas">PNCP</Link> para consultar editais
        publicados e verificar os requisitos de habilitação antes de decidir participar. Nossa
        plataforma SmartLic analisa automaticamente a viabilidade de cada edital —{' '}
        incluindo indicadores de modalidade, valor e prazo — para que você priorize os pregões
        com maior probabilidade de sucesso.
      </p>
      <p>
        Para empresas de{' '}
        <Link href="/licitacoes/engenharia">engenharia e construção</Link>, que costumam ter
        exigências de qualificação técnica mais complexas (CAT, acervo de responsável técnico,
        comprovação de aparelhamento), a análise antecipada do edital é ainda mais importante.
        Descobrir que falta um CAT dois dias antes da abertura não deixa tempo hábil para
        providenciar.
      </p>

      <div className="not-prose my-8 sm:my-10 bg-brand/5 border border-brand/20 rounded-lg p-6 sm:p-8 text-center">
        <h3 className="text-xl font-bold mb-2">Encontre Licitações Compatíveis com Sua Habilitação</h3>
        <p className="text-ink-secondary mb-4">
          O SmartLic analisa editais do PNCP e indica quais exigências de habilitação cada pregão tem.
          Prepare sua documentação com antecedência e pare de perder oportunidades por erro burocrático.
        </p>
        <Link
          href="/consultoria-b2g?ref=blog-checklist-habilitacao"
          className="inline-block bg-brand text-white font-semibold px-6 py-3 rounded-lg hover:bg-brand/90 transition-colors"
        >
          Testar Grátis por 14 Dias →
        </Link>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Com quanto tempo de antecedência devo começar a reunir a documentação?</h3>
      <p>
        O ideal é iniciar pelo menos <strong>15 dias antes</strong> da data de abertura das
        propostas. Certidões com validade de 6 meses (CND Federal, CNDT) podem ser obtidas com
        maior antecedência. O CRF do FGTS, com validade de apenas 30 dias, deve ser emitido mais
        próximo à data da sessão. Se sua empresa participa de múltiplas licitações por mês, o
        melhor é manter um calendário de validades atualizado permanentemente.
      </p>

      <h3>Documentos digitais têm validade em licitações?</h3>
      <p>
        Sim. O art. 12, §1º da Lei 14.133/2021 reconhece documentos com assinatura digital
        ICP-Brasil como plenamente válidos. Para pregões eletrônicos, todos os documentos são
        enviados digitalmente — a plataforma do pregão (ComprasNet, BEC, Licitanet etc.) tem
        campo específico para upload. A assinatura eletrônica com certificado e-CNPJ ou e-CPF
        substitui o reconhecimento de firma. Editais de órgãos estaduais e municipais menores
        ainda podem exigir documentos físicos — verifique sempre.
      </p>

      <h3>A documentação pode ser da matriz quando quem participa é uma filial?</h3>
      <p>
        Em regra, certidões fiscais e trabalhistas devem ser do CNPJ participante. Se a filial
        tem CNPJ próprio (sufixo diferente de 0001), as certidões devem ser da filial. A CND
        Federal consolida todas as inscrições do mesmo CNPJ raiz, então ela cobre matriz e filiais.
        A qualificação técnica e econômica em geral pode ser apresentada em nome da matriz, desde
        que o edital não exija especificamente da unidade participante. Sempre leia o edital com
        atenção nesse ponto.
      </p>

      <h3>Qual a validade das certidões mais cobradas?</h3>
      <p>
        CND Federal: 6 meses. CRF do FGTS: 30 dias. CNDT (trabalhista): 180 dias. Certidões
        estaduais e municipais: geralmente 6 meses, mas verifique na fonte emissora. Certidão
        Negativa de Falência: o edital especifica, geralmente entre 60 e 90 dias. Recomendamos
        registrar todas as datas de validade numa planilha e configurar alertas de renovação com
        pelo menos 7 dias de antecedência.
      </p>

      <h3>O SICAF elimina a necessidade de apresentar documentos?</h3>
      <p>
        Para licitações federais, sim — em grande parte. Com o SICAF atualizado nos níveis II e
        III, o pregoeiro consulta a habilitação jurídica e a regularidade fiscal diretamente no
        sistema, sem exigir que você envie os documentos. No entanto, a qualificação técnica
        (nível IV) e econômica (nível V) ainda costumam ser verificadas via documentos
        específicos do edital, e o SICAF precisa estar com as certidões válidas. Para licitações
        estaduais e municipais, o SICAF federal geralmente não tem validade — cada ente tem seu
        próprio sistema de cadastro.
      </p>
    </>
  );
}
