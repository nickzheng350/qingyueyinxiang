"""结构化日志模块测试"""

import asyncio
import io
import json
import logging
import sys

from src.core.logging import (
    JSONFormatter,
    RequestIdFilter,
    TextFormatter,
    bind_request_id,
    get_logger,
    get_request_id,
    setup_logging,
)


def make_record(message: str = "hello", request_id: str | None = None) -> logging.LogRecord:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, message, None, None)
    if request_id is not None:
        record.request_id = request_id
    return record


def test_json_formatter_outputs_valid_json():
    payload = json.loads(JSONFormatter().format(make_record()))
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test"
    assert "timestamp" in payload


def test_json_formatter_includes_request_id():
    payload = json.loads(JSONFormatter().format(make_record(request_id="req-1")))
    assert payload["request_id"] == "req-1"


def test_json_formatter_omits_missing_request_id():
    payload = json.loads(JSONFormatter().format(make_record()))
    assert "request_id" not in payload


def test_json_formatter_includes_exception_detail():
    try:
        raise ValueError("boom")
    except ValueError:
        record = make_record()
        record.exc_info = sys.exc_info()

    payload = json.loads(JSONFormatter().format(record))
    assert payload["exception"]["type"] == "ValueError"
    assert payload["exception"]["message"] == "boom"
    assert payload["exception"]["traceback"]


def test_text_formatter_prefixes_request_id():
    formatted = TextFormatter().format(make_record(request_id="req-9"))
    assert "[req-9]" in formatted
    assert "hello" in formatted


def test_request_id_filter_injects_context_value():
    bind_request_id("req-ctx")
    try:
        record = make_record()
        assert RequestIdFilter().filter(record) is True
        assert record.request_id == "req-ctx"
    finally:
        bind_request_id(None)


def test_bind_and_read_request_id():
    bind_request_id("abc")
    assert get_request_id() == "abc"
    bind_request_id(None)
    assert get_request_id() is None


def test_setup_logging_emits_json_to_stream():
    original = sys.stdout
    buffer = io.StringIO()
    try:
        sys.stdout = buffer
        setup_logging("INFO", json_format=True)
        get_logger("hydraflow.test").info("结构化日志测试")
    finally:
        sys.stdout = original

    last_line = buffer.getvalue().strip().splitlines()[-1]
    payload = json.loads(last_line)
    assert payload["message"] == "结构化日志测试"
    assert payload["logger"] == "hydraflow.test"


async def test_request_id_isolated_between_tasks():
    """并发任务之间的 request_id 不应互相串扰"""
    observed: dict[str, str | None] = {}

    async def worker(name: str, request_id: str) -> None:
        bind_request_id(request_id)
        await asyncio.sleep(0)
        observed[name] = get_request_id()

    await asyncio.gather(worker("a", "req-a"), worker("b", "req-b"))
    assert observed == {"a": "req-a", "b": "req-b"}

    bind_request_id(None)
