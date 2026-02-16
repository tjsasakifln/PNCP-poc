"""
CNAE to SmartLic sector mapping.

Maps Brazilian CNAE (Classificação Nacional de Atividades Econômicas)
codes to SmartLic sector IDs used by the search pipeline.
"""


# Top 10 CNAE→sector mappings (AC6)
# Format: CNAE 4-digit prefix → sector_id
CNAE_TO_SETOR: dict[str, str] = {
    # Vestuário / Uniformes
    "4781": "vestuario",     # Comércio varejista de artigos de vestuário e acessórios
    "1412": "vestuario",     # Confecção de peças de vestuário, exceto roupas íntimas
    # Facilities / Limpeza
    "8121": "facilities",    # Limpeza em prédios e em domicílios
    "8011": "facilities",    # Atividades de vigilância e segurança privada
    # Equipamentos
    "2710": "equipamentos",  # Fabricação de geradores, transformadores, motores elétricos
    "3250": "equipamentos",  # Fabricação de instrumentos e materiais para uso médico
    # Alimentos
    "1011": "alimentos",     # Abate de reses, exceto suínos
    "1091": "alimentos",     # Fabricação de produtos de panificação e confeitaria
    # TI / Informática
    "6201": "informatica",   # Desenvolvimento de programas de computador sob encomenda
    "6202": "informatica",   # Desenvolvimento e licenciamento de programas de computador
}

# Reverse mapping: sector descriptions for user feedback
SETOR_NAMES: dict[str, str] = {
    "vestuario": "Vestuário e Uniformes",
    "facilities": "Facilities e Serviços",
    "equipamentos": "Equipamentos",
    "alimentos": "Alimentos e Merenda",
    "informatica": "Hardware e Equipamentos de TI",
}


def map_cnae_to_setor(cnae: str) -> str:
    """
    Map CNAE code to SmartLic sector ID.

    Extracts the 4-digit prefix from CNAE codes in various formats:
    - "4781" → "vestuario"
    - "4781-4/00" → "vestuario"
    - "47814" → "vestuario"

    Falls back to "vestuario" if CNAE not recognized.

    Args:
        cnae: CNAE code or prefix string

    Returns:
        Sector ID string (e.g., "vestuario", "facilities")
    """
    # Extract 4-digit prefix: handle "4781-4/00", "4781400", "4781" formats
    cleaned = cnae.strip().replace(" ", "")
    # Take first 4 digits
    prefix = ""
    for ch in cleaned:
        if ch.isdigit():
            prefix += ch
            if len(prefix) == 4:
                break

    if not prefix or len(prefix) < 4:
        return "vestuario"  # Default fallback

    return CNAE_TO_SETOR.get(prefix, "vestuario")


def get_setor_name(setor_id: str) -> str:
    """Get human-readable sector name."""
    return SETOR_NAMES.get(setor_id, setor_id.replace("_", " ").title())
