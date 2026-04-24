"""
Testes do fluxo de busca — fluxo principal do SmartLic.

Hard asserts: busca retorna resultado ou estado vazio em tempo limite.
Soft insights: performance, UX de progresso, descoberta de download.

Requer: ADMIN_PASSWORD configurado (usa logged_in_driver).
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.buscar_page import BuscarPage


@pytest.mark.search
class TestBuscarFlow:
    def test_page_loads_for_authenticated_user(self, logged_in_driver, collector, base_url):
        page = BuscarPage(logged_in_driver, base_url)
        load_time = page.navigate_to()

        collector.metric("buscar_page_load_seconds", round(load_time, 2))
        if load_time > 3:
            collector.warn("PERF", f"/buscar carregou em {load_time:.1f}s — página principal do produto")

        assert not page.page_has_error() if hasattr(page, "page_has_error") else True
        assert page.is_element_present(
            By.CSS_SELECTOR, "button[type='submit']"
        ), "/buscar: botão de busca ausente após autenticação"

    def test_sector_dropdown_has_expected_options(self, logged_in_driver, collector, base_url):
        """Deve ter os 15 setores configurados em sectors_data.yaml."""
        page = BuscarPage(logged_in_driver, base_url)
        page.navigate_to()

        count = page.get_sector_options_count()
        collector.metric("sector_dropdown_count", count)

        if count == 0:
            collector.warn("UX", "Dropdown de setores vazio ou não abriu — impossível determinar contagem")
        elif count < 15:
            collector.warn(
                "CONTENT",
                f"Dropdown mostra {count} setores mas o sistema tem 15 definidos em sectors_data.yaml. "
                "Possível setor faltando no frontend.",
            )
        elif count > 15:
            collector.warn(
                "CONTENT",
                f"Dropdown mostra {count} setores (esperado 15) — verificar duplicatas ou setor extra.",
            )

    def test_uf_selector_opens_and_has_states(self, logged_in_driver, collector, base_url):
        """Seletor de UFs deve ter todos os 27 estados disponíveis."""
        page = BuscarPage(logged_in_driver, base_url)
        page.navigate_to()
        page.open_filter_panel()

        try:
            container = page.wait_for_element(
                By.CSS_SELECTOR, "[data-tour='uf-selector']", timeout=8
            )
            uf_buttons = container.find_elements(By.TAG_NAME, "button")
            # Filtrar botões de ação (Selecionar todos, Limpar)
            state_buttons = [
                btn for btn in uf_buttons
                if len(btn.text.strip()) == 2 and btn.text.strip().isupper()
            ]
            count = len(state_buttons)
            collector.metric("uf_selector_state_count", count)

            if count < 27:
                collector.warn(
                    "CONTENT",
                    f"Seletor de UFs exibe {count} estados (esperado 27). "
                    "Filtros de UF incompletos reduzem cobertura de busca.",
                )
        except Exception as e:
            collector.warn("UX", f"Painel de UFs não abriu — usuário não consegue filtrar por estado: {e}")

    @pytest.mark.timeout(150)
    def test_search_full_flow_with_results(self, logged_in_driver, collector, base_url):
        """Fluxo completo: selecionar UF → buscar → aguardar resultado → medir tempo."""
        page = BuscarPage(logged_in_driver, base_url)
        page.navigate_to()

        page.select_uf("SP")

        t0 = time.time()
        page.submit_search()

        # Aguardar progresso aparecer logo após submit
        time.sleep(1.5)
        progress_appeared = page.is_progress_visible()
        if not progress_appeared:
            collector.warn(
                "UX",
                "Barra de progresso não detectada após submit — usuário pode não saber "
                "que a busca está em andamento (sem feedback visual imediato).",
            )

        resolved = page.wait_for_results(timeout=120)
        elapsed = time.time() - t0
        collector.metric("search_full_flow_seconds", round(elapsed, 1))

        assert resolved, f"Busca não resolveu em 120s — possível travamento ou timeout silencioso"

        if elapsed > 60:
            collector.warn(
                "PERF",
                f"Busca levou {elapsed:.0f}s — acima de 60s tem alto risco de abandono. "
                "Considerar resultados parciais progressivos ou feedback mais detalhado.",
            )
        elif elapsed > 30:
            collector.warn(
                "PERF",
                f"Busca levou {elapsed:.0f}s > 30s benchmark — monitorar crescimento com volume.",
            )

    @pytest.mark.timeout(150)
    def test_download_button_discoverability(self, logged_in_driver, collector, base_url):
        """Botão de download deve ser visível sem scroll após busca concluída."""
        page = BuscarPage(logged_in_driver, base_url)
        page.navigate_to()
        page.select_uf("SP")
        page.submit_search()
        page.wait_for_results(timeout=120)

        has_download = page.is_download_button_present()
        if not has_download:
            collector.warn(
                "CONTENT",
                "Botão de download de Excel não encontrado após busca com resultados. "
                "Download é feature diferenciadora — deve ser proeminente.",
            )
            return

        in_viewport = page.is_download_button_in_viewport()
        if not in_viewport:
            collector.warn(
                "UX",
                "Botão de download fora do viewport após busca — "
                "usuário precisa rolar para encontrá-lo. Considerar sticky footer ou CTA fixo.",
            )

    @pytest.mark.timeout(150)
    def test_raw_vs_filtered_count_communication(self, logged_in_driver, collector, base_url):
        """Diferença entre total raw e filtrado deve ser comunicada ao usuário."""
        page = BuscarPage(logged_in_driver, base_url)
        page.navigate_to()
        page.select_uf("SP")
        page.submit_search()
        page.wait_for_results(timeout=120)

        communicated = page.get_result_raw_vs_filtered_communicated()
        if not communicated:
            collector.warn(
                "UX",
                "A diferença entre total de editais encontrados e filtrados por setor "
                "não é claramente comunicada. Usuário pode achar que viu todos os resultados "
                "quando na verdade só viu os relevantes ao setor.",
            )

    def test_empty_state_has_actionable_cta(self, logged_in_driver, collector, base_url):
        """Estado vazio deve guiar o usuário para tentar novamente."""
        page = BuscarPage(logged_in_driver, base_url)
        page.navigate_to()

        # Busca com setor que provavelmente terá poucos resultados em UF pequena
        page.select_uf("AC")  # Acre — menor volume
        page.submit_search()
        page.wait_for_results(timeout=90)

        if page.has_empty_state():
            has_cta = page.get_empty_state_has_cta()
            if not has_cta:
                collector.warn(
                    "UX",
                    "Estado vazio sem CTA de ação — usuário fica sem guia do que fazer. "
                    "Sugestões: 'Tentar outro setor', 'Expandir para Brasil', 'Ver editais recentes'.",
                )

    def test_all_brazil_selection(self, logged_in_driver, collector, base_url):
        """Opção 'Todo o Brasil' deve estar acessível e com label claro."""
        page = BuscarPage(logged_in_driver, base_url)
        page.navigate_to()
        page.open_filter_panel()

        selected = page.select_all_brazil()
        if not selected:
            collector.warn(
                "UX",
                "Opção 'Todo o Brasil' não encontrada no seletor de UFs — "
                "usuário precisa marcar 27 estados individualmente.",
            )
