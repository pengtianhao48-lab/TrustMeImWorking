"""Basic unit tests for TrustMeImWorking core modules."""

import json
import os
import sys
import tempfile
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from trustmework.platforms import get_base_url, get_default_model, list_platforms
from trustmework import config as cfg_mod
from trustmework import state as st


# ── Platform tests ────────────────────────────────────────────────────────────

def test_list_platforms_nonempty():
    platforms = list_platforms()
    assert len(platforms) > 10


def test_get_base_url_openai():
    url = get_base_url("openai")
    assert "openai.com" in url


def test_get_base_url_custom_override():
    url = get_base_url("openai", custom_url="https://my-proxy.com/v1")
    assert url == "https://my-proxy.com/v1"


def test_get_default_model_deepseek():
    model = get_default_model("deepseek")
    assert model == "deepseek-reasoner"


def test_get_default_model_unknown_fallback():
    model = get_default_model("unknown_platform_xyz")
    assert model == "gpt-5.4"


# ── Config tests ──────────────────────────────────────────────────────────────

def test_generate_and_load_random_template():
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        path = f.name
    try:
        cfg_mod.generate_template(path, mode="random")
        raw = json.loads(open(path).read())
        assert raw["simulate_work"] is False
        assert "weekly_min" in raw
    finally:
        os.unlink(path)


def test_generate_and_load_work_template():
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        path = f.name
    try:
        cfg_mod.generate_template(path, mode="work")
        raw = json.loads(open(path).read())
        assert raw["simulate_work"] is True
        assert "job_description" in raw
        assert "work_start" in raw
    finally:
        os.unlink(path)


def test_load_valid_random_config():
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({
            "platform": "openai",
            "api_key": "sk-test",
            "weekly_min": 10000,
            "weekly_max": 20000,
            "simulate_work": False,
        }, f)
        path = f.name
    try:
        config = cfg_mod.load(path)
        assert config["api_key"] == "sk-test"
    finally:
        os.unlink(path)


def test_load_missing_api_key_raises():
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"weekly_min": 1000, "weekly_max": 2000}, f)
        path = f.name
    try:
        try:
            cfg_mod.load(path)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "api_key" in str(e)
    finally:
        os.unlink(path)


def test_load_weekly_min_gt_max_raises():
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump({"api_key": "sk-x", "weekly_min": 9000, "weekly_max": 1000, "simulate_work": False}, f)
        path = f.name
    try:
        try:
            cfg_mod.load(path)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "weekly_min" in str(e)
    finally:
        os.unlink(path)


# ── State tests ───────────────────────────────────────────────────────────────

def test_state_record_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.json")
        open(config_path, "w").write("{}")

        tz = datetime.timezone.utc
        state = st.load(config_path)
        assert st.today_consumed(state, tz) == 0

        st.record(config_path, state, 1234, tz)
        assert st.today_consumed(state, tz) == 1234

        st.record(config_path, state, 500, tz)
        assert st.today_consumed(state, tz) == 1734


def test_state_last_n_days():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.json")
        open(config_path, "w").write("{}")

        tz = datetime.timezone.utc
        state = st.load(config_path)
        days = st.last_n_days(state, tz, 7)
        assert len(days) == 7
        for date_str, val in days:
            assert val == 0
