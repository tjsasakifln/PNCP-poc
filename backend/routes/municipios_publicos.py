"""Sprint 4 Parte 13: perfis de municipios para SEO programatico.

Endpoints publicos (sem auth) que agregam:
  - Dados de enriquecimento IBGE (enriched_entities entity_type='municipio')
  - Licitacoes abertas do PNCP datalake (pncp_raw_bids)

Endpoints:
  GET /v1/municipios/{slug}/profile   — perfil do municipio para /municipios/{slug}
  GET /v1/sitemap/municipios          — lista de slugs para sitemap.xml
"""

import asyncio
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Response

from routes._sitemap_cache_headers import SITEMAP_CACHE_HEADERS
from pydantic import BaseModel

from metrics import record_sitemap_count

logger = logging.getLogger(__name__)
router = APIRouter(tags=["municipios-publicos"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_municipio_profile_cache: dict[str, tuple[dict, float]] = {}
_municipio_sitemap_cache: dict[str, tuple[dict, float]] = {}

# Seed: 200 municipios de maior relevancia B2G (capitais + polos regionais)
# Formato: (slug, ibge_code, nome_display, uf, populacao_estimada)
_MUNICIPIOS_SEED: list[tuple[str, str, str, str, int]] = [
    ("sao-paulo-sp",         "3550308", "Sao Paulo",         "SP", 11451245),
    ("rio-de-janeiro-rj",    "3304557", "Rio de Janeiro",    "RJ",  6776147),
    ("brasilia-df",          "5300108", "Brasilia",          "DF",  3094325),
    ("salvador-ba",          "2927408", "Salvador",          "BA",  2886698),
    ("fortaleza-ce",         "2304400", "Fortaleza",         "CE",  2686612),
    ("belo-horizonte-mg",    "3106200", "Belo Horizonte",    "MG",  2530701),
    ("manaus-am",            "1302603", "Manaus",            "AM",  2255903),
    ("curitiba-pr",          "4106902", "Curitiba",          "PR",  1963726),
    ("recife-pe",            "2611606", "Recife",            "PE",  1661017),
    ("porto-alegre-rs",      "4314902", "Porto Alegre",      "RS",  1484941),
    ("belem-pa",             "1501402", "Belem",             "PA",  1506420),
    ("goiania-go",           "5208707", "Goiania",           "GO",  1536097),
    ("sao-luis-ma",          "2111300", "Sao Luis",          "MA",  1115932),
    ("maceio-al",            "2704302", "Maceio",            "AL",   1018948),
    ("natal-rn",             "2408102", "Natal",             "RN",   890480),
    ("teresina-pi",          "2211001", "Teresina",          "PI",   868075),
    ("campo-grande-ms",      "5002704", "Campo Grande",      "MS",   902901),
    ("joao-pessoa-pb",       "2507507", "Joao Pessoa",       "PB",   817511),
    ("aracaju-se",           "2800308", "Aracaju",           "SE",   664908),
    ("porto-velho-ro",       "1100205", "Porto Velho",       "RO",   548952),
    ("macapa-ap",            "1600303", "Macapa",            "AP",   512902),
    ("cuiaba-mt",            "5103403", "Cuiaba",            "MT",   650131),
    ("florianopolis-sc",     "4205407", "Florianopolis",     "SC",   508826),
    ("vitoria-es",           "3205309", "Vitoria",           "ES",   369889),
    ("palmas-to",            "1721000", "Palmas",            "TO",   313588),
    ("rio-branco-ac",        "1200401", "Rio Branco",        "AC",   413418),
    ("boa-vista-rr",         "1400100", "Boa Vista",         "RR",   419652),
    # Polos regionais
    ("campinas-sp",          "3509502", "Campinas",          "SP",  1222674),
    ("guarulhos-sp",         "3518800", "Guarulhos",         "SP",  1392121),
    ("sao-bernardo-do-campo-sp", "3548708", "Sao Bernardo do Campo", "SP", 844483),
    ("osasco-sp",            "3534401", "Osasco",            "SP",   696850),
    ("ribeirao-preto-sp",    "3543402", "Ribeirao Preto",    "SP",   714169),
    ("santo-andre-sp",       "3547809", "Santo Andre",       "SP",   721884),
    ("sao-jose-dos-campos-sp", "3549904", "Sao Jose dos Campos", "SP", 738976),
    ("sorocaba-sp",          "3552205", "Sorocaba",          "SP",   700888),
    ("mogi-das-cruzes-sp",   "3530607", "Mogi das Cruzes",   "SP",   461534),
    ("santos-sp",            "3548500", "Santos",            "SP",   433311),
    ("uberlandia-mg",        "3170206", "Uberlandia",        "MG",   706597),
    ("contagem-mg",          "3118601", "Contagem",          "MG",   663077),
    ("juiz-de-fora-mg",      "3136702", "Juiz de Fora",      "MG",   573285),
    ("niteroi-rj",           "3303302", "Niteroi",           "RJ",   511786),
    ("duque-de-caxias-rj",   "3301702", "Duque de Caxias",   "RJ",   930157),
    ("nova-iguacu-rj",       "3303500", "Nova Iguacu",       "RJ",   795212),
    ("feira-de-santana-ba",  "2910800", "Feira de Santana",  "BA",   627477),
    ("caruaru-pe",           "2604106", "Caruaru",           "PE",   361118),
    ("petrolina-pe",         "2611101", "Petrolina",         "PE",   352648),
    ("caxias-do-sul-rs",     "4305108", "Caxias do Sul",     "RS",   503048),
    ("pelotas-rs",           "4314100", "Pelotas",           "RS",   344156),
    ("londrina-pr",          "4113700", "Londrina",          "PR",   575277),
    ("maringa-pr",           "4115200", "Maringa",           "PR",   440723),
    ("anapolis-go",          "5201405", "Anapolis",          "GO",   391772),
    ("aparecida-de-goiania-go", "5201405", "Aparecida de Goiania", "GO", 590638),
    ("imperatriz-ma",        "2105302", "Imperatriz",        "MA",   258873),
    ("camaçari-ba",          "2905701", "Camacari",          "BA",   334579),
    ("vitoria-da-conquista-ba", "2933307", "Vitoria da Conquista", "BA", 341532),
    ("mossoró-rn",           "2408003", "Mossoro",           "RN",   301339),
    ("sobral-ce",            "2312908", "Sobral",            "CE",   230810),
    ("macae-rj",             "3302403", "Macae",             "RJ",   259764),
    ("volta-redonda-rj",     "3306701", "Volta Redonda",     "RJ",   271523),
    ("blumenau-sc",          "4202404", "Blumenau",          "SC",   369430),
    ("joinville-sc",         "4209102", "Joinville",         "SC",   616527),
    ("sao-jose-sc",          "4216602", "Sao Jose",          "SC",   261260),
    ("foz-do-iguacu-pr",     "4108304", "Foz do Iguacu",     "PR",   258532),
    ("cascavel-pr",          "4104808", "Cascavel",          "PR",   349316),
    ("betim-mg",             "3106705", "Betim",             "MG",   440852),
    ("montes-claros-mg",     "3143302", "Montes Claros",     "MG",   415059),
    ("bauru-sp",             "3506003", "Bauru",             "SP",   374272),
    ("jundiai-sp",           "3525904", "Jundiai",           "SP",   422427),
    ("santo-andre-sp",       "3547809", "Santo Andre",       "SP",   721884),
    ("sao-jose-do-rio-preto-sp", "3549805", "Sao Jose do Rio Preto", "SP", 457374),
    ("santarem-pa",          "1506807", "Santarem",          "PA",   308073),
    ("maues-am",             "1302900", "Maues",             "AM",    61633),
    ("parauapebas-pa",       "1505536", "Parauapebas",       "PA",   224249),
    ("ananindeua-pa",        "1500800", "Ananindeua",        "PA",   535547),
    ("barreiras-ba",         "2903201", "Barreiras",         "BA",   163376),
    ("ilheus-ba",            "2913606", "Ilheus",            "BA",   185562),
    ("porto-seguro-ba",      "2925303", "Porto Seguro",      "BA",   149513),
    ("alagoinhas-ba",        "2900702", "Alagoinhas",        "BA",   162250),
    ("divinopolis-mg",       "3121605", "Divinopolis",       "MG",   247109),
    ("ipatinga-mg",          "3131307", "Ipatinga",          "MG",   256407),
    ("governador-valadares-mg", "3127701", "Governador Valadares", "MG", 284702),
    ("teofilo-otoni-mg",     "3168606", "Teofilo Otoni",     "MG",   139853),
    ("ponta-grossa-pr",      "4119905", "Ponta Grossa",      "PR",   363218),
    ("maringá-pr",           "4115200", "Maringa",           "PR",   440723),
    ("chapeco-sc",           "4204202", "Chapeco",           "SC",   232985),
    ("criciuma-sc",          "4204608", "Criciuma",          "SC",   224213),
    ("novo-hamburgo-rs",     "4313409", "Novo Hamburgo",     "RS",   243173),
    ("santa-maria-rs",       "4316907", "Santa Maria",       "RS",   285990),
    ("cambe-pr",             "4104501", "Cambe",             "PR",   109498),
    ("araçatuba-sp",         "3502804", "Aracatuba",         "SP",   188778),
    ("presidente-prudente-sp", "3541406", "Presidente Prudente", "SP", 230783),
    ("franca-sp",            "3516200", "Franca",            "SP",   353604),
    ("piracicaba-sp",        "3538709", "Piracicaba",        "SP",   416241),
    ("limeira-sp",           "3526902", "Limeira",           "SP",   314017),
    ("taubate-sp",           "3554102", "Taubate",           "SP",   318348),
    ("carapicuiba-sp",       "3510609", "Carapicuiba",       "SP",   398523),
    ("praia-grande-sp",      "3541000", "Praia Grande",      "SP",   337397),
    ("suzano-sp",            "3552502", "Suzano",            "SP",   301799),
    ("diadema-sp",           "3513801", "Diadema",           "SP",   400898),
    ("maua-sp",              "3529401", "Maua",              "SP",   476887),
    ("sao-vicente-sp",       "3551702", "Sao Vicente",       "SP",   366384),
    ("sao-caetano-do-sul-sp", "3548807", "Sao Caetano do Sul", "SP",  161647),
    ("rio-claro-sp",         "3543907", "Rio Claro",         "SP",   216141),
    ("americana-sp",         "3501608", "Americana",         "SP",   241675),
    ("itaquaquecetuba-sp",   "3522901", "Itaquaquecetuba",   "SP",   373267),
    ("caçapava-sp",          "3508603", "Cacapava",          "SP",   108688),
    ("ferraz-de-vasconcelos-sp", "3515608", "Ferraz de Vasconcelos", "SP", 195782),
    ("itapecerica-da-serra-sp", "3522406", "Itapecerica da Serra", "SP", 163785),
    ("birigui-sp",           "3506508", "Birigui",           "SP",    125020),
    ("jaboticabal-sp",       "3524105", "Jaboticabal",       "SP",    76023),
    ("sertaozinho-sp",       "3551702", "Sertaozinho",       "SP",   118956),
    ("araraquara-sp",        "3503208", "Araraquara",        "SP",   242200),
    ("marilia-sp",           "3529005", "Marilia",           "SP",   241564),
    ("barueri-sp",           "3505708", "Barueri",           "SP",   283482),
    ("cotia-sp",             "3512803", "Cotia",             "SP",   279411),
    ("santana-de-parnaiba-sp", "3547304", "Santana de Parnaiba", "SP", 130082),
    ("itapevi-sp",           "3522505", "Itapevi",           "SP",   240668),
    ("itaborai-rj",          "3301900", "Itaborai",          "RJ",   248030),
    ("belford-roxo-rj",      "3300456", "Belford Roxo",      "RJ",   494145),
    ("sao-joao-de-meriti-rj", "3305109", "Sao Joao de Meriti", "RJ", 468376),
    ("campos-dos-goytacazes-rj", "3301009", "Campos dos Goytacazes", "RJ", 536111),
    ("petropolis-rj",        "3303906", "Petropolis",        "RJ",   306645),
    ("angra-dos-reis-rj",    "3300100", "Angra dos Reis",    "RJ",   198341),
    ("cabo-frio-rj",         "3300704", "Cabo Frio",         "RJ",   224025),
    ("sao-goncalo-rj",       "3304904", "Sao Goncalo",       "RJ",  1107806),
    ("nilopolis-rj",         "3303203", "Nilopolis",         "RJ",   155950),
    ("mesquita-rj",          "3302858", "Mesquita",          "RJ",   176725),
    ("nilópolis-rj",         "3303203", "Nilopolis",         "RJ",   155950),
    ("maringa-pr",           "4115200", "Maringa",           "PR",   440723),
    ("guarapuava-pr",        "4109401", "Guarapuava",        "PR",   181566),
    ("toledo-pr",            "4127700", "Toledo",            "PR",   144684),
    ("araucaria-pr",         "4101804", "Araucaria",         "PR",   148375),
    ("colombo-pr",           "4104659", "Colombo",           "PR",   243817),
    ("sao-jose-dos-pinhais-pr", "4125506", "Sao Jose dos Pinhais", "PR", 327401),
    ("almirante-tamandare-pr", "4100707", "Almirante Tamandare", "PR", 113590),
    ("pinhais-pr",           "4119152", "Pinhais",           "PR",   135192),
    ("hortolandia-sp",       "3519071", "Hortolandia",       "SP",   244573),
    ("indaiatuba-sp",        "3521309", "Indaiatuba",        "SP",   260360),
    ("boituva-sp",           "3507605", "Boituva",           "SP",    70498),
    ("itatiba-sp",           "3523404", "Itatiba",           "SP",   123694),
    ("sao-roque-sp",         "3550001", "Sao Roque",         "SP",    93484),
    ("braganca-paulista-sp", "3507605", "Braganca Paulista",  "SP",   172523),
    ("campina-grande-pb",    "2504009", "Campina Grande",    "PB",   415403),
    ("patos-pb",             "2510808", "Patos",             "PB",   102762),
    ("parnaiba-pi",          "2207702", "Parnaiba",          "PI",   152447),
    ("picos-pi",             "2208007", "Picos",             "PI",    76683),
    ("crato-ce",             "2304202", "Crato",             "CE",   133818),
    ("juazeiro-do-norte-ce", "2307304", "Juazeiro do Norte", "CE",   278225),
    ("iguatu-ce",            "2305506", "Iguatu",            "CE",    101577),
    ("timon-ma",             "2112209", "Timon",             "MA",   170029),
    ("caxias-ma",            "2102880", "Caxias",            "MA",   163045),
    ("bacabal-ma",           "2101400", "Bacabal",           "MA",   105476),
    ("arapiraca-al",         "2701209", "Arapiraca",         "AL",   236695),
    ("uniao-dos-palmares-al", "2714408", "Uniao dos Palmares", "AL",  62656),
    ("lagarto-se",           "2803500", "Lagarto",           "SE",    104157),
    ("itabaiana-se",         "2803005", "Itabaiana",         "SE",    97044),
    ("ilheus-ba",            "2913606", "Ilheus",            "BA",   185562),
    ("jequie-ba",            "2918001", "Jequie",            "BA",   167366),
    ("senhor-do-bonfim-ba",  "2930105", "Senhor do Bonfim",  "BA",    76534),
    ("eunapolis-ba",         "2910727", "Eunapolis",         "BA",   120476),
    ("teixeira-de-freitas-ba", "2931350", "Teixeira de Freitas", "BA", 169067),
    ("rondonopolis-mt",      "5107602", "Rondonopolis",      "MT",   284612),
    ("sinop-mt",             "5107909", "Sinop",             "MT",   153539),
    ("varzea-grande-mt",     "5108402", "Varzea Grande",     "MT",   282965),
    ("dourados-ms",          "5003702", "Dourados",          "MS",   228862),
    ("tres-lagoas-ms",       "5008305", "Tres Lagoas",       "MS",   125662),
    ("corumba-ms",           "5003207", "Corumba",           "MS",    113291),
    ("rio-verde-go",         "5218805", "Rio Verde",         "GO",   245359),
    ("luziania-go",          "5212501", "Luziania",          "GO",   221057),
    ("caldas-novas-go",      "5204508", "Caldas Novas",      "GO",   116458),
    ("sao-luis-de-montes-belos-go", "5220058", "Sao Luis de Montes Belos", "GO", 31050),
    ("palmas-to",            "1721000", "Palmas",            "TO",   313588),
    ("araguaina-to",         "1702109", "Araguaina",         "TO",   185878),
    ("gurupi-to",            "1709500", "Gurupi",            "TO",    89592),
    ("porto-nacional-to",    "1718204", "Porto Nacional",    "TO",    56397),
    ("marabá-pa",            "1504208", "Maraba",            "PA",   285297),
    ("altamira-pa",          "1500602", "Altamira",          "PA",   113257),
    ("cajazerias-pb",        "2503704", "Cajazerias",        "PB",    60516),
    ("sobral-ce",            "2312908", "Sobral",            "CE",   230810),
    ("quixada-ce",           "2311405", "Quixada",           "CE",    84519),
    ("crateus-ce",           "2304269", "Crateus",           "CE",    75267),
    ("iguatu-ce",            "2305506", "Iguatu",            "CE",   101577),
    ("caucaia-ce",           "2303709", "Caucaia",           "CE",   356978),
    ("maracanau-ce",         "2307650", "Maracanau",         "CE",   235491),
    ("caninde-ce",           "2302800", "Caninde",           "CE",    64969),
    ("russas-ce",            "2312403", "Russas",            "CE",    77793),
    ("quixeramobim-ce",      "2311603", "Quixeramobim",      "CE",    82800),
    ("guaramirim-sc",        "4206306", "Guaramirim",        "SC",    40897),
    ("itajai-sc",            "4208203", "Itajai",            "SC",   225891),
    ("balneario-camboriu-sc", "4202008", "Balneario Camboriu", "SC",  145074),
    ("tubarao-sc",           "4218707", "Tubarao",           "SC",   104913),
    ("lages-sc",             "4209300", "Lages",             "SC",   156727),
    ("sao-bento-do-sul-sc",  "4215901", "Sao Bento do Sul",  "SC",    82963),
    ("cacador-sc",           "4203006", "Cacador",           "SC",    76503),
    ("videira-sc",           "4219507", "Videira",           "SC",    52038),
    ("concordia-sc",         "4204202", "Concordia",         "SC",    77278),
    ("xanxere-sc",           "4223903", "Xanxere",           "SC",    49337),
    ("pelotas-rs",           "4314100", "Pelotas",           "RS",   344156),
    ("canoas-rs",            "4304606", "Canoas",            "RS",   348955),
    ("sao-leopoldo-rs",      "4318705", "Sao Leopoldo",      "RS",   229626),
    ("bage-rs",              "4301602", "Bage",              "RS",   121286),
    ("uruguaiana-rs",        "4322400", "Uruguaiana",        "RS",   126935),
    ("passo-fundo-rs",       "4314407", "Passo Fundo",       "RS",   210937),
    ("novo-hamburgo-rs",     "4313409", "Novo Hamburgo",     "RS",   243173),
    ("gravatai-rs",          "4309209", "Gravatai",          "RS",   271393),
    ("viamao-rs",            "4323002", "Viamao",            "RS",   261068),
    ("alvorada-rs",          "4300604", "Alvorada",          "RS",   225840),
    ("sapucaia-do-sul-rs",   "4320008", "Sapucaia do Sul",   "RS",   144986),
    ("cachoeirinha-rs",      "4303103", "Cachoeirinha",      "RS",   138732),
    ("esteio-rs",            "4307609", "Esteio",            "RS",    84006),
    ("sapiranga-rs",         "4320107", "Sapiranga",         "RS",    81353),
    ("rio-grande-rs",        "4315602", "Rio Grande",        "RS",   209378),
    ("ijui-rs",              "4309100", "Ijui",              "RS",    83557),
    ("santana-do-livramento-rs", "4317301", "Santana do Livramento", "RS", 89419),
    ("macapa-ap",            "1600303", "Macapa",            "AP",   512902),
    ("santana-ap",           "1600600", "Santana",           "AP",   131768),
    ("laranjal-do-jari-ap",  "1600279", "Laranjal do Jari",  "AP",    61949),
    ("oiapoque-ap",          "1600501", "Oiapoque",          "AP",    29462),
    ("porto-velho-ro",       "1100205", "Porto Velho",       "RO",   548952),
    ("ji-parana-ro",         "1100122", "Ji-Parana",         "RO",   140564),
    ("cacoal-ro",            "1100049", "Cacoal",            "RO",    99346),
    ("vilhena-ro",           "1100304", "Vilhena",           "RO",   103219),
    ("rio-branco-ac",        "1200401", "Rio Branco",        "AC",   413418),
    ("cruzeiro-do-sul-ac",   "1200203", "Cruzeiro do Sul",   "AC",    83044),
    ("boa-vista-rr",         "1400100", "Boa Vista",         "RR",   419652),
    ("rorainopolis-rr",      "1400472", "Rorainopolis",      "RR",    43534),
    ("tefé-am",              "1304203", "Tefe",              "AM",    63568),
    ("itacoatiara-am",       "1301902", "Itacoatiara",       "AM",    99139),
    ("parintins-am",         "1303403", "Parintins",         "AM",   118681),
    ("tabatinga-am",         "1304062", "Tabatinga",         "AM",    62025),
    ("coari-am",             "1301209", "Coari",             "AM",    77965),
    ("palmas-to",            "1721000", "Palmas",            "TO",   313588),
]

# Dedup preservando primeira ocorrencia por slug
_seen_slugs: set[str] = set()
_MUNICIPIOS: list[tuple[str, str, str, str, int]] = []
for _m in _MUNICIPIOS_SEED:
    if _m[0] not in _seen_slugs:
        _seen_slugs.add(_m[0])
        _MUNICIPIOS.append(_m)

# Indice slug → (ibge_code, nome, uf, pop)
_SLUG_INDEX: dict[str, dict] = {
    m[0]: {"ibge_code": m[1], "nome": m[2], "uf": m[3], "populacao": m[4]}
    for m in _MUNICIPIOS
}


def _get_cached(cache: dict, key: str) -> Optional[dict]:
    if key not in cache:
        return None
    data, ts = cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del cache[key]
        return None
    return data


def _set_cached(cache: dict, key: str, data: dict) -> None:
    cache[key] = (data, time.time())


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class FaqItem(BaseModel):
    question: str
    answer: str


class LicitacaoRecente(BaseModel):
    objeto: str
    orgao: str
    valor: Optional[float] = None
    data_publicacao: str
    modalidade: str


class MunicipioProfileResponse(BaseModel):
    slug: str
    nome: str
    uf: str
    ibge_code: str
    populacao: int
    pib_per_capita: Optional[float] = None
    total_licitacoes_abertas: int
    valor_total_licitacoes: float
    licitacoes_recentes: list[LicitacaoRecente]
    faq_items: list[FaqItem]
    last_updated: str
    aviso_legal: str


class SitemapMunicipiosResponse(BaseModel):
    slugs: list[str]
    total: int
    updated_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/municipios/{slug}/profile",
    response_model=MunicipioProfileResponse,
    summary="Perfil de municipio com licitacoes abertas (por slug)",
)
async def municipio_profile(slug: str):
    """Agrega licitacoes abertas do PNCP datalake + dados IBGE para a pagina
    /municipios/{slug}. Publico, sem auth. Cache: 24h TTL em memoria."""
    slug_clean = slug.strip().lower()
    if slug_clean not in _SLUG_INDEX:
        raise HTTPException(status_code=404, detail="Municipio nao encontrado")

    cache_key = f"municipio_profile:{slug_clean}"
    cached = _get_cached(_municipio_profile_cache, cache_key)
    if cached:
        return MunicipioProfileResponse(**cached)

    meta = _SLUG_INDEX[slug_clean]
    ibge_code = meta["ibge_code"]
    nome = meta["nome"]
    uf = meta["uf"]
    populacao = meta["populacao"]

    from supabase_client import get_supabase
    sb = get_supabase()

    # Dados enriquecidos do IBGE (enriched_entities)
    pib_per_capita: Optional[float] = None
    try:
        enrich_resp = (
            sb.table("enriched_entities")
            .select("data")
            .eq("entity_type", "municipio")
            .eq("entity_id", ibge_code)
            .limit(1)
            .execute()
        )
        if enrich_resp.data:
            enrich_data = enrich_resp.data[0].get("data") or {}
            pib_per_capita = enrich_data.get("pib_per_capita")
            populacao = enrich_data.get("populacao") or populacao
    except Exception as e:
        logger.warning(
            "[Municipios] enriched_entities falhou para %s (continuando sem enrichment): %s",
            ibge_code, e,
        )

    # Licitacoes abertas no datalake (pncp_raw_bids)
    # STORY-425: use correct column name `data_publicacao` (not `data_publicacao_pncp` — never existed)
    # STORY-426: wrap in asyncio.wait_for to guard against statement_timeout (57014)
    _BIDS_QUERY_TIMEOUT_S = float(os.getenv("MUNICIPIOS_BIDS_QUERY_TIMEOUT_S", "6.0"))
    total_licitacoes = 0
    valor_total = 0.0
    licitacoes_recentes: list[dict] = []
    try:
        _query = (
            sb.table("pncp_raw_bids")
            .select(
                "objeto_compra,orgao_razao_social,valor_total_estimado,"
                "data_publicacao,modalidade_nome"
            )
            .eq("uf", uf)
            .eq("is_active", True)
            .order("data_publicacao", desc=True)
            .limit(500)
        )
        bids_resp = await asyncio.wait_for(
            asyncio.to_thread(_query.execute),
            timeout=_BIDS_QUERY_TIMEOUT_S,
        )
        rows = bids_resp.data or []
        total_licitacoes = len(rows)
        for row in rows:
            v = _safe_float(row.get("valor_total_estimado"))
            valor_total += v
        # Top 20 recentes
        for row in rows[:20]:
            obj = (row.get("objeto_compra") or "").strip()
            if len(obj) > 200:
                obj = obj[:197] + "..."
            licitacoes_recentes.append({
                "objeto": obj or "Nao informado",
                "orgao": (row.get("orgao_razao_social") or "").strip() or "Nao informado",
                "valor": _safe_float(row.get("valor_total_estimado")) or None,
                "data_publicacao": (row.get("data_publicacao") or "")[:10],
                "modalidade": (row.get("modalidade_nome") or "").strip() or "Nao informado",
            })
    except asyncio.TimeoutError:
        # STORY-426 AC2: degraded response on timeout — return empty bid lists, no 500
        try:
            from metrics import SUPABASE_QUERY_TIMEOUT_TOTAL
            SUPABASE_QUERY_TIMEOUT_TOTAL.labels(endpoint="municipios_stats").inc()
        except Exception:
            pass
        logger.warning(
            "[Municipios] pncp_raw_bids query timeout (>%.1fs) para uf=%s — retornando degradado",
            _BIDS_QUERY_TIMEOUT_S, uf,
        )
        # total_licitacoes / valor_total / licitacoes_recentes keep their zero defaults
    except Exception as e:
        logger.error("[Municipios] pncp_raw_bids query falhou para uf=%s: %s", uf, e)

    faq_items = _build_faq(nome, uf, total_licitacoes, populacao)

    response_data = {
        "slug": slug_clean,
        "nome": nome,
        "uf": uf,
        "ibge_code": ibge_code,
        "populacao": populacao,
        "pib_per_capita": round(pib_per_capita, 2) if pib_per_capita else None,
        "total_licitacoes_abertas": total_licitacoes,
        "valor_total_licitacoes": round(valor_total, 2),
        "licitacoes_recentes": licitacoes_recentes,
        "faq_items": faq_items,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aviso_legal": (
            "Dados de fontes publicas: Portal Nacional de Contratacoes Publicas (PNCP) "
            "e Instituto Brasileiro de Geografia e Estatistica (IBGE). "
            "Atualizacao diaria. Populacao: estimativa IBGE."
        ),
    }

    _set_cached(_municipio_profile_cache, cache_key, response_data)
    return MunicipioProfileResponse(**response_data)


@router.get(
    "/sitemap/municipios",
    response_model=SitemapMunicipiosResponse,
    summary="Lista de slugs de municipios para sitemap.xml",
)
async def sitemap_municipios(response: Response):
    """Retorna slugs dos municipios pre-cadastrados para o sitemap.xml.
    Cache: 24h em memoria.
    """
    response.headers.update(SITEMAP_CACHE_HEADERS)
    cached = _get_cached(_municipio_sitemap_cache, "slugs")
    if cached:
        record_sitemap_count("municipios", len(cached.get("slugs", [])))
        return SitemapMunicipiosResponse(**cached)

    slugs = [m[0] for m in _MUNICIPIOS]
    data = {
        "slugs": slugs,
        "total": len(slugs),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _set_cached(_municipio_sitemap_cache, "slugs", data)
    record_sitemap_count("municipios", len(slugs))
    return SitemapMunicipiosResponse(**data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _build_faq(nome: str, uf: str, total: int, pop: int) -> list[dict]:
    pop_fmt = f"{pop:,}".replace(",", ".") if pop else "nao informada"
    return [
        {
            "question": f"Quantas licitacoes estao abertas em {nome}-{uf}?",
            "answer": (
                f"Ha {total} licitacao{'es' if total != 1 else ''} ativa{'s' if total != 1 else ''} "
                f"registrada{'s' if total != 1 else ''} no Portal Nacional de Contratacoes Publicas (PNCP) "
                f"para orgaos sediados em {nome}-{uf}. "
                "Os dados sao atualizados diariamente a partir do PNCP."
            ),
        },
        {
            "question": f"Como participar de licitacoes em {nome}-{uf}?",
            "answer": (
                f"Para participar de licitacoes em {nome}-{uf}, a empresa deve estar habilitada "
                "no SICAF (Sistema de Cadastramento Unificado de Fornecedores) ou no cadastro do "
                "orgao especifico, e apresentar documentacao de regularidade fiscal e trabalhista. "
                "O SmartLic monitora automaticamente os editais abertos e filtra os mais relevantes "
                "para o seu setor."
            ),
        },
        {
            "question": f"Qual a populacao de {nome}-{uf}?",
            "answer": (
                f"{nome} tem populacao estimada de {pop_fmt} habitantes, "
                "segundo o Instituto Brasileiro de Geografia e Estatistica (IBGE)."
            ),
        },
    ]
