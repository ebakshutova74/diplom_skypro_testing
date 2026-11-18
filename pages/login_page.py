from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginPage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

        # Поля ввода
        self.username_input = (By.NAME, "username")
        self.password_input = (By.NAME, "password")

        # Ссылка «Войти с помощью пароля» — это <a>, а не <button>
        self.switch_to_password = (
            By.CSS_SELECTOR,
            "a.js-send-otp-form-to-username-password",
        )

        # Кнопка «Войти»
        self.login_button = (
            By.CSS_SELECTOR,
            "button.button--primary .js-username-password-form-button",
        )

        # Сообщение об ошибке
        self.error_message = (
            By.CSS_SELECTOR,
            ".field__description.js-username-password-form-description",
        )

    def open(self, base_url):
        self.driver.get(base_url)

    def click_switch_to_password(self):
        try:
            elem = self.wait.until(EC.element_to_be_clickable(self.switch_to_password))
            elem.click()
        except Exception:
            pass

    def type_username(self, username: str):
        elem = self.wait.until(EC.visibility_of_element_located(self.username_input))
        elem.clear()
        elem.send_keys(username)

    def type_password(self, password: str):
        elem = self.wait.until(EC.visibility_of_element_located(self.password_input))
        elem.clear()
        elem.send_keys(password)

    def click_login(self):
        btn = self.wait.until(EC.element_to_be_clickable(self.login_button))
        btn.click()

    def wait_for_error(self):
        return self.wait.until(EC.visibility_of_element_located(self.error_message))

    def get_error_text(self) -> str:
        elem = self.wait_for_error()
        return elem.text.strip()

    def is_error_visible(self, timeout=3) -> bool:
        short_wait = WebDriverWait(self.driver, timeout)
        try:
            short_wait.until(EC.visibility_of_element_located(self.error_message))
            return True
        except Exception:
            return False
