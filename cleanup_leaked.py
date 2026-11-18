"""Разовая очистка событий, оставшихся от упавших тестов."""
from config import BASE_URL, SESSION, TOKEN
from pages.schedule_api import ScheduleApi, ts

TITLES = ("Полное событие", "Только обязательные", "Пять минут", "Почти сутки",
          "Я", "Смена цвета", "Старое название", "Перенос времени",
          "Фильтр onlyTypes", "На удаление", "Через полночь", "autotest",
          "AC2", "AC2П", "AC3")

api = ScheduleApi(BASE_URL, {"session_global": SESSION, "token_global": TOKEN})

# Неделя назад (чтобы поймать утечки старых прогонов) ... послезавтра
for days in range(-7, 3):
    resp = api.get_events(ts(days=days, hour=0), ts(days=days, hour=23, minute=59))
    for e in api.parse_events(resp):
        payload = e.get("payload") or {}
        inner = payload.get("payload") or {}
        title = inner.get("title") or e.get("title") or ""
        if any(t in title for t in TITLES):
            ev_id = payload.get("id") or e.get("id")
            start = e.get("startAt") or payload.get("startAt")
            #r = api.remove_event(ev_id, start)
            print(days, title, ev_id, "->", r.status_code)
