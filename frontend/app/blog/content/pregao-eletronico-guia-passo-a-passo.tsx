import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * Pregão Eletrônico: Guia Passo a Passo para Primeira Participação
 *
 * Target: ~3200 words | Cluster: guias transversais
 * Primary keyword: pregão eletrônico como participar
 */
export default function PregaoEletronicoGuiaPassoAPasso() {
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
                name: 'Quanto tempo dura um pregão eletrônico do início ao fim?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Um pregão eletrônico completo leva em média de 25 a 45 dias corridos. O edital deve ser publicado com antecedência mínima de 8 dias úteis antes da sessão (art. 55, I da Lei 14.133/2021). Após a sessão de lances, há prazo para habilitação e recursos (geralmente 3 dias úteis cada). A adjudicação e homologação ocorrem após o esgotamento dos prazos recursais. A assinatura do contrato tem prazo máximo de 20 dias após a homologação (art. 90, §1º).',
                },
              },
              {
                '@type': 'Question',
                name: 'Posso participar de pregões em estados onde minha empresa não tem sede?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O pregão eletrônico permite participação de qualquer empresa do Brasil, independentemente do estado sede. A vedação geográfica é proibida pela Lei 14.133/2021 (art. 9º, IV), salvo em situações excepcionais devidamente justificadas (ex.: necessidade de atendimento imediato, visita técnica presencial obrigatória). Na prática, empresas de São Paulo participam de pregões do Amazonas e vice-versa rotineiramente.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que acontece se eu vencer e não conseguir entregar o que foi contratado?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O não cumprimento do contrato público acarreta sanções previstas nos arts. 155 a 163 da Lei 14.133/2021: advertência, multa (geralmente entre 5% e 20% do valor do contrato), impedimento de licitar e contratar por até 3 anos, e declaração de inidoneidade por até 6 anos em casos graves. Além das sanções administrativas, a empresa pode ser responsabilizada civilmente por perdas e danos. Por isso, é fundamental analisar sua capacidade real de entrega antes de participar.',
                },
              },
              {
                '@type': 'Question',
                name: 'Existe tamanho mínimo de empresa para participar de pregões?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não há tamanho mínimo. Qualquer empresa regularmente constituída pode participar de pregões eletrônicos, desde que atenda aos requisitos de habilitação do edital. Microempresas (ME), empresas de pequeno porte (EPP) e microempreendedores individuais (MEI) têm direito a benefícios específicos pela Lei Complementar 123/2006: empate ficto, regularização fiscal tardia, licitações exclusivas em contratos até R$ 80 mil e cotas reservadas.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual é o custo para participar de um pregão eletrônico?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A participação em pregões eletrônicos federais via ComprasNet é gratuita. Alguns portais estaduais e privados (Licitanet, BLL, BEC-SP) cobram taxa de cadastro ou mensalidade, geralmente entre R$ 50 e R$ 300 por mês. O maior custo inicial é o certificado digital e-CNPJ (entre R$ 150 e R$ 500 dependendo da validade e tipo A1/A3). Emissão de certidões negativas na esfera federal é gratuita. Certidões estaduais e municipais podem ter pequenas taxas dependendo do estado ou município.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        O pregão eletrônico representa mais de <strong>80% do volume de compras do governo
        federal</strong> e é a modalidade mais acessível para empresas que estão começando no
        mercado de licitações públicas. Criado pelo Decreto 3.555/2000 e consolidado pela{' '}
        <Link href="/blog/lei-14133-guia-fornecedores">Lei 14.133/2021</Link> (art. 28, I) e
        pelo Decreto 10.024/2019, o pregão eletrônico é inteiramente conduzido online — sem
        necessidade de presença física, sem burocracia presencial e com regras padronizadas que
        favorecem a transparência. Se você nunca participou de um pregão, este guia detalha
        todos os sete passos, do início ao contrato assinado.
      </p>

      <h2>O que é o Pregão Eletrônico e por que é a modalidade mais importante</h2>
      <p>
        O pregão eletrônico é a modalidade de licitação utilizada para aquisição de{' '}
        <strong>bens e serviços comuns</strong> — aqueles cujos padrões de desempenho e qualidade
        podem ser objetivamente definidos por especificações usuais de mercado. O art. 28, I da
        Lei 14.133/2021 define o pregão como modalidade obrigatória para bens e serviços comuns,
        independentemente do valor. O Decreto 10.024/2019 regulamenta a versão eletrônica no
        âmbito federal.
      </p>
      <p>
        A dinâmica central do pregão é a <strong>disputa de lances</strong>: as empresas
        cadastradas apresentam propostas iniciais e depois competem em tempo real com lances
        sucessivos de redução de preço. Vence quem oferecer o menor preço (ou melhor combinação
        de técnica e preço, em modalidades específicas). Após a disputa, apenas o vencedor tem
        sua documentação de habilitação verificada — o que agiliza o processo.
      </p>
      <p>
        O pregão eletrônico é usado para compras de materiais de escritório, equipamentos de TI,
        veículos, serviços de limpeza, vigilância, manutenção predial, consultoria, software,
        serviços de alimentação, logística e centenas de outras categorias. Se sua empresa
        fornece algo que o governo compra regularmente, há alta probabilidade de que o pregão
        seja a modalidade certa para você.
      </p>

      <h2>Antes de Começar — Pré-requisitos Essenciais</h2>
      <p>
        Antes de participar do primeiro pregão, sua empresa precisa ter quatro pré-requisitos
        em ordem. Não há como avançar sem eles:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Pré-requisitos para Participar de Pregões</h3>
        <ul className="space-y-3 text-sm">
          <li>
            <strong>1. CNPJ ativo</strong> — A empresa deve estar regular na Receita Federal com
            situação cadastral "Ativa". MEIs, sociedades simples e empresários individuais também
            participam.
          </li>
          <li>
            <strong>2. Certificado Digital e-CNPJ</strong> — Obrigatório para assinar documentos
            digitalmente e acessar portais. O certificado A1 (software, R$ 150–250, validade 1
            ano) é suficiente para a maioria dos pregões. O A3 (token físico, R$ 300–500) oferece
            maior segurança. Emita em certificadoras credenciadas pelo ICP-Brasil.
          </li>
          <li>
            <strong>3. Cadastro no SICAF</strong> — Para pregões federais, o{' '}
            <Link href="/blog/sicaf-como-cadastrar-manter-ativo-2026">
              SICAF (sicaf.gov.br)
            </Link>{' '}
            é o sistema de cadastro. O credenciamento (Nível I) é feito online. A habilitação
            completa (Níveis II a V) requer upload de documentos e validação pelo órgão gestor,
            levando de 3 a 7 dias úteis.
          </li>
          <li>
            <strong>4. Cadastro nos portais de pregão</strong> — Além do SICAF, você precisa
            estar cadastrado no portal onde o pregão está publicado. Os principais são:
            ComprasNet/Gov.br (comprasnet.gov.br) para federal, BEC (bec.sp.gov.br) para São Paulo,
            Licitanet (licitanet.com.br) e BLL (bll.org.br) para estados e municípios variados.
          </li>
        </ul>
      </div>

      <p>
        O processo completo de preparação — emissão do certificado digital, cadastro no SICAF e
        nos portais, obtenção das certidões — leva de <strong>10 a 20 dias</strong> se tudo
        correr bem. Não deixe para se preparar quando já tiver um pregão em vista. Para um
        diagnóstico dos documentos necessários antes do primeiro pregão, veja nosso{' '}
        <Link href="/blog/checklist-habilitacao-licitacao-2026">
          checklist completo de habilitação
        </Link>
        .
      </p>

      <h2>Passo 1 — Encontrar o Pregão Certo para o Seu Negócio</h2>
      <p>
        O primeiro desafio prático é <strong>localizar pregões compatíveis</strong> com o que
        sua empresa oferece. Há milhares de pregões publicados diariamente no Brasil — a questão
        é filtrar os relevantes. As fontes principais são:
      </p>
      <ul>
        <li>
          <strong>PNCP (pncp.gov.br)</strong> — Portal Nacional de Contratações Públicas, criado
          pela Lei 14.133/2021. Centraliza publicações de todas as esferas (federal, estadual,
          municipal). É a fonte oficial e mais completa. Veja nosso{' '}
          <Link href="/blog/pncp-guia-completo-empresas">guia do PNCP para empresas</Link>.
        </li>
        <li>
          <strong>ComprasNet/Gov.br</strong> — Para compras federais. Sistema legado ainda em uso
          paralelo ao PNCP para órgãos federais.
        </li>
        <li>
          <strong>Portais estaduais e municipais</strong> — BEC (SP), FGPP (RJ), COMPRAS-SC,
          LicitaCidades e outros sistemas regionais com publicações que podem não estar no PNCP.
        </li>
        <li>
          <strong>Plataformas de monitoramento</strong> — Ferramentas como o SmartLic agregam
          múltiplas fontes e filtram por setor, UF, valor e modalidade, eliminando o trabalho
          manual de verificar portal por portal.
        </li>
      </ul>
      <p>
        Ao filtrar pregões, use os critérios: <strong>objeto</strong> (compatível com sua
        atividade CNAE?), <strong>UF</strong> (você consegue entregar?), <strong>valor
        estimado</strong> (compatível com sua capacidade?) e <strong>prazo de abertura</strong>
        (tempo suficiente para preparar a proposta?). Nossa{' '}
        <Link href="/calculadora">calculadora de viabilidade</Link> ajuda a pontuar cada
        oportunidade.
      </p>

      <h2>Passo 2 — Analisar o Edital com Atenção</h2>
      <p>
        O edital é o documento central do pregão. Tudo que não está no edital não existe para
        efeitos do certame. Ler o edital integralmente antes de qualquer outra ação é
        imprescindível — mesmo editais de objetos idênticos de órgãos diferentes podem ter
        exigências completamente distintas.
      </p>
      <p>
        As seções mais críticas para revisar são:
      </p>
      <ul>
        <li>
          <strong>Objeto:</strong> Descrição exata do que será comprado, com especificações
          técnicas. Verifique se sua empresa entrega exatamente o que é pedido.
        </li>
        <li>
          <strong>Habilitação:</strong> Lista de documentos exigidos. Verifique se você tem todos
          antes de gastar tempo preparando a proposta.
        </li>
        <li>
          <strong>Critério de julgamento:</strong> Menor preço (mais comum), melhor técnica,
          técnica e preço, ou maior retorno econômico. O pregão eletrônico usa quase sempre
          menor preço ou menor preço por item.
        </li>
        <li>
          <strong>Prazos:</strong> Data e hora exata da abertura das propostas, prazo para
          pedido de esclarecimento e impugnação (geralmente até 3 dias úteis antes da abertura),
          prazo da sessão de lances.
        </li>
        <li>
          <strong>Penalidades:</strong> Arts. 155 a 163 da Lei 14.133/2021 definem as sanções
          por descumprimento. Verifique as multas previstas — um contrato com multa de 20% por
          atraso de entrega muda completamente o cálculo de risco.
        </li>
        <li>
          <strong>Dotação orçamentária:</strong> Confirme que o órgão tem recurso previsto
          (orçamento). Contratos sem dotação são nulos.
        </li>
      </ul>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">⚠ Dúvidas sobre o Edital? Use o Pedido de Esclarecimento</p>
        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
          Se alguma cláusula do edital for ambígua ou potencialmente restritiva, você tem direito
          de enviar pedido de esclarecimento ao pregoeiro (art. 41 da Lei 14.133/2021), geralmente
          até 3 dias úteis antes da abertura. Se a cláusula for ilegal ou restritiva à
          concorrência, cabe impugnação no mesmo prazo. As respostas são publicadas no próprio
          sistema do pregão e vinculam o órgão.
        </p>
      </div>

      <h2>Passo 3 — Preparar a Proposta de Preço</h2>
      <p>
        A proposta de preço é o documento que determina o valor pelo qual você está disposto a
        fornecer o objeto. No pregão eletrônico, a proposta é cadastrada no sistema antes da
        sessão de lances — ela é o ponto de partida para a disputa.
      </p>
      <p>
        Os elementos essenciais da proposta são:
      </p>
      <ul>
        <li>
          <strong>Preço unitário e total:</strong> Calcule com precisão os custos diretos
          (insumos, mão de obra, logística), custos indiretos (overhead, tributos, encargos),
          margem de lucro e impostos sobre o faturamento. O BDI (Benefícios e Despesas Indiretas)
          é o percentual que adiciona esses custos ao preço direto em contratos de obras e
          serviços de engenharia.
        </li>
        <li>
          <strong>Validade da proposta:</strong> Geralmente 60 dias. Confirme o prazo exigido no
          edital.
        </li>
        <li>
          <strong>Prazo de entrega ou execução:</strong> Declare o prazo que você consegue cumprir.
          Não declare um prazo que não pode honrar — isso é motivo de sanção.
        </li>
        <li>
          <strong>Marca/modelo (quando aplicável):</strong> Para bens, declare a marca e modelo
          do produto que será fornecido. O produto deve atender às especificações do edital.
        </li>
      </ul>
      <p>
        Atenção ao conceito de <strong>preço inexequível</strong>: o art. 59, §4º da Lei
        14.133/2021 permite ao órgão desclassificar propostas com preços abaixo do custo de
        produção — ou exigir que o licitante comprove que consegue executar pelo valor ofertado.
        Calcule seus custos com precisão antes de definir o preço inicial.
      </p>
      <p>
        Para estimar o preço de referência do órgão (valor estimado), consulte o PNCP — o edital
        deve publicar a estimativa de preço. Você também pode pesquisar contratos anteriores
        similares para ter benchmark de mercado. Nossa{' '}
        <Link href="/calculadora">calculadora de viabilidade de licitações</Link> oferece
        referências de preço por categoria de objeto.
      </p>

      <BlogInlineCTA slug="pregao-eletronico-guia-passo-a-passo" campaign="guias" />

      <h2>Passo 4 — Cadastrar a Proposta no Sistema</h2>
      <p>
        Com a proposta calculada, o próximo passo é cadastrá-la no sistema do pregão. O processo
        varia ligeiramente por portal, mas segue a mesma lógica geral:
      </p>
      <ul>
        <li>
          <strong>ComprasNet/Gov.br (federal):</strong> Acesse o portal, localize o pregão pelo
          número ou UASG, clique em "Acessar" e depois em "Cadastrar Proposta". Preencha preço,
          prazo, marca (se aplicável) e anexe a proposta em PDF assinada digitalmente. A proposta
          deve ser enviada até o prazo de encerramento definido no edital — geralmente a mesma
          hora da abertura da sessão.
        </li>
        <li>
          <strong>BEC-SP (São Paulo estadual):</strong> Acesso via bec.sp.gov.br com certificado
          digital. A interface é diferente do ComprasNet mas o processo é equivalente.
        </li>
        <li>
          <strong>Licitanet / BLL / outros:</strong> Portais privados credenciados pelos órgãos
          licitantes. Cada um tem sua interface, mas o fluxo de cadastro de proposta é similar.
          Leia o manual do portal disponível no edital.
        </li>
      </ul>
      <p>
        <strong>Erro crítico a evitar:</strong> enviar a proposta em formato errado (ex.: PDF
        não assinado quando exigido assinatura digital) ou deixar campos obrigatórios em branco.
        Antes de enviar, revise todos os campos e faça um teste com um pregão de valor baixo para
        conhecer a interface do sistema.
      </p>
      <p>
        O sistema guarda sua proposta até o momento do encerramento para cadastramento. Você pode
        alterar a proposta quantas vezes quiser antes desse prazo. Após o encerramento, nenhuma
        alteração é possível.
      </p>

      <h2>Passo 5 — Participar da Disputa de Lances</h2>
      <p>
        A sessão de lances é a parte mais dinâmica do pregão eletrônico. Ela ocorre no horário
        definido no edital e tem duração variável — geralmente entre 15 minutos e 2 horas,
        dependendo da modalidade de disputa e do número de licitantes.
      </p>
      <p>
        A Lei 14.133/2021 e o Decreto 10.024/2019 preveem dois modos de disputa:
      </p>
      <ul>
        <li>
          <strong>Modo Aberto:</strong> Os lances são visíveis a todos os participantes em tempo
          real. É o modo mais comum. Cada lance deve ser inferior ao anterior. Há uma etapa final
          de prorrogação automática: se houver lance nos últimos 2 minutos da sessão, o sistema
          prorroga por mais 2 minutos, repetindo enquanto houver lances.
        </li>
        <li>
          <strong>Modo Fechado:</strong> Os licitantes enviam um único lance final sem ver os
          lances dos concorrentes. Após o prazo, todos os lances são revelados simultaneamente.
          Usado em objetos estratégicos onde o modo aberto poderia distorcer o mercado.
        </li>
        <li>
          <strong>Modo Aberto e Fechado (combinado):</strong> Primeiro ocorre uma fase fechada
          para os três melhores da fase aberta, permitindo ajuste estratégico.
        </li>
      </ul>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Estratégias para a Fase de Lances</h3>
        <ul className="space-y-2 text-sm">
          <li>• <strong>Defina seu preço mínimo antes da sessão</strong> — saiba exatamente até onde você pode ir sem prejuízo</li>
          <li>• <strong>Não lance precipitadamente</strong> — observe os concorrentes nas fases iniciais antes de revelar sua estratégia</li>
          <li>• <strong>Atenção ao lance mínimo:</strong> alguns sistemas exigem redução mínima por lance (ex.: 0,5% ou R$ X) — verifique no edital</li>
          <li>• <strong>Benefício ME/EPP:</strong> microempresas têm direito ao empate ficto — se sua proposta estiver até 5% acima do melhor lance, você pode cobrir o preço vencedor</li>
          <li>• <strong>Esteja disponível:</strong> sessões podem durar horas com múltiplos itens. Reserve o tempo necessário no dia</li>
          <li>• <strong>Conexão estável:</strong> problemas técnicos durante a sessão de lances podem custar a oportunidade</li>
        </ul>
      </div>

      <h2>Passo 6 — Negociação e Habilitação</h2>
      <p>
        Após o encerramento dos lances, o pregoeiro pode iniciar uma <strong>negociação
        direta</strong> com o licitante que apresentou o menor preço, buscando redução adicional
        (art. 61 da Lei 14.133/2021). Essa negociação é registrada no sistema. Se você for o
        melhor colocado, esteja preparado para negociar — mas nunca aceite um preço abaixo do seu
        custo apenas para ganhar o contrato.
      </p>
      <p>
        Após a negociação, inicia-se a fase de <strong>habilitação</strong>. Como explicamos no
        guia sobre o{' '}
        <Link href="/blog/checklist-habilitacao-licitacao-2026">
          checklist de habilitação
        </Link>
        , o pregoeiro verifica os documentos do licitante vencedor. No pregão eletrônico, isso é
        feito via upload de documentos no sistema ou consulta ao SICAF. Os documentos solicitados
        devem ser enviados no prazo definido pelo pregoeiro — geralmente 2 horas a 1 dia útil.
      </p>
      <p>
        Se algum documento estiver incorreto ou vencido, o pregoeiro pode convocar o segundo
        colocado. Por isso, é fundamental ter toda a documentação pronta antes da sessão,
        mesmo que a habilitação só seja exigida do vencedor.
      </p>

      <h2>Passo 7 — Recurso, Adjudicação e Assinatura do Contrato</h2>
      <p>
        Após a habilitação, os demais licitantes têm direito de manifestar intenção de recurso
        (art. 165, I da Lei 14.133/2021). O prazo para manifestação de intenção é de 3 dias
        úteis. Se houver intenção de recurso aceita pelo pregoeiro, o recorrente tem mais 3 dias
        úteis para apresentar as razões.
      </p>
      <p>
        Se não houver recursos, ou após o julgamento dos recursos, o processo segue para:
      </p>
      <ul>
        <li><strong>Adjudicação:</strong> O pregoeiro declara o vencedor formalmente.</li>
        <li><strong>Homologação:</strong> A autoridade superior confirma a legalidade do processo.</li>
        <li>
          <strong>Assinatura do Contrato:</strong> O art. 90, §1º da Lei 14.133/2021 define prazo
          máximo de 20 dias corridos após a homologação para assinatura. O contrato deve ser
          assinado com certificado digital ICP-Brasil.
        </li>
      </ul>
      <p>
        Após a assinatura, o contrato é publicado no PNCP (obrigatório pela Lei 14.133/2021) e
        a execução pode começar conforme os prazos definidos nas cláusulas contratuais.
      </p>

      <h2>A Armadilha do Preço Inexequível</h2>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">⚠ O Risco do Preço Baixo Demais</p>
        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
          O art. 59, §4º da Lei 14.133/2021 permite desclassificar propostas com preços
          manifestamente inexequíveis — abaixo do custo de produção sem justificativa técnica.
          Em pregões de serviços com dedicação exclusiva de mão de obra (limpeza, vigilância,
          recepção), o cálculo do preço inexequível é feito com base na planilha de custos e
          formação de preços. Ganhar um pregão com preço abaixo do custo e não conseguir cumprir
          o contrato resulta em sanções administrativas que podem inviabilizar sua empresa para
          futuras licitações por anos.
        </p>
      </div>

      <h2>Cronograma Típico de um Pregão Eletrônico</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Linha do Tempo — Pregão Eletrônico Padrão</h3>
        <ul className="space-y-3 text-sm">
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dia 0</span>
            <span>Publicação do edital no PNCP e no portal do pregão</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dias 1–5</span>
            <span>Prazo para pedidos de esclarecimento e impugnação (até 3 dias úteis antes da abertura)</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dias 5–8</span>
            <span>Órgão publica respostas a esclarecimentos e julgamento de impugnações</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Até dia 8</span>
            <span>Prazo mínimo legal para abertura (8 dias úteis da publicação — art. 55, I)</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dia 8–10</span>
            <span>Sessão de abertura de propostas e disputa de lances (horário no edital)</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dia 10–12</span>
            <span>Negociação, verificação de habilitação do primeiro colocado</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dias 12–17</span>
            <span>Prazo para manifestação de intenção de recurso (3 dias úteis) e razões (mais 3 dias úteis)</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dia 18–20</span>
            <span>Adjudicação e homologação pela autoridade superior</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Dia 20–40</span>
            <span>Assinatura do contrato (prazo máximo: 20 dias corridos após homologação)</span>
          </li>
          <li className="flex gap-3">
            <span className="font-semibold text-ink-secondary min-w-[80px]">Após contrato</span>
            <span>Início da execução conforme prazo contratual; primeiro pagamento após atesto da NF</span>
          </li>
        </ul>
      </div>

      <h2>Como Monitorar Pregões Continuamente</h2>
      <p>
        Participar de licitações de forma consistente exige monitoramento constante. Empresas que
        participam apenas de pregões que encontram por acidente dificilmente constroem uma
        estratégia eficiente. O ideal é ter um fluxo de monitoramento que:
      </p>
      <ul>
        <li>Identifique novos pregões compatíveis diariamente ou semanalmente</li>
        <li>Filtre por objeto, UF, valor estimado e prazo de abertura</li>
        <li>Alerte quando um edital relevante for publicado com tempo hábil para preparação</li>
        <li>Permita análise de viabilidade rápida antes de investir tempo na proposta</li>
      </ul>
      <p>
        O PNCP é a fonte oficial, mas sua interface de busca é básica. Plataformas especializadas
        como o SmartLic agregam PNCP, portais estaduais e ComprasNet em uma busca unificada,
        com filtros por setor e análise automática de viabilidade. Veja como funciona a{' '}
        <Link href="/blog/como-participar-primeira-licitacao-2026">
          estratégia de seleção de licitações para iniciantes
        </Link>{' '}
        e como evitar os{' '}
        <Link href="/blog/erros-desclassificam-propostas-licitacao">
          erros mais comuns que desclassificam propostas
        </Link>
        .
      </p>
      <p>
        Para empresas do setor de{' '}
        <Link href="/licitacoes/engenharia">engenharia e obras</Link>, o processo de preparação
        é mais extenso — inclui análise de plantas, composição de BDI, atestados de capacidade
        técnica e CAT — mas a dinâmica do pregão eletrônico é a mesma descrita neste guia.
      </p>

      <div className="not-prose my-8 sm:my-10 bg-brand/5 border border-brand/20 rounded-lg p-6 sm:p-8 text-center">
        <h3 className="text-xl font-bold mb-2">Encontre Pregões Compatíveis com Seu Negócio Agora</h3>
        <p className="text-ink-secondary mb-4">
          O SmartLic monitora o PNCP e dezenas de portais em tempo real, filtra por setor e UF e
          analisa a viabilidade de cada pregão automaticamente. Pare de gastar horas procurando
          editais manualmente.
        </p>
        <Link
          href="/consultoria-b2g?ref=blog-pregao-eletronico"
          className="inline-block bg-brand text-white font-semibold px-6 py-3 rounded-lg hover:bg-brand/90 transition-colors"
        >
          Testar Grátis por 14 Dias →
        </Link>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Quanto tempo dura um pregão eletrônico do início ao fim?</h3>
      <p>
        Um pregão eletrônico completo leva em média de <strong>25 a 45 dias corridos</strong>. O
        edital deve ser publicado com antecedência mínima de 8 dias úteis antes da sessão (art.
        55, I da Lei 14.133/2021). Após a sessão de lances, há prazo para habilitação e recursos
        (geralmente 3 dias úteis cada). A adjudicação e homologação ocorrem após o esgotamento
        dos prazos recursais. A assinatura do contrato tem prazo máximo de 20 dias após a
        homologação (art. 90, §1º).
      </p>

      <h3>Posso participar de pregões em estados onde minha empresa não tem sede?</h3>
      <p>
        Sim. O pregão eletrônico permite participação de qualquer empresa do Brasil,
        independentemente do estado sede. A vedação geográfica é expressamente proibida pela Lei
        14.133/2021 (art. 9º, IV), salvo em situações excepcionais devidamente justificadas.
        Na prática, empresas de São Paulo participam rotineiramente de pregões do Pará, Goiás,
        Rio Grande do Sul e qualquer outra UF. A única limitação real é logística: verifique se
        você consegue entregar o objeto no local exigido pelo contrato.
      </p>

      <h3>O que acontece se eu vencer e não conseguir entregar?</h3>
      <p>
        O não cumprimento acarreta sanções dos arts. 155 a 163 da Lei 14.133/2021: advertência,
        multa (5% a 20% do contrato conforme o edital), impedimento de licitar por até 3 anos e,
        nos casos mais graves, declaração de inidoneidade por até 6 anos. Além disso, a empresa
        pode ser responsabilizada pelos danos causados ao órgão. Por isso, a análise de
        viabilidade operacional — não apenas financeira — é tão importante quanto o preço antes
        de oferecer.
      </p>

      <h3>Existe tamanho mínimo de empresa para participar?</h3>
      <p>
        Não. Qualquer empresa regularmente constituída pode participar. MEI, microempresa e EPP
        participam com os benefícios da LC 123/2006: direito ao empate ficto (até 5% acima do
        melhor lance no pregão), regularização fiscal tardia e acesso a licitações exclusivas
        para ME/EPP em contratos até R$ 80 mil. O edital pode exigir requisitos mínimos de
        habilitação técnica ou econômica — esses são os limites reais, não o porte da empresa.
      </p>

      <h3>Qual é o custo para participar de um pregão eletrônico?</h3>
      <p>
        A participação em pregões federais via ComprasNet é gratuita. O principal custo é o
        certificado digital e-CNPJ (R$ 150 a R$ 500 dependendo do tipo e validade). Portais
        privados (Licitanet, BLL) podem cobrar mensalidade de R$ 50 a R$ 300. Emissão de
        certidões negativas federais (Receita, PGFN, FGTS, Trabalhista) é gratuita. Certidões
        estaduais e municipais podem ter pequenas taxas. Fora esses custos fixos, não há taxa
        para participar de pregões.
      </p>
    </>
  );
}
