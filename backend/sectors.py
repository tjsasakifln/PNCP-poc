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
            "alimento", "alimentos", "alimentacao", "alimentação",
            "genero alimenticio", "generos alimenticios",
            "merenda", "merenda escolar",
            "refeição", "refeicao", "refeições", "refeicoes",
            "rancho", "rancho militar",
            "cesta basica", "cesta básica",
            "hortifruti", "hortifrutigranjeiro",
            "carne", "carnes", "frango", "peixe",
            "leite", "laticinio", "laticinios",
            "arroz", "feijão", "feijao", "farinha",
            "açúcar", "acucar", "sal", "óleo", "oleo",
            "pão", "pao", "paes",
            "fruta", "frutas", "verdura", "verduras", "legume", "legumes",
            "bebida", "bebidas", "suco", "sucos", "água mineral", "agua mineral",
            "cafe", "café",
            "biscoito", "biscoitos", "bolacha", "bolachas",
            "macarrão", "macarrao", "massa", "massas",
            "tempero", "temperos", "condimento", "condimentos",
            "conserva", "conservas", "enlatado", "enlatados",
            "congelado", "congelados",
            "kit alimentação", "kit alimentacao",
            "fornecimento de alimentação", "fornecimento de alimentacao",
            "serviço de alimentação", "servico de alimentacao",
        },
        exclusions={
            "alimentação de dados",
            "alimentação elétrica",
            "alimentação de energia",
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
            "servidor", "servidores",
            "monitor", "monitores",
            "impressora", "impressoras",
            "scanner", "scanners",
            "teclado", "teclados",
            "mouse", "mouses",
            "nobreak", "nobreaks",
            "software", "softwares",
            "licença de software", "licenca de software",
            "sistema operacional",
            "antivirus", "antivírus",
            "firewall",
            "switch", "switches",
            "roteador", "roteadores",
            "cabo de rede", "cabeamento",
            "storage", "armazenamento",
            "hd", "ssd", "disco rigido",
            "memória ram", "memoria ram",
            "processador", "processadores",
            "placa de video", "placa de vídeo",
            "tablet", "tablets",
            "projetor", "projetores",
            "toner", "toners", "cartucho", "cartuchos",
            "informática", "informatica",
            "tecnologia da informação", "tecnologia da informacao",
            "equipamento de informatica", "equipamento de informática",
            "ti", "tic",
        },
        exclusions={
            "informática educativa",  # Usually means teaching, not buying
        },
    ),
    "limpeza": SectorConfig(
        id="limpeza",
        name="Produtos de Limpeza",
        description="Materiais de limpeza, higienização, saneantes, descartáveis",
        keywords={
            "limpeza", "material de limpeza",
            "produto de limpeza", "produtos de limpeza",
            "detergente", "detergentes",
            "desinfetante", "desinfetantes",
            "sabão", "sabao", "sabonete", "sabonetes",
            "alvejante", "alvejantes",
            "água sanitária", "agua sanitaria",
            "cloro",
            "saneante", "saneantes",
            "higiene", "higienização", "higienizacao",
            "papel higienico", "papel higiênico",
            "papel toalha",
            "saco de lixo", "sacos de lixo",
            "luva de limpeza", "luvas de limpeza",
            "vassoura", "vassouras",
            "rodo", "rodos",
            "balde", "baldes",
            "pano de chão", "pano de chao",
            "esponja", "esponjas",
            "desengordurante",
            "limpa vidro",
            "cera", "ceras",
            "inseticida", "inseticidas",
            "descartável", "descartavel", "descartáveis", "descartaveis",
            "copa e cozinha",
            "material de higienização", "material de higienizacao",
        },
        exclusions=set(),
    ),
    "mobiliario": SectorConfig(
        id="mobiliario",
        name="Mobiliário",
        description="Mesas, cadeiras, armários, estantes, móveis de escritório",
        keywords={
            "mobiliário", "mobiliario", "mobília", "mobilia",
            "móvel", "movel", "móveis", "moveis",
            "mesa", "mesas",
            "cadeira", "cadeiras",
            "armário", "armario", "armários", "armarios",
            "estante", "estantes",
            "arquivo", "arquivos",
            "gaveteiro", "gaveteiros",
            "balcão", "balcao", "balcões", "balcoes",
            "escrivaninha", "escrivaninhas",
            "sofá", "sofa", "sofás", "sofas",
            "poltrona", "poltronas",
            "banco", "bancos",
            "prateleira", "prateleiras",
            "rack", "racks",
            "birô", "biro",
            "púlpito", "pulpito",
            "mesa de reunião", "mesa de reuniao",
            "mobiliário escolar", "mobiliario escolar",
            "carteira escolar", "carteiras escolares",
            "quadro branco", "quadro negro",
            "lousa", "lousas",
        },
        exclusions={
            "mesa de negociação",  # Financial context
            "mesa redonda",  # Event context
        },
    ),
    "papelaria": SectorConfig(
        id="papelaria",
        name="Papelaria e Material de Escritório",
        description="Papel, canetas, material de escritório, suprimentos administrativos",
        keywords={
            "papelaria", "material de escritório", "material de escritorio",
            "papel", "papéis", "papeis",
            "papel a4", "papel sulfite",
            "caneta", "canetas",
            "lápis", "lapis",
            "borracha", "borrachas",
            "cola", "colas",
            "tesoura", "tesouras",
            "grampeador", "grampeadores",
            "grampo", "grampos",
            "clipe", "clipes",
            "envelope", "envelopes",
            "pasta", "pastas",
            "fichário", "fichario",
            "caderno", "cadernos",
            "bloco de notas",
            "post-it",
            "fita adesiva", "fita crepe",
            "régua", "regua",
            "marca texto", "marca-texto",
            "pincel atômico", "pincel atomico",
            "etiqueta", "etiquetas",
            "agenda", "agendas",
            "calculadora", "calculadoras",
            "material escolar",
            "kit escolar",
            "expediente",
            "material de expediente",
        },
        exclusions=set(),
    ),
    "engenharia": SectorConfig(
        id="engenharia",
        name="Engenharia e Construção",
        description="Obras, reformas, construção civil, pavimentação, infraestrutura",
        keywords={
            "obra", "obras",
            "construção", "construcao", "construções", "construcoes",
            "reforma", "reformas",
            "pavimentação", "pavimentacao",
            "engenharia", "engenharias",
            "edificação", "edificacao",
            "ampliação", "ampliacao",
            "restauração", "restauracao",
            "manutenção predial", "manutencao predial",
            "impermeabilização", "impermeabilizacao",
            "pintura predial", "pintura de fachada",
            "instalação elétrica", "instalacao eletrica",
            "instalação hidráulica", "instalacao hidraulica",
            "ar condicionado",
            "climatização", "climatizacao",
            "elevador", "elevadores",
            "telhado", "cobertura",
            "piso", "pisos", "revestimento", "revestimentos",
            "alvenaria",
            "concreto", "cimento",
            "aço", "aco", "ferro",
            "madeira", "madeiras",
            "tijolo", "tijolos",
            "areia", "brita", "cascalho",
            "asfalto", "asfaltamento",
            "drenagem", "saneamento básico", "saneamento basico",
            "infraestrutura",
            "terraplanagem",
            "demolição", "demolicao",
            "projeto arquitetônico", "projeto arquitetonico",
            "laudo técnico", "laudo tecnico",
        },
        exclusions={
            "engenharia de software",
            "engenharia de dados",
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
