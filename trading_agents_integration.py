"""
TradingAgents-CN 与贾维斯量化系统整合模块

目标：
1. 将 TradingAgents-CN 的多智能体架构整合到贾维斯系统
2. 优化现有的 multi_agent.py
3. 实现数据共享和模型统一管理
"""

import os
import sys
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
import logging

# 添加 TradingAgents-CN 到路径
trading_agents_path = "/root/.openclaw/workspace/TradingAgents-CN"
if trading_agents_path not in sys.path:
    sys.path.insert(0, trading_agents_path)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingAgentsCNIntegration:
    """
    TradingAgents-CN 整合类
    
    主要功能：
    1. 加载 TradingAgents-CN 的核心组件
    2. 提供与贾维斯系统兼容的接口
    3. 管理模型配置和 API 密钥
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化整合模块
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.trading_agents_available = False
        self.graph = None
        self.propagator = None
        
        # 尝试导入 TradingAgents-CN
        self._import_trading_agents()
        
        if self.trading_agents_available:
            self._initialize_trading_agents()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        config = {
            "use_chinese_output": True,
            "llm_provider": "deepseek",  # 默认使用 DeepSeek
            "deep_think_llm": "deepseek-chat",
            "quick_think_llm": "deepseek-chat",
            "debug": False,
            "api_keys": {
                "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
                "openai": os.getenv("OPENAI_API_KEY", ""),
                "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
                "google": os.getenv("GOOGLE_API_KEY", ""),
                "dashscope": os.getenv("DASHSCOPE_API_KEY", "")
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
            except Exception as e:
                logger.warning(f"无法加载配置文件 {config_path}: {e}")
        
        return config
    
    def _import_trading_agents(self):
        """尝试导入 TradingAgents-CN 模块"""
        try:
            # 尝试导入核心组件
            from tradingagents.graph.trading_graph import TradingAgentsGraph
            from tradingagents.graph.propagation import Propagator
            from tradingagents.default_config import DEFAULT_CONFIG
            
            self.TradingAgentsGraph = TradingAgentsGraph
            self.Propagator = Propagator
            self.DEFAULT_CONFIG = DEFAULT_CONFIG
            self.trading_agents_available = True
            
            logger.info("✅ TradingAgents-CN 导入成功")
            
        except ImportError as e:
            logger.error(f"❌ 无法导入 TradingAgents-CN: {e}")
            logger.info("请确保已安装 TradingAgents-CN: pip install -e .")
            self.trading_agents_available = False
    
    def _initialize_trading_agents(self):
        """初始化 TradingAgents"""
        if not self.trading_agents_available:
            return
        
        try:
            # 获取 API 密钥
            llm_provider = self.config["llm_provider"]
            api_key = self.config["api_keys"].get(llm_provider, "")
            
            if not api_key:
                logger.warning(f"⚠️  {llm_provider} API 密钥未设置")
            
            # 创建 TradingAgentsGraph
            self.graph = self.TradingAgentsGraph(
                selected_analysts=["market", "social", "news", "fundamentals"],
                debug=self.config["debug"],
                config={
                    "llm_provider": llm_provider,
                    "deep_think_llm": self.config["deep_think_llm"],
                    "quick_think_llm": self.config["quick_think_llm"],
                    "api_key": api_key
                }
            )
            
            logger.info(f"✅ TradingAgents 初始化完成，使用模型: {llm_provider}")
            
        except Exception as e:
            logger.error(f"❌ TradingAgents 初始化失败: {e}")
            self.trading_agents_available = False
    
    def analyze_stock(
        self,
        ticker: str,
        company_name: str,
        trade_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 TradingAgents-CN 分析股票
        
        Args:
            ticker: 股票代码
            company_name: 公司名称
            trade_date: 交易日期
            
        Returns:
            分析结果字典
        """
        if not self.trading_agents_available or not self.graph:
            return {
                "ticker": ticker,
                "company_name": company_name,
                "error": "TradingAgents-CN 未初始化",
                "timestamp": datetime.now().isoformat()
            }
        
        if trade_date is None:
            trade_date = date.today().isoformat()
        
        logger.info(f"🔍 TradingAgents 分析: {ticker} ({company_name})")
        
        try:
            # 设置股票代码
            self.graph.ticker = ticker
            
            # 执行分析
            final_state, processed_signal = self.graph.propagate(company_name, trade_date)
            
            # 提取关键信息
            result = {
                "ticker": ticker,
                "company_name": company_name,
                "trade_date": trade_date,
                "decision": processed_signal.get("decision", "HOLD"),
                "confidence": processed_signal.get("confidence", 0.5),
                "reasoning": self._extract_reasoning(final_state),
                "reports": {
                    "market": final_state.get("market_report", ""),
                    "sentiment": final_state.get("sentiment_report", ""),
                    "news": final_state.get("news_report", ""),
                    "fundamentals": final_state.get("fundamentals_report", ""),
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 翻译决策为中文
            result["decision_cn"] = self._translate_decision(result["decision"])
            
            logger.info(f"✅ 分析完成: {ticker} -> {result['decision_cn']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 分析失败 {ticker}: {e}")
            return {
                "ticker": ticker,
                "company_name": company_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_reasoning(self, state: Dict[str, Any]) -> str:
        """从状态中提取推理过程"""
        reasoning_parts = []
        
        # 添加各个报告
        for report_type in ["market_report", "sentiment_report", "news_report", "fundamentals_report"]:
            if report_type in state and state[report_type]:
                # 截取前200字符
                content = state[report_type]
                if len(content) > 200:
                    content = content[:200] + "..."
                reasoning_parts.append(f"{report_type.replace('_report', '')}: {content}")
        
        # 添加交易者决策
        if "trader_investment_plan" in state:
            content = state["trader_investment_plan"]
            if len(content) > 200:
                content = content[:200] + "..."
            reasoning_parts.append(f"交易者计划: {content}")
        
        # 添加最终决策
        if "final_trade_decision" in state:
            content = state["final_trade_decision"]
            if len(content) > 200:
                content = content[:200] + "..."
            reasoning_parts.append(f"最终决策: {content}")
        
        return "\n\n".join(reasoning_parts)
    
    def _translate_decision(self, decision: str) -> str:
        """翻译决策为中文"""
        decision_map = {
            "BUY": "买入",
            "SELL": "卖出", 
            "HOLD": "持有",
            "STRONG_BUY": "强烈买入",
            "STRONG_SELL": "强烈卖出"
        }
        return decision_map.get(decision, decision)
    
    def batch_analyze(
        self,
        stock_list: List[Tuple[str, str]],
        trade_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量分析多个股票
        
        Args:
            stock_list: 股票列表，每个元素为 (ticker, company_name)
            trade_date: 交易日期
            
        Returns:
            分析结果列表
        """
        results = []
        
        logger.info(f"📊 开始批量分析 {len(stock_list)} 只股票")
        
        for ticker, company_name in stock_list:
            try:
                result = self.analyze_stock(ticker, company_name, trade_date)
                results.append(result)
                logger.info(f"✅ 完成: {ticker} -> {result.get('decision_cn', '未知')}")
            except Exception as e:
                logger.error(f"❌ 分析失败 {ticker}: {e}")
                results.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        logger.info(f"📊 批量分析完成: {len(results)}/{len(stock_list)} 成功")
        return results


class EnhancedMultiAgent:
    """
    增强的多智能体系统
    结合贾维斯原有系统和 TradingAgents-CN
    """
    
    def __init__(self, trading_agents_config: Optional[str] = None):
        """
        初始化增强多智能体系统
        
        Args:
            trading_agents_config: TradingAgents 配置文件路径
        """
        # 导入贾维斯原有系统
        from jarvis_trading_system.src.multi_agent import JarvisMultiAgent
        
        # 初始化原有系统
        self.jarvis_agent = JarvisMultiAgent()
        
        # 初始化 TradingAgents-CN 整合
        self.ta_integration = TradingAgentsCNIntegration(trading_agents_config)
        
        logger.info("🤖 增强多智能体系统初始化完成")
    
    def enhanced_analyze(self, stock_code: str, stock_name: str = None) -> Dict[str, Any]:
        """
        增强分析：结合贾维斯原有系统和 TradingAgents-CN
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            
        Returns:
            增强的分析结果
        """
        name = stock_name or stock_code
        
        logger.info(f"🔍 开始增强分析: {name} ({stock_code})")
        
        # 1. 贾维斯原有分析
        logger.info("📊 执行贾维斯原有分析...")
        jarvis_result = self.jarvis_agent.analyze_stock(stock_code, name)
        
        # 2. TradingAgents-CN 分析
        logger.info("🤖 执行 TradingAgents-CN 分析...")
        ta_result = self.ta_integration.analyze_stock(stock_code, name)
        
        # 3. 结合分析结果
        combined_result = self._combine_analyses(jarvis_result, ta_result)
        
        logger.info(f"✅ 增强分析完成: {stock_code}")
        return combined_result
    
    def _combine_analyses(self, jarvis_result: Dict, ta_result: Dict) -> Dict[str, Any]:
        """结合两个分析结果"""
        # 提取关键信息
        jarvis_decision = self._extract_jarvis_decision(jarvis_result)
        ta_decision = ta_result.get("decision", "HOLD")
        
        # 决策评分
        decision_scores = {
            "STRONG_BUY": 2,
            "BUY": 1,
            "HOLD": 0,
            "SELL": -1,
            "STRONG_SELL": -2
        }
        
        jarvis_score = decision_scores.get(jarvis_decision, 0)
        ta_score = decision_scores.get(ta_decision, 0)
        
        # 加权计算（贾维斯权重0.6，TradingAgents权重0.4）
        total_score = jarvis_score * 0.6 + ta_score * 0.4
        
        # 根据总分决定最终决策
        if total_score >= 1.5:
            final_decision = "STRONG_BUY"
        elif total_score >= 0.5:
            final_decision = "BUY"
        elif total_score <= -1.5:
            final_decision = "STRONG_SELL"
        elif total_score <= -0.5:
            final_decision = "SELL"
        else:
            final_decision = "HOLD"
        
        # 构建结果
        result = {
            "stock_code": jarvis_result.get("stock_code", ""),
            "stock_name": jarvis_result.get("stock_name", ""),
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "jarvis_analysis": {
                "fundamental": jarvis_result.get("fundamental", ""),
                "technical": jarvis_result.get("technical", ""),
                "sentiment": jarvis_result.get("sentiment", ""),
                "risk": jarvis_result.get("risk", ""),
                "decision": jarvis_decision
            },
            "trading_agents_analysis": ta_result,
            "combined_decision": final_decision,
            "combined_decision_cn": self._translate_decision(final_decision),
            "confidence_scores": {
                "jarvis": jarvis_score,
                "trading_agents": ta_score,
                "combined": total_score
            }
        }
        
        return result
    
    def _extract_jarvis_decision(self, jarvis_result: Dict) -> str:
        """从贾维斯分析结果中提取决策"""
        # 这里需要根据贾维斯分析结果提取决策
        # 暂时返回 HOLD
        return "HOLD"
    
    def _translate_decision(self, decision: str) -> str:
        """翻译决策为中文"""
        decision_map = {
            "BUY": "买入",
            "SELL": "卖出", 
            "HOLD": "持有",
            "STRONG_BUY": "强烈买入",
            "STRONG_SELL": "强烈卖出"
        }
        return decision_map.get(decision, decision)
    
    def format_enhanced_report(self, result: Dict) -> str:
        """格式化增强分析报告"""
        report = f"""
{'='*80}
🤖 贾维斯增强多智能体分析报告
{'='*80}

📈 股票: {result['stock_name']} ({result['stock_code']})
⏰ 分析时间: {result['analysis_time']}

{'='*80}
🎯 综合决策
{'='*80}
📊 最终决策: {result['combined_decision_cn']} ({result['combined_decision']})
📈 置信度评分: {result['confidence_scores']['combined']:.2f}
   - 贾维斯系统: {result['confidence_scores']['jarvis']:.2f}
   - TradingAgents: {result['confidence_scores']['trading_agents']:.2f}

{'='*80}
🤵 贾维斯原有分析
{'='*80}
📈 基本面分析:
{result['jarvis_analysis']['fundamental'][:300]}...

📉 技术面分析:
{result['jarvis_analysis']['technical'][:300]}...

💬 情绪面分析:
{result['jarvis_analysis']['sentiment'][:300]}...

⚠️ 风险评估:
{result['jarvis_analysis']['risk'][:300]}...

{'='*80}
🤖 TradingAgents-CN 分析
{'='*80}
📊 决策: {result['trading_agents_analysis'].get('decision_cn', '未知')}
📈 置信度: {result['trading_agents_analysis'].get('confidence', '未知')}

📝 分析摘要:
{result['trading_agents_analysis'].get('reasoning', '无')[:500]}...

{'='*80}
📋 操作建议
{'='*80}
基于多智能体综合分析，建议：
1. 操作: {result['combined_decision_cn']}
2. 仓位: 根据风险承受能力配置
3. 止损: 建议设置止损位
4. 持有周期: 建议根据市场变化调整

{'='*80}
⚠️ 风险提示
{'='*80}
1. 本分析仅供参考，不构成投资建议
2. 股市有风险，投资需谨慎
3. 请结合自身风险承受能力做出决策

{'='*80}
🤵 贾维斯出品 | 多智能体增强版 v1.0
{'='*80}
"""
        return report


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     贾维斯 + TradingAgents-CN 整合测试               ║
    ║     多智能体增强分析系统                            ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # 测试 TradingAgents-CN 整合
    print("1. 测试 Trading