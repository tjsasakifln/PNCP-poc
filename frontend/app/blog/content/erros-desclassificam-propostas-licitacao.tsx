import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * Erros que Desclassificam Propostas em Licitações — Guia Completo
 *
 * Target: ~2800 words | Cluster: habilitação / pregão
 * Primary keyword: erros desclassificação proposta licitação
 */
export default function ErrosDesclassificamPropostasLicitacao() {
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
                name: 'Qual o erro mais comum que desclassifica propostas em licitações?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O erro mais frequente é a certidão de regularidade fiscal vencida — especialmente a Certidão de Regularidade do FGTS (validade 30 dias) e a Certidão Conjunta Receita/PGFN (validade 180 dias). Muitas empresas enviam proposta com documentação completa, mas o pregoeiro constata durante a fase de habilitação que uma certidão expirou dias antes. Esse é um erro eliminatório e, em regra, não sana após a sessão.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é preço inexequível em licitação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Preço inexequível é o valor da proposta tão abaixo do estimado que não há possibilidade real de execução do contrato sem prejuízo. A Lei 14.133/2021, no art. 59, §§ 1º e 2º, considera inexequíveis propostas de obras e serviços de engenharia abaixo de 75% do orçamento-base. Para outras contratações, o critério é analisado caso a caso pelo pregoeiro. A empresa pode ser chamada a comprovar a viabilidade do preço — se não conseguir, é desclassificada.',
                },
              },
              {
                '@type': 'Question',
                name: 'Erros formais na proposta podem ser corrigidos durante a sessão do pregão?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Depende. A Lei 14.133/2021, no art. 64, permite ao pregoeiro solicitar esclarecimentos ou a complementação de informações para sanar erros formais (não substanciais) nas propostas. Erros aritméticos simples, falta de assinatura em documento auxiliar e pequenas inconsistências de formatação podem ser saneáveis a critério do pregoeiro. Já erros como preço inexequível, certidão vencida, proposta fora do objeto licitado ou ausência de documentos obrigatórios são eliminatórios e não admitem saneamento.',
                },
              },
              {
                '@type': 'Question',
                name: 'Atestado de capacidade técnica insuficiente causa desclassificação?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim. O atestado técnico é parte da habilitação técnica (art. 67 da Lei 14.133/2021) e deve comprovar que a empresa já executou objeto compatível com o que está sendo licitado, com as quantidades, complexidade e características exigidas no edital. Atestados que não atingem o percentual mínimo exigido (em geral 50% da quantidade ou valor licitado), que não descrevem adequadamente os serviços ou que são emitidos por pessoas físicas sem CNPJ idôneo são recusados e geram inabilitação.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como evitar erros de prazo em licitações — envio fora do horário?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'O horário de abertura do pregão eletrônico é improrrogável. Propostas enviadas após o horário estipulado no edital são automaticamente rejeitadas pelo sistema — não há como o pregoeiro aceitar ou justificar o atraso. A recomendação prática é enviar a proposta com pelo menos 24 horas de antecedência e revisá-la no sistema antes do fechamento. Conexão lenta, falha de sistema ou erro de upload não são aceitos como justificativa pelo TCU.',
                },
              },
            ],
          }),
        }}
      />

      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Estudos de auditoria do Tribunal de Contas da União e análises de portais de compras governamentais indicam que mais de 35% das propostas inabilitadas ou desclassificadas em pregões eletrônicos foram eliminadas por erros evitáveis — problemas burocráticos, não técnicos. Ou seja: a empresa tinha capacidade para entregar o contrato, o preço era competitivo, mas foi eliminada por uma certidão vencida, um campo preenchido com o CNPJ errado ou uma assinatura ausente. Este guia mapeia os erros mais frequentes, classifica sua gravidade e mostra como montar um processo de revisão que praticamente elimina o risco de desclassificação evitável.
      </p>

      <h2>Erros de Documentação — Os 4 Mais Frequentes</h2>
      <p>
        A fase de habilitação é onde a maioria das desclassificações acontece. Os documentos exigidos pelo edital devem ser apresentados em formato, prazo e conteúdo exatos — qualquer divergência pode ser fatal. Os quatro erros mais comuns nessa categoria são:
      </p>

      <p>
        <strong>1. Certidão de regularidade fiscal vencida.</strong> A Certidão de Regularidade do FGTS tem validade de apenas 30 dias — a que mais surpreende fornecedores. A Certidão Conjunta Receita/PGFN e a Certidão Negativa de Débitos Trabalhistas (CNDT/TST) valem 180 dias. Certidões estaduais e municipais variam de 30 a 90 dias conforme o ente. O pregoeiro verifica cada uma individualmente durante a sessão. Uma única certidão expirada — mesmo que os demais documentos estejam perfeitos — gera inabilitação imediata. Veja o{' '}
        <Link href="/blog/checklist-habilitacao-licitacao-2026">checklist completo de habilitação</Link>{' '}
        para nunca perder um prazo.
      </p>

      <p>
        <strong>2. CNPJ errado — filial vs. matriz.</strong> Empresas com matriz e filiais frequentemente submetem proposta com o CNPJ de uma e a documentação de habilitação da outra. Como cada CNPJ é uma pessoa jurídica distinta perante a Receita Federal, certidões emitidas para o CNPJ da matriz não valem automaticamente para a filial. O CNPJ que assina a proposta deve ser o mesmo que consta em todos os documentos de habilitação — e esse CNPJ deve estar regular em todas as certidões exigidas.
      </p>

      <p>
        <strong>3. Assinatura ausente ou inválida.</strong> A proposta comercial, as declarações obrigatórias e os documentos de habilitação devem ser assinados pelo representante legal da empresa ou por procurador com poderes expressos. Em pregões eletrônicos, a assinatura digital via certificado e-CNPJ ou e-CPF (ICP-Brasil) é aceita e frequentemente obrigatória. Procurações devem ter firma reconhecida ou ser assinadas digitalmente. Documentos sem assinatura válida ou com assinatura de pessoa sem poderes de representação são rejeitados.
      </p>

      <p>
        <strong>4. Balanço patrimonial incompleto ou desatualizado.</strong> O balanço exigido é o do último exercício social encerrado, devidamente publicado ou autenticado. Empresas obrigadas a publicação no Diário Oficial devem apresentá-lo com esse comprovante. O balanço deve estar assinado pelo contador responsável com CRC ativo. Índices financeiros calculados com base no balanço (liquidez geral, liquidez corrente, solvência geral) devem atender aos mínimos estabelecidos no edital — geralmente igual ou superior a 1. Um balanço que não comprove os índices mínimos é causa de inabilitação por insuficiência econômico-financeira.
      </p>

      <h2>Erros na Proposta de Preço — Os 4 Mais Frequentes</h2>
      <p>
        A proposta comercial é o coração da disputa. Erros aqui podem eliminar a empresa mesmo que toda a documentação de habilitação esteja perfeita. Veja os quatro mais comuns:
      </p>

      <p>
        <strong>1. Preço inexequível.</strong> Conforme o art. 59, §§ 1º e 2º da Lei 14.133/2021, são consideradas inexequíveis as propostas de obras e serviços de engenharia com valor global inferior a 75% do orçamento-base e as de serviços comuns com valor que demonstre impossibilidade de execução rentável. A inexequibilidade não é automática em todas as modalidades — o pregoeiro pode convocar a empresa para comprovar a viabilidade (planilha de custos, contratos similares). Se a comprovação não for satisfatória, a desclassificação é inevitável. Propostas com preço unitário zerado em algum item também são questionadas.
      </p>

      <p>
        <strong>2. Ausência de preços unitários.</strong> Editais que exigem planilha de formação de preços com itens unitários (comum em contratos de serviços contínuos e obras) desclassificam propostas que apresentem apenas o valor total. Cada item deve ter seu preço unitário preenchido, pois é com base neles que se calculam aditivos, supressões e medições mensais durante a execução. Campos em branco ou com valor zero em itens obrigatórios são causa de desclassificação.
      </p>

      <p>
        <strong>3. Erros aritméticos não detectados.</strong> A soma dos itens não confere com o total da proposta, o BDI foi calculado com percentual diferente do declarado ou os impostos foram aplicados sobre base de cálculo errada. Em pregões eletrônicos, o sistema frequentemente detecta esses erros automaticamente — mas em licitações onde a planilha é enviada em PDF ou Word, o pregoeiro verifica manualmente. Erros aritméticos são em tese "saneáveis" (art. 64 da Lei 14.133/2021), mas dependem da discricionariedade do pregoeiro e do impacto no preço final.
      </p>

      <p>
        <strong>4. Proposta em formato diferente do exigido pelo edital.</strong> O edital especifica o formato da proposta: planilha modelo a ser preenchida, campos obrigatórios, unidades de medida, moeda, número de casas decimais e, às vezes, até a fonte e o tamanho da letra. Propostas que não seguem o modelo exato — mesmo com o conteúdo correto — podem ser desclassificadas por descumprimento formal. Sempre baixe e preencha o modelo anexo ao edital, nunca use um modelo próprio.
      </p>

      <h2>Erros de Habilitação Técnica — Os 4 Mais Frequentes</h2>
      <p>
        A habilitação técnica (art. 67 da Lei 14.133/2021) comprova que a empresa tem experiência e capacidade para executar o objeto licitado. É onde empresas com boa qualificação técnica real são eliminadas por não saber apresentar essa qualificação corretamente.
      </p>

      <p>
        <strong>1. Atestado de capacidade técnica insuficiente.</strong> O atestado deve ser emitido por pessoa jurídica de direito público ou privado, descrever o objeto executado com especificidade e atingir o percentual mínimo exigido (em geral 50% da quantidade, metragem ou valor do objeto licitado). Atestados vagos ("prestou serviços de tecnologia da informação"), emitidos para objeto diferente ou que não atingem a quantidade mínima são recusados. Se você tem múltiplos atestados, a soma pode ser aceita — mas verifique se o edital permite.
      </p>

      <p>
        <strong>2. Ausência de registro profissional (CREA, CRM, CRF, CRO).</strong> Licitações de engenharia, saúde, farmácia e outras áreas reguladas exigem o registro ativo no conselho de classe correspondente — tanto da empresa (pessoa jurídica) quanto dos responsáveis técnicos indicados. Empresas que atuam em área regulada mas não renovaram o registro no conselho (que vence anualmente em 31 de dezembro) são inabilitadas mesmo com toda a documentação fiscal em ordem.
      </p>

      <p>
        <strong>3. Tipo de garantia de proposta incorreto.</strong> Editais de grande porte (acima de determinado valor) podem exigir garantia de proposta, conforme art. 58 da Lei 14.133/2021. As modalidades aceitas são: caução em dinheiro, seguro-garantia ou fiança bancária. Apresentar o tipo errado (ex.: caução quando o edital aceita apenas seguro-garantia, ou valor abaixo do exigido) gera desclassificação. O prazo de vigência da garantia deve cobrir pelo menos o período da validade da proposta estabelecido no edital.
      </p>

      <p>
        <strong>4. Declarações obrigatórias ausentes ou com conteúdo incorreto.</strong> A Lei 14.133/2021 exige declarações específicas em editais: declaração de inexistência de vínculo empregatício com servidores do órgão licitante, declaração de cumprimento de requisitos de habilitação, declaração de que não é empresa de grande porte em licitações exclusivas para ME/EPP, entre outras. Cada edital especifica as declarações exigidas. A ausência de qualquer delas — ou o preenchimento com conteúdo equivocado — é causa de inabilitação.
      </p>

      <BlogInlineCTA slug="erros-desclassificam-propostas-licitacao" campaign="guias" />

      <h2>Erros de Prazo — Quando o Relógio Elimina sua Empresa</h2>
      <p>
        Em licitações, o prazo não é uma sugestão — é uma barreira absoluta. Os três erros de prazo mais frequentes são:
      </p>

      <p>
        <strong>Upload de proposta após o horário limite.</strong> O sistema do pregão eletrônico fecha automaticamente no horário estabelecido no edital. Propostas enviadas após esse horário são recusadas pelo sistema — não há como o pregoeiro aceitar manualmente. Problemas de conexão, falha de upload ou demora no preenchimento não constituem justificativa. A recomendação padrão de profissionais de licitações é: envie a proposta com no mínimo 24 horas de antecedência e faça um login de verificação algumas horas antes do fechamento.
      </p>

      <p>
        <strong>Perda do prazo de impugnação.</strong> Identificou uma cláusula ilegal ou problemática no edital? A impugnação deve ser apresentada até 3 dias úteis antes da data marcada para a abertura da sessão (art. 164 da Lei 14.133/2021). Após esse prazo, o órgão não é obrigado a responder e pode rejeitar a impugnação por intempestividade. Saiba mais sobre{' '}
        <Link href="/blog/impugnacao-edital-quando-como-contestar">como e quando impugnar um edital</Link>.
      </p>

      <p>
        <strong>Recurso administrativo intempestivo.</strong> Após a fase de julgamento ou habilitação, a empresa pode interpor recurso. O prazo padrão é de 3 dias úteis, contados da data da sessão em que foi proferida a decisão impugnada (art. 165 da Lei 14.133/2021). Recursos apresentados fora desse prazo — mesmo que fundamentados — são declarados intempestivos e não são conhecidos, encerrando definitivamente a possibilidade de reverter a decisão naquela instância.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-semibold mb-3">Os 12 Erros Mais Comuns — Frequência e Gravidade</h3>
        <ul className="space-y-2 text-sm">
          <li>• <strong>1. Certidão fiscal vencida</strong> — Frequência: muito alta | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
          <li>• <strong>2. CNPJ errado (filial vs. matriz)</strong> — Frequência: alta | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
          <li>• <strong>3. Proposta enviada após o prazo</strong> — Frequência: média | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
          <li>• <strong>4. Preço inexequível sem comprovação</strong> — Frequência: média | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
          <li>• <strong>5. Atestado técnico insuficiente</strong> — Frequência: alta | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
          <li>• <strong>6. Declarações obrigatórias ausentes</strong> — Frequência: alta | Gravidade: <span className="text-orange-600 font-semibold">Eliminatório / Sanável*</span></li>
          <li>• <strong>7. Assinatura inválida ou ausente</strong> — Frequência: média | Gravidade: <span className="text-orange-600 font-semibold">Eliminatório / Sanável*</span></li>
          <li>• <strong>8. Ausência de registro profissional</strong> — Frequência: média | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
          <li>• <strong>9. Proposta em formato diferente do edital</strong> — Frequência: média | Gravidade: <span className="text-orange-600 font-semibold">Eliminatório / Sanável*</span></li>
          <li>• <strong>10. Erros aritméticos na planilha</strong> — Frequência: média | Gravidade: <span className="text-yellow-600 font-semibold">Sanável* a critério do pregoeiro</span></li>
          <li>• <strong>11. Preços unitários ausentes na planilha</strong> — Frequência: média | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
          <li>• <strong>12. Garantia de proposta incorreta</strong> — Frequência: baixa | Gravidade: <span className="text-red-600 font-semibold">Eliminatório</span></li>
        </ul>
        <p className="text-xs text-ink-secondary mt-3">* Sanável a critério do pregoeiro, conforme art. 64 da Lei 14.133/2021. Não há direito subjetivo ao saneamento.</p>
      </div>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="font-semibold text-amber-800 dark:text-amber-200">⚠ Entenda o Conceito de "Erro Sanável"</p>
        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
          O art. 64 da Lei 14.133/2021 permite ao pregoeiro sanar erros ou falhas que não alterem a substância das propostas e dos documentos. Isso inclui erros aritméticos, omissões de informações que podem ser consultadas em bases públicas e inconsistências formais menores. No entanto, o saneamento é uma faculdade do pregoeiro, não um direito da empresa. Na prática, a margem de saneamento varia muito conforme o órgão, o valor do contrato e o perfil do pregoeiro. Nunca conte com o saneamento como plano principal — sua proposta deve estar perfeita antes do envio.
        </p>
      </div>

      <h2>Como Montar um Checklist Anti-Erro</h2>
      <p>
        A diferença entre empresas que ganham contratos consistentemente e as que são desclassificadas repetidamente está, em grande parte, na existência de um processo de revisão estruturado. Veja como montar um checklist eficaz:
      </p>
      <p>
        <strong>Etapa 1 — Leitura completa do edital (não apenas o resumo).</strong> Marque todos os documentos exigidos, prazos, formatos e condições específicas. Editais longos frequentemente escondem exigências especiais em cláusulas de habilitação técnica ou nos anexos.
      </p>
      <p>
        <strong>Etapa 2 — Verificação de validade de cada certidão.</strong> Com o checklist do edital em mãos, verifique a data de vencimento de cada certidão exigida. Se alguma vence antes da data da sessão, renove imediatamente. Consulte o{' '}
        <Link href="/blog/checklist-habilitacao-licitacao-2026">checklist completo de habilitação</Link>{' '}
        para ter uma lista padrão de documentos com prazos de renovação.
      </p>
      <p>
        <strong>Etapa 3 — Revisão da proposta de preço por pessoa diferente de quem preencheu.</strong> Erros aritméticos e campos esquecidos são muito mais fáceis de identificar com "olhos frescos". Implemente uma regra de dupla revisão: quem preencheu a planilha não pode ser quem faz a verificação final.
      </p>
      <p>
        <strong>Etapa 4 — Conferência do CNPJ em todos os documentos.</strong> Confirme que o mesmo CNPJ aparece na proposta, nas certidões, nos atestados técnicos e nas declarações. Se sua empresa tem filiais, defina uma política clara sobre qual CNPJ participa de cada licitação.
      </p>
      <p>
        <strong>Etapa 5 — Upload de teste com 48 horas de antecedência.</strong> Em pregões eletrônicos, acesse o sistema, faça o upload da proposta e das declarações, e verifique se o sistema confirma o recebimento. Ainda há tempo para corrigir eventuais falhas de sistema ou arquivo corrompido. Na véspera, confirme que a proposta está corretamente registrada.
      </p>

      <h2>Quando o Erro É do Edital, Não da Proposta</h2>
      <p>
        Nem todo problema vem da proposta da empresa — às vezes o edital tem cláusulas ilegais, exigências desproporcionais ou erros que prejudicam a participação. Nesses casos, a ferramenta correta é a impugnação do edital, não a adequação forçada às regras problemáticas.
      </p>
      <p>
        Exemplos de situações que justificam impugnação: exigência de atestado com quantidade superior ao dobro do objeto licitado (viola art. 67 da Lei 14.133/2021), restrição a MEI ou microempresa sem justificativa, exigência de marca específica sem razão técnica documentada, prazo de validade da proposta excessivamente longo sem garantia correspondente. Saiba mais sobre{' '}
        <Link href="/blog/impugnacao-edital-quando-como-contestar">quando e como contestar um edital</Link>{' '}
        antes de desistir de uma licitação.
      </p>
      <p>
        É também possível pedir esclarecimentos ao órgão licitante sobre cláusulas ambíguas — antes da sessão, com prazo definido no edital (em geral até 3 dias úteis antes da abertura). Esclarecimentos bem feitos evitam interpretações erradas que levariam à desclassificação. Para entender o processo completo desde o início, veja o{' '}
        <Link href="/blog/como-participar-primeira-licitacao-2026">guia de como participar da primeira licitação</Link>.
      </p>
      <p>
        Outra proteção importante é escolher bem os editais em que participar. Disputar licitações para as quais sua empresa não tem qualificação técnica suficiente — ou em que o prazo de execução é inviável — aumenta o risco de desclassificação e, em caso de vitória, de não conseguir entregar. Use a{' '}
        <Link href="/calculadora">calculadora de viabilidade</Link>{' '}
        para avaliar cada oportunidade antes de investir tempo na proposta.
      </p>

      <div className="not-prose my-8 sm:my-10 bg-brand/5 border border-brand/20 rounded-lg p-6 sm:p-8 text-center">
        <h3 className="text-xl font-bold mb-2">Encontre Licitações com Mais Chance de Sucesso</h3>
        <p className="text-ink-secondary mb-4">
          O SmartLic analisa editais do PNCP e outros portais, classifica relevância por setor e avalia viabilidade com 4 fatores — modalidade, prazo, valor e geografia. Foque nas oportunidades certas e reduza o desperdício de propostas.
        </p>
        <Link
          href="/consultoria-b2g?ref=blog-erros-desclassificam"
          className="inline-block bg-brand text-white font-semibold px-6 py-3 rounded-lg hover:bg-brand/90 transition-colors"
        >
          Testar grátis por 14 dias →
        </Link>
      </div>

      <h2>Perguntas Frequentes</h2>

      <h3>Qual o erro mais comum que desclassifica propostas?</h3>
      <p>
        Certidão de regularidade fiscal vencida — especialmente a do FGTS, com validade de apenas 30 dias. É o erro mais frequente e sempre eliminatório. Verifique a validade de todas as certidões com pelo menos uma semana de antecedência à sessão.
      </p>

      <h3>O que é preço inexequível e como evitar?</h3>
      <p>
        Preço inexequível é aquele tão abaixo do estimado que não permite a execução do contrato sem prejuízo. Para obras e serviços de engenharia, a Lei 14.133/2021 define 75% do orçamento-base como limite. Para demais contratações, o critério é discricionário. Evite oferecer preços que não consiga justificar com planilha de custos — o pregoeiro pode exigir comprovação.
      </p>

      <h3>Erros formais podem ser corrigidos durante a sessão?</h3>
      <p>
        Alguns, a critério do pregoeiro, conforme o art. 64 da Lei 14.133/2021. Erros aritméticos e inconsistências formais menores podem ser saneados. Certidões vencidas, preço inexequível e ausência de documentos obrigatórios são eliminatórios sem possibilidade de saneamento.
      </p>

      <h3>Atestado de capacidade técnica insuficiente causa inabilitação?</h3>
      <p>
        Sim. O atestado deve comprovar experiência em objeto compatível com o licitado, atingindo o percentual mínimo exigido (geralmente 50%). Atestados vagos, com objeto diferente ou abaixo da quantidade mínima são recusados. Junte múltiplos atestados quando um só não for suficiente — se o edital permitir.
      </p>

      <h3>Como evitar ser eliminado por prazo de envio?</h3>
      <p>
        Envie a proposta com no mínimo 24 horas de antecedência e faça login de verificação algumas horas antes do fechamento. O sistema fecha automaticamente no horário do edital — problemas técnicos não são aceitos como justificativa pelo TCU. Use alertas de calendário para cada etapa da licitação.
      </p>
    </>
  );
}
