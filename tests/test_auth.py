import datetime as dt
import logging
import os

import allure
import pytest
import requests

pytestmark = pytest.mark.api

from config import SESSION, TOKEN

log = logging.getLogger(__name__)

SESSION = os.environ.get("SKY_SESSION") or SESSION
TOKEN = os.environ.get("SKY_TOKEN") or TOKEN

BASE_URL = "https://api-teachers.skyeng.ru/api/v2/schedule/event"


@allure.step("GET /api/v2/schedule/event")
def get_schedule(cookies=None) -> requests.Response:
    """Окно расписания: с 02:00 сегодня до 01:59:59 через неделю (UTC+5)."""
    tz = dt.timezone(dt.timedelta(hours=5))
    start = dt.datetime.now(tz).replace(hour=2, minute=0, second=0, microsecond=0)
    end = start + dt.timedelta(days=7) - dt.timedelta(seconds=1)
    params = [
        ("from", start.isoformat()),
        ("till", end.isoformat()),
        ("onlyTypes[]", "event"),
        ("onlyTypes[]", "slot"),
    ]
    resp = requests.get(BASE_URL, params=params, cookies=cookies or {}, timeout=10)
    allure.attach(f"HTTP {resp.status_code}\n{resp.text[:2000]}",
                  "Ответ сервера", allure.attachment_type.TEXT)
    log.info("HTTP %s: %.300s", resp.status_code, resp.text)
    return resp


@allure.title("Валидные куки — расписание отдаётся (200)")
def test_full_auth():
    resp = get_schedule({"session_global": SESSION, "token_global": TOKEN})
    assert resp.status_code == 200, \
        f"Ожидали 200, получили {resp.status_code}: {resp.text[:300]}"
    data = resp.json()
    assert "data" in data, f"Нет ключа data, верхнеуровневые ключи: {list(data)}"
    assert data["errors"] is None, f"Ошибки в ответе: {data['errors']}"


@allure.title("Фейковый токен при настоящей сессии — доступ запрещён")
@pytest.mark.xfail(reason="Баг BR-001: token_global не валидируется, сервер отвечает 200")
def test_fake_token():
    resp = get_schedule({"session_global": SESSION, "token_global": "fake_token_12345"})
    assert resp.status_code in (400, 401), \
        f"Ожидали 400/401, получили {resp.status_code}"


@allure.title("Фейковая session_global при настоящем токене — доступ запрещён")
def test_fake_session():
    resp = get_schedule({"session_global": "fake_session_999", "token_global": TOKEN})
    assert resp.status_code in (400, 401), \
        f"Ожидали 400/401, получили {resp.status_code}"


@pytest.mark.parametrize(
    "cookies, expected",
    [
        pytest.param({"token_global": TOKEN}, 401, id="только token_global"),
        pytest.param(None, 401, id="без кук вообще"),
        pytest.param({"session_global": "", "token_global": ""}, 401, id="пустые значения кук"),
    ],
)
@allure.title("Запрос без валидных кук — доступ запрещён ({id})")
def test_access_denied(cookies, expected):
    resp = get_schedule(cookies)
    assert resp.status_code == expected, \
        f"Ожидали {expected}, получили {resp.status_code}: {resp.text[:300]}"
