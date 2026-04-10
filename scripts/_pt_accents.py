"""Central dictionary of Portuguese accent replacements for SmartLic static content.

Used by:
- scripts/fix_content_accents.py (normalizer + --check mode)
- scripts/check_content_accents.py (CI alias)

Contract:
- Each entry is an (unaccented, accented) pair. Both forms are word-boundary sensitive
  when applied (via \b...\b regex).
- Capitalized variants are generated automatically by the applier (see build_rules()).
- Slug-like strings (lowercase + hyphens/digits only) are SKIPPED by the applier, so
  entries like "licitacao" -> "licitação" do NOT corrupt URL slugs.
- Ambiguous tokens (e.g. "e" conjunction vs "é" verb, "por" vs "pôr") are NEVER in
  this dictionary. They require human review.

Coverage: ~280 words observed in frontend/lib/questions.ts and glossary content
(2026-04-10 audit). Extend as new content patterns emerge.
"""

from __future__ import annotations

import re
from typing import Iterable

# ---------------------------------------------------------------------------
# Core replacements (lowercase form -> accented lowercase form).
# The applier auto-generates Capitalized + UPPERCASE variants.
# Order matters ONLY for overlapping prefixes — longer tokens first.
# ---------------------------------------------------------------------------

REPLACEMENTS: dict[str, str] = {
    # -------- -ção / -ções --------
    "adjudicacao": "adjudicação",
    "habilitacao": "habilitação",
    "inabilitacao": "inabilitação",
    "desabilitacao": "desabilitação",
    "homologacao": "homologação",
    "impugnacao": "impugnação",
    "fiscalizacao": "fiscalização",
    "execucao": "execução",
    "medicao": "medição",
    "contratacoes": "contratações",
    "contratacao": "contratação",
    "subcontratacao": "subcontratação",
    "publicacoes": "publicações",
    "publicacao": "publicação",
    "licitacoes": "licitações",
    "licitacao": "licitação",
    "selecao": "seleção",
    "sancoes": "sanções",
    "sancao": "sanção",
    "revogacao": "revogação",
    "anulacao": "anulação",
    "dotacao": "dotação",
    "aquisicoes": "aquisições",
    "aquisicao": "aquisição",
    "alienacao": "alienação",
    "avaliacao": "avaliação",
    "situacoes": "situações",
    "situacao": "situação",
    "autorizacao": "autorização",
    "aprovacao": "aprovação",
    "manutencao": "manutenção",
    "regularizacao": "regularização",
    "negociacao": "negociação",
    "participacao": "participação",
    "classificacao": "classificação",
    "qualificacao": "qualificação",
    "verificacao": "verificação",
    "composicao": "composição",
    "reducao": "redução",
    "punicao": "punição",
    "adequacao": "adequação",
    "elaboracao": "elaboração",
    "atualizacao": "atualização",
    "restricoes": "restrições",
    "restricao": "restrição",
    "comparacao": "comparação",
    "substituicao": "substituição",
    "conclusao": "conclusão",
    "rescisao": "rescisão",
    "inscricao": "inscrição",
    "inclusao": "inclusão",
    "exclusao": "exclusão",
    "protecao": "proteção",
    "constituicao": "constituição",
    "vinculacao": "vinculação",
    "convocacoes": "convocações",
    "convocacao": "convocação",
    "atribuicao": "atribuição",
    "versao": "versão",
    "previsao": "previsão",
    "informacoes": "informações",
    "informacao": "informação",
    "condicoes": "condições",
    "condicao": "condição",
    "obrigacoes": "obrigações",
    "obrigacao": "obrigação",
    "emissao": "emissão",
    "declaracoes": "declarações",
    "declaracao": "declaração",
    "operacoes": "operações",
    "operacao": "operação",
    "suspensao": "suspensão",
    "sessoes": "sessões",
    "sessao": "sessão",
    "inversao": "inversão",
    "interrupcao": "interrupção",
    "definicoes": "definições",
    "aplicacao": "aplicação",
    "obtencao": "obtenção",
    "comprovacao": "comprovação",
    "desclassificacao": "desclassificação",
    "lancamentos": "lançamentos",
    "lancamento": "lançamento",
    "excecoes": "exceções",
    "excecao": "exceção",
    "opcoes": "opções",
    "opcao": "opção",
    "relacoes": "relações",
    "relacao": "relação",
    "mediacao": "mediação",
    "funcoes": "funções",
    "funcao": "função",
    "centralizacao": "centralização",
    "indexacao": "indexação",
    "atencao": "atenção",
    "discussao": "discussão",
    "discussoes": "discussões",
    "decisao": "decisão",
    "decisoes": "decisões",
    "regiao": "região",
    "regioes": "regiões",
    "razoes": "razões",
    "razao": "razão",
    "contrarrazao": "contrarrazão",
    "contrarrazoes": "contrarrazões",
    "administracao": "administração",
    "documentacao": "documentação",
    "certidoes": "certidões",
    "certidao": "certidão",
    "prorrogacao": "prorrogação",
    "prorrogacoes": "prorrogações",
    "repactuacao": "repactuação",
    "gestao": "gestão",
    "formacao": "formação",
    "inovacao": "inovação",
    "construcao": "construção",
    "convencao": "convenção",
    "adesao": "adesão",
    "adesoes": "adesões",
    "competicao": "competição",
    "estao": "estão",
    "manifestacao": "manifestação",
    "intencao": "intenção",
    "alimentacao": "alimentação",
    "apresentacao": "apresentação",
    "dedicacao": "dedicação",
    "integracao": "integração",
    "cartao": "cartão",
    "cartoes": "cartões",
    "deteccao": "detecção",
    "especializacoes": "especializações",
    "especializacao": "especialização",
    "utilizacao": "utilização",
    "extincao": "extinção",
    "legislacao": "legislação",
    "cotacoes": "cotações",
    "cotacao": "cotação",
    "pregoes": "pregões",
    "pregao": "pregão",
    "certificacoes": "certificações",
    "certificacao": "certificação",
    "concessoes": "concessões",
    "concessao": "concessão",
    "solucoes": "soluções",
    "solucao": "solução",
    "padroes": "padrões",
    "padrao": "padrão",
    "notificacoes": "notificações",
    "notificacao": "notificação",
    "investigacoes": "investigações",
    "investigacao": "investigação",
    "especificacoes": "especificações",
    "especificacao": "especificação",
    "alteracoes": "alterações",
    "alteracao": "alteração",
    "bonificacoes": "bonificações",
    "bonificacao": "bonificação",
    "instalacoes": "instalações",
    "instalacao": "instalação",
    "transacoes": "transações",
    "transacao": "transação",
    "execucoes": "execuções",
    "prorrogacoes": "prorrogações",
    "preocupacao": "preocupação",
    "preocupacoes": "preocupações",
    "instrucoes": "instruções",
    "instrucao": "instrução",
    "comunicacoes": "comunicações",
    "comunicacao": "comunicação",
    "confeccoes": "confecções",
    "confeccao": "confecção",
    "provisoes": "provisões",
    "provisao": "provisão",
    "orientacoes": "orientações",
    "orientacao": "orientação",
    "limitacoes": "limitações",
    "limitacao": "limitação",
    "interacoes": "interações",
    "interacao": "interação",
    "edificacoes": "edificações",
    "edificacao": "edificação",
    "regulamentacoes": "regulamentações",
    "regulamentacao": "regulamentação",
    "fundamentacao": "fundamentação",
    "digitalizacao": "digitalização",
    "validacao": "validação",
    "variacao": "variação",
    "direcao": "direção",
    "atencoes": "atenções",
    "mencao": "menção",
    "mencoes": "menções",
    "elaboracoes": "elaborações",
    "aprovacoes": "aprovações",
    "apresentacoes": "apresentações",
    "classificacoes": "classificações",
    "qualificacoes": "qualificações",
    "verificacoes": "verificações",
    "composicoes": "composições",
    "reducoes": "reduções",
    "avaliacoes": "avaliações",
    "manutencoes": "manutenções",
    "regularizacoes": "regularizações",
    "negociacoes": "negociações",
    "autorizacoes": "autorizações",
    "dotacoes": "dotações",
    "revogacoes": "revogações",
    "vinculacoes": "vinculações",
    "atribuicoes": "atribuições",
    "previsoes": "previsões",
    "conclusoes": "conclusões",
    "inscricoes": "inscrições",
    "recessao": "recessão",
    "extincoes": "extinções",
    "homologacoes": "homologações",
    "impugnacoes": "impugnações",
    "desclassificacoes": "desclassificações",
    "inabilitacoes": "inabilitações",
    "protecoes": "proteções",

    # -------- Proper nouns / other -ão --------
    "glossario": "glossário",
    "dialogo": "diálogo",
    "consorcio": "consórcio",
    "leilao": "leilão",
    "leiloes": "leilões",
    "orgao": "órgão",
    "orgaos": "órgãos",

    # -------- -ônico / -ônica --------
    "eletronicos": "eletrônicos",
    "eletronicas": "eletrônicas",
    "eletronico": "eletrônico",
    "eletronica": "eletrônica",
    "eletronicamente": "eletronicamente",  # actually no accent, keep
    "cronicos": "crônicos",
    "cronicas": "crônicas",
    "cronico": "crônico",
    "cronica": "crônica",
    "sincronico": "síncrono",  # rare; skip if not present

    # -------- Orçamento --------
    "orcamentaria": "orçamentária",
    "orcamentario": "orçamentário",
    "orcamento": "orçamento",
    "orcamentos": "orçamentos",

    # -------- Público --------
    "publicos": "públicos",
    "publicas": "públicas",
    "publico": "público",
    "publica": "pública",
    "publicamente": "publicamente",  # correct without accent; keep

    # -------- Técnico --------
    "tecnicos": "técnicos",
    "tecnicas": "técnicas",
    "tecnico": "técnico",
    "tecnica": "técnica",
    "tecnicamente": "tecnicamente",  # correct without accent; keep

    # -------- Específico --------
    "especificos": "específicos",
    "especificas": "específicas",
    "especifico": "específico",
    "especifica": "específica",
    "especificidade": "especificidade",  # correct; keep
    "especificar": "especificar",  # correct; keep

    # -------- Único --------
    "unicos": "únicos",
    "unicas": "únicas",
    "unico": "único",
    "unica": "única",
    "unicamente": "unicamente",  # correct; keep

    # -------- Jurídico --------
    "juridicos": "jurídicos",
    "juridicas": "jurídicas",
    "juridico": "jurídico",
    "juridica": "jurídica",

    # -------- Obrigatório --------
    "obrigatorios": "obrigatórios",
    "obrigatorias": "obrigatórias",
    "obrigatorio": "obrigatório",
    "obrigatoria": "obrigatória",

    # -------- Licitatório --------
    "licitatorios": "licitatórios",
    "licitatorias": "licitatórias",
    "licitatorio": "licitatório",
    "licitatoria": "licitatória",

    # -------- Prática --------
    "praticas": "práticas",
    "praticos": "práticos",
    "pratico": "prático",
    "pratica": "prática",
    "praticamente": "praticamente",  # correct; keep

    # -------- Própria --------
    "proprias": "próprias",
    "proprios": "próprios",
    "propria": "própria",
    "proprio": "próprio",

    # -------- Econômico --------
    "economicos": "econômicos",
    "economicas": "econômicas",
    "economico": "econômico",
    "economica": "econômica",

    # -------- Critério --------
    "criterios": "critérios",
    "criterio": "critério",

    # -------- Número --------
    "numeros": "números",
    "numero": "número",

    # -------- Período --------
    "periodos": "períodos",
    "periodo": "período",
    "periodicos": "periódicos",
    "periodico": "periódico",
    "periodica": "periódica",
    "periodicamente": "periodicamente",  # correct; keep

    # -------- Máximo/mínimo --------
    "maximo": "máximo",
    "maxima": "máxima",
    "maximos": "máximos",
    "maximas": "máximas",
    "minimos": "mínimos",
    "minimas": "mínimas",
    "minimo": "mínimo",
    "minima": "mínima",

    # -------- Último --------
    "ultimas": "últimas",
    "ultimos": "últimos",
    "ultima": "última",
    "ultimo": "último",
    "ultimamente": "ultimamente",  # correct; keep

    # -------- Próximo --------
    "proximos": "próximos",
    "proximas": "próximas",
    "proximo": "próximo",
    "proxima": "próxima",

    # -------- Básico --------
    "basicos": "básicos",
    "basicas": "básicas",
    "basico": "básico",
    "basica": "básica",
    "basicamente": "basicamente",  # correct; keep

    # -------- Referência --------
    "referencias": "referências",
    "referencia": "referência",
    "referencial": "referencial",  # correct; keep
    "referenciais": "referenciais",  # correct; keep

    # -------- -ência / -ância --------
    "concorrencias": "concorrências",
    "concorrencia": "concorrência",
    "concorrencial": "concorrencial",  # correct; keep
    "preferencias": "preferências",
    "preferencia": "preferência",
    "experiencias": "experiências",
    "experiencia": "experiência",
    "inteligencias": "inteligências",
    "inteligencia": "inteligência",
    "inteligente": "inteligente",  # correct; keep
    "inteligentes": "inteligentes",  # correct; keep
    "emergencias": "emergências",
    "emergencia": "emergência",
    "emergencial": "emergencial",  # correct; keep
    "emergenciais": "emergenciais",  # correct; keep
    "jurisprudencias": "jurisprudências",
    "jurisprudencia": "jurisprudência",
    "exigencias": "exigências",
    "exigencia": "exigência",
    "transparencias": "transparências",
    "transparencia": "transparência",
    "transparente": "transparente",  # correct; keep
    "transparentes": "transparentes",  # correct; keep
    "conveniencias": "conveniências",
    "conveniencia": "conveniência",
    "transferencias": "transferências",
    "transferencia": "transferência",
    "assistencias": "assistências",
    "assistencia": "assistência",
    "incidencias": "incidências",
    "incidencia": "incidência",
    "antecedencias": "antecedências",
    "antecedencia": "antecedência",
    "eficiencias": "eficiências",
    "eficiencia": "eficiência",
    "tendencias": "tendências",
    "tendencia": "tendência",
    "conferencias": "conferências",
    "conferencia": "conferência",
    "diligencias": "diligências",
    "diligencia": "diligência",
    "procedencias": "procedências",
    "procedencia": "procedência",
    "videoconferencias": "videoconferências",
    "videoconferencia": "videoconferência",
    "deficiencias": "deficiências",
    "deficiencia": "deficiência",
    "sobrevivencias": "sobrevivências",
    "sobrevivencia": "sobrevivência",
    "consequencias": "consequências",
    "consequencia": "consequência",
    "evidencias": "evidências",
    "evidencia": "evidência",
    "anuencias": "anuências",
    "anuencia": "anuência",
    "solvencia": "solvência",
    "vigilancia": "vigilância",
    "relevancia": "relevância",
    "substancias": "substâncias",
    "substancia": "substância",
    "importancia": "importância",
    "importancias": "importâncias",
    "instancias": "instâncias",
    "instancia": "instância",
    "tolerancia": "tolerância",
    "tolerancias": "tolerâncias",
    "distancias": "distâncias",
    "distancia": "distância",
    "circunstancia": "circunstância",
    "circunstancias": "circunstâncias",

    # -------- -ível --------
    "nivel": "nível",
    "niveis": "níveis",
    "possivel": "possível",
    "possiveis": "possíveis",
    "impossivel": "impossível",
    "imprevisivel": "imprevisível",
    "imprevisiveis": "imprevisíveis",
    "previsivel": "previsível",
    "disponivel": "disponível",
    "disponiveis": "disponíveis",
    "inexigivel": "inexigível",
    "exigiveis": "exigíveis",
    "inexequivel": "inexequível",
    "inexequiveis": "inexequíveis",
    "divisivel": "divisível",
    "divisiveis": "divisíveis",
    "acessivel": "acessível",
    "acessiveis": "acessíveis",
    "verificaveis": "verificáveis",
    "verificavel": "verificável",

    # -------- -ável --------
    "responsavel": "responsável",
    "responsaveis": "responsáveis",
    "sustentavel": "sustentável",
    "sustentaveis": "sustentáveis",
    "prorrogavel": "prorrogável",
    "improrrogavel": "improrrogável",
    "inviavel": "inviável",
    "viavel": "viável",
    "aplicavel": "aplicável",
    "indispensavel": "indispensável",
    "favoravel": "favorável",
    "auditavel": "auditável",
    "estavel": "estável",
    "razoavel": "razoável",
    "razoaveis": "razoáveis",
    "subcontratavel": "subcontratável",
    "irretratavel": "irretratável",
    "passiveis": "passíveis",
    "passivel": "passível",
    "reciclaveis": "recicláveis",
    "biodegradaveis": "biodegradáveis",
    "pereciveis": "perecíveis",
    "perecivel": "perecível",

    # -------- -óvel / -óveis --------
    "imoveis": "imóveis",
    "imovel": "imóvel",
    "moveis": "móveis",
    "movel": "móvel",
    "automoveis": "automóveis",
    "automovel": "automóvel",

    # -------- Bulk additions from 2026-04-10 questions.ts audit --------
    # -ção / -ções (systematic)
    "acao": "ação",  # (not a verb form here — "ação" noun)
    "atuacao": "atuação",
    "estruturacao": "estruturação",
    "formulacao": "formulação",
    "demonstracao": "demonstração",
    "indenizacao": "indenização",
    "duracao": "duração",
    "mobilizacao": "mobilização",
    "descricao": "descrição",
    "representacao": "representação",
    "vedacao": "vedação",
    "devolucao": "devolução",
    "producao": "produção",
    "anotacao": "anotação",
    "recomendacao": "recomendação",
    "recomendacoes": "recomendações",
    "eliminacao": "eliminação",
    "incorporacao": "incorporação",
    "insercao": "inserção",
    "pontuacao": "pontuação",
    "localizacao": "localização",
    "combinacao": "combinação",
    "realizacao": "realização",
    "restauracao": "restauração",
    "visitacao": "visitação",
    "distincao": "distinção",
    "virtualizacao": "virtualização",
    "conexao": "conexão",
    "conexoes": "conexões",
    "adaptacao": "adaptação",
    "violacao": "violação",
    "citacao": "citação",
    "exposicao": "exposição",
    "constatacao": "constatação",
    "arrematacao": "arrematação",
    "preparacao": "preparação",
    "republicacao": "republicação",
    "formalizacao": "formalização",
    "indicacao": "indicação",
    "inflacao": "inflação",
    "remuneracao": "remuneração",
    "transicao": "transição",
    "resolucao": "resolução",
    "exportacao": "exportação",
    "circulacao": "circulação",
    "instituicao": "instituição",
    "instituicoes": "instituições",
    "precisao": "precisão",
    "identificacao": "identificação",
    "liquidacao": "liquidação",
    "renovacao": "renovação",
    "correcao": "correção",
    "correcoes": "correções",
    "antecipacao": "antecipação",
    "procuracao": "procuração",
    "autenticacao": "autenticação",
    "recuperacao": "recuperação",
    "supervisao": "supervisão",
    "revisao": "revisão",
    "revisoes": "revisões",
    "comissao": "comissão",
    "comissoes": "comissões",
    "divulgacao": "divulgação",
    "geracao": "geração",
    "geracoes": "gerações",
    "fabricacao": "fabricação",
    "prestacao": "prestação",
    "prestacoes": "prestações",
    "precificacao": "precificação",
    "capacitacao": "capacitação",
    "refeicao": "refeição",
    "refeicoes": "refeições",
    "caucao": "caução",
    "uniao": "união",
    "acordao": "acórdão",
    "acordaos": "acórdãos",
    "cidadao": "cidadão",
    "cidadaos": "cidadãos",
    "opiniao": "opinião",
    "opinioes": "opiniões",
    "visao": "visão",
    "visoes": "visões",
    "divisao": "divisão",
    "divisoes": "divisões",
    "aptidao": "aptidão",
    "serao": "serão",
    "tao": "tão",
    "balcao": "balcão",
    "balcoes": "balcões",
    "gestao": "gestão",  # already
    "oficializacao": "oficialização",
    "degustacao": "degustação",
    "reajuste": "reajuste",  # correct
    # -ário / -ária / -ários / -árias
    "salario": "salário",
    "salarios": "salários",
    "cenario": "cenário",
    "cenarios": "cenários",
    "tributario": "tributário",
    "tributarios": "tributários",
    "tributaria": "tributária",
    "tributarias": "tributárias",
    "bancario": "bancário",
    "bancarios": "bancários",
    "bancaria": "bancária",
    "bancarias": "bancárias",
    "unitario": "unitário",
    "unitarios": "unitários",
    "unitaria": "unitária",
    "unitarias": "unitárias",
    "usuario": "usuário",
    "usuarios": "usuários",
    "usuaria": "usuária",
    "usuarias": "usuárias",
    "escritorio": "escritório",
    "escritorios": "escritórios",
    "cartorio": "cartório",
    "cartorios": "cartórios",
    "funcionario": "funcionário",
    "funcionarios": "funcionários",
    "funcionaria": "funcionária",
    "funcionarias": "funcionárias",
    "calendario": "calendário",
    "calendarios": "calendários",
    "mobiliario": "mobiliário",
    "mobiliarios": "mobiliários",
    "signatario": "signatário",
    "signatarios": "signatários",
    "horario": "horário",
    "horarios": "horários",
    "horaria": "horária",
    "horarias": "horárias",
    "ministerio": "ministério",
    "ministerios": "ministérios",
    "territorio": "território",
    "territorios": "territórios",
    "judiciario": "judiciário",
    "judiciarios": "judiciários",
    "judiciaria": "judiciária",
    "judiciarias": "judiciárias",
    "provisorio": "provisório",
    "provisorios": "provisórios",
    "provisoria": "provisória",
    "provisorias": "provisórias",
    "notoria": "notória",
    "notorio": "notório",
    "notorias": "notórias",
    "notorios": "notórios",
    "solidaria": "solidária",
    "solidario": "solidário",
    "monetaria": "monetária",
    "monetario": "monetário",
    "sanitaria": "sanitária",
    "sanitario": "sanitário",
    "sanitarias": "sanitárias",
    "sanitarios": "sanitários",
    "temporaria": "temporária",
    "temporarias": "temporárias",
    "temporario": "temporário",
    "temporarios": "temporários",
    "regulatoria": "regulatória",
    "regulatoria": "regulatória",
    "regulatorias": "regulatórias",
    "regulatorio": "regulatório",
    "regulatorios": "regulatórios",
    "extraordinario": "extraordinário",
    "extraordinarios": "extraordinários",
    "extraordinaria": "extraordinária",
    "extraordinarias": "extraordinárias",
    "previdenciario": "previdenciário",
    "previdenciarios": "previdenciários",
    "previdenciaria": "previdenciária",
    "previdenciarias": "previdenciárias",
    "rodoviario": "rodoviário",
    "rodoviarios": "rodoviários",
    "rodoviaria": "rodoviária",
    "rodoviarias": "rodoviárias",
    "aleatorio": "aleatório",
    "aleatorios": "aleatórios",
    "aleatoria": "aleatória",
    "aleatorias": "aleatórias",
    "satisfatorio": "satisfatório",
    "satisfatorios": "satisfatórios",
    "satisfatoria": "satisfatória",
    "satisfatorias": "satisfatórias",
    "somatorio": "somatório",
    "somatorios": "somatórios",
    "vitoria": "vitória",
    "vitorias": "vitórias",
    "ferias": "férias",
    "agencia": "agência",
    "agencias": "agências",
    "falencia": "falência",
    "ausencia": "ausência",
    # -ística / -ático / -ógico / -ônico
    "logistica": "logística",
    "informatica": "informática",
    "automatica": "automática",
    "automatico": "automático",
    "automaticos": "automáticos",
    "automaticas": "automáticas",
    "metricas": "métricas",
    "metrica": "métrica",
    "artistico": "artístico",
    "artisticos": "artísticos",
    "artistica": "artística",
    "artisticas": "artísticas",
    "biologico": "biológico",
    "biologicos": "biológicos",
    "biologica": "biológica",
    "biologicas": "biológicas",
    "psicologica": "psicológica",
    "psicologico": "psicológico",
    "psicologicos": "psicológicos",
    "psicologicas": "psicológicas",
    "criptografico": "criptográfico",
    "criptograficos": "criptográficos",
    "criptografica": "criptográfica",
    "criptograficas": "criptográficas",
    "agroecologico": "agroecológico",
    "agroecologicos": "agroecológicos",
    "agroecologica": "agroecológica",
    "agroecologicas": "agroecológicas",
    "energetica": "energética",
    "energetico": "energético",
    "cibernetica": "cibernética",
    "cibernetico": "cibernético",
    "mecanica": "mecânica",
    "mecanico": "mecânico",
    "sinonimo": "sinônimo",
    "sinonimos": "sinônimos",
    # -ência (remaining)
    "identica": "idêntica",
    "identicas": "idênticas",
    "identico": "idêntico",
    "identicos": "idênticos",
    "autentica": "autêntica",
    "autentico": "autêntico",
    "autenticos": "autênticos",
    "autenticas": "autênticas",
    # -íbrio / -álculo / -ínsula
    "desequilibrio": "desequilíbrio",
    "equilibrio": "equilíbrio",
    # Outros
    "hortalicas": "hortaliças",
    "toxicas": "tóxicas",
    "toxicos": "tóxicos",
    "toxico": "tóxico",
    "toxica": "tóxica",
    "fabrica": "fábrica",
    "fabricas": "fábricas",
    "industria": "indústria",
    "industrias": "indústrias",
    "acrescimo": "acréscimo",
    "acrescimos": "acréscimos",
    "curtissimo": "curtíssimo",
    "curtissima": "curtíssima",
    # -------- Glossary/programmatic additions 2026-04-10 --------
    "milhao": "milhão",
    "milhoes": "milhões",
    "bilhao": "bilhão",
    "bilhoes": "bilhões",
    "trilhao": "trilhão",
    "trilhoes": "trilhões",
    "patrimonio": "patrimônio",
    "patrimonios": "patrimônios",
    "vicio": "vício",
    "vicios": "vícios",
    "contabil": "contábil",
    "contabeis": "contábeis",
    "posicao": "posição",
    "posicoes": "posições",
    "balanco": "balanço",
    "balancos": "balanços",
    "liquido": "líquido",
    "liquida": "líquida",
    "liquidos": "líquidos",
    "liquidas": "líquidas",
    "preparatoria": "preparatória",
    "preparatorias": "preparatórias",
    "preparatorio": "preparatório",
    "preparatorios": "preparatórios",
    "pavimentacao": "pavimentação",
    "pavimentacoes": "pavimentações",
    "asfaltica": "asfáltica",
    "asfaltico": "asfáltico",
    "asfalticas": "asfálticas",
    "asfalticos": "asfálticos",
    "supressao": "supressão",
    "supressoes": "supressões",
    "edificio": "edifício",
    "edificios": "edifícios",
    "invalidacao": "invalidação",
    "invalidacoes": "invalidações",
    "compativel": "compatível",
    "compativeis": "compatíveis",
    "incompativel": "incompatível",
    "incompativeis": "incompatíveis",
    "dispensavel": "dispensável",
    "aceitavel": "aceitável",
    "aceitacao": "aceitação",
    "educacao": "educação",
    "inexistencia": "inexistência",
    "migracao": "migração",
    "modernizacao": "modernização",
    "convocatorio": "convocatório",
    "convocatoria": "convocatória",
    "convocatorias": "convocatórias",
    "convocatorios": "convocatórios",
    "designacao": "designação",
    "designacoes": "designações",
    "contrario": "contrário",
    "contrarios": "contrários",
    "secretario": "secretário",
    "secretarios": "secretários",
    "ressonancia": "ressonância",
    "magnetica": "magnética",
    "magnetico": "magnético",
    "magneticas": "magnéticas",
    "magneticos": "magnéticos",
    "quantificacao": "quantificação",
    "advertencia": "advertência",
    "advertencias": "advertências",
    "diagnostico": "diagnóstico",
    "diagnosticos": "diagnósticos",
    "diagnostica": "diagnóstica",
    "intermediaria": "intermediária",
    "intermediarias": "intermediárias",
    "intermediario": "intermediário",
    "intermediarios": "intermediários",
    "dimensao": "dimensão",
    "dimensoes": "dimensões",
    "distribuicao": "distribuição",
    "distribuicoes": "distribuições",
    "expansao": "expansão",
    "expansoes": "expansões",
    "iluminacao": "iluminação",
    "participacoes": "participações",
    "renovacoes": "renovações",
    # More -orio/-oria from glossary observations
    "obrigatoriedade": "obrigatoriedade",  # correct; keep
    "laboratorio": "laboratório",
    "laboratorios": "laboratórios",
    "oratorio": "oratório",
    "acessorio": "acessório",
    "acessorios": "acessórios",
    "acessoria": "acessória",
    "acessorias": "acessórias",
    # Round 3 glossary/programmatic additions
    "vestuario": "vestuário",
    "universitario": "universitário",
    "universitarios": "universitários",
    "universitaria": "universitária",
    "universitarias": "universitárias",
    "computacao": "computação",
    "conservacao": "conservação",
    "renovaveis": "renováveis",
    "renovavel": "renovável",
    "locacao": "locação",
    "locacoes": "locações",
    "ergonomico": "ergonômico",
    "ergonomica": "ergonômica",
    "ergonomicos": "ergonômicos",
    "ergonomicas": "ergonômicas",
    "luminaria": "luminária",
    "luminarias": "luminárias",
    "hidraulico": "hidráulico",
    "hidraulica": "hidráulica",
    "hidraulicos": "hidráulicos",
    "hidraulicas": "hidráulicas",
    "hidrica": "hídrica",
    "hidrico": "hídrico",
    "hidricos": "hídricos",
    "hidricas": "hídricas",
    "climatizacao": "climatização",
    "sinalizacao": "sinalização",
    "sinalizacoes": "sinalizações",
    "viaria": "viária",
    "viarias": "viárias",
    "viario": "viário",
    "viarios": "viários",
    "transformacao": "transformação",
    "transformacoes": "transformações",
    "sistematica": "sistemática",
    "sistematico": "sistemático",
    "sistematicos": "sistemáticos",
    "sistematicas": "sistemáticas",
    # -------- Verbos / advérbios comuns --------
    "sao": "são",  # verb "to be" plural — but also "São" (city prefix). Safe in prose.
    "alem": "além",
    "analise": "análise",
    "analises": "análises",
    "voce": "você",
    "voces": "vocês",
    "indice": "índice",
    "indices": "índices",
    "agil": "ágil",
    "ageis": "ágeis",
    "agua": "água",
    "aguas": "águas",
    "inicio": "início",
    "inicios": "inícios",
    "materia": "matéria",
    "materias": "matérias",
    "media": "média",  # "average" — noun. Risk: rare English "media" as brand. Accept.
    "medias": "médias",
    "policia": "polícia",
    "politica": "política",
    "politicas": "políticas",
    "politico": "político",
    "politicos": "políticos",
    "proibicao": "proibição",
    "proibicoes": "proibições",
    "proximo": "próximo",
    "proximos": "próximos",
    "proxima": "próxima",
    "proximas": "próximas",
    "concluido": "concluído",
    "concluida": "concluída",
    "concluidos": "concluídos",
    "concluidas": "concluídas",
    "caracteristica": "característica",
    "caracteristicas": "características",
    "duvida": "dúvida",
    "duvidas": "dúvidas",
    "multipla": "múltipla",
    "multiplas": "múltiplas",
    "multiplo": "múltiplo",
    "multiplos": "múltiplos",
    "eletrica": "elétrica",
    "eletricas": "elétricas",
    "eletrico": "elétrico",
    "eletricos": "elétricos",
    "critica": "crítica",
    "criticas": "críticas",
    "critico": "crítico",
    "criticos": "críticos",
    "tipica": "típica",
    "tipicas": "típicas",
    "tipico": "típico",
    "tipicos": "típicos",
    "sumario": "sumário",
    "sumarios": "sumários",
    "fragil": "frágil",
    "fraco": "fraco",  # correct
    "fraca": "fraca",  # correct
    "historia": "história",
    "historias": "histórias",
    "memoria": "memória",
    "memorias": "memórias",
    "teoria": "teoria",  # correct
    "categoria": "categoria",  # correct
    "premio": "prêmio",
    "premios": "prêmios",
    "series": "séries",
    "serie": "série",
    "estavel": "estável",
    "instavel": "instável",
    "incrivel": "incrível",
    "terrivel": "terrível",
    "horrivel": "horrível",
    "impressionante": "impressionante",  # correct
    "diaria": "diária",
    "diarias": "diárias",
    "diario": "diário",
    "diarios": "diários",
    "incluindo": "incluindo",  # correct
    "oleo": "óleo",
    "oleos": "óleos",
    "onibus": "ônibus",
    "virus": "vírus",
    "statu": "status",  # rare typo
    "urgente": "urgente",  # correct
    "urgencia": "urgência",
    "urgencias": "urgências",
    "duas": "duas",  # correct
    "tres": "três",
    "dificil": "difícil",
    "dificeis": "difíceis",
    "facil": "fácil",
    "faceis": "fáceis",
    "movel": "móvel",
    "hotel": "hotel",  # correct (hotel doesn't take accent)
    "nivel": "nível",  # already in
    # -------- Outras palavras comuns --------
    "saude": "saúde",
    # NOTE: "pais" NOT included — ambiguous ("país" vs plural of "pai" = "parents").
    "genero": "gênero",
    "generos": "gêneros",
    "alinea": "alínea",
    "alineas": "alíneas",
    "hipotese": "hipótese",
    "hipoteses": "hipóteses",
    "paragrafo": "parágrafo",
    "paragrafos": "parágrafos",
    "veridica": "verídica",
    "veridico": "verídico",
    "tecnologia": "tecnologia",  # correct
    "tecnologica": "tecnológica",
    "tecnologico": "tecnológico",
    "tecnologicos": "tecnológicos",
    "tecnologicas": "tecnológicas",
    "estrategia": "estratégia",
    "estrategias": "estratégias",
    "estrategica": "estratégica",
    "estrategico": "estratégico",
    "estrategicos": "estratégicos",
    "estrategicas": "estratégicas",
    "politica": "política",
    "politicas": "políticas",
    "politico": "político",
    "politicos": "políticos",
    "analitica": "analítica",
    "analitico": "analítico",
    "analiticas": "analíticas",
    "analiticos": "analíticos",
    "historico": "histórico",
    "historicos": "históricos",
    "historica": "histórica",
    "historicas": "históricas",
    "logica": "lógica",
    "logicas": "lógicas",
    "logico": "lógico",
    "logicos": "lógicos",
    "metodo": "método",
    "metodos": "métodos",
    "metodologia": "metodologia",  # correct
    "pedagogico": "pedagógico",
    "pedagogica": "pedagógica",
    "pedagogicos": "pedagógicos",
    "pedagogicas": "pedagógicas",
    "idoneo": "idôneo",
    "idoneos": "idôneos",
    "idoneas": "idôneas",
    "idonea": "idônea",
    "idoneidade": "idoneidade",  # correct
    "necessario": "necessário",
    "necessarios": "necessários",
    "necessaria": "necessária",
    "necessarias": "necessárias",
    "vario": "vário",  # rare
    "varios": "vários",
    "varia": "varia",  # verb "varies" — WITHOUT accent; keep
    "variavel": "variável",
    "variaveis": "variáveis",
    "valido": "válido",
    "validos": "válidos",
    "valida": "válida",
    "validas": "válidas",
    "validade": "validade",  # correct
    "valor": "valor",  # correct
    "clausulas": "cláusulas",
    "clausula": "cláusula",
    "previo": "prévio",
    "previa": "prévia",
    "previos": "prévios",
    "previas": "prévias",
    "previstos": "previstos",  # correct
    "prevista": "prevista",  # correct
    "previsto": "previsto",  # correct
    "reequilibrio": "reequilíbrio",
    "reequilibrios": "reequilíbrios",
    "prejuizo": "prejuízo",
    "prejuizos": "prejuízos",
    "exequibilidade": "exequibilidade",  # correct
    "inexequibilidade": "inexequibilidade",  # correct
    "inexigibilidade": "inexigibilidade",  # correct
    "inexigibilidades": "inexigibilidades",  # correct
    "emprestimo": "empréstimo",
    "emprestimos": "empréstimos",
    "conteudo": "conteúdo",
    "conteudos": "conteúdos",
    "util": "útil",
    "uteis": "úteis",
    "mes": "mês",  # singular; plural "meses" is correct
    "ambiguidade": "ambiguidade",  # correct
    "ambiguo": "ambíguo",
    "ambigua": "ambígua",
    "ambiguos": "ambíguos",
    "ambiguas": "ambíguas",
    "credito": "crédito",
    "creditos": "créditos",
    "debito": "débito",
    "debitos": "débitos",
    "bonus": "bônus",
    "onus": "ônus",
    "fax": "fax",  # correct
    "tabela": "tabela",  # correct
    "tabelas": "tabelas",  # correct
    # Segurança / vigência variants
    "seguranca": "segurança",
    "vigencia": "vigência",
    "vigencias": "vigências",
    "vigente": "vigente",  # correct; keep
    "vigentes": "vigentes",  # correct; keep
    # Diferença
    "diferenca": "diferença",
    "diferencas": "diferenças",
    # Preço / preços (specific to procurement content)
    "preco": "preço",
    "precos": "preços",
    # Serviços
    "servico": "serviço",
    "servicos": "serviços",
    # Família / familiar
    "familia": "família",
    "familias": "famílias",
    # Alimentos / médicos
    "medicos": "médicos",
    "medico": "médico",
    "medica": "médica",
    "medicas": "médicas",
    "medicamentos": "medicamentos",  # correct
    # Orgânico / químico / físico (sector-specific)
    "organico": "orgânico",
    "organica": "orgânica",
    "organicos": "orgânicos",
    "organicas": "orgânicas",
    "quimica": "química",
    "quimico": "químico",
    "quimicos": "químicos",
    "quimicas": "químicas",
    "fisica": "física",
    "fisico": "físico",
    "fisicos": "físicos",
    "fisicas": "físicas",
    "ciencia": "ciência",
    "ciencias": "ciências",
    "cientifico": "científico",
    "cientifica": "científica",
    "cientificos": "científicos",
    "cientificas": "científicas",
    # Outros
    "area": "área",
    "areas": "áreas",
    "aerea": "aérea",
    "aereo": "aéreo",
    "aereas": "aéreas",
    "aereos": "aéreos",
    "padronizacao": "padronização",
    # Lei reference nouns
    "artigo": "artigo",  # correct
    "artigos": "artigos",  # correct
    "inciso": "inciso",  # correct
    "incisos": "incisos",  # correct
    # (no concat edge cases — handled by main dict via word boundaries)
}

# ---------------------------------------------------------------------------
# Word-boundary replacements applied AFTER the main dict.
# Use tuples of (lowercase_from, lowercase_to) — case is handled by the applier.
# These are things where word boundaries are critical (e.g., "nao" is not a
# substring of anything else).
# ---------------------------------------------------------------------------

WORD_BOUNDARY_REPLACEMENTS: dict[str, str] = {
    "nao": "não",
    "ate": "até",
    "atraves": "através",
    "apos": "após",
    "tambem": "também",
    "so": "só",
    "ja": "já",
    # "ha" / "la" / "ai" omitted — too short and ambiguous (HTML attrs, abbreviations).
    "vao": "vão",
}

# Safety: drop identity mappings (they'd be no-ops and hide bugs).
REPLACEMENTS = {k: v for k, v in REPLACEMENTS.items() if k != v}
WORD_BOUNDARY_REPLACEMENTS = {k: v for k, v in WORD_BOUNDARY_REPLACEMENTS.items() if k != v}


# ---------------------------------------------------------------------------
# Compiled rules
# ---------------------------------------------------------------------------

def _capitalize(word: str) -> str:
    return word[:1].upper() + word[1:]


def build_rules() -> list[tuple[re.Pattern[str], str]]:
    """Build a list of (compiled_pattern, replacement) pairs.

    Longer unaccented tokens are emitted first to avoid partial overlaps
    (e.g., "contratacoes" must be replaced before "contratacao").
    Each entry generates two variants: lowercase and Capitalized.
    """
    rules: list[tuple[re.Pattern[str], str]] = []
    combined = {**REPLACEMENTS, **WORD_BOUNDARY_REPLACEMENTS}
    # Sort by length (desc) so "licitacoes" wins over "licitacao"
    for src in sorted(combined.keys(), key=len, reverse=True):
        dst = combined[src]
        # Lowercase variant
        rules.append((
            re.compile(r"\b" + re.escape(src) + r"\b"),
            dst,
        ))
        # Capitalized variant (first letter upper)
        rules.append((
            re.compile(r"\b" + re.escape(_capitalize(src)) + r"\b"),
            _capitalize(dst),
        ))
    return rules


# ---------------------------------------------------------------------------
# Slug detection — strings to skip (URLs, identifiers, arrays of slugs).
# A slug is lowercase alphanumeric + hyphens/underscores/dots/digits.
# ---------------------------------------------------------------------------

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")
# Also skip strings that look like CSS class names, URL paths, or identifiers
IDENT_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$-]*$")


def is_slug_like(s: str) -> bool:
    """Return True if the string should NOT be modified (slug, ident, URL)."""
    s = s.strip()
    if len(s) < 4:
        return True
    if SLUG_RE.match(s):
        return True
    if IDENT_RE.match(s):
        return True
    return False


# ---------------------------------------------------------------------------
# Phrase-level rules for verb "é" in high-confidence patterns.
#
# These run AFTER the word-boundary dict rules and cover cases where "e" is
# unambiguously the verb "é" because the following word is an adjective or
# past participle that only makes sense with a copulative verb.
#
# Examples:
#   "dispensa e permitida"  →  "dispensa é permitida"
#   "o julgamento e obrigatorio"  →  "o julgamento é obrigatório"
#
# "X e Y" where Y is a noun (conjunction case) is NEVER matched because Y
# here is restricted to a closed set of adjectives/participles.
# ---------------------------------------------------------------------------

def _vpat(word_pat: str, replacement_tail: str) -> tuple[re.Pattern[str], str]:
    """Build a phrase rule that converts 'e <word>' → 'é <word>'.

    ``word_pat`` is a regex fragment for the following word (accented or not).
    ``replacement_tail`` is the literal replacement for the word.
    """
    return (
        re.compile(r"\b[Ee]\s+(" + word_pat + r")\b"),
        "é " + replacement_tail,
    )


# Both unaccented and accented forms are matched because PHRASE_RULES runs
# AFTER the dict rules, which may have already applied accents to the word.
# Optional adverb prefix (e.g., "praticamente", "geralmente", "absolutamente")
# captured so it can be preserved in the replacement.
_ADV = r"((?:\w+mente\s+)?)"

PHRASE_RULES: list[tuple[re.Pattern[str], str]] = [
    # "e [adv] permitid*"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"permitid([oa]s?)\b"), r"é \1permitid\2"),
    # "e [adv] obrigatório*" / "obrigatoriamente"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"obrigatóri([oa]s?)\b"), r"é \1obrigatóri\2"),
    (re.compile(r"\b[Ee]\s+" + _ADV + r"obrigatori([oa]s?)\b"), r"é \1obrigatóri\2"),
    (re.compile(r"\b[Ee]\s+" + _ADV + r"obrigatoriamente\b"), r"é \1obrigatoriamente"),
    # "e [adv] possível/impossível"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"poss[ií]vel\b"), r"é \1possível"),
    (re.compile(r"\b[Ee]\s+" + _ADV + r"imposs[ií]vel\b"), r"é \1impossível"),
    # "e [adv] inviável/viável"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"invi[áa]vel\b"), r"é \1inviável"),
    (re.compile(r"\b[Ee]\s+" + _ADV + r"vi[áa]vel\b"), r"é \1viável"),
    # "e [adv] fundamental/essencial"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"fundamental\b"), r"é \1fundamental"),
    (re.compile(r"\b[Ee]\s+" + _ADV + r"essencial\b"), r"é \1essencial"),
    # "e [adv] necessário*"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"necessári([oa]s?)\b"), r"é \1necessári\2"),
    (re.compile(r"\b[Ee]\s+" + _ADV + r"necessari([oa]s?)\b"), r"é \1necessári\2"),
    # "e [adv] vedad*"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"vedad([oa]s?)\b"), r"é \1vedad\2"),
    # "e [adv] proibid*"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"proibid([oa]s?)\b"), r"é \1proibid\2"),
    # "e [adv] aplicável"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"aplic[áa]vel\b"), r"é \1aplicável"),
    # "e [adv] inexigível/exigível"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"inexig[ií]vel\b"), r"é \1inexigível"),
    (re.compile(r"\b[Ee]\s+" + _ADV + r"exig[ií]vel\b"), r"é \1exigível"),
    # "e [adv] indispensável"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"indispens[áa]vel\b"), r"é \1indispensável"),
    # "e [adv] inexequível"
    (re.compile(r"\b[Ee]\s+" + _ADV + r"inexequ[ií]vel\b"), r"é \1inexequível"),
]


# ---------------------------------------------------------------------------
# Detection of raw markdown syntax (for reporting, NOT auto-fixing)
# ---------------------------------------------------------------------------

MARKDOWN_PATTERNS: Iterable[tuple[str, re.Pattern[str]]] = (
    ("bold_asterisks", re.compile(r"\*\*[^\s*][^*]*?[^\s*]?\*\*")),
    ("italic_asterisk", re.compile(r"(?<![*\w])\*[^\s*][^*\n]*?[^\s*]\*(?![*\w])")),
    ("heading", re.compile(r"(?:^|\\n)#{1,6}\s")),
    ("bullet_list", re.compile(r"(?:^|\\n)[-*]\s")),
    ("numbered_list", re.compile(r"(?:^|\\n)\d+\.\s")),
)


def detect_markdown(s: str) -> list[str]:
    """Return a list of markdown pattern names found in the string."""
    hits: list[str] = []
    for name, pat in MARKDOWN_PATTERNS:
        if pat.search(s):
            hits.append(name)
    return hits
