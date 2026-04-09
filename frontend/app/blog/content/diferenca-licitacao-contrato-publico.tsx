import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO-12.3.3 Art-03: Diferença entre licitação e contrato público
 * Content cluster: contratos públicos
 * Target: ~2,500 words | Primary KW: diferença licitação contrato público
 */
export default function DiferencaLicitacaoContratoPublico() {
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
                name: 'Qual a diferença entre licitação e contrato público?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A licitação é o procedimento administrativo pelo qual o poder público seleciona a proposta mais vantajosa para celebrar um contrato. Ela começa com a publicação do edital e termina com a adjudicação e homologação do resultado. Já o contrato público é o instrumento jurídico que formaliza a relação entre o vencedor da licitação e o órgão público, estabelecendo obrigações, prazos, valores e penalidades. Em síntese: a licitação é o processo de seleção; o contrato é o acordo resultante desse processo.',
                },
              },
              {
                '@type': 'Question',
                name: 'A licitação sempre gera um contrato público?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Não necessariamente. Em casos de dispensa ou inexigibilidade de licitação (arts. 74 e 79 da Lei 14.133/2021), o contrato pode ser firmado diretamente sem processo licitatório prévio. Além disso, uma licitação pode ser revogada ou anulada antes de chegar à fase contratual. Quando concluída regularmente, porém, a licitação sempre culmina em um contrato ou instrumento equivalente (nota de empenho, carta-contrato).',
                },
              },
              {
                '@type': 'Question',
                name: 'Quais são as modalidades de licitação previstas na Lei 14.133/2021?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 (Nova Lei de Licitações) prevê cinco modalidades: pregão (bens e serviços comuns), concorrência (obras, serviços especiais e concessões), concurso (trabalho técnico, científico ou artístico), leilão (alienação de bens) e diálogo competitivo (contratações inovadoras). A tomada de preços e o convite, previstos na Lei 8.666/1993, foram extintos para a maioria dos órgãos que já adotaram a nova lei.',
                },
              },
              {
                '@type': 'Question',
                name: 'Por quanto tempo um contrato público pode ser prorrogado?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Depende do tipo de contrato. Contratos de serviços contínuos podem ser prorrogados por até 5 anos (art. 106 da Lei 14.133/2021), podendo chegar a 10 anos em casos específicos. Contratos de fornecimento têm prazo máximo de 1 ano, prorrogável por igual período. Contratos de obras seguem o cronograma físico-financeiro, sem prazo máximo genérico, mas com restrições para aditivos acima de 25% do valor original. Contratos de serviços regulados e concessões podem ter até 35 anos.',
                },
              },
              {
                '@type': 'Question',
                name: 'Onde posso consultar licitações e contratos públicos em andamento?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O Portal Nacional de Contratações Públicas (PNCP) é o repositório oficial e obrigatório para todos os órgãos federais, estaduais e municipais que adotaram a Lei 14.133/2021. Nele é possível pesquisar editais de licitação em andamento, contratos firmados, atas de registro de preços e aditivos. Ferramentas como o SmartLic agregam e classificam esses dados com inteligência artificial, facilitando o monitoramento setorial.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Os termos &ldquo;licitação&rdquo; e &ldquo;contrato público&rdquo; são frequentemente
        utilizados de forma intercambiável no mercado de compras governamentais, mas
        representam etapas fundamentalmente distintas do processo de contratação pública.
        Compreender essa diferença não é apenas uma questão semântica: ela determina quais
        obrigações legais se aplicam a cada fase, quais documentos são necessários e quais
        riscos a empresa assume em cada momento. Este artigo esclarece a distinção de forma
        prática, com base na Lei 14.133/2021, e mostra como monitorar ambos os processos
        de forma eficiente.
      </p>

      <h2>O que é uma licitação pública</h2>

      <p>
        A licitação é o procedimento administrativo pelo qual a administração pública
        — federal, estadual ou municipal — seleciona a proposta mais vantajosa para adquirir
        bens, contratar serviços ou executar obras. Trata-se de um processo competitivo,
        regulamentado pela Lei 14.133/2021, que substituiu a Lei 8.666/1993 como marco
        legal das contratações públicas no Brasil.
      </p>

      <p>
        O objetivo central da licitação é garantir isonomia entre os participantes, promover
        competição e assegurar que os recursos públicos sejam aplicados da forma mais
        eficiente possível. Na prática, a licitação funciona como um processo seletivo em
        que empresas interessadas apresentam suas propostas e o órgão público avalia qual
        atende melhor aos critérios estabelecidos no edital.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Modalidades de licitação na Lei 14.133/2021
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>Pregão eletrônico:</strong> modalidade mais utilizada, obrigatória para bens e serviços comuns. Mais de 70% dos processos no PNCP.</li>
          <li><strong>Concorrência:</strong> para obras, serviços de engenharia e contratações de maior complexidade técnica.</li>
          <li><strong>Concurso:</strong> para seleção de trabalho técnico, científico ou artístico, mediante prêmio ou remuneração.</li>
          <li><strong>Leilão:</strong> para alienação de bens inservíveis ou legalmente apreendidos.</li>
          <li><strong>Diálogo competitivo:</strong> novidade da Lei 14.133, para objetos que envolvam inovação tecnológica ou técnica.</li>
        </ul>
      </div>

      <h3>Fases da licitação</h3>

      <p>
        O processo licitatório percorre etapas bem definidas: planejamento (estudo técnico
        preliminar e termo de referência), publicação do edital, fase de propostas, habilitação,
        julgamento, recursos, adjudicação e homologação. A adjudicação é o ato pelo qual a
        autoridade competente atribui o objeto da licitação ao vencedor. A homologação
        confirma a regularidade de todo o procedimento.
      </p>

      <p>
        Nem toda licitação resulta em contrato. A administração pode revogar o certame por
        motivo de interesse público superveniente ou anulá-lo por vício de legalidade,
        conforme Art. 71 da Lei 14.133/2021. Para o fornecedor, isso significa que o
        investimento em elaboração de proposta não garante, por si só, a celebração do
        contrato.
      </p>

      <h2>O que é um contrato público</h2>

      <p>
        O contrato público é o instrumento jurídico que formaliza a relação entre o
        órgão contratante e o fornecedor selecionado. Diferentemente da licitação — que é
        um processo seletivo — o contrato é um acordo bilateral que cria direitos e
        obrigações para ambas as partes.
      </p>

      <p>
        O contrato público é regido pelos artigos 89 a 154 da Lei 14.133/2021 e deve
        conter cláusulas essenciais: objeto, regime de execução, preço, condições de
        pagamento, prazos, penalidades, condições de rescisão e vinculação ao edital
        original. A ausência de qualquer cláusula essencial pode tornar o contrato nulo.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Tipos de contrato público
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>Contrato de fornecimento:</strong> aquisição de bens, com entrega única ou parcelada.</li>
          <li><strong>Contrato de prestação de serviços:</strong> execução de atividades específicas, com ou sem dedicação exclusiva de mão de obra.</li>
          <li><strong>Contrato de serviço continuado:</strong> atividades de natureza permanente (limpeza, vigilância, manutenção), prorrogáveis por até 10 anos.</li>
          <li><strong>Contrato de obra:</strong> execução de construção, reforma ou ampliação de edificação ou infraestrutura.</li>
          <li><strong>Ata de registro de preços:</strong> compromisso de fornecimento futuro a preço registrado, sem obrigação de compra imediata.</li>
        </ul>
      </div>

      <h3>Quando o contrato é dispensado</h3>

      <p>
        Nem toda contratação pública exige instrumento contratual formal. A Lei 14.133/2021
        permite que contratações de pequeno valor sejam formalizadas por nota de empenho
        ou ordem de serviço, dispensando o contrato escrito. Isso ocorre tipicamente em
        compras diretas com dispensa de licitação (Art. 75), como aquisições de até
        R$ 50 mil para bens ou R$ 100 mil para serviços e obras de engenharia.
      </p>

      <BlogInlineCTA slug="diferenca-licitacao-contrato-publico" campaign="contratos" />

      <h2>Comparação prática: licitação versus contrato</h2>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Licitação versus contrato: diferenças essenciais
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>Natureza:</strong> licitação é processo seletivo; contrato é acordo bilateral.</li>
          <li><strong>Objetivo:</strong> licitação seleciona a melhor proposta; contrato formaliza a execução.</li>
          <li><strong>Participantes:</strong> na licitação, qualquer empresa habilitada pode concorrer; no contrato, apenas o vencedor ou adjudicatário.</li>
          <li><strong>Duração:</strong> licitação tem prazo para cada fase (publicação, propostas, recursos); contrato tem vigência definida.</li>
          <li><strong>Obrigações financeiras:</strong> durante a licitação, o custo é de elaboração de proposta; no contrato, há obrigação de execução e direito a pagamento.</li>
          <li><strong>Penalidades:</strong> na licitação, impedimento de licitar (Art. 156, III); no contrato, multas, suspensão e declaração de inidoneidade.</li>
          <li><strong>Alteração:</strong> o edital pode ser alterado antes da data de abertura; o contrato admite aditivos limitados (25% para acréscimos, 25% para supressões).</li>
          <li><strong>Base legal:</strong> licitação: Art. 1 a 88 da Lei 14.133; contrato: Art. 89 a 154.</li>
        </ul>
      </div>

      <h2>O caminho completo: da publicação ao contrato</h2>

      <p>
        Para um fornecedor que vende ao governo, o ciclo completo de uma oportunidade
        segue uma sequência previsível:
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Fluxo completo: da publicação do edital ao contrato
        </p>
        <ol className="space-y-2 text-sm text-ink-secondary list-decimal list-inside">
          <li><strong>Publicação do edital:</strong> o órgão publica o edital no PNCP e em diário oficial.</li>
          <li><strong>Fase de propostas:</strong> empresas interessadas analisam o edital e enviam propostas.</li>
          <li><strong>Julgamento:</strong> análise das propostas conforme critérios do edital (menor preço, técnica e preço, maior desconto).</li>
          <li><strong>Habilitação:</strong> verificação da documentação jurídica, fiscal, econômica e técnica do vencedor.</li>
          <li><strong>Adjudicação:</strong> o objeto é atribuído ao vencedor pelo pregoeiro ou comissão.</li>
          <li><strong>Homologação:</strong> a autoridade superior confirma a regularidade de todo o processo.</li>
          <li><strong>Celebração do contrato:</strong> assinatura do instrumento contratual entre as partes.</li>
          <li><strong>Execução:</strong> fornecimento do bem ou prestação do serviço, com fiscalização do órgão.</li>
          <li><strong>Pagamento:</strong> liquidação da despesa e pagamento conforme cronograma contratual.</li>
        </ol>
      </div>

      <p>
        Cada etapa tem prazos legais e possibilidade de recurso administrativo. O intervalo
        entre a publicação do edital e a assinatura do contrato pode variar de 15 dias
        (pregão eletrônico para bens comuns) a vários meses (concorrência para obras
        complexas). Monitorar esse ciclo é essencial para empresas que participam de
        múltiplas oportunidades simultaneamente.
      </p>

      <h2>Por que essa distinção importa para fornecedores</h2>

      <p>
        Confundir licitação com contrato leva a erros estratégicos comuns. O primeiro é
        tratar a adjudicação como certeza de receita: até que o contrato seja assinado e
        a ordem de serviço emitida, não há obrigação de pagamento por parte do órgão.
        O segundo é ignorar a fase contratual: muitas empresas investem pesadamente na
        conquista de editais, mas negligenciam a gestão do contrato, incorrendo em
        penalidades por atraso, descumprimento de escopo ou falhas na documentação fiscal.
      </p>

      <p>
        Para empresas que atuam no mercado B2G (Business-to-Government), entender essa
        distinção permite separar claramente o funil comercial: a fase de prospecção e
        proposta (licitação) e a fase de execução e receita (contrato). Plataformas como
        o SmartLic permitem monitorar ambos os estágios em um{' '}
        <Link href="/pipeline" className="text-brand-blue hover:underline">
          pipeline de oportunidades
        </Link>{' '}
        unificado.
      </p>

      <h2>Como monitorar licitações e contratos</h2>

      <p>
        O PNCP (Portal Nacional de Contratações Públicas) é a fonte oficial para ambos:
        licitações são publicadas na seção de contratações, e contratos na seção de
        contratos. No entanto, navegar pelo portal manualmente é demorado e limitado
        em termos de filtros.
      </p>

      <p>
        O SmartLic agrega dados do PNCP e de outras fontes para oferecer uma visão
        consolidada. As{' '}
        <Link href="/licitacoes" className="text-brand-blue hover:underline">
          licitações por setor
        </Link>{' '}
        permitem identificar oportunidades abertas, enquanto os{' '}
        <Link href="/contratos" className="text-brand-blue hover:underline">
          contratos por setor e estado
        </Link>{' '}
        revelam o histórico de contratações de cada órgão. Cruzar essas duas dimensões
        gera inteligência competitiva: saber quem compra, quanto paga e com que frequência
        renova contratos.
      </p>

      <p>
        Para análises setoriais detalhadas, consulte os guias por setor:{' '}
        <Link href="/blog/contratos/saude" className="text-brand-blue hover:underline">
          contratos de saúde
        </Link>,{' '}
        <Link href="/blog/contratos/engenharia" className="text-brand-blue hover:underline">
          contratos de engenharia
        </Link>{' '}
        e{' '}
        <Link href="/blog/contratos/ti" className="text-brand-blue hover:underline">
          contratos de TI
        </Link>.
      </p>

      <h2>Perguntas Frequentes</h2>

      <h3>Qual a diferença entre licitação e contrato público?</h3>
      <p>
        A licitação é o processo administrativo pelo qual a administração pública seleciona
        a proposta mais vantajosa para contratar obras, serviços, compras ou alienações.
        O contrato público é o instrumento jurídico que formaliza a relação entre o órgão
        contratante e o fornecedor vencedor da licitação, estabelecendo direitos, obrigações,
        prazos e penalidades.
      </p>

      <h3>Uma licitação sempre resulta em contrato?</h3>
      <p>
        Não necessariamente. A licitação pode ser revogada por interesse público ou anulada
        por vício de legalidade, conforme previsto no Art. 71 da Lei 14.133/2021. Mesmo após
        a adjudicação, a administração pode optar por não celebrar o contrato se houver motivos
        justificados. Além disso, compras de pequeno valor podem ser formalizadas por nota de
        empenho, dispensando o instrumento contratual.
      </p>

      <h3>Quais são as modalidades de licitação na Lei 14.133/2021?</h3>
      <p>
        A Lei 14.133/2021 prevê cinco modalidades: pregão (eletrônico ou presencial),
        concorrência, concurso, leilão e diálogo competitivo. O pregão eletrônico é a
        modalidade mais utilizada, representando mais de 70% dos processos registrados
        no PNCP.
      </p>

      <h3>Qual a duração máxima de um contrato público?</h3>
      <p>
        A duração depende do tipo de contrato. Contratos de serviços continuados podem ter
        vigência de até 5 anos, prorrogáveis por até 10 anos no total (Art. 106 e 107 da Lei
        14.133/2021). Contratos vinculados a créditos orçamentários seguem o exercício
        financeiro. Contratos de parceria público-privada podem chegar a 35 anos.
      </p>

      <h3>Onde consultar licitações e contratos públicos?</h3>
      <p>
        O Portal Nacional de Contratações Públicas (PNCP) é a plataforma oficial para
        consulta de licitações e contratos de todos os entes federativos, conforme Art. 174
        da Lei 14.133/2021. Plataformas especializadas como o{' '}
        <Link href="/contratos" className="text-brand-blue hover:underline">
          SmartLic
        </Link>{' '}
        agregam dados do PNCP e de outras fontes, aplicando classificação setorial
        por IA para facilitar a busca.
      </p>
    </>
  );
}
