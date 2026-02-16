"""
STORY-248 AC1-AC3: Golden Sample Test Suite

Tests real-world procurement descriptions against the filter pipeline
to ensure zero false positives and zero false negatives across ALL 15 sectors.

Each sector has:
- 5+ POSITIVE samples (should MATCH the sector filter)
- 5+ NEGATIVE samples (should NOT match the sector filter)
- Edge cases: ambiguous terms, long text, typos/orthographic variants

The match_keywords function:
1. Normalizes text (lowercase, remove accents, replace punctuation with spaces)
2. Checks exclusions first (fail-fast)
3. Matches keywords with word boundaries (\\b)
4. Validates context_required_keywords (generic keywords need confirming context)
"""

import pytest
from filter import match_keywords
from sectors import get_sector, SECTORS


# ---------------------------------------------------------------------------
# Helper: build kwargs for match_keywords from a SectorConfig
# ---------------------------------------------------------------------------


def _sector_kwargs(sector_id: str) -> dict:
    """Return dict ready to spread into match_keywords(**kwargs)."""
    cfg = get_sector(sector_id)
    return {
        "keywords": cfg.keywords,
        "exclusions": cfg.exclusions or set(),
        "context_required": cfg.context_required_keywords or {},
    }


# ===========================================================================
# 1. VESTUÁRIO E UNIFORMES
# ===========================================================================


class TestGoldenSamplesVestuario:
    """Vestuário e Uniformes — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("vestuario")

    # -- POSITIVE SAMPLES --------------------------------------------------

    @pytest.mark.parametrize("description", [
        # Primary keywords
        "Aquisição de uniformes escolares para alunos da rede municipal de ensino",
        "Confecção de uniformes profissionais para servidores do hospital municipal",
        "Fornecimento de fardamento completo para guardas municipais",
        "Registro de preço para aquisição de vestuário profissional para agentes comunitários",
        "Contratação de empresa para confecção de camisetas e calças para os funcionários da prefeitura",
        # Context-required: avental + context "cozinha"
        "Aquisição de aventais para cozinha da merenda escolar do município",
        # Context-required: jaleco + context "profissional"
        "Fornecimento de jalecos profissional para técnicos de laboratório municipal",
        # Context-required: colete + context "identificação"
        "Aquisição de coletes de identificação para agentes de trânsito da prefeitura",
        # Context-required: epi + context "uniforme"
        "Fornecimento de epi e uniforme completo para equipe operacional da secretaria de obras",
        # Context-required: macacão + context "operacional"
        "Aquisição de macacão para uso operacional dos servidores da coleta de resíduos",
        # Edge case: very long description (200+ chars)
        "Registro de preços para eventual aquisição de uniformes escolares compostos por camisetas, bermudas, calças, meias e agasalhos para atender os alunos matriculados nas escolas municipais de educação infantil e ensino fundamental do município de Campinas no estado de São Paulo",
        # Edge case: description with accents and formal language
        "Pregão eletrônico para aquisição de fardamento destinado à Guarda Civil Municipal, composto por gandolas, calças táticas e bonés",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match vestuario but didn't: {description!r}"

    # -- NEGATIVE SAMPLES ---------------------------------------------------

    @pytest.mark.parametrize("description", [
        # Exclusion: uniformização de procedimentos
        "Uniformização de procedimentos administrativos do tribunal de justiça",
        # Exclusion: confecção de placas
        "Confecção de placas de sinalização para vias públicas do município",
        # Exclusion: curso de costura
        "Curso de corte e costura para capacitação de jovens da comunidade",
        # No matching keywords
        "Aquisição de material de construção para reforma do prédio da secretaria de educação",
        "Contratação de serviço de limpeza e conservação predial para o fórum da comarca",
        # Exclusion: military context
        "Aquisição de uniformes para o batalhão de infantaria do exército",
        # Exclusion: roupa de cama
        "Fornecimento de roupa de cama mesa e banho para abrigo institucional",
        # Context-required WITHOUT context: avental without cozinha/uniforme/etc.
        "Aquisição de avental plumbífero para radiologia do hospital municipal",
        # Exclusion: material de construção matches
        "Fornecimento de material de construção incluindo coletes e botas para canteiro de obra",
        # Exclusion: colete balistico
        "Aquisição de colete balístico para policiais militares do batalhão",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match vestuario but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 2. ALIMENTOS E MERENDA
# ===========================================================================


class TestGoldenSamplesAlimentos:
    """Alimentos e Merenda — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("alimentos")

    @pytest.mark.parametrize("description", [
        "Aquisição de gêneros alimentícios para merenda escolar da rede municipal de ensino",
        "Registro de preço para fornecimento de cesta básica para famílias em situação de vulnerabilidade social",
        "Fornecimento de carne bovina, frango e peixe para o restaurante popular do município",
        "Aquisição de arroz, feijão, farinha e açúcar para o programa de alimentação escolar",
        "Contratação de serviço de alimentação e fornecimento de refeições para servidores públicos",
        # Edge case: long formal description
        "Pregão eletrônico para registro de preços visando à aquisição parcelada de gêneros alimentícios perecíveis e não perecíveis destinados ao atendimento das necessidades da Secretaria Municipal de Educação para o programa de alimentação escolar do município de Belo Horizonte no estado de Minas Gerais",
        # Specific items
        "Aquisição de leite, laticínios e produtos de hortifruti para o programa de merenda escolar",
        "Fornecimento de biscoitos, bolachas, macarrão e conservas para a cozinha do hospital municipal",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match alimentos but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: alimentação in electrical context
        "Aquisição de fonte de alimentação ininterrupta para o data center da prefeitura",
        # Exclusion: óleo lubrificante
        "Fornecimento de óleo lubrificante para manutenção da frota municipal",
        # Exclusion: óleo diesel
        "Abastecimento de oleo diesel para os veículos da secretaria de obras",
        # No matching keywords
        "Aquisição de material de escritório e papelaria para a secretaria municipal de administração",
        "Contratação de empresa para reforma do prédio da escola municipal",
        # Exclusion: bebida alcoólica
        "Fornecimento de bebida alcoólica para evento comemorativo da prefeitura",
        # Exclusion: sal mineral (not food salt)
        "Aquisição de sal mineral para nutrição do rebanho bovino da fazenda experimental",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match alimentos but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 3. HARDWARE E EQUIPAMENTOS DE TI (informatica)
# ===========================================================================


class TestGoldenSamplesInformatica:
    """Hardware e Equipamentos de TI — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("informatica")

    @pytest.mark.parametrize("description", [
        "Aquisição de computadores desktop e notebooks para a secretaria municipal de educação",
        "Registro de preço para fornecimento de impressoras multifuncionais laser coloridas",
        "Aquisição de toner e cartuchos de impressão para a câmara municipal",
        "Fornecimento de equipamento de informática incluindo teclados, scanners e nobreaks",
        "Contratação de empresa para instalação de cabeamento estruturado de rede na nova sede",
        # Edge case: long description with multiple items
        "Pregão eletrônico para registro de preços visando à aquisição de equipamentos de informática e tecnologia da informação, incluindo computadores, monitores, tablets, memória ram e processadores para atender as demandas das secretarias municipais de Curitiba",
        # Specific compound terms
        "Aquisição de acessórios de informatica e periféricos de computador para o laboratório de informática",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match informatica but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: servidor público (people, not machines)
        "Pagamento de remuneração dos servidores públicos da prefeitura municipal",
        # Exclusion: monitor de aluno
        "Contratação de monitor de alunos para o transporte escolar da rede municipal",
        # Exclusion: EPI / uniforme context
        "Aquisição de equipamento de proteção individual e uniformes para a guarda municipal",
        # No matching keywords at all
        "Aquisição de gêneros alimentícios para merenda escolar",
        "Contratação de serviço de vigilância patrimonial para as unidades de saúde",
        # Exclusion: informática educativa
        "Projeto de informática educativa para escolas municipais com capacitação docente",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match informatica but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 4. MOBILIÁRIO
# ===========================================================================


class TestGoldenSamplesMobiliario:
    """Mobiliário — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("mobiliario")

    @pytest.mark.parametrize("description", [
        "Aquisição de mobiliário para o escritório da secretaria municipal de administração",
        "Registro de preço para fornecimento de armários de aço e estantes para o almoxarifado",
        "Aquisição de cadeiras giratórias executivas para a câmara municipal de vereadores",
        "Fornecimento de carteiras escolares e mobiliário escolar para as escolas municipais",
        "Aquisição de poltronas, sofás e escrivaninhas para o gabinete do prefeito",
        # Context-required: mesa + context "escritório"
        "Fornecimento de mesas de escritório com gavetas para a nova sede administrativa",
        # Context-required: banco + context "praça"
        "Aquisição de bancos de madeira para a praça central do município",
        # Context-required: arquivo + context "aço"
        "Fornecimento de arquivos de aço com quatro gavetas para o setor de recursos humanos",
        # Edge case: very long description
        "Pregão eletrônico para registro de preços visando eventual aquisição de mobiliário de escritório incluindo gaveteiros, prateleiras, birôs e mesas de reunião para equipar as novas dependências da Secretaria Municipal de Planejamento e Gestão do município de Salvador",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match mobiliario but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: mesa de negociação
        "Abertura de mesa de negociação entre governo e sindicato dos servidores",
        # Exclusion: banco de dados
        "Contratação de empresa para manutenção do banco de dados da prefeitura",
        # Exclusion: unidade móvel (not furniture)
        "Aquisição de unidade móvel de saúde para atendimento nas comunidades rurais",
        # Exclusion: cadeira de rodas (medical)
        "Fornecimento de cadeira de rodas para pacientes do centro de reabilitação",
        # Exclusion: equipamento médico
        "Aquisição de equipamento médico e mobiliário clínico para o hospital municipal",
        # Context-required: mesa WITHOUT context (standalone)
        "Aquisição de mesa de som profissional para o auditório municipal",
        # Exclusion: telefonia móvel
        "Contratação de serviço de telefonia móvel para os servidores da prefeitura",
        # Exclusion: rack de servidor (IT rack)
        "Aquisição de rack de servidores para o data center da secretaria de tecnologia",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match mobiliario but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 5. PAPELARIA E MATERIAL DE ESCRITÓRIO
# ===========================================================================


class TestGoldenSamplesPapelaria:
    """Papelaria e Material de Escritório — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("papelaria")

    @pytest.mark.parametrize("description", [
        "Aquisição de material de escritório incluindo papel A4, canetas e grampeadores",
        "Fornecimento de material de expediente para as secretarias municipais",
        "Registro de preço para aquisição de papelaria escolar e material de escritório",
        "Aquisição de envelopes, cadernos, fichários, blocos de notas e fita adesiva",
        "Fornecimento de material escolar básico incluindo lápis de cor e giz de cera para as escolas",
        # Edge case: compound terms
        "Aquisição de caneta esferográfica, marca-texto, pincel atômico e calculadoras para a secretaria",
        # Edge case: very long description
        "Pregão eletrônico para registro de preços visando à aquisição parcelada de material de escritório e papelaria, incluindo papel sulfite, etiquetas, clipes, pasta suspensa, perfurador de papel e demais itens necessários ao funcionamento administrativo das unidades da Prefeitura Municipal",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match papelaria but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: papel de parede
        "Aquisição de papel de parede para redecoração do gabinete do prefeito",
        # Exclusion: papel higiênico (cleaning, not stationery)
        "Fornecimento de papel higiênico e papel toalha para as unidades de saúde",
        # Exclusion: cola cirúrgica (medical)
        "Aquisição de cola cirúrgica e materiais especiais para o centro cirúrgico",
        # Exclusion: grampo cirúrgico (medical)
        "Fornecimento de grampo cirúrgico descartável para o hospital municipal",
        # No matching keywords
        "Aquisição de uniformes escolares para alunos da rede municipal de ensino",
        # Exclusion: pasta de dente
        "Fornecimento de pasta de dente e material de higiene pessoal para abrigos municipais",
        # Exclusion: horário de expediente
        "Regulamentação do horário de expediente das repartições públicas municipais",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match papelaria but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 6. ENGENHARIA, PROJETOS E OBRAS
# ===========================================================================


class TestGoldenSamplesEngenharia:
    """Engenharia, Projetos e Obras — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("engenharia")

    @pytest.mark.parametrize("description", [
        "Contratação de empresa para execução de obra de construção civil do novo terminal rodoviário",
        "Obra de pavimentação asfáltica em diversas ruas do município",
        "Reforma do prédio da secretaria municipal de educação incluindo pintura predial e impermeabilização",
        "Contratação de projeto arquitetônico para a nova sede da câmara municipal",
        "Execução de obra de construção civil com fornecimento de material e mão de obra",
        # Edge case: long description
        "Pregão eletrônico para contratação de empresa especializada em engenharia para execução de obra de construção civil visando a ampliação e reforma do prédio da Secretaria Municipal de Saúde incluindo alvenaria, concreto armado, instalação elétrica, instalação hidráulica e pintura de fachada no município de Porto Alegre",
        # Materials
        "Aquisição de cimento, aço, areia e brita para obra de edificação da escola municipal",
        # Precision terms
        "Contratação de sondagem geotécnica e laudo técnico para terreno da futura unidade de saúde",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match engenharia but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: engenharia de software
        "Contratação de empresa de engenharia de software para desenvolvimento de sistema",
        # Exclusion: reforma administrativa
        "Implementação da reforma administrativa no âmbito da prefeitura municipal",
        # Exclusion: infraestrutura de TI
        "Contratação de infraestrutura de ti para o data center da prefeitura",
        # Exclusion: construção de conhecimento (abstract)
        "Projeto de construção de conhecimento para capacitação de professores da rede",
        # No matching keywords
        "Aquisição de gêneros alimentícios para merenda escolar",
        # Exclusion: infraestrutura de rede
        "Implantação de infraestrutura de rede e cabeamento estruturado para a secretaria",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match engenharia but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 7. SOFTWARE E SISTEMAS
# ===========================================================================


class TestGoldenSamplesSoftware:
    """Software e Sistemas — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("software")

    @pytest.mark.parametrize("description", [
        "Aquisição de licença de software Microsoft 365 para as estações de trabalho da prefeitura",
        "Contratação de empresa para desenvolvimento de software de gestão pública municipal",
        "Licenciamento de software AutoCAD para o departamento de engenharia",
        "Contratação de serviço SaaS para sistema de gestão escolar da rede municipal",
        "Implantação de sistema ERP integrado para gestão administrativa e financeira",
        # Edge case: long description
        "Pregão eletrônico para contratação de solução tecnológica em plataforma cloud para sistema de gestão pública incluindo módulos de compras, licitação, almoxarifado, folha de pagamento, protocolo e portal de transparência com licenciamento por assinatura mensal",
        # Business intelligence
        "Aquisição de ferramenta de business intelligence e consultoria de TI para análise de dados",
        # Digital platform
        "Contratação de plataforma digital para portal web da prefeitura municipal",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match software but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: hardware (keep in informatica)
        "Aquisição de computadores e notebooks para a secretaria de educação",
        # Exclusion: sistema de ar condicionado (physical)
        "Instalação de sistema de ar condicionado para a nova sede da secretaria",
        # Exclusion: sistema de alarme (security)
        "Aquisição de sistema de alarme e vigilância eletrônica para as escolas",
        # Exclusion: sistema de drenagem
        "Implantação de sistema de drenagem pluvial na área urbana do município",
        # Exclusion: curso de software
        "Contratação de curso de software para capacitação dos servidores",
        # Exclusion: sistema fotovoltaico
        "Instalação de sistema fotovoltaico na cobertura do prédio da prefeitura",
        # No matching keywords
        "Aquisição de uniformes escolares para alunos da rede municipal",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match software but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 8. FACILITIES E MANUTENÇÃO
# ===========================================================================


class TestGoldenSamplesFacilities:
    """Facilities e Manutenção — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("facilities")

    @pytest.mark.parametrize("description", [
        "Contratação de serviço de limpeza e conservação predial para as unidades da prefeitura",
        "Aquisição de material de limpeza incluindo detergente, desinfetante e água sanitária",
        "Fornecimento de papel higiênico, papel toalha e saco de lixo para as repartições públicas",
        "Contratação de empresa para serviços prediais de portaria, recepção e zeladoria",
        "Contratação de serviços de jardinagem e paisagismo para as áreas verdes do prédio",
        # Edge case: long description
        "Pregão eletrônico para contratação de empresa especializada em serviços de facilities management incluindo limpeza predial, conservação de imóveis, copa e cozinha, recepção, copeira e zelador para atender as necessidades da Secretaria Municipal de Administração do município de Recife",
        # Cleaning products
        "Aquisição de saneantes, alvejante, sabão, vassouras, rodos e esponjas para o almoxarifado",
        # Third-party support
        "Contratação de terceirização de mão de obra para serviços de apoio administrativo",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match facilities but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: manutenção de veículos
        "Contratação de manutenção de veículos e frota da secretaria de transportes",
        # Exclusion: pavimentação (engenharia)
        "Obra de pavimentação e recapeamento de vias públicas do município",
        # Exclusion: limpeza de bueiros (infra)
        "Contratação de serviço de limpeza de bueiros e galerias pluviais",
        # Exclusion: construção civil
        "Execução de obra de construção civil para reforma do prédio da prefeitura",
        # Exclusion: limpeza de terrenos
        "Contratação para limpeza de terrenos baldios no perímetro urbano",
        # Exclusion: desinsetização (pest control)
        "Contratação de controle de pragas e desinsetização para as unidades de saúde",
        # Exclusion: portaria ministerial
        "Publicação de portaria ministerial regulamentando o uso de recursos do FNDE",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match facilities but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 9. SAÚDE E MEDICAMENTOS
# ===========================================================================


class TestGoldenSamplesSaude:
    """Saúde e Medicamentos — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("saude")

    @pytest.mark.parametrize("description", [
        "Aquisição de medicamentos da farmácia básica para as unidades de saúde do município",
        "Fornecimento de material médico-hospitalar incluindo seringas, agulhas e gazes",
        "Registro de preço para aquisição de equipamento médico hospitalar para o novo hospital",
        "Aquisição de reagentes e kit diagnóstico para o laboratório municipal de análises clínicas",
        "Fornecimento de próteses e órteses para pacientes do centro de reabilitação",
        # Specific drugs
        "Aquisição de dipirona, paracetamol, amoxicilina e omeprazol para a rede de atenção básica",
        # Edge case: long description
        "Pregão eletrônico para registro de preços visando à aquisição de materiais médico-hospitalares incluindo luva de procedimento, compressa, atadura, esparadrapo, fio de sutura, bisturi e curativo para atender as necessidades das unidades básicas de saúde e do hospital municipal do município de Manaus no estado do Amazonas",
        # Medical equipment
        "Aquisição de desfibrilador, monitor multiparâmetro e ventilador pulmonar para a UTI",
        # Dental
        "Fornecimento de material odontológico incluindo resina dental e anestésicos para o CEO",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match saude but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: saúde do trabalhador
        "Implementação do programa de saúde do trabalhador para os servidores municipais",
        # Exclusion: vigilância sanitária
        "Contratação de agentes para vigilância sanitária do município",
        # Exclusion: sondagem de solo (not medical sonda)
        "Execução de sondagem de solo e sondagem geotécnica para obra de fundação",
        # Exclusion: software / sistema de gestão
        "Implantação de sistema de gestão hospitalar via software de prontuário eletrônico",
        # No matching keywords
        "Aquisição de uniformes escolares para alunos da rede municipal de ensino",
        # Exclusion: material de limpeza
        "Aquisição de material de limpeza e produto de limpeza para o hospital",
        # Exclusion: instrumental musical
        "Aquisição de instrumental musical e instrumentais musicais para a escola de música",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match saude but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 10. VIGILÂNCIA E SEGURANÇA PATRIMONIAL
# ===========================================================================


class TestGoldenSamplesVigilancia:
    """Vigilância e Segurança Patrimonial — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("vigilancia")

    @pytest.mark.parametrize("description", [
        "Contratação de empresa para prestação de serviço de vigilância patrimonial armada e desarmada",
        "Implantação de sistema de CFTV com câmeras de segurança nas escolas municipais",
        "Contratação de serviço de monitoramento eletrônico 24 horas para os prédios públicos",
        "Aquisição de catracas e sistema de controle de acesso para a sede da prefeitura",
        "Contratação de vigilantes armados para postos de vigilância nas unidades de saúde",
        # Edge case: electronic security
        "Aquisição de câmeras de monitoramento, central de alarme e detector de metais para o fórum",
        # Edge case: long description
        "Pregão eletrônico para contratação de empresa especializada na prestação de serviços de vigilância patrimonial armada e desarmada, portaria armada, monitoramento remoto via circuito fechado de televisão e segurança eletrônica para as dependências da Prefeitura Municipal de Fortaleza no estado do Ceará",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match vigilancia but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: vigilância sanitária
        "Fortalecimento das ações de vigilância sanitária nas feiras livres do município",
        # Exclusion: vigilância epidemiológica
        "Contratação de equipe para vigilância epidemiológica e controle de endemias",
        # Exclusion: segurança da informação
        "Implementação de política de segurança da informação para os sistemas da prefeitura",
        # Exclusion: segurança do trabalho
        "Contratação de empresa de segurança do trabalho para emissão de laudos técnicos",
        # Exclusion: uniforme (keep in vestuario)
        "Aquisição de uniformes e fardamento para a guarda municipal",
        # No matching keywords
        "Aquisição de material de escritório para a secretaria municipal de administração",
        # Exclusion: monitoramento ambiental
        "Serviço de monitoramento ambiental dos recursos hídricos da bacia hidrográfica",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match vigilancia but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 11. TRANSPORTE E VEÍCULOS
# ===========================================================================


class TestGoldenSamplesTransporte:
    """Transporte e Veículos — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("transporte")

    @pytest.mark.parametrize("description", [
        "Aquisição de veículos zero km tipo sedan para a frota da secretaria de saúde",
        "Contratação de serviço de manutenção de veículos e frota da prefeitura municipal",
        "Registro de preço para abastecimento de combustível gasolina e diesel para a frota municipal",
        "Aquisição de pneus e peças automotivas para os veículos da secretaria de obras",
        "Contratação de transporte escolar com micro-ônibus para os alunos da zona rural",
        # Edge case: multiple vehicle types
        "Aquisição de ambulâncias, caminhões e caminhonetes para as secretarias municipais",
        # Edge case: long description
        "Pregão eletrônico para registro de preços visando à contratação de empresa especializada na prestação de serviços de manutenção preventiva e corretiva de veículos da frota municipal incluindo manutenção automotiva, funilaria e pintura, borracharia, autoelétrica e oficina mecânica para atender as necessidades do município de Goiânia",
        # Fuel cards
        "Contratação de empresa para fornecimento de cartão combustível para abastecimento da frota",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match transporte but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: veículo de comunicação
        "Contratação de veículo de comunicação para publicidade institucional da prefeitura",
        # Exclusion: filtro de água (not automotive filter)
        "Aquisição de filtro de água e bebedouros para as escolas municipais",
        # Exclusion: bateria de notebook (not automotive)
        "Fornecimento de bateria de notebook e acessórios de informática",
        # Exclusion: ventilador mecânico (medical)
        "Aquisição de ventilador mecânico para a unidade de terapia intensiva do hospital",
        # No matching keywords
        "Aquisição de material de limpeza e produtos de higienização",
        # Exclusion: software / sistema de gestão
        "Implantação de sistema de gestão para controle patrimonial da prefeitura",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match transporte but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 12. MANUTENÇÃO E CONSERVAÇÃO PREDIAL
# ===========================================================================


class TestGoldenSamplesManutencaoPredial:
    """Manutenção e Conservação Predial — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("manutencao_predial")

    @pytest.mark.parametrize("description", [
        "Contratação de empresa para manutenção predial preventiva e corretiva dos prédios públicos",
        "Manutenção de elevadores das unidades da prefeitura municipal incluindo peças e mão de obra",
        "Contratação de serviço de climatização e manutenção de ar condicionado tipo PMOC",
        "Execução de pintura predial e impermeabilização da cobertura do prédio da secretaria",
        "Manutenção das instalações elétricas e instalações hidráulicas dos prédios municipais",
        # Edge case: long description
        "Pregão eletrônico para contratação de empresa especializada na prestação de serviços de manutenção predial preventiva e corretiva incluindo instalações prediais elétricas e hidráulicas, pintura de fachada, impermeabilização, manutenção de elevadores e gestão predial de utilidades para as edificações da Prefeitura Municipal de Brasília",
        # Building generators
        "Manutenção de grupo gerador e subestação dos prédios da administração municipal",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match manutencao_predial but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: manutenção de veículos
        "Serviço de manutenção de veículos e manutenção de frota para a secretaria de transportes",
        # Exclusion: manutenção de estradas (infra)
        "Contratação para manutenção de estradas vicinais no município",
        # Exclusion: manutenção de computador (IT)
        "Serviço de manutenção de computador e manutenção de impressora do parque tecnológico",
        # Exclusion: construção civil (engenharia)
        "Execução de obra de construção civil para ampliação do prédio da escola",
        # Exclusion: manutenção de tratores (agriculture)
        "Contratação de manutenção de tratores e implementos agrícolas para a secretaria rural",
        # No matching keywords
        "Aquisição de material de escritório para a secretaria de administração",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match manutencao_predial but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 13. ENGENHARIA RODOVIÁRIA E INFRAESTRUTURA VIÁRIA
# ===========================================================================


class TestGoldenSamplesEngenhariaRodoviaria:
    """Engenharia Rodoviária e Infraestrutura Viária — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("engenharia_rodoviaria")

    @pytest.mark.parametrize("description", [
        "Execução de pavimentação asfáltica com CBUQ em diversas ruas do município",
        "Contratação de obra de recapeamento asfáltico das principais rodovias estaduais",
        "Implantação de sinalização viária e sinalização rodoviária na BR-101",
        "Serviço de conservação rodoviária e manutenção rodoviária da rodovia estadual",
        "Execução de serviço de fresagem e micropavimento na rodovia municipal",
        # Context-required: ponte + context "construção"
        "Construção de ponte sobre o rio Paraná na rodovia estadual",
        # Context-required: estrada + context "pavimentação"
        "Pavimentação de estrada vicinal de acesso às comunidades rurais",
        # Edge case: long description
        "Pregão eletrônico para contratação de empresa especializada em engenharia rodoviária para execução de obra de restauração rodoviária incluindo recapeamento asfáltico, drenagem rodoviária, sinalização viária, defensas metálicas e acostamento na rodovia BR-116 no trecho entre os municípios de Feira de Santana e Vitória da Conquista no estado da Bahia",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match engenharia_rodoviaria but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: terminal rodoviário (bus terminal)
        "Reforma do terminal rodoviário municipal para melhoria do embarque de passageiros",
        # Exclusion: estação rodoviária (bus station)
        "Aquisição de mobiliário para a nova estação rodoviária interestadual",
        # Exclusion: túnel vpn (IT, not physical)
        "Configuração de túnel vpn para interligação das secretarias municipais",
        # Exclusion: engenharia de software
        "Contratação de consultoria em engenharia de software para o departamento de TI",
        # Context-required: ponte WITHOUT construction context
        "Curso de ponte de rede e infraestrutura de dados para servidores públicos",
        # No matching keywords
        "Aquisição de material de escritório e papelaria para a câmara municipal",
        # Exclusion: estrada de ferro
        "Manutenção da estrada de ferro para transporte de minério",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match engenharia_rodoviaria but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 14. MATERIAIS ELÉTRICOS E INSTALAÇÕES
# ===========================================================================


class TestGoldenSamplesMateriaisEletricos:
    """Materiais Elétricos e Instalações — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("materiais_eletricos")

    @pytest.mark.parametrize("description", [
        "Aquisição de materiais elétricos incluindo cabos, disjuntores e eletrodutos",
        "Fornecimento de luminárias LED e lâmpadas para iluminação pública do município",
        "Aquisição de quadro de distribuição elétrica e quadro elétrico para a nova escola",
        "Contratação de serviço de instalação elétrica e manutenção elétrica nos prédios",
        "Aquisição de transformador e subestação para a rede elétrica do distrito industrial",
        # Edge case: long description
        "Registro de preços visando à aquisição de material elétrico incluindo fio de cobre, cabo elétrico, condutor elétrico, condulete, caixa de passagem, tomada, interruptor, painel elétrico, reator, refletor e estabilizador para atender as demandas das secretarias municipais de Cuiabá",
        # Voltage/protection
        "Aquisição de chave seccionadora, para-raios e sistema de aterramento para proteção elétrica",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match materiais_eletricos but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: eletrodomésticos
        "Aquisição de eletrodomésticos para a cozinha do restaurante popular municipal",
        # Exclusion: equipamento eletrônico
        "Fornecimento de equipamento eletrônico e eletrônicos para o laboratório da escola",
        # Exclusion: informática
        "Aquisição de computadores e equipamentos de informatica para a secretaria de educação",
        # Exclusion: veículo elétrico
        "Aquisição de ônibus elétrico para o sistema de transporte público municipal",
        # Exclusion: guitarra elétrica
        "Aquisição de guitarra elétrica e instrumentos musicais para a escola de música",
        # Exclusion: cerca elétrica (security)
        "Instalação de cerca elétrica no perímetro da escola municipal",
        # No matching keywords
        "Aquisição de uniformes escolares para os alunos da rede municipal de ensino",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match materiais_eletricos but did: {description!r}, matched: {keywords}"


# ===========================================================================
# 15. MATERIAIS HIDRÁULICOS E SANEAMENTO
# ===========================================================================


class TestGoldenSamplesMateriaisHidraulicos:
    """Materiais Hidráulicos e Saneamento — Golden Samples."""

    @pytest.fixture
    def kw(self):
        return _sector_kwargs("materiais_hidraulicos")

    @pytest.mark.parametrize("description", [
        "Aquisição de materiais hidráulicos incluindo tubos PVC, conexões e registros",
        "Contratação de serviço de perfuração de poço artesiano para abastecimento de água",
        "Aquisição de bomba submersa e hidrômetro para o sistema de distribuição de água",
        "Implantação de rede coletora de esgoto e estação de tratamento de esgoto no distrito",
        "Fornecimento de tubo PEAD e válvula hidráulica para a adutora municipal",
        # Edge case: long description
        "Pregão eletrônico para registro de preços visando à aquisição de material hidráulico incluindo tubulação, encanamento, conexão hidráulica, registro hidráulico, tubo de ferro fundido, tubo galvanizado e reservatório de água para as obras de saneamento básico do município de Belém no estado do Pará",
        # Sanitation
        "Execução de obra de esgotamento sanitário e implantação de fossa séptica em comunidades rurais",
        # Water treatment
        "Contratação de serviço de tratamento de água incluindo cloração e fluoretação para a ETA",
    ])
    def test_positive_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert matched, f"Should match materiais_hidraulicos but didn't: {description!r}"

    @pytest.mark.parametrize("description", [
        # Exclusion: prensa hidráulica (industrial)
        "Aquisição de prensa hidráulica para o setor de manutenção industrial",
        # Exclusion: elevador hidráulico (not plumbing)
        "Manutenção de elevador hidráulico do estacionamento da secretaria de administração",
        # Exclusion: escavadeira hidráulica (heavy equipment)
        "Locação de escavadeira hidráulica para obra de terraplanagem no município",
        # Exclusion: direção hidráulica (automotive)
        "Reparo de direção hidráulica nos veículos da frota municipal",
        # Exclusion: freio hidráulico (automotive)
        "Troca de freio hidráulico e suspensão hidráulica dos caminhões da coleta de lixo",
        # No matching keywords
        "Aquisição de uniformes escolares para alunos da rede municipal de ensino",
    ])
    def test_negative_samples(self, kw, description):
        matched, keywords = match_keywords(description, **kw)
        assert not matched, f"Should NOT match materiais_hidraulicos but did: {description!r}, matched: {keywords}"


# ===========================================================================
# CROSS-SECTOR EDGE CASES
# ===========================================================================


class TestGoldenSamplesCrossSectorEdgeCases:
    """Edge cases that span multiple sectors or test boundary conditions."""

    def test_empty_description_matches_no_sector(self):
        """An empty description should never match any sector."""
        for sector_id in SECTORS:
            kw = _sector_kwargs(sector_id)
            matched, keywords = match_keywords("", **kw)
            assert not matched, f"Empty string matched {sector_id}: {keywords}"

    def test_gibberish_matches_no_sector(self):
        """Random gibberish should never match any sector."""
        gibberish = "xyzzyplugh qwerty asdfgh zxcvbn foobar bazquux"
        for sector_id in SECTORS:
            kw = _sector_kwargs(sector_id)
            matched, keywords = match_keywords(gibberish, **kw)
            assert not matched, f"Gibberish matched {sector_id}: {keywords}"

    def test_all_15_sectors_loaded(self):
        """Verify all 15 expected sectors are loaded from YAML."""
        expected = {
            "vestuario", "alimentos", "informatica", "mobiliario",
            "papelaria", "engenharia", "software", "facilities",
            "saude", "vigilancia", "transporte", "manutencao_predial",
            "engenharia_rodoviaria", "materiais_eletricos", "materiais_hidraulicos",
        }
        assert set(SECTORS.keys()) == expected

    @pytest.mark.parametrize("description,expected_sector", [
        # Ambiguous: "reforma" could be engenharia but not administrative
        (
            "Reforma da sede da secretaria de educação incluindo pintura predial e alvenaria",
            "engenharia",
        ),
        # Ambiguous: "limpeza" must be facilities, not infra
        (
            "Aquisição de detergente e desinfetante para limpeza predial das escolas",
            "facilities",
        ),
        # Ambiguous: "manutenção" for building must be manutencao_predial not transporte
        (
            "Contratação de manutenção predial preventiva das instalações elétricas",
            "manutencao_predial",
        ),
    ])
    def test_ambiguous_matches_correct_sector(self, description, expected_sector):
        """Verify ambiguous descriptions match the intended sector."""
        kw = _sector_kwargs(expected_sector)
        matched, keywords = match_keywords(description, **kw)
        assert matched, (
            f"Description should match {expected_sector} but didn't: "
            f"{description!r}"
        )

    def test_accent_insensitive_matching(self):
        """Keywords with accents should match descriptions without accents and vice versa."""
        # "pavimentação" (keyword has accent) vs description without accent
        kw = _sector_kwargs("engenharia_rodoviaria")
        matched, _ = match_keywords(
            "Execucao de obra de pavimentacao asfaltica no municipio",
            **kw,
        )
        assert matched, "Accent-free description should match accented keyword"

    def test_hyphenated_terms(self):
        """Hyphenated terms should match after normalization (hyphen -> space)."""
        kw = _sector_kwargs("saude")
        matched, _ = match_keywords(
            "Aquisição de material médico-hospitalar para o hospital municipal",
            **kw,
        )
        assert matched, "Hyphenated term should match after normalization"

    def test_very_long_description_performance(self):
        """A 500+ character description should still match correctly."""
        long_desc = (
            "Pregão eletrônico para registro de preços visando à aquisição "
            "parcelada de gêneros alimentícios perecíveis e não perecíveis "
            "incluindo arroz tipo 1, feijão carioca, farinha de mandioca, "
            "açúcar cristal, óleo de soja, macarrão espaguete, biscoitos "
            "salgados e doces, leite integral, carne bovina de primeira, "
            "frango resfriado inteiro e em cortes, peixe congelado em filé, "
            "frutas da estação, verduras e legumes frescos do tipo hortifruti "
            "para atender as necessidades do programa de alimentação escolar "
            "do município ao longo do exercício de dois mil e vinte e seis "
            "conforme termo de referência e especificações técnicas em anexo "
            "ao edital de licitação publicado no portal nacional."
        )
        assert len(long_desc) > 500
        kw = _sector_kwargs("alimentos")
        matched, keywords = match_keywords(long_desc, **kw)
        assert matched, f"Long description should match alimentos: {keywords}"
        assert len(keywords) > 3, "Multiple keywords should match in long text"
