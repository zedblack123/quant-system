"""
情绪分析Agent
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SentimentAgent:
    """情绪分析Agent"""

    def __init__(self, tool_registry, analytics):
        self.tool_registry = tool_registry
        self.analytics = analytics

    async def analyze(self, stock_code: str, stock_name: str, task_type: str = 'sentiment_analysis') -> str:
        """
        分析股票情绪

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            task_type: 任务类型

        Returns:
            str: 分析报告
        """
        logger.info(f"📊 SentimentAgent 开始分析: {stock_code}")

        # 获取情绪分析工具
        news_tool = self.tool_registry.get_tool('news')
        sentiment_tool = self.tool_registry.get_tool('sentiment')

        try:
            # 获取新闻和社交媒体数据
            news_result = {}
            sentiment_result = {}

            if news_tool:
                news_result = await news_tool.execute({
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'max_results': 10
                })

            if sentiment_tool:
                sentiment_result = await sentiment_tool.execute({
                    'stock_code': stock_code,
                    'platforms': ['eastmoney', 'tonghuashun']
                })

            # 构建分析提示
            prompt = f"""请分析以下股票的市场情绪：

股票代码: {stock_code}
股票名称: {stock_name}

新闻数据:
{news_result.get('data', {})}

社交媒体情绪:
{sentiment_result.get('data', {})}

请从以下维度进行分析：
1. 新闻情绪（利好/利空）
2. 社交媒体热度（讨论量、关注度）
3. 机构评级变化
4. 市场情绪周期

请给出简明的情绪分析结论：
- 当前市场情绪（乐观/中性/悲观）
- 情绪趋势（升温/降温/稳定）
- 主要舆论焦点
- 投资建议（强烈买入/买入/持有/卖出/强烈卖出）

请用中文回复。"""

            # 使用模型路由进行分析
            from ..core.router import ModelRouter
            router = ModelRouter()
            analysis = await router.route(task_type, prompt)

            return analysis

        except Exception as e:
            logger.error(f"❌ SentimentAgent 分析失败: {e}")
            return f"分析失败: {str(e)}"
