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
            # High precision terms
            "genero alimenticio", "generos alimenticios",
            "gênero alimentício", "gêneros alimentícios",
            "merenda", "merenda escolar",
            "refeição", "refeicao", "refeições", "refeicoes",
            "rancho militar",
            "cesta basica", "cesta básica",
            "hortifruti", "hortifrutigranjeiro",
            # Specific food categories (multi-word to avoid ambiguity)
            "generos alimenticios", "gêneros alimentícios",
            "kit alimentação", "kit alimentacao",
            "fornecimento de alimentação", "fornecimento de alimentacao",
            "serviço de alimentação", "servico de alimentacao",
            "aquisição de alimentos", "aquisicao de alimentos",
            # Specific staple items (less ambiguous in procurement context)
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
        },
        exclusions={
            "alimentação de dados",
            "alimentação elétrica",
            "alimentação de energia",
            "alimentação ininterrupta",  # nobreak/UPS
            "fonte de alimentação",  # power supply
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
        },
        exclusions={
            "informática educativa",
            # Ambiguous terms removed from keywords; these would cause
            # false positives in other sectors:
            "servidor público",  # civil servant, not hardware
            "servidor municipal",
            "servidor efetivo",
            "monitor de aluno",  # school monitor person
            "monitor de pátio",
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
        },
        exclusions={
            "limpeza de dados",  # data cleanup
            "limpeza de terreno",  # land clearing (construction)
            "limpeza de fossa",  # septic cleaning (sanitation)
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
        },
        exclusions={
            "mesa de negociação",
            "mesa redonda",
            "mesa de cirurgia",  # surgical table
            "banco de dados",  # database
            "banco central",
            "banco do brasil",
            "arquivo morto",  # dead files storage
            "arquivo digital",
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
        },
        exclusions={
            "papel de parede",  # wallpaper (construction)
            "papel moeda",  # currency
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
            # Construction materials (specific enough in context)
            "alvenaria",
            "concreto armado",
            "asfalto", "asfaltamento",
            "drenagem",
        },
        exclusions={
            "engenharia de software",
            "engenharia de dados",
            "engenharia social",
            "reforma administrativa",
            "reforma tributária",
            "reforma tributaria",
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
