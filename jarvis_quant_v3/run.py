#!/usr/bin/env python3
"""
贾维斯量化系统 v3.0 启动脚本

使用方法:
    python run.py                    # 启动Web界面
    python run.py --cli             # 启动CLI模式
    python run.py --analyze 000001 # 分析指定股票
"""

import sys
import os
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主入口"""

    parser = argparse.ArgumentParser(
        description="贾维斯量化系统 v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python run.py                    # 启动Web界面
    python run.py --cli             # 启动CLI模式
    python run.py --analyze 000001 # 分析股票
    python run.py --test            # 测试模式
        """
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='启动CLI命令行模式'
    )

    parser.add_argument(
        '--analyze',
        type=str,
        help='分析指定股票代码，如: --analyze 000001'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='运行测试'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Web服务端口 (默认: 8501)'
    )

    args = parser.parse_args()

    if args.cli:
        # CLI模式
        run_cli()
    elif args.analyze:
        # 分析指定股票
        run_analysis(args.analyze)
    elif args.test:
        # 测试模式
        run_test()
    else:
        # 默认启动Web界面
        run_web(args.port)


def run_web(port: int = 8501):
    """启动Web界面"""
    import subprocess

    print(f"""
╔════════════════════════════════════════════════════════╗
║         🤖 贾维斯量化系统 v3.0                       ║
║         基于 Claude Code 架构设计                      ║
╚════════════════════════════════════════════════════════╝
    """)

    print(f"🌐 正在启动Web服务...")
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"🔄 按 Ctrl+C 停止服务")
    print()

    try:
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", "web/app.py", "--server.port", str(port)]
        stcli.main()
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


def run_cli():
    """启动CLI命令行模式"""
    from jarvis_quant_v3.agents.coordinator import MultiAgentCoordinator
    import asyncio

    print("""
╔════════════════════════════════════════════════════════╗
║         🤖 贾维斯量化系统 v3.0 - CLI模式             ║
╚════════════════════════════════════════════════════════╝
    """)

    coordinator = MultiAgentCoordinator()

    print("📊 贾维斯CLI模式")
    print("-" * 40)
    print("输入股票代码进行分析 (输入 'quit' 退出)")
    print()

    while True:
        try:
            stock_code = input("股票代码: ").strip()

            if stock_code.lower() == 'quit':
                print("👋 再见！")
                break

            if not stock_code:
                continue

            print(f"\n🚀 开始分析 {stock_code}...")
            print("-" * 40)

            async def analyze():
                return await coordinator.analyze_stock(stock_code, stock_code)

            result = asyncio.run(analyze())

            print(coordinator.format_result(result))

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 分析失败: {e}\n")


def run_analysis(stock_code: str):
    """分析指定股票"""
    from jarvis_quant_v3.agents.coordinator import MultiAgentCoordinator
    import asyncio

    print(f"📊 分析股票: {stock_code}")

    coordinator = MultiAgentCoordinator()

    async def analyze():
        return await coordinator.analyze_stock(stock_code, stock_code)

    result = asyncio.run(analyze())

    print(coordinator.format_result(result))


def run_test():
    """运行测试"""
    print("🧪 运行系统测试...")
    print()

    # 测试导入
    print("📦 测试模块导入...")

    try:
        from jarvis_quant_v3.tools.registry import ToolRegistry
        print("  ✅ tools.registry")

        from jarvis_quant_v3.hooks.manager import HookManager
        print("  ✅ hooks.manager")

        from jarvis_quant_v3.core.analytics import AnalyticsTracker
        print("  ✅ core.analytics")

        from jarvis_quant_v3.core.permissions import PermissionChecker
        print("  ✅ core.permissions")

        from jarvis_quant_v3.core.router import ModelRouter
        print("  ✅ core.router")

        from jarvis_quant_v3.agents.coordinator import MultiAgentCoordinator
        print("  ✅ agents.coordinator")

        print()
        print("✅ 所有模块导入成功！")

    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
