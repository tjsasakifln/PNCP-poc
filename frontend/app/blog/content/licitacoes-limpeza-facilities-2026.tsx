import Link from 'next/link';
import BlogInlineCTA from '../components/BlogInlineCTA';

/**
 * SEO GUIA-S4: Licitações de Limpeza e Facilities 2026 — Guia Completo
 *
 * Content cluster: guias setoriais
 * Target: 3,000+ words | Primary KW: licitações limpeza
 */
export default function LicitacoesLimpezaFacilities2026() {
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
                name: 'Como montar planilha de custos para licitação de limpeza?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A planilha de custos para licitação de limpeza deve incluir: remuneração base conforme a convenção coletiva vigente (CCT), encargos sociais e trabalhistas (INSS, FGTS, 13º, férias — entre 65% e 80% sobre o salário), insumos (produtos de limpeza, EPIs, uniformes), equipamentos (incluindo depreciação), custos indiretos (supervisão, administração) e BDI (Bonificação e Despesas Indiretas, tipicamente entre 15% e 25%). A soma de todos esses componentes, dividida pela produtividade por m², gera o custo por posto de serviço.',
                },
              },
              {
                '@type': 'Question',
                name: 'Qual o peso da convenção coletiva na formação de preço?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A convenção coletiva de trabalho (CCT) é o fator determinante na formação de preço de serviços de limpeza. O salário base definido na CCT da região de execução do contrato representa entre 50% e 60% do custo total do posto. Cada reajuste anual da CCT (dissídio) impacta diretamente o preço — empresas que não consideram o dissídio projetado na formação de preço correm risco de operar com margem negativa após o reajuste.',
                },
              },
              {
                '@type': 'Question',
                name: 'Preciso de quantos atestados de capacidade?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A Lei 14.133/2021 permite que o edital exija atestados que comprovem execução de até 50% do quantitativo licitado (art. 67, §1º). Na prática, editais de limpeza exigem entre 1 e 3 atestados que demonstrem experiência na prestação de serviços similares (limpeza predial, conservação, asseio) com quantitativo mínimo de postos ou área atendida. Atestados de contratos públicos têm maior peso, mas contratos privados também são aceitos quando acompanhados de documentação comprobatória.',
                },
              },
              {
                '@type': 'Question',
                name: 'É possível participar em UFs diferentes da sede?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'Sim, não há restrição legal para participar de licitações em UFs diferentes da sede da empresa. Porém, é necessário considerar que a convenção coletiva aplicável é a do local de execução do contrato (não a da sede), o que pode alterar significativamente o custo. Além disso, muitos editais exigem que a empresa mantenha escritório ou preposto na cidade de execução durante a vigência do contrato.',
                },
              },
              {
                '@type': 'Question',
                name: 'Como funciona a repactuação de contratos de limpeza?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'A repactuação é o mecanismo de reajuste de contratos de serviços contínuos com mão de obra dedicada, prevista no art. 135 da Lei 14.133/2021. Diferente do reajuste por índice, a repactuação se baseia na variação dos custos efetivos — especialmente o novo piso salarial definido pela CCT. O contratado deve solicitar a repactuação apresentando planilha de custos atualizada, demonstrando a variação de cada componente. O prazo mínimo para a primeira repactuação é de 12 meses contados da data do orçamento estimativo.',
                },
              },
              {
                '@type': 'Question',
                name: 'O que é BDI e como calcular para serviços de limpeza?',
                acceptedAnswer: {
                  '@type': 'Answer',
                  text: 'BDI (Bonificação e Despesas Indiretas) é o percentual aplicado sobre os custos diretos para cobrir despesas administrativas, impostos sobre faturamento (ISS, PIS, COFINS, CSLL, IRPJ) e a margem de lucro. Para serviços de limpeza, o BDI típico varia entre 15% e 25%. O cálculo segue a fórmula: BDI = [(1 + AC) × (1 + S) × (1 + R) × (1 + L) / (1 - I)] - 1, onde AC = administração central, S = seguros, R = riscos, L = lucro e I = impostos. O TCU possui referências de BDI aceitáveis em seus acórdãos (Acórdão 2622/2013-TCU-Plenário).',
                },
              },
            ],
          }),
        }}
      />

      {/* HowTo JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'HowTo',
            name: 'Como participar de licitações de limpeza e facilities em 2026',
            description:
              'Passo a passo para empresas de limpeza, conservação e facilities que desejam vender serviços ao governo via licitações públicas.',
            step: [
              {
                '@type': 'HowToStep',
                name: 'Identifique a convenção coletiva da região-alvo',
                text: 'Consulte a CCT do sindicato de asseio e conservação da cidade onde pretende executar o contrato. O piso salarial é a base de toda a planilha de custos.',
              },
              {
                '@type': 'HowToStep',
                name: 'Monte a planilha de custos detalhada',
                text: 'Elabore planilha com salário base (CCT), encargos sociais e trabalhistas, insumos, EPIs, uniformes, equipamentos, custos indiretos e BDI.',
              },
              {
                '@type': 'HowToStep',
                name: 'Reúna atestados de capacidade técnica',
                text: 'Obtenha atestados de contratos anteriores (públicos ou privados) que comprovem experiência em limpeza predial ou serviços similares.',
              },
              {
                '@type': 'HowToStep',
                name: 'Cadastre-se nos portais de compras',
                text: 'Faça cadastro no PNCP, ComprasGov (SICAF) e portais estaduais. Mantenha documentação fiscal e trabalhista sempre atualizada.',
              },
              {
                '@type': 'HowToStep',
                name: 'Analise a viabilidade antes de participar',
                text: 'Avalie cada edital considerando valor estimado, CCT aplicável, número de postos, localização e histórico de pagamento do órgão.',
              },
            ],
          }),
        }}
      />

      {/* Opening paragraph */}
      <p className="text-base sm:text-xl leading-relaxed text-ink">
        Serviços de limpeza, conservação e facilities management representam uma das
        maiores categorias de contratação pública no Brasil. Em 2024, o governo
        federal sozinho manteve mais de <strong>R$ 12 bilhões em contratos ativos</strong>{' '}
        de serviços terceirizados de limpeza e conservação predial, segundo o Painel
        de Compras do Governo Federal. Somando estados e municípios, o mercado
        ultrapassa R$ 40 bilhões anuais. A demanda é constante, os contratos são
        de longa duração (12 a 60 meses) e a renovação é previsível. Mas vencer
        nesse segmento exige domínio de planilha de custos, conhecimento profundo
        da convenção coletiva e capacidade operacional comprovada. Este guia
        apresenta tudo o que você precisa saber para participar com competitividade
        de licitações de limpeza e facilities em 2026.
      </p>

      {/* Section 1: Panorama */}
      <h2>Panorama: terceirização no setor público</h2>

      <p>
        A terceirização de serviços de limpeza, conservação, portaria e manutenção
        predial é uma realidade consolidada na administração pública brasileira.
        Desde o Decreto 9.507/2018, regulamentado agora pela Lei 14.133/2021, o
        governo pode contratar empresas privadas para executar serviços de apoio
        que não envolvam atividade-fim do órgão. Na prática, isso significa que
        praticamente todo órgão público — de um tribunal federal a uma escola
        municipal — contrata limpeza e conservação via licitação.
      </p>

      <p>
        O PNCP registra entre 5.000 e 9.000 publicações mensais relacionadas a
        serviços de limpeza, conservação e facilities, considerando todas as
        esferas e modalidades. Esse volume faz do segmento a maior categoria de
        serviços continuados terceirizados no setor público, a frente de
        vigilância, TI e alimentação.
      </p>

      <p>
        Uma característica definidora desse mercado é a mão de obra intensiva.
        Em contratos de limpeza, o custo com pessoal (salários + encargos)
        representa entre 70% e 82% do valor total. Isso torna a convenção
        coletiva de trabalho (CCT) o fator mais crítico na formação de preço
        — é o principal diferenciador entre uma proposta competitiva e uma
        proposta inexequível.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Dados de referência — Mercado de limpeza e facilities no setor público
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Volume mensal no PNCP:</strong> 5.000 a 9.000 publicações
            (pregões, dispensas, atas de registro de preço) em todas as esferas.
          </li>
          <li>
            <strong>Contratos federais ativos:</strong> mais de R$ 12 bilhões em
            serviços de limpeza e conservação (Painel de Compras, 2024).
          </li>
          <li>
            <strong>Duração média do contrato:</strong> 12 meses iniciais com
            possibilidade de prorrogação por até 10 anos (art. 107 da Lei
            14.133/2021 para serviços continuados).
          </li>
          <li>
            <strong>Percentual de custo com pessoal:</strong> 70% a 82% do valor
            total do contrato (fonte: IN SEGES/ME 5/2017, modelo referencial).
          </li>
          <li>
            <strong>Setores sindicais:</strong> SEAC (Sindicato das Empresas de
            Asseio e Conservação) presente em todos os 26 estados e DF, com CCTs
            próprias por base territorial.
          </li>
        </ul>
      </div>

      {/* Section 2: Tipos de objeto */}
      <h2>Tipos de objeto: limpeza, jardinagem, portaria, manutenção e copeiragem</h2>

      <p>
        O conceito de &ldquo;facilities management&rdquo; abrange diversos serviços de
        apoio à operação de edifícios e instalações. Em licitações públicas, os
        objetos mais frequentes são:
      </p>

      <h3>Limpeza e conservação predial</h3>

      <p>
        O objeto mais comum é mais volumoso. Inclui varrição, lavagem, aspiração,
        higienização de banheiros, recolhimento de resíduos, limpeza de vidros e
        fachadas. Os editais definem a produtividade esperada por servente (tipicamente
        600 a 1.200 m² por jornada de 8 horas, conforme IN SEGES 5/2017) e o
        número de postos necessários. A frequência pode ser diária, semanal ou
        quinzenal, dependendo do tipo de área (administrativa, hospitalar, laboratório).
      </p>

      <h3>Jardinagem e paisagismo</h3>

      <p>
        Serviços de manutenção de áreas verdes, incluindo poda, irrigação, adubação,
        controle de pragas e plantio. Frequentemente licitados em conjunto com
        limpeza predial em editais multisserviços, ou separadamente para órgãos
        com grandes áreas externas (universidades, quartéis, hospitais com campus).
      </p>

      <h3>Portaria e recepção</h3>

      <p>
        Controle de acesso, atendimento ao público, operação de interfones e CCTV,
        recepção de visitantes. Embora não seja estritamente &ldquo;limpeza&rdquo;,
        muitos editais de facilities agrupam portaria com limpeza e conservação em
        um único contrato. O custo por posto de portaria é tipicamente maior que
        limpeza, pois exige jornada 12x36 ou 24 horas com escalas.
      </p>

      <h3>Manutenção predial</h3>

      <p>
        Serviços de manutenção preventiva e corretiva de instalações elétricas,
        hidráulicas, de climatização e de alvenaria. Requer mão de obra qualificada
        (eletricistas, encanadores, técnicos de refrigeração) e pode envolver
        fornecimento de materiais. As convenções coletivas para manutenção são
        diferentes das de limpeza (SINDMACON ou equivalente), com pisos salariais
        superiores.
      </p>

      <h3>Copeiragem</h3>

      <p>
        Preparação e distribuição de café, chá, água e lanches em ambientes
        administrativos. Serviço de menor porte, mas presente em praticamente
        todo órgão público. Frequentemente incluído em editais de limpeza como
        item adicional.
      </p>

      {/* Section 3: Modalidades */}
      <h2>Modalidades: pregão, SRP e contratação continuada</h2>

      <p>
        Serviços de limpeza são classificados como serviços comuns (art. 6, XIII da
        Lei 14.133/2021), o que torna o{' '}
        <Link href="/glossario#pregao-eletrônico" className="text-brand-navy dark:text-brand-blue hover:underline">
          pregão eletrônico
        </Link>{' '}
        a modalidade obrigatória. Mais de 85% dos editais de limpeza publicados no
        PNCP utilizam pregão eletrônico com critério de menor preço global ou menor
        preço por lote.
      </p>

      <p>
        O Sistema de Registro de Preços (SRP) é utilizado quando o órgão deseja
        flexibilidade no quantitativo — por exemplo, quando precisa contratar
        serviços de limpeza para múltiplas unidades com cronogramas diferentes.
        A ata de registro de preços permite acionar o fornecedor conforme a
        necessidade, sem obrigação de contratação integral.
      </p>

      <p>
        A contratação continuada (art. 106 da Lei 14.133/2021) é a regra para
        serviços de limpeza: o contrato é firmado por 12 meses com possibilidade
        de prorrogação sucessiva, podendo atingir até 10 anos de duração total
        (art. 107). Essa característica é vantajosa para o fornecedor porque
        gera receita recorrente e previsível — desde que a empresa consiga manter
        a qualidade do serviço e negociar repactuações adequadas ao longo do tempo.
      </p>

      {/* Section 4: Planilha de custos */}
      <h2>Planilha de custos e formação de preço</h2>

      <p>
        A planilha de custos é o documento mais crítico em licitações de limpeza.
        Diferente de pregões de bens (onde o preço é simples: custo do produto +
        margem), em serviços de limpeza cada componente de custo deve ser
        discriminado e justificado. A Instrução Normativa SEGES/ME 5/2017
        (ainda vigente como referência) estabelece o modelo de planilha, e a
        maioria dos editais adota esse formato.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Estrutura da planilha de custos — Limpeza predial
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li>
            <strong>Módulo 1 — Remuneração:</strong> Salário base (conforme CCT),
            adicional de insalubridade (quando aplicável, 20% do salário mínimo),
            adicional noturno (se houver turno noturno), vale-transporte
            (desconto legal de 6%).
          </li>
          <li>
            <strong>Módulo 2 — Encargos e benefícios:</strong> INSS patronal
            (20% + RAT/FAP), FGTS (8%), PIS/PASEP (1%), SESC/SESI (1,5%), SENAC/SENAI
            (1%), SEBRAE (0,6%), INCRA (0,2%), salário-educação (2,5%), férias + 1/3,
            13º salário, licenças, rescisão provisionada. Total de encargos: 65% a 80%
            sobre o salário.
          </li>
          <li>
            <strong>Módulo 3 — Insumos:</strong> Produtos de limpeza (detergente,
            desinfetante, cera, limpa-vidro), sacos de lixo, papel higiênico, papel
            toalha. Custo médio: R$ 150 a R$ 400 por posto/mês.
          </li>
          <li>
            <strong>Módulo 4 — Uniformes e EPIs:</strong> 2 jogos de uniforme por
            semestre, calçados, luvas, máscaras, óculos de proteção. Custo médio:
            R$ 80 a R$ 200 por posto/mês (amortizado).
          </li>
          <li>
            <strong>Módulo 5 — Equipamentos:</strong> Aspiradores, enceradeiras,
            lavadoras, carrinhos funcionais. Custo de depreciação: R$ 50 a R$ 150
            por posto/mês.
          </li>
          <li>
            <strong>Módulo 6 — Custos indiretos e BDI:</strong> Administração
            central (3% a 5%), lucro (5% a 10%), impostos (ISS 2% a 5%, PIS 0,65%
            a 1,65%, COFINS 3% a 7,6%, CSLL 1,08%, IRPJ 1,2%). BDI total: 15% a 25%.
          </li>
        </ul>
      </div>

      <p>
        O erro mais grave na formação de preço é utilizar valores genéricos em vez
        dos valores específicos da convenção coletiva da região de execução. Um
        servente de limpeza em São Paulo (piso de R$ 1.870 em 2025) custa
        significativamente mais que em cidades do interior do Nordeste (piso de
        R$ 1.420 a R$ 1.550). Usar o piso errado gera uma proposta inexequível
        (se usar o piso menor para uma vaga em SP) ou não competitiva (se usar
        o piso maior para uma vaga no interior).
      </p>

      {/* Section 5: Convenção coletiva */}
      <h2>Convenção coletiva e impacto regional</h2>

      <p>
        A convenção coletiva de trabalho (CCT) é o documento que define o piso
        salarial, benefícios, jornada e condições específicas para trabalhadores
        do setor de asseio e conservação em uma determinada base territorial.
        Cada estado — e em alguns casos, cada região metropolitana — possui
        sua própria CCT, negociada entre o SEAC (sindicato patronal) e o
        sindicato dos empregados.
      </p>

      <p>
        A variação entre regiões é significativa. O piso salarial para servente
        de limpeza pode variar em até 40% entre a capital e o interior do mesmo
        estado, e em até 60% entre estados diferentes. Benefícios obrigatórios
        (vale-alimentação, plano odontológico, seguro de vida, cesta básica)
        também variam conforme a CCT, impactando diretamente a planilha de
        custos.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-surface-1 border border-[var(--border)] rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Pisos salariais de referência — Servente de limpeza (CCTs 2024/2025)
        </p>
        <ul className="space-y-2 text-sm text-ink-secondary">
          <li><strong>São Paulo (capital):</strong> R$ 1.870,00</li>
          <li><strong>Rio de Janeiro (capital):</strong> R$ 1.750,00</li>
          <li><strong>Belo Horizonte:</strong> R$ 1.620,00</li>
          <li><strong>Curitiba:</strong> R$ 1.710,00</li>
          <li><strong>Porto Alegre:</strong> R$ 1.680,00</li>
          <li><strong>Salvador:</strong> R$ 1.550,00</li>
          <li><strong>Brasília (DF):</strong> R$ 1.795,00</li>
          <li><strong>Recife:</strong> R$ 1.480,00</li>
          <li className="pt-2 text-xs">
            Fonte: CCTs registradas no Sistema Mediador (MTE), vigência 2024/2025.
            Valores aproximados, sujeitos a negociações coletivas em andamento.
          </li>
        </ul>
      </div>

      <p>
        O dissídio anual (reajuste definido na nova CCT) é o evento que mais
        impacta a rentabilidade de contratos em andamento. Se a empresa não
        provisionar o dissídio projetado na formação de preço original, corre
        risco de operar no prejuízo até conseguir a repactuação contratual —
        que pode levar 60 a 120 dias após a vigência da nova CCT.
      </p>

      {/* Section 6: UFs com maior demanda */}
      <h2>UFs com maior demanda de serviços de limpeza</h2>

      <p>
        O volume de licitações de limpeza segue a concentração de órgãos públicos
        e a população urbana. Os estados com maior número de publicações são
        aqueles com mais unidades administrativas, hospitais, escolas e tribunais.
      </p>

      <p>
        <strong>São Paulo</strong> lidera de forma expressiva, com o maior número
        de municípios populosos e a maior administração estadual do país.{' '}
        <strong>Minas Gerais</strong>, com 853 municípios (o maior número entre
        todas as UFs), gera volume alto de pregões municipais. O{' '}
        <strong>Distrito Federal</strong> concentra a administração federal e
        produz editais de grande valor (ministérios, tribunais superiores,
        autarquias). <strong>Rio de Janeiro</strong> e <strong>Rio Grande do
        Sul</strong> completam o top 5, impulsionados por suas redes estaduais
        de saúde e educação.
      </p>

      <p>
        Para fornecedores que buscam expandir atuação, estados do Centro-Oeste
        (GO, MT, MS) oferecem oportunidades com menor concorrência. A desvantagem
        é a necessidade de manter equipe local, pois editais de serviços
        continuados exigem presença operacional permanente.
      </p>

      {/* Section 7: Requisitos */}
      <h2>Requisitos de habilitação</h2>

      <p>
        Licitações de limpeza exigem documentação específica além dos requisitos
        genéricos da Lei 14.133/2021.
      </p>

      <p>
        <strong>CNAE adequado:</strong> O CNPJ deve conter CNAE compatível com o
        objeto. Os mais comuns são 8121-4/00 (limpeza em prédios e em domicílios)
        e 8111-7/00 (serviços combinados para apoio a edifícios). Editais multisserviços
        podem exigir CNAEs adicionais (8130-3/00 para paisagismo, 8020-0/01 para
        portaria).
      </p>

      <p>
        <strong>Atestados de capacidade técnica:</strong> Comprovação de execução
        anterior de serviços similares com quantitativo mínimo definido no edital
        (tipicamente 50% do número de postos licitados). Atestados devem ser
        emitidos por órgãos ou empresas contratantes, com descrição detalhada
        do objeto, quantitativos e período de execução. Para entender os
        requisitos legais completos, veja{' '}
        <Link href="/blog/lei-14133-guia-fornecedores" className="text-brand-navy dark:text-brand-blue hover:underline">
          o guia prático da Lei 14.133 para fornecedores
        </Link>.
      </p>

      <p>
        <strong>Qualificação econômico-financeira:</strong> Balanço patrimonial
        demonstrando índices de liquidez geral (LG), liquidez corrente (LC)
        e solvência geral (SG) iguais ou superiores a 1. Para contratos de grande
        porte (acima de R$ 5 milhões anuais), pode ser exigido capital social
        mínimo proporcional ao valor da contratação (tipicamente 10%).
      </p>

      <p>
        <strong>Vistoria técnica:</strong> Muitos editais exigem vistoria
        presencial nas instalações do órgão antes da apresentação da proposta.
        A vistoria permite avaliar a área total, o tipo de piso, a altura dos
        vidros, o número de banheiros e outras condições que impactam
        diretamente a produtividade e o custo.
      </p>

      {/* CTA at ~40% */}
      <BlogInlineCTA
        slug="licitações-limpeza-facilities-2026"
        campaign="guias"
        ctaHref="/explorar"
        ctaText="Explorar licitações gratis"
        ctaMessage="Descubra editais abertos no seu setor — busca gratuita"
      />

      {/* Section 8: Erros fatais */}
      <h2>Erros fatais em licitações de limpeza</h2>

      <p>
        O setor de limpeza tem armadilhas específicas que eliminam fornecedores
        antes mesmo da fase de lances. Conhecer esses erros é a diferença entre
        uma empresa que cresce com contratos públicos e uma que acumula prejuízos.
      </p>

      <h3>Erro 1: Não considerar o dissídio na formação de preço</h3>

      <p>
        O erro mais comum é mais caro. A empresa formula o preço com base no piso
        salarial vigente sem considerar que, em 6 a 10 meses, o dissídio reajustará
        esse piso em 5% a 12%. Se o contrato não prever cláusula de repactuação, ou
        se a repactuação demorar a ser processada, a empresa opera com margem negativa
        durante meses. A prática recomendada é incluir na proposta uma projeção de
        dissídio baseada no histórico da CCT (média dos últimos 3 reajustes).
      </p>

      <h3>Erro 2: Esquecer uniformes e EPIs no custo</h3>

      <p>
        A NR-6 exige fornecimento gratuito de EPIs (luvas, máscaras, calçados de
        segurança) ao trabalhador. A CCT tipicamente obriga o fornecimento de 2
        jogos de uniforme por semestre. Empresas que não incluem esses itens na
        planilha de custos apresentam proposta com valor artificialmente baixo —
        que será questionada na análise de exequibilidade (art. 59, parágrafo 4
        da Lei 14.133/2021) e pode resultar em desclassificação.
      </p>

      <h3>Erro 3: Subestimar a supervisão</h3>

      <p>
        Contratos de limpeza com mais de 15 postos tipicamente exigem um
        encarregado (supervisor) dedicado. O custo desse profissional (salário
        30% a 50% superior ao do servente, conforme CCT) deve ser incluído na
        planilha. Muitas empresas omitem o encarregado para reduzir o preço,
        mas a ausência de supervisão resulta em queda de qualidade, notificações
        e, eventualmente, rescisão contratual.
      </p>

      <h3>Erro 4: Usar a CCT errada</h3>

      <p>
        A CCT aplicável é a do local de execução do contrato, não a da sede da
        empresa. Uma empresa sediada em Recife que vence um pregão em Brasília
        deve aplicar a CCT de Brasília — cujo piso é significativamente superior.
        Usar o piso de Recife na proposta gera inexequibilidade e desclassificação.
        Para um panorama de como outros setores lidam com formação de preço, veja{' '}
        <Link href="/blog/licitacoes-alimentacao-2026" className="text-brand-navy dark:text-brand-blue hover:underline">
          o guia de licitações de alimentação 2026
        </Link>.
      </p>

      <h3>Erro 5: Não provisionar rescisões trabalhistas</h3>

      <p>
        Contratos de limpeza têm rotatividade alta (turnover de 15% a 30% ao ano).
        Cada desligamento gera custos (aviso prévio, multa FGTS 40%, férias
        proporcionais). Empresas que não provisionam esses custos na planilha
        (tipicamente 3% a 5% sobre o custo de pessoal) enfrentam problemas de
        fluxo de caixa ao longo do contrato.
      </p>

      {/* Section 9: Como vencer */}
      <h2>Como vencer em licitações de limpeza: o preço é 80% do critério</h2>

      <p>
        Em pregões eletrônicos de limpeza, o critério de julgamento é quase sempre
        menor preço. Isso significa que a capacidade de formular o preço mais baixo
        viável — sem ser inexequível — é o fator decisivo. A margem de diferença
        entre propostas vencedoras e classificadas em segundo lugar costuma ser
        inferior a 3%.
      </p>

      <p>
        As empresas que consistentemente vencem licitações de limpeza compartilham
        três características:
      </p>

      <p>
        <strong>Domínio da planilha:</strong> Conhecem profundamente cada componente
        de custo e conseguem otimizar sem cortar itens obrigatórios. A diferença
        entre propostas não está no salário (definido pela CCT) nem nos encargos
        (definidos por lei), mas nos custos de insumos, equipamentos e
        administração central — onde há espaço para eficiência.
      </p>

      <p>
        <strong>Escala operacional:</strong> Empresas com mais contratos conseguem
        diluir custos de administração central, comprar insumos com desconto de
        volume e manter equipe de supervisão compartilhada entre contratos
        próximos geograficamente.
      </p>

      <p>
        <strong>Gestão de pessoal eficiente:</strong> O maior custo é pessoal.
        Empresas que conseguem reduzir turnover (via benefícios, treinamento,
        boas condições de trabalho) economizam nos custos de rescisão e
        recrutamento, permitindo preços mais competitivos. Para uma abordagem
        estruturada sobre como analisar a viabilidade de cada edital antes de
        investir na proposta, consulte{' '}
        <Link href="/blog/analise-viabilidade-editais-guia" className="text-brand-navy dark:text-brand-blue hover:underline">
          o guia de análise de viabilidade de editais
        </Link>.
      </p>

      <div className="not-prose my-6 sm:my-8 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 sm:p-6">
        <p className="text-sm font-semibold text-ink mb-3">
          Exemplo prático — Formação de preço por posto de limpeza em SP
        </p>
        <ul className="space-y-1.5 text-sm text-ink-secondary">
          <li>
            <strong>Salário base (CCT SP 2024/25):</strong> R$ 1.870,00
          </li>
          <li>
            <strong>Encargos sociais e trabalhistas (72%):</strong> R$ 1.346,40
          </li>
          <li>
            <strong>Benefícios CCT (VT, VA, plano odontológico):</strong> R$ 520,00
          </li>
          <li>
            <strong>Insumos de limpeza:</strong> R$ 280,00
          </li>
          <li>
            <strong>Uniformes e EPIs (amortizado):</strong> R$ 120,00
          </li>
          <li>
            <strong>Equipamentos (depreciação):</strong> R$ 85,00
          </li>
          <li>
            <strong>Supervisão (proporcional):</strong> R$ 190,00
          </li>
          <li>
            <strong>Subtotal custo direto:</strong> R$ 4.411,40
          </li>
          <li>
            <strong>BDI (20%):</strong> R$ 882,28
          </li>
          <li className="pt-2 font-semibold">
            Preço por posto/mês: R$ 5.293,68
          </li>
        </ul>
      </div>

      {/* Section 10: Repactuação */}
      <h2>Repactuação: como manter a rentabilidade ao longo do contrato</h2>

      <p>
        A repactuação é o mecanismo que permite reequilibrar o contrato após
        mudanças nos custos de mão de obra (dissídio) e insumos. Diferente do
        reajuste por índice (que aplica um único percentual), a repactuação
        exige demonstração item a item da variação de custos, com base na
        nova CCT e nos preços de mercado.
      </p>

      <p>
        O art. 135 da Lei 14.133/2021 prevê a repactuação para contratos de serviços
        continuados com mão de obra dedicada. O processo funciona assim: após a
        vigência da nova CCT (que define o novo piso salarial), a empresa solicita
        a repactuação ao órgão contratante, apresentando planilha de custos
        atualizada. O órgão analisa, negocia e, se os valores estiverem adequados,
        formaliza o aditivo contratual com efeitos retroativos à data da nova CCT.
      </p>

      <p>
        Na prática, o processo pode levar de 60 a 120 dias entre a solicitação e o
        pagamento do retroativo. Nesse período, a empresa absorve a diferença de
        custo. Por isso, é essencial manter reserva de capital de giro proporcional
        ao número de contratos ativos e ao impacto esperado do dissídio.
      </p>

      {/* CTA Section */}
      <div className="not-prose mt-8 sm:mt-12 bg-brand-blue-subtle dark:bg-brand-navy/20 rounded-xl p-5 sm:p-8 text-center border border-brand-blue/20">
        <p className="text-lg sm:text-xl font-bold text-ink mb-2">
          Encontre editais de limpeza e facilities com o SmartLic — 14 dias grátis
        </p>
        <p className="text-sm sm:text-base text-ink-secondary mb-4 sm:mb-6 max-w-lg mx-auto">
          O SmartLic monitora o PNCP e classifica editais por setor usando IA.
          Receba licitações de limpeza, conservação e facilities compatíveis com
          seu perfil — filtradas por UF, valor e modalidade.
        </p>
        <Link
          href="/signup?source=blog&article=licitações-limpeza-facilities-2026&utm_source=blog&utm_medium=cta&utm_content=licitações-limpeza-facilities-2026&utm_campaign=guias"
          className="inline-block bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-5 sm:px-6 py-2.5 sm:py-3 rounded-button text-sm sm:text-base transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Teste Grátis por 14 Dias
        </Link>
        <p className="text-xs text-ink-secondary mt-3">
          Sem cartão de crédito. Veja todas as funcionalidades na{' '}
          <Link href="/features" className="underline hover:text-ink">
            página de recursos
          </Link>.
        </p>
      </div>

      {/* FAQ Section */}
      <h2>Perguntas Frequentes</h2>

      <h3>Como montar planilha de custos para licitação de limpeza?</h3>
      <p>
        A planilha deve incluir remuneração base conforme a CCT vigente do local
        de execução, encargos sociais e trabalhistas (65% a 80% sobre o salário),
        insumos de limpeza, EPIs e uniformes, equipamentos (depreciação), custos
        indiretos (supervisão, administração central) e BDI (15% a 25%). A soma
        de todos os componentes gera o custo por posto de serviço. Siga o modelo
        da IN SEGES/ME 5/2017 como referência e adapte aos termos específicos
        do edital. Cada item deve ser justificado com base em convenção coletiva,
        pesquisa de mercado ou norma regulatória.
      </p>

      <h3>Qual o peso da convenção coletiva na formação de preço?</h3>
      <p>
        A CCT é o fator determinante. O salário base definido pela convenção
        representa entre 50% e 60% do custo total do posto, e os encargos
        incidentes sobre o salário elevam esse percentual para 70% a 82%.
        Cada reajuste anual (dissídio) impacta diretamente o preço. Empresas
        que não projetam o dissídio na formação de preço correm risco de operar
        com margem negativa após o reajuste.{' '}
        <Link href="/glossario#valor-estimado" className="text-brand-navy dark:text-brand-blue hover:underline">
          Entender o valor estimado
        </Link>{' '}
        do edital em relação à CCT é fundamental.
      </p>

      <h3>Preciso de quantos atestados de capacidade?</h3>
      <p>
        A Lei 14.133/2021 permite exigência de atestados que comprovem até 50%
        do quantitativo licitado (art. 67, parágrafo 1). Na prática, editais de
        limpeza exigem entre 1 e 3 atestados demonstrando experiência com serviços
        similares, indicando número de postos ou área atendida, período de execução
        e qualidade do serviço. Atestados de contratos públicos têm maior peso,
        mas contratos privados são aceitos quando acompanhados de notas fiscais e
        contrato.
      </p>

      <h3>É possível participar em UFs diferentes da sede?</h3>
      <p>
        Sim, não há restrição legal. Porém, é essencial considerar que a CCT
        aplicável é a do local de execução (não a da sede), o que altera
        significativamente os custos. Muitos editais exigem escritório ou preposto
        na cidade de execução durante a vigência. Além disso, a logística de
        supervisão, recrutamento e fornecimento de insumos deve ser planejada
        para a localidade de destino, não para a origem.
      </p>

      <h3>Como funciona a repactuação de contratos de limpeza?</h3>
      <p>
        A repactuação (art. 135 da Lei 14.133/2021) é o reajuste de contratos de
        serviços continuados baseado na variação de custos efetivos. Após a vigência
        da nova CCT, o contratado solicita repactuação apresentando planilha
        atualizada. O órgão analisa e formaliza aditivo com efeitos retroativos.
        O prazo mínimo para a primeira repactuação é 12 meses da data do orçamento.
        Na prática, o processo leva 60 a 120 dias entre solicitação e pagamento,
        exigindo capital de giro da empresa para absorver o custo nesse período. Consulte
        também{' '}
        <Link href="/glossario#habilitação" className="text-brand-navy dark:text-brand-blue hover:underline">
          os requisitos de habilitação
        </Link>{' '}
        para garantir conformidade durante todo o contrato.
      </p>

      <h3>O que é BDI e como calcular para serviços de limpeza?</h3>
      <p>
        BDI (Bonificação e Despesas Indiretas) é o percentual aplicado sobre os
        custos diretos para cobrir administração central, seguros, riscos, impostos
        sobre faturamento (ISS, PIS, COFINS, CSLL, IRPJ) e margem de lucro. Para
        serviços de limpeza, o BDI típico varia entre 15% e 25%. O cálculo segue a
        fórmula do TCU (Acórdão 2622/2013-Plenário). Na prática, BDI abaixo de 15%
        levanta suspeita de inexequibilidade, e acima de 30% pode ser questionado
        na análise de aceitabilidade. O regime tributário da empresa (Simples Nacional,
        Lucro Presumido ou Real) impacta diretamente o componente de impostos dentro
        do BDI.
      </p>
    </>
  );
}
