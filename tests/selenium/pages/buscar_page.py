import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_page import BasePage

# Seletores de resultado — fallbacks por ordem de prioridade
_RESULT_SELECTORS = [
    "[data-testid='result-card']",
    "[class*='ResultCard']",
    "[class*='result-card']",
    ".licitacao-card",
    "article[class*='licitacao']",
]

_EMPTY_STATE_SELECTORS = [
    "[data-testid='empty-state']",
    "[class*='EmptyState']",
    "[class*='empty-state']",
    "[class*='no-results']",
]

_DOWNLOAD_SELECTORS = [
    "[data-testid='download-button']",
    "a[href*='download']",
    "button[class*='download']",
    "a[class*='download']",
]


class BuscarPage(BasePage):
    CUSTOMIZE_TOGGLE = (By.CSS_SELECTOR, "[data-tour='customize-toggle']")
    UF_SELECTOR = (By.CSS_SELECTOR, "[data-tour='uf-selector']")
    DATE_INICIAL = (By.ID, "data-inicial")
    DATE_FINAL = (By.ID, "data-final")
    SETOR_DROPDOWN = (By.CSS_SELECTOR, "[id='setor-dropdown'], [aria-label*='setor'], [aria-label*='Setor']")
    SEARCH_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    PROGRESS = (By.CSS_SELECTOR, "[role='progressbar'], [class*='Progress'], [class*='progress-bar']")

    def navigate_to(self) -> float:
        return self.navigate("/buscar")

    def open_filter_panel(self):
        try:
            toggle = self.wait_for_clickable(*self.CUSTOMIZE_TOGGLE, timeout=8)
            if toggle.get_attribute("aria-expanded") != "true":
                toggle.click()
                time.sleep(0.4)
        except Exception:
            pass

    def select_uf(self, uf: str) -> bool:
        """Seleciona UF pelo texto. Retorna True se encontrada."""
        self.open_filter_panel()
        try:
            container = self.wait_for_element(*self.UF_SELECTOR, timeout=8)
            for btn in container.find_elements(By.TAG_NAME, "button"):
                if btn.text.strip().upper() == uf.upper():
                    btn.click()
                    return True
        except Exception:
            pass
        return False

    def select_all_brazil(self) -> bool:
        """Clica em 'Todo o Brasil' ou equivalente."""
        self.open_filter_panel()
        try:
            container = self.wait_for_element(*self.UF_SELECTOR, timeout=8)
            for btn in container.find_elements(By.TAG_NAME, "button"):
                text = btn.text.lower()
                if "brasil" in text or "todos" in text or "27" in text:
                    btn.click()
                    return True
        except Exception:
            pass
        return False

    def submit_search(self) -> float:
        t0 = time.time()
        btn = self.wait_for_clickable(*self.SEARCH_BUTTON, timeout=10)
        btn.click()
        return time.time() - t0

    def wait_for_results(self, timeout: int = 120) -> bool:
        """Aguarda resultados OU estado vazio aparecer. Retorna True se algo apareceu."""
        def _resolved(d):
            for sel in _RESULT_SELECTORS + _EMPTY_STATE_SELECTORS:
                if d.find_elements(By.CSS_SELECTOR, sel):
                    return True
            return False

        try:
            WebDriverWait(self.driver, timeout).until(_resolved)
            return True
        except TimeoutException:
            return False

    def has_results(self) -> bool:
        for sel in _RESULT_SELECTORS:
            if self.driver.find_elements(By.CSS_SELECTOR, sel):
                return True
        return False

    def has_empty_state(self) -> bool:
        for sel in _EMPTY_STATE_SELECTORS:
            if self.driver.find_elements(By.CSS_SELECTOR, sel):
                return True
        return False

    def count_results(self) -> int:
        for sel in _RESULT_SELECTORS:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                return len(els)
        return 0

    def is_progress_visible(self) -> bool:
        try:
            els = self.driver.find_elements(*self.PROGRESS)
            return any(el.is_displayed() for el in els)
        except Exception:
            return False

    def is_download_button_present(self) -> bool:
        for sel in _DOWNLOAD_SELECTORS:
            if self.driver.find_elements(By.CSS_SELECTOR, sel):
                return True
        return False

    def is_download_button_in_viewport(self) -> bool:
        for sel in _DOWNLOAD_SELECTORS:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                return self.is_element_in_viewport(els[0])
        return False

    def get_sector_options_count(self) -> int:
        """Conta opções no dropdown de setores."""
        try:
            # Try opening the dropdown first
            trigger = self.driver.find_element(*self.SETOR_DROPDOWN)
            trigger.click()
            time.sleep(0.5)
            options = self.driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            if options:
                return len(options)
        except Exception:
            pass
        return 0

    def get_empty_state_has_cta(self) -> bool:
        """Verifica se estado vazio tem CTA para nova busca."""
        for sel in _EMPTY_STATE_SELECTORS:
            els = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                el = els[0]
                buttons = el.find_elements(By.TAG_NAME, "button")
                links = el.find_elements(By.TAG_NAME, "a")
                return bool(buttons or links)
        return False

    def get_result_raw_vs_filtered_communicated(self) -> bool:
        """Verifica se a diferença entre raw e filtrado é mostrada ao usuário."""
        keywords = ["filtrado", "encontrado", "de", "resultado"]
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        return sum(1 for kw in keywords if kw in page_text) >= 2
