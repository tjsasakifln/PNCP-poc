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
        assert ids == {"vestuario", "alimentos", "informatica", "mobiliario", "papelaria", "engenharia", "software", "facilities", "saude", "vigilancia", "transporte", "manutencao_predial", "engenharia_rodoviaria", "materiais_eletricos", "materiais_hidraulicos"}

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
        """Now matches via 'sondagem geotécnica' compound keyword (standalone 'obras' removed)."""
        ok, _ = self._match(
            "CONTRATAÇÃO DE EMPRESA PARA PRESTAÇÃO DE SERVIÇOS DE SONDAGEM GEOTÉCNICA — Secretaria de Obras"
        )
        assert ok is True

    def test_allows_mao_de_obra_civil(self):
        """Now matches via 'material e mão de obra' compound (standalone 'obra' removed).

        Audit 2026-02-08: Standalone 'obra'/'obras' removed to eliminate ~12 FPs
        from 'mão de obra' in staffing contexts. Compound forms preserve legitimate matches.
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


class TestSaudeSector:
    """Tests for Saúde (health) sector."""

    def _match(self, objeto: str):
        s = get_sector("saude")
        return match_keywords(objeto, s.keywords, s.exclusions)

    # TRUE POSITIVES
    def test_matches_medicamentos(self):
        ok, _ = self._match("Aquisição de medicamentos para atender a rede municipal de saúde")
        assert ok is True

    def test_matches_material_medico_hospitalar(self):
        ok, _ = self._match("Registro de preço para aquisição de material médico-hospitalar")
        assert ok is True

    def test_matches_equipamento_hospitalar(self):
        ok, _ = self._match("Aquisição de equipamentos hospitalares para o Hospital Municipal")
        assert ok is True

    def test_matches_insumos_hospitalares(self):
        ok, _ = self._match("Aquisição de insumos hospitalares para uso dos pacientes admitidos no SAD")
        assert ok is True

    def test_matches_seringas_agulhas(self):
        ok, _ = self._match("Registro de preços para aquisição de seringas e agulhas descartáveis")
        assert ok is True

    def test_matches_opme(self):
        ok, _ = self._match("Aquisição de OPME - órteses, próteses e materiais especiais")
        assert ok is True

    def test_matches_reagentes_laboratorio(self):
        ok, _ = self._match("Registro de preços para aquisição de reagentes de laboratório")
        assert ok is True

    def test_matches_oxigenio_medicinal(self):
        ok, _ = self._match("Contratação de fornecimento de oxigênio medicinal e gases medicinais")
        assert ok is True

    def test_matches_material_odontologico(self):
        ok, _ = self._match("Aquisição de material odontológico para as UBS")
        assert ok is True

    # FALSE POSITIVES (should be excluded)
    def test_matches_secretaria_saude_with_medical_object(self):
        """Secretaria de Saúde in description should NOT block medical procurement."""
        ok, _ = self._match("Aquisição de gases medicinais para a Secretaria de Saúde")
        assert ok is True

    def test_excludes_plano_de_saude(self):
        ok, _ = self._match("Contratação de plano de saúde para servidores municipais")
        assert ok is False

    def test_matches_dipirona(self):
        ok, _ = self._match("Registro de preços para fornecimento de dipirona sódica solução injetável")
        assert ok is True

    def test_matches_tela_cirurgica(self):
        ok, _ = self._match("Fornecimento de telas cirúrgicas não absorvíveis para Hospital Municipal")
        assert ok is True

    def test_matches_fisioterapia(self):
        ok, _ = self._match("Prestação de serviço de fisioterapia clínica e domiciliar")
        assert ok is True

    def test_matches_telemedicina(self):
        ok, _ = self._match("Prestação de serviços de telemedicina cardiológica 24 horas")
        assert ok is True

    def test_matches_instrumental_cirurgico(self):
        ok, _ = self._match("Instrumentais em Titânio para Cirurgia Cardíaca")
        assert ok is True

    def test_matches_bipap(self):
        ok, _ = self._match("Aquisição de aparelho bipap em cumprimento de determinação judicial")
        assert ok is True

    def test_matches_colostomia(self):
        ok, _ = self._match("Aquisição de Material de Consumo (Bolsa de Colostomia/Ileostomia)")
        assert ok is True

    def test_matches_tubo_coletor_sangue(self):
        ok, _ = self._match("Aquisição de tubos coletores de sangue para o Hospital Metropolitano")
        assert ok is True

    def test_excludes_plotagem_hospital(self):
        """Plotagem for hospital is graphic services, not medical."""
        ok, _ = self._match("Confecção de plotagens e painéis para atender a demanda do Hospital Municipal")
        assert ok is False

    def test_excludes_agulha_costura(self):
        ok, _ = self._match("Aquisição de agulhas de costura e linhas para oficina de costura")
        assert ok is False

    def test_excludes_lamina_serra(self):
        ok, _ = self._match("Aquisição de lâminas de serra para marcenaria")
        assert ok is False

    def test_excludes_vigilancia_sanitaria(self):
        ok, _ = self._match("Serviços de vigilância sanitária e fiscalização")
        assert ok is False


class TestVigilanciaSector:
    """Tests for Vigilância e Segurança sector."""

    def _match(self, objeto: str):
        s = get_sector("vigilancia")
        return match_keywords(objeto, s.keywords, s.exclusions)

    # TRUE POSITIVES
    def test_matches_vigilancia_patrimonial(self):
        ok, _ = self._match("Contratação de empresa de vigilância patrimonial armada e desarmada")
        assert ok is True

    def test_matches_cftv(self):
        ok, _ = self._match("Implantação de sistema de CFTV com câmeras de monitoramento")
        assert ok is True

    def test_matches_alarme_monitoramento(self):
        ok, _ = self._match("Prestação de serviços de monitoramento eletrônico com sistema de alarme")
        assert ok is True

    def test_matches_controle_acesso(self):
        ok, _ = self._match("Aquisição e instalação de sistema de controle de acesso com catracas")
        assert ok is True

    def test_matches_seguranca_eletronica(self):
        ok, _ = self._match("Contratação de serviços de segurança eletrônica e videomonitoramento")
        assert ok is True

    def test_matches_vigilante_armado(self):
        ok, _ = self._match("Contratação de postos de vigilante armado 24 horas")
        assert ok is True

    # FALSE POSITIVES (should be excluded)
    def test_excludes_vigilancia_sanitaria(self):
        ok, _ = self._match("Ações de vigilância sanitária para fiscalização de alimentos")
        assert ok is False

    def test_excludes_vigilancia_epidemiologica(self):
        ok, _ = self._match("Serviços de vigilância epidemiológica e controle de doenças")
        assert ok is False

    def test_excludes_seguranca_trabalho(self):
        ok, _ = self._match("Contratação de serviços de segurança do trabalho e medicina ocupacional")
        assert ok is False

    def test_excludes_seguranca_informacao(self):
        ok, _ = self._match("Consultoria em segurança da informação e segurança cibernética")
        assert ok is False

    def test_excludes_monitoramento_ambiental(self):
        ok, _ = self._match("Serviços de monitoramento ambiental e controle de poluição")
        assert ok is False


class TestTransporteSector:
    """Tests for Transporte e Veículos sector."""

    def _match(self, objeto: str):
        s = get_sector("transporte")
        return match_keywords(objeto, s.keywords, s.exclusions)

    # TRUE POSITIVES
    def test_matches_locacao_veiculos(self):
        ok, _ = self._match("Locação de veículos com motorista para a Secretaria de Educação")
        assert ok is True

    def test_matches_combustivel(self):
        ok, _ = self._match("Registro de preços para aquisição de combustível (gasolina e diesel)")
        assert ok is True

    def test_matches_manutencao_frota(self):
        ok, _ = self._match("Contratação de serviços de manutenção preventiva e corretiva da frota municipal")
        assert ok is True

    def test_matches_pneus(self):
        ok, _ = self._match("Registro de preços para aquisição de pneus para a frota de veículos")
        assert ok is True

    def test_matches_transporte_escolar(self):
        ok, _ = self._match("Contratação de serviços de transporte escolar para alunos da rede municipal")
        assert ok is True

    def test_matches_aquisicao_veiculos(self):
        ok, _ = self._match("Aquisição de veículos zero km tipo caminhonete para a Secretaria de Obras")
        assert ok is True

    def test_matches_ambulancia(self):
        ok, _ = self._match("Aquisição de ambulância tipo D para o SAMU")
        assert ok is True

    # FALSE POSITIVES (should be excluded)
    def test_excludes_veiculo_comunicacao(self):
        ok, _ = self._match("Contratação de veículo de comunicação para publicidade institucional")
        assert ok is False

    def test_excludes_mecanica_solos(self):
        ok, _ = self._match("Serviços de mecânica dos solos e sondagem geotécnica")
        assert ok is False

    def test_excludes_ventilador_mecanico(self):
        ok, _ = self._match("Aquisição de ventilador mecânico para UTI neonatal")
        assert ok is False

    def test_excludes_filtro_agua(self):
        ok, _ = self._match("Aquisição de filtro de água para bebedouros")
        assert ok is False

    def test_excludes_bateria_notebook(self):
        ok, _ = self._match("Substituição de bateria de notebook Dell Latitude")
        assert ok is False


class TestEngenhariaRC1ObraFix:
    """RC1 fix: standalone 'obra'/'obras' removed — no more 'mão de obra' false positives."""

    def _match(self, texto):
        s = SECTORS["engenharia"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_excludes_mao_de_obra_limpeza(self):
        """Cleaning staffing mentioning 'mão de obra' should NOT match engineering."""
        ok, _ = self._match(
            "Contratação de empresa para prestação de serviços de mão de obra terceirizada de limpeza"
        )
        assert ok is False

    def test_excludes_mao_de_obra_vigilancia(self):
        """Security staffing mentioning 'mão de obra' should NOT match engineering."""
        ok, _ = self._match(
            "Contratação de mão de obra para serviços de vigilância patrimonial"
        )
        assert ok is False

    def test_excludes_mao_de_obra_ti(self):
        """IT staffing mentioning 'mão de obra' should NOT match engineering."""
        ok, _ = self._match(
            "Prestação de serviços de mão de obra especializada em tecnologia da informação"
        )
        assert ok is False

    def test_excludes_mao_de_obra_radiologia(self):
        """Radiology staffing mentioning 'mão de obra' should NOT match engineering."""
        ok, _ = self._match(
            "Contratação de mão de obra para serviços de radiologia e diagnóstico por imagem"
        )
        assert ok is False

    def test_still_matches_material_e_mao_de_obra(self):
        """Civil works with 'material e mão de obra' should still match via compound."""
        ok, _ = self._match(
            "Contratação com fornecimento de material e mão de obra para reforma de escola"
        )
        assert ok is True

    def test_still_matches_execucao_de_obra(self):
        """'execução de obra' compound should still match."""
        ok, _ = self._match(
            "Contratação de empresa para execução de obra de ampliação do hospital"
        )
        assert ok is True

    def test_still_matches_obra_publica(self):
        """'obra pública' compound should match."""
        ok, _ = self._match(
            "Fiscalização e supervisão de obra pública de saneamento básico"
        )
        assert ok is True

    def test_still_matches_obra_de_infraestrutura(self):
        """'obra de infraestrutura' compound should still match."""
        ok, _ = self._match(
            "Contratação de empresa para execução de obra de infraestrutura viária"
        )
        assert ok is True


class TestEngenhariaRC2AcFix:
    """RC2 fix: 'ar condicionado'/'climatização' removed from engenharia (belongs in manutencao_predial)."""

    def _eng_match(self, texto):
        s = SECTORS["engenharia"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def _mp_match(self, texto):
        s = SECTORS["manutencao_predial"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_engenharia_excludes_ar_condicionado(self):
        """AC equipment purchase should NOT match engineering sector."""
        ok, _ = self._eng_match(
            "Aquisição de aparelhos de ar condicionado tipo split para as unidades de saúde"
        )
        assert ok is False

    def test_engenharia_excludes_climatizacao(self):
        """HVAC service should NOT match engineering sector."""
        ok, _ = self._eng_match(
            "Contratação de serviços de climatização para o auditório municipal"
        )
        assert ok is False

    def test_manutencao_predial_still_matches_ac(self):
        """AC should still match manutencao_predial sector."""
        ok, _ = self._mp_match(
            "Aquisição de aparelhos de ar condicionado tipo split para as unidades de saúde"
        )
        assert ok is True

    def test_manutencao_predial_still_matches_climatizacao(self):
        """HVAC should still match manutencao_predial sector."""
        ok, _ = self._mp_match(
            "Contratação de serviços de climatização para o auditório municipal"
        )
        assert ok is True


class TestEngenhariaRC3GenericFix:
    """RC3 fix: generic standalone terms removed — 'infraestrutura', 'cobertura', 'restauração'."""

    def _match(self, texto):
        s = SECTORS["engenharia"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_excludes_infraestrutura_department(self):
        """Department name containing 'infraestrutura' should NOT match."""
        ok, _ = self._match(
            "Aquisição de materiais de expediente para a Diretoria de Infraestrutura"
        )
        assert ok is False

    def test_excludes_cobertura_jornalistica(self):
        """Media/journalism coverage should NOT match engineering."""
        ok, _ = self._match(
            "Contratação de serviços de cobertura jornalística para eventos oficiais"
        )
        assert ok is False

    def test_excludes_restauracao_documentos(self):
        """Document/archive restoration should NOT match engineering."""
        ok, _ = self._match(
            "Contratação de serviços de restauração de arquivo e digitalização de documentos"
        )
        assert ok is False

    def test_still_matches_cobertura_metalica(self):
        """Metal roofing (construction) should still match via compound."""
        ok, _ = self._match(
            "Contratação de empresa para instalação de cobertura metálica na quadra poliesportiva"
        )
        assert ok is True

    def test_still_matches_restauracao_edificio(self):
        """Building restoration should still match via compound."""
        ok, _ = self._match(
            "Contratação de empresa para restauração de edifício tombado pelo patrimônio histórico"
        )
        assert ok is True

    def test_still_matches_sondagem_geotecnica(self):
        """Geotechnical survey should still match via compound."""
        ok, _ = self._match(
            "Contratação de empresa para sondagem geotécnica do terreno da nova escola"
        )
        assert ok is True

    def test_still_matches_pavimentacao(self):
        """Paving should still match (unchanged keyword)."""
        ok, _ = self._match(
            "Contratação de empresa para pavimentação asfáltica de vias urbanas"
        )
        assert ok is True


class TestFacilitiesPortariaExclusions:
    """Tests for facilities sector portaria/recepção exclusions."""

    def _match(self, texto):
        s = SECTORS["facilities"]
        return match_keywords(texto, s.keywords, s.exclusions)

    def test_excludes_portaria_ministerial(self):
        """Administrative decree should NOT match facilities."""
        ok, _ = self._match(
            "Publicação de portaria ministerial regulamentando o uso de recursos federais"
        )
        assert ok is False

    def test_excludes_portaria_normativa(self):
        """Regulatory decree should NOT match facilities."""
        ok, _ = self._match(
            "Atendimento à portaria normativa sobre gestão de contratos administrativos"
        )
        assert ok is False

    def test_still_matches_servico_portaria(self):
        """Building reception/doorman service should still match."""
        ok, _ = self._match(
            "Contratação de empresa para prestação de serviços de portaria e recepção para o prédio sede"
        )
        assert ok is True


# ============================================================
# STORY-242: New Sectors — Engenharia Rodoviária, Materiais Elétricos, Materiais Hidráulicos
# ============================================================


class TestNewSectorsLoaded:
    """AC5: Verify all 3 new sectors exist in SECTORS dict."""

    def test_engenharia_rodoviaria_exists(self):
        s = get_sector("engenharia_rodoviaria")
        assert s.id == "engenharia_rodoviaria"
        assert s.name == "Engenharia Rodoviária e Infraestrutura Viária"
        assert len(s.keywords) >= 30
        assert len(s.exclusions) >= 15

    def test_materiais_eletricos_exists(self):
        s = get_sector("materiais_eletricos")
        assert s.id == "materiais_eletricos"
        assert s.name == "Materiais Elétricos e Instalações"
        assert s.max_contract_value == 20_000_000
        assert len(s.keywords) >= 25
        assert len(s.exclusions) >= 10

    def test_materiais_hidraulicos_exists(self):
        s = get_sector("materiais_hidraulicos")
        assert s.id == "materiais_hidraulicos"
        assert s.name == "Materiais Hidráulicos e Saneamento"
        assert s.max_contract_value == 30_000_000
        assert len(s.keywords) >= 25
        assert len(s.exclusions) >= 10

    def test_list_sectors_includes_new(self):
        sectors = list_sectors()
        ids = {s["id"] for s in sectors}
        assert "engenharia_rodoviaria" in ids
        assert "materiais_eletricos" in ids
        assert "materiais_hidraulicos" in ids
        assert len(sectors) >= 15  # 12 existing + 3 new


class TestEngenhariaRodoviariaSector:
    """AC6: Filter tests for engenharia_rodoviaria sector."""

    def _match(self, texto):
        s = SECTORS["engenharia_rodoviaria"]
        return match_keywords(texto, s.keywords, s.exclusions)

    # True positives
    def test_matches_pavimentacao_asfaltica(self):
        ok, kw = self._match("Contratação de empresa para pavimentação asfáltica da rodovia BR-101")
        assert ok is True

    def test_matches_recapeamento(self):
        ok, kw = self._match("Serviço de recapeamento asfáltico em vias urbanas do município")
        assert ok is True

    def test_matches_sinalizacao_viaria(self):
        ok, kw = self._match("Aquisição de materiais para sinalização viária horizontal e vertical")
        assert ok is True

    def test_matches_conservacao_rodoviaria(self):
        ok, kw = self._match("Contrato de conservação rodoviária preventiva no trecho sul")
        assert ok is True

    def test_matches_defensas_metalicas(self):
        ok, kw = self._match("Fornecimento e instalação de defensas metálicas em rodovias estaduais")
        assert ok is True

    def test_matches_viaduto(self):
        ok, kw = self._match("Construção de viaduto sobre a BR-116 no km 52")
        assert ok is True

    def test_matches_tapa_buraco(self):
        ok, kw = self._match("Operação tapa-buraco em vias municipais danificadas")
        assert ok is True

    def test_matches_fresagem(self):
        ok, kw = self._match("Serviço de fresagem de pavimento asfáltico deteriorado")
        assert ok is True

    # False positives (exclusions)
    def test_excludes_terminal_rodoviario(self):
        ok, _ = self._match("Reforma do terminal rodoviário central para passageiros")
        assert ok is False

    def test_excludes_engenharia_software(self):
        ok, _ = self._match("Contratação de serviço de engenharia de software para sistemas")
        assert ok is False

    def test_excludes_passagem_rodoviaria(self):
        ok, _ = self._match("Aquisição de passagem rodoviária para servidores em viagem")
        assert ok is False

    def test_excludes_tunnel_vpn(self):
        ok, _ = self._match("Configuração de túnel VPN para acesso remoto seguro")
        assert ok is False


class TestMateriaisEletricosSector:
    """AC6: Filter tests for materiais_eletricos sector."""

    def _match(self, texto):
        s = SECTORS["materiais_eletricos"]
        return match_keywords(texto, s.keywords, s.exclusions)

    # True positives
    def test_matches_disjuntores(self):
        ok, kw = self._match("Aquisição de disjuntores termomagnéticos para quadro de distribuição")
        assert ok is True

    def test_matches_cabo_eletrico(self):
        ok, kw = self._match("Fornecimento de cabo elétrico flexível 2,5mm para instalações")
        assert ok is True

    def test_matches_iluminacao_publica(self):
        ok, kw = self._match("Modernização da iluminação pública com tecnologia LED")
        assert ok is True

    def test_matches_transformador(self):
        ok, kw = self._match("Aquisição de transformador trifásico para subestação")
        assert ok is True

    def test_matches_eletroduto(self):
        ok, kw = self._match("Fornecimento de eletrodutos e conduletes para instalação predial")
        assert ok is True

    def test_matches_material_eletrico(self):
        ok, kw = self._match("Registro de preços para material elétrico diverso")
        assert ok is True

    # False positives (exclusions)
    def test_excludes_computadores(self):
        ok, _ = self._match("Aquisição de computadores e notebooks para o setor administrativo")
        assert ok is False

    def test_excludes_eletrodomesticos(self):
        ok, _ = self._match("Compra de eletrodomésticos para cozinha do refeitório")
        assert ok is False

    def test_excludes_veiculo_eletrico(self):
        ok, _ = self._match("Aquisição de veículo elétrico para transporte municipal")
        assert ok is False

    def test_excludes_guitarra_eletrica(self):
        ok, _ = self._match("Compra de guitarra elétrica para escola de música municipal")
        assert ok is False


class TestMateriaisHidraulicosSector:
    """AC6: Filter tests for materiais_hidraulicos sector."""

    def _match(self, texto):
        s = SECTORS["materiais_hidraulicos"]
        return match_keywords(texto, s.keywords, s.exclusions)

    # True positives
    def test_matches_tubo_pvc(self):
        ok, kw = self._match("Aquisição de tubo PVC para rede de distribuição de água")
        assert ok is True

    def test_matches_bomba_submersa(self):
        ok, kw = self._match("Fornecimento de bomba submersa para poço artesiano municipal")
        assert ok is True

    def test_matches_tratamento_agua(self):
        ok, kw = self._match("Contratação de empresa para tratamento de água na ETA central")
        assert ok is True

    def test_matches_material_hidraulico(self):
        ok, kw = self._match("Registro de preços para aquisição de material hidráulico")
        assert ok is True

    def test_matches_saneamento_basico(self):
        ok, kw = self._match("Obra de saneamento básico no distrito industrial")
        assert ok is True

    def test_matches_rede_coletora(self):
        ok, kw = self._match("Implantação de rede coletora de esgoto no bairro norte")
        assert ok is True

    def test_matches_fossa_septica(self):
        ok, kw = self._match("Instalação de fossa séptica em unidades habitacionais rurais")
        assert ok is True

    # False positives (exclusions)
    def test_excludes_prensa_hidraulica(self):
        ok, _ = self._match("Aquisição de prensa hidráulica para oficina mecânica industrial")
        assert ok is False

    def test_excludes_macaco_hidraulico(self):
        ok, _ = self._match("Compra de macaco hidráulico para manutenção de veículos")
        assert ok is False

    def test_excludes_direcao_hidraulica(self):
        ok, _ = self._match("Reparo de direção hidráulica de veículo da frota municipal")
        assert ok is False

    def test_excludes_escavadeira_hidraulica(self):
        ok, _ = self._match("Locação de escavadeira hidráulica para obra de terraplanagem")
        assert ok is False
