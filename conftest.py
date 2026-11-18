import time
from datetime import datetime

import pytest
from selenium import webdriver

from config import BASE_URL, SESSION, TOKEN
from pages.schedule_api import ScheduleApi, ts


@pytest.fixture
def auth_cookies():
    return {"session_global": SESSION, "token_global": TOKEN}


@pytest.fixture
def api(auth_cookies):
    return ScheduleApi(BASE_URL, auth_cookies)


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    drv = webdriver.Chrome(options=options)
    try:
        drv.get("https://teachers.skyeng.ru/schedule")
        time.sleep(2)

        for cookie in (
            {"name": "session_global", "value": SESSION, "domain": ".skyeng.ru", "path": "/"},
            {"name": "token_global", "value": TOKEN, "domain": ".skyeng.ru", "path": "/"},
        ):
            drv.add_cookie(cookie)

        drv.get("https://teachers.skyeng.ru/schedule")
    except Exception:
        drv.quit()
        raise
    yield drv
    drv.quit()


@pytest.fixture
def make_event(api):
    """Создаёт событие через API; после теста подчищает созданное."""
    created = []  # <-- ВАЖНО: пустой список

    def _make(**overrides):
        params = {
            "title": f"autotest {datetime.now().strftime('%H%M%S%f')}",
            "start_at": ts(days=1, hour=10),
            "end_at": ts(days=1, hour=11),
        }
        params.update(overrides)
        
        resp = api.create_event(**params)
        print(">>>", resp.request.method, resp.request.url)
        
        assert resp.status_code == 200 and resp.json().get("data"), resp.text
        data = resp.json()["data"]
        payload = data.get("payload") or {}
        event = {
            "id": payload.get("id"),
            "eventId": data.get("eventId"),
            "startAt": params["start_at"],
            "endAt": params["end_at"],
            "title": params["title"],
            "description": params.get("description"),
        }
        created.append(event)
        return event

    yield _make

    for event in created:
        try:
            api.remove_event(event["id"], event["startAt"])
        except Exception:
            pass
