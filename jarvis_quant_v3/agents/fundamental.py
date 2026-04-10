"""
基本面分析Agent
"""

import logging
from typing import Dict, Any
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class FundamentalAgent:
    """基本面分析Agent"""

    def __init__(self, model_router, analytics):
        self.model_router = model_router
        self.analytics = analytics
        self.tool_registry = ToolRegistry.get_instance()

    async def analyze(self, stock_code: str, stock_name: str, task_type: str = 'fundamental_analysis') -> str:
        """
        分析股票基本面

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            task_type: 任务类型

        Returns:
            str: 分析报告
        """
        logger.info(f"📊 FundamentalAgent 开始分析: {stock_code}")

        # 获取股票数据工具
        stock_tool = self.tool_registry.get_tool('stock_data')
        if not stock_tool:
            return "❌ StockDataTool 未注册"

        try:
            # 获取基本面数据
            result = await stock_tool.execute({
                'stock_code': stock_code,
                'data_type': 'fundamentals'
            })

            # 构建分析提示
            prompt = f"""请分析以下股票的基本面：

股票代码: {stock_code}
股票名称: {stock_name}

基本面数据:
{result.get('data', {})}

请从以下维度进行分析：
1. 盈利能力（毛利率、净利率、ROE等）
2. 成长性（营收增长、利润增长）
3. 估值水平（PE、PB、PS等）
4. 财务健康（资产负债率、现金流）

请给出简明的分析结论，包括：
- 当前估值是否合理
- 盈利能力如何
- 主要风险点
- 投资建议（强烈买入/买入/持有/卖出/强烈卖出）

请用中文回复。"""

            # 使用模型路由进行分析
            analysis = await self.model_router.route(task_type, prompt)

            return analysis

        except Exception as e:
            logger.error(f"❌ FundamentalAgent 分析失败: {e}")
            return f"分析失败: {str(e)}"
