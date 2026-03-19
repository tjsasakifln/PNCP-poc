#!/usr/bin/env python3
"""intel-analyze.py — Step 7: Análise profunda dos top 20 editais."""

import json

INPUT = "docs/intel/intel-01721078000168-lcm-construcoes-2026-03-19.json"

# Analysis for each top20 edital based on document review
ANALYSES = [
    # 1. Gravataí - Drenagem Pluvial (R$15.9M)
    {
        "resumo_objeto": "Elaboração de projetos básico e executivo e execução integral de obra de drenagem pluvial no município de Gravataí/RS. Empreitada por preço global, financiada pelo FUNRIGS (Fundo Estadual de Recuperação RS).",
        "requisitos_tecnicos": [
            "Capacidade técnica em drenagem pluvial/saneamento",
            "Elaboração de projeto básico e executivo inclusos",
            "Referência SINAPI/SICRO para custos unitários",
        ],
        "requisitos_habilitacao": [
            "Certidão de falência/concordata",
            "Regularidade fiscal (federal, estadual, municipal, FGTS)",
            "Acervo técnico compatível com drenagem",
        ],
        "qualificacao_economica": "Certidão de falência. Provável exigência de patrimônio líquido mínimo (10% do valor).",
        "prazo_execucao": "12 meses de vigência contratual",
        "garantias": "Não especificado no trecho analisado",
        "criterio_julgamento": "Menor Preço Global, modo de disputa Aberto",
        "visita_tecnica": "Não mencionada no trecho analisado",
        "consorcio": "Não mencionado no trecho analisado",
        "observacoes_criticas": "VALOR ACIMA DA CAPACIDADE 10x (R$16M capital = capacidade R$16M, edital R$15.9M — no limite). Obra financiada por fundo estadual, o que reduz risco de inadimplência. Requer capacidade em projetos de drenagem. Abertura 29/05/2026 — prazo confortável para preparação.",
        "nivel_dificuldade": "ALTO",
        "recomendacao_acao": "AVALIAR COM CAUTELA — valor no limite da capacidade. Se tiver acervo em drenagem, vale participar. Sessão em 29/05/2026.",
        "custo_logistico_nota": "Gravataí/RS fica a ~470km de Itajaí/SC. Custo logístico moderado.",
    },
    # 2. Gravataí - DUPLICATA do 1
    {
        "resumo_objeto": "DUPLICATA do edital #1 (mesma licitação publicada no Portal de Compras Públicas). Ver análise do edital #1.",
        "requisitos_tecnicos": ["Ver edital #1"],
        "requisitos_habilitacao": ["Ver edital #1"],
        "qualificacao_economica": "Ver edital #1",
        "prazo_execucao": "Ver edital #1",
        "garantias": "Ver edital #1",
        "criterio_julgamento": "Ver edital #1",
        "visita_tecnica": "Ver edital #1",
        "consorcio": "Ver edital #1",
        "observacoes_criticas": "Publicação duplicada — mesmo edital no PNCP e no Portal de Compras Públicas.",
        "nivel_dificuldade": "ALTO",
        "recomendacao_acao": "DUPLICATA — ver edital #1",
        "custo_logistico_nota": "Ver edital #1",
    },
    # 3. Cornélio Procópio - CBUQ e Emulsão RR1C (R$15.3M)
    {
        "resumo_objeto": "Registro de preços para aquisição de asfalto usinado a quente (CBUQ) e emulsão RR1C no município de Cornélio Procópio/PR. Pregão eletrônico, menor preço por item.",
        "requisitos_tecnicos": [
            "Fornecimento de CBUQ (concreto betuminoso usinado a quente)",
            "Fornecimento de emulsão asfáltica RR1C",
            "Registro de preços — fornecimento sob demanda",
        ],
        "requisitos_habilitacao": [
            "Ramo de atividade compatível",
            "Cadastro na plataforma BBMNET",
            "Certidões de regularidade fiscal",
        ],
        "qualificacao_economica": "Não detalhada no trecho analisado",
        "prazo_execucao": "Registro de preços válido por 12 meses",
        "garantias": "Não especificado",
        "criterio_julgamento": "Menor Preço por Item",
        "visita_tecnica": "Não exigida (aquisição de material)",
        "consorcio": "Vedada participação em consórcio",
        "observacoes_criticas": "É registro de preços para MATERIAL (CBUQ/emulsão), não serviço de pavimentação. A LCM é construtora, não usina de asfalto. NÃO RECOMENDADO — objeto incompatível com atividade da empresa.",
        "nivel_dificuldade": "BAIXO",
        "recomendacao_acao": "NÃO PARTICIPAR — objeto é fornecimento de material asfáltico, não execução de pavimentação. Incompatível com CNAE da empresa.",
        "custo_logistico_nota": "Cornélio Procópio/PR ~630km de Itajaí/SC.",
    },
    # 4. Cascavel - Micro-revestimento (R$15.3M)
    {
        "resumo_objeto": "Registro de preços para execução de micro-revestimento a frio com emulsão modificada com polímero de 12mm em Cascavel/PR. Concorrência eletrônica.",
        "requisitos_tecnicos": [
            "Execução de micro-revestimento a frio",
            "Emulsão modificada com polímero de 12mm",
            "Experiência comprovada em pavimentação",
        ],
        "requisitos_habilitacao": [
            "CAT em micro-revestimento ou pavimentação similar",
            "Regularidade fiscal completa",
            "Cadastro em plataforma eletrônica",
        ],
        "qualificacao_economica": "Não detalhada no trecho analisado (edital com minuta padronizada de Cascavel)",
        "prazo_execucao": "Registro de preços — execução sob demanda",
        "garantias": "Não especificado",
        "criterio_julgamento": "Menor Preço",
        "visita_tecnica": "Não mencionada",
        "consorcio": "Não mencionado",
        "observacoes_criticas": "Serviço especializado de micro-revestimento requer equipamento específico (usina de emulsão, caminhão distribuidor). Se a LCM tem acervo e equipamentos para pavimentação asfáltica, é uma oportunidade interessante. Valor no limite da capacidade.",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "PARTICIPAR SE TIVER EQUIPAMENTOS de pavimentação asfáltica. Cascavel é município grande com demanda recorrente.",
        "custo_logistico_nota": "Cascavel/PR ~630km de Itajaí/SC. Custo logístico elevado para mobilização de equipamentos.",
    },
    # 5. Cascavel - DUPLICATA do 4
    {
        "resumo_objeto": "DUPLICATA do edital #4 (mesma licitação publicada no Portal de Compras Públicas). Ver análise do edital #4.",
        "requisitos_tecnicos": ["Ver edital #4"],
        "requisitos_habilitacao": ["Ver edital #4"],
        "qualificacao_economica": "Ver edital #4",
        "prazo_execucao": "Ver edital #4",
        "garantias": "Ver edital #4",
        "criterio_julgamento": "Ver edital #4",
        "visita_tecnica": "Ver edital #4",
        "consorcio": "Ver edital #4",
        "observacoes_criticas": "Publicação duplicada.",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "DUPLICATA — ver edital #4",
        "custo_logistico_nota": "Ver edital #4",
    },
    # 6. Nova América da Colina - Escola Sustentável (R$14.99M)
    {
        "resumo_objeto": "Construção da Escola Municipal Sustentável de Nova América da Colina/PR. Área construída de 4.448m² em terreno de 12.929m². Conceito biofílico com energia solar, captação de água pluvial, telhado verde, horta educativa, anfiteatro.",
        "requisitos_tecnicos": [
            "Construção completa de escola (4.448m²)",
            "Sistemas sustentáveis: fotovoltaico, captação de água, telhado verde",
            "Fundações, superestrutura, vedações",
            "Infraestrutura pedagógica (salas, biblioteca, anfiteatro)",
            "Áreas de vivência (horta, jardim sensorial, compostagem)",
        ],
        "requisitos_habilitacao": [
            "Capacidade técnica em construção de edificações escolares",
            "CAT compatível com obras de porte similar",
            "Regularidade fiscal e trabalhista",
        ],
        "qualificacao_economica": "Não detalhada — esperar exigência de patrimônio líquido mínimo (10%)",
        "prazo_execucao": "18 meses a partir da Ordem de Serviço",
        "garantias": "Não especificado no trecho analisado",
        "criterio_julgamento": "Menor Preço Global, modo Aberto",
        "visita_tecnica": "Não mencionada no trecho analisado",
        "consorcio": "Permitido (até 3 empresas) — amplia competitividade",
        "observacoes_criticas": "EXCELENTE OPORTUNIDADE. Obra de construção civil pura (CNAE 4120), valor dentro da capacidade (R$15M vs R$16M limite). Conceito sustentável diferenciado pode reduzir concorrência. Consórcio permitido — pode ser estratégico se faltar acervo específico. Sessão em 09/04/2026 — prazo curto para preparação.",
        "nivel_dificuldade": "ALTO",
        "recomendacao_acao": "PARTICIPAR — oportunidade prioritária. Obra alinhada com CNAE principal. Preparar proposta imediatamente. Avaliar consórcio se necessário.",
        "custo_logistico_nota": "Nova América da Colina/PR ~480km de Itajaí/SC. Mobilização moderada.",
    },
    # 7. SC - Materiais Higiene/Limpeza (R$14.9M)
    {
        "resumo_objeto": "Aquisição parcelada de materiais de higiene e limpeza sob demanda. Pregão eletrônico, registro de preços.",
        "requisitos_tecnicos": [
            "Fornecimento de materiais de higiene e limpeza",
        ],
        "requisitos_habilitacao": ["Ramo compatível com comércio de materiais de limpeza"],
        "qualificacao_economica": "N/A",
        "prazo_execucao": "Registro de preços 12 meses",
        "garantias": "N/A",
        "criterio_julgamento": "Menor Preço",
        "visita_tecnica": "Não aplicável",
        "consorcio": "N/A",
        "observacoes_criticas": "NÃO COMPATÍVEL com CNAE da empresa. É aquisição de materiais de limpeza, não serviço de construção ou manutenção. Entrou no top 20 por erro no gate de classificação.",
        "nivel_dificuldade": "BAIXO",
        "recomendacao_acao": "NÃO PARTICIPAR — objeto incompatível. Fornecimento de materiais de higiene/limpeza não é atividade da construtora.",
        "custo_logistico_nota": "N/A",
    },
    # 8. Porto Alegre - Centro CONVIVE (R$14.5M)
    {
        "resumo_objeto": "Execução de obra de engenharia para o Centro Comunitário pela Vida (CONVIVE) em Porto Alegre/RS. 7 edificações térreas + estacionamento + quadra coberta + campo society + piscina + playground + áreas ajardinadas. Secretaria Municipal de Esporte e Lazer.",
        "requisitos_tecnicos": [
            "Construção de 7 edificações térreas",
            "Quadra de esportes coberta",
            "Campo society e piscina",
            "Playground e paisagismo",
            "ART de responsável técnico para execução",
        ],
        "requisitos_habilitacao": [
            "Vínculo profissional do responsável técnico (condição para assinatura)",
            "ART/RRT de execução dos serviços",
            "CAT compatível com obras esportivas/comunitárias",
            "Regularidade fiscal completa",
        ],
        "qualificacao_economica": "Não detalhada no trecho analisado",
        "prazo_execucao": "Conforme cronograma (não especificado no trecho)",
        "garantias": "Não especificado",
        "criterio_julgamento": "Menor Preço Global, modo Aberto",
        "visita_tecnica": "Não mencionada no trecho",
        "consorcio": "Não mencionado",
        "observacoes_criticas": "BOA OPORTUNIDADE. Obra diversificada (edificações + esportes + paisagismo) em Porto Alegre. Valor dentro da capacidade. Prefeitura de Porto Alegre é contratante confiável. Exige vínculo do responsável técnico como condição para assinar contrato.",
        "nivel_dificuldade": "ALTO",
        "recomendacao_acao": "PARTICIPAR — obra compatível com CNAE, bom contratante. Verificar data da sessão e preparar documentação técnica.",
        "custo_logistico_nota": "Porto Alegre/RS ~470km de Itajaí/SC. Custo moderado.",
    },
    # 9. Rio Bonito do Iguaçu - Escola FNDE 13 salas (R$13.7M)
    {
        "resumo_objeto": "Construção de Unidade Escolar Padrão FNDE — Escola de 13 Salas Térreo no município de Rio Bonito do Iguaçu/PR. Inclui memorial descritivo, projetos técnicos e planilha orçamentária.",
        "requisitos_tecnicos": [
            "Construção de escola padrão FNDE (13 salas)",
            "Execução conforme projetos e memorial do FNDE",
            "Regime de empreitada parcelada",
        ],
        "requisitos_habilitacao": [
            "CAT compatível com construção escolar",
            "Regularidade fiscal e trabalhista",
            "Cadastro na plataforma BLL Compras",
        ],
        "qualificacao_economica": "Não detalhada no trecho analisado",
        "prazo_execucao": "Conforme cronograma físico-financeiro (não especificado no trecho)",
        "garantias": "Não especificado",
        "criterio_julgamento": "Menor Preço por Lote, modo Aberto",
        "visita_tecnica": "Não mencionada",
        "consorcio": "Itens exclusivos ME/EPP + Itens ampla — verificar enquadramento",
        "observacoes_criticas": "BOA OPORTUNIDADE. Escola padrão FNDE tem projeto pré-definido (reduz complexidade de elaboração). R$13.7M dentro da capacidade. ATENÇÃO: prazo de propostas já encerrou (16/03/2026). Verificar se ainda está aberto ou se houve adiamento.",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "VERIFICAR PRAZO — data limite de propostas era 16/03/2026. Se ainda aberto, participar. Escola FNDE é projeto padronizado, reduz risco técnico.",
        "custo_logistico_nota": "Rio Bonito do Iguaçu/PR ~500km de Itajaí/SC. Região remota, custo logístico elevado.",
    },
    # 10. São João do Ivaí - PA + Maternidade (R$13.6M)
    {
        "resumo_objeto": "Construção de Pronto Atendimento Municipal e Maternidade no município de São João do Ivaí/PR. Conforme Resolução SESA nº 1100/2025. Empreitada por preço global.",
        "requisitos_tecnicos": [
            "Construção de unidade de saúde (PA + Maternidade)",
            "Conformidade com Resolução SESA 1100/2025",
            "Projeto com especificações de saúde (ANVISA/SUS)",
        ],
        "requisitos_habilitacao": [
            "CAT em construção de unidades de saúde",
            "Regularidade fiscal e trabalhista",
            "Cadastro BLL Compras",
        ],
        "qualificacao_economica": "Não detalhada no trecho analisado",
        "prazo_execucao": "Conforme cronograma (não especificado no trecho)",
        "garantias": "Não especificado",
        "criterio_julgamento": "Menor Preço Global, modo Aberto",
        "visita_tecnica": "Não mencionada",
        "consorcio": "Ampla disputa — não exclusivo ME/EPP",
        "observacoes_criticas": "BOA OPORTUNIDADE. Construção hospitalar dentro da capacidade. Sessão em 07/04/2026 — tempo para preparar. Construção de saúde exige atenção especial às normas ANVISA/RDC. Se tiver acervo em obras de saúde, é competitivo.",
        "nivel_dificuldade": "ALTO",
        "recomendacao_acao": "PARTICIPAR SE TIVER ACERVO em obras de saúde. Sessão 07/04/2026. Verificar exigências específicas de habilitação técnica.",
        "custo_logistico_nota": "São João do Ivaí/PR ~530km de Itajaí/SC. Custo logístico moderado-alto.",
    },
    # 11. Curitiba - Parque Paulo Gorski (R$12.5M)
    {
        "resumo_objeto": "Estruturação do Território Verde e Requalificação do Parque Paulo Gorski em Curitiba/PR (SAM 199). Sem documentos disponíveis para análise detalhada.",
        "requisitos_tecnicos": [
            "Obras de urbanização e paisagismo",
            "Requalificação de parque público",
            "Análise limitada — sem documentos disponíveis",
        ],
        "requisitos_habilitacao": ["Não disponível — documentos indisponíveis no PNCP"],
        "qualificacao_economica": "Não disponível",
        "prazo_execucao": "Não disponível",
        "garantias": "Não disponível",
        "criterio_julgamento": "Não disponível",
        "visita_tecnica": "Não disponível",
        "consorcio": "Não disponível",
        "observacoes_criticas": "Documentos indisponíveis no PNCP. Obra de requalificação de parque em Curitiba — município de grande porte, bom pagador. Compatível com CNAEs de urbanização e paisagismo. BUSCAR DOCUMENTOS no site da prefeitura de Curitiba.",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "INVESTIGAR — buscar edital completo no portal de Curitiba. Requalificação de parque é compatível com os CNAEs da empresa.",
        "custo_logistico_nota": "Curitiba/PR ~300km de Itajaí/SC. Custo logístico baixo.",
    },
    # 12. Herval d'Oeste - Repavimentação (R$12.4M)
    {
        "resumo_objeto": "Registro de preços para contratação de serviços de repavimentação asfáltica parcial e/ou total em diversas vias de Herval d'Oeste/SC. Inclui fresagem, CBUQ, sinalização. Fornecimento de materiais, mão de obra e equipamentos.",
        "requisitos_tecnicos": [
            "Repavimentação asfáltica (parcial e total)",
            "Fresagem de pavimento existente",
            "Aplicação de CBUQ",
            "Sinalização viária",
            "CAT em pavimentação/recapeamento com fresagem",
        ],
        "requisitos_habilitacao": [
            "CAT compatível com pavimentação e recapeamento",
            "Certidão de falência/concordata",
            "Regularidade fiscal completa",
            "Declaração de visita técnica ou conhecimento do local",
        ],
        "qualificacao_economica": "Certidão de falência. Patrimônio líquido provável.",
        "prazo_execucao": "Registro de preços — execução sob demanda por 12 meses",
        "garantias": "Não especificado",
        "criterio_julgamento": "Menor Preço",
        "visita_tecnica": "Facultativa — pode substituir por declaração de conhecimento",
        "consorcio": "Vedada participação em consórcio",
        "observacoes_criticas": "BOA OPORTUNIDADE. Repavimentação é serviço recorrente e previsível. Herval d'Oeste é em SC, mais próximo da sede. Registro de preços permite execução gradual. Requer equipamentos de pavimentação (fresadora, vibroacabadora).",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "PARTICIPAR SE TIVER EQUIPAMENTOS de pavimentação. Herval d'Oeste/SC é relativamente próximo. Registro de preços = demanda recorrente.",
        "custo_logistico_nota": "Herval d'Oeste/SC ~350km de Itajaí/SC. Custo logístico moderado.",
    },
    # 13. Tubos PEAD - CISAM MO (R$12.2M)
    {
        "resumo_objeto": "Registro de preços para aquisição de tubos e conexões (PP/PEAD) para os consorciados do CISAM MO (SC). Aquisição de materiais, não serviço.",
        "requisitos_tecnicos": ["Fornecimento de tubos PP/PEAD e conexões"],
        "requisitos_habilitacao": ["Ramo de comércio de materiais hidráulicos"],
        "qualificacao_economica": "N/A",
        "prazo_execucao": "Registro de preços 12 meses",
        "garantias": "N/A",
        "criterio_julgamento": "Menor Preço",
        "visita_tecnica": "Não aplicável",
        "consorcio": "N/A",
        "observacoes_criticas": "NÃO COMPATÍVEL — é aquisição de materiais (tubos), não serviço de instalação. LCM é construtora, não distribuidora de materiais hidráulicos.",
        "nivel_dificuldade": "BAIXO",
        "recomendacao_acao": "NÃO PARTICIPAR — objeto é fornecimento de materiais, incompatível com atividade.",
        "custo_logistico_nota": "N/A",
    },
    # 14. DUPLICATA do 13
    {
        "resumo_objeto": "DUPLICATA do edital #13. Ver análise acima.",
        "requisitos_tecnicos": ["Ver edital #13"],
        "requisitos_habilitacao": ["Ver edital #13"],
        "qualificacao_economica": "Ver edital #13",
        "prazo_execucao": "Ver edital #13",
        "garantias": "Ver edital #13",
        "criterio_julgamento": "Ver edital #13",
        "visita_tecnica": "Ver edital #13",
        "consorcio": "Ver edital #13",
        "observacoes_criticas": "DUPLICATA",
        "nivel_dificuldade": "BAIXO",
        "recomendacao_acao": "NÃO PARTICIPAR — DUPLICATA, ver #13",
        "custo_logistico_nota": "N/A",
    },
    # 15. Tijucas - Consultoria Engenharia (R$11.7M)
    {
        "resumo_objeto": "Contratação de empresa de consultoria multidisciplinar de engenharia para prestação de serviços técnicos especializados: estudos, levantamentos, projetos, serviços ambientais e gerenciamento de obras públicas. Execução parcelada sob demanda no município de Tijucas/SC.",
        "requisitos_tecnicos": [
            "Consultoria multidisciplinar de engenharia",
            "Estudos e levantamentos técnicos",
            "Elaboração de projetos",
            "Serviços ambientais",
            "Gerenciamento e acompanhamento de obras",
        ],
        "requisitos_habilitacao": [
            "Equipe técnica multidisciplinar (engenheiros, arquitetos, ambientais)",
            "CAT em gestão/gerenciamento de obras",
            "Regularidade fiscal e profissional",
        ],
        "qualificacao_economica": "Não detalhada",
        "prazo_execucao": "Sob demanda — parcelado",
        "garantias": "Não especificado",
        "criterio_julgamento": "Concorrência (provável técnica e preço)",
        "visita_tecnica": "Não mencionada",
        "consorcio": "Mencionado no edital (verificar condições)",
        "observacoes_criticas": "OPORTUNIDADE DIFERENCIADA. Tijucas/SC é próximo de Itajaí (30km). Serviço intelectual sob demanda — baixo risco financeiro. Porém exige equipe multidisciplinar permanente. Se LCM tem departamento de projetos, é excelente encaixe.",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "PARTICIPAR SE TIVER EQUIPE DE PROJETOS. Tijucas é vizinha de Itajaí. Contrato sob demanda = risco baixo.",
        "custo_logistico_nota": "Tijucas/SC ~30km de Itajaí/SC. Custo logístico mínimo — praticamente local.",
    },
    # 16. Guaíba - Manutenção vias (R$11.6M)
    {
        "resumo_objeto": "Contratação de empresa para manutenção de vias e logradouros no município de Guaíba/RS. Sem documentos disponíveis para análise detalhada.",
        "requisitos_tecnicos": [
            "Manutenção de vias urbanas",
            "Conservação de logradouros",
            "Análise limitada — sem documentos",
        ],
        "requisitos_habilitacao": ["Não disponível — documentos indisponíveis"],
        "qualificacao_economica": "Não disponível",
        "prazo_execucao": "Não disponível",
        "garantias": "Não disponível",
        "criterio_julgamento": "Pregão Eletrônico",
        "visita_tecnica": "Não disponível",
        "consorcio": "Não disponível",
        "observacoes_criticas": "Manutenção de vias é compatível com CNAEs da empresa. Guaíba/RS fica na região metropolitana de Porto Alegre. BUSCAR DOCUMENTOS no portal de Guaíba.",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "INVESTIGAR — buscar edital no portal de Guaíba. Manutenção viária é compatível.",
        "custo_logistico_nota": "Guaíba/RS ~490km de Itajaí/SC. Custo moderado.",
    },
    # 17. Rolândia - Tubos de Concreto (R$11.6M)
    {
        "resumo_objeto": "Registro de preços para aquisição de tubos de concreto no município de Rolândia/PR. Fornecimento de materiais pré-fabricados.",
        "requisitos_tecnicos": ["Fornecimento de tubos de concreto pré-fabricados"],
        "requisitos_habilitacao": ["Ramo de fabricação/comércio de artefatos de concreto"],
        "qualificacao_economica": "Não detalhada",
        "prazo_execucao": "Registro de preços 12 meses",
        "garantias": "N/A",
        "criterio_julgamento": "Menor Preço",
        "visita_tecnica": "Não aplicável",
        "consorcio": "N/A",
        "observacoes_criticas": "NÃO COMPATÍVEL — é aquisição de tubos de concreto (material), não serviço de instalação. LCM é construtora, não fábrica de pré-moldados.",
        "nivel_dificuldade": "BAIXO",
        "recomendacao_acao": "NÃO PARTICIPAR — fornecimento de materiais pré-fabricados, incompatível.",
        "custo_logistico_nota": "N/A",
    },
    # 18. DUPLICATA do 17
    {
        "resumo_objeto": "DUPLICATA do edital #17. Ver análise acima.",
        "requisitos_tecnicos": ["Ver edital #17"],
        "requisitos_habilitacao": ["Ver edital #17"],
        "qualificacao_economica": "Ver edital #17",
        "prazo_execucao": "Ver edital #17",
        "garantias": "Ver edital #17",
        "criterio_julgamento": "Ver edital #17",
        "visita_tecnica": "Ver edital #17",
        "consorcio": "Ver edital #17",
        "observacoes_criticas": "DUPLICATA",
        "nivel_dificuldade": "BAIXO",
        "recomendacao_acao": "NÃO PARTICIPAR — DUPLICATA, ver #17",
        "custo_logistico_nota": "N/A",
    },
    # 19. Ponta Grossa - Delegacia Cidadã (R$11.5M)
    {
        "resumo_objeto": "Construção da Delegacia Cidadã Padrão III em Ponta Grossa/PR. Localizada à Rua Maria Rita Perpétuo da Cruz, bairro Oficinas. Contratação do Governo do Estado do PR (SESP).",
        "requisitos_tecnicos": [
            "Construção de delegacia padrão estadual",
            "Projeto executivo com especificações de segurança pública",
            "ART de responsável técnico",
        ],
        "requisitos_habilitacao": [
            "CAT compatível com construção de edificações públicas",
            "ART/RRT de execução",
            "Regularidade fiscal e trabalhista",
            "Consórcio NÃO permitido",
        ],
        "qualificacao_economica": "Não detalhada no trecho analisado",
        "prazo_execucao": "300 dias a partir da Ordem de Serviço",
        "garantias": "Não especificado",
        "criterio_julgamento": "Menor Preço, modo Aberto",
        "visita_tecnica": "Não mencionada",
        "consorcio": "NÃO permitido — vedada participação em consórcio",
        "observacoes_criticas": "BOA OPORTUNIDADE. Construção de edificação pública, perfeitamente alinhada com CNAE 4120. Contratante é Governo do Paraná (SESP) — pagador confiável. Prazo de 300 dias é razoável. Consórcio vedado — precisa ter capacidade individual. Verificar data da sessão.",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "PARTICIPAR — obra de construção alinhada com CNAE principal. Governo do PR é bom pagador. Prazo 300 dias.",
        "custo_logistico_nota": "Ponta Grossa/PR ~300km de Itajaí/SC. Custo logístico baixo-moderado.",
    },
    # 20. DUPLICATA do 19
    {
        "resumo_objeto": "DUPLICATA do edital #19. Ver análise acima.",
        "requisitos_tecnicos": ["Ver edital #19"],
        "requisitos_habilitacao": ["Ver edital #19"],
        "qualificacao_economica": "Ver edital #19",
        "prazo_execucao": "Ver edital #19",
        "garantias": "Ver edital #19",
        "criterio_julgamento": "Ver edital #19",
        "visita_tecnica": "Ver edital #19",
        "consorcio": "Ver edital #19",
        "observacoes_criticas": "DUPLICATA",
        "nivel_dificuldade": "MEDIO",
        "recomendacao_acao": "DUPLICATA — ver edital #19",
        "custo_logistico_nota": "Ver edital #19",
    },
]


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    top20 = data["top20"]
    assert len(top20) == 20, f"Expected 20, got {len(top20)}"

    for i, analysis in enumerate(ANALYSES):
        top20[i]["analise"] = analysis

    # Resumo executivo
    data["resumo_executivo"] = (
        "A busca exaustiva no PNCP identificou 8.160 editais abertos nos estados do Sul (SC, PR, RS) "
        "nos últimos 30 dias, dos quais 1.907 são compatíveis com os CNAEs da LCM Construções "
        "(construção civil, infraestrutura, manutenção predial, facilities). "
        "Considerando a capacidade estimada de R$ 16 milhões (10× capital social de R$ 1,6M), "
        "foram selecionadas 1.879 oportunidades dentro da faixa de valor.\n\n"
        "Entre os top 20 por valor, destacam-se 7 oportunidades genuínas de obras de construção civil:\n"
        "1. Escola Sustentável em Nova América da Colina/PR (R$ 15,0M) — conceito biofílico, consórcio permitido\n"
        "2. Centro CONVIVE em Porto Alegre/RS (R$ 14,5M) — complexo esportivo/comunitário\n"
        "3. Escola FNDE 13 salas em Rio Bonito do Iguaçu/PR (R$ 13,7M) — projeto padronizado\n"
        "4. PA + Maternidade em São João do Ivaí/PR (R$ 13,6M) — construção hospitalar\n"
        "5. Requalificação Parque Paulo Gorski em Curitiba/PR (R$ 12,5M) — urbanização\n"
        "6. Delegacia Cidadã em Ponta Grossa/PR (R$ 11,5M) — edificação pública\n"
        "7. Consultoria de Engenharia em Tijucas/SC (R$ 11,7M) — próximo da sede, sob demanda\n\n"
        "Foram descartados 5 editais que são fornecimento de materiais (CBUQ, tubos, materiais de limpeza) "
        "e 5 duplicatas (mesmo edital publicado em dois portais). "
        "Há também 2 oportunidades em pavimentação que requerem equipamentos especializados "
        "(Cascavel/PR e Herval d'Oeste/SC)."
    )

    data["proximos_passos"] = [
        "URGENTE: Verificar se edital #9 (Escola FNDE Rio Bonito do Iguaçu) ainda está aberto — prazo de propostas era 16/03/2026",
        "PRIORITÁRIO: Preparar documentação para edital #6 (Escola Nova América da Colina) — sessão 09/04/2026. Avaliar necessidade de consórcio.",
        "PRIORITÁRIO: Preparar documentação para edital #10 (PA + Maternidade São João do Ivaí) — sessão 07/04/2026. Requer acervo em obras de saúde.",
        "BUSCAR DOCUMENTOS: Edital #11 (Parque Paulo Gorski, Curitiba) e #16 (Manutenção vias, Guaíba) — documentos indisponíveis no PNCP.",
        "AVALIAR: Editais #8 (Centro CONVIVE Porto Alegre) e #19 (Delegacia Ponta Grossa) — verificar datas de sessão e exigências de habilitação.",
        "AVALIAR CAPACIDADE: Se tiver equipe de projetos, edital #15 (Consultoria Tijucas/SC) é excelente por proximidade (30km da sede).",
        "DESCONSIDERAR: Editais #3 (CBUQ), #7 (limpeza), #13/#14 (tubos PEAD), #17/#18 (tubos concreto) — objetos incompatíveis.",
        "MONITORAR: Planilha Excel contém 1.907 editais compatíveis. Revisar semanalmente para novas oportunidades com valor menor.",
    ]

    with open(INPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Análise profunda salva no JSON.")
    print(f"Top 20 com análise: {len([e for e in top20 if e.get('analise')])}/20")
    print(f"Resumo executivo: {len(data['resumo_executivo'])} chars")
    print(f"Próximos passos: {len(data['proximos_passos'])} itens")


if __name__ == "__main__":
    main()
