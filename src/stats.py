import os
import json


def save_data(data):
    try:
        os.mkdir(os.path.join(os.getenv("APPDATA"), "vry"))
    except FileExistsError:
        pass
    try:
        with open(os.path.join(os.getenv("APPDATA"), "vry/stats.json")) as f:
            original_data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        original_data = {}

    updated_data = original_data.copy()
    for puuid in data.keys():
        if not original_data.get(puuid):
            updated_data.update({puuid: [data[puuid]]})
        else:
            updated_data[puuid].append(data[puuid])

    with open(os.path.join(os.getenv("APPDATA"), "vry/stats.json"), "w") as f:
        json.dump(updated_data, f)


def read_data():
    try:
        with open(os.path.join(os.getenv("APPDATA"), "vry/stats.json")) as f:
            return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


def convert_time(s):
    s = int(s)
    if s < 60:
        if s == 1:
            return f"{s} second"
        else:
            return f"{s} seconds"
    elif s < 3600:
        if s // 60 == 1:
            return f"{s // 60} minute"
        else:
            return f"{s // 60} minutes"
    elif s < 86400:
        if s // 3600 == 1:
            return f"{s // 3600} hours"
        else:
            return f"{s // 3600} hours"
    else:
        if s // 86400 == 1:
            return f"{s // 86400} days"
        else:
            return f"{s // 86400} days"
