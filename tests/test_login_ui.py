import os

import allure
import pytest
from selenium.webdriver.support.wait import WebDriverWait

pytestmark = pytest.mark.ui

from config import LOGIN_URL
from pages.login_page import LoginPage

USERNAME = os.environ.get("SKY_USERNAME") or "test_user"
PASSWORD = os.environ.get("SKY_PASSWORD") or "test_password_123"


@pytest.fixture
def login_page(driver):
    driver.delete_all_cookies()   # каждый тест начинается с чистого листа
    page = LoginPage(driver)
    page.open(LOGIN_URL)
    page.click_switch_to_password()
    return page


@allure.title("Смоук. Вход по логину и паролю — попадаем в личный кабинет")
def test_login_positive(login_page, driver):
    login_page.type_username(USERNAME)
    login_page.type_password(PASSWORD)
    login_page.click_login()

    # Ожидаем редирект на главную личного кабинета
    WebDriverWait(driver, 15).until(lambda d: d.current_url == "https://teacher.skyeng.ru/")

    # SPA рисует контент после загрузки каркаса — ждём приветствие
    WebDriverWait(driver, 15).until(
        lambda d: "Мария" in d.page_source
    ), "Приветствие с именем пользователя не появилось — вход, вероятно, не выполнен"


@allure.title("Смоук. Неверный пароль — остаёмся на форме, появляется ошибка")
def test_login_wrong_password(login_page):
    login_page.type_username(USERNAME)
    login_page.type_password("wrong_password_999")
    login_page.click_login()

    assert login_page.is_error_visible(), (
        "Сообщение об ошибке не появилось при неверном пароле"
    )
    error_text = login_page.get_error_text()
    assert "неверный" in error_text.lower(), (
        f"Текст ошибки не соответствует ожидаемому. Получено: '{error_text}'"
    )
