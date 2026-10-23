"""代码质量门禁。

目的不是一次性清零技术债，而是**防止继续恶化**：
新增的裸 except / 宽泛 except 会直接让 CI 失败，
存量问题随重构逐步下降时只需调低下面的基线。
"""

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# 基线：随重构推进只允许下调，不允许上调
# 68 = 2026-10-23 实测值（已修复 core/pool.py 的静默 pass）
MAX_BROAD_EXCEPTS = 68
MAX_BARE_EXCEPTS = 0

BROAD_EXCEPTION_NAMES = {"Exception", "BaseException"}


def iter_python_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def collect_exception_handlers(root: Path) -> tuple[list[str], list[str]]:
    """返回 (宽泛异常列表, 裸 except 列表)，元素为 `相对路径:行号`"""
    broad: list[str] = []
    bare: list[str] = []

    for path in iter_python_files(root):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            location = f"{relative}:{node.lineno}"
            if node.type is None:
                bare.append(location)
            elif isinstance(node.type, ast.Name) and node.type.id in BROAD_EXCEPTION_NAMES:
                broad.append(location)

    return broad, bare


def test_no_bare_except():
    _, bare = collect_exception_handlers(SRC_DIR)
    assert not bare, f"存在裸 except（会吞掉 SystemExit/KeyboardInterrupt）: {bare}"


def test_broad_except_does_not_regress():
    broad, _ = collect_exception_handlers(SRC_DIR)
    assert len(broad) <= MAX_BROAD_EXCEPTS, (
        f"宽泛异常捕获 {len(broad)} 处，已超过基线 {MAX_BROAD_EXCEPTS}。"
        f"请使用 src/core/exceptions.py 中的具体异常类型。\n"
        + "\n".join(f"  - {item}" for item in broad[:20])
    )
