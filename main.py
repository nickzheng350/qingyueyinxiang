#!/usr/bin/env python3
"""清悦印象 - 主入口文件"""

import argparse
import sys
import logging

from src.api.app import create_app


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="清悦印象 - 九头蛇生成式工作流平台")
    subparsers = parser.add_subparsers(title="命令", dest="command")

    api_parser = subparsers.add_parser("api", help="启动 API 服务")
    api_parser.add_argument("--host", default="0.0.0.0", help="绑定主机地址")
    api_parser.add_argument("--port", type=int, default=8000, help="API 服务端口")
    api_parser.add_argument("--reload", action="store_true", help="启用热重载")
    api_parser.add_argument("--log-level", default="INFO", help="日志级别")

    subparsers.add_parser("diagnose", help="系统诊断")
    subparsers.add_parser("repair", help="自我修复")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "api":
        setup_logging(args.log_level)
        logger = logging.getLogger("清悦印象")
        logger.info(f"启动 清悦印象 API 服务: {args.host}:{args.port}")

        import uvicorn

        if args.reload:
            uvicorn.run(
                "src.api.app:create_app",
                host=args.host,
                port=args.port,
                reload=True,
                factory=True,
            )
        else:
            app = create_app()
            uvicorn.run(app, host=args.host, port=args.port)

    elif args.command == "diagnose":
        setup_logging("DEBUG")
        print("=== 清悦印象 系统诊断 ===")
        print()

        from src.core.config import get_config
        config = get_config()
        print(f"项目根目录: {config.project_root}")
        print(f"全局配置: {'已加载' if config.global_config else '未找到'}")
        print(f"模型配置: {'已加载' if config.models_config else '未找到'}")
        print(f"API密钥配置: {'已加载' if config.api_keys_config else '未找到'}")
        print()

        from src.intent_parser.factory import IntentParserFactory
        factory = IntentParserFactory()
        parsers = factory.list_parsers()
        print(f"已注册解析器: {len(parsers)}")
        for p in parsers:
            print(f"  - {p['name']}: {p['model_info'].get('description', '')}")
        print()

        from src.prompt_engine.engine import PromptEngine
        engine = PromptEngine()
        styles = engine.list_styles()
        print(f"已加载风格模板: {len(styles)}")
        for s in styles:
            print(f"  - {s}")
        print()

        from src.model_dispatcher.dispatcher import ModelDispatcher
        dispatcher = ModelDispatcher()
        stats = dispatcher.get_statistics()
        print(f"已注册模型: {stats['total_models']}")
        print()

        from src.skills.skill_manager import SkillManager
        skill_mgr = SkillManager()
        skill_stats = skill_mgr.get_statistics()
        print(f"已安装技能: {skill_stats['total_skills']}")
        print()

        from src.task_engine import get_task_executor
        executor = get_task_executor()
        task_stats = executor.get_task_statistics()
        print(f"任务执行器: 运行中")
        print(f"  - 任务总数: {task_stats['total']}")
        print(f"  - 运行中: {task_stats['running']}")
        print(f"  - 已完成: {task_stats['completed']}")
        print()

        from src.cache import get_cache_manager
        cache_mgr = get_cache_manager()
        cache_stats = cache_mgr.get_all_stats()
        print(f"缓存管理器: 运行中")
        print(f"  - 命名空间数: {len(cache_stats)}")
        print()

        from src.monitoring import get_monitor
        monitor = get_monitor()
        health = monitor.get_health()
        print(f"监控系统: {health['status']}")
        print(f"  - 健康分数: {health['health_score']}/100")
        print(f"  - 运行时间: {health['uptime_formatted']}")
        print()

        from src.core.stability import get_stability_manager
        stability = get_stability_manager()
        print(f"系统健康分数: {stability.get_health_score()}/100")
        print()
        print("=== 诊断完成 ===")

    elif args.command == "repair":
        setup_logging("INFO")
        print("=== 清悦印象 自我修复 ===")
        print()

        import os
        import shutil
        from pathlib import Path

        project_root = Path(__file__).parent
        repaired = 0

        required_dirs = ["src", "src/core", "src/intent_parser", "src/prompt_engine",
                         "src/model_dispatcher", "src/skills", "src/api",
                         "src/task_engine", "src/persistence", "src/cache", "src/monitoring",
                         "config", "prompts", "skills", "skills/core", "skills/local"]
        for d in required_dirs:
            dir_path = project_root / d
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                (dir_path / "__init__.py").touch(exist_ok=True)
                print(f"  ✓ 创建缺失目录: {d}/")
                repaired += 1

        required_init_files = [
            "src/__init__.py", "src/core/__init__.py",
            "src/intent_parser/__init__.py", "src/prompt_engine/__init__.py",
            "src/model_dispatcher/__init__.py", "src/skills/__init__.py",
            "src/api/__init__.py", "src/task_engine/__init__.py",
            "src/persistence/__init__.py", "src/cache/__init__.py",
            "src/monitoring/__init__.py",
        ]
        for f in required_init_files:
            file_path = project_root / f
            if not file_path.exists():
                file_path.touch()
                print(f"  ✓ 创建缺失文件: {f}")
                repaired += 1

        pycache_dirs = list((project_root / "src").rglob("__pycache__")) + \
                       list((project_root / "scripts").rglob("__pycache__"))
        for cache_dir in pycache_dirs:
            shutil.rmtree(cache_dir, ignore_errors=True)
            print(f"  ✓ 清理缓存: {cache_dir.relative_to(project_root)}")
            repaired += 1

        env_file = project_root / ".env"
        env_example = project_root / ".env.example"
        if not env_file.exists() and env_example.exists():
            shutil.copy2(env_example, env_file)
            print(f"  ✓ 从 .env.example 创建 .env")
            repaired += 1

        try:
            from src.core.config import get_config
            config = get_config()
            print(f"  ✓ 配置加载正常")
        except Exception as e:
            print(f"  ✗ 配置加载异常: {e}")
            repaired += 1

        try:
            from src.intent_parser.factory import IntentParserFactory
            factory = IntentParserFactory()
            parsers = factory.list_parsers()
            print(f"  ✓ 解析器注册正常 ({len(parsers)} 个)")
        except Exception as e:
            print(f"  ✗ 解析器异常: {e}")
            repaired += 1

        try:
            from src.prompt_engine.engine import PromptEngine
            engine = PromptEngine()
            styles = engine.list_styles()
            print(f"  ✓ 提示词引擎正常 ({len(styles)} 个模板)")
        except Exception as e:
            print(f"  ✗ 提示词引擎异常: {e}")
            repaired += 1

        try:
            from src.model_dispatcher.dispatcher import ModelDispatcher
            dispatcher = ModelDispatcher()
            stats = dispatcher.get_statistics()
            print(f"  ✓ 模型调度器正常 ({stats['total_models']} 个模型)")
        except Exception as e:
            print(f"  ✗ 模型调度器异常: {e}")
            repaired += 1

        try:
            from src.core.stability import get_stability_manager
            stability = get_stability_manager()
            score = stability.get_health_score()
            print(f"  ✓ 健康分数: {score}/100")
        except Exception as e:
            print(f"  ✗ 稳定性管理器异常: {e}")
            repaired += 1

        print()
        if repaired == 0:
            print("✓ 系统完好，无需修复")
        else:
            print(f"✓ 修复完成，共处理 {repaired} 个问题")
        print()
        print("=== 修复完成 ===")


if __name__ == "__main__":
    main()
