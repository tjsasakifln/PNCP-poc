import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-10: Transparência em compras públicas: Como a Lei 14.133 mudou tudo
 * Content cluster: contratos públicos
 * Target: ~2,800 words | Primary KW: transparência compras públicas Lei 14.133
 */
export default function TransparenciaComprasPublicasLei14133() {
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
                name: 'O que mudou na transparência das compras públicas com a Lei 14.133/2021?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 tornou obrigatória a publicação de todos os atos de contratação no Portal Nacional de Contratações Públicas (PNCP), criando uma fonte única e centralizada de dados. Antes, as informações ficavam dispersas em diários oficiais estaduais e municipais, portais próprios de cada órgão e sistemas incompatíveis entre si. A nova lei também exige dados abertos em formato estruturado, rastreabilidade em tempo real de contratos e mecanismos formais de participação cidadã nos processos licitatórios.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é o PNCP e qual é seu papel na transparência das licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O Portal Nacional de Contratações Públicas (PNCP) é o repositório oficial criado pela Lei 14.133/2021 (Arts. 174 a 176) para centralizar todas as informações sobre contratações públicas no Brasil. Ele funciona como fonte única de verdade: editais, contratos, atas de registro de preços, aditivos e termos de encerramento devem ser publicados no PNCP antes de produzir efeitos jurídicos. Isso garante que qualquer cidadão, empresa ou sistema automatizado possa acessar dados atualizados em tempo real.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como empresas B2G podem usar a transparência das compras públicas para inteligência competitiva?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A transparência imposta pela Lei 14.133/2021 transforma dados públicos em vantagem competitiva. Empresas podem analisar o histórico de contratos de órgãos-alvo para entender padrões de compra, valores praticados e fornecedores recorrentes. É possível identificar quais concorrentes ganham contratos e em quais segmentos, calibrar propostas com base em preços reais praticados pelo mercado, antecipar necessidades de renovação de contratos vigentes e mapear janelas de oportunidade antes da abertura formal dos editais.',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais são as penalidades previstas na Lei 14.133 para falta de transparência?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Os Arts. 155 a 163 da Lei 14.133/2021 estabelecem um regime sancionatório robusto. Para fornecedores, as penalidades incluem advertência, multa de até 30% do valor do contrato, impedimento de licitar por até 3 anos e declaração de inidoneidade por até 6 anos. Para agentes públicos, a omissão na publicação de atos no PNCP pode configurar improbidade administrativa nos termos da Lei 8.429/1992, além de responsabilidade nos termos da Lei de Acesso à Informação (Lei 12.527/2011).',
                },
              },
              {
                '@type': 'Question',
                name: 'Como o TCU e a CGU fiscalizam o cumprimento da transparência nas compras públicas?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O Tribunal de Contas da União (TCU) fiscaliza contratos da União acima de determinados limiares, podendo determinar a suspensão de licitações irregulares e aplicar multas a gestores. A Controladoria-Geral da União (CGU) monitora a conformidade dos órgãos federais com as obrigações de transparência ativa, publica rankings de transparência e conduz auditorias periódicas. Ambos os órgãos utilizam dados do PNCP e do Portal da Transparência como insumo primário para suas análises de risco e seleção de objetos de fiscalização.',
                },
              },
            ],
          }),
        }}
      />

      {/* Article Content */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Durante quase três décadas, a Lei 8.666/1993 governou as compras públicas brasileiras com um modelo que,
        apesar de suas intenções, produziu opacidade sistêmica: publicações fragmentadas em diários oficiais de
        difícil acesso, sistemas eletrônicos incompatíveis entre esferas de governo e uma assimetria de informação
        que favorecia fornecedores estabelecidos em detrimento de novos entrantes. A promulgação da Lei 14.133/2021
        — a Nova Lei de Licitações — representou uma ruptura com essa lógica, colocando a transparência como
        princípio estruturante, não como obrigação acessória.
      </p>

      <h2>O legado de opacidade da Lei 8.666/1993</h2>

      <p>
        A Lei 8.666/1993 nasceu como resposta a escândalos de corrupção e tinha na formalidade procedimental seu
        mecanismo de controle. O problema é que formalidade e transparência não são sinônimos. Na prática, um edital
        publicado em um Diário Oficial impresso de circulação regional atendia à letra da lei, mas tornava o processo
        inacessível para a maioria dos potenciais fornecedores.
      </p>

      <p>
        Ao longo dos anos, surgiram iniciativas pontuais para ampliar o acesso às informações: o ComprasNet (depois
        ComprasGov), os portais de transparência estaduais e o advento do Pregão Eletrônico via Lei 10.520/2002.
        Cada sistema, porém, operava de forma isolada, com formatos de dados proprietários, APIs inconsistentes e
        ausência de padronização semântica. O resultado era um mosaico de informação dispersa que exigia esforço
        desproporcionalmente alto para ser consolidado.
      </p>

      <p>
        A Constituição Federal, em seu Art. 37, estabelece a publicidade como princípio da administração pública.
        A Lei de Acesso à Informação (Lei 12.527/2011) avançou ao criar obrigações de transparência ativa — ou
        seja, divulgação espontânea, sem necessidade de requerimento. Mas foi a Lei 14.133/2021 que integrou esses
        mandatos em um sistema operacional coerente.
      </p>

      <h2>O PNCP como fonte única de verdade: Arts. 174 a 176</h2>

      <p>
        O coração da nova arquitetura de transparência é o Portal Nacional de Contratações Públicas (PNCP), criado
        pelos Arts. 174 a 176 da Lei 14.133/2021. Trata-se de um repositório centralizado mantido pelo governo
        federal, de acesso livre e gratuito, que agrega dados de todos os entes da federação.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-base font-semibold text-ink mb-3">O que deve ser publicado no PNCP (Art. 174)</h3>
        <ul className="space-y-2 text-sm text-ink-light">
          <li>Editais e instrumentos convocatórios, antes da abertura das propostas</li>
          <li>Atas de registro de preços e seus termos aditivos</li>
          <li>Contratos e respectivos aditivos, apostilamentos e encadramentos</li>
          <li>Termos de rescisão e encerramento de contratos</li>
          <li>Notas de empenho vinculadas a dispensas e inexigibilidades</li>
          <li>Resultados de julgamento e habilitação, em tempo real</li>
        </ul>
        <p className="text-xs text-ink-muted mt-3">
          Fonte: Art. 174, incisos I a VI, Lei 14.133/2021
        </p>
      </div>

      <p>
        A inovação central está no Art. 175: os atos listados no Art. 174 somente produzem efeitos jurídicos após
        sua publicação no PNCP. Isso inverte a lógica anterior, em que a publicação era consequência do ato.
        Agora, a publicação é condição de validade. Um contrato não publicado no PNCP é, juridicamente, um contrato
        que ainda não existe.
      </p>

      <p>
        O Art. 176 complementa ao determinar que o PNCP deve disponibilizar suas informações em formato aberto,
        legível por máquina, por meio de interfaces programáticas (APIs). Isso cria a base técnica para que
        sistemas como o SmartLic possam agregar, processar e disponibilizar esses dados de forma estruturada para
        empresas que precisam monitorar oportunidades de{' '}
        <Link href="/licitacoes">licitações públicas</Link>.
      </p>

      <h2>As inovações de transparência da Lei 14.133/2021</h2>

      <h3>Publicação obrigatória no PNCP (Arts. 54 e 94)</h3>

      <p>
        O Art. 54 trata especificamente das fases da licitação, exigindo que o edital seja disponibilizado no PNCP
        com antecedência mínima que varia de 8 a 25 dias úteis, conforme a modalidade e o valor. Esse prazo
        garantido é uma das mais práticas inovações para fornecedores: há tempo hábil para analisar o objeto,
        preparar documentação de habilitação e formular proposta competitiva.
      </p>

      <p>
        O Art. 94 disciplina a publicação dos contratos: o instrumento deve ser divulgado no PNCP em até 20 dias
        úteis de sua assinatura. Aditivos têm prazo de 10 dias úteis. Essa obrigação cria uma trilha auditável
        completa do ciclo de vida de cada contrato público no Brasil.
      </p>

      <h3>Dados abertos e interoperabilidade</h3>

      <p>
        A Lei 14.133/2021 adota, pela primeira vez em legislação licitatória, o conceito de dados abertos como
        requisito legal, não como opção de política pública. O PNCP é obrigado a disponibilizar seus dados em
        formatos estruturados, atualizados em tempo real, sem barreiras de acesso. Isso inclui não apenas textos
        de editais, mas metadados estruturados: CNPJ do órgão, valor estimado, modalidade, UF, situação do processo,
        vencedor e valor adjudicado.
      </p>

      <p>
        Para empresas com capacidade técnica, esses dados abertos permitem construir sistemas de inteligência de
        mercado que seriam impossíveis no regime anterior. Para empresas sem essa capacidade, plataformas como
        o SmartLic processam e qualificam essas informações, tornando-as acionáveis para equipes comerciais.
        Explore como os{' '}
        <Link href="/fornecedores/saude/SP">fornecedores do setor de saúde em São Paulo</Link>{' '}
        já utilizam dados públicos como ferramenta de posicionamento competitivo.
      </p>

      <h3>Rastreabilidade em tempo real dos contratos</h3>

      <p>
        Uma das mudanças mais significativas é a possibilidade de acompanhar contratos públicos em tempo real.
        No regime da Lei 8.666/1993, era comum que aditivos e encadramentos demorassem semanas ou meses para
        aparecer em consultas públicas. Com o PNCP, o prazo máximo é de 10 dias úteis para aditivos, e o
        sistema permite consultas por contrato, por fornecedor e por órgão.
      </p>

      <p>
        Isso tem implicações diretas para a inteligência competitiva: empresas podem monitorar quando contratos
        de concorrentes estão próximos do fim de vigência, identificar padrões de aditamento (indicativo de
        demanda contínua do órgão) e antecipar oportunidades de renovação ou substituição de fornecedores.
        Consulte o{' '}
        <Link href="/contratos/orgao/00394460000141">histórico de contratos do Ministério da Saúde</Link>{' '}
        como exemplo de inteligência derivada de dados públicos.
      </p>

      <h3>Mecanismos de participação e controle cidadão</h3>

      <p>
        A Lei 14.133/2021 inovou ao institucionalizar canais de participação: audiências públicas prévias para
        contratações de grande vulto (Art. 21), diálogo competitivo como nova modalidade que exige interação
        prévia com o mercado (Art. 32), e a possibilidade de impugnação de editais por qualquer interessado
        (Art. 164). Esses mecanismos transformam o processo licitatório de um ato unilateral em um processo
        dialógico, com maior accountability dos gestores públicos.
      </p>

      <BlogInlineCTA slug="transparencia-compras-publicas-lei-14133" campaign="contratos" />

      <h2>Antes e depois: o que mudou para empresas B2G</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-base font-semibold text-ink mb-4">Comparativo: Lei 8.666/1993 vs Lei 14.133/2021</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-ink-light border-collapse">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left py-2 pr-4 font-semibold text-ink">Dimensão</th>
                <th className="text-left py-2 pr-4 font-semibold text-ink">Lei 8.666/1993</th>
                <th className="text-left py-2 font-semibold text-ink">Lei 14.133/2021</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              <tr>
                <td className="py-2 pr-4 font-medium text-ink">Publicação</td>
                <td className="py-2 pr-4">Diários Oficiais fragmentados</td>
                <td className="py-2">PNCP centralizado, fonte única</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium text-ink">Formato dos dados</td>
                <td className="py-2 pr-4">PDF e texto não estruturado</td>
                <td className="py-2">APIs com dados abertos estruturados</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium text-ink">Contratos</td>
                <td className="py-2 pr-4">Publicação variável por ente</td>
                <td className="py-2">20 dias úteis, obrigatório PNCP</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium text-ink">Aditivos</td>
                <td className="py-2 pr-4">Sem prazo padronizado</td>
                <td className="py-2">10 dias úteis, rastreável</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium text-ink">Participação</td>
                <td className="py-2 pr-4">Restrita a licitantes</td>
                <td className="py-2">Qualquer interessado pode impugnar</td>
              </tr>
              <tr>
                <td className="py-2 pr-4 font-medium text-ink">Validade do ato</td>
                <td className="py-2 pr-4">Publicação como formalidade</td>
                <td className="py-2">Publicação como condição de validade</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p>
        Para empresas B2G, a mudança mais imediata é operacional: antes, monitorar licitações exigia uma equipe
        dedicada a varrer dezenas de diários oficiais e portais, processo caro e propenso a falhas. Hoje, um único
        ponto de acesso — o PNCP — concentra toda a produção licitatória do país. A dificuldade se deslocou da
        coleta para a análise: o volume de dados disponíveis é imenso, e a competitividade depende de quem consegue
        extrair inteligência relevante com maior velocidade.
      </p>

      <h2>Portal da Transparência: a dimensão fiscal da transparência</h2>

      <p>
        O Portal da Transparência do governo federal (<em>transparencia.gov.br</em>), mantido pela CGU, complementa
        o PNCP ao oferecer uma perspectiva fiscal das compras públicas. Enquanto o PNCP foca no processo licitatório,
        o Portal da Transparência permite rastrear a execução financeira: empenhos, liquidações e pagamentos
        vinculados a contratos específicos.
      </p>

      <p>
        Para análise de fornecedores, o Portal da Transparência é particularmente valioso: é possível consultar
        todos os contratos firmados com um determinado CNPJ com a União, os valores recebidos por período e a
        vinculação a órgãos específicos. Esse dado, cruzado com informações do PNCP, permite construir um perfil
        completo de um concorrente no mercado público. Consulte, como exemplo,{' '}
        <Link href="/cnpj/33000167000101">o perfil de contratações da Petrobras</Link>{' '}
        para entender como esses dados podem ser organizados para inteligência de mercado.
      </p>

      <p>
        A integração entre PNCP e Portal da Transparência ainda não é perfeita — os sistemas usam identificadores
        distintos e há defasagem temporal entre a publicação do contrato e o registro do empenho. Mas a tendência
        de convergência é clara, e plataformas especializadas já fazem esse cruzamento automaticamente.
      </p>

      <h2>Como usar dados de transparência para inteligência competitiva</h2>

      <p>
        A transparência imposta pela Lei 14.133/2021 não beneficia apenas cidadãos e órgãos de controle. Para
        empresas B2G, representa uma janela sem precedentes para o mercado público. Veja as principais
        aplicações práticas:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-base font-semibold text-ink mb-3">Inteligência competitiva via dados públicos</h3>
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-ink mb-1">Mapeamento de concorrentes</p>
            <p className="text-sm text-ink-light">
              Identifique quais empresas vencem contratos no seu segmento, em quais órgãos e a que preços.
              Dados de resultado de licitação incluem CNPJ do vencedor e valor adjudicado.
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-ink mb-1">Benchmarking de preços</p>
            <p className="text-sm text-ink-light">
              Consulte valores de contratos similares para calibrar sua proposta. A diferença entre ganhar
              e perder uma licitação costuma ser precisão na precificação, não qualidade técnica.
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-ink mb-1">Antecipação de demanda</p>
            <p className="text-sm text-ink-light">
              Contratos com vigência próxima do fim indicam necessidade de renovação ou nova licitação.
              Monitorar esse ciclo coloca sua empresa na posição de propor soluções antes do edital.
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-ink mb-1">Qualificação de órgãos</p>
            <p className="text-sm text-ink-light">
              Órgãos com histórico de pagamento em dia, poucos aditivos por inadimplência e processos
              bem estruturados são clientes de menor risco. Dados do PNCP permitem essa qualificação.
            </p>
          </div>
        </div>
      </div>

      <p>
        O hub de{' '}
        <Link href="/contratos">contratos públicos</Link>{' '}
        do SmartLic organiza esses dados por setor, UF e órgão, facilitando a extração de inteligência sem
        necessidade de lidar diretamente com APIs governamentais. Para aprofundar em segmentos específicos,
        o{' '}
        <Link href="/blog/contratos/ti">guia de contratos de TI</Link>{' '}
        ilustra como essa análise funciona na prática para o setor de tecnologia.
      </p>

      <h2>O papel do TCU e da CGU na fiscalização da transparência</h2>

      <p>
        A arquitetura de controle da transparência em compras públicas no Brasil opera em dois eixos principais.
        O Tribunal de Contas da União (TCU) exerce controle externo sobre as contas da União, com competência
        para fiscalizar contratos, determinar suspensão de licitações irregulares, aplicar multas a gestores e
        declarar inidoneidade de fornecedores. Suas decisões são publicadas e acessíveis, constituindo fonte
        valiosa de jurisprudência para empresas que participam de licitações federais.
      </p>

      <p>
        A Controladoria-Geral da União (CGU) atua no controle interno do Poder Executivo federal, com foco em
        prevenção e detecção de irregularidades. A CGU mantém o Sistema de Gestão de Convênios e Contratos de
        Repasse (SICONV), o Cadastro de Empresas Inidôneas e Suspensas (CEIS) e o Cadastro Nacional de
        Condenações Cíveis por Ato de Improbidade Administrativa (CNIA). Para fornecedores, esses cadastros são
        ferramentas de due diligence: verificar se um potencial parceiro de consórcio está impedido de contratar
        com o poder público é etapa essencial de qualquer estratégia licitatória.
      </p>

      <p>
        Ambos os órgãos passaram a utilizar dados do PNCP como insumo primário para seleção de objetos de
        auditoria. Algoritmos de análise de risco identificam padrões suspeitos — como concentração de contratos
        com um único fornecedor, sobrepreço recorrente em determinada categoria ou fracionamento irregular de
        despesas — e direcionam recursos de fiscalização de forma mais eficiente. A transparência, portanto,
        não é apenas um benefício para o mercado: é também a infraestrutura do controle institucional.
      </p>

      <h2>Penalidades para ausência de transparência: Arts. 155 a 163</h2>

      <p>
        A Lei 14.133/2021 estabelece um regime sancionatório significativamente mais rigoroso que o da
        Lei 8.666/1993. Os Arts. 155 a 163 disciplinam as sanções aplicáveis a fornecedores que descumprem
        obrigações contratuais, incluindo as de natureza informacional. As penalidades são:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-base font-semibold text-ink mb-3">Regime sancionatório (Arts. 155-163)</h3>
        <div className="space-y-3">
          <div className="flex gap-3">
            <span className="text-sm font-semibold text-ink min-w-[120px]">Advertência</span>
            <span className="text-sm text-ink-light">
              Para infrações leves, sem reincidência. Registrada no SICAF e no PNCP.
            </span>
          </div>
          <div className="flex gap-3">
            <span className="text-sm font-semibold text-ink min-w-[120px]">Multa</span>
            <span className="text-sm text-ink-light">
              Até 30% do valor do contrato (inexecução total) ou 0,5% ao dia (mora). Cumulativa com outras sanções.
            </span>
          </div>
          <div className="flex gap-3">
            <span className="text-sm font-semibold text-ink min-w-[120px]">Impedimento</span>
            <span className="text-sm text-ink-light">
              Até 3 anos de impedimento para licitar com o ente sancionador. Substituiu a "suspensão" da Lei 8.666.
            </span>
          </div>
          <div className="flex gap-3">
            <span className="text-sm font-semibold text-ink min-w-[120px]">Inidoneidade</span>
            <span className="text-sm text-ink-light">
              Até 6 anos, com efeitos para todos os entes da federação. A mais grave das sanções.
            </span>
          </div>
        </div>
        <p className="text-xs text-ink-muted mt-4">
          As sanções são registradas no PNCP e no SICAF, com efeito nacional imediato após publicação.
        </p>
      </div>

      <p>
        Para agentes públicos, a omissão na publicação de atos no PNCP pode configurar improbidade administrativa
        nos termos da Lei 8.429/1992 (com as alterações da Lei 14.230/2021), além de infração às obrigações de
        transparência ativa da Lei 12.527/2011. A responsabilidade é do ordenador de despesas, não apenas do
        servidor que operacionaliza o sistema.
      </p>

      <p>
        Um ponto de atenção para fornecedores: as sanções da Lei 14.133/2021 têm efeitos nacionais automáticos,
        o que representa uma mudança em relação à Lei 8.666/1993, em que a suspensão ficava restrita ao ente
        sancionador. Empresas declaradas inidôneas por qualquer órgão ficam impedidas de contratar com toda a
        administração pública federal, estadual e municipal.
      </p>

      <h2>Como o SmartLic agrega dados públicos para inteligência de negócios</h2>

      <p>
        O SmartLic foi construído sobre a premissa de que a transparência pública cria valor comercial quando
        processada com metodologia adequada. A plataforma consome as APIs abertas do PNCP, consolida dados de
        múltiplas fontes — incluindo o{' '}
        <Link href="/contratos">repositório de contratos</Link>{' '}
        — e aplica modelos de inteligência artificial para classificar oportunidades por setor de atuação,
        calcular viabilidade e identificar padrões de mercado.
      </p>

      <p>
        O processo funciona em três camadas. Na primeira, um pipeline de ingestão coleta dados do PNCP em tempo
        quase real, armazenando contratos, editais e resultados em um banco de dados estruturado e indexado para
        busca semântica em português. Na segunda, algoritmos de classificação setorial — calibrados com os 15
        setores econômicos do CNAE mais relevantes para o mercado B2G — qualificam cada oportunidade segundo
        critérios de aderência ao perfil da empresa. Na terceira, uma análise de viabilidade avalia quatro
        fatores: modalidade licitatória, prazo disponível, valor estimado e abrangência geográfica.
      </p>

      <p>
        O resultado é uma camada de inteligência sobre dados que são, por definição, públicos. A transparência
        da Lei 14.133/2021 cria a matéria-prima; a tecnologia cria a vantagem competitiva. Empresas que ainda
        acessam esses dados manualmente — ou que simplesmente não os acessam — operam em desvantagem estrutural
        crescente em relação a concorrentes que automatizaram esse processo.
      </p>

      <h2>O futuro: IA e automação na fiscalização das compras públicas</h2>

      <p>
        A combinação de dados abertos obrigatórios (Lei 14.133/2021) com capacidades crescentes de inteligência
        artificial aponta para uma transformação profunda no ecossistema de compras públicas nos próximos anos.
        TCU e CGU já utilizam modelos de machine learning para detecção de anomalias em dados de contratos. A
        tendência é que esses sistemas se tornem mais sofisticados e abrangentes.
      </p>

      <p>
        Para fornecedores, isso tem duas implicações. A primeira é positiva: a IA vai reduzir ainda mais o custo
        de monitoramento de oportunidades, permitindo que empresas de qualquer porte acessem inteligência de
        mercado antes restrita a grandes consultorias. A segunda é de compliance: em um ambiente com fiscalização
        algorítmica, irregularidades que antes passavam despercebidas serão detectadas automaticamente. A
        transparência, portanto, não é apenas uma obrigação legal — é um princípio de gestão de risco.
      </p>

      <p>
        No horizonte de médio prazo, espera-se a integração do PNCP com outros sistemas federais (SIAFI, SICONV,
        Receita Federal), criando um grafo de dados públicos que permitirá rastrear o ciclo completo de uma
        contratação: desde o planejamento orçamentário até o pagamento final, passando pela habilitação do
        fornecedor e pela execução contratual. Para empresas B2G, esse cenário exige capacidade de interpretar
        e agir sobre um volume crescente de dados estruturados — o que reforça a importância de investir em
        inteligência de mercado como competência estratégica.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-base font-semibold text-ink mb-3">Referências legais e fontes</h3>
        <ul className="space-y-1 text-sm text-ink-light">
          <li>
            <strong>Lei 14.133/2021</strong> — Nova Lei de Licitações e Contratos Administrativos
          </li>
          <li>
            <strong>Lei 8.666/1993</strong> — Lei de Licitações (em processo de revogação progressiva até 2025)
          </li>
          <li>
            <strong>Lei 12.527/2011</strong> — Lei de Acesso à Informação (LAI)
          </li>
          <li>
            <strong>Lei 8.429/1992</strong> — Lei de Improbidade Administrativa (alterada pela Lei 14.230/2021)
          </li>
          <li>
            <strong>Constituição Federal, Art. 37</strong> — Princípios da administração pública
          </li>
          <li>
            <strong>PNCP</strong> — Portal Nacional de Contratações Públicas (<em>pncp.gov.br</em>)
          </li>
          <li>
            <strong>TCU</strong> — Tribunal de Contas da União (<em>tcu.gov.br</em>)
          </li>
          <li>
            <strong>CGU</strong> — Controladoria-Geral da União (<em>cgu.gov.br</em>)
          </li>
          <li>
            <strong>Portal da Transparência</strong> — Execução financeira federal (<em>transparencia.gov.br</em>)
          </li>
        </ul>
      </div>

      <h2>Perguntas frequentes sobre transparência nas compras públicas</h2>

      <div className="not-prose my-6 sm:my-8 space-y-4">
        <div className="bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
          <h3 className="text-base font-semibold text-ink mb-2">
            O que mudou na transparência das compras públicas com a Lei 14.133/2021?
          </h3>
          <p className="text-sm text-ink-light">
            A Lei 14.133/2021 tornou obrigatória a publicação de todos os atos de contratação no Portal Nacional
            de Contratações Públicas (PNCP), criando uma fonte única e centralizada de dados. Antes, as informações
            ficavam dispersas em diários oficiais estaduais e municipais, portais próprios de cada órgão e sistemas
            incompatíveis entre si. A nova lei também exige dados abertos em formato estruturado, rastreabilidade
            em tempo real de contratos e mecanismos formais de participação cidadã nos processos licitatórios.
          </p>
        </div>

        <div className="bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
          <h3 className="text-base font-semibold text-ink mb-2">
            O que é o PNCP e qual é seu papel na transparência das licitações?
          </h3>
          <p className="text-sm text-ink-light">
            O Portal Nacional de Contratações Públicas (PNCP) é o repositório oficial criado pela Lei 14.133/2021
            (Arts. 174 a 176) para centralizar todas as informações sobre contratações públicas no Brasil. Ele
            funciona como fonte única de verdade: editais, contratos, atas de registro de preços, aditivos e
            termos de encerramento devem ser publicados no PNCP antes de produzir efeitos jurídicos. Isso garante
            que qualquer cidadão, empresa ou sistema automatizado possa acessar dados atualizados em tempo real.
          </p>
        </div>

        <div className="bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
          <h3 className="text-base font-semibold text-ink mb-2">
            Como empresas B2G podem usar a transparência das compras públicas para inteligência competitiva?
          </h3>
          <p className="text-sm text-ink-light">
            A transparência imposta pela Lei 14.133/2021 transforma dados públicos em vantagem competitiva.
            Empresas podem analisar o histórico de contratos de órgãos-alvo para entender padrões de compra,
            valores praticados e fornecedores recorrentes. É possível identificar quais concorrentes ganham
            contratos e em quais segmentos, calibrar propostas com base em preços reais praticados pelo mercado,
            antecipar necessidades de renovação de contratos vigentes e mapear janelas de oportunidade antes
            da abertura formal dos editais.
          </p>
        </div>

        <div className="bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
          <h3 className="text-base font-semibold text-ink mb-2">
            Quais são as penalidades previstas na Lei 14.133 para falta de transparência?
          </h3>
          <p className="text-sm text-ink-light">
            Os Arts. 155 a 163 da Lei 14.133/2021 estabelecem um regime sancionatório robusto. Para fornecedores,
            as penalidades incluem advertência, multa de até 30% do valor do contrato, impedimento de licitar por
            até 3 anos e declaração de inidoneidade por até 6 anos. Para agentes públicos, a omissão na publicação
            de atos no PNCP pode configurar improbidade administrativa nos termos da Lei 8.429/1992, além de
            responsabilidade nos termos da Lei de Acesso à Informação (Lei 12.527/2011).
          </p>
        </div>

        <div className="bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
          <h3 className="text-base font-semibold text-ink mb-2">
            Como o TCU e a CGU fiscalizam o cumprimento da transparência nas compras públicas?
          </h3>
          <p className="text-sm text-ink-light">
            O Tribunal de Contas da União (TCU) fiscaliza contratos da União acima de determinados limiares,
            podendo determinar a suspensão de licitações irregulares e aplicar multas a gestores. A
            Controladoria-Geral da União (CGU) monitora a conformidade dos órgãos federais com as obrigações
            de transparência ativa, publica rankings de transparência e conduz auditorias periódicas. Ambos
            os órgãos utilizam dados do PNCP e do Portal da Transparência como insumo primário para suas
            análises de risco e seleção de objetos de fiscalização.
          </p>
        </div>
      </div>
    </>
  );
}
