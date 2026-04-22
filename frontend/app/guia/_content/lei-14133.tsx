import Link from 'next/link';

export const sections = [
  { id: 'contexto', title: 'Contexto e origem da Lei 14.133' },
  { id: 'vigencia', title: 'Vigência e transição' },
  { id: 'principios', title: 'Princípios (art. 5º)' },
  { id: 'agente-contratacao', title: 'Agente de contratação' },
  { id: 'modalidades', title: 'Modalidades e critérios de julgamento' },
  { id: 'fases', title: 'Fases do procedimento' },
  { id: 'habilitacao', title: 'Habilitação (arts. 62-70)' },
  { id: 'contratos', title: 'Execução contratual (arts. 90-121)' },
  { id: 'matriz-risco', title: 'Matriz de risco e reequilíbrio' },
  { id: 'sancoes', title: 'Sanções administrativas (arts. 155-163)' },
  { id: 'diferencas-8666', title: 'Principais diferenças da Lei 8.666/93' },
  { id: 'impacto-fornecedor', title: 'Impacto prático para fornecedores' },
];

const ExternalLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <a href={href} target="_blank" rel="noopener noreferrer">
    {children}
  </a>
);

export default function Lei14133Content() {
  return (
    <>
      <p className="text-xl leading-relaxed text-ink font-medium !mt-0">
        A Lei 14.133/2021, publicada em 1º de abril de 2021 e vigente integralmente desde 30/12/2023, é o novo regime jurídico único de licitações e contratos administrativos no Brasil. Substituiu a Lei 8.666/93, a Lei do Pregão (10.520/02) e o Regime Diferenciado de Contratações (RDC). Para empresas B2G, é a regra de todas as oportunidades abertas a partir do final de 2023 — e entender suas mudanças estruturais é pré-requisito para atuar no mercado de compras públicas.
      </p>

      <h2 id="contexto">Contexto e origem da Lei 14.133</h2>
      <p>
        A Lei 8.666/93 carregava 30 anos de jurisprudência, vícios operacionais (certames morosos, comissões colegiadas lentas, excesso formal) e fragmentação legislativa (Pregão em lei separada, RDC em outra). A proposta que gerou a 14.133 tramitou por mais de 5 anos no Congresso com objetivo de unificar e modernizar: um único diploma para regular todo o processo de contratação pública, com ênfase em governança, planejamento e eficiência.
      </p>
      <p>
        O texto final, aprovado após vetos e sanções parciais, consolidou três inovações estruturais: (i) pregão como modalidade padrão para bens e serviços comuns (não mais em lei separada); (ii) introdução do diálogo competitivo, inspirado no EU Procurement Directive; (iii) deslocamento de responsabilidade da comissão colegiada para um agente de contratação individual. O{' '}
        <ExternalLink href="https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm">texto integral está no Planalto</ExternalLink>.
      </p>

      <h2 id="vigencia">Vigência e transição</h2>
      <p>
        A 14.133 entrou em vigor na publicação (abril de 2021), mas com período de transição em que a administração podia optar entre o regime antigo e o novo. O marco decisivo foi 30/12/2023: desde essa data, toda nova licitação deve seguir a 14.133. Contratos firmados anteriormente continuam regidos pela legislação anterior — as Leis 8.666/93, 10.520/02 e 12.462/11 (RDC) foram integralmente revogadas para novos atos, mas sobrevivem para contratos em curso.
      </p>
      <p>
        Consequência prática para empresas: em 2026 ainda é possível encontrar contratos longos executados sob a 8.666 (por exemplo, contratos de 36 meses iniciados em 2022), enquanto 100% dos editais novos estão sob a 14.133. A curva de adaptação é, portanto, dupla — operar contratos antigos e novos em paralelo por alguns anos ainda.
      </p>

      <h2 id="principios">Princípios (art. 5º)</h2>
      <p>
        O artigo 5º da Lei 14.133 lista 22 princípios, um catálogo mais extenso do que a 8.666 previa. Os 5 com maior impacto operacional para fornecedores:
      </p>
      <ul>
        <li>
          <strong>Planejamento:</strong> administração deve publicar plano anual de contratações (PAC). Empresas que monitoram PAC antecipam oportunidades futuras com 6-12 meses de lead time.
        </li>
        <li>
          <strong>Transparência:</strong> publicação obrigatória no{' '}
          <ExternalLink href="https://pncp.gov.br/">PNCP</ExternalLink>{' '}
          de todos os atos. Ausência de publicação = nulidade.
        </li>
        <li>
          <strong>Segregação de funções:</strong> quem planeja não executa, quem executa não fiscaliza. Reduz conluio, aumenta rastreabilidade.
        </li>
        <li>
          <strong>Vinculação ao edital:</strong> edital é contrato pré-firmado. Qualquer alteração unilateral gera nulidade impugnável (ver{' '}
          <Link href="/blog/impugnacao-edital-quando-como-contestar">guia de impugnação</Link>).
        </li>
        <li>
          <strong>Economicidade:</strong> melhor proposta, não necessariamente menor preço. Tecnicismo e qualidade são avaliáveis.
        </li>
      </ul>

      <h2 id="agente-contratacao">Agente de contratação</h2>
      <p>
        Uma das mudanças estruturais mais importantes: a 14.133 substitui a Comissão Permanente de Licitação (CPL) da 8.666 pelo agente de contratação, um servidor efetivo designado para conduzir individualmente o certame, assessorado por equipe de apoio quando necessário. O benefício esperado é celeridade — um servidor decide, não uma comissão colegiada que precisa reunir-se.
      </p>
      <p>
        Para fornecedores, isso significa mudança no canal de interlocução: dúvidas, impugnações e recursos agora endereçados ao agente nomeado, cujo nome consta do edital. Conhecer o perfil do agente (rigor de condução, histórico de julgamentos) passa a ser parte da estratégia pré-certame.
      </p>

      <h2 id="modalidades">Modalidades e critérios de julgamento</h2>
      <p>
        São cinco modalidades (art. 28): pregão, concorrência, diálogo competitivo, concurso, leilão. Seis critérios de julgamento (art. 33): menor preço, maior desconto, melhor técnica, técnica e preço, maior retorno econômico, maior oferta de preço (para alienações). Para detalhes operacionais, ver{' '}
        <Link href="/guia/licitacoes">guia geral de licitações</Link>.
      </p>
      <p>
        Três pontos que mudam o dia-a-dia do fornecedor:
      </p>
      <ul>
        <li>
          <strong>Pregão como padrão:</strong> para bens e serviços comuns, pregão é a primeira opção regulatória. Apenas justificativa fundamentada permite outra modalidade.
        </li>
        <li>
          <strong>Maior desconto:</strong> novo critério aplicável a compras em lotes, medido percentualmente sobre valor de referência. Demanda contabilidade diferenciada para formação de proposta.
        </li>
        <li>
          <strong>Maior retorno econômico:</strong> critério aplicável a contratos de eficiência (ESCO, por exemplo). A remuneração do contratado vem da economia gerada — modelo performance-based.
        </li>
      </ul>

      <h2 id="fases">Fases do procedimento</h2>
      <p>
        O art. 17 estabelece a sequência obrigatória, com uma inovação importante: a inversão de fases (proposta antes da habilitação) que já era padrão no pregão tornou-se regra geral. As fases:
      </p>
      <ol>
        <li>
          <strong>Preparatória:</strong> estudo técnico preliminar, termo de referência ou projeto básico, matriz de risco (em contratos complexos).
        </li>
        <li>
          <strong>Divulgação do edital:</strong> publicação no PNCP, prazo mínimo conforme art. 55.
        </li>
        <li>
          <strong>Apresentação de propostas e lances:</strong> sessão pública, disputa em ambiente eletrônico.
        </li>
        <li>
          <strong>Julgamento:</strong> classificação pelo critério do edital, análise da exequibilidade.
        </li>
        <li>
          <strong>Habilitação:</strong> apenas do vencedor provisório (regra geral, salvo inversão justificada).
        </li>
        <li>
          <strong>Recursal:</strong> prazos únicos conforme art. 165-167.
        </li>
        <li>
          <strong>Homologação e adjudicação:</strong> pela autoridade superior.
        </li>
      </ol>

      <h2 id="habilitacao">Habilitação (arts. 62-70)</h2>
      <p>
        A 14.133 divide habilitação em quatro blocos, cada um detalhado em artigo específico. Para o checklist operacional atualizado, ver{' '}
        <Link href="/blog/checklist-habilitacao-licitacao-2026">checklist de habilitação 2026</Link>. Resumo:
      </p>
      <ul>
        <li>
          <strong>Art. 66 — Jurídica:</strong> ato constitutivo atualizado.
        </li>
        <li>
          <strong>Art. 67 — Técnica:</strong> atestados de capacidade técnica e registros em conselhos.
        </li>
        <li>
          <strong>Art. 68 — Fiscal, social e trabalhista:</strong> CNPJ, certidões federal/estadual/municipal, FGTS, CNDT.
        </li>
        <li>
          <strong>Art. 69 — Econômico-financeira:</strong> balanço patrimonial, índices, garantias.
        </li>
      </ul>
      <p>
        Inovação da 14.133: a administração pode, em certames de alto valor ou risco, exigir critérios adicionais (capital social mínimo, patrimônio líquido, fidelidade técnica). Fornecedores que aspiram a contratos acima de R$ 5 milhões precisam estruturar balanço para atender a esses índices.
      </p>

      <h2 id="contratos">Execução contratual (arts. 90-121)</h2>
      <p>
        A seção contratual da 14.133 é mais extensa que a da 8.666, com ênfase em governança de execução. Tópicos-chave:
      </p>
      <ul>
        <li>
          <strong>Vigência (art. 105-107):</strong> regra de 5 anos para serviços continuados, com possibilidade de prorrogação. Aquisições episódicas seguem o cronograma do objeto.
        </li>
        <li>
          <strong>Subcontratação (art. 122):</strong> permitida quando prevista no edital, com limites percentuais definidos.
        </li>
        <li>
          <strong>Alterações contratuais (art. 124-128):</strong> limite de 25% para alterações unilaterais (acréscimos/supressões). Além disso, é necessário aditivo bilateral.
        </li>
        <li>
          <strong>Reajuste e reequilíbrio (art. 134-137):</strong> reajuste por índice contratual (IPCA, INCC, etc.). Reequilíbrio econômico-financeiro requer prova de evento superveniente imprevisível.
        </li>
        <li>
          <strong>Recebimento (art. 140):</strong> provisório e definitivo, com prazos específicos. Não recebimento justificado libera a administração do pagamento.
        </li>
      </ul>

      <h2 id="matriz-risco">Matriz de risco e reequilíbrio</h2>
      <p>
        Em contratos complexos (obras, serviços de engenharia de grande vulto, contratos de concessão), a 14.133 torna obrigatória a matriz de risco, documento anexo ao contrato que define qual parte (administração ou contratada) assume cada risco identificado: variação cambial, atraso de licenças, interferência arqueológica, alteração regulatória, caso fortuito/força maior.
      </p>
      <p>
        Consequência para precificação: a matriz expõe riscos antes opacos. Fornecedores agora precificam explicitamente esses riscos nas propostas (via BDI, reservas de contingência, seguros). Consultar{' '}
        <Link href="/blog/como-calcular-preco-proposta-licitacao">guia de precificação de proposta</Link>{' '}
        para a metodologia sob a 14.133.
      </p>

      <h2 id="sancoes">Sanções administrativas (arts. 155-163)</h2>
      <p>
        A 14.133 expandiu o catálogo sancionatório e formalizou critérios de dosimetria. As sanções, em gradação:
      </p>
      <ul>
        <li>
          <strong>Advertência:</strong> infrações leves, sem dano.
        </li>
        <li>
          <strong>Multa:</strong> percentual sobre valor do contrato, conforme regulamento.
        </li>
        <li>
          <strong>Impedimento de licitar e contratar com o ente sancionador:</strong> até 3 anos.
        </li>
        <li>
          <strong>Declaração de inidoneidade:</strong> até 6 anos, com efeito em todos os entes federativos. Reabilitação depende de ressarcimento de prejuízos.
        </li>
      </ul>
      <p>
        Para empresas B2G, isso eleva o rigor de compliance: um único descumprimento em contrato pequeno pode gerar impedimento que inviabiliza pipeline inteiro. Governança de execução contratual deixou de ser opcional.
      </p>

      <h2 id="diferencas-8666">Principais diferenças da Lei 8.666/93</h2>
      <table>
        <thead>
          <tr>
            <th>Dimensão</th>
            <th>Lei 8.666/93</th>
            <th>Lei 14.133/2021</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Modalidade padrão</td>
            <td>Concorrência (bens/serviços comuns em lei à parte)</td>
            <td>Pregão eletrônico</td>
          </tr>
          <tr>
            <td>Condução do certame</td>
            <td>Comissão Permanente de Licitação</td>
            <td>Agente de contratação (individual)</td>
          </tr>
          <tr>
            <td>Diálogo competitivo</td>
            <td>Inexistente</td>
            <td>Art. 32 — aplicável a contratações complexas</td>
          </tr>
          <tr>
            <td>Matriz de risco</td>
            <td>Facultativa, pouco usada</td>
            <td>Obrigatória em contratos complexos</td>
          </tr>
          <tr>
            <td>Critérios de julgamento</td>
            <td>Menor preço, melhor técnica, técnica e preço</td>
            <td>Acima + maior desconto + maior retorno econômico</td>
          </tr>
          <tr>
            <td>Canal de publicação</td>
            <td>DOU, jornal de grande circulação, sites próprios</td>
            <td>PNCP (canal único obrigatório)</td>
          </tr>
          <tr>
            <td>Impedimento de licitar</td>
            <td>Até 2 anos (Lei 10.520 — pregão)</td>
            <td>Até 3 anos, com critérios de dosimetria</td>
          </tr>
          <tr>
            <td>Inidoneidade</td>
            <td>Prazo indeterminado por reabilitação</td>
            <td>Até 6 anos, com critérios objetivos</td>
          </tr>
        </tbody>
      </table>

      <h2 id="impacto-fornecedor">Impacto prático para fornecedores</h2>
      <p>
        Empresas que já atuavam sob a 8.666 e migram para a 14.133 tipicamente enfrentam três adaptações: (1) revisão de templates de proposta para incluir matriz de risco quando aplicável, (2) ajuste de contabilidade para atender índices mais rigorosos de habilitação econômico-financeira, (3) fortalecimento de governança contratual para evitar descumprimentos que, sob a 14.133, sancionam com maior severidade.
      </p>
      <p>
        Empresas novas no mercado B2G não enfrentam esse atrito — começam já estruturadas para a 14.133. O desafio é diferente: construir rápido o cadastro SICAF, obter os primeiros atestados de capacidade técnica (muitas vezes via contratos menores que servem de portfólio), e estabelecer processo de triagem de editais com o volume hoje disponível no{' '}
        <Link href="/guia/pncp">PNCP</Link>.
      </p>
      <p>
        Para erros típicos específicos do primeiro ano sob a 14.133, ver{' '}
        <Link href="/blog/erro-operacional-perder-contratos-publicos">erros operacionais que fazem empresas perderem contratos</Link>. Para estratégia de escolha de editais sob o novo regime, ver{' '}
        <Link href="/blog/escolher-editais-maior-probabilidade-vitoria">como escolher editais com maior probabilidade de vitória</Link>.
      </p>

      <p className="!mt-12 text-sm text-ink-secondary italic not-prose">
        Guia atualizado para 2026. A Lei 14.133 ainda recebe regulamentações complementares — acompanhe em{' '}
        <ExternalLink href="https://portal.tcu.gov.br/">portal.tcu.gov.br</ExternalLink>{' '}
        e na página oficial do{' '}
        <ExternalLink href="https://pncp.gov.br/">PNCP</ExternalLink>.
      </p>
    </>
  );
}
