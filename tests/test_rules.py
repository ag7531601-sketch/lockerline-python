"""A compact policy table runs each refusal at both supported free windows."""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lockerline.app import create_app
from lockerline.clock import FixedClock, get_clock
from lockerline.settings import Settings

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "tests" / "rules.csv").open(newline="", encoding="utf-8") as source:
    RULES = list(csv.DictReader(source))


@pytest.mark.parametrize("rule", RULES, ids=[row["case"] for row in RULES])
@pytest.mark.parametrize("window", [48, 24], ids=["48-hours", "24-hours"])
def test_rule_table(tmp_path, rule, window):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / (rule["case"] + str(window) + ".db")).as_posix()}",
        seed_dir=str(ROOT / "seed"),
        free_window_hours=window,
    )
    clock = FixedClock(datetime(2026, 9, 25, 13, 10, tzinfo=timezone.utc))
    app = create_app(settings)
    app.dependency_overrides[get_clock] = lambda: clock
    expected_status = int(rule["status" + str(window)])
    expected_type = rule["type" + str(window)]

    with TestClient(app) as client:
        code = None
        for instruction in filter(None, rule["setup"].split(";")):
            parts = instruction.split()
            if parts[0] == "fill":
                size = parts[1]
                while True:
                    response = client.post("/drops", json={"size_class": size, "flat": "302"})
                    if response.status_code == 409:
                        break
                    assert response.status_code == 201, response.text
            elif parts[0] == "drop":
                code = client.post(
                    "/drops",
                    json={"size_class": "M", "flat": "302"},
                ).json()["code"]
            elif parts[0] == "pickup":
                response = client.post("/pickups", json={"code": code})
                assert response.status_code == 200, response.text
            elif parts[0] == "advance":
                clock.advance(hours=int(parts[1]))

        action = rule["action"].split()
        if action[0] == "drop":
            response = client.post(
                "/drops",
                json={"size_class": action[1], "flat": action[2]},
            )
        elif action[0] == "pickup":
            response = client.post("/pickups", json={"code": code or action[1]})
        else:
            raise AssertionError(f"Unknown rule-table action: {rule['action']}")

    assert response.status_code == expected_status, (rule["case"], response.text)
    if expected_type:
        assert response.json()["type"] == expected_type


def test_ui_rule_table_matches_csv():
    app_js = (ROOT / "lockerline" / "static" / "app.js").read_text(encoding="utf-8")
    match = re.search(r"var RULES = (\[.*?\]);", app_js, re.S)
    assert match, "The UI rule table is missing"
    assert json.loads(match.group(1)) == [
        [
            row[key]
            for key in (
                "case",
                "tag",
                "setup",
                "action",
                "status48",
                "type48",
                "status24",
                "type24",
            )
        ]
        for row in RULES
    ]


def test_settings_endpoint_reports_active_window(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'settings.db').as_posix()}",
        seed_dir=str(ROOT / "seed"),
        free_window_hours=24,
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/settings").json() == {
            "free_window_hours": 24,
            "sizes": ["S", "M", "L"],
        }