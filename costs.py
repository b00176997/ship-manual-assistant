"""Tracks how much was spent on Claude answers, totalled per day.
Stored in a small JSON file so it survives restarts."""
import json
import datetime
import config

LOG_FILE = config.BASE_DIR / "usage_log.json"


def _load():
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _today_key():
    return datetime.date.today().isoformat()


def record(cost_usd, input_tokens, output_tokens):
    """Add one query's usage to today's running total."""
    data = _load()
    day = _today_key()
    d = data.get(day, {"cost_usd": 0.0, "input": 0, "output": 0, "queries": 0})
    d["cost_usd"] = round(d["cost_usd"] + cost_usd, 6)
    d["input"] += input_tokens
    d["output"] += output_tokens
    d["queries"] += 1
    data[day] = d
    try:
        LOG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass
    return d


def today():
    """Today's totals (zeros if nothing spent yet)."""
    return _load().get(
        _today_key(), {"cost_usd": 0.0, "input": 0, "output": 0, "queries": 0}
    )
