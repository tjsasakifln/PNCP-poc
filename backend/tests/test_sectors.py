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
        assert ids == {"vestuario", "alimentos", "informatica", "mobiliario", "papelaria", "engenharia", "software", "facilities", "saude", "vigilancia", "transporte", "manutencao_predial"}

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
