import Link from 'next/link';

export const sections = [
  { id: 'o-que-e-licitacao', title: 'O que é uma licitação' },
  { id: 'por-que-o-governo-licita', title: 'Por que o governo precisa licitar' },
  { id: 'modalidades', title: 'Modalidades da Lei 14.133' },
  { id: 'como-participar', title: 'Como participar — passo a passo' },
  { id: 'habilitacao', title: 'Documentação e habilitação' },
  { id: 'lei-14133-vs-8666', title: 'Lei 14.133 vs Lei 8.666' },
  { id: 'pncp', title: 'PNCP: porta de entrada atual' },
  { id: 'erros-comuns', title: 'Erros comuns de iniciantes' },
  { id: 'vale-a-pena', title: 'Quando vale a pena participar' },
  { id: 'ferramentas', title: 'Ferramentas que automatizam' },
];

const ExternalLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <a href={href} target="_blank" rel="noopener noreferrer">
    {children}
  </a>
);

export default function LicitacoesContent() {
  return (
    <>
      <p className="text-xl leading-relaxed text-ink font-medium !mt-0">
        Licitação pública é o processo administrativo pelo qual órgãos governamentais selecionam a proposta mais vantajosa para contratar bens, serviços ou obras, garantindo isonomia entre fornecedores e economicidade para o Estado. Este guia reúne tudo o que uma empresa brasileira precisa saber em 2026 para participar com segurança: modalidades, documentação, fluxo operacional, erros típicos e ferramentas que transformam ruído em pipeline qualificado.
      </p>

      <h2 id="o-que-e-licitacao">O que é uma licitação pública?</h2>
      <p>
        A licitação é a forma que a administração pública encontrou para comprar sem privilegiar ninguém. Toda vez que uma prefeitura precisa contratar limpeza predial, um hospital federal precisa de insumos, ou um ministério precisa de um sistema de TI, o caminho obrigatório passa por um edital público que descreve o que se quer comprar e define regras claras para quem quiser vender.
      </p>
      <p>
        Os princípios fundamentais estão no artigo 5º da{' '}
        <ExternalLink href="https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm">Lei 14.133/2021</ExternalLink>:
        legalidade, impessoalidade, moralidade, publicidade, eficiência, interesse público, probidade administrativa, igualdade, planejamento, transparência, eficácia, segregação de funções, motivação, vinculação ao edital, julgamento objetivo, segurança jurídica, razoabilidade, competitividade, proporcionalidade, celeridade, economicidade e desenvolvimento nacional sustentável. Cada um tem desdobramentos práticos que afetam como sua empresa deve se comportar no certame.
      </p>

      <h2 id="por-que-o-governo-licita">Por que o governo precisa licitar?</h2>
      <p>
        A Constituição Federal, no artigo 37, inciso XXI, estabelece que &ldquo;ressalvados os casos especificados na legislação, as obras, serviços, compras e alienações serão contratados mediante processo de licitação pública que assegure igualdade de condições a todos os concorrentes&rdquo;. Isso significa que comprar sem licitar é exceção — e as exceções (dispensa e inexigibilidade) têm requisitos rígidos de justificativa e limites de valor.
      </p>
      <p>
        Do ponto de vista do fornecedor, é aqui que nasce a oportunidade: o governo brasileiro movimenta aproximadamente R$ 800 bilhões por ano em compras públicas, segundo dados do{' '}
        <ExternalLink href="https://pncp.gov.br/">PNCP</ExternalLink>. Empresas que dominam o processo acessam um mercado com pagamento garantido em lei, contratos de longa duração e previsibilidade regulatória — exatamente o tipo de cliente que o mercado privado raramente oferece em volume comparável.
      </p>

      <h2 id="modalidades">Modalidades previstas na Lei 14.133/2021</h2>
      <p>
        A Nova Lei de Licitações unificou e simplificou o regime jurídico. São cinco modalidades, cada uma aplicável a situações específicas. Entender qual modalidade se aplica é pré-requisito para saber se sua empresa deve participar:
      </p>

      <h3>Pregão (eletrônico e presencial)</h3>
      <p>
        Modalidade padrão para aquisição de bens e serviços comuns — aqueles cujos padrões de desempenho e qualidade podem ser objetivamente definidos no edital. É de longe a mais utilizada no Brasil em 2026 devido à celeridade: procedimento inverso (proposta antes da habilitação) e disputa de lances em tempo real. O pregão eletrônico é a regra; o presencial é exceção justificada. Para o detalhe operacional, consulte o{' '}
        <Link href="/blog/pregao-eletronico-guia-passo-a-passo">guia de pregão eletrônico passo a passo</Link>.
      </p>

      <h3>Concorrência</h3>
      <p>
        Aplicável quando o objeto é complexo ou de grande vulto, especialmente obras e serviços de engenharia de grande porte. Admite os critérios de menor preço, melhor técnica, técnica e preço, maior desconto ou maior retorno econômico. Historicamente a modalidade &ldquo;pesada&rdquo; da 8.666, hoje preserva importância para contratos estratégicos.
      </p>

      <h3>Diálogo competitivo</h3>
      <p>
        Modalidade inédita introduzida pela 14.133 (art. 32) para contratações inovadoras ou complexas em que a administração não consegue pré-definir a solução ideal. O órgão dialoga com licitantes previamente selecionados para desenvolver alternativas técnicas, e só depois dessa fase emite o documento descritivo que serve de base para as propostas finais. Na prática, é pouco usado fora de projetos de TI governamental estratégicos.
      </p>

      <h3>Concurso</h3>
      <p>
        Modalidade para escolha de trabalho técnico, científico ou artístico, cuja remuneração se dá por prêmios ou remuneração aos vencedores. Aplicação mais comum: seleção de projetos arquitetônicos, premiações de pesquisa, editais culturais.
      </p>

      <h3>Leilão</h3>
      <p>
        Usado para alienação de bens móveis inservíveis, produtos apreendidos, bens imóveis cuja alienação esteja justificada. Menos relevante para fornecedores comuns, mais importante para quem compra materiais ou ativos públicos.
      </p>

      <p>
        Uma leitura crítica das 5 modalidades mostra: <strong>95%+ do mercado B2G brasileiro resume-se a pregão eletrônico</strong>. Se sua empresa vende bens comuns (material de escritório, equipamentos médicos padrão, serviços de limpeza e vigilância, licenças de software homologadas) ou serviços comuns, concentre esforço operacional nessa modalidade.
      </p>

      <h2 id="como-participar">Como participar de uma licitação — passo a passo</h2>
      <ol>
        <li>
          <strong>Prepare-se formalmente:</strong> obtenha CNPJ ativo, registro junto ao{' '}
          <ExternalLink href="https://www.gov.br/compras/pt-br">SICAF (Compras.gov.br)</ExternalLink>{' '}
          para certames federais, e estude as certidões negativas exigidas (veja{' '}
          <Link href="/blog/sicaf-como-cadastrar-manter-ativo-2026">guia do SICAF em 2026</Link>).
        </li>
        <li>
          <strong>Monitore editais relevantes:</strong> consulte o{' '}
          <ExternalLink href="https://pncp.gov.br/">PNCP</ExternalLink>{' '}
          diariamente (ou use uma plataforma que automatize isso — a variável de tempo é o maior gargalo operacional em empresas B2G novatas). Veja{' '}
          <Link href="/blog/reduzir-tempo-analisando-editais-irrelevantes">como reduzir 80% do tempo analisando editais irrelevantes</Link>.
        </li>
        <li>
          <strong>Filtre por viabilidade:</strong> antes de abrir o edital completo, avalie 4 fatores rápidos: modalidade (é pregão?), prazo de apresentação (há tempo útil?), valor estimado (está no seu playing field?), geografia (entrega exequível?). Detalhes em{' '}
          <Link href="/blog/analise-viabilidade-editais-guia">guia de análise de viabilidade</Link>.
        </li>
        <li>
          <strong>Leia integralmente o edital e anexos:</strong> Termo de Referência, Projeto Básico, Planilha de Composição de Custos, Minuta de Contrato. 80% das desclassificações vêm de não atender a exigências que estavam no edital — apenas não foram lidas.
        </li>
        <li>
          <strong>Cadastre proposta no sistema correto:</strong> Compras.gov.br (federal), BNC/BLL/Licitanet (estaduais e municipais em geral), ou o sistema indicado no edital. Cada plataforma tem suas peculiaridades de upload, certificado digital, prazos.
        </li>
        <li>
          <strong>Participe da disputa:</strong> em pregões, esteja online no horário marcado, monitore lances, ofereça propostas coerentes com sua margem mínima. Veja{' '}
          <Link href="/blog/como-calcular-preco-proposta-licitacao">como calcular o preço da proposta</Link>.
        </li>
        <li>
          <strong>Habilitação:</strong> sendo vencedor provisório, envie toda a documentação exigida (jurídica, fiscal, técnica, econômico-financeira) nos prazos do edital. Qualquer falha aqui desclassifica. Consulte o{' '}
          <Link href="/blog/checklist-habilitacao-licitacao-2026">checklist de habilitação 2026</Link>.
        </li>
        <li>
          <strong>Adjudicação e contratação:</strong> após habilitação, o órgão adjudica e emite ordem de compra, nota de empenho ou contrato formal. Só nesse ponto sua empresa pode executar. Pagamento ocorre conforme cronograma contratual.
        </li>
      </ol>

      <h2 id="habilitacao">Documentação e habilitação</h2>
      <p>
        A Lei 14.133, nos artigos 62 a 70, divide a habilitação em quatro blocos. Cada um tem finalidade fiscalizatória distinta:
      </p>
      <ul>
        <li>
          <strong>Habilitação jurídica (art. 66):</strong> ato constitutivo, estatuto ou contrato social atualizado. Para sociedade por ações, documento de eleição dos administradores.
        </li>
        <li>
          <strong>Habilitação fiscal, social e trabalhista (art. 68):</strong> CNPJ, inscrição estadual/municipal, certidões negativas (Receita Federal, FGTS, CNDT, municipal, estadual), regularidade previdenciária.
        </li>
        <li>
          <strong>Habilitação técnica (art. 67):</strong> atestados de capacidade técnica (quem sua empresa já atendeu, com desempenho comprovado em objeto similar), registros em conselhos de classe quando aplicável (CREA, CRA, CRM etc.).
        </li>
        <li>
          <strong>Habilitação econômico-financeira (art. 69):</strong> balanço patrimonial do último exercício, índices de Liquidez Corrente, Liquidez Geral e Solvência Geral acima de 1 (regra geral), garantias quando exigidas.
        </li>
      </ul>
      <p>
        Três dicas operacionais que economizam dinheiro em 2026:
      </p>
      <ul>
        <li>Mantenha todas as certidões renovadas mensalmente com automação (calendário compartilhado + alerta 15 dias antes do vencimento).</li>
        <li>Arquive atestados de capacidade técnica digitalmente, em PDF pesquisável — vai precisar recuperar rápido em prazos curtos.</li>
        <li>Contabilidade que atende B2G precisa entregar balanço patrimonial com índices formatados conforme edital, não apenas DRE padrão.</li>
      </ul>

      <h2 id="lei-14133-vs-8666">Lei 14.133 vs Lei 8.666: principais mudanças</h2>
      <p>
        A Lei 8.666/93 foi integralmente revogada em 30/12/2023. Toda nova licitação aberta a partir dessa data segue a 14.133. Para um aprofundamento das mudanças, consulte o{' '}
        <Link href="/blog/lei-14133-guia-fornecedores">guia prático da Lei 14.133 para fornecedores</Link>. As diferenças de impacto operacional mais relevantes:
      </p>
      <ul>
        <li>
          <strong>Pregão como modalidade-padrão:</strong> na 8.666 era exceção regulada por lei separada (Lei 10.520/02); agora é a primeira opção regulatória para bens e serviços comuns.
        </li>
        <li>
          <strong>Agente de contratação substitui a Comissão:</strong> centralização de responsabilidade em um único servidor capacitado, com apoio de equipe quando necessário. Acelera decisões.
        </li>
        <li>
          <strong>Matriz de risco obrigatória em contratos complexos:</strong> define quem (administração ou contratada) arca com cada tipo de imprevisto. Reduz litígio futuro mas exige precificação mais cuidadosa.
        </li>
        <li>
          <strong>Diálogo competitivo:</strong> nova modalidade para soluções inovadoras (inspirada no EU Procurement Directive).
        </li>
        <li>
          <strong>Critérios de julgamento expandidos:</strong> maior desconto, maior retorno econômico, melhor técnica, técnica e preço, menor preço.
        </li>
        <li>
          <strong>Sanções mais severas:</strong> multa, impedimento de licitar (até 3 anos), declaração de inidoneidade (até 6 anos), tornando compliance B2G mais crítico.
        </li>
      </ul>

      <h2 id="pncp">Portal PNCP: a porta de entrada atual</h2>
      <p>
        O{' '}
        <ExternalLink href="https://pncp.gov.br/">PNCP (Portal Nacional de Contratações Públicas)</ExternalLink>{' '}
        é o canal único obrigatório, por força do art. 174 da Lei 14.133, para divulgação de editais, atas de registro de preço e contratos de todos os entes federativos. Em 2026, qualquer edital válido precisa estar publicado no PNCP para produzir efeitos — ausência de publicação significa certame nulo.
      </p>
      <p>
        Para empresas, isso traz três consequências práticas: (1) a busca de oportunidades concentra-se num portal único, (2) existe API pública gratuita que permite automação em larga escala, (3) o histórico é persistente, permitindo data-driven analysis de concorrentes, valores praticados, órgãos com maior frequência de compra. O{' '}
        <Link href="/guia/pncp">guia completo do PNCP</Link>{' '}
        detalha esse ecossistema.
      </p>

      <h2 id="erros-comuns">Erros comuns de iniciantes</h2>
      <ol>
        <li>
          <strong>Não ler o Termo de Referência:</strong> resposta: 80% das desclassificações. Edital é contrato pré-assinado. Ler por completo, incluindo anexos, é pré-requisito para propor preço.
        </li>
        <li>
          <strong>Precificar com planilha genérica:</strong> cada edital tem composição de custos específica. BDI, encargos sociais, insumos são customizáveis. Uma composição pobre deixa margem na mesa ou coloca a empresa em risco de execução negativa.
        </li>
        <li>
          <strong>Entregar certidão vencida:</strong> certidões têm validade (90 dias é comum). Em disputas longas, uma certidão pode vencer entre a proposta e a habilitação. Renovação proativa elimina o risco.
        </li>
        <li>
          <strong>Participar de tudo que aparece:</strong> triagem sem critério gera dispersão operacional e taxa de vitória baixa. Empresas B2G eficientes selecionam 15-25% dos editais mapeados como viáveis, recusando o resto — e ganham mais em absoluto. Ver{' '}
          <Link href="/blog/escolher-editais-maior-probabilidade-vitoria">como escolher editais com maior probabilidade de vitória</Link>.
        </li>
        <li>
          <strong>Não impugnar edital viciado:</strong> quando o edital tem restrição indevida, o prazo para impugnar é curto (tipicamente 3 dias úteis antes da abertura). Empresas que deixam passar aceitam tacitamente a restrição. Veja{' '}
          <Link href="/blog/impugnacao-edital-quando-como-contestar">guia de impugnação de edital</Link>.
        </li>
      </ol>

      <h2 id="vale-a-pena">Quando vale a pena participar?</h2>
      <p>
        A pergunta que separa empresas operacionalmente maduras das iniciantes é simples: &ldquo;esse edital tem viabilidade para nós, dado nosso perfil, capacidade e pipeline atual?&rdquo;. Um framework de 4 fatores útil em 2026, detalhado no{' '}
        <Link href="/blog/vale-a-pena-disputar-pregao">guia &ldquo;vale a pena disputar este pregão&rdquo;</Link>:
      </p>
      <ul>
        <li>
          <strong>Modalidade (30% do score):</strong> pregão eletrônico escalável. Concorrência lenta e complexa demanda BDI maior. Dispensa raramente vale tempo.
        </li>
        <li>
          <strong>Timeline (25%):</strong> prazo útil mínimo para proposta + entrega. Pregão com 7 dias de antecedência só vale se sua empresa já tem TR precificado para o setor.
        </li>
        <li>
          <strong>Valor estimado (25%):</strong> dentro do range histórico em que sua empresa opera lucrativa. Acima, risco de execução; abaixo, margem não compensa overhead administrativo.
        </li>
        <li>
          <strong>Geografia (20%):</strong> entrega em estado distante sem cadeia logística estruturada inverte a margem rapidamente.
        </li>
      </ul>
      <p>
        Editais que somam &lt;60% no score dos 4 fatores raramente compensam. Aplicar esse filtro na triagem aumenta taxa de vitória de 8% para 25% — o dobro de receita com o mesmo time operacional. Ver{' '}
        <Link href="/blog/como-aumentar-taxa-vitoria-licitacoes">como aumentar taxa de vitória</Link>.
      </p>

      <h2 id="ferramentas">Ferramentas que automatizam a busca</h2>
      <p>
        Empresas B2G que faturam consistentemente acima de R$ 5 milhões/ano em contratos públicos não monitoram PNCP manualmente. Elas usam plataformas que integram múltiplas fontes (PNCP + Compras.gov + Portal de Compras Públicas + sistemas estaduais), aplicam filtros setoriais por keywords e exclusões, rodam classificação de relevância com IA e entregam ao analista humano apenas os 5-10 editais do dia que realmente merecem leitura integral.
      </p>
      <p>
        O <Link href="/">SmartLic</Link> é a plataforma brasileira especializada nisso: busca multi-fonte com deduplicação por hash de conteúdo, classificação setorial GPT-4.1-nano (85%+ precisão), análise de viabilidade 4-fatores nativa, pipeline kanban para editais em tracking. 14 dias grátis, sem cartão — uma empresa B2G média recupera o custo da assinatura em um único contrato ganho no primeiro mês.
      </p>

      <p className="!mt-12 text-sm text-ink-secondary italic not-prose">
        Este guia é atualizado periodicamente com as mudanças regulatórias aplicáveis. Última revisão: abril de 2026.
      </p>
    </>
  );
}
