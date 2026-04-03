"""
多智能体协调器 - MultiAgentCoordinator
整合所有Agent、工具系统、Hook系统和Analytics
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ..tools.registry import ToolRegistry
from ..hooks.manager import HookManager
from ..core.analytics import AnalyticsTracker
from ..core.permissions import PermissionChecker, PermissionLevel
from ..core.router import ModelRouter

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    stock_code: str
    stock_name: str
    analysis_time: str
    decision: str  # BUY/SELL/HOLD/STRONG_BUY/STRONG_SELL
    decision_cn: str
    confidence: float
    reasoning: str
    reports: Dict[str, str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


class MultiAgentCoordinator:
    """
    多智能体协调器

    负责：
    1. 管理所有Agent的生命周期
    2. 协调工具调用
    3. 执行生命周期钩子
    4. 追踪Analytics
    5. 进行综合决策
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tool_registry = ToolRegistry.get_instance()
        self.hook_manager = HookManager()
        self.analytics = AnalyticsTracker()
        self.permission_checker = PermissionChecker()
        self.model_router = ModelRouter()

        # 初始化内置钩子
        self._register_builtin_hooks()

        # Agent状态
        self.agents = {}
        self._initialize_agents()

        logger.info("✅ MultiAgentCoordinator 初始化完成")

    def _register_builtin_hooks(self):
        """注册内置钩子"""
        from ..hooks.builtins import (
            risk_check_hook,
            permission_check_hook,
            trade_log_hook,
            performance_track_hook
        )

        self.hook_manager.register_hook('pre_analysis', risk_check_hook)
        self.hook_manager.register_hook('pre_decision', permission_check_hook)
        self.hook_manager.register_hook('post_trade', trade_log_hook)
        self.hook_manager.register_hook('post_analysis', performance_track_hook)

        logger.info("✅ 内置钩子注册完成")

    def _initialize_agents(self):
        """初始化所有Agent"""
        from .fundamental import FundamentalAgent
        from .technical import TechnicalAgent
        from .sentiment import SentimentAgent
        from .risk import RiskAgent

        self.agents['fundamental'] = FundamentalAgent(self.model_router, self.analytics)
        self.agents['technical'] = TechnicalAgent(self.tool_registry, self.analytics)
        self.agents['sentiment'] = SentimentAgent(self.tool_registry, self.analytics)
        self.agents['risk'] = RiskAgent(self.tool_registry, self.analytics)

        logger.info(f"✅ 已初始化 {len(self.agents)} 个Agent: {list(self.agents.keys())}")

    async def analyze_stock(self, stock_code: str, stock_name: str, 
                           user_permission: int = PermissionLevel.MEDIUM) -> AnalysisResult:
        """
        分析股票

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            user_permission: 用户权限等级

        Returns:
            AnalysisResult: 分析结果
        """
        logger.info(f"📊 开始分析: {stock_name} ({stock_code})")

        # 构建上下文
        context = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'user_permission': user_permission,
            'timestamp': datetime.now().isoformat(),
        }

        # 执行 pre_analysis 钩子
        if not await self.hook_manager.execute_hook('pre_analysis', context):
            logger.warning("⚠️ pre_analysis 钩子返回 False，分析终止")
            return self._create_empty_result(stock_code, stock_name, "分析被钩子阻止")

        reports = {}

        # 并行执行所有Agent分析
        import asyncio

        tasks = []
        for name, agent in self.agents.items():
            task = self._run_agent(name, agent, context)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(self.agents.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"❌ Agent {name} 执行失败: {result}")
                reports[name] = f"执行失败: {str(result)}"
            else:
                reports[name] = result

        # 执行 post_analysis 钩子
        context['reports'] = reports
        await self.hook_manager.execute_hook('post_analysis', context)

        # 执行 pre_decision 钩子
        if not await self.hook_manager.execute_hook('pre_decision', context):
            logger.warning("⚠️ pre_decision 钩子返回 False")

        # 综合决策
        decision, confidence, reasoning = self._make_decision(reports)

        # 执行 post_decision 钩子
        context['decision'] = decision
        context['confidence'] = confidence
        await self.hook_manager.execute_hook('post_decision', context)

        # 创建结果
        result = AnalysisResult(
            stock_code=stock_code,
            stock_name=stock_name,
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            decision=decision,
            decision_cn=self._translate_decision(decision),
            confidence=confidence,
            reasoning=reasoning,
            reports=reports,
            metadata={
                'agents_used': list(self.agents.keys()),
                'user_permission': user_permission,
            }
        )

        logger.info(f"✅ 分析完成: {stock_code} -> {result.decision_cn} (置信度: {confidence:.2f})")

        return result

    async def _run_agent(self, name: str, agent, context: Dict) -> str:
        """运行单个Agent"""
        start_time = datetime.now()

        try:
            # 根据Agent类型获取任务类型
            task_type_map = {
                'fundamental': 'fundamental_analysis',
                'technical': 'technical_analysis',
                'sentiment': 'sentiment_analysis',
                'risk': 'risk_assessment',
            }

            task_type = task_type_map.get(name, 'final_decision')

            result = await agent.analyze(
                stock_code=context['stock_code'],
                stock_name=context['stock_name'],
                task_type=task_type
            )

            # 记录Analytics
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.analytics.record_agent_call(
                agent_name=name,
                latency=latency,
                confidence=0.7,  # 默认置信度
                decision=self._extract_decision(result)
            )

            return result

        except Exception as e:
            logger.error(f"❌ Agent {name} 执行异常: {e}")
            return f"执行异常: {str(e)}"

    def _make_decision(self, reports: Dict[str, str]) -> tuple:
        """综合所有报告做出决策"""
        # 简单的加权评分
        decision_scores = {
            "STRONG_BUY": 2, "BUY": 1, "HOLD": 0, "SELL": -1, "STRONG_SELL": -2
        }

        total_score = 0
        total_weight = 0

        weights = {
            'fundamental': 0.35,
            'technical': 0.25,
            'sentiment': 0.20,
            'risk': 0.20,
        }

        for name, report in reports.items():
            weight = weights.get(name, 0.1)
            score = self._extract_score(report, decision_scores)
            total_score += score * weight
            total_weight += weight

        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0

        # 根据分数决定决策
        if normalized_score >= 1.5:
            decision = "STRONG_BUY"
            confidence = min(0.9, abs(normalized_score) / 2 + 0.7)
        elif normalized_score >= 0.5:
            decision = "BUY"
            confidence = min(0.8, normalized_score / 2 + 0.5)
        elif normalized_score <= -1.5:
            decision = "STRONG_SELL"
            confidence = min(0.9, abs(normalized_score) / 2 + 0.7)
        elif normalized_score <= -0.5:
            decision = "SELL"
            confidence = min(0.8, abs(normalized_score) / 2 + 0.5)
        else:
            decision = "HOLD"
            confidence = 0.5

        reasoning = self._generate_reasoning(reports, decision, normalized_score)

        return decision, confidence, reasoning

    def _extract_score(self, report: str, decision_scores: Dict) -> float:
        """从报告中提取评分"""
        text = report.lower()

        # 关键词匹配
        if '强烈买入' in text or '强力买入' in text:
            return 2
        elif '买入' in text or '推荐' in text:
            return 1
        elif '卖出' in text or '减持' in text:
            return -1
        elif '强烈卖出' in text or '强烈减持' in text:
            return -2

        return 0

    def _extract_decision(self, report: str) -> str:
        """从报告中提取决策"""
        text = report.lower()

        if '强烈买入' in text or '强力买入' in text:
            return "STRONG_BUY"
        elif '买入' in text or '推荐' in text:
            return "BUY"
        elif '卖出' in text or '减持' in text:
            return "SELL"
        elif '强烈卖出' in text or '强烈减持' in text:
            return "STRONG_SELL"

        return "HOLD"

    def _generate_reasoning(self, reports: Dict[str, str], decision: str, score: float) -> str:
        """生成推理过程"""
        lines = [
            f"综合评分: {score:.2f}",
            f"最终决策: {self._translate_decision(decision)}",
            "",
            "各维度分析:",
        ]

        for name, report in reports.items():
            # 截取前100字符
            brief = report[:100] + "..." if len(report) > 100 else report
            lines.append(f"- {name}: {brief}")

        return "\n".join(lines)

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

    def _create_empty_result(self, stock_code: str, stock_name: str, reason: str) -> AnalysisResult:
        """创建空结果"""
        return AnalysisResult(
            stock_code=stock_code,
            stock_name=stock_name,
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            decision="HOLD",
            decision_cn="持有",
            confidence=0,
            reasoning=f"分析未完成: {reason}",
            reports={},
            metadata={'error': reason}
        )

    async def execute_trade(self, stock_code: str, direction: str, quantity: int,
                           price: float, user_permission: int) -> Dict:
        """
        执行交易

        Args:
            stock_code: 股票代码
            direction: BUY/SELL
            quantity: 数量
            price: 价格
            user_permission: 用户权限

        Returns:
            Dict: 交易结果
        """
        trade_amount = quantity * price

        # 检查权限
        required_level = PermissionLevel.HIGH if trade_amount > 100000 else PermissionLevel.MEDIUM

        if not self.permission_checker.check(required_level, user_permission):
            return {'success': False, 'error': '权限不足'}

        # 检查是否需要多重确认
        confirmations = self.permission_checker.require_multi_confirmation(trade_amount)
        if confirmations > 0:
            logger.warning(f"⚠️ 交易金额 {trade_amount} 需要 {confirmations} 次确认")

        # 构建上下文
        context = {
            'stock_code': stock_code,
            'direction': direction,
            'quantity': quantity,
            'price': price,
            'amount': trade_amount,
            'user_permission': user_permission,
        }

        # 执行 pre_trade 钩子
        if not await self.hook_manager.execute_hook('pre_trade', context):
            return {'success': False, 'error': '交易被钩子阻止'}

        # TODO: 调用实际的交易API

        # 模拟交易结果
        result = {
            'success': True,
            'trade_id': f'TRADE_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'stock_code': stock_code,
            'direction': direction,
            'quantity': quantity,
            'price': price,
            'amount': trade_amount,
            'timestamp': datetime.now().isoformat(),
        }

        # 执行 post_trade 钩子
        await self.hook_manager.execute_hook('post_trade', result)

        # 记录交易
        self.analytics.record_trade(result)

        return result

    def get_analytics_report(self) -> str:
        """获取Analytics报告"""
        return self.analytics.generate_report()

    def format_result(self, result: AnalysisResult) -> str:
        """格式化分析结果"""
        return f"""
{'='*60}
🤖 贾维斯量化分析报告 v3.0
{'='*60}

📈 股票: {result.stock_name} ({result.stock_code})
⏰ 分析时间: {result.analysis_time}

🎯 综合决策: {result.decision_cn} ({result.decision})
📈 置信度: {result.confidence:.2%}

📝 推理过程:
{result.reasoning}

{'='*60}
📋 详细分析
{'='*60}
"""

