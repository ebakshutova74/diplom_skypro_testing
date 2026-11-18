import requests
from config import BASE_URL, SESSION, TOKEN

url = BASE_URL + "/v2/schedule/createPersonal"
print("URL:", url)

resp = requests.post(
    url,
json={
        "title": "проверка связи",
        "startAt": "2026-11-19T11:00:00+05:00",
        "endAt": "2026-11-19T12:00:00+05:00",
        "color": "#0000ff",
        "backgroundColor": "#0000ff",
    },
    cookies={"session_global": SESSION, "token_global": TOKEN},
    headers={"Content-Type": "application/json"},
)

print("Статус:", resp.status_code)
print("Ответ:", resp.text[:300])
