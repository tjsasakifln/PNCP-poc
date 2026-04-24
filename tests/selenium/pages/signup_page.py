import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base_page import BasePage


class SignupPage(BasePage):
    FULLNAME_INPUT = (By.ID, "fullName")
    EMAIL_INPUT = (By.ID, "email")
    PHONE_INPUT = (By.ID, "phone")
    PASSWORD_INPUT = (By.ID, "new-password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirmPassword")

    NAME_ERROR = (By.CSS_SELECTOR, "[data-testid='name-error']")
    EMAIL_ERROR = (By.CSS_SELECTOR, "[data-testid='email-error']")
    PHONE_ERROR = (By.CSS_SELECTOR, "[data-testid='phone-error']")
    PASSWORD_STRENGTH_LABEL = (By.CSS_SELECTOR, "[data-testid='password-strength-label']")
    CONFIRM_ERROR = (By.CSS_SELECTOR, "[data-testid='confirm-password-error']")
    CONFIRM_MATCH = (By.CSS_SELECTOR, "[data-testid='confirm-password-match']")
    ALREADY_AUTH_BANNER = (By.CSS_SELECTOR, "[data-testid='already-auth-banner']")

    def navigate_to(self) -> float:
        return self.navigate("/signup")

    def fill_form(self, name: str, email: str, phone: str, password: str, confirm: str):
        self.navigate_to()
        self.wait_for_clickable(*self.FULLNAME_INPUT).send_keys(name)
        self.driver.find_element(*self.EMAIL_INPUT).send_keys(email)
        self.driver.find_element(*self.PHONE_INPUT).send_keys(phone)
        self.driver.find_element(*self.PASSWORD_INPUT).send_keys(password)
        self.driver.find_element(*self.CONFIRM_PASSWORD_INPUT).send_keys(confirm)

    def get_password_strength_label(self) -> str:
        try:
            el = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.PASSWORD_STRENGTH_LABEL)
            )
            return el.text.strip()
        except Exception:
            return ""

    def get_visible_errors(self) -> dict[str, str]:
        errors: dict[str, str] = {}
        for field, locator in [
            ("name", self.NAME_ERROR),
            ("email", self.EMAIL_ERROR),
            ("phone", self.PHONE_ERROR),
            ("confirm", self.CONFIRM_ERROR),
        ]:
            try:
                el = self.driver.find_element(*locator)
                if el.is_displayed():
                    errors[field] = el.text.strip()
            except Exception:
                pass
        return errors

    def is_confirm_match_shown(self) -> bool:
        try:
            el = self.driver.find_element(*self.CONFIRM_MATCH)
            return el.is_displayed()
        except Exception:
            return False

    def is_already_authenticated(self) -> bool:
        return self.is_element_present(*self.ALREADY_AUTH_BANNER)
