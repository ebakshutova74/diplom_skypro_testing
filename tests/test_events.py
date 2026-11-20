import time
from datetime import datetime, timedelta

import allure
import pytest

pytestmark = pytest.mark.api

from pages.schedule_api import TZ, ts


def _assert_error(resp):
    assert resp.json().get("data") is None and resp.json().get("errors"), (
        f"ожидался массив errors с data: null, получено: {resp.text}")
    return resp.json()["errors"]


def _assert_validation_error(resp):
    errors = _assert_error(resp)
    assert all(e.get("error", {}).get("code") == "not_valid" for e in errors), resp.text


def _assert_domain_error(resp):
    errors = _assert_error(resp)
    assert any(e.get("error", {}).get("code") == "domain_error" for e in errors), resp.text


def _field(event: dict, field: str):
    """Достаёт поле события независимо от того, где оно лежит в структуре."""
    payload = event.get("payload") or {}
    inner = payload.get("payload") or {}
    return event.get(field) or inner.get(field) or payload.get(field)


def _ids(api, resp) -> list:
    return [str(_field(e, "id")) for e in api.parse_events(resp)]


def _titles(api, resp) -> list:
    return [str(_field(e, "title") or "") for e in api.parse_events(resp)]


# ===================== Позитивные =====================

@allure.title("P1. Создание события со всеми заполненными полями")
def test_create_full_fields(api, make_event):
    event = make_event(title="Полное событие", description="Описание автотеста",
                       start_at=ts(days=1, hour=9), end_at=ts(days=1, hour=10))
    resp = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    assert resp.status_code == 200
    assert str(event["id"]) in _ids(api, resp)


@allure.title("P2. Создание события только с обязательными полями")
def test_create_required_only(api, make_event):
    event = make_event(title="Только обязательные",
                       start_at=ts(days=1, hour=11),
                       end_at=ts(days=1, hour=12))
    resp = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    assert resp.status_code == 200
    assert str(event["id"]) in _ids(api, resp)


@allure.title("P3. Событие длительностью 5 минут (мин. граница по ТЗ)")
def test_create_5_minutes(api, make_event):
    event = make_event(title="Пять минут",
                       start_at=ts(days=1, hour=10, minute=0),
                       end_at=ts(days=1, hour=10, minute=5))
    resp = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    assert resp.status_code == 200
    assert str(event["id"]) in _ids(api, resp)


@allure.title("P4. Событие 23 ч 59 мин в пределах суток (макс. граница по ТЗ)")
def test_create_23h59(api, make_event):
    event = make_event(title="Почти сутки",
                       start_at=ts(days=1, hour=0, minute=0),
                       end_at=ts(days=1, hour=23, minute=59))
    resp = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    assert resp.status_code == 200
    assert str(event["id"]) in _ids(api, resp)


@allure.title("P5. Название в 1 символ (мин. граница названия)")
def test_create_single_char_title(api, make_event):
    event = make_event(title="Я")
    resp = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    assert resp.status_code == 200
    assert str(event["id"]) in _ids(api, resp)


@allure.title("P6. Редактирование цвета события")
def test_edit_color(api, make_event):
    event = make_event(title="Смена цвета")
    resp = api.update_event_by_ref(event, background_color="#FF0000",
                                   color="#FFFFFF")
    assert resp.status_code == 200
    payload = (resp.json().get("data") or {}).get("payload") or {}
    inner = payload.get("payload") or payload
    assert (inner.get("backgroundColor") or "").upper() == "#FF0000"


@allure.title("P7. Редактирование названия события")
def test_edit_title(api, make_event):
    event = make_event(title="Старое название")
    resp = api.update_event_by_ref(event, title="Новое название")
    assert resp.status_code == 200
    list_resp = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    assert "Новое название" in _titles(api, list_resp)


@allure.title("P8. Редактирование даты и времени начала события")
def test_edit_start_time(api, make_event):
    event = make_event(title="Перенос времени",
                       start_at=ts(days=1, hour=9), end_at=ts(days=1, hour=10))
    resp = api.update_event_by_ref(event, start_at=ts(days=2, hour=15),
                                   end_at=ts(days=2, hour=16))
    assert resp.status_code == 200
    resp_list = api.get_events(ts(days=2, hour=0), ts(days=2, hour=23, minute=59))
    assert str(event["id"]) in _ids(api, resp_list)


@allure.title("P9. Список событий на месяц; NFR2: ответ не дольше 3 секунд")
def test_month_list_performance(api):
    now = datetime.now(TZ)
    first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    nxt = (first.replace(day=28) + timedelta(days=7)).replace(day=1)
    till = nxt - timedelta(seconds=1)
    start = time.perf_counter()
    resp = api.get_events(first.isoformat(), till.isoformat())
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200
    assert elapsed <= 3, f"NFR2 нарушено: список за месяц грузится {elapsed:.2f} с"


@allure.title("P10. Фильтр onlyTypes по типу созданного события")
def test_only_types(api, make_event):
    event = make_event(title="Фильтр onlyTypes",
                       start_at=ts(days=1, hour=8), end_at=ts(days=1, hour=9))
    base = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    own = next((e for e in api.parse_events(base)
                if str(_field(e, "id")) == str(event["id"])), None)
    assert own is not None, "созданное событие не найдено в базовом списке"
    etype = _field(own, "type") or own.get("type")
    if etype is None:
        pytest.skip("В ответе events нет поля type — названия типов нужно уточнить")
    filtered = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59),
                              only_types=[etype])
    assert filtered.status_code == 200
    assert all((_field(e, "type") or e.get("type")) == etype
               for e in api.parse_events(filtered))


@allure.title("P11. Удаление созданного события")
def test_delete_event(api, make_event):
    event = make_event(title="На удаление")
    resp = api.remove_event(event["id"], event["startAt"])
    assert resp.status_code == 200
    list_resp = api.get_events(ts(days=1, hour=0), ts(days=1, hour=23, minute=59))
    assert str(event["id"]) not in _ids(api, list_resp)


# ===================== Негативные =====================

@allure.title("N1. Создание события с пустым названием")
def test_create_empty_title(api):
    resp = api.create_event(title="",
                            start_at=ts(days=1, hour=9),
                            end_at=ts(days=1, hour=10))
    _assert_validation_error(resp)


@allure.title("N2. Создание события с пустым полем даты и времени окончания")
def test_create_empty_end_at(api):
    resp = api.create_event(title="Без конца",
                            start_at=ts(days=1, hour=9),
                            end_at="")
    _assert_validation_error(resp)


@allure.title("N3. Событие с переходом на другой день")
@pytest.mark.xfail(reason="Баг BR-002: сервер принимает событие через полночь (200), "
                          "хотя по ТЗ оно не может начинаться и заканчиваться в разные дни",
                   strict=False)
def test_create_crossing_midnight(api):
    resp = api.create_event(title="Через полночь",
                            start_at=ts(days=1, hour=23, minute=30),
                            end_at=ts(days=2, hour=0, minute=30))
    _assert_validation_error(resp)


@allure.title("N4. Редактирование названия в 41 символ (верхняя граница — 40)")
def test_edit_title_41_chars(api, make_event):
    event = make_event(title="Длинное название")
    resp = api.update_event_by_ref(event, title="Б" * 41)
    _assert_validation_error(resp)


@allure.title("N5. Редактирование несуществующего события")
def test_update_nonexistent(api):
    resp = api.update_event(event_id=999999999,
                            old_start_at=ts(days=1, hour=10),
                            title="Призрак",
                            start_at=ts(days=1, hour=10),
                            end_at=ts(days=1, hour=11))
    _assert_domain_error(resp)


@allure.title("N6. Удаление несуществующего события")
def test_remove_nonexistent(api):
    resp = api.remove_event(999999999, ts(days=1, hour=10))
    _assert_domain_error(resp)
