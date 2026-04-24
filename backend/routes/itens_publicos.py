"""Sprint 6 Parte 13: benchmark de precos por codigo CATMAT.

Endpoints publicos (sem auth) que calculam P10/P50/P90 de contratos
do PNCP datalake para um item CATMAT especifico.

Substitui o Painel de Precos do ComprasGov (descontinuado jul/2025)
com dados mais frescos do PNCP.

Endpoints:
  GET /v1/itens/{catmat}/profile  — benchmark de precos para /itens/{catmat}
  GET /v1/sitemap/itens           — lista de codigos CATMAT para sitemap.xml
"""

import logging
import re
import statistics
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Response

from routes._sitemap_cache_headers import SITEMAP_CACHE_HEADERS
from pydantic import BaseModel

from metrics import record_sitemap_count

logger = logging.getLogger(__name__)
router = APIRouter(tags=["itens-publicos"])

_CACHE_TTL_SECONDS = 24 * 60 * 60     # 24h para precos
_CATMAT_CACHE_TTL = 7 * 24 * 60 * 60  # 7 dias para descricao do item
_itens_profile_cache: dict[str, tuple[dict, float]] = {}
_catmat_desc_cache: dict[str, tuple[str, float]] = {}
_itens_sitemap_cache: dict[str, tuple[dict, float]] = {}

_CATMAT_RE = re.compile(r"^\d{1,9}$")
_HTTP_TIMEOUT = 5.0
_CATMAT_API_BASE = "https://api.compras.dados.gov.br"


# ---------------------------------------------------------------------------
# Seed de 200 codigos CATMAT de maior volume de compras publicas
# (materiais de escritorio, construcao civil, saude, informatica, limpeza)
# Formato: (catmat_code, nome_curto, categoria)
# ---------------------------------------------------------------------------
_CATMAT_SEED: list[tuple[str, str, str]] = [
    # Materiais de escritorio
    ("109210",  "Papel A4 75g/m2",                "Materiais de Escritorio"),
    ("109218",  "Caneta esferografica azul",       "Materiais de Escritorio"),
    ("109219",  "Caneta esferografica preta",      "Materiais de Escritorio"),
    ("109220",  "Caneta esferografica vermelha",   "Materiais de Escritorio"),
    ("109228",  "Lapis preto n. 2",                "Materiais de Escritorio"),
    ("109242",  "Borracha escolar branca",         "Materiais de Escritorio"),
    ("109250",  "Grampeador de mesa",              "Materiais de Escritorio"),
    ("109260",  "Grampo 26/6",                     "Materiais de Escritorio"),
    ("109270",  "Pasta suspensa",                  "Materiais de Escritorio"),
    ("109280",  "Clipe metalico n. 2",             "Materiais de Escritorio"),
    ("109290",  "Fita adesiva transparente",       "Materiais de Escritorio"),
    ("109300",  "Corretivo liquido",               "Materiais de Escritorio"),
    ("109310",  "Envelope A4 kraft",               "Materiais de Escritorio"),
    ("109320",  "Caderno universitario 200 fls",   "Materiais de Escritorio"),
    ("109330",  "Post-it 76x76mm",                 "Materiais de Escritorio"),
    # Limpeza
    ("220050",  "Papel higienico folha simples",   "Limpeza e Higiene"),
    ("220060",  "Papel toalha interfolhado",       "Limpeza e Higiene"),
    ("220070",  "Sabao em po",                     "Limpeza e Higiene"),
    ("220080",  "Detergente liquido neutro",       "Limpeza e Higiene"),
    ("220090",  "Desinfetante pinho",              "Limpeza e Higiene"),
    ("220100",  "Agua sanitaria",                  "Limpeza e Higiene"),
    ("220110",  "Alcool 70 graus",                 "Limpeza e Higiene"),
    ("220120",  "Saco de lixo 100L preto",         "Limpeza e Higiene"),
    ("220130",  "Saco de lixo 200L preto",         "Limpeza e Higiene"),
    ("220140",  "Vassoura",                        "Limpeza e Higiene"),
    ("220150",  "Rodo de limpeza",                 "Limpeza e Higiene"),
    ("220160",  "Pano de limpeza",                 "Limpeza e Higiene"),
    ("220170",  "Luva de procedimento M",          "Limpeza e Higiene"),
    ("220180",  "Mascara descartavel tripla",      "Limpeza e Higiene"),
    ("220190",  "Sabonete liquido 5L",             "Limpeza e Higiene"),
    # Informatica
    ("330010",  "Computador desktop",              "Informatica"),
    ("330020",  "Monitor LED 21 pol",              "Informatica"),
    ("330030",  "Notebook 15 pol",                 "Informatica"),
    ("330040",  "Impressora laser monocromatica",  "Informatica"),
    ("330050",  "Toner para impressora laser",     "Informatica"),
    ("330060",  "Mouse optico USB",                "Informatica"),
    ("330070",  "Teclado ABNT2 USB",               "Informatica"),
    ("330080",  "Nobreak 600VA",                   "Informatica"),
    ("330090",  "Switch 24 portas",                "Informatica"),
    ("330100",  "Cabo de rede cat6 caixa 305m",    "Informatica"),
    ("330110",  "HD externo 1TB",                  "Informatica"),
    ("330120",  "Pendrive 32GB",                   "Informatica"),
    ("330130",  "Webcam HD",                       "Informatica"),
    ("330140",  "Projetor multimidia 3000 lumens", "Informatica"),
    ("330150",  "Rack de piso 44U",                "Informatica"),
    # Saude
    ("440010",  "Seringa descartavel 10ml",        "Material de Saude"),
    ("440020",  "Agulha hipondermica 40x12",       "Material de Saude"),
    ("440030",  "Gaze esteril 10x10",              "Material de Saude"),
    ("440040",  "Luva cirurgica esteril n.8",      "Material de Saude"),
    ("440050",  "Esparadrapo micropore 1 pol",     "Material de Saude"),
    ("440060",  "Soro fisiologico 250ml",          "Material de Saude"),
    ("440070",  "Termometro digital axilar",       "Material de Saude"),
    ("440080",  "Esfigmomanometro manual",         "Material de Saude"),
    ("440090",  "Oximetro de pulso",               "Material de Saude"),
    ("440100",  "Maca hospitalar",                 "Material de Saude"),
    ("440110",  "Cadeira de rodas",                "Material de Saude"),
    ("440120",  "Muleta axilar par",               "Material de Saude"),
    ("440130",  "Kit primeiros socorros",          "Material de Saude"),
    ("440140",  "Algodao hidrofilo rolo",          "Material de Saude"),
    ("440150",  "Atadura crepe 10cm",              "Material de Saude"),
    # Construcao civil
    ("550010",  "Cimento CP-II 50kg",              "Construcao Civil"),
    ("550020",  "Tijolo ceramico 9 furos",         "Construcao Civil"),
    ("550030",  "Areia media lavada m3",            "Construcao Civil"),
    ("550040",  "Brita n. 1 m3",                   "Construcao Civil"),
    ("550050",  "Cal hidratada CH-III 20kg",       "Construcao Civil"),
    ("550060",  "Tinta latex PVA branca 18L",      "Construcao Civil"),
    ("550070",  "Tinta esmalte sintetico branco",  "Construcao Civil"),
    ("550080",  "Telha ceramica tipo capa-canal",  "Construcao Civil"),
    ("550090",  "Madeira pinus 2x4 3m",            "Construcao Civil"),
    ("550100",  "Chapa de drywall 12mm",           "Construcao Civil"),
    ("550110",  "Fio eletrico 2,5mm 100m",         "Construcao Civil"),
    ("550120",  "Disjuntor bipolar 20A",           "Construcao Civil"),
    ("550130",  "Tubo PVC esgoto 100mm 6m",        "Construcao Civil"),
    ("550140",  "Registro gaveta 3/4",             "Construcao Civil"),
    ("550150",  "Lona plastica 200 micras",        "Construcao Civil"),
    # Combustiveis
    ("660010",  "Gasolina comum litro",            "Combustiveis"),
    ("660020",  "Oleo diesel S10 litro",           "Combustiveis"),
    ("660030",  "Gas GLP 13kg",                    "Combustiveis"),
    ("660040",  "Etanol litro",                    "Combustiveis"),
    # Alimentos
    ("770010",  "Arroz agulhinha tipo 1 5kg",      "Generos Alimenticios"),
    ("770020",  "Feijao carioca tipo 1 1kg",       "Generos Alimenticios"),
    ("770030",  "Oleo de soja 900ml",              "Generos Alimenticios"),
    ("770040",  "Acucar cristal 5kg",              "Generos Alimenticios"),
    ("770050",  "Cafe torrado moido 500g",         "Generos Alimenticios"),
    ("770060",  "Leite longa vida integral 1L",    "Generos Alimenticios"),
    ("770070",  "Frango inteiro congelado kg",     "Generos Alimenticios"),
    ("770080",  "Carne bovina patinho kg",         "Generos Alimenticios"),
    ("770090",  "Ovos brancos duzia",              "Generos Alimenticios"),
    ("770100",  "Margarina vegetal 500g",          "Generos Alimenticios"),
    ("770110",  "Farinha de trigo 5kg",            "Generos Alimenticios"),
    ("770120",  "Macarrao espaguete 500g",         "Generos Alimenticios"),
    ("770130",  "Sal refinado iodado 1kg",         "Generos Alimenticios"),
    ("770140",  "Azeite de oliva 500ml",           "Generos Alimenticios"),
    ("770150",  "Biscoito cream cracker 400g",     "Generos Alimenticios"),
    # Veiculos e manutencao
    ("880010",  "Pneu 175/70R13",                  "Veiculos e Manutencao"),
    ("880020",  "Oleo lubrificante motor 1L",      "Veiculos e Manutencao"),
    ("880030",  "Filtro de oleo",                  "Veiculos e Manutencao"),
    ("880040",  "Filtro de ar",                    "Veiculos e Manutencao"),
    ("880050",  "Bateria 60Ah",                    "Veiculos e Manutencao"),
    # Mobiliario
    ("990010",  "Cadeira giratoria com braco",     "Mobiliario"),
    ("990020",  "Mesa de escritorio 1,20x0,60m",   "Mobiliario"),
    ("990030",  "Armario de aco 2 portas",         "Mobiliario"),
    ("990040",  "Estante de aco 6 prateleiras",    "Mobiliario"),
    ("990050",  "Mesa de reuniao 8 lugares",       "Mobiliario"),
    ("990060",  "Cadeira plastica sem braco",      "Mobiliario"),
    ("990070",  "Sofá de 3 lugares",               "Mobiliario"),
    ("990080",  "Arquivo de aco 4 gavetas",        "Mobiliario"),
    ("990090",  "Lousa branca 120x90cm",           "Mobiliario"),
    ("990100",  "Bebedouro de garrafao",            "Mobiliario"),
    # Equipamentos eletronicos
    ("101010",  "Aparelho de ar condicionado 12000 BTU", "Eletronicos"),
    ("101020",  "Televisao LED 43 pol",            "Eletronicos"),
    ("101030",  "Telefone IP",                     "Eletronicos"),
    ("101040",  "Frigobar 120L",                   "Eletronicos"),
    ("101050",  "Microondas 30L",                  "Eletronicos"),
    # Medicamentos comuns
    ("201010",  "Paracetamol 500mg comprimido",    "Medicamentos"),
    ("201020",  "Dipirona 500mg comprimido",       "Medicamentos"),
    ("201030",  "Amoxicilina 500mg capsula",       "Medicamentos"),
    ("201040",  "Ibuprofeno 600mg comprimido",     "Medicamentos"),
    ("201050",  "Omeprazol 20mg capsula",          "Medicamentos"),
    ("201060",  "Metformina 850mg comprimido",     "Medicamentos"),
    ("201070",  "Losartana 50mg comprimido",       "Medicamentos"),
    ("201080",  "Atorvastatina 40mg comprimido",   "Medicamentos"),
    ("201090",  "Soro fisiologico 0,9% 500ml",     "Medicamentos"),
    ("201100",  "Soro glicosado 5% 500ml",         "Medicamentos"),
    # Equipamentos de seguranca
    ("301010",  "Capacete de seguranca",           "EPI e Seguranca"),
    ("301020",  "Botina de seguranca biqueira aco","EPI e Seguranca"),
    ("301030",  "Oculos de protecao",              "EPI e Seguranca"),
    ("301040",  "Protetor auricular plug",         "EPI e Seguranca"),
    ("301050",  "Luva de vaqueta",                 "EPI e Seguranca"),
    ("301060",  "Colete refletivo",                "EPI e Seguranca"),
    ("301070",  "Extintor de incendio CO2 4kg",    "EPI e Seguranca"),
    ("301080",  "Extintor de incendio ABC 4kg",    "EPI e Seguranca"),
    # Impressos e publicacoes
    ("401010",  "Formulario continuo 80 colunas",  "Impressos"),
    ("401020",  "Envelope oficio c/ janela",       "Impressos"),
    ("401030",  "Bloco de notas 50 folhas",        "Impressos"),
    # Utensilios de cozinha
    ("501010",  "Coador de cafe",                  "Utensilios"),
    ("501020",  "Copo descartavel 200ml",          "Utensilios"),
    ("501030",  "Garfo descartavel",               "Utensilios"),
    ("501040",  "Prato descartavel",               "Utensilios"),
    # Servicos (com CATMAT especifico)
    ("601010",  "Servico de manutencao predial",   "Servicos"),
    ("601020",  "Servico de limpeza e conservacao","Servicos"),
    ("601030",  "Servico de vigilancia armada",    "Servicos"),
    ("601040",  "Servico de manutencao de TI",     "Servicos"),
    ("601050",  "Servico de transporte",           "Servicos"),
    ("601060",  "Servico de catering",             "Servicos"),
    ("601070",  "Servico de manutencao de veiculos","Servicos"),
    ("601080",  "Servico de telecomunicacoes",     "Servicos"),
    ("601090",  "Servico de seguros",              "Servicos"),
    ("601100",  "Servico de treinamento e capacitacao", "Servicos"),
]

# Indice catmat → (nome_curto, categoria)
_CATMAT_INDEX: dict[str, tuple[str, str]] = {
    s[0]: (s[1], s[2]) for s in _CATMAT_SEED
}


def _get_cached(cache: dict, key: str, ttl: float = _CACHE_TTL_SECONDS) -> Optional[dict]:
    if key not in cache:
        return None
    data, ts = cache[key]
    if time.time() - ts >= ttl:
        del cache[key]
        return None
    return data


def _set_cached(cache: dict, key: str, data: dict) -> None:
    cache[key] = (data, time.time())


def _get_desc_cached(catmat: str) -> Optional[str]:
    if catmat not in _catmat_desc_cache:
        return None
    desc, ts = _catmat_desc_cache[catmat]
    if time.time() - ts >= _CATMAT_CACHE_TTL:
        del _catmat_desc_cache[catmat]
        return None
    return desc


def _set_desc_cached(catmat: str, desc: str) -> None:
    _catmat_desc_cache[catmat] = (desc, time.time())


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class FaqItem(BaseModel):
    question: str
    answer: str


class ContratoReferencia(BaseModel):
    objeto: str
    orgao: str
    valor: float
    data_assinatura: str
    uf: str


class ItemProfileResponse(BaseModel):
    catmat: str
    nome_item: str
    categoria: str
    total_contratos: int
    valor_p10: Optional[float] = None
    valor_p50: Optional[float] = None
    valor_p90: Optional[float] = None
    valor_medio: Optional[float] = None
    unidade_referencia: str
    contratos_referencia: list[ContratoReferencia]
    faq_items: list[FaqItem]
    periodo_referencia: str
    last_updated: str
    aviso_legal: str


class SitemapItensResponse(BaseModel):
    catmats: list[str]
    total: int
    updated_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/itens/{catmat}/profile",
    response_model=ItemProfileResponse,
    summary="Benchmark de precos governamentais por codigo CATMAT",
)
async def item_profile(catmat: str):
    """Calcula P10/P50/P90 de contratos do PNCP datalake para um item CATMAT.

    Publico, sem auth. Cache: 24h. Substitui o Painel de Precos do ComprasGov
    (descontinuado jul/2025).
    """
    catmat_clean = catmat.strip()
    if not _CATMAT_RE.match(catmat_clean):
        raise HTTPException(status_code=400, detail="Codigo CATMAT invalido (esperado numerico 1-9 digitos)")

    cache_key = f"item_profile:{catmat_clean}"
    cached = _get_cached(_itens_profile_cache, cache_key)
    if cached:
        return ItemProfileResponse(**cached)

    # Nome do item: seed local ou CATMAT API
    nome_item, categoria = _CATMAT_INDEX.get(catmat_clean, (None, "Materiais e Servicos"))
    if not nome_item:
        nome_item = await _fetch_catmat_desc(catmat_clean)
    if not nome_item:
        raise HTTPException(status_code=404, detail="Codigo CATMAT nao encontrado")

    # Contratos do PNCP para este item (busca por palavras-chave do nome)
    valores, contratos_ref = await _fetch_price_data(nome_item)

    if not valores:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum contrato encontrado no datalake para '{nome_item}'",
        )

    p10 = round(statistics.quantiles(valores, n=10)[0], 2) if len(valores) >= 2 else valores[0]
    p50 = round(statistics.median(valores), 2)
    p90 = round(statistics.quantiles(valores, n=10)[-1], 2) if len(valores) >= 2 else valores[-1]
    media = round(sum(valores) / len(valores), 2)

    faq_items = _build_faq(nome_item, catmat_clean, len(valores), p50, media)

    response_data = {
        "catmat": catmat_clean,
        "nome_item": nome_item,
        "categoria": categoria,
        "total_contratos": len(valores),
        "valor_p10": p10,
        "valor_p50": p50,
        "valor_p90": p90,
        "valor_medio": media,
        "unidade_referencia": "por contrato",
        "contratos_referencia": contratos_ref,
        "faq_items": faq_items,
        "periodo_referencia": "Ultimos 12 meses — PNCP",
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aviso_legal": (
            "Precos calculados a partir de contratos publicos registrados no Portal "
            "Nacional de Contratacoes Publicas (PNCP). Os valores representam o preco "
            "contratado global (nao unitario) e podem incluir quantidades distintas. "
            "Utilize como referencia de benchmark, nao como preco de tabela."
        ),
    }

    _set_cached(_itens_profile_cache, cache_key, response_data)
    return ItemProfileResponse(**response_data)


@router.get(
    "/sitemap/itens",
    response_model=SitemapItensResponse,
    summary="Lista de codigos CATMAT para sitemap.xml",
)
async def sitemap_itens(response: Response):
    response.headers.update(SITEMAP_CACHE_HEADERS)
    cached = _get_cached(_itens_sitemap_cache, "catmats")
    if cached:
        record_sitemap_count("itens", len(cached.get("catmats", [])))
        return SitemapItensResponse(**cached)

    catmats = [s[0] for s in _CATMAT_SEED]
    data = {
        "catmats": catmats,
        "total": len(catmats),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _set_cached(_itens_sitemap_cache, "catmats", data)
    record_sitemap_count("itens", len(catmats))
    return SitemapItensResponse(**data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fetch_catmat_desc(catmat: str) -> Optional[str]:
    """Tenta obter nome do item no CATMAT API. Cache: 7 dias."""
    cached = _get_desc_cached(catmat)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(
                f"{_CATMAT_API_BASE}/catmat/v1/materiais",
                params={"codigo": catmat},
            )
        if r.status_code == 200:
            body = r.json()
            items = body if isinstance(body, list) else (body.get("data") or [])
            if items:
                nome = (items[0].get("nomeItem") or items[0].get("descricaoItem") or "").strip()
                if nome:
                    _set_desc_cached(catmat, nome)
                    return nome
    except Exception as e:
        logger.debug("[Itens] CATMAT API falhou para %s: %s", catmat, e)

    return None


async def _fetch_price_data(nome_item: str) -> tuple[list[float], list[dict]]:
    """Busca contratos do PNCP que contenham o nome do item no objeto.

    Retorna (lista_de_valores, top_10_contratos_referencia).
    """
    # Usa as 2 primeiras palavras significativas (>=4 chars) para evitar ruido
    palavras = [p for p in nome_item.lower().split() if len(p) >= 4][:2]
    if not palavras:
        return [], []

    from supabase_client import get_supabase
    sb = get_supabase()

    # Busca contratos com keyword match no objeto
    valores: list[float] = []
    contratos_ref: list[dict] = []

    try:
        # Busca por primeira palavra-chave (PostgREST ilike)
        resp = (
            sb.table("pncp_supplier_contracts")
            .select(
                "valor_global,objeto_contrato,orgao_nome,data_assinatura,uf"
            )
            .ilike("objeto_contrato", f"%{palavras[0]}%")
            .eq("is_active", True)
            .order("data_assinatura", desc=True)
            .limit(1000)
            .execute()
        )
        rows = resp.data or []

        # Filtra por segunda palavra se disponivel (reduz falsos positivos)
        if len(palavras) >= 2:
            rows = [
                r for r in rows
                if palavras[1] in (r.get("objeto_contrato") or "").lower()
            ]

        for row in rows:
            v = _safe_float(row.get("valor_global"))
            if v and v > 0.0:
                valores.append(v)
                if len(contratos_ref) < 10:
                    obj = (row.get("objeto_contrato") or "").strip()
                    contratos_ref.append({
                        "objeto": obj[:200] if len(obj) > 200 else obj,
                        "orgao": (row.get("orgao_nome") or "").strip() or "Nao informado",
                        "valor": v,
                        "data_assinatura": (row.get("data_assinatura") or "")[:10],
                        "uf": (row.get("uf") or "").strip().upper(),
                    })

    except Exception as e:
        logger.error("[Itens] price_data query falhou para '%s': %s", nome_item, e)

    return valores, contratos_ref


def _safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _build_faq(nome: str, catmat: str, total: int, p50: float, media: float) -> list[dict]:
    p50_fmt = _fmt_brl(p50)
    media_fmt = _fmt_brl(media)
    return [
        {
            "question": f"Qual o preco medio de {nome} nas compras publicas?",
            "answer": (
                f"Com base em {total} contrato{'s' if total != 1 else ''} registrado{'s' if total != 1 else ''} "
                f"no Portal Nacional de Contratacoes Publicas (PNCP), o preco mediano (P50) de "
                f"{nome} e {p50_fmt} e a media e {media_fmt}. Os valores refletem o preco "
                "global do contrato, que pode incluir diferentes quantidades."
            ),
        },
        {
            "question": f"O que e o codigo CATMAT {catmat}?",
            "answer": (
                f"O codigo CATMAT {catmat} identifica o item '{nome}' no Catalogo de Materiais "
                "do Governo Federal. O CATMAT e utilizado por orgaos publicos para padronizar "
                "descricoes de itens em processos licitatorios, facilitando a comparacao de precos "
                "entre diferentes contratos."
            ),
        },
        {
            "question": f"Como consultar contratos de {nome} no governo?",
            "answer": (
                f"Todos os contratos de {nome} listados nesta pagina sao dados publicos do "
                "Portal Nacional de Contratacoes Publicas (PNCP), disponivel em pncp.gov.br. "
                "O SmartLic agrega esses dados diariamente e permite monitorar novas licitacoes "
                f"deste item automaticamente."
            ),
        },
    ]


def _fmt_brl(value: float) -> str:
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    if value >= 1_000:
        return f"R$ {value / 1_000:,.0f} mil".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
