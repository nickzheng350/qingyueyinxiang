#!/usr/bin/env python3
"""安全检查脚本 - 检测潜在的安全漏洞"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

SECURITY_PATTERNS = {
    "SQL_INJECTION": [
        (r'execute\s*\(\s*["\'].*?\+.*?["\']\s*\)', "字符串拼接 SQL 查询"),
        (r'query\s*\(\s*["\'].*?\+.*?["\']\s*\)', "字符串拼接查询"),
        (r'format\s*\(\s*["\'].*?\{.*?\}.*?["\']\s*,\s*.*?\)', "使用 format 拼接 SQL"),
        (r'%s.*%\s*\(', "使用 % 格式化 SQL"),
    ],
    "XSS": [
        (r'innerHTML\s*=\s*[^;]+', "直接设置 innerHTML"),
        (r'outerHTML\s*=\s*[^;]+', "直接设置 outerHTML"),
        (r'document\.write\s*\(', "使用 document.write"),
        (r'eval\s*\(', "使用 eval"),
    ],
    "HARD_CODED_SECRETS": [
        (r'(password|secret|api_key|token)\s*=\s*["\'][^"\']{10,}["\']', "硬编码密钥"),
        (r'(password|secret|api_key|token)\s*=\s*[a-zA-Z0-9+/=]{20,}', "硬编码密钥（Base64）"),
        (r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*', "硬编码 Bearer token"),
    ],
    "INSECURE_RANDOM": [
        (r'random\(\)', "使用不安全的 random()"),
        (r'math\.random\(\)', "使用不安全的 Math.random()"),
    ],
    "INSECURE_HASH": [
        (r'md5\s*\(', "使用不安全的 MD5"),
        (r'sha1\s*\(', "使用不安全的 SHA1"),
    ],
    "COMMAND_INJECTION": [
        (r'subprocess\.(call|run|Popen)\s*\(\s*["\'].*?\+.*?["\']', "命令注入风险"),
        (r'os\.system\s*\(\s*["\'].*?\+.*?["\']', "命令注入风险"),
        (r'os\.popen\s*\(\s*["\'].*?\+.*?["\']', "命令注入风险"),
    ],
    "PATH_TRAVERSAL": [
        (r'open\s*\(\s*["\'].*?\.\.\/', "路径遍历风险"),
        (r'open\s*\(\s*["\'].*?\.\.\\', "路径遍历风险"),
    ],
    "DEBUG_INFO": [
        (r'print\s*\(\s*.*?(password|secret|token|api_key)', "打印敏感信息"),
        (r'logger\.(debug|info)\s*\(\s*.*?(password|secret|token)', "记录敏感信息"),
    ],
}


def check_file(file_path: Path) -> List[Dict[str, str]]:
    """检查单个文件的安全问题"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception:
        return issues

    for category, patterns in SECURITY_PATTERNS.items():
        for pattern, description in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1].strip()

                try:
                    rel_path = str(file_path.relative_to(Path.cwd()))
                except ValueError:
                    rel_path = str(file_path)

                issues.append({
                    "file": rel_path,
                    "line": line_num,
                    "category": category,
                    "description": description,
                    "content": line_content[:100],
                    "severity": get_severity(category),
                })

    return issues


def get_severity(category: str) -> str:
    """获取问题严重程度"""
    high_severity = ["HARD_CODED_SECRETS", "SQL_INJECTION", "COMMAND_INJECTION"]
    medium_severity = ["XSS", "PATH_TRAVERSAL", "INSECURE_HASH"]

    if category in high_severity:
        return "HIGH"
    elif category in medium_severity:
        return "MEDIUM"
    else:
        return "LOW"


def check_gitignore() -> List[str]:
    """检查 .gitignore 配置"""
    issues = []

    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        issues.append(".gitignore 文件不存在")
        return issues

    with open(gitignore_path, 'r') as f:
        content = f.read()

    required_patterns = [
        ".env",
        "*.key",
        "*.pem",
        "secrets/",
        "*.log",
        "__pycache__",
        ".venv/",
    ]

    for pattern in required_patterns:
        if pattern not in content:
            issues.append(f".gitignore 缺少: {pattern}")

    return issues


def check_dependencies() -> List[Dict[str, str]]:
    """检查依赖项安全性"""
    issues = []

    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        return issues

    with open(requirements_path, 'r') as f:
        lines = f.readlines()

    vulnerable_packages = {
        "flask": "建议使用 FastAPI 替代",
        "django": "建议使用 FastAPI 替代",
        "requests": "建议使用 httpx",
        "urllib3": "建议使用 httpx",
    }

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        package = line.split('>=')[0].split('==')[0].split('~=')[0].strip().lower()

        if package in vulnerable_packages:
            issues.append({
                "package": package,
                "recommendation": vulnerable_packages[package],
            })

    return issues


def check_file_permissions() -> List[Dict[str, str]]:
    """检查文件权限"""
    issues = []

    sensitive_files = [
        ".env",
        "config/secrets.json",
        "secrets/",
    ]

    for file_pattern in sensitive_files:
        for file_path in Path('.').rglob(file_pattern):
            if file_path.is_file():
                stat = file_path.stat()
                mode = oct(stat.st_mode)[-3:]
                if mode != '600' and mode != '400':
                    issues.append({
                        "file": str(file_path),
                        "current_mode": mode,
                        "recommended_mode": "600",
                    })

    return issues


def main():
    """主函数"""
    print("=" * 60)
    print("HydraFlow AI - 安全检查工具")
    print("=" * 60)
    print()

    all_issues = []

    print("📁 检查代码文件...")
    python_files = list(Path('src').rglob('*.py'))

    for file_path in python_files:
        issues = check_file(file_path)
        all_issues.extend(issues)

    if all_issues:
        print(f"⚠️  发现 {len(all_issues)} 个潜在安全问题")
        print()

        for issue in all_issues:
            print(f"  [{issue['severity']}] {issue['category']}")
            print(f"    文件: {issue['file']}:{issue['line']}")
            print(f"    描述: {issue['description']}")
            print(f"    内容: {issue['content']}")
            print()
    else:
        print("✅ 未发现代码安全问题")
    print()

    print("📝 检查 .gitignore 配置...")
    gitignore_issues = check_gitignore()
    if gitignore_issues:
        print(f"⚠️  发现 {len(gitignore_issues)} 个 .gitignore 问题:")
        for issue in gitignore_issues:
            print(f"  - {issue}")
    else:
        print("✅ .gitignore 配置正确")
    print()

    print("📦 检查依赖项...")
    dep_issues = check_dependencies()
    if dep_issues:
        print(f"⚠️  发现 {len(dep_issues)} 个依赖项建议:")
        for issue in dep_issues:
            print(f"  - {issue['package']}: {issue['recommendation']}")
    else:
        print("✅ 依赖项检查通过")
    print()

    print("🔒 检查文件权限...")
    perm_issues = check_file_permissions()
    if perm_issues:
        print(f"⚠️  发现 {len(perm_issues)} 个文件权限问题:")
        for issue in perm_issues:
            print(f"  - {issue['file']}: 当前权限 {issue['current_mode']}, 建议改为 {issue['recommended_mode']}")
    else:
        print("✅ 文件权限检查通过")
    print()

    total_issues = len(all_issues) + len(gitignore_issues) + len(dep_issues) + len(perm_issues)

    print("=" * 60)
    if total_issues == 0:
        print("✅ 安全检查通过！未发现严重问题。")
    else:
        print(f"⚠️  共发现 {total_issues} 个问题，请及时修复。")
    print("=" * 60)

    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
