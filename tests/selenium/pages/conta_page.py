from selenium.webdriver.common.by import By
from .base_page import BasePage


class ContaPage(BasePage):
    def navigate_to_plano(self) -> float:
        return self.navigate("/conta/plano")

    def navigate_to_dados(self) -> float:
        return self.navigate("/conta/dados")

    def navigate_to_seguranca(self) -> float:
        return self.navigate("/conta/seguranca")

    def navigate_to_conta(self) -> float:
        return self.navigate("/conta")

    def get_plan_info(self) -> dict:
        """Extrai informações do plano atual de /conta/plano."""
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()

        plan_keywords = ["pro", "trial", "grátis", "gratuito", "consultoria", "plano"]
        date_keywords = ["próxima cobrança", "vence em", "válido até", "renova em", "expira"]
        cancel_keywords = ["cancelar", "encerrar assinatura"]

        return {
            "plan_name_visible": any(kw in body_text for kw in plan_keywords),
            "billing_date_visible": any(kw in body_text for kw in date_keywords),
            "price_visible": "r$" in body_text,
            "cancel_option_visible": any(kw in body_text for kw in cancel_keywords),
        }

    def are_dados_fields_prefilled(self) -> bool:
        """Verifica se campos de /conta/dados estão pré-preenchidos."""
        inputs = self.driver.find_elements(
            By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel']"
        )
        filled = sum(1 for inp in inputs if (inp.get_attribute("value") or "").strip())
        return filled > 0

    def has_security_options(self) -> bool:
        """Verifica se /conta/seguranca tem opções de segurança."""
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        security_keywords = ["senha", "password", "autenticação", "2fa", "segurança"]
        return any(kw in body_text for kw in security_keywords)
