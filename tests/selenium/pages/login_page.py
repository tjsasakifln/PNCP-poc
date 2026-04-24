import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base_page import BasePage


class LoginPage(BasePage):
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "#login-panel-password button[type='submit']")
    ERROR_DIV = (By.ID, "login-error")
    GOOGLE_BUTTON = (By.CSS_SELECTOR, "[data-testid='google-oauth-button']")
    FORGOT_LINK = (By.CSS_SELECTOR, "a[href='/recuperar-senha']")
    SIGNUP_LINK = (By.CSS_SELECTOR, "a[href='/signup']")

    def navigate_to(self) -> float:
        return self.navigate("/login")

    def login(self, email: str, password: str, timeout: int = 30) -> float:
        """Executa login e retorna tempo total em segundos."""
        self.navigate_to()
        t0 = time.time()

        email_el = self.wait_for_clickable(*self.EMAIL_INPUT)
        email_el.clear()
        email_el.send_keys(email)

        pwd_el = self.driver.find_element(*self.PASSWORD_INPUT)
        pwd_el.clear()
        pwd_el.send_keys(password)

        self.driver.find_element(*self.SUBMIT_BUTTON).click()

        WebDriverWait(self.driver, timeout).until(
            lambda d: "/login" not in d.current_url
        )
        return time.time() - t0

    def submit_invalid_login(self, email: str, password: str):
        """Submete credenciais inválidas sem esperar redirect."""
        self.navigate_to()
        self.wait_for_clickable(*self.EMAIL_INPUT).send_keys(email)
        self.driver.find_element(*self.PASSWORD_INPUT).send_keys(password)
        self.driver.find_element(*self.SUBMIT_BUTTON).click()

    def get_error_text(self, timeout: int = 10) -> str:
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.ERROR_DIV)
            )
            return el.text.strip()
        except TimeoutException:
            return ""

    def is_google_button_present(self) -> bool:
        return self.is_element_present(*self.GOOGLE_BUTTON)

    def is_google_button_in_viewport(self) -> bool:
        try:
            el = self.driver.find_element(*self.GOOGLE_BUTTON)
            return self.is_element_in_viewport(el)
        except Exception:
            return False
