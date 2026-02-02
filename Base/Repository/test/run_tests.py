#!/usr/bin/env python
"""
测试运行脚本
方便快速运行 Repository 模块的测试
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """运行命令并打印结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, shell=True, cwd=Path(__file__).parent)
    return result.returncode


def main():
    """主函数"""
    test_dir = Path(__file__).parent

    print("="*60)
    print("Repository 模块测试套件")
    print("="*60)

    # 菜单
    print("\n请选择测试模式：")
    print("1. 运行所有测试")
    print("2. 运行 SQLite 连接测试")
    print("3. 运行 BaseConnection 测试")
    print("4. 运行 BaseDBModel 测试")
    print("5. 运行 ConnectionManager 测试")
    print("6. 运行集成测试")
    print("7. 运行测试并生成覆盖率报告")
    print("8. 只运行失败的测试")
    print("9. 运行所有测试（详细模式）")
    print("0. 退出")

    choice = input("\n请输入选项 (0-9): ").strip()

    commands = {
        "1": "pytest -v",
        "2": "pytest test_sqlite_connection.py -v",
        "3": "pytest test_base_connection.py -v",
        "4": "pytest test_base_db_model.py -v",
        "5": "pytest test_connection_manager.py -v",
        "6": "pytest test_integration.py -v",
        "7": "pytest --cov=Base.Repository --cov-report=html -v",
        "8": "pytest --lf -v",
        "9": "pytest -v -s",
    }

    if choice in commands:
        returncode = run_command(commands[choice], f"选项 {choice}")
        sys.exit(returncode)
    elif choice == "0":
        print("\n退出测试")
        sys.exit(0)
    else:
        print(f"\n无效选项: {choice}")
        sys.exit(1)


if __name__ == "__main__":
    main()
