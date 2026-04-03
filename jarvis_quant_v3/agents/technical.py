"""
技术分析Agent
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TechnicalAgent:
    """技术分析Agent"""

    def __init__(self, tool_registry, analytics):
        self.tool_registry = tool_registry
        self.analytics = analytics

    async def analyze(self, stock_code: str, stock_name: str, task_type: str = 'technical_analysis') -> str:
        """
        分析股票技术面

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            task_type: 任务类型

        Returns:
            str: 分析报告
        """
        logger.info(f"📊 TechnicalAgent 开始分析: {stock_code}")

        # 获取技术分析工具
        tech_tool = self.tool_registry.get_tool('technical')
        if not tech_tool:
            return "❌ TechnicalAnalysisTool 未注册"

        try:
            # 获取技术数据
            result = await tech_tool.execute({
                'stock_code': stock_code,
                'indicators': ['MA', 'MACD', 'KDJ', 'RSI', 'BOLL']
            })

            # 构建分析提示
            prompt = f"""请分析以下股票的技术面：

股票代码: {stock_code}
股票名称: {stock_name}

技术指标数据:
{result.get('data', {})}

请从以下维度进行分析：
1. 趋势判断（均线系统、趋势线）
2. 动量指标（MACD、KDJ、RSI）
3. 支撑压力位
4. 成交量配合

请给出简明的技术分析结论：
- 当前趋势（上涨/下跌/震荡）
- 关键支撑位和压力位
- 可能的买卖点
- 投资建议（强烈买入/买入/持有/卖出/强烈卖出）

请用中文回复。"""

            # 使用模型路由进行分析
            from ..core.router import ModelRouter
            router = ModelRouter()
            analysis = await router.route(task_type, prompt)

            return analysis

        except Exception as e:
            logger.error(f"❌ TechnicalAgent 分析失败: {e}")
            return f"分析失败: {str(e)}"
