import Link from 'next/link';

export const sections = [
  { id: 'o-que-e-pncp', title: 'O que é o PNCP' },
  { id: 'fundamento-legal', title: 'Fundamento legal' },
  { id: 'obrigatoriedade', title: 'Obrigatoriedade e entes submetidos' },
  { id: 'consultar-editais', title: 'Como consultar editais' },
  { id: 'api-publica', title: 'API pública — automação' },
  { id: 'paginacao-limites', title: 'Limites e paginação (50/página desde fev/2026)' },
  { id: 'tipos-de-publicacao', title: 'Tipos de atos publicados' },
  { id: 'alertas', title: 'Como receber alertas de novos editais' },
  { id: 'integracao-outros-portais', title: 'PNCP + Compras.gov + outros portais' },
  { id: 'estrategias-empresa', title: 'Estratégias de empresas B2G' },
];

const ExternalLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <a href={href} target="_blank" rel="noopener noreferrer">
    {children}
  </a>
);

export default function PncpContent() {
  return (
    <>
      <p className="text-xl leading-relaxed text-ink font-medium !mt-0">
        O PNCP (Portal Nacional de Contratações Públicas), disponível em{' '}
        <ExternalLink href="https://pncp.gov.br/">pncp.gov.br</ExternalLink>, é o canal único oficial de divulgação de editais, atas de registro de preço e contratos de toda a administração pública brasileira desde 30/12/2023. Entender como navegar, consultar e automatizar a extração de dados do PNCP é o primeiro passo operacional de qualquer empresa B2G em 2026.
      </p>

      <h2 id="o-que-e-pncp">O que é o PNCP</h2>
      <p>
        O PNCP é um sistema centralizador mantido pela Secretaria de Gestão do Ministério da Gestão e Inovação (MGI). Reúne, em um mesmo ambiente, atos de contratação pública de todos os entes federativos — União, Estados, Distrito Federal, Municípios e empresas estatais. Substitui (ou complementa, conforme o órgão) canais anteriormente fragmentados: Diário Oficial da União (DOU), sites próprios de ministérios, portais estaduais heterogêneos, jornais de grande circulação.
      </p>
      <p>
        Para o fornecedor, o valor prático é direto: em vez de acompanhar 50+ canais heterogêneos, há agora um único repositório pesquisável com todos os editais válidos. Para a administração, reduz redundância, aumenta transparência e oferece dados abertos para análise pública.
      </p>

      <h2 id="fundamento-legal">Fundamento legal</h2>
      <p>
        O art. 174 da{' '}
        <ExternalLink href="https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art174">Lei 14.133/2021</ExternalLink>{' '}
        institui formalmente o PNCP como &ldquo;sítio eletrônico oficial destinado à divulgação centralizada e obrigatória dos atos exigidos por esta Lei&rdquo;. O art. 54 reforça a obrigatoriedade de publicação no PNCP para produção de efeitos do edital.
      </p>
      <p>
        O Decreto 11.462/2023 regulamenta operacionalmente o portal: arquitetura, modelo de dados, fluxos de integração entre sistemas de contratação (federais, estaduais, municipais) e o PNCP. Na prática, cada sistema de compras envia ao PNCP os atos via APIs específicas; o PNCP agrega e disponibiliza publicamente.
      </p>

      <h2 id="obrigatoriedade">Obrigatoriedade e entes submetidos</h2>
      <p>
        Todos os seguintes entes são obrigados a publicar no PNCP:
      </p>
      <ul>
        <li>Administração direta, autárquica e fundacional da União.</li>
        <li>Administração direta, autárquica e fundacional dos Estados, DF e Municípios.</li>
        <li>Empresas estatais (dependentes) controladas direta ou indiretamente pela União, Estados ou Municípios.</li>
        <li>Consórcios públicos intermunicipais.</li>
        <li>Serviços sociais autônomos (quando utilizarem recursos públicos).</li>
      </ul>
      <p>
        A omissão de publicação configura nulidade do ato. Em 2026, é cada vez mais raro encontrar edital válido fora do PNCP — quando acontece, geralmente é sinal de erro processual que pode ser objeto de representação ao TCU ou ao Tribunal de Contas estadual/municipal correspondente.
      </p>

      <h2 id="consultar-editais">Como consultar editais no PNCP</h2>
      <p>
        Em{' '}
        <ExternalLink href="https://pncp.gov.br/app/editais">pncp.gov.br/app/editais</ExternalLink>, a interface oferece filtros:
      </p>
      <ul>
        <li>
          <strong>Palavra-chave:</strong> busca textual no objeto do edital.
        </li>
        <li>
          <strong>Modalidade:</strong> pregão, concorrência, dispensa, inexigibilidade, credenciamento, leilão, diálogo competitivo.
        </li>
        <li>
          <strong>UF e município:</strong> filtra por geografia.
        </li>
        <li>
          <strong>Valor estimado:</strong> faixas de valor contratual.
        </li>
        <li>
          <strong>Data de publicação:</strong> janela temporal.
        </li>
        <li>
          <strong>Situação:</strong> aberto, encerrado, homologado, cancelado.
        </li>
      </ul>
      <p>
        Resultados podem ser exportados em CSV (limite por página). Cada edital tem ficha com metadados, link para o documento integral e timeline de eventos (publicação, abertura, adjudicação, homologação).
      </p>

      <h2 id="api-publica">API pública — automação</h2>
      <p>
        O PNCP expõe{' '}
        <ExternalLink href="https://pncp.gov.br/api/consulta/">API pública de consulta</ExternalLink>{' '}
        gratuita e sem autenticação. Endpoint principal:
      </p>
      <blockquote>
        <code>https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao</code>
      </blockquote>
      <p>
        Aceita parâmetros: <code>dataInicial</code>, <code>dataFinal</code>, <code>codigoModalidadeContratacao</code>, <code>uf</code>, <code>pagina</code>, <code>tamanhoPagina</code> (máx 50 desde fev/2026). Retorna JSON com array de contratações e metadados de paginação.
      </p>
      <p>
        Para empresas que querem consumir a API diretamente, três conselhos práticos de quem opera isso em produção:
      </p>
      <ul>
        <li>
          <strong>Rate limiting conservador:</strong> o PNCP responde bem até ~5 requests/segundo. Acima, há throttling silencioso (HTTP 422) sem mensagem clara.
        </li>
        <li>
          <strong>Retry com backoff exponencial:</strong> HTTP 422 e 5xx são ocasionais; retry com 500ms/1s/2s resolve a maioria dos casos.
        </li>
        <li>
          <strong>Paginação phased por UF:</strong> consultar 27 UFs em paralelo satura o portal; consultar em batches de 5 UFs com 2s de delay entre batches mantém estabilidade.
        </li>
      </ul>

      <h2 id="paginacao-limites">Limites e paginação</h2>
      <p>
        Em fevereiro de 2026, o PNCP reduziu o limite de <code>tamanhoPagina</code> de 500 para 50 registros por página. Valores acima de 50 retornam HTTP 400 silencioso (sem mensagem clara de causa) — um armadilha comum para quem ainda não atualizou clients existentes. Documentação da mudança está no{' '}
        <ExternalLink href="https://pncp.gov.br/api/consulta/">Manual da API</ExternalLink>, mas foi comunicada em changelog menor que muitas empresas não monitoram.
      </p>
      <p>
        Consequência operacional: buscas de 10 dias cobrindo todas as UFs e 6 modalidades principais (4, 5, 6, 7, 8, 12) podem gerar até ~4.000 páginas. Quem automatiza precisa planejar job de longa duração (15-30 minutos) com checkpointing para retomar após falhas.
      </p>

      <h2 id="tipos-de-publicacao">Tipos de atos publicados</h2>
      <p>
        O PNCP não é só editais de licitação. Inclui:
      </p>
      <ul>
        <li>
          <strong>Editais de licitação:</strong> pregão, concorrência, dispensa eletrônica, credenciamento etc.
        </li>
        <li>
          <strong>Atas de registro de preços:</strong> permitem adesão por outros órgãos (&ldquo;carona&rdquo;) durante 12 meses.
        </li>
        <li>
          <strong>Contratos:</strong> íntegra dos contratos firmados, com termos aditivos.
        </li>
        <li>
          <strong>Avisos de contratação direta:</strong> dispensa e inexigibilidade.
        </li>
        <li>
          <strong>Planos anuais de contratações (PAC):</strong> lista de compras previstas por órgão para o ano corrente.
        </li>
      </ul>
      <p>
        O PAC é um dos ativos mais subutilizados do PNCP: empresas que consultam o PAC antecipam pipelines com 6-12 meses de lead time, estabelecem relacionamento pré-edital com áreas compradoras e posicionam-se melhor quando o edital efetivamente abre.
      </p>

      <h2 id="alertas">Como receber alertas de novos editais</h2>
      <p>
        O PNCP não oferece notificações nativas (email, push, webhook) de novos editais. Isso é, intencionalmente, uma limitação: a filosofia é que o portal é fonte pública e cada interessado deve consumir segundo sua necessidade. Para receber alertas, há três caminhos:
      </p>
      <ol>
        <li>
          <strong>Script próprio consumindo a API:</strong> viável para empresas com time técnico. Requer cron (ex.: 3x/dia), armazenamento (para diff), envio (SMTP, Slack, etc.). Custo de manutenção crescente — quando o PNCP muda schema (como em fev/2026), o script quebra silenciosamente.
        </li>
        <li>
          <strong>Plataformas terceiras B2G:</strong> SmartLic, Conlicitação, Effecti, entre outras. Vendem por assinatura mensal; entregam alertas configuráveis por palavra-chave, UF, modalidade.
        </li>
        <li>
          <strong>Consultorias de licitação:</strong> terceirizam o monitoramento inteiro, por taxa mensal. Viável quando volume é baixo e empresa prefere &ldquo;out of box&rdquo; sem ferramenta própria.
        </li>
      </ol>
      <p>
        Empresas B2G que processam mais de 50 editais/mês consistentemente usam plataforma. Script próprio raramente compensa no médio prazo — o custo humano de debugar mudanças de schema excede a assinatura de uma plataforma.
      </p>

      <h2 id="integracao-outros-portais">PNCP + Compras.gov + outros portais</h2>
      <p>
        Apesar do PNCP ser canal obrigatório de publicação, a execução operacional de muitos certames ocorre em outros sistemas:
      </p>
      <ul>
        <li>
          <strong>Compras.gov.br:</strong> sistema federal da União, onde pregões federais rodam efetivamente (cadastro de proposta, lances, habilitação).
        </li>
        <li>
          <strong>Sistemas estaduais:</strong> Compras-MG, SIGAe-SP, PE-Integrado, entre outros.
        </li>
        <li>
          <strong>Sistemas privados integrados:</strong> Licitanet, BNC (Bolsa Nacional de Compras), BLL (Bolsa de Licitações e Leilões) — usados por muitos municípios como solução SaaS.
        </li>
        <li>
          <strong>Portal de Compras Públicas (compras.api.portaldecompraspublicas.com.br):</strong> agrega dados de múltiplas plataformas em API pública alternativa ao PNCP.
        </li>
      </ul>
      <p>
        Para empresas que atuam nacionalmente, o desafio é claro: o edital é encontrado no PNCP, mas a participação ocorre na plataforma que o órgão usa. O SmartLic agrega as 3 principais fontes de dados e resolve isso na primeira etapa do funil (descoberta + triagem).
      </p>

      <h2 id="estrategias-empresa">Estratégias de empresas B2G para PNCP</h2>
      <p>
        Três estratégias que separam empresas que ganham editais via PNCP das que apenas consomem dados:
      </p>

      <h3>1. Monitorar o Plano Anual de Contratações (PAC)</h3>
      <p>
        Todo órgão publica o PAC no PNCP no início do exercício. Empresas B2G maduras leem os PACs dos órgãos prioritários do seu setor, identificam compras previstas nos próximos 6-12 meses, fazem visitas técnicas (quando permitido), posicionam oferta. Quando o edital efetivamente abre, já estão 3 passos à frente dos concorrentes reagindo a anúncio.
      </p>

      <h3>2. Análise histórica de adjudicações</h3>
      <p>
        O PNCP persiste histórico completo. Isso permite benchmark: quem tem ganhado em setores similares, quais valores adjudicados, quais órgãos compram com frequência, quais são os ciclos sazonais. O{' '}
        <Link href="/blog/como-calcular-preco-proposta-licitacao">guia de precificação de proposta</Link>{' '}
        detalha como usar isso para formar preços competitivos-mas-lucrativos.
      </p>

      <h3>3. Triagem sistemática com score de viabilidade</h3>
      <p>
        O PNCP publica 500-2000 novos atos/dia. Ler tudo é impossível. Empresas eficientes aplicam triagem em duas camadas: (a) filtro por keyword e exclusão setorial — reduz para ~50 editais relevantes/dia; (b) score de viabilidade em 4 fatores (modalidade, timeline, valor, geografia) — reduz para 5-10 editais para análise humana aprofundada. Ver{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao">guia de análise de viabilidade</Link>.
      </p>

      <p>
        Essa disciplina de triagem é o que separa empresas com taxa de vitória de 8% (participam de tudo, ganham pouco) das com 25% (escolhem 20% dos editais, convertem com disciplina). O{' '}
        <Link href="/">SmartLic</Link>{' '}
        automatiza as três camadas acima (PAC crawler, histórico para benchmark, triagem em 4 fatores), com 14 dias de trial gratuito — a maioria das empresas B2G recupera o custo em um único contrato ganho no primeiro mês.
      </p>

      <p className="!mt-12 text-sm text-ink-secondary italic not-prose">
        Guia atualizado para abril de 2026. A API do PNCP segue em evolução; mudanças relevantes são documentadas em{' '}
        <ExternalLink href="https://pncp.gov.br/api/consulta/">pncp.gov.br/api/consulta</ExternalLink>.
      </p>
    </>
  );
}
