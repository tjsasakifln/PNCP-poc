"""
Testes de admin e conta — completeness, dados reais vs placeholders.

Requer: ADMIN_PASSWORD configurado (usa logged_in_driver).
"""

import pytest
from selenium.webdriver.common.by import By

from pages.conta_page import ContaPage
from pages.public_page import PublicPage


@pytest.mark.admin
class TestAdminPages:
    def test_admin_dashboard_loads(self, logged_in_driver, collector, base_url):
        page = PublicPage(logged_in_driver, base_url)
        load_time = page.navigate_to("/admin")

        collector.metric("admin_page_load_seconds", round(load_time, 2))
        if load_time > 3:
            collector.warn("PERF", f"/admin carregou em {load_time:.1f}s")

        assert not page.page_has_error(), "/admin retornou erro — verifique autorização ou rota"

    def test_admin_has_real_data_not_placeholders(self, logged_in_driver, collector, base_url):
        """Widgets admin devem mostrar dados reais, não '--' ou 'N/A' em todos os campos."""
        page = PublicPage(logged_in_driver, base_url)
        page.navigate_to("/admin")

        body_text = logged_in_driver.find_element(By.TAG_NAME, "body").text

        placeholder_count = body_text.count("--") + body_text.count("N/A") + body_text.count("n/a")
        collector.metric("admin_placeholder_values_count", placeholder_count)

        if placeholder_count > 5:
            collector.warn(
                "CONTENT",
                f"/admin tem {placeholder_count} ocorrências de '--' ou 'N/A' — "
                "métricas sem dados impedem tomada de decisão. Verificar se widgets "
                "estão conectados às fontes corretas.",
            )

    def test_admin_feature_flags_page(self, logged_in_driver, collector, base_url):
        page = PublicPage(logged_in_driver, base_url)
        load_time = page.navigate_to("/admin/feature-flags")

        collector.metric("admin_feature_flags_load_seconds", round(load_time, 2))

        assert not page.page_has_error(), "/admin/feature-flags retornou erro"

        body_text = logged_in_driver.find_element(By.TAG_NAME, "body").text.lower()

        # Deve ter pelo menos as flags documentadas no CLAUDE.md
        expected_flags = ["datalake", "llm", "viability"]
        for flag in expected_flags:
            if flag not in body_text:
                collector.warn(
                    "CONTENT",
                    f"/admin/feature-flags: flag '{flag}' não visível — "
                    "admin precisa ver todas as feature flags documentadas para operar com segurança.",
                )

        # Verificar se há toggle controls (não só leitura)
        toggles = logged_in_driver.find_elements(
            By.CSS_SELECTOR, "input[type='checkbox'], button[role='switch'], [class*='toggle']"
        )
        if not toggles:
            collector.warn(
                "UX",
                "/admin/feature-flags sem controles de toggle — "
                "se flags são somente leitura, admin não consegue mudar sem deploy.",
            )

    def test_admin_slo_dashboard(self, logged_in_driver, collector, base_url):
        page = PublicPage(logged_in_driver, base_url)
        load_time = page.navigate_to("/admin/slo")

        if page.page_has_error():
            collector.warn("CONTENT", "/admin/slo retornou erro — dashboard de SLO inacessível")
            return

        collector.metric("admin_slo_load_seconds", round(load_time, 2))

        body_text = logged_in_driver.find_element(By.TAG_NAME, "body").text
        has_percentages = "%" in body_text
        if not has_percentages:
            collector.warn(
                "CONTENT",
                "/admin/slo sem percentuais visíveis — dashboard de SLO sem métricas "
                "não permite monitorar conformidade de SLA com usuários.",
            )

    def test_admin_cache_page(self, logged_in_driver, collector, base_url):
        page = PublicPage(logged_in_driver, base_url)
        page.navigate_to("/admin/cache")

        if page.page_has_error():
            collector.warn("CONTENT", "/admin/cache retornou erro — gestão de cache inacessível")
            return

        body_text = logged_in_driver.find_element(By.TAG_NAME, "body").text.lower()
        cache_terms = ["cache", "hit", "miss", "ttl", "entries"]
        has_cache_info = any(term in body_text for term in cache_terms)
        if not has_cache_info:
            collector.warn(
                "CONTENT",
                "/admin/cache sem informações de cache visíveis — "
                "página de gestão deve mostrar hit rate, TTL e entradas para diagnóstico.",
            )


@pytest.mark.admin
class TestContaPages:
    def test_conta_plano_shows_plan_info(self, logged_in_driver, collector, base_url):
        page = ContaPage(logged_in_driver, base_url)
        load_time = page.navigate_to_plano()

        collector.metric("conta_plano_load_seconds", round(load_time, 2))
        assert not page.page_has_error() if hasattr(page, "page_has_error") else True

        info = page.get_plan_info()

        if not info["plan_name_visible"]:
            collector.warn(
                "CONTENT",
                "/conta/plano sem nome do plano atual — usuário não sabe qual plano está usando.",
            )

        if not info["billing_date_visible"]:
            collector.warn(
                "UX",
                "/conta/plano sem data da próxima cobrança — "
                "transparência de billing reduz contestações e churn por surpresa.",
            )

        if not info["price_visible"]:
            collector.warn(
                "CONTENT",
                "/conta/plano sem valor visível — "
                "usuário não sabe quanto está pagando sem sair da página.",
            )

        if not info["cancel_option_visible"]:
            collector.warn(
                "UX",
                "/conta/plano sem opção de cancelamento visível — "
                "esconder cancelamento aumenta frustração e piora NPS. "
                "Melhor: mostrar cancelamento + oferta de retenção.",
            )

    def test_conta_dados_has_prefilled_fields(self, logged_in_driver, collector, base_url):
        page = ContaPage(logged_in_driver, base_url)
        load_time = page.navigate_to_dados()

        collector.metric("conta_dados_load_seconds", round(load_time, 2))

        prefilled = page.are_dados_fields_prefilled()
        if not prefilled:
            collector.warn(
                "UX",
                "/conta/dados sem campos pré-preenchidos — usuário precisa redigitar "
                "informações que o sistema já tem (email, nome). Reduz trust e aumenta erros.",
            )

    def test_conta_seguranca_has_password_option(self, logged_in_driver, collector, base_url):
        page = ContaPage(logged_in_driver, base_url)
        page.navigate_to_seguranca()

        has_security = page.has_security_options()
        assert has_security, "/conta/seguranca sem opções de segurança — página vazia ou erro"

        body_text = logged_in_driver.find_element(By.TAG_NAME, "body").text.lower()
        if "2fa" not in body_text and "dois fatores" not in body_text and "autenticação de dois" not in body_text:
            collector.warn(
                "UX",
                "/conta/seguranca sem menção a 2FA — "
                "empresas B2G frequentemente exigem 2FA por compliance. "
                "Oferecer TOTP/SMS aumenta credibilidade com grandes clientes.",
            )

    def test_conta_navigation_works(self, logged_in_driver, collector, base_url):
        """Navegação entre abas de conta deve funcionar sem erros."""
        page = ContaPage(logged_in_driver, base_url)

        sub_pages = [
            ("/conta/dados", "dados"),
            ("/conta/plano", "plano"),
            ("/conta/seguranca", "segurança"),
        ]

        for path, label in sub_pages:
            page.navigate(path)
            body_text = logged_in_driver.find_element(By.TAG_NAME, "body").text.lower()

            error_signals = ["404", "500", "not found", "internal server error", "an error occurred"]
            has_error = any(signal in body_text for signal in error_signals)
            if has_error:
                collector.warn(
                    "CONTENT",
                    f"/conta/{label} retornou erro — sub-página de conta inacessível.",
                )
