"""
风险分析Agent
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RiskAgent:
    """风险分析Agent"""

    def __init__(self, tool_registry, analytics):
        self.tool_registry = tool_registry
        self.analytics = analytics

    async def analyze(self, stock_code: str, stock_name: str, task_type: str = 'risk_assessment') -> str:
        """
        分析股票风险

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            task_type: 任务类型

        Returns:
            str: 分析报告
        """
        logger.info(f"📊 RiskAgent 开始分析: {stock_code}")

        # 获取风险计算工具
        risk_tool = self.tool_registry.get_tool('risk')
        stock_tool = self.tool_registry.get_tool('stock_data')

        try:
            # 获取风险数据
            risk_result = {}
            stock_result = {}

            if risk_tool:
                risk_result = await risk_tool.execute({
                    'stock_code': stock_code
                })

            if stock_tool:
                stock_result = await stock_tool.execute({
                    'stock_code': stock_code,
                    'data_type': 'basic'
                })

            # 构建分析提示
            prompt = f"""请分析以下股票的风险因素：

股票代码: {stock_code}
股票名称: {stock_name}

风险指标:
{risk_result.get('data', {})}

基本面数据:
{stock_result.get('data', {})}

请从以下维度进行风险评估：
1. 市场风险（Beta、波动率）
2. 流动性风险（成交量、流通股本）
3. 财务风险（资产负债率、现金流）
4. 行业风险（政策风险、竞争格局）
5. 黑天鹅风险（极端事件）

请给出简明的风险评估：
- 整体风险等级（高/中/低）
- 主要风险因素
- 风险控制建议
- 投资建议（强烈买入/买入/持有/卖出/强烈卖出）

请用中文回复。"""

            # 使用模型路由进行分析
            from ..core.router import ModelRouter
            router = ModelRouter()
            analysis = await router.route(task_type, prompt)

            return analysis

        except Exception as e:
            logger.error(f"❌ RiskAgent 分析失败: {e}")
            return f"分析失败: {str(e)}"
