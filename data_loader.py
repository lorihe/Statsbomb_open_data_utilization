from pathlib import Path
from typing import Any, Dict, List

import orjson
import requests

EVENTS_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{}.json"
)

_EVENTS_DISK_DIR = Path(__file__).resolve().parent / ".cache" / "statsbomb_events"

_events_cache: Dict[int, List[Any]] = {}


def load_json_from_url(url: str, timeout: int = 60) -> object:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return orjson.loads(response.content)


def get_match_events(match_id: int) -> List[Any]:
    if match_id in _events_cache:
        return _events_cache[match_id]

    path = _EVENTS_DISK_DIR / f"{match_id}.json"
    if path.is_file():
        data = orjson.loads(path.read_bytes())
        _events_cache[match_id] = data
        return data

    url = EVENTS_URL_TEMPLATE.format(match_id)
    data = load_json_from_url(url)
    _events_cache[match_id] = data
    try:
        _EVENTS_DISK_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(data))
    except OSError:
        pass
    return data
