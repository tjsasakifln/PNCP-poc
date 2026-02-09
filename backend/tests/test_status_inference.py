"""
Tests for status inference layer (status_inference.py).

This module tests the intelligent status inference based on dates,
values, and textual situation fields from PNCP API.
"""

from datetime import datetime, timedelta
from status_inference import inferir_status_licitacao, enriquecer_com_status_inferido


class TestInferirStatusLicitacao:
    """Tests for inferir_status_licitacao() function."""

    def test_encerrada_por_homologacao(self):
        """Licitação com valor homologado deve ser inferida como 'encerrada'."""
        lic = {
            "valorTotalHomologado": 100000.0,
            "dataEncerramentoProposta": "2025-01-01T10:00:00",
        }
        assert inferir_status_licitacao(lic) == "encerrada"

    def test_encerrada_por_situacao_textual(self):
        """Situação textual de finalização indica 'encerrada'."""
        situacoes_finalizadas = [
            "Homologada",
            "Adjudicada",
            "Anulada",
            "Revogada",
            "Fracassada",
            "Deserta",
            "Suspensa",
        ]

        for situacao in situacoes_finalizadas:
            lic = {"situacaoCompraNome": situacao}
            result = inferir_status_licitacao(lic)
            assert result == "encerrada", f"Situação '{situacao}' deveria ser 'encerrada'"

    def test_recebendo_proposta_intervalo_datas(self):
        """Licitação aberta (entre data_abertura e data_encerramento)."""
        agora = datetime.now()
        abertura = (agora - timedelta(days=1)).isoformat()  # Abriu ontem
        encerramento = (agora + timedelta(days=7)).isoformat()  # Fecha daqui 7 dias

        lic = {
            "dataAberturaProposta": abertura,
            "dataEncerramentoProposta": encerramento,
            "valorTotalHomologado": None,
        }

        assert inferir_status_licitacao(lic) == "recebendo_proposta"

    def test_recebendo_proposta_aguardando_abertura(self):
        """Licitação que ainda não abriu (data_atual < data_abertura)."""
        agora = datetime.now()
        abertura = (agora + timedelta(days=2)).isoformat()  # Abre daqui 2 dias
        encerramento = (agora + timedelta(days=10)).isoformat()

        lic = {
            "dataAberturaProposta": abertura,
            "dataEncerramentoProposta": encerramento,
        }

        # Aguardando abertura ainda é considerado "recebendo_proposta"
        # (usuário quer ver oportunidades futuras)
        assert inferir_status_licitacao(lic) == "recebendo_proposta"

    def test_em_julgamento_por_data_encerrada(self):
        """Prazo encerrado mas sem homologação → em_julgamento."""
        agora = datetime.now()
        abertura = (agora - timedelta(days=30)).isoformat()
        encerramento = (agora - timedelta(days=7)).isoformat()  # Encerrou há 7 dias

        lic = {
            "dataAberturaProposta": abertura,
            "dataEncerramentoProposta": encerramento,
            "valorTotalHomologado": None,
        }

        assert inferir_status_licitacao(lic) == "em_julgamento"

    def test_em_julgamento_por_situacao_textual(self):
        """Situação textual de julgamento indica 'em_julgamento'."""
        situacoes_julgamento = [
            "Em julgamento",
            "Análise",
            "Classificação",
            "Habilitação",
            "Propostas encerradas",
        ]

        for situacao in situacoes_julgamento:
            lic = {"situacaoCompraNome": situacao}
            result = inferir_status_licitacao(lic)
            assert result == "em_julgamento", f"Situação '{situacao}' deveria ser 'em_julgamento'"

    def test_recebendo_proposta_por_situacao_textual(self):
        """Situação textual de abertura indica 'recebendo_proposta'."""
        situacoes_abertas = [
            "Aberta",
            "Recebendo propostas",
            "Vigente",
        ]

        for situacao in situacoes_abertas:
            lic = {"situacaoCompraNome": situacao}
            result = inferir_status_licitacao(lic)
            assert result == "recebendo_proposta", f"Situação '{situacao}' deveria ser 'recebendo_proposta'"

    def test_divulgada_publicada_nao_sao_recebendo_proposta(self):
        """'Divulgada no PNCP' e 'Publicada' NÃO indicam 'recebendo_proposta'.

        Estes termos significam apenas que a licitação foi publicada no portal.
        Sem informações de data, não é possível determinar se está aberta.
        Devem cair no fallback ('todos') para não exibir licitações fechadas
        como abertas.
        """
        situacoes_ambiguas = [
            "Divulgada no PNCP",
            "Publicada",
        ]

        for situacao in situacoes_ambiguas:
            lic = {"situacaoCompraNome": situacao}
            result = inferir_status_licitacao(lic)
            assert result == "todos", (
                f"Situação '{situacao}' deveria ser 'todos' (indeterminado), "
                f"não '{result}'. 'Divulgada' não prova que está recebendo propostas."
            )

    def test_fallback_dados_insuficientes(self):
        """Sem dados suficientes → retorna 'todos' (não filtra)."""
        lic = {}  # Licitação vazia
        assert inferir_status_licitacao(lic) == "todos"

        lic_minima = {"objetoCompra": "Aquisição de uniformes"}
        assert inferir_status_licitacao(lic_minima) == "todos"

    def test_data_invalida_fallback(self):
        """Datas inválidas não quebram a inferência."""
        lic = {
            "dataAberturaProposta": "INVALID_DATE",
            "dataEncerramentoProposta": "NOT_A_DATE",
            "situacaoCompraNome": "Divulgada",
        }

        # "Divulgada" não é mais classificada como "recebendo_proposta"
        # (apenas indica publicação, não abertura). Com datas inválidas,
        # cai no fallback "todos".
        assert inferir_status_licitacao(lic) == "todos"

    def test_prioridade_homologacao_sobre_datas(self):
        """Valor homologado tem prioridade sobre datas (sempre encerrada)."""
        agora = datetime.now()
        encerramento_futuro = (agora + timedelta(days=7)).isoformat()

        lic = {
            "dataEncerramentoProposta": encerramento_futuro,  # Futuro
            "valorTotalHomologado": 50000.0,  # Mas já homologada
        }

        # Homologação tem prioridade
        assert inferir_status_licitacao(lic) == "encerrada"

    def test_fallback_publicacao_antiga_com_prazo_futuro(self):
        """Publicação >90 dias atrás com prazo futuro deve ser em_julgamento."""
        agora = datetime.now()
        encerramento_futuro = (agora + timedelta(days=30)).isoformat()
        publicacao_antiga = (agora - timedelta(days=120)).isoformat()

        lic = {
            "dataEncerramentoProposta": encerramento_futuro,
            "dataPublicacaoPncp": publicacao_antiga,
            "valorTotalHomologado": None,
        }

        assert inferir_status_licitacao(lic) == "em_julgamento"

    def test_fallback_publicacao_recente_com_prazo_futuro(self):
        """Publicação recente com prazo futuro deve ser recebendo_proposta."""
        agora = datetime.now()
        encerramento_futuro = (agora + timedelta(days=30)).isoformat()
        publicacao_recente = (agora - timedelta(days=10)).isoformat()

        lic = {
            "dataEncerramentoProposta": encerramento_futuro,
            "dataPublicacaoPncp": publicacao_recente,
            "valorTotalHomologado": None,
        }

        assert inferir_status_licitacao(lic) == "recebendo_proposta"

    def test_fallback_sem_publicacao_com_prazo_futuro(self):
        """Sem data de publicação, prazo futuro → recebendo_proposta (conservador)."""
        agora = datetime.now()
        encerramento_futuro = (agora + timedelta(days=30)).isoformat()

        lic = {
            "dataEncerramentoProposta": encerramento_futuro,
            "valorTotalHomologado": None,
        }

        assert inferir_status_licitacao(lic) == "recebendo_proposta"


class TestEnriquecerComStatusInferido:
    """Tests for enriquecer_com_status_inferido() function."""

    def test_adiciona_campo_status_inferido(self):
        """Função deve adicionar campo '_status_inferido' a cada licitação."""
        lics = [
            {"valorTotalHomologado": 100000},
            {"dataEncerramentoProposta": (datetime.now() + timedelta(days=7)).isoformat()},
            {"situacaoCompraNome": "Em julgamento"},
        ]

        result = enriquecer_com_status_inferido(lics)

        # Verifica que o campo foi adicionado
        assert all("_status_inferido" in lic for lic in result)

        # Verifica valores esperados
        assert result[0]["_status_inferido"] == "encerrada"
        assert result[1]["_status_inferido"] == "recebendo_proposta"
        assert result[2]["_status_inferido"] == "em_julgamento"

    def test_modifica_lista_in_place(self):
        """Função modifica a lista original (in-place)."""
        lics = [{"valorTotalHomologado": 100000}]
        original_id = id(lics[0])

        enriquecer_com_status_inferido(lics)

        # Mesmo objeto foi modificado
        assert id(lics[0]) == original_id
        assert "_status_inferido" in lics[0]

    def test_lista_vazia(self):
        """Lista vazia não causa erro."""
        result = enriquecer_com_status_inferido([])
        assert result == []

    def test_multiplas_licitacoes(self):
        """Processa múltiplas licitações corretamente."""
        agora = datetime.now()

        lics = [
            # 10 licitações abertas
            *[
                {
                    "dataAberturaProposta": (agora - timedelta(days=1)).isoformat(),
                    "dataEncerramentoProposta": (agora + timedelta(days=i)).isoformat(),
                }
                for i in range(1, 11)
            ],
            # 5 licitações em julgamento
            *[
                {
                    "dataEncerramentoProposta": (agora - timedelta(days=i)).isoformat(),
                }
                for i in range(1, 6)
            ],
            # 3 licitações encerradas
            *[{"valorTotalHomologado": 100000 + i} for i in range(3)],
        ]

        result = enriquecer_com_status_inferido(lics)

        # Conta por status
        status_count = {}
        for lic in result:
            status = lic["_status_inferido"]
            status_count[status] = status_count.get(status, 0) + 1

        assert status_count.get("recebendo_proposta", 0) == 10
        assert status_count.get("em_julgamento", 0) == 5
        assert status_count.get("encerrada", 0) == 3
