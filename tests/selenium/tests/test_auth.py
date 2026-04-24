"""
Testes de autenticação — login, signup, recuperação de senha.

Hard asserts: elementos críticos presentes, fluxo funcional.
Soft insights: UX quality, friction points, acessibilidade.
"""

import time
import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.signup_page import SignupPage


@pytest.mark.auth
class TestLoginPage:
    def test_page_loads_and_has_required_fields(self, driver, collector, base_url):
        page = LoginPage(driver, base_url)
        load_time = page.navigate_to()

        collector.metric("login_page_load_seconds", round(load_time, 2))
        if load_time > 3:
            collector.warn("PERF", f"/login carregou em {load_time:.1f}s > 3s — pode aumentar bounce")

        assert page.is_element_present(By.ID, "email"), "/login: campo #email ausente"
        assert page.is_element_present(By.ID, "password"), "/login: campo #password ausente"
        assert page.is_element_present(
            By.CSS_SELECTOR, "#login-panel-password button[type='submit']"
        ), "/login: botão submit ausente"

    def test_google_oauth_button_visibility(self, driver, collector, base_url):
        """OAuth deve estar visível sem scroll — é alternativa de conversão alta."""
        page = LoginPage(driver, base_url)
        page.navigate_to()

        assert page.is_google_button_present(), "Botão Google OAuth não encontrado — possível regressão"

        if not page.is_google_button_in_viewport():
            collector.warn(
                "UX",
                "Botão 'Entrar com Google' fora do viewport inicial — usuário precisa rolar para ver "
                "alternativa. OAuth tipicamente tem 30-50% maior conversão que email/senha.",
            )

    def test_error_message_on_invalid_login(self, driver, collector, base_url):
        """Mensagem de erro deve aparecer e ser específica o suficiente para guiar o usuário."""
        page = LoginPage(driver, base_url)
        page.submit_invalid_login("naoexiste@teste.com", "senhaerrada123")

        error_text = page.get_error_text(timeout=10)
        assert error_text, "Nenhuma mensagem de erro exibida após credenciais inválidas"

        collector.metric("login_error_message", error_text)

        specific_hints = ["senha", "email", "credenciais", "incorrect", "inválid", "wrong"]
        is_specific = any(hint in error_text.lower() for hint in specific_hints)
        if not is_specific:
            collector.warn(
                "UX",
                f"Erro de login genérico: '{error_text}'. Mensagem específica reduz tentativas "
                "de suporte e melhora UX para usuários que erraram apenas a senha.",
            )

    def test_forgot_password_link_present_and_visible(self, driver, collector, base_url):
        page = LoginPage(driver, base_url)
        page.navigate_to()

        assert page.is_element_present(
            By.CSS_SELECTOR, "a[href='/recuperar-senha']"
        ), "Link 'Esqueci minha senha' ausente — usuário sem saída se esquecer senha"

        link = driver.find_element(By.CSS_SELECTOR, "a[href='/recuperar-senha']")
        if not page.is_element_in_viewport(link):
            collector.warn(
                "UX",
                "Link 'Esqueci minha senha' fora do viewport — usuário pode não encontrar "
                "e recorrer ao suporte desnecessariamente.",
            )

    def test_password_reset_page(self, driver, collector, base_url):
        page = LoginPage(driver, base_url)
        load_time = page.navigate("/recuperar-senha")

        collector.metric("password_reset_page_load_seconds", round(load_time, 2))
        if load_time > 3:
            collector.warn("PERF", f"/recuperar-senha carregou em {load_time:.1f}s")

        has_email_input = page.is_element_present(
            By.CSS_SELECTOR, "input[type='email'], #email"
        )
        assert has_email_input, "/recuperar-senha: campo de email ausente"

        has_back_link = page.is_element_present(By.CSS_SELECTOR, "a[href='/login']")
        if not has_back_link:
            collector.warn(
                "UX",
                "/recuperar-senha sem link de retorno para /login — usuário pode ficar preso "
                "se chegou aqui por engano.",
            )

    def test_login_form_usable_on_mobile(self, driver, collector, base_url):
        """Form de login deve ser completamente usável em 390px (iPhone 14 Pro)."""
        driver.set_window_size(390, 844)
        try:
            page = LoginPage(driver, base_url)
            page.navigate_to()

            email_el = driver.find_element(By.ID, "email")
            assert email_el.is_displayed(), "Campo email não visível em viewport 390px"

            submit = driver.find_element(
                By.CSS_SELECTOR, "#login-panel-password button[type='submit']"
            )
            if not page.is_element_in_viewport(submit):
                collector.warn(
                    "UX",
                    "Botão submit fora do viewport mobile (390px) — usuário precisa rolar antes "
                    "de submeter o form. Especialmente problemático com teclado virtual aberto.",
                )
        finally:
            driver.set_window_size(1280, 720)


@pytest.mark.auth
class TestSignupPage:
    def test_page_loads_with_all_fields(self, driver, collector, base_url):
        page = SignupPage(driver, base_url)
        load_time = page.navigate_to()

        collector.metric("signup_page_load_seconds", round(load_time, 2))
        if load_time > 3:
            collector.warn("PERF", f"/signup carregou em {load_time:.1f}s")

        for field_id, label in [
            ("fullName", "nome completo"),
            ("email", "email"),
            ("new-password", "senha"),
        ]:
            assert page.is_element_present(By.ID, field_id), f"/signup: campo #{field_id} ({label}) ausente"

    def test_password_strength_indicator(self, driver, collector, base_url):
        """Indicador de força de senha deve responder a diferentes senhas."""
        page = SignupPage(driver, base_url)
        page.navigate_to()

        pwd_field = page.wait_for_clickable(By.ID, "new-password")
        pwd_field.send_keys("123")
        time.sleep(0.3)
        weak_label = page.get_password_strength_label()

        if not weak_label:
            collector.warn(
                "UX",
                "Indicador de força de senha não aparece após digitar — "
                "usuário sem feedback sobre requisitos. Reduz abandono de form.",
            )
            return

        pwd_field.clear()
        pwd_field.send_keys("SenhaForte@2026#")
        time.sleep(0.3)
        strong_label = page.get_password_strength_label()

        if weak_label == strong_label:
            collector.warn(
                "UX",
                f"Indicador de força não diferencia senhas: fraca='{weak_label}', "
                f"forte='{strong_label}'. Usuário não tem guia de melhoria.",
            )

    def test_confirm_password_match_feedback(self, driver, collector, base_url):
        """Feedback em tempo real quando senhas coincidem reduz erros no submit."""
        page = SignupPage(driver, base_url)
        page.navigate_to()

        pwd = page.wait_for_clickable(By.ID, "new-password")
        pwd.send_keys("MinhaSenha@2026")

        confirm = driver.find_element(By.ID, "confirmPassword")
        confirm.send_keys("MinhaSenha@2026")
        confirm.send_keys("\t")
        time.sleep(0.5)

        if not page.is_confirm_match_shown():
            collector.warn(
                "UX",
                "Feedback 'senhas coincidem' não aparece em tempo real — "
                "usuário só descobre erro de digitação ao submeter o form.",
            )

    def test_already_authenticated_redirect(self, driver, collector, base_url):
        """Usuário já autenticado não deve ver form de cadastro confuso."""
        page = SignupPage(driver, base_url)
        page.navigate_to()

        if page.is_already_authenticated():
            collector.warn(
                "UX",
                "/signup exibe banner 'já autenticado' — considerar redirect automático "
                "para /buscar em vez de mostrar form inacessível.",
            )
