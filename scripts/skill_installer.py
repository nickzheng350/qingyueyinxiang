#!/usr/bin/env python3
"""
HydraFlow AI 技能安装工具
支持本地安装和市场安装两种方式
"""

import argparse
import sys
import os
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.skills.skill_manager import SkillManager

def setup_utf8_output():
    """设置 UTF-8 输出编码，解决 Windows 终端 emoji 显示问题"""
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

setup_utf8_output()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    HydraFlow AI 技能安装工具                     ║
║           Skill Installation Tool for HydraFlow AI              ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def list_categories(manager):
    """列出所有分类"""
    print("\n📋 可用的技能分类 (Available Categories):\n")
    categories = manager.get_market_categories()
    
    if "categories" in categories:
        for cat_id, cat_info in categories["categories"].items():
            icon = cat_info.get("icon", "")
            name = cat_info.get("name", cat_id)
            name_en = cat_info.get("name_en", "")
            desc = cat_info.get("description", "")
            print(f"  {icon} {name} ({name_en})")
            print(f"     {desc}")
            
            if "subcategories" in cat_info:
                for sub_id, sub_info in cat_info["subcategories"].items():
                    sub_name = sub_info.get("name", sub_id)
                    print(f"       - {sub_name}")
            print()


def search_skills(manager, query="", category="", limit=10):
    """搜索技能"""
    print(f"\n🔍 搜索技能 (Searching Skills): '{query}'\n")
    skills = manager.search_market_skills(query=query, category=category, limit=limit)
    
    if not skills:
        print("  未找到匹配的技能 (No matching skills found)")
        return
    
    for i, skill in enumerate(skills, 1):
        icon = skill.get("icon", "🔹")
        name = skill.get("name", skill.get("skill_id"))
        name_en = skill.get("name_en", "")
        version = skill.get("version", "1.0.0")
        desc = skill.get("description", "")
        downloads = skill.get("download_count", 0)
        rating = skill.get("rating", 0.0)
        skill_id = skill.get("skill_id")
        
        print(f"  {i}. {icon} {name} ({name_en}) v{version}")
        print(f"     ID: {skill_id}")
        print(f"     {desc}")
        print(f"     ⬇️  下载量 (Downloads): {downloads:,} | ⭐ 评分 (Rating): {rating}")
        print()


def list_featured(manager, limit=5):
    """列出推荐技能"""
    print(f"\n⭐ 推荐技能 (Featured Skills):\n")
    skills = manager.get_featured_skills(limit=limit)
    
    for i, skill in enumerate(skills, 1):
        icon = skill.get("icon", "🔹")
        name = skill.get("name", skill.get("skill_id"))
        name_en = skill.get("name_en", "")
        version = skill.get("version", "1.0.0")
        desc = skill.get("description", "")
        skill_id = skill.get("skill_id")
        
        print(f"  {i}. {icon} {name} ({name_en}) v{version}")
        print(f"     ID: {skill_id}")
        print(f"     {desc}")
        print()


def install_from_path(manager, path, skill_type="local"):
    """从本地路径安装"""
    print(f"\n📦 从本地路径安装技能 (Installing from path): {path}\n")
    result = manager.install_skill_from_path(path, skill_type)
    
    if result["status"] == "success":
        print(f"  ✅ {result['message']}")
        if "skill_id" in result:
            print(f"  技能 ID (Skill ID): {result['skill_id']}")
        if "name" in result:
            print(f"  技能名称 (Name): {result['name']}")
        if "path" in result:
            print(f"  安装路径 (Install Path): {result['path']}")
    else:
        print(f"  ❌ 安装失败 (Installation failed): {result['message']}")
        return False
    return True


def install_from_market(manager, skill_id):
    """从市场安装"""
    print(f"\n🛒 从市场安装技能 (Installing from market): {skill_id}\n")
    result = manager.install_skill_from_market(skill_id)
    
    if result["status"] == "success":
        print(f"  ✅ {result['message']}")
    else:
        print(f"  ❌ 安装失败 (Installation failed): {result['message']}")
        return False
    return True


def list_installed(manager, skill_type=None):
    """列出已安装的技能"""
    print("\n📚 已安装的技能 (Installed Skills):\n")
    
    if skill_type:
        skills = manager.list_skills_by_type(skill_type)
        type_names = {
            "core": "核心技能 (Core)",
            "local": "本地技能 (Local)",
            "market": "市场技能 (Market)",
            "user": "用户技能 (User)"
        }
        print(f"  类型 (Type): {type_names.get(skill_type, skill_type)}\n")
    else:
        skills = manager.list_skills()
    
    if not skills:
        print("  暂未安装任何技能 (No skills installed yet)")
        return
    
    for i, skill in enumerate(skills, 1):
        name = skill.get("name", skill.get("skill_id"))
        version = skill.get("version", "1.0.0")
        desc = skill.get("description", "")
        author = skill.get("author", "Unknown")
        skill_type = skill.get("type", "unknown")
        skill_id = skill.get("skill_id")
        
        type_icons = {
            "core": "⚙️",
            "local": "📁",
            "market": "🛒",
            "user": "👤"
        }
        icon = type_icons.get(skill_type, "🔹")
        
        print(f"  {i}. {icon} {name} v{version}")
        print(f"     ID: {skill_id}")
        print(f"     作者 (Author): {author}")
        print(f"     类型 (Type): {skill_type}")
        print(f"     {desc}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="HydraFlow AI 技能安装工具 (Skill Installation Tool)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例 (Examples):
  列出分类                    python skill_installer.py categories
  搜索技能                    python skill_installer.py search "coding"
  列出推荐技能                python skill_installer.py featured
  从本地目录安装              python skill_installer.py install-path ./my-skill
  从 ZIP 文件安装             python skill_installer.py install-path ./skill.zip --type user
  从市场安装                  python skill_installer.py install-market coding-agent
  列出已安装技能              python skill_installer.py list
  按类型列出                  python skill_installer.py list --type local
        """
    )
    
    subparsers = parser.add_subparsers(title="命令 (Commands)", dest="command")
    
    # categories 命令
    categories_parser = subparsers.add_parser("categories", help="列出所有分类 (List all categories)")
    
    # search 命令
    search_parser = subparsers.add_parser("search", help="搜索技能市场 (Search skill market)")
    search_parser.add_argument("query", nargs="?", default="", help="搜索关键词 (Search query)")
    search_parser.add_argument("--category", "-c", default="", help="分类过滤 (Category filter)")
    search_parser.add_argument("--limit", "-l", type=int, default=20, help="返回数量限制 (Limit results)")
    
    # featured 命令
    featured_parser = subparsers.add_parser("featured", help="列出推荐技能 (List featured skills)")
    featured_parser.add_argument("--limit", "-l", type=int, default=5, help="返回数量限制 (Limit results)")
    
    # install-path 命令
    install_path_parser = subparsers.add_parser("install-path", help="从本地路径安装 (Install from local path)")
    install_path_parser.add_argument("path", help="技能目录或 ZIP 文件路径 (Skill directory or ZIP file path)")
    install_path_parser.add_argument("--type", "-t", default="local", choices=["local", "user"], 
                                     help="技能类型 (Skill type, default: local)")
    
    # install-market 命令
    install_market_parser = subparsers.add_parser("install-market", help="从市场安装 (Install from market)")
    install_market_parser.add_argument("skill_id", help="市场技能 ID (Market skill ID)")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出已安装的技能 (List installed skills)")
    list_parser.add_argument("--type", "-t", choices=["core", "local", "market", "user"], 
                            help="按类型过滤 (Filter by type)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print_banner()
    
    try:
        manager = SkillManager()
        
        if args.command == "categories":
            list_categories(manager)
        
        elif args.command == "search":
            search_skills(manager, query=args.query, category=args.category, limit=args.limit)
        
        elif args.command == "featured":
            list_featured(manager, limit=args.limit)
        
        elif args.command == "install-path":
            install_from_path(manager, args.path, args.type)
        
        elif args.command == "install-market":
            install_from_market(manager, args.skill_id)
        
        elif args.command == "list":
            list_installed(manager, skill_type=args.type)
    
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消 (Operation cancelled)")
    except Exception as e:
        print(f"\n❌ 发生错误 (Error occurred): {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
