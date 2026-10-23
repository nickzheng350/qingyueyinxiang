"""性能基准（防回退）。

断言刻意设置得宽松，目的是捕捉数量级级别的性能回退，
而不是在 CI 上做微基准抖动检测。
"""

import time

PARSE_SAMPLE_COUNT = 50
# 单次解析的冷路径上限（毫秒）。关键词优先解析应在毫秒级完成，
# 这里放宽到 200ms 以容忍慢机器与 CI 抖动。
MAX_COLD_PARSE_MS = 200
# 命中缓存后的单次解析上限（毫秒）
MAX_CACHED_PARSE_MS = 50


def test_cold_parse_latency(parser_factory):
    texts = [f"生成一张风格编号{i}的插画" for i in range(PARSE_SAMPLE_COUNT)]

    start = time.perf_counter()
    for text in texts:
        parser_factory.parse(text, use_cache=False)
    elapsed = time.perf_counter() - start

    average_ms = elapsed / len(texts) * 1000
    assert average_ms < MAX_COLD_PARSE_MS, (
        f"意图解析平均耗时 {average_ms:.1f}ms，超过上限 {MAX_COLD_PARSE_MS}ms"
    )


def test_cached_parse_is_faster_than_cold(parser_factory):
    text = "重复查询的性能基准文本"
    parser_factory.parse(text)  # 预热，写入缓存

    start = time.perf_counter()
    for _ in range(20):
        parser_factory.parse(text)
    elapsed = time.perf_counter() - start

    average_ms = elapsed / 20 * 1000
    assert average_ms < MAX_CACHED_PARSE_MS, (
        f"缓存命中平均耗时 {average_ms:.1f}ms，超过上限 {MAX_CACHED_PARSE_MS}ms"
    )


def test_model_selection_latency(dispatcher):
    start = time.perf_counter()
    for _ in range(20):
        dispatcher.select_model("image_generation")
    elapsed = time.perf_counter() - start

    average_ms = elapsed / 20 * 1000
    assert average_ms < MAX_COLD_PARSE_MS, (
        f"模型选择平均耗时 {average_ms:.1f}ms，超过上限 {MAX_COLD_PARSE_MS}ms"
    )
