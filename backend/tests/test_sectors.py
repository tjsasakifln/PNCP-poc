"""
Tests for multi-sector keyword filtering — based on real PNCP audit (2026-01-29).

Each test case was derived from actual procurement descriptions found in PNCP data.
"""

from filter import match_keywords
from sectors import SECTORS, get_sector, list_sectors


class TestSectorConfig:
    """Tests for sector configuration basics."""

    def test_all_sectors_exist(self):
        sectors = list_sectors()
        ids = {s["id"] for s in sectors}
        assert ids == {"vestuario", "alimentos", "informatica", "mobiliario", "papelaria", "engenharia", "software", "facilities", "manutencao_predial"}

    def test_get_sector_returns_config(self):
        s = get_sector("vestuario")
        assert s.id == "vestuario"
        assert len(s.keywords) > 0

    def test_get_sector_invalid_raises(self):
        import pytest
        with pytest.raises(KeyError):
            get_sector("inexistente")


class TestInformaticaSector:
    """Tests for Informática e Tecnologia sector — audit-derived."""

    def _match(self, texto):
        s = SECTORS["informatica"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_matches_notebooks(self):
        ok, kw = self._match("Registro de Preços para aquisição de notebooks para a FIPASE")
        assert ok is True

    def test_matches_toner(self):
        ok, _ = self._match("REGISTRO DE PREÇO PARA AQUISIÇÃO DE RECARGAS DE CARTUCHOS DE TONERS")
        assert ok is True

    def test_matches_desktops_monitors(self):
        ok, _ = self._match("AQUISIÇÃO DE ESTAÇÕES DE TRABALHO (DESKTOPS) E MONITORES")
        assert ok is True

    def test_excludes_servidores_publicos(self):
        """Audit FP: 'servidores públicos' matched 'servidores' keyword."""
        ok, _ = self._match(
            "Registro de preços para aquisição de EPIs destinados à proteção dos servidores públicos"
        )
        assert ok is False

    def test_excludes_pagamento_servidores(self):
        """Audit FP: banking service for civil servants matched 'servidores'."""
        ok, _ = self._match(
            "CONTRATAÇÃO DE ESTABELECIMENTO BANCÁRIO PARA PAGAMENTOS DOS SERVIDORES ATIVOS E INATIVOS"
        )
        assert ok is False

    def test_excludes_folha_pagamento_servidores(self):
        ok, _ = self._match(
            "Contratação de instituição bancária para folha de pagamento dos servidores da Prefeitura"
        )
        assert ok is False


class TestLimpezaInFacilities:
    """Tests for cleaning products/services (now merged into facilities)."""

    def _match(self, texto):
        s = SECTORS["facilities"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_matches_material_limpeza(self):
        ok, _ = self._match("AQUISIÇÃO FUTURA DE DIVERSOS MATERIAIS DE LIMPEZA")
        assert ok is True

    def test_matches_saco_de_lixo(self):
        ok, _ = self._match("AQUISICAO DE SACO DE LIXO")
        assert ok is True

    def test_excludes_escavadeira_limpeza(self):
        """Audit FP: excavator for lagoon cleaning matched 'limpeza'."""
        ok, _ = self._match(
            "Aquisição de escavadeira hidráulica anfíbia destinada às atividades de limpeza e desassoreamento da lagoa"
        )
        assert ok is False

    def test_excludes_nebulizacao(self):
        """Audit FP: pest control nebulization matched 'inseticida'."""
        ok, _ = self._match(
            "Registro de preços de serviços de nebulização costal com inseticida fornecido"
        )
        assert ok is False

    def test_excludes_limpeza_veiculos(self):
        """Audit FP: automotive cleaning products matched 'limpeza'."""
        ok, _ = self._match(
            "AQUISIÇÃO DE LUBRIFICANTES E PRODUTOS DE LIMPEZA PESADA PARA VEÍCULOS"
        )
        assert ok is False


class TestMobiliarioSector:
    """Tests for Mobiliário sector — audit-derived."""

    def _match(self, texto):
        s = SECTORS["mobiliario"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_matches_mesas_reuniao(self):
        ok, _ = self._match("Aquisição eventual de 80 mesas de reunião")
        assert ok is True

    def test_matches_armario(self):
        ok, _ = self._match("Aquisição de armário vestiário de aço")
        assert ok is True

    def test_excludes_equipamentos_moveis(self):
        """Audit FP: 'EQUIPAMENTOS MÓVEIS (NOTEBOOKS)' matched 'móveis'."""
        ok, _ = self._match("AQUISIÇÃO DE ESTAÇÕES DE TRABALHO (DESKTOPS), EQUIPAMENTOS MÓVEIS (NOTEBOOKS)")
        assert ok is False

    def test_excludes_roupa_cama_mesa_banho(self):
        """Audit FP: 'roupa de cama, mesa e banho' matched 'mesa'."""
        ok, _ = self._match("Aquisição de material de roupa de cama, mesa e banho")
        assert ok is False


class TestPapelariaSector:
    """Tests for Papelaria sector — audit-derived."""

    def _match(self, texto):
        s = SECTORS["papelaria"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_matches_papel_sulfite(self):
        ok, _ = self._match("Abertura de Ata de Registro de Preços para aquisição de Papel Sulfite")
        assert ok is True

    def test_matches_material_escolar(self):
        ok, _ = self._match("Aquisição de kits de material escolar")
        assert ok is True

    def test_excludes_clipes_aneurisma(self):
        """Audit FP: surgical clips (OPME) matched 'clipes'."""
        ok, _ = self._match("Aquisição de Material de Consumo, OPME Clipes de Aneurismas")
        assert ok is False


class TestEngenhariaSector:
    """Tests for Engenharia e Construção sector — audit-derived."""

    def _match(self, texto):
        s = SECTORS["engenharia"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_matches_materiais_construcao(self):
        ok, _ = self._match("AQUISIÇÃO DE MATERIAIS DE CONSTRUÇÃO DIVERSOS")
        assert ok is True

    def test_matches_concreto(self):
        ok, _ = self._match("REGISTRO DE PREÇOS para eventual aquisição de concreto")
        assert ok is True

    def test_matches_sondagem_geotecnica(self):
        ok, _ = self._match(
            "CONTRATAÇÃO DE EMPRESA PARA PRESTAÇÃO DE SERVIÇOS DE SONDAGEM GEOTÉCNICA — Secretaria de Obras"
        )
        assert ok is True

    def test_allows_mao_de_obra_civil(self):
        """'Mão de obra' should NOT be excluded — legit civil works use this term.

        Audit 2026-01-29: Removing 'mão de obra' exclusion because it blocks
        legitimate items like 'fornecimento de material e mão de obra para reforma'.
        Prefer false positives over false negatives (lost opportunities).
        """
        ok, _ = self._match(
            "CONTRATAÇÃO COM FORNECIMENTO DE MATERIAL E MÃO DE OBRA PARA REVITALIZAÇÃO DA PRAÇA"
        )
        assert ok is True

    def test_excludes_infraestrutura_telecom(self):
        """Audit FP: telecom infrastructure matched 'infraestrutura'."""
        ok, _ = self._match(
            "Contratação para modernizar e ampliar a infraestrutura de comunicação da Prefeitura"
        )
        assert ok is False

    def test_excludes_infraestrutura_temporaria(self):
        """Audit FP: temporary event infrastructure matched 'infraestrutura'."""
        ok, _ = self._match(
            "Prestação de serviços de montagem e desmontagem de infraestrutura temporária para eventos"
        )
        assert ok is False

    def test_excludes_cenarios_cenograficos(self):
        """Audit FP: stage scenography matched 'construção'."""
        ok, _ = self._match(
            "CONTRATAÇÃO PARA CONSTRUÇÃO DE CENÁRIOS CENOGRÁFICOS DESTINADOS À PAIXÃO DE CRISTO"
        )
        assert ok is False

    def test_excludes_secretaria_infraestrutura(self):
        """Audit FP: department name containing 'infraestrutura'."""
        ok, _ = self._match(
            "Contratação de postos de trabalho de auxiliar de serviços gerais — Secretaria de Infraestrutura"
        )
        assert ok is False

    def test_excludes_carroceria_madeira(self):
        """Audit FP: vehicle with wooden body matched 'madeira'."""
        ok, _ = self._match("Locação de caminhão toco com cabine suplementar e carroceria de madeira")
        assert ok is False


class TestAlimentosSector:
    """Tests for Alimentos e Merenda sector — audit-derived."""

    def _match(self, texto):
        s = SECTORS["alimentos"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_matches_generos_alimenticios(self):
        ok, _ = self._match("Gêneros Alimentícios Remanescentes")
        assert ok is True

    def test_matches_merenda_escolar(self):
        ok, _ = self._match(
            "REGISTRO DE PREÇOS PARA AQUISIÇÃO DE GÊNEROS ALIMENTÍCIOS PARA MERENDA ESCOLAR"
        )
        assert ok is True

    def test_matches_cafe(self):
        ok, _ = self._match("AQUISIÇÃO PARCELADA DE CAFÉ PARA O ANO DE 2026")
        assert ok is True

    def test_excludes_oleo_diesel(self):
        ok, _ = self._match("Aquisição de óleo diesel para frota municipal")
        assert ok is False

    def test_excludes_oleo_lubrificante(self):
        ok, _ = self._match("Aquisição de óleo lubrificante para máquinas")
        assert ok is False


class TestSoftwareSector:
    """Tests for Software e Sistemas sector — real-world derived."""

    def _match(self, texto):
        s = SECTORS["software"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_matches_microsoft_office(self):
        ok, _ = self._match("Aquisição de licenças Microsoft Office 365 para a Secretaria de Educação")
        assert ok is True

    def test_matches_licenca_software(self):
        ok, _ = self._match("CONTRATAÇÃO DE LICENCIAMENTO DE SOFTWARE DE GESTÃO PÚBLICA")
        assert ok is True

    def test_matches_saas_plataforma(self):
        ok, _ = self._match("Contratação de plataforma SaaS em nuvem para gestão escolar")
        assert ok is True

    def test_matches_desenvolvimento_sistema(self):
        ok, _ = self._match("Desenvolvimento de sistema web para protocolo digital")
        assert ok is True

    def test_matches_sistema_gestao(self):
        ok, _ = self._match("AQUISIÇÃO DE SISTEMA DE GESTÃO HOSPITALAR")
        assert ok is True

    def test_matches_erp(self):
        ok, _ = self._match("Implantação de sistema ERP integrado para Prefeitura")
        assert ok is True

    def test_matches_consultoria_ti(self):
        ok, _ = self._match("Contratação de consultoria de TI para implantação de sistema de compras")
        assert ok is True

    def test_excludes_hardware_computador(self):
        """Hardware should be in 'informatica' sector, not 'software'."""
        ok, _ = self._match("Aquisição de computadores e notebooks para laboratório")
        assert ok is False

    def test_excludes_hardware_impressora(self):
        ok, _ = self._match("AQUISIÇÃO DE IMPRESSORAS E SCANNERS PARA SECRETARIA")
        assert ok is False

    def test_excludes_hardware_servidor_fisico(self):
        ok, _ = self._match("Aquisição de servidor físico para datacenter")
        assert ok is False

    def test_excludes_curso_treinamento(self):
        """Training/courses are not software procurement."""
        ok, _ = self._match("Contratação de curso de desenvolvimento de software para servidores")
        assert ok is False

    def test_excludes_capacitacao_ti(self):
        ok, _ = self._match("Capacitação em software de gestão para equipe administrativa")
        assert ok is False

    def test_allows_software_plus_consultoria(self):
        """Software procurement bundled with consultancy services should match."""
        ok, _ = self._match(
            "Aquisição de licenças de software SAP com serviços de implantação e consultoria"
        )
        assert ok is True

    def test_allows_portal_transparencia(self):
        ok, _ = self._match("Desenvolvimento de portal de transparência para município")
        assert ok is True

    def test_allows_sistema_licitacao(self):
        ok, _ = self._match("Contratação de sistema de licitação e compras eletrônicas")
        assert ok is True

    # False Positive Prevention Tests (Issue #FESTIVAL-FP)

    def test_excludes_agua_mineral(self):
        """Water should NOT match software sector."""
        ok, _ = self._match("Aquisição de água mineral, por sistema de registro de preços")
        assert ok is False

    def test_excludes_plotagem_paineis(self):
        """Physical signage/panels should NOT match software."""
        ok, _ = self._match(
            "Contratação de empresa especializada no serviço de confecção de plotagens e painéis em chapa"
        )
        assert ok is False

    def test_excludes_sistema_climatizacao(self):
        """HVAC systems should NOT match software."""
        ok, _ = self._match(
            "Contratação de empresa para locação de sistema de climatização evaporativa para os pavilhões"
        )
        assert ok is False

    def test_excludes_sistema_sonorizacao(self):
        """Audio systems should NOT match software."""
        ok, _ = self._match(
            "PRESTAÇÃO DE SERVIÇO TÉCNICO PARA A MANUTENÇÃO PREVENTIVA E CORRETIVA DE INTRUMENTOS MUSICAIS, SISTEMAS DE SONORIZAÇÃO E ILUNAÇÃO CÊNICA"
        )
        assert ok is False

    def test_excludes_balanca_gado(self):
        """Livestock scales should NOT match software."""
        ok, _ = self._match(
            "fornecimento de balança para pesagem de gado composta por plataforma 4×2,5 m em madeira cumaru com estrutura metálica reforçada, sistema de pesagem manual"
        )
        assert ok is False

    def test_excludes_primeiros_socorros(self):
        """First aid supplies should NOT match software."""
        ok, _ = self._match(
            "Aquisição de itens de primeiros socorros, higiene pessoal, proteção individual e apoio à assistência básica"
        )
        assert ok is False

    def test_excludes_ferramentas_manuais(self):
        """Hand tools should NOT match software."""
        ok, _ = self._match("Aquisição de ferramentas manuais e acessórios por meio de Sistema de Registro de Preços")
        assert ok is False

    def test_excludes_sistema_videomonitoramento(self):
        """Video surveillance hardware should NOT match software."""
        ok, _ = self._match(
            "Serviços de manutenção preventiva e corretiva do sistema de videomonitoramento urbano do Município"
        )
        assert ok is False

    def test_excludes_moto_bombas(self):
        """Water pumps should NOT match software."""
        ok, _ = self._match(
            "AQUISIÇÃO DE MOTO BOMBAS SUBMERSAS, CABOS DE PRIMEIRA QUALIDADE, CONTRATAÇÃO DE MÃO DE OBRA ESPECIALIZADA"
        )
        assert ok is False

    def test_excludes_oxigenio_medicinal(self):
        """Medical oxygen should NOT match software."""
        ok, _ = self._match(
            "AQUISIÇÃO CONTÍNUA E PARCELADA DE OXIGÊNIO MEDICINAL, DEVIDAMENTE COMPRIMIDO E ACONDICIONADO EM CILINDROS"
        )
        assert ok is False

    def test_excludes_caminhao_plataforma(self):
        """Trucks should NOT match software."""
        ok, _ = self._match(
            "Aquisição de Equipamento Rodoviário sendo um CAMINHÃO PLATAFORMA FIXA SOBRE CHASSI 6x4"
        )
        assert ok is False

    def test_excludes_kit_lanche(self):
        """Food kits should NOT match software."""
        ok, _ = self._match(
            "Registro de preços para a aquisição de kits de lanche matinal para os usuário do sistema único de saúde"
        )
        assert ok is False

    def test_excludes_sondagem_geologica(self):
        """Geological surveying should NOT match software."""
        ok, _ = self._match(
            "Contratação de empresa especializada por meio do Sistema de Registro de Preços para execução de serviços de Sondagens - Tipo SPT"
        )
        assert ok is False

    def test_excludes_curso_corte_costura(self):
        """Sewing classes should NOT match software."""
        ok, _ = self._match(
            "Contratacao de instrutor de corte costura e artesanato com reconhecimento pelo SICAB"
        )
        assert ok is False

    def test_excludes_escavadeira_hidraulica(self):
        """Excavators should NOT match software."""
        ok, _ = self._match(
            "CONTRATAÇÃO DE EMPRESA PARA PRESTAÇÃO DE SERVIÇOS DE HORAS MÁQUINA DE ESCAVADEIRA HIDRÁULICA"
        )
        assert ok is False

    def test_excludes_iluminacao_publica(self):
        """Public lighting should NOT match software."""
        ok, _ = self._match(
            "CONTRATAÇÃO DE EMPRESAS PARA FORNECIMENTO DE MATERIAIS PARA MANUTENÇÃO DA ILUMINAÇÃO PÚBLICA"
        )
        assert ok is False

    def test_excludes_maquiagem_cabelo(self):
        """Beauty services should NOT match software."""
        ok, _ = self._match(
            "contratação de empresa especializada em cuidados com beleza para suprir a necessidade de serviço de maquiagem e cabelo"
        )
        assert ok is False

    def test_excludes_sistema_gradeamento(self):
        """Mechanical grating systems should NOT match software."""
        ok, _ = self._match(
            "Contratação de empresa especializada na prestação de serviços de manutenção preventiva e corretiva, com fornecimento de peças, de sistemas de gradeamento mecanizado"
        )
        assert ok is False

    def test_excludes_sistema_energia_solar(self):
        """Solar panels should NOT match software."""
        ok, _ = self._match(
            "Contratação de empresa especializada para fornecimento e instalação de sistema de microgeração de energia solar fotovoltaica"
        )
        assert ok is False


class TestFacilitiesSector:
    """Tests for Facilities (Serviços de Zeladoria) sector."""

    def _match(self, texto):
        s = SECTORS["facilities"]
        return match_keywords(texto, s.keywords, s.exclusions)

    # TRUE POSITIVES - Should match facilities (zeladoria) contracts

    def test_matches_limpeza_conservacao_imoveis(self):
        """Real PNCP: Building cleaning and conservation."""
        ok, kw = self._match(
            "CONTRATAÇÃO DE EMPRESA PARA PRESTAÇÃO DE SERVIÇOS DE LIMPEZA, ASSEIO E CONSERVAÇÃO EM DIVERSAS SEDES DE PRÓPRIOS PÚBLICOS DE BARUERI"
        )
        assert ok is True

    def test_matches_limpeza_conservacao_imoveis_saae(self):
        """Real PNCP: Building cleaning services."""
        ok, _ = self._match("Contratação de empresa para limpeza e conservação dos imóveis da SAAE Atibaia.")
        assert ok is True

    def test_matches_facilities_english_term(self):
        ok, kw = self._match(
            "Contratação de empresa para prestação de serviços de facilities management incluindo limpeza e segurança"
        )
        assert ok is True
        assert "facilities" in kw

    def test_matches_servicos_prediais(self):
        ok, kw = self._match(
            "Registro de preços para eventual contratação de serviços prediais para conservação de edifícios públicos"
        )
        assert ok is True

    def test_matches_portaria_recepcao(self):
        ok, _ = self._match(
            "Contratação de empresa para prestação de serviços de portaria, recepção e controle de acesso"
        )
        assert ok is True

    def test_matches_zeladoria(self):
        ok, _ = self._match("Contratação de serviços de zeladoria para os prédios da prefeitura")
        assert ok is True

    def test_matches_terceirizacao(self):
        ok, _ = self._match(
            "Contratação de empresa para terceirização de mão de obra para serviços de copeira e recepcionista"
        )
        assert ok is True

    def test_matches_jardinagem(self):
        ok, _ = self._match("Contratação de serviços de jardinagem e paisagismo para as áreas verdes do campus")
        assert ok is True

    # FALSE POSITIVES - Should NOT match

    def test_excludes_manutencao_veiculos(self):
        ok, _ = self._match(
            "AQUISIÇÃO DE TINTAS AUTOMOTIVAS PADRONIZADAS E DE INSUMOS DE PINTURA PARA A MANUTENÇÃO DA FROTA DO MUNICÍPIO"
        )
        assert ok is False

    def test_excludes_iluminacao_publica(self):
        ok, _ = self._match(
            "REGISTRO DE PREÇO para eventual contratação de empresa(s) especializada(s) para o fornecimento de "
            "materiais elétricos, referentes a manutenção da iluminação pública"
        )
        assert ok is False

    def test_excludes_construcao_reforma(self):
        ok, _ = self._match(
            "Contratação de empresa para execução de obra de reforma e ampliação do prédio da secretaria municipal"
        )
        assert ok is False

    def test_excludes_medicamento(self):
        ok, _ = self._match(
            "REGISTRO DE PREÇOS do medicamento USTEQUINUMABE 90 mg, para assegurar a manutenção da assistência farmacêutica"
        )
        assert ok is False

    def test_excludes_manutencao_animais(self):
        ok, _ = self._match(
            "PRESTAÇÃO DE SERVIÇOS DE RECOLHIMENTO, GUARDA E MANUTENÇÃO DE ANIMAIS DE MÉDIO E GRANDE PORTE"
        )
        assert ok is False

    def test_excludes_software_facilities(self):
        ok, _ = self._match(
            "Contratação de empresa para fornecimento de software de gestão de facilities"
        )
        assert ok is False

    def test_excludes_jardinagem_publica(self):
        """Public urban gardening should NOT match (belongs in engenharia/public works)."""
        ok, _ = self._match(
            "Contratação de serviços de jardinagem pública para praças e canteiros centrais"
        )
        assert ok is False


class TestManutencaoPredialSector:
    """Tests for Manutenção Predial sector."""

    def _match(self, texto):
        s = SECTORS["manutencao_predial"]
        return match_keywords(texto, s.keywords, s.exclusions)

    # TRUE POSITIVES

    def test_matches_manutencao_predial(self):
        ok, kw = self._match(
            "Contratação empresa especializada na prestação de serviços contínuos de manutenção predial, "
            "abrangendo a execução de rotinas preventivas e corretivas"
        )
        assert ok is True

    def test_matches_unidades_residenciais(self):
        ok, kw = self._match("Serviço de Manutenção de unidades residenciais do CRUSP.")
        assert ok is True

    def test_matches_elevadores(self):
        ok, kw = self._match(
            "Contratação de empresa especializada em manutenção preventiva e corretiva dos elevadores da Superintendência Regional"
        )
        assert ok is True

    def test_matches_ar_condicionado_pmoc(self):
        ok, _ = self._match(
            "Serviço de manutenção preventiva e corretiva em ar condicionado, cortinas de ar, "
            "purificadores de água e execução do Plano de Manutenção, Operação e Controle (PMOC)"
        )
        assert ok is True

    def test_matches_instalacoes_eletricas(self):
        ok, _ = self._match(
            "Prestação de Serviço de Manutenção e Conservação de Instalações Elétricas, para atender à demanda da UNESP"
        )
        assert ok is True

    def test_matches_impermeabilizacao(self):
        ok, _ = self._match("Contratação de serviços de impermeabilização predial para a sede do tribunal")
        assert ok is True

    def test_matches_pintura_predial(self):
        ok, _ = self._match("Contratação de serviços de pintura predial para os prédios da universidade")
        assert ok is True

    def test_matches_grupo_gerador(self):
        ok, _ = self._match("Manutenção preventiva e corretiva de grupo gerador da sede administrativa")
        assert ok is True

    # FALSE POSITIVES - Should NOT match

    def test_excludes_manutencao_veiculos(self):
        ok, _ = self._match("Manutenção preventiva e corretiva da frota de veículos oficiais do município")
        assert ok is False

    def test_excludes_manutencao_estradas(self):
        ok, _ = self._match("Manutenção de estradas vicinais e rodovias municipais")
        assert ok is False

    def test_excludes_manutencao_servidor_ti(self):
        ok, _ = self._match("Manutenção preventiva e corretiva de servidor de dados do datacenter")
        assert ok is False

    def test_excludes_manutencao_tratores(self):
        ok, _ = self._match("Manutenção de tratores e implementos agrícolas da secretaria de agricultura")
        assert ok is False

    def test_excludes_construcao_civil(self):
        ok, _ = self._match("Construção civil de novo prédio da secretaria de saúde")
        assert ok is False

    def test_excludes_medicamento(self):
        ok, _ = self._match("REGISTRO DE PREÇOS do medicamento para manutenção de tratamento oncológico")
        assert ok is False

    # NORMALIZATION TESTS

    def test_normalization_accents(self):
        ok1, _ = self._match("Manutenção predial")
        ok2, _ = self._match("MANUTENÇÃO PREDIAL")
        assert ok1 is True
        assert ok2 is True

    def test_normalization_case_insensitive(self):
        ok1, _ = self._match("AR CONDICIONADO")
        ok2, _ = self._match("ar condicionado")
        assert ok1 is True
        assert ok2 is True
