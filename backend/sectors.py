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
            # "monitor" in non-IT context
            "monitor de aluno", "monitor de alunos",
            "monitor de pátio", "monitor de patio",
            "monitor de transporte",
            "monitor social",
            # "switch" in non-IT context (unlikely but guard)
            "switch grass",
        },
    ),
    "limpeza": SectorConfig(
        id="limpeza",
        name="Produtos de Limpeza",
        description="Materiais de limpeza, higienização, saneantes, descartáveis",
        keywords={
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
            "serviço de limpeza", "servico de limpeza",
            "limpeza e conservação", "limpeza e conservacao",
            "limpeza predial",
            # Restored standalone terms (guarded by exclusions)
            "limpeza",
            "sabão", "sabao", "sabonete",
            "cloro",
            "balde", "baldes",
            "cera",
            "higiene", "higienização", "higienizacao",
            "descartável", "descartaveis", "descartáveis",
            "copa e cozinha",
            "inseticida",
        },
        exclusions={
            "limpeza de dados",
            "limpeza de terreno", "limpeza de terrenos",
            "limpeza de fossa", "limpeza de fossas",
            "limpeza de código", "limpeza de codigo",
            # "limpeza" in environmental/infrastructure context
            "limpeza de rio", "limpeza de lagoa", "limpeza de canal",
            "limpeza de córrego", "limpeza de corrego",
            "limpeza de bueiro", "limpeza de bueiros",
            "limpeza de galeria", "limpeza de galerias",
            "desassoreamento",
            "escavadeira",
            # "limpeza" in automotive context
            "limpeza pesada para veículos", "limpeza pesada para veiculos",
            "limpeza automotiva",
            # "inseticida" in pest control services (not cleaning product)
            "nebulização", "nebulizacao",
            "desinsetização", "desinsetizacao",
            "controle de pragas",
            "controle de vetores",
            # "cera" in non-cleaning context
            "cera perdida",  # lost-wax casting
            "cera ortodôntica", "cera ortodontica",
            # "higiene" in non-product context
            "higiene ocupacional",
            "higiene do trabalho",
        },
    ),
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

            # Non-software engineering
            "engenharia de software",  # if it's about services, not procurement
            "curso de desenvolvimento",
            "bootcamp",

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
