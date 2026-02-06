"""
Multi-sector configuration for BidIQ procurement search.

Each sector defines a keyword set and exclusion list used by filter.py
to identify relevant procurement opportunities in PNCP data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from filter import KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO


@dataclass(frozen=True)
class SectorConfig:
    """Configuration for a procurement sector."""

    id: str
    name: str
    description: str
    keywords: Set[str]
    exclusions: Set[str] = field(default_factory=set)


SECTORS: Dict[str, SectorConfig] = {
    "vestuario": SectorConfig(
        id="vestuario",
        name="Vestuário e Uniformes",
        description="Uniformes, fardamentos, roupas profissionais, EPIs de vestuário",
        keywords=KEYWORDS_UNIFORMES,
        exclusions=KEYWORDS_EXCLUSAO,
    ),
    "alimentos": SectorConfig(
        id="alimentos",
        name="Alimentos e Merenda",
        description="Gêneros alimentícios, merenda escolar, refeições, rancho",
        keywords={
            # High precision compound terms
            "genero alimenticio", "generos alimenticios",
            "gênero alimentício", "gêneros alimentícios",
            "merenda", "merenda escolar",
            "refeição", "refeicao", "refeições", "refeicoes",
            "rancho militar",
            "cesta basica", "cesta básica",
            "kit alimentação", "kit alimentacao",
            "fornecimento de alimentação", "fornecimento de alimentacao",
            "serviço de alimentação", "servico de alimentacao",
            "aquisição de alimentos", "aquisicao de alimentos",
            # Specific staple items
            "carne bovina", "carne suina", "carne suína",
            "leite", "laticinio", "laticinios", "laticínio", "laticínios",
            "arroz", "feijão", "feijao", "farinha",
            "açúcar", "acucar",
            "hortifruti", "hortifrutigranjeiro",
            "água mineral", "agua mineral",
            "biscoito", "biscoitos", "bolacha", "bolachas",
            "macarrão", "macarrao",
            "conserva", "conservas", "enlatado", "enlatados",
            "congelado", "congelados",
            # Restored standalone terms (guarded by exclusions)
            "sal", "óleo", "oleo", "café", "cafe",
            "fruta", "frutas", "verdura", "verduras", "legume", "legumes",
            "carne", "frango", "peixe",
            "pão", "pao", "pães", "paes",
            "bebida", "bebidas", "suco", "sucos",
        },
        exclusions={
            # "alimentação" in non-food context
            "alimentação de dados",
            "alimentação elétrica", "alimentacao eletrica",
            "alimentação de energia", "alimentacao de energia",
            "alimentação ininterrupta", "alimentacao ininterrupta",
            "fonte de alimentação", "fonte de alimentacao",
            # "sal" in non-food context
            "sal de audiência", "sal de audiencia",
            "salário", "salario",
            # "óleo" in non-food context
            "óleo lubrificante", "oleo lubrificante",
            "óleo diesel", "oleo diesel",
            "óleo hidráulico", "oleo hidraulico",
            "troca de óleo", "troca de oleo",
            # "bebida" — exclude non-procurement
            "bebida alcoólica", "bebida alcoolica",
            "concessão", "concessao",
            "exploração publicitária", "exploracao publicitaria",
        },
    ),
    "informatica": SectorConfig(
        id="informatica",
        name="Informática e Tecnologia",
        description="Computadores, servidores, software, periféricos, redes",
        keywords={
            "computador", "computadores",
            "notebook", "notebooks",
            "desktop", "desktops",
            "impressora", "impressoras",
            "scanner", "scanners",
            "teclado", "teclados",
            "nobreak", "nobreaks",
            "software", "softwares",
            "licença de software", "licenca de software",
            "sistema operacional",
            "antivirus", "antivírus",
            "firewall",
            "roteador", "roteadores",
            "cabo de rede", "cabeamento estruturado",
            "memória ram", "memoria ram",
            "processador", "processadores",
            "tablet", "tablets",
            "toner", "toners", "cartucho", "cartuchos",
            "informática", "informatica",
            "tecnologia da informação", "tecnologia da informacao",
            "equipamento de informatica", "equipamento de informática",
            # Restored standalone terms (guarded by exclusions)
            "servidor", "servidores",
            "monitor", "monitores",
            "mouse", "mouses",
            "switch", "switches",
            "hd", "ssd", "storage",
            "projetor", "projetores",
            "placa de video", "placa de vídeo",

            # COMPOUND TERMS ADDED (Issue #informatica-precision - 2026-02-06)
            # Increase precision by using procurement-specific compound terms
            "aquisição de computador", "aquisicao de computador",
            "aquisição de notebook", "aquisicao de notebook",
            "fornecimento de equipamento de informática", "fornecimento de equipamento de informatica",
            "locação de impressora", "locacao de impressora",
            "manutenção de equipamento de informática", "manutencao de equipamento de informatica",
            "manutenção de computador", "manutencao de computador",
            "instalação de rede", "instalacao de rede",
            "cabeamento de rede", "infraestrutura de rede",
            "suporte técnico de informática", "suporte tecnico de informatica",
            "assistência técnica", "assistencia tecnica",
            "peças para computador", "pecas para computador",
            "acessórios de informática", "acessorios de informatica",
            "periféricos de computador", "perifericos de computador",
        },
        exclusions={
            "informática educativa",
            # "servidor" in non-IT context (people, not machines)
            "servidor público", "servidor publico",
            "servidores públicos", "servidores publicos",
            "servidor municipal", "servidores municipais",
            "servidor efetivo", "servidores efetivos",
            "servidor estadual", "servidores estaduais",
            "servidor federal", "servidores federais",
            "servidor comissionado", "servidores comissionados",
            "servidor temporário", "servidor temporario",
            "servidores temporários", "servidores temporarios",
            "servidor ativo", "servidores ativos",
            "servidor inativo", "servidores inativos",
            "remuneração dos servidores", "remuneracao dos servidores",
            "salário dos servidores", "salario dos servidores",
            "pagamento dos servidores",
            "folha de pagamento dos servidores",
            "servidores e colaboradores",
            "proteção dos servidores", "protecao dos servidores",
            "equipamento de proteção individual", "equipamento de protecao individual",
            "equipamentos de proteção individual", "equipamentos de protecao individual",
            "epi", "epis",
            "uniforme", "uniformes", "fardamento",
            # "monitor" in non-IT context
            "monitor de aluno", "monitor de alunos",
            "monitor de pátio", "monitor de patio",
            "monitor de transporte",
            "monitor social",
            # "switch" in non-IT context (unlikely but guard)
            "switch grass",
        },
    ),
    # NOTE: "limpeza" was merged into "facilities" — cleaning products and services
    # are both part of facilities management.
    "mobiliario": SectorConfig(
        id="mobiliario",
        name="Mobiliário",
        description="Mesas, cadeiras, armários, estantes, móveis de escritório",
        keywords={
            "mobiliário", "mobiliario", "mobília", "mobilia",
            "móvel", "movel", "móveis", "moveis",
            "cadeira", "cadeiras",
            "armário", "armario", "armários", "armarios",
            "estante", "estantes",
            "gaveteiro", "gaveteiros",
            "escrivaninha", "escrivaninhas",
            "sofá", "sofa", "sofás", "sofas",
            "poltrona", "poltronas",
            "prateleira", "prateleiras",
            "birô", "biro",
            "mesa de reunião", "mesa de reuniao",
            "mesa de escritório", "mesa de escritorio",
            "mobiliário escolar", "mobiliario escolar",
            "carteira escolar", "carteiras escolares",
            "móvel planejado", "móveis planejados",
            "movel planejado", "moveis planejados",
            # Restored standalone terms (guarded by exclusions)
            "mesa", "mesas",
            "banco", "bancos",
            "balcão", "balcao",
            "arquivo", "arquivos",
            "rack", "racks",
            "quadro branco", "lousa",

            # COMPOUND TERMS ADDED (Issue #mobiliario-precision - 2026-02-06)
            "aquisição de mobiliário", "aquisicao de mobiliario",
            "fornecimento de móveis", "fornecimento de moveis",
            "móveis de escritório", "moveis de escritorio",
            "móveis escolares", "moveis escolares",
            "cadeira de escritório", "cadeira de escritorio",
            "cadeira giratória", "cadeira giratoria",
            "mesa para escritório", "mesa para escritorio",
            "armário de aço", "armario de aco",
            "estante de aço", "estante de aco",
            "arquivo de aço", "arquivo de aco",
            "mesa para computador",
        },
        exclusions={
            "mesa de negociação", "mesa de negociacao",
            "mesa redonda",
            "mesa de cirurgia",
            "mesa de bilhar",
            # "mesa" in non-furniture context (bed/bath linen)
            "roupa de cama mesa e banho",
            "cama mesa e banho",
            "roupa de mesa",
            # "móveis/móvel" in non-furniture context (portable/mobile)
            "equipamentos móveis", "equipamentos moveis",
            "equipamento móvel", "equipamento movel",
            "unidade móvel", "unidade movel",
            "telefonia móvel", "telefonia movel",
            "bens móveis", "bens moveis",
            "equipamentos médicos", "equipamentos medicos",
            "equipamento médico", "equipamento medico",
            "equipamentos hospitalares", "equipamento hospitalar",
            # "banco" in non-furniture context
            "banco de dados",
            "banco central",
            "banco do brasil",
            "banco de sangue",
            "banco de leite",
            "banco de horas",
            "banco de talentos",
            "estabelecimento bancário", "estabelecimento bancario",
            "instituição bancária", "instituicao bancaria",
            # "arquivo" in non-furniture context
            "arquivo morto",
            "arquivo digital",
            "arquivo pdf",
            "arquivo de dados",
            # "rack" in non-furniture context
            "rack de servidor", "rack de servidores",
            "rack de rede",
            # "balcão" in non-furniture context
            "porta balcão", "porta balcao",
            "concessão", "concessao",
        },
    ),
    "papelaria": SectorConfig(
        id="papelaria",
        name="Papelaria e Material de Escritório",
        description="Papel, canetas, material de escritório, suprimentos administrativos",
        keywords={
            "papelaria", "material de escritório", "material de escritorio",
            "papel a4", "papel sulfite",
            "caneta", "canetas",
            "lápis", "lapis",
            "grampeador", "grampeadores",
            "clipe", "clipes",
            "envelope", "envelopes",
            "fichário", "fichario",
            "caderno", "cadernos",
            "bloco de notas",
            "fita adesiva", "fita crepe",
            "marca texto", "marca-texto",
            "pincel atômico", "pincel atomico",
            "etiqueta", "etiquetas",
            "calculadora", "calculadoras",
            "material escolar",
            "kit escolar",
            "material de expediente",
            # Restored standalone terms (guarded by exclusions)
            "papel", "papéis", "papeis",
            "borracha", "borrachas",
            "cola", "colas",
            "tesoura", "tesouras",
            "grampo", "grampos",
            "pasta", "pastas",
            "agenda", "agendas",
            "expediente",

            # COMPOUND TERMS ADDED (Issue #papelaria-precision - 2026-02-06)
            "aquisição de material de escritório", "aquisicao de material de escritorio",
            "fornecimento de material de expediente",
            "material de papelaria",
            "artigos de papelaria",
            "papel ofício", "papel oficio",
            "caneta esferográfica", "caneta esfero", "caneta esferografica",
            "lápis de cor", "lapis de cor",
            "giz de cera",
            "marcador de texto",
            "pasta suspensa", "pasta arquivo",
            "grampeador de mesa",
            "perfurador de papel",
            "material escolar básico", "material escolar basico",
        },
        exclusions={
            "papel de parede",
            "papel moeda",
            "papel higiênico", "papel higienico",  # cleaning sector
            "papel toalha",  # cleaning sector
            # "borracha" in non-stationery context
            "borracha natural",
            "borracha de vedação", "borracha de vedacao",
            "pneu",
            # "clipe" in non-stationery context (medical)
            "clipe de aneurisma", "clipes de aneurisma",
            "clipes de aneurismas",
            "opme",  # Órteses, Próteses e Materiais Especiais
            # "cola" in non-stationery context
            "coca cola",
            "cola cirúrgica", "cola cirurgica",
            # "pasta" in non-stationery context
            "pasta de dente", "pasta dental",
            "pasta de solda",
            # "grampo" in non-stationery context
            "grampo cirúrgico", "grampo cirurgico",
            "grampo de cabelo",
            # "agenda" in non-product context
            "agenda de reunião", "agenda de reuniao",
            "agenda legislativa",
            # "expediente" in non-product context
            "horário de expediente", "horario de expediente",
            "fora de expediente",
            # "envelope" in non-stationery context
            "concessão", "concessao",
        },
    ),
    "engenharia": SectorConfig(
        id="engenharia",
        name="Engenharia e Construção",
        description="Obras, reformas, construção civil, pavimentação, infraestrutura",
        keywords={
            # High precision compound terms
            "construção civil", "construcao civil",
            "pavimentação", "pavimentacao",
            "recapeamento", "recapeamento asfaltico", "recapeamento asfáltico",
            "manutenção predial", "manutencao predial",
            "impermeabilização", "impermeabilizacao",
            "pintura predial", "pintura de fachada",
            "instalação elétrica", "instalacao eletrica",
            "instalação hidráulica", "instalacao hidraulica",
            "ar condicionado",
            "climatização", "climatizacao",
            "saneamento básico", "saneamento basico",
            "terraplanagem",
            "projeto arquitetônico", "projeto arquitetonico",
            "laudo técnico", "laudo tecnico",
            "obra de engenharia",
            "serviço de engenharia", "servico de engenharia",
            # Construction materials
            "alvenaria",
            "concreto armado", "concreto",
            "asfalto", "asfaltamento",
            "drenagem",
            # Restored standalone terms (guarded by exclusions)
            "obra", "obras",
            "reforma", "reformas",
            "engenharia",
            "construção", "construcao",
            "edificação", "edificacao",
            "ampliação", "ampliacao",
            "restauração", "restauracao",
            "demolição", "demolicao",
            "infraestrutura",
            "cimento", "aço", "aco", "ferro",
            "madeira", "tijolo", "tijolos",
            "areia", "brita", "cascalho",
            "telhado", "cobertura",
            "piso", "revestimento",
            "elevador", "elevadores",
        },
        exclusions={
            "engenharia de software",
            "engenharia de dados",
            "engenharia social",
            # "reforma" in non-construction context
            "reforma administrativa",
            "reforma tributária", "reforma tributaria",
            "reforma curricular",
            "reforma política", "reforma politica",
            # "restauração" in non-construction context
            "restauração de dados",
            "restauração de arquivo",
            "restauração de backup",
            # "infraestrutura" in IT/telecom context
            "infraestrutura de ti",
            "infraestrutura de rede",
            "infraestrutura de dados",
            "infraestrutura como serviço", "infraestrutura como servico",
            "infraestrutura de comunicação", "infraestrutura de comunicacao",
            "infraestrutura de telecomunicação", "infraestrutura de telecomunicacao",
            "infraestrutura de telefonia",
            # "infraestrutura" in events/temporary context
            "infraestrutura temporária", "infraestrutura temporaria",
            "infraestrutura para evento", "infraestrutura para eventos",
            # "infraestrutura" as department name (not construction)
            "secretaria de infraestrutura",
            "secretaria da infraestrutura",
            "secretaria municipal de infraestrutura",
            "secretaria municipal da infraestrutura",
            "diretoria de infraestrutura",
            # "obra" in non-construction context (keep specific, avoid blocking legit civil works)
            # NOTE: "mão de obra" removed — too aggressive, blocks legit civil works
            # like "fornecimento de material e mão de obra para reforma"
            # "construção" in non-civil context
            "construção de cenário", "construcao de cenario",
            "construção de cenários", "construcao de cenarios",
            "cenários cenográficos", "cenarios cenograficos",
            # "madeira" in non-construction context
            "carroceria de madeira",
            # "cobertura" in non-construction context
            "cobertura de seguro",
            "cobertura jornalística", "cobertura jornalistica",
            "cobertura vacinal",
            # "ferro" in non-construction context
            "ferro de passar",
            # Automotive services that mention "infraestrutura"
            "serviços de borracharia", "servicos de borracharia",
            # Sports context matching "areia" (sand courts)
            "arbitragem",
        },
    ),
    "software": SectorConfig(
        id="software",
        name="Software e Sistemas",
        description="Licenças de software, SaaS, desenvolvimento de sistemas, consultoria de TI",
        keywords={
            # Software licenses (high precision)
            "licença de software", "licenca de software",
            "licenciamento de software",
            "licenciamento", "licenca",
            "microsoft office", "office 365", "microsoft 365",
            "windows server", "sql server",
            "adobe", "autocad", "corel",
            "sap", "oracle", "salesforce",
            "software de gestão", "software de gestao",

            # SaaS & Cloud platforms
            "saas", "software as a service",
            "software como serviço", "software como servico",
            "plataforma cloud", "plataforma em nuvem",
            "assinatura de software", "assinatura de sistema",
            "serviço de nuvem", "servico de nuvem",

            # Custom development
            "desenvolvimento de software",
            "desenvolvimento de sistema",
            "desenvolvimento de aplicativo",
            "desenvolvimento web",
            "sistema web", "aplicação web", "aplicacao web",
            "sistema de gestão", "sistema de gestao",
            "software customizado", "software personalizado",
            "aplicativo mobile", "aplicativo móvel", "aplicativo movel",

            # Software services
            "consultoria de software",
            "consultoria de ti",
            "implantação de sistema", "implantacao de sistema",
            "integração de sistema", "integracao de sistema",
            "manutenção de software", "manutencao de software",
            "suporte técnico de software", "suporte tecnico de software",

            # Specific business systems
            "erp", "crm", "bi", "business intelligence",
            "sistema de folha de pagamento",
            "sistema de protocolo",
            "sistema de almoxarifado",
            "sistema de gestão escolar", "sistema de gestao escolar",
            "sistema de gestão hospitalar", "sistema de gestao hospitalar",
            "sistema de gestão pública", "sistema de gestao publica",
            "sistema de compras",
            "sistema de licitação", "sistema de licitacao",
            "portal de transparência", "portal de transparencia",

            # Restored standalone terms (guarded by exclusions)
            "software", "softwares",
            "aplicativo", "aplicativos",

            # CRITICAL ADDITIONS (Issue #software-0-results - 2026-02-06)
            # These compound terms are ESSENTIAL for matching real PNCP bids
            "sistema informatizado", "sistema informatizada",
            "aplicação informatizada", "aplicacao informatizada",
            "solução tecnológica", "solucao tecnologica",
            "solução de tecnologia", "solucao de tecnologia",
            "ferramenta digital", "ferramenta de gestão", "ferramenta de gestao",
            "plataforma digital", "portal digital", "portal web",
            "tecnologia da informação", "tecnologia da informacao",
            "serviços de tecnologia", "servicos de tecnologia",
            "contratação de ti", "contratacao de ti",
            "fornecimento de software", "aquisição de software", "aquisicao de software",

            # NOTE: "sistema" and "plataforma" are TOO AMBIGUOUS in Brazilian Portuguese
            # They match everything from "sistema de climatização" (HVAC) to "sistema de registro de preços" (procurement modality)
            # Only use compound terms like "sistema de gestão", "sistema web", "plataforma cloud"
        },
        exclusions={
            # Hardware (keep in "informatica" sector)
            "hardware",
            "equipamento de informatica", "equipamento de informática",
            "computador", "computadores",
            "notebook", "notebooks",
            "servidor físico", "servidor fisico",
            "impressora", "impressoras",
            "scanner", "scanners",
            "roteador", "roteadores",
            "switch", "switches",
            "teclado", "mouse",
            "monitor", "monitores",

            # Training/courses (not software procurement)
            "curso de software",
            "treinamento de software",
            "capacitação em software", "capacitacao em software",
            "treinamento em ti",
            "capacitação em ti", "capacitacao em ti",
            "curso de corte costura", "instrutor de corte costura",

            # Physical goods
            "caixa de software",  # physical packaging
            "embalagem de software",

            # Non-software training/education (REVISED - Issue #software-0-results)
            # REMOVED: "engenharia de software" - too broad, blocks valid procurement like "contratação de empresa de engenharia de software"
            "curso de engenharia de software",
            "graduação em engenharia de software", "graduacao em engenharia de software",
            "bacharelado em engenharia de software",
            "curso de desenvolvimento",
            "bootcamp",
            "treinamento de desenvolvimento",

            # "Sistema" in non-software context (CRITICAL - high false positive rate)
            "sistema de climatização", "sistema de climatizacao",
            "sistema de ar condicionado",
            "sistema de sonorização", "sistema de sonorizacao",
            "sistema de som",
            "sistema de iluminação", "sistema de iluminacao",
            "sistema de videomonitoramento",
            "sistema de câmeras", "sistema de cameras",
            "sistema de segurança eletrônica", "sistema de seguranca eletronica",
            "sistema de alarme",
            "sistema de combate a incêndio", "sistema de combate a incendio",
            "sistema de hidrantes",
            "sistema de registro de preços", "sistema de registro de precos",  # procurement modality, not software!
            "sistema único de saúde", "sistema unico de saude", "sus",  # SUS - Brazilian public health system
            "sistema de abastecimento de água", "sistema de abastecimento de agua",
            "sistema de esgoto",
            "sistema de drenagem",
            "sistema de gradeamento",
            "sistema de tratamento",
            "sistema elétrico", "sistema eletrico",
            "sistema hidráulico", "sistema hidraulico",
            "sistema de freios",
            "sistema de transmissão", "sistema de transmissao",
            "sistema de suspensão", "sistema de suspensao",
            "sistema fotovoltaico",
            "sistema de energia solar",
            "sistema de microgeração", "sistema de microgeracao",

            # Physical infrastructure and equipment
            "balança", "balanca",
            "bomba", "bombas",
            "moto bomba", "motobomba",
            "escavadeira",
            "caminhão", "caminhao",
            "veículo", "veiculo", "veículos", "veiculos",
            "máquina", "maquina",
            "equipamento rodoviário", "equipamento rodoviario",
            "plataforma fixa",  # truck platform

            # HVAC and climate control
            "climatização", "climatizacao",
            "ar condicionado",
            "ventilação", "ventilacao",
            "refrigeração", "refrigeracao",

            # Audio/video equipment
            "sonorização", "sonorizacao",
            "iluminação cênica", "iluminacao cenica",
            "instrumentos musicais",

            # Medical/health supplies
            "oxigênio medicinal", "oxigenio medicinal",
            "primeiros socorros",

            # Food and consumables
            "água mineral", "agua mineral",
            "lanche", "lanches",
            "kit de lanche",

            # Physical construction/maintenance
            "plotagem", "plotagens",
            "painel", "painéis", "paineis",
            "sondagem",
            "gradeamento mecanizado",

            # Personal services
            "maquiagem",
            "cabelo",
            "beleza",

            # Generic materials
            "ferramentas manuais",
            "materiais para manutenção", "materiais para manutencao",
            "peças", "pecas",
            "acessórios", "acessorios",
            "insumos",

            # Lighting/electrical
            "iluminação pública", "iluminacao publica",
            "extintores",
            "luminárias", "luminarias",
        },
    ),
    "facilities": SectorConfig(
        id="facilities",
        name="Facilities (Limpeza e Zeladoria)",
        description="Limpeza predial, produtos de limpeza, conservação, copa/cozinha, segurança patrimonial, portaria, recepção, zeladoria, jardinagem",
        keywords={
            # Core facilities management (English + Portuguese)
            "facilities", "facilities management", "fm",
            "gestão de facilities", "gestao de facilities",

            # Facilities services
            "serviços prediais", "servicos prediais",
            "serviços de facilities", "servicos de facilities",
            "serviços de conservação predial", "servicos de conservacao predial",

            # Cleaning services (building-specific)
            "limpeza predial",
            "limpeza e conservação", "limpeza e conservacao",
            "conservação de imóveis", "conservacao de imoveis",
            "conservação dos imóveis", "conservacao dos imoveis",
            "limpeza de edificações", "limpeza de edificacoes",
            "asseio de próprios públicos", "asseio de proprios publicos",
            "próprios públicos", "proprios publicos",
            "asseio",
            "conservação predial", "conservacao predial",
            "serviço de limpeza", "servico de limpeza",

            # Cleaning products (merged from limpeza sector)
            "material de limpeza", "materiais de limpeza",
            "produto de limpeza", "produtos de limpeza",
            "detergente", "detergentes",
            "desinfetante", "desinfetantes",
            "alvejante", "alvejantes",
            "água sanitária", "agua sanitaria",
            "saneante", "saneantes",
            "papel higienico", "papel higiênico",
            "papel toalha",
            "saco de lixo", "sacos de lixo",
            "luva de limpeza", "luvas de limpeza",
            "vassoura", "vassouras",
            "rodo", "rodos",
            "pano de chão", "pano de chao",
            "esponja", "esponjas",
            "desengordurante",
            "limpa vidro",
            "material de higienização", "material de higienizacao",
            "limpeza",
            "sabão", "sabao", "sabonete",
            "cloro",
            "balde", "baldes",
            "cera",
            "higiene", "higienização", "higienizacao",
            "descartável", "descartaveis", "descartáveis",
            "inseticida",

            # Support services (NOTE: vigilância/segurança patrimonial moved to "vigilancia" sector)
            "portaria", "recepção", "recepcao",
            "copa e cozinha",
            "zeladoria", "zelador",
            "recepcionista",
            "copeira", "copeiro",

            # Outsourced services (only compound forms specific to facilities)
            "terceirização de mão de obra", "terceirizacao de mao de obra",
            "serviços de apoio administrativo", "servicos de apoio administrativo",

            # Gardening (internal / condominium)
            "jardinagem",
            "paisagismo",
            "manutenção de jardim", "manutencao de jardim",
            "manutenção de jardins", "manutencao de jardins",
            "áreas verdes", "areas verdes",
        },
        exclusions={
            # Automotive
            "manutenção de veículos", "manutencao de veiculos",
            "manutenção de frota", "manutencao de frota",
            "manutenção automotiva", "manutencao automotiva",
            "pneus", "câmara de ar", "camara de ar",
            "óleo lubrificante", "oleo lubrificante",
            "tintas automotivas",
            "borracharia",
            "limpeza pesada para veículos", "limpeza pesada para veiculos",
            "limpeza automotiva",

            # IT/Equipment maintenance
            "manutenção de equipamentos de ti", "manutencao de equipamentos de ti",
            "tecnologia da informação", "tecnologia da informacao",
            "infraestrutura de ti", "infraestrutura de tecnologia",
            "equipamentos de informatica", "equipamentos de informática",

            # Infrastructure/Public works (keep in "engenharia")
            "pavimentação", "pavimentacao",
            "recapeamento",
            "iluminação pública", "iluminacao publica",
            "drenagem", "bueiros", "galerias",
            "sistema de drenagem",
            "limpeza de áreas públicas", "limpeza de areas publicas",
            "limpeza de vias públicas", "limpeza de vias publicas",
            "limpeza de ruas",
            "varrição de vias", "varricao de vias",
            "capinação", "capinacao",
            "jardinagem pública", "jardinagem publica",

            # "limpeza" in environmental/infrastructure context
            "limpeza de dados",
            "limpeza de terreno", "limpeza de terrenos",
            "limpeza de fossa", "limpeza de fossas",
            "limpeza de código", "limpeza de codigo",
            "limpeza de rio", "limpeza de lagoa", "limpeza de canal",
            "limpeza de córrego", "limpeza de corrego",
            "limpeza de bueiro", "limpeza de bueiros",
            "limpeza de galeria", "limpeza de galerias",
            "desassoreamento",
            "escavadeira",

            # Construction/Engineering (keep in "engenharia")
            "construção civil", "construcao civil",
            "reforma", "reformas",
            "ampliação", "ampliacao",
            "obra de construção", "obra de construcao",
            "obras civis",
            "edificação", "edificacao",

            # Healthcare/Pharmacy
            "medicamento", "medicamentos",
            "assistência farmacêutica", "assistencia farmaceutica",

            # Heavy equipment
            "máquinas pesadas", "maquinas pesadas",
            "retroescavadeira",
            "patrol", "rolo compressor",

            # Animal services
            "recolhimento de animais",
            "guarda de animais",
            "manutenção de animais", "manutencao de animais",

            # Software (keep in "software" sector)
            "software",
            "sistema de gestão", "sistema de gestao",
            "plataforma",

            # Agriculture
            "manutenção de tratores", "manutencao de tratores",

            # Pest control (not cleaning)
            "nebulização", "nebulizacao",
            "desinsetização", "desinsetizacao",
            "controle de pragas",
            "controle de vetores",

            # "cera" in non-cleaning context
            "cera perdida",
            "cera ortodôntica", "cera ortodontica",

            # "higiene" in non-product context
            "higiene ocupacional",
            "higiene do trabalho",
        },
    ),
    "saude": SectorConfig(
        id="saude",
        name="Saúde",
        description="Medicamentos, equipamentos hospitalares, insumos médicos, materiais de laboratório, órteses e próteses",
        keywords={
            # High precision compound terms
            "medicamento", "medicamentos",
            "material médico", "material medico",
            "material médico-hospitalar", "material medico-hospitalar",
            "material médico hospitalar", "material medico hospitalar",
            "materiais médicos", "materiais medicos",
            "materiais médico-hospitalares", "materiais medico-hospitalares",
            "insumo hospitalar", "insumos hospitalares",
            "insumo médico", "insumo medico",
            "insumos médicos", "insumos medicos",
            "equipamento médico", "equipamento medico",
            "equipamento hospitalar", "equipamentos hospitalares",
            "equipamentos médicos", "equipamentos medicos",
            "equipamentos médico-hospitalares", "equipamentos medico-hospitalares",
            "equipamento médico-hospitalar", "equipamento medico-hospitalar",

            # Pharmacy and drugs
            "farmácia", "farmacia",
            "farmacêutico", "farmaceutico",
            "assistência farmacêutica", "assistencia farmaceutica",
            "distribuição de medicamentos", "distribuicao de medicamentos",
            "drogaria",
            "fármaco", "farmaco", "fármacos", "farmacos",
            "produto farmacêutico", "produto farmaceutico",
            "produtos farmacêuticos", "produtos farmaceuticos",

            # Specific medical items
            "seringa", "seringas",
            "agulha", "agulhas",
            "cateter", "cateteres",
            "sonda", "sondas",
            "luva cirúrgica", "luva cirurgica",
            "luva de procedimento", "luvas de procedimento",
            "luva hospitalar",
            "gaze", "gazes", "compressa", "compressas",
            "atadura", "ataduras",
            "esparadrapo",
            "bisturi", "bisturis",
            "sutura", "suturas", "fio de sutura",
            "curativo", "curativos",

            # Orthotics, prosthetics, special materials
            "órtese", "ortese", "órteses", "orteses",
            "prótese", "protese", "próteses", "proteses",
            "opme",  # Órteses, Próteses e Materiais Especiais
            "material especial", "materiais especiais",
            "implante", "implantes",
            "stent", "stents",
            "marca-passo", "marcapasso",

            # Medical equipment (large)
            "raio-x", "raio x", "aparelho de raio",
            "ultrassom", "ultrassonografia",
            "tomógrafo", "tomografo", "tomografia",
            "ressonância magnética", "ressonancia magnetica",
            "desfibrilador", "desfibriladores",
            "monitor multiparâmetro", "monitor multiparametro",
            "monitor de sinais vitais",
            "ventilador pulmonar", "ventilador mecânico", "ventilador mecanico",
            "respirador", "respiradores",
            "autoclave", "autoclaves",
            "eletrocardiógrafo", "eletrocardiografo",
            "oxímetro", "oximetro",
            "esfigmomanômetro", "esfigmomanometro",
            "estetoscópio", "estetoscopio",
            "maca", "macas",
            "cama hospitalar", "camas hospitalares",
            "cadeira de rodas",
            "muleta", "muletas",
            "andador", "andadores",

            # Laboratory
            "material de laboratório", "material de laboratorio",
            "reagente", "reagentes",
            "kit diagnóstico", "kit diagnostico",
            "teste rápido", "teste rapido", "testes rápidos", "testes rapidos",
            "hemograma",
            "lâmina", "lamina", "lâminas", "laminas",
            "tubo de ensaio",
            "pipeta", "pipetas",
            "centrífuga", "centrifuga",
            "microscópio", "microscopio",

            # Dental
            "material odontológico", "material odontologico",
            "odontológico", "odontologico",
            "odontologia",
            "resina dental", "resina odontológica", "resina odontologica",
            "amálgama", "amalgama",
            "anestésico", "anestesico", "anestésicos", "anestesicos",

            # Specific drugs / active ingredients (common in PNCP)
            "dipirona", "dexametasona", "prednisolona",
            "paracetamol", "ibuprofeno", "omeprazol",
            "amoxicilina", "cefalexina", "azitromicina",
            "insulina", "metformina",
            "gabapentina", "losartana", "enalapril",
            "captopril", "atenolol", "sinvastatina",
            "diazepam", "clonazepam", "fluoxetina",
            "água destilada", "agua destilada",
            "soro fisiológico", "soro fisiologico",
            "solução injetável", "solucao injetavel",
            "solução parenteral", "solucao parenteral",
            "comprimido", "comprimidos",
            "cápsula", "capsula", "cápsulas", "capsulas",
            "pomada", "pomadas",
            "colírio", "colirio",

            # Surgical and specialized
            "tela cirúrgica", "tela cirurgica",
            "telas cirúrgicas", "telas cirurgicas",
            "instrumental cirúrgico", "instrumental cirurgico",
            "instrumentais cirúrgicos", "instrumentais cirurgicos",
            "instrumental", "instrumentais",
            "colostomia", "ileostomia",
            "bolsa coletora", "bolsas coletoras",
            "bolsa pressórica", "bolsa pressorica",
            "bolsas pressóricas", "bolsas pressoricas",
            "dreno", "drenos",

            # Therapies and specialties
            "fisioterapia", "fonoaudiologia",
            "telemedicina", "telessaúde", "telessaude",
            "oftalmologia", "oftalmológico", "oftalmologico",
            "endodontia", "endodôntico", "endodontico",
            "ortopedia", "ortopédico", "ortopedico",
            "neurologia", "cardiologia",
            "cirurgia", "cirúrgico", "cirurgico",
            "oncologia", "oncológico", "oncologico",

            # Lab consumables
            "tubo coletor", "tubos coletores",
            "tubo de coleta", "tubos de coleta",

            # Respiratory equipment
            "bipap", "cpap",

            # Hospital services and general
            "hospitalar", "hospitalares",
            "hospital",
            "saúde", "saude",
            "clínica", "clinica",
            "ambulatorial",
            "nutrição", "nutricao",
            "dieta enteral", "nutrição enteral", "nutricao enteral",
            "nutrição parenteral", "nutricao parenteral",
            "oxigênio medicinal", "oxigenio medicinal",
            "gases medicinais",
        },
        exclusions={
            # "saúde" in non-medical procurement context
            # NOTE: "secretaria de saúde" and "fundo municipal de saúde" REMOVED
            # from exclusions — they appear in legitimate medical procurement
            # descriptions (e.g., "Aquisição de gases medicinais para a Secretaria de Saúde")
            "saúde do trabalhador", "saude do trabalhador",
            "saúde ocupacional", "saude ocupacional",
            "segurança e saúde", "seguranca e saude",
            "plano de saúde", "plano de saude",
            "vigilância em saúde", "vigilancia em saude",
            "vigilância sanitária", "vigilancia sanitaria",

            # "sonda" in non-medical context
            "sondagem de solo", "sondagem geotécnica", "sondagem geotecnica",
            "sondagem spt",

            # "respirador" in non-medical context (PPE masks)
            "respirador pff2", "respirador pff3",
            "respirador semifacial",
            "máscara pff2", "mascara pff2",

            # Cleaning products
            "material de limpeza", "produto de limpeza",
            "detergente", "desinfetante",

            # IT/Software
            "software", "sistema de gestão", "sistema de gestao",
            "tecnologia da informação", "tecnologia da informacao",

            # Construction
            "construção civil", "construcao civil",
            "reforma", "obra",

            # Food
            "merenda", "merenda escolar",
            "gênero alimentício", "genero alimenticio",
            "refeição", "refeicao",

            # Furniture
            "mobiliário", "mobiliario",
            "cadeira de escritório", "cadeira de escritorio",

            # Uniforms
            "uniforme", "uniformes", "fardamento",
            "vestuário", "vestuario",

            # "agulha" in non-medical context
            "agulha de costura", "agulhas de costura",
            "agulha de crochê", "agulha de croche",
            "agulhas de crochê", "agulhas de croche",

            # "lâmina" in non-medical context
            "lâmina de barbear", "lamina de barbear",
            "lâminas de barbear", "laminas de barbear",
            "lâmina de serra", "lamina de serra",
            "lâminas de serra", "laminas de serra",

            # "monitor" in non-medical context
            "monitor de computador",
            "monitor de aluno", "monitor de pátio", "monitor de patio",

            # "clínica" in non-procurement context
            "clínica veterinária", "clinica veterinaria",
            "ensaio clínico", "ensaio clinico",  # research, not procurement

            # "hospital" in non-medical context
            "hospital de campanha",  # military/emergency infrastructure

            # "instrumental" in non-medical context
            "instrumental musical", "instrumentais musicais",

            # "nutrição" in non-medical context
            "nutrição animal", "nutricao animal",
            "ração", "racao",

            # "cirurgia/cirúrgico" — avoid plotagem/gráfica for hospitals
            "plotagem", "plotagens",
            "material gráfico", "material grafico",
            "materiais gráficos", "materiais graficos",

            # "comprimido" in non-medical context (compressed)
            "ar comprimido",
        },
    ),
    "vigilancia": SectorConfig(
        id="vigilancia",
        name="Vigilância e Segurança",
        description="Vigilância patrimonial, segurança eletrônica, CFTV, alarmes, controle de acesso, portaria armada/desarmada",
        keywords={
            # Core security services
            "vigilância", "vigilancia",
            "vigilância patrimonial", "vigilancia patrimonial",
            "vigilância armada", "vigilancia armada",
            "vigilância desarmada", "vigilancia desarmada",
            "segurança patrimonial", "seguranca patrimonial",
            "segurança privada", "seguranca privada",
            "segurança orgânica", "seguranca organica",
            "serviço de vigilância", "servico de vigilancia",
            "serviço de segurança", "servico de seguranca",
            "serviços de vigilância", "servicos de vigilancia",
            "serviços de segurança", "servicos de seguranca",

            # Armed/unarmed guard
            "vigilante", "vigilantes",
            "vigilante armado", "vigilantes armados",
            "vigilante desarmado", "vigilantes desarmados",
            "posto de vigilância", "posto de vigilancia",
            "posto de segurança", "posto de seguranca",
            "portaria armada",
            "portaria desarmada",

            # Electronic security
            "segurança eletrônica", "seguranca eletronica",
            "vigilância eletrônica", "vigilancia eletronica",
            "monitoramento eletrônico", "monitoramento eletronico",
            "cftv", "circuito fechado de televisão", "circuito fechado de televisao",
            "circuito fechado de tv",
            "câmera de segurança", "camera de seguranca",
            "câmeras de segurança", "cameras de seguranca",
            "câmera de monitoramento", "camera de monitoramento",
            "câmeras de monitoramento", "cameras de monitoramento",
            "câmera de vigilância", "camera de vigilancia",
            "videomonitoramento",

            # Alarms and access control
            "alarme", "alarmes",
            "sistema de alarme", "sistemas de alarme",
            "central de alarme",
            "controle de acesso",
            "catracas", "catraca",
            "cancela", "cancelas",
            "detector de metais",
            "raio x de bagagem",

            # Monitoring center
            "central de monitoramento",
            "monitoramento 24 horas", "monitoramento 24h",
            "monitoramento remoto",

            # Security equipment
            "colete balístico", "colete balistico",
            "coletes balísticos", "coletes balisticos",
            "colete à prova de balas", "colete a prova de balas",
            "arma de fogo",
            "munição", "municao",
            "rádio comunicador", "radio comunicador",
            "rádio comunicação", "radio comunicacao",
        },
        exclusions={
            # "vigilância" in health context
            "vigilância sanitária", "vigilancia sanitaria",
            "vigilância em saúde", "vigilancia em saude",
            "vigilância epidemiológica", "vigilancia epidemiologica",
            "vigilância ambiental", "vigilancia ambiental",
            "vigilância alimentar", "vigilancia alimentar",

            # "segurança" in non-guard context
            "segurança do trabalho", "seguranca do trabalho",
            "segurança da informação", "seguranca da informacao",
            "segurança cibernética", "seguranca cibernetica",
            "segurança alimentar", "seguranca alimentar",
            "segurança viária", "seguranca viaria",
            "segurança pública", "seguranca publica",
            "secretaria de segurança", "secretaria de seguranca",
            "equipamento de proteção individual", "equipamento de protecao individual",
            "epi", "epis",

            # "alarme" in non-security context
            "alarme de incêndio", "alarme de incendio",
            "alarme hospitalar",

            # IT/Software
            "software", "sistema de gestão", "sistema de gestao",
            "tecnologia da informação", "tecnologia da informacao",
            "infraestrutura de ti",

            # Construction
            "construção civil", "construcao civil",
            "reforma", "obra",

            # Cleaning/Facilities (already in facilities)
            "limpeza", "conservação predial", "conservacao predial",

            # Uniforms (keep in vestuario)
            "uniforme", "uniformes", "fardamento",

            # "monitoramento" in non-security context
            "monitoramento ambiental",
            "monitoramento de qualidade",
            "monitoramento de alunos",
            "monitoramento de saúde", "monitoramento de saude",
        },
    ),
    "transporte": SectorConfig(
        id="transporte",
        name="Transporte e Veículos",
        description="Aquisição/locação de veículos, combustíveis, manutenção de frota, pneus, peças automotivas, gerenciamento de frota",
        keywords={
            # Vehicle acquisition
            "veículo", "veiculo", "veículos", "veiculos",
            "automóvel", "automovel", "automóveis", "automoveis",
            "caminhão", "caminhao", "caminhões", "caminhoes",
            "ônibus", "onibus",
            "micro-ônibus", "micro-onibus", "micro ônibus", "micro onibus",
            "motocicleta", "motocicletas",
            "ambulância", "ambulancia", "ambulâncias", "ambulancias",
            "van", "vans",
            "utilitário", "utilitario",
            "caminhonete", "caminhoneta",
            "veículo zero km", "veiculo zero km",
            "veículo novo", "veiculo novo",
            "aquisição de veículo", "aquisicao de veiculo",
            "aquisição de veículos", "aquisicao de veiculos",

            # Vehicle rental/leasing
            "locação de veículo", "locacao de veiculo",
            "locação de veículos", "locacao de veiculos",
            "aluguel de veículo", "aluguel de veiculo",
            "aluguel de veículos", "aluguel de veiculos",
            "locação de automóvel", "locacao de automovel",

            # Fleet management
            "frota", "frotas",
            "gestão de frota", "gestao de frota",
            "gerenciamento de frota",
            "manutenção de frota", "manutencao de frota",
            "manutenção de veículos", "manutencao de veiculos",
            "manutenção veicular", "manutencao veicular",
            "manutenção automotiva", "manutencao automotiva",
            "manutenção preventiva veicular", "manutencao preventiva veicular",
            "manutenção corretiva veicular", "manutencao corretiva veicular",

            # Fuel
            "combustível", "combustivel", "combustíveis", "combustiveis",
            "gasolina",
            "diesel", "óleo diesel", "oleo diesel",
            "etanol",
            "abastecimento de combustível", "abastecimento de combustivel",
            "posto de combustível", "posto de combustivel",
            "cartão combustível", "cartao combustivel",
            "gnv", "gás natural veicular", "gas natural veicular",

            # Tires and parts
            "pneu", "pneus",
            "câmara de ar", "camara de ar",
            "peças automotivas", "pecas automotivas",
            "peças de reposição veicular", "pecas de reposicao veicular",
            "peças para veículos", "pecas para veiculos",
            "bateria automotiva", "baterias automotivas",
            "óleo lubrificante", "oleo lubrificante",
            "lubrificante", "lubrificantes",
            "filtro de óleo", "filtro de oleo",
            "filtro automotivo", "filtros automotivos",
            "filtro de ar", "filtro de combustível", "filtro de combustivel",
            "pastilha de freio",
            "amortecedor", "amortecedores",

            # Transport services
            "transporte escolar",
            "transporte de passageiros",
            "transporte de carga",
            "transporte de pacientes",
            "frete", "fretes",
            "serviço de transporte", "servico de transporte",
            "serviços de transporte", "servicos de transporte",

            # Automotive services
            "borracharia",
            "funilaria", "funilaria e pintura",
            "mecânica", "mecanica",
            "oficina mecânica", "oficina mecanica",
            "retífica", "retifica",
            "autoelétrica", "autoeletrica",
        },
        exclusions={
            # "veículo" in non-automotive context
            "veículo de comunicação", "veiculo de comunicacao",
            "veículo de informação", "veiculo de informacao",
            "veículo de mídia", "veiculo de midia",
            "veículo de publicidade", "veiculo de publicidade",

            # "diesel" in non-fuel context
            "grupo gerador diesel",  # keep in manutencao_predial
            "gerador a diesel",

            # "filtro" in non-automotive context
            "filtro de água", "filtro de agua",
            "filtro de linha",

            # "bateria" in non-automotive context
            "bateria musical",
            "bateria de notebook",
            "bateria de celular",

            # "transporte" as department name
            "secretaria de transporte",
            "secretaria de transportes",
            "secretaria municipal de transporte",
            "secretaria de mobilidade",

            # IT/Software
            "software", "sistema de gestão", "sistema de gestao",
            "tecnologia da informação", "tecnologia da informacao",

            # Construction
            "construção civil", "construcao civil",

            # Medical
            "medicamento", "medicamentos",
            "ambulância aérea", "ambulancia aerea",  # aircraft, not vehicle

            # Cleaning
            "material de limpeza", "produto de limpeza",

            # Furniture
            "mobiliário", "mobiliario",

            # "mecânica" in non-automotive context
            "mecânica dos solos", "mecanica dos solos",
            "ventilação mecânica", "ventilacao mecanica",
            "ventilador mecânico", "ventilador mecanico",

            # "lubrificante" in non-automotive context
            "lubrificante cirúrgico", "lubrificante cirurgico",
            "lubrificante industrial",
        },
    ),
    "manutencao_predial": SectorConfig(
        id="manutencao_predial",
        name="Manutenção Predial",
        description="Manutenção preventiva/corretiva de edificações, PMOC, ar condicionado, elevadores, instalações elétricas/hidráulicas, pintura predial, impermeabilização",
        keywords={
            # Building maintenance (HIGH PRECISION)
            "manutenção predial", "manutencao predial",
            "manutenção de imóveis", "manutencao de imoveis",
            "manutenção de edificações", "manutencao de edificacoes",
            "conservação de edificações", "conservacao de edificacoes",
            "manutenção de unidades residenciais", "manutencao de unidades residenciais",
            "conservação de unidades residenciais", "conservacao de unidades residenciais",

            # Maintenance types (with "predial")
            "manutenção preventiva predial", "manutencao preventiva predial",
            "manutenção corretiva predial", "manutencao corretiva predial",
            "manutenção preditiva predial", "manutencao preditiva predial",

            # HVAC / Air conditioning
            "ar condicionado",
            "climatização", "climatizacao",
            "climatização predial", "climatizacao predial",
            "ventilação predial", "ventilacao predial",
            "pmoc",

            # Elevators
            "elevador", "elevadores",
            "manutenção de elevador", "manutencao de elevador",
            "manutenção de elevadores", "manutencao de elevadores",

            # Electrical and hydraulic installations
            "instalações elétricas", "instalacoes eletricas",
            "instalações hidráulicas", "instalacoes hidraulicas",
            "instalações prediais", "instalacoes prediais",
            "instalação elétrica predial", "instalacao eletrica predial",
            "instalação hidráulica predial", "instalacao hidraulica predial",

            # Building painting
            "pintura predial", "pintura de fachada",
            "pintura de edificação", "pintura de edificacao",

            # Waterproofing
            "impermeabilização", "impermeabilizacao",
            "impermeabilização predial", "impermeabilizacao predial",

            # Generators and substations (building-specific)
            "subestação", "subestacao",
            "gerador predial",
            "grupo gerador",

            # Building utilities management
            "gestão predial", "gestao predial",
            "gestão de edificações", "gestao de edificacoes",
            "gestão predial de utilidades", "gestao predial de utilidades",
        },
        exclusions={
            # Automotive
            "manutenção de veículos", "manutencao de veiculos",
            "manutenção de frota", "manutencao de frota",
            "manutenção automotiva", "manutencao automotiva",
            "manutenção de caminhões", "manutencao de caminhoes",
            "manutenção de ônibus", "manutencao de onibus",
            "pneus", "câmara de ar", "camara de ar",
            "óleo lubrificante", "oleo lubrificante",
            "sistema de freios", "sistema diferencial",
            "borracharia",

            # IT/Equipment maintenance
            "manutenção de equipamentos de ti", "manutencao de equipamentos de ti",
            "manutenção de servidor", "manutencao de servidor",
            "manutenção de computador", "manutencao de computador",
            "manutenção de impressora", "manutencao de impressora",
            "tecnologia da informação", "tecnologia da informacao",
            "infraestrutura de ti",

            # Infrastructure/Public works (keep in "engenharia")
            "manutenção de estradas", "manutencao de estradas",
            "manutenção de vias", "manutencao de vias",
            "manutenção de rodovias", "manutencao de rodovias",
            "pavimentação", "pavimentacao",
            "recapeamento",
            "iluminação pública", "iluminacao publica",
            "drenagem", "bueiros", "galerias",
            "sistema de drenagem",

            # Construction (keep in "engenharia")
            "construção civil", "construcao civil",
            "obra de construção", "obra de construcao",
            "obras civis",

            # Healthcare
            "medicamento", "medicamentos",
            "manutenção de tratamento",

            # Heavy equipment
            "máquinas pesadas", "maquinas pesadas",
            "retroescavadeira", "escavadeira",
            "patrol", "rolo compressor",
            "motores diesel",

            # Animal services
            "manutenção de animais", "manutencao de animais",

            # Software
            "software",
            "sistema de gestão", "sistema de gestao",

            # Agriculture
            "manutenção de tratores", "manutencao de tratores",
            "manutenção de implementos agrícolas", "manutencao de implementos agricolas",
        },
    ),
}


def get_sector(sector_id: str) -> SectorConfig:
    """
    Get sector configuration by ID.

    Args:
        sector_id: Sector identifier (e.g., "vestuario", "alimentos")

    Returns:
        SectorConfig for the requested sector

    Raises:
        KeyError: If sector_id not found
    """
    if sector_id not in SECTORS:
        raise KeyError(
            f"Setor '{sector_id}' não encontrado. "
            f"Setores disponíveis: {list(SECTORS.keys())}"
        )
    return SECTORS[sector_id]


def list_sectors() -> List[dict]:
    """
    List all available sectors for frontend consumption.

    Returns:
        List of dicts with id, name, description for each sector.
    """
    return [
        {"id": s.id, "name": s.name, "description": s.description}
        for s in SECTORS.values()
    ]
