#!/usr/bin/env python3
"""
TradingAgents-CN 与贾维斯系统整合测试
"""

import os
import sys
import json
from datetime import datetime

# 添加路径
sys.path.insert(0, "/root/.openclaw/workspace")

def test_trading_agents_import():
    """测试 TradingAgents-CN 导入"""
    print("🧪 测试 TradingAgents-CN 导入...")
    
    try:
        # 尝试导入核心模块
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.graph.propagation import Propagator
        
        print("✅ TradingAgents-CN 核心模块导入成功")
        
        # 检查版本
        import tradingagents
        print(f"📦 TradingAgents-CN 版本: {tradingagents.__version__ if hasattr(tradingagents, '__version__') else '未知'}")
        
        return True
    except ImportError as e:
        print(f"❌ TradingAgents-CN 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ TradingAgents-CN 导入异常: {e}")
        return False

def test_model_manager():
    """测试模型管理器"""
    print("\n🧪 测试模型管理器...")
    
    try:
        from optimized_multi_agent import ModelManager
        
        manager = ModelManager()
        print("✅ 模型管理器初始化成功")
        
        # 检查可用的客户端
        available_clients = [p for p, c in manager.clients.items() if c]
        print(f"📡 可用客户端: {available_clients}")
        
        return True
    except Exception as e:
        print(f"❌ 模型管理器测试失败: {e}")
        return False

def test_agents():
    """测试智能体"""
    print("\n🧪 测试智能体...")
    
    try:
        from optimized_multi_agent import (
            ModelManager, FundamentalAgent, TechnicalAgent,
            SentimentAgent, RiskAgent
        )
        
        manager = ModelManager()
        
        # 测试各个智能体
        agents = [
            ("基本面", FundamentalAgent(manager)),
            ("技术面", TechnicalAgent(manager)),
            ("情绪面", SentimentAgent(manager)),
            ("风险", RiskAgent(manager))
        ]
        
        for name, agent in agents:
            print(f"  🤖 测试 {name} 智能体...")
            try:
                # 简单测试
                prompt = f"请简要分析测试股票"
                result = agent._call_llm(prompt)
                if result and len(result) > 10:
                    print(f"  ✅ {name} 智能体测试成功")
                else:
                    print(f"  ⚠️ {name} 智能体返回结果过短")
            except Exception as e:
                print(f"  ❌ {name} 智能体测试失败: {e}")
        
        return True
    except Exception as e:
        print(f"❌ 智能体测试失败: {e}")
        return False

def test_trading_agents_wrapper():
    """测试 TradingAgents 包装器"""
    print("\n🧪 测试 TradingAgents 包装器...")
    
    try:
        from optimized_multi_agent import ModelManager, TradingAgentsWrapper
        
        manager = ModelManager()
        wrapper = TradingAgentsWrapper(manager)
        
        if wrapper.ta_available:
            print("✅ TradingAgents 包装器初始化成功")
            print(f"📊 TradingAgents 可用: {wrapper.ta_available}")
            
            # 测试分析
            print("  🔍 测试 TradingAgents 分析...")
            try:
                result = wrapper.analyze("002202", "金风科技")
                if result.get("available", False):
                    print(f"  ✅ TradingAgents 分析成功")
                    print(f"    决策: {result.get('decision', '未知')}")
                    print(f"    置信度: {result.get('confidence', '未知')}")
                else:
                    print(f"  ⚠️ TradingAgents 分析不可用: {result.get('error', '未知错误')}")
            except Exception as e:
                print(f"  ❌ TradingAgents 分析失败: {e}")
        else:
            print("⚠️ TradingAgents 包装器不可用")
        
        return wrapper.ta_available
    except Exception as e:
        print(f"❌ TradingAgents 包装器测试失败: {e}")
        return False

def test_coordinator():
    """测试协调器"""
    print("\n🧪 测试多智能体协调器...")
    
    try:
        from optimized_multi_agent import MultiAgentCoordinator
        
        print("🚀 初始化协调器...")
        coordinator = MultiAgentCoordinator()
        
        print("✅ 协调器初始化成功")
        print(f"🤖 已加载智能体: {list(coordinator.agents.keys())}")
        print(f"📊 TradingAgents 可用: {coordinator.ta_wrapper and coordinator.ta_wrapper.ta_available}")
        
        # 测试快速分析
        print("\n🔍 测试快速分析...")
        try:
            result = coordinator.analyze_stock("002202", "金风科技")
            print(f"✅ 分析成功")
            print(f"  股票: {result.stock_name} ({result.stock_code})")
            print(f"  决策: {result.decision_cn}")
            print(f"  置信度: {result.confidence:.2%}")
            print(f"  使用的智能体: {result.metadata.get('agents_used', [])}")
            
            # 保存结果
            output_file = "/tmp/test_analysis_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"💾 结果已保存到: {output_file}")
            
            return True
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 协调器测试失败: {e}")
        return False

def test_integration_module():
    """测试整合模块"""
    print("\n🧪 测试整合模块...")
    
    try:
        from trading_agents_integration import TradingAgentsCNIntegration
        
        print("🚀 初始化整合模块...")
        integration = TradingAgentsCNIntegration()
        
        if integration.trading_agents_available:
            print("✅ TradingAgents-CN 整合模块初始化成功")
            
            # 测试分析
            print("🔍 测试股票分析...")
            result = integration.analyze_stock("002202", "金风科技")
            
            if "error" not in result:
                print(f"✅ 分析成功")
                print(f"  决策: {result.get('decision_cn', '未知')}")
                print(f"  置信度: {result.get('confidence', '未知')}")
                print(f"  报告数量: {len(result.get('reports', {}))}")
                
                # 保存结果
                output_file = "/tmp/integration_test_result.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"💾 结果已保存到: {output_file}")
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
            
            return True
        else:
            print("⚠️ TradingAgents-CN 整合模块不可用")
            return False
            
    except Exception as e:
        print(f"❌ 整合模块测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🤖 TradingAgents-CN 与贾维斯系统整合测试")
    print("=" * 60)
    
    # 设置环境变量（测试用）
    os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "test_key")
    
    test_results = {}
    
    # 运行各个测试
    test_results["import"] = test_trading_agents_import()
    test_results["model_manager"] = test_model_manager()
    test_results["agents"] = test_agents()
    test_results["ta_wrapper"] = test_trading_agents_wrapper()
    test_results["coordinator"] = test_coordinator()
    test_results["integration"] = test_integration_module()
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, passed in test_results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    print(f"\n📈 通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！整合成功！")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败，请检查配置")
    
    # 生成测试报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": test_results,
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0
        },
        "environment": {
            "python_version": sys.version,
            "trading_agents_path": "/root/.openclaw/workspace/TradingAgents-CN",
            "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY"))
        }
    }
    
    report_file = "/tmp/integration_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细测试报告已保存到: {report_file}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)