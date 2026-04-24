from selenium.webdriver.common.by import By
from .base_page import BasePage


class PublicPage(BasePage):
    def navigate_to(self, path: str) -> float:
        return self.navigate(path)

    def has_h1(self) -> bool:
        return bool(self.driver.find_elements(By.TAG_NAME, "h1"))

    def get_h2_count(self) -> int:
        return len(self.driver.find_elements(By.TAG_NAME, "h2"))

    def has_content_loaded(self) -> bool:
        """Verifica se conteúdo principal carregou (não só skeleton)."""
        for selector in ["main", "[role='main']", "article", "section", "div[class*='max-w']", "div[class*='container']"]:
            els = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for el in els:
                try:
                    if len(el.text.strip()) > 80:
                        return True
                except Exception:
                    pass
        return False

    def get_internal_links_count(self) -> int:
        base = self.base_url.replace("https://", "").replace("http://", "")
        links = self.driver.find_elements(By.TAG_NAME, "a")
        return sum(
            1 for link in links
            if base in (link.get_attribute("href") or "")
        )

    def has_pagination(self) -> bool:
        for selector in [
            "[class*='pagination']",
            "[class*='Pagination']",
            "nav[aria-label*='page']",
            "nav[aria-label*='página']",
        ]:
            if self.driver.find_elements(By.CSS_SELECTOR, selector):
                return True
        return False

    def has_breadcrumb(self) -> bool:
        for selector in [
            "nav[aria-label*='breadcrumb']",
            "[class*='breadcrumb']",
            "[class*='Breadcrumb']",
        ]:
            if self.driver.find_elements(By.CSS_SELECTOR, selector):
                return True
        return False

    def has_cta_button(self) -> bool:
        """Verifica se há CTA visível (ex: 'Teste grátis', 'Começar')."""
        cta_texts = ["teste grátis", "começar", "criar conta", "experimentar", "comece"]
        links_and_buttons = (
            self.driver.find_elements(By.TAG_NAME, "a") +
            self.driver.find_elements(By.TAG_NAME, "button")
        )
        for el in links_and_buttons:
            if any(cta in (el.text or "").lower() for cta in cta_texts):
                return True
        return False

    def page_has_error(self) -> bool:
        """Detecta página de erro (404, 500, Next.js error boundary)."""
        title = self.driver.title.lower()
        # Check title for HTTP error codes (accurate — titles say "404 Not Found" etc.)
        if any(signal in title for signal in ["404", "500", "not found", "error", "internal server"]):
            return True
        # Check for Next.js specific error elements
        if self.driver.find_elements(By.CSS_SELECTOR, "[data-nextjs-error], #__nextjs_error"):
            return True
        return False
