import os
import time

from selenium.webdriver.common.by import By


class CalendarPage:
    URL = "https://teachers.skyeng.ru/schedule"
    CARD_PERSONAL = (By.CSS_SELECTOR, "div.personal-container")

    def __init__(self, driver):
        self.driver = driver

    def _scan(self, title: str):
        cards = self.driver.find_elements(*self.CARD_PERSONAL)
        for card in cards:
            if title.lower() in card.text.lower():
                return card
        return None

    def find_card(self, title: str, timeout: int = 15):
        """Ищет карточку по вхождению названия, ожидая загрузки календаря."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            card = self._scan(title)
            if card:
                return card
            time.sleep(0.3)
        self._dump_artifacts(title)
        raise AssertionError(f"Событие '{title}' не найдено на календаре")

    def opacity(self, card) -> str:
        """Возвращает computed opacity карточки как строку ("1", "0.9"...)."""
        return self.driver.execute_script(
            "return getComputedStyle(arguments[0]).opacity;", card)

    def transform(self, card) -> str:
        """Возвращает CSS transform карточки ("none", "matrix(...)"...)."""
        return self.driver.execute_script(
            "return getComputedStyle(arguments[0]).transform;", card)

    def dom_index(self, title: str, timeout: int = 15) -> int:
        """Позиция карточки среди личных событий в DOM.
        Больше индекс — позже в разметке — выше при наложении."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            cards = self.driver.find_elements(*self.CARD_PERSONAL)
            for i, card in enumerate(cards):
                if title.lower() in card.text.lower():
                    return i
            time.sleep(0.3)
        self._dump_artifacts(title)
        raise AssertionError(f"Событие '{title}' не найдено на календаре")

    def _dump_artifacts(self, title: str):
        """Сохраняет скриншот и HTML страницы для диагностики."""
        try:
            os.makedirs("artifacts", exist_ok=True)
            safe = title.replace(" ", "_")
            self.driver.save_screenshot(f"artifacts/notfound_{safe}.png")
            with open(f"artifacts/notfound_{safe}.html", "w",
                      encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"\n[диагностика] скриншот и HTML сохранены в artifacts/, "
                  f"текущий URL: {self.driver.current_url}")
        except Exception as exc:  # noqa: BLE001
            print(f"[диагностика] не удалось сохранить артефакты: {exc}")
