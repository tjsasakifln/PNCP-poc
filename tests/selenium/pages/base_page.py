import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException


class BasePage:
    def __init__(self, driver, base_url: str):
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    def navigate(self, path: str) -> float:
        """Navega para path e retorna tempo de carregamento em segundos."""
        url = self.base_url + path
        t0 = time.time()
        self.driver.get(url)
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return time.time() - t0

    def wait_for_element(self, by: By, selector: str, timeout: int = 15):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )

    def wait_for_clickable(self, by: By, selector: str, timeout: int = 15):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )

    def wait_for_url_contains(self, path: str, timeout: int = 30):
        WebDriverWait(self.driver, timeout).until(EC.url_contains(path))

    def is_element_present(self, by: By, selector: str) -> bool:
        try:
            self.driver.find_element(by, selector)
            return True
        except NoSuchElementException:
            return False

    def is_element_in_viewport(self, element) -> bool:
        return self.driver.execute_script(
            """
            const r = arguments[0].getBoundingClientRect();
            return r.top >= 0 && r.left >= 0
                && r.bottom <= (window.innerHeight || document.documentElement.clientHeight)
                && r.right  <= (window.innerWidth  || document.documentElement.clientWidth);
            """,
            element,
        )

    def get_seo_snapshot(self) -> dict:
        """Extrai metadados SEO da página atual."""
        title = self.driver.title

        def _meta(selector: str, attr: str = "content") -> str:
            try:
                return self.driver.find_element(By.CSS_SELECTOR, selector).get_attribute(attr) or ""
            except NoSuchElementException:
                return ""

        description = _meta("meta[name='description']")
        canonical = _meta("link[rel='canonical']", "href")
        og_title = _meta("meta[property='og:title']")
        og_description = _meta("meta[property='og:description']")

        h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
        h1_texts_safe: list[str] = []
        for el in h1_elements:
            try:
                h1_texts_safe.append(el.text)
            except StaleElementReferenceException:
                pass

        structured_data_types: list[str] = []
        for script in self.driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']"):
            try:
                data = json.loads(script.get_attribute("innerHTML") or "{}")
                if isinstance(data, dict):
                    structured_data_types.append(data.get("@type", "Unknown"))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            structured_data_types.append(item.get("@type", "Unknown"))
            except (json.JSONDecodeError, Exception):
                pass

        images_without_alt: int = self.driver.execute_script(
            "return Array.from(document.images).filter(i => !i.alt || !i.alt.trim()).length"
        )
        buttons_without_label: int = self.driver.execute_script(
            """return Array.from(document.querySelectorAll('button'))
               .filter(b => !b.textContent.trim() && !b.getAttribute('aria-label')).length"""
        )

        return {
            "title": title,
            "title_length": len(title),
            "description": description,
            "description_length": len(description),
            "canonical": canonical,
            "h1_count": len(h1_texts_safe),
            "h1_texts": h1_texts_safe,
            "og_title": og_title,
            "og_description": og_description,
            "structured_data_types": structured_data_types,
            "images_without_alt": images_without_alt,
            "buttons_without_label": buttons_without_label,
        }

    def audit_seo(self, snapshot: dict, collector, url: str):
        """Emite insights baseados no snapshot SEO. Não falha o teste."""
        if not snapshot["title"]:
            collector.warn("SEO", f"{url}: título ausente")
        elif snapshot["title_length"] > 60:
            collector.warn("SEO", f"{url}: título {snapshot['title_length']} chars > 60 — truncado no Google")

        if not snapshot["description"]:
            collector.warn("SEO", f"{url}: meta description ausente")
        elif snapshot["description_length"] < 50:
            collector.warn("SEO", f"{url}: description {snapshot['description_length']} chars < 50 — muito curta")
        elif snapshot["description_length"] > 160:
            collector.warn("SEO", f"{url}: description {snapshot['description_length']} chars > 160 — truncada")

        if snapshot["h1_count"] == 0:
            collector.warn("SEO", f"{url}: H1 ausente")
        elif snapshot["h1_count"] > 1:
            collector.warn("SEO", f"{url}: {snapshot['h1_count']} H1s — deve ter exatamente 1")

        if not snapshot["canonical"]:
            collector.warn("SEO", f"{url}: canonical ausente")

        if snapshot["images_without_alt"] > 0:
            collector.warn("A11Y", f"{url}: {snapshot['images_without_alt']} imagem(ns) sem alt text")

        if snapshot["buttons_without_label"] > 0:
            collector.warn("A11Y", f"{url}: {snapshot['buttons_without_label']} botão(ões) sem label acessível")
