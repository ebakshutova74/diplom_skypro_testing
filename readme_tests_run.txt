Запуск тестов API и UI расписания Skyeng Teachers

1. Требования: Python 3.13, установленный Allure CLI
   (scoop install allure или установщик с сайта allure).

2. Установить зависимости:
   pip install -r requirements.txt

3. Запуск всех тестов:
   pytest tests -v

4. Запуск с формированием отчёта Allure:
   pytest tests -v --alluredir=allure-results
   allure serve allure-results

5. Содержимое:
   config.py               - URL и куки авторизации (обновлять при 401)
   conftest.py             - фикстуры: куки, API-клиент, Selenium, создание событий
   pages/schedule_api.py   - API-клиент расписания (create/update/remove/events)
   pages/calendar_page.py  - локаторы карточек событий календаря
   tests/test_auth.py      - тесты авторизации (cookies session_global / token_global)
   tests/test_events.py    - позитивные и негативные тесты CRUD событий (P1-P11, N1-N6)
   tests/test_ui_priority.py - проверка FR02.01: AC2 и AC3 автотестами, AC1 blocked

Примечание: значения SESSION и TOKEN в config.py получены вручную из браузера
и со временем устаревают — при 401 обновите куки.
Примечание: UI-тесты открывают Chrome и требуют, чтобы календарь в браузере
и куки относились к одному аккаунту.
