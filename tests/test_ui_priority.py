import allure
import pytest

from config import UI_URL
from pages.calendar_page import CalendarPage
from pages.schedule_api import ts


@allure.title("AC1. Урок отображается поверх личного события")
@pytest.mark.skip(reason="Создание уроков недоступно в тестовой песочнице — "
                         "кейс задокументирован как blocked (BR-таблица UI)")
def test_ac1_lesson_over_event():
    """Метод проверки подготовлен (как в AC2), но функционал уроков
    в песочнице отсутствует."""


@allure.title("AC2. Позже созданное событие отображается поверх ранее созданного")
def test_ac2_created_later_on_top(driver, api, make_event):
    make_event(title="AC2 ранее",
               start_at=ts(days=0, hour=22, minute=0),
               end_at=ts(days=0, hour=23, minute=0))
    make_event(title="AC2 позже",
               start_at=ts(days=0, hour=22, minute=30),
               end_at=ts(days=0, hour=23, minute=30))
    driver.get(UI_URL)
    page = CalendarPage(driver)
    assert page.dom_index("AC2 позже") > page.dom_index("AC2 ранее")


@pytest.mark.xfail(reason="Гипотеза не подтвердилась: порядок в DOM определяется не временем создания — расхождение с AC2, см. отчёт")
def test_ac2_created_later_starts_earlier(driver, api, make_event):
    """Контроль гипотезы: порядок в DOM определяется временем создания,
    а не временем начала события. Если тест упадёт — расхождение с AC2."""
    make_event(title="AC2К раннее",
               start_at=ts(days=0, hour=20, minute=0),
               end_at=ts(days=0, hour=21, minute=0))
    make_event(title="AC2К позднее",
               start_at=ts(days=0, hour=19, minute=0),
               end_at=ts(days=0, hour=20, minute=30))
    driver.get(UI_URL)
    page = CalendarPage(driver)
    assert page.dom_index("AC2К позднее") > page.dom_index("AC2К раннее")


@allure.title("AC2. После изменения приоритет переходит к изменённому событию")
@pytest.mark.xfail(reason="Баг BR-002: изменение события не поднимает его поверх "
                          "созданного позже, порядок остаётся по времени создания")
def test_ac2_edited_on_top(driver, api, make_event):
    first = make_event(title="AC2П изменяемое",
                       start_at=ts(days=0, hour=21, minute=0),
                       end_at=ts(days=0, hour=22, minute=0))
    make_event(title="AC2П неизменяемое",
               start_at=ts(days=0, hour=21, minute=30),
               end_at=ts(days=0, hour=22, minute=30))
    driver.get(UI_URL)
    page = CalendarPage(driver)
    assert page.dom_index("AC2П изменяемое") < page.dom_index("AC2П неизменяемое")

    api.update_event_by_ref(first, title="AC2П изменяемое (правка)")
    driver.refresh()
    # Убеждаемся, что правка реально применилась и карточка переименовалась
    page.find_card("AC2П изменяемое (правка)")
    assert page.dom_index("AC2П изменяемое (правка)") > page.dom_index("AC2П неизменяемое"), (
        "Правка применена, но изменённое событие осталось ниже созданного позже")


@allure.title("AC3. Наложение не делает текст событий нечитаемым")
def test_ac3_text_readable(driver, make_event):
    make_event(title="AC3 первое",
               start_at=ts(days=0, hour=23, minute=0),
               end_at=ts(days=0, hour=23, minute=40))
    make_event(title="AC3 второе",
               start_at=ts(days=0, hour=23, minute=20),
               end_at=ts(days=0, hour=23, minute=59))
    driver.get(UI_URL)
    page = CalendarPage(driver)
    for title in ("AC3 первое", "AC3 второе"):
        card = page.find_card(title)
        assert page.opacity(card) == "1", (
            f"У '{title}' полупрозрачность: {page.opacity(card)}")
        transform = page.transform(card)
        assert transform in ("none", "matrix(1, 0, 0, 1, 0, 0)"), (
            f"У '{title}' есть смещение: {transform}")
