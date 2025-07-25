import json
from pathlib import Path

FILE = Path("user_settings.json")

def load_settings():
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {}

def save_settings(data):
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def get_user_city(user_id):
    data = load_settings()
    return data.get(str(user_id), {}).get("city")

def set_user_city(user_id, city_id):
    data = load_settings()
    if str(user_id) not in data:
        data[str(user_id)] = {}
    data[str(user_id)]["city"] = city_id
    save_settings(data)
