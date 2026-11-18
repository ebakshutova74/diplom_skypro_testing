import requests
from datetime import datetime, timedelta, timezone


class ScheduleApi:
    """Клиент API расписания Skyeng Teachers."""

    def __init__(self, base_url: str, cookies: dict):
        self.base_url = base_url.rstrip("/")
        self.cookies = cookies

   
    def _post(self, path: str, body: dict) -> requests.Response:
        print(f"\n>>> POST {self.base_url}{path}")
        return requests.post(
            f"{self.base_url}{path}",
            json=body,
            cookies=self.cookies,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

    # ---------- Расписание ----------

    def get_events(self, from_dt: str, till_dt: str, only_types=None):
        body = {"from": from_dt, "till": till_dt}
        if only_types is not None:
            body["onlyTypes"] = only_types
        return self._post("/v2/schedule/events", body)

    @staticmethod
    def parse_events(resp: requests.Response) -> list:
        """Достаёт список событий из ответа независимо от структуры data."""
        data = resp.json().get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("items", "events", "list"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    # ---------- Создание ----------

    def create_event(self, title, start_at, end_at, **extra):
        payload = {
            "title": title,
            "startAt": start_at,
            "endAt": end_at,
            "color": "#0000ff",
            "backgroundColor": "#0000ff",
        }
        payload.update(extra)
        return self._post("/v2/schedule/createPersonal", payload)

    # ---------- Изменение ----------

    def update_event(self, event_id, old_start_at, title, start_at, end_at,
                     background_color="#FFF7C7", color="#FAC641",
                     description=None):
        body = {
            "id": event_id,
            "oldStartAt": old_start_at,
            "title": title,
            "startAt": start_at,
            "endAt": end_at,
            "backgroundColor": background_color,
            "color": color,
        }
        if description is not None:
            body["description"] = description
        return self._post("/v2/schedule/updatePersonal", body)

    def update_event_by_ref(self, event: dict, **changes) -> requests.Response:
        """Обновляет событие и синхронизирует словарь-ссылку.
        id может смениться после изменения: сначала пробуем взять его
        из ответа, если там его нет — перечитываем список и ищем событие
        по названию и точному времени старта."""
        merged = {
            "title": event.get("title", "Событие"),
            "description": event.get("description"),
            "start_at": event["startAt"],
            "end_at": event["endAt"],
            "background_color": "#FFF7C7",
            "color": "#FAC641",
        }
        merged.update(changes)
        resp = self.update_event(
            event_id=event["id"],
            old_start_at=event["startAt"],
            title=merged["title"],
            start_at=merged["start_at"],
            end_at=merged["end_at"],
            background_color=merged["background_color"],
            color=merged["color"],
            description=merged["description"],
        )
        if resp.status_code != 200:
            return resp

        data = resp.json().get("data") or {}
        payload = data.get("payload") or {}
        inner = payload.get("payload") or payload
        new_id = inner.get("id")
        if new_id is None:
            # id в ответе нет — ищем событие в списке дня по названию
            day = merged["start_at"][:10]
            listing = self.get_events(f"{day}T00:00:00+05:00",
                                      f"{day}T23:59:59+05:00")
            candidates = [
                e for e in self.parse_events(listing)
                if ((e.get("payload") or {}).get("payload")
                    or e.get("payload") or e).get("title") == merged["title"]
            ]
            if len(candidates) == 1:
                e = candidates[0]
                ep = e.get("payload") or {}
                new_id = ((ep.get("payload") or {}).get("id")
                          or ep.get("id") or e.get("id"))
        if new_id is not None:
            event["id"] = new_id
        event["startAt"] = merged["start_at"]
        event["endAt"] = merged["end_at"]
        event["title"] = merged["title"]
        return resp


    # ---------- Удаление ----------

    def remove_event(self, event_id, start_at):
        return self._post("/v2/schedule/removePersonal",
                          {"id": event_id, "startAt": start_at})


# ---------- Утилиты времени ----------

# Пояс пользователя (+05:00) — чтобы события попадали в текущую неделю
# интерфейса. В примерах документации +03:00, но валиден любой ISO 8601.
TZ = timezone(timedelta(hours=5))


def ts(days=0, hour=10, minute=0) -> str:
    """ISO-строка: указанное время, смещённое на days дней от сегодня."""
    base = datetime.now(TZ) + timedelta(days=days)
    return base.replace(hour=hour, minute=minute, second=0,
                        microsecond=0).isoformat()


def soon_times(offset_min=30, duration_min=30):
    """Пара (startAt, endAt) в ближайшем будущем — для UI-тестов.
    Начало: через offset_min минут от сейчас, округлено вверх до 5 минут."""
    base = (datetime.now(TZ) + timedelta(minutes=offset_min)).replace(
        second=0, microsecond=0)
    base += timedelta(minutes=(5 - base.minute % 5) % 5)
    return base.isoformat(), (base + timedelta(minutes=duration_min)).isoformat()
