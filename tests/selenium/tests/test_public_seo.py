"""
Auditoria SEO e qualidade de conteúdo — páginas públicas.

Foco em: title, description, H1, canonical, structured data, alt texts.
Todas as páginas testadas aqui são públicas (sem auth).
"""

import pytest

from pages.public_page import PublicPage


PUBLIC_PAGES = [
    ("/", "home"),
    ("/licitacoes", "licitações hub"),
    ("/contratos", "contratos hub"),
    ("/fornecedores", "fornecedores hub"),
    ("/blog", "blog"),
    ("/sobre", "sobre"),
    ("/planos", "planos/pricing"),
    ("/features", "features"),
    ("/ajuda", "ajuda"),
]

SEO_PAGES_WITH_STRUCTURED_DATA = {
    "/": ["Organization", "WebSite"],
    "/sobre": ["Organization"],
    "/blog": ["Blog"],
    "/planos": ["Product"],
}


@pytest.mark.seo
class TestPublicPagesSEO:
    @pytest.mark.parametrize("path,label", PUBLIC_PAGES)
    def test_page_loads_without_error(self, driver, collector, base_url, path, label):
        page = PublicPage(driver, base_url)
        load_time = page.navigate_to(path)

        collector.metric(f"page_load_{label.replace('/', '_').replace(' ', '_')}_seconds", round(load_time, 2))

        assert not page.page_has_error(), f"{path}: página retornou erro (404/500)"

        if load_time > 3:
            collector.warn("PERF", f"{path}: carregou em {load_time:.1f}s > 3s — impacta Core Web Vitals")

    @pytest.mark.parametrize("path,label", PUBLIC_PAGES)
    def test_seo_snapshot_audit(self, driver, collector, base_url, path, label):
        """Executa auditoria SEO completa em cada página pública."""
        page = PublicPage(driver, base_url)
        page.navigate_to(path)

        snapshot = page.get_seo_snapshot()
        page.audit_seo(snapshot, collector, path)

        # Hard asserts apenas para elementos críticos
        assert snapshot["title"], f"{path}: <title> ausente — bloqueador SEO crítico"
        assert snapshot["h1_count"] > 0, f"{path}: H1 ausente — impacto direto no ranking"

        collector.metric(f"seo_{path.replace('/', '_') or 'home'}_title_len", snapshot["title_length"])
        collector.metric(f"seo_{path.replace('/', '_') or 'home'}_desc_len", snapshot["description_length"])

    @pytest.mark.parametrize("path,expected_types", SEO_PAGES_WITH_STRUCTURED_DATA.items())
    def test_structured_data_present(self, driver, collector, base_url, path, expected_types):
        """Páginas-chave devem ter JSON-LD com tipos específicos."""
        page = PublicPage(driver, base_url)
        page.navigate_to(path)
        snapshot = page.get_seo_snapshot()

        present_types = snapshot["structured_data_types"]
        collector.metric(f"structured_data_{path.replace('/', '_') or 'home'}", str(present_types))

        for expected_type in expected_types:
            if expected_type not in present_types:
                collector.warn(
                    "SEO",
                    f"{path}: structured data '{expected_type}' ausente. "
                    f"Presentes: {present_types or 'nenhum'}. "
                    f"Rich results no Google dependem deste schema.",
                )

    def test_licitacoes_hub_has_content_and_links(self, driver, collector, base_url):
        page = PublicPage(driver, base_url)
        page.navigate_to("/licitacoes")

        assert page.has_content_loaded(), "/licitacoes: conteúdo principal não carregou"

        internal_links = page.get_internal_links_count()
        collector.metric("licitacoes_internal_links_count", internal_links)
        if internal_links < 5:
            collector.warn(
                "SEO",
                f"/licitacoes tem apenas {internal_links} links internos — "
                "hub de conteúdo deve ter links para subpáginas de setores/UFs para distribuir PageRank.",
            )

        h2_count = page.get_h2_count()
        if h2_count < 2:
            collector.warn(
                "CONTENT",
                f"/licitacoes tem {h2_count} H2(s) — "
                "headings secundários melhoram estrutura e scaneabilidade do conteúdo.",
            )

    def test_blog_has_articles_listed(self, driver, collector, base_url):
        from selenium.webdriver.common.by import By
        page = PublicPage(driver, base_url)
        page.navigate_to("/blog")

        assert page.has_content_loaded(), "/blog: conteúdo não carregou"

        # Check for article links
        article_links = driver.find_elements(
            By.CSS_SELECTOR, "article a, [class*='post'] a, [class*='article'] a"
        )
        collector.metric("blog_article_links_count", len(article_links))
        if len(article_links) < 3:
            collector.warn(
                "CONTENT",
                f"/blog lista {len(article_links)} artigos visíveis — "
                "hub de blog com poucos artigos linkados impacta crawlability.",
            )

    def test_planos_page_shows_prices(self, driver, collector, base_url):
        from selenium.webdriver.common.by import By
        page = PublicPage(driver, base_url)
        page.navigate_to("/planos")

        body_text = driver.find_element(By.TAG_NAME, "body").text
        has_price = "R$" in body_text or "grátis" in body_text.lower()
        assert has_price, "/planos: preços não encontrados — página de pricing sem preços é bloqueador de conversão"

        # Verificar se plano trial está destacado
        trial_highlighted = "14" in body_text or "trial" in body_text.lower() or "grátis" in body_text.lower()
        if not trial_highlighted:
            collector.warn(
                "UX",
                "/planos não destaca o período de trial de 14 dias — "
                "reduzir fricção mencionando 'sem cartão' e 'gratuito por 14 dias' aumenta conversão.",
            )

    def test_ajuda_page_has_searchable_content(self, driver, collector, base_url):
        from selenium.webdriver.common.by import By
        page = PublicPage(driver, base_url)
        page.navigate_to("/ajuda")

        assert page.has_content_loaded(), "/ajuda: conteúdo não carregou"

        has_search = page.is_element_present(
            By.CSS_SELECTOR, "input[type='search'], input[placeholder*='buscar'], input[placeholder*='pesquisar']"
        )
        if not has_search:
            collector.warn(
                "UX",
                "/ajuda sem campo de busca — usuários com dúvida específica precisam "
                "navegar manualmente. Campo de busca reduz tickets de suporte.",
            )

    def test_sobre_page_has_trust_signals(self, driver, collector, base_url):
        from selenium.webdriver.common.by import By
        page = PublicPage(driver, base_url)
        page.navigate_to("/sobre")

        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()

        trust_signals = {
            "cnpj": "CNPJ da empresa",
            "confenge": "razão social",
            "equipe": "informação de equipe",
        }
        for signal, label in trust_signals.items():
            if signal not in body_text:
                collector.warn(
                    "CONTENT",
                    f"/sobre sem {label} ('{signal}') — páginas 'Sobre' com informações de empresa "
                    "aumentam confiança em B2G onde due diligence é comum.",
                )

    def test_home_has_cta_above_fold(self, driver, collector, base_url):
        page = PublicPage(driver, base_url)
        page.navigate_to("/")

        has_cta = page.has_cta_button()
        if not has_cta:
            collector.warn(
                "UX",
                "Home sem CTA visível ('Teste grátis', 'Começar', etc.) — "
                "hero section sem CTA claro reduz conversão de visitantes orgânicos.",
            )
