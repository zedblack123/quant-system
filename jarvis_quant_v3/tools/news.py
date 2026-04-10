"""
新闻搜索工具
获取财经新闻和市场资讯
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .base import BaseTool, PermissionLevel


class NewsSearchTool(BaseTool):
    """新闻搜索工具"""
    
    def __init__(self):
        """初始化新闻搜索工具"""
        super().__init__(
            name="news_search",
            description="获取财经新闻、市场资讯和公司公告",
            version="1.0.0"
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行新闻搜索
        
        Args:
            query: 搜索关键词
            source: 新闻来源 ('all', 'eastmoney', 'sina', 'xueqiu', 'announcement')
            stock_code: 股票代码 (用于获取相关新闻)
            days: 获取最近几天的新闻 (默认7)
            limit: 返回数量限制 (默认20)
            
        Returns:
            新闻数据
        """
        try:
            query = kwargs.get('query', '')
            source = kwargs.get('source', 'all')
            stock_code = kwargs.get('stock_code')
            days = kwargs.get('days', 7)
            limit = kwargs.get('limit', 20)
            
            # 根据来源获取新闻
            if source == 'all' or source == 'eastmoney':
                news_data = self._get_eastmoney_news(query, days, limit)
            elif source == 'sina':
                news_data = self._get_sina_news(query, days, limit)
            elif source == 'xueqiu':
                news_data = self._get_xueqiu_news(query, days, limit)
            elif source == 'announcement':
                if not stock_code:
                    return {
                        "success": False,
                        "error": "获取公告需要股票代码",
                        "data": None
                    }
                news_data = self._get_announcements(stock_code, days, limit)
            else:
                return {
                    "success": False,
                    "error": f"不支持的新闻来源: {source}",
                    "data": None
                }
            
            # 如果指定了股票代码，过滤相关新闻
            if stock_code and source != 'announcement':
                news_data = self._filter_related_news(news_data, stock_code)
            
            # 分析新闻情感
            sentiment_analysis = self._analyze_sentiment(news_data)
            
            return {
                "success": True,
                "data": {
                    "query": query,
                    "source": source,
                    "stock_code": stock_code,
                    "days": days,
                    "total_count": len(news_data),
                    "news": news_data[:limit],
                    "sentiment_analysis": sentiment_analysis,
                    "timestamp": datetime.now().isoformat()
                },
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"新闻搜索失败: {str(e)}",
                "data": None
            }
    
    def get_permission_level(self) -> PermissionLevel:
        """获取权限级别"""
        return PermissionLevel.LOW
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "source": {
                    "type": "string",
                    "enum": ["all", "eastmoney", "sina", "xueqiu", "announcement"],
                    "description": "新闻来源"
                },
                "stock_code": {
                    "type": "string",
                    "description": "股票代码"
                },
                "days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                    "description": "获取最近几天的新闻"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "返回数量限制"
                }
            },
            "required": []
        }
    
    def _get_tags(self) -> List[str]:
        """获取标签"""
        return ["news", "sentiment", "market", "information"]
    
    def _get_eastmoney_news(self, query: str, days: int, limit: int) -> List[Dict[str, Any]]:
        """获取东方财富新闻"""
        try:
            # 获取财经新闻
            news_df = ak.news_cctv()
            
            # 转换为标准格式
            news_list = []
            for _, row in news_df.iterrows():
                news_item = {
                    "title": str(row.get('新闻标题', '')),
                    "content": str(row.get('新闻内容', '')),
                    "source": "东方财富",
                    "url": str(row.get('新闻链接', '')),
                    "publish_time": str(row.get('新闻发布时间', '')),
                    "category": "财经新闻"
                }
                
                # 过滤关键词
                if query:
                    if query.lower() not in news_item['title'].lower() and \
                       query.lower() not in news_item['content'].lower():
                        continue
                
                news_list.append(news_item)
            
            return news_list[:limit]
            
        except Exception as e:
            print(f"获取东方财富新闻失败: {e}")
            return []
    
    def _get_sina_news(self, query: str, days: int, limit: int) -> List[Dict[str, Any]]:
        """获取新浪财经新闻"""
        try:
            # 获取新浪财经新闻
            news_df = ak.news_report_time()
            
            news_list = []
            for _, row in news_df.iterrows():
                news_item = {
                    "title": str(row.get('title', '')),
                    "content": str(row.get('content', '')),
                    "source": "新浪财经",
                    "url": str(row.get('url', '')),
                    "publish_time": str(row.get('ctime', '')),
                    "category": "财经新闻"
                }
                
                if query:
                    if query.lower() not in news_item['title'].lower():
                        continue
                
                news_list.append(news_item)
            
            return news_list[:limit]
            
        except Exception as e:
            print(f"获取新浪财经新闻失败: {e}")
            return []
    
    def _get_xueqiu_news(self, query: str, days: int, limit: int) -> List[Dict[str, Any]]:
        """获取雪球新闻"""
        try:
            # 获取雪球热门文章
            news_df = ak.stock_news_em()
            
            news_list = []
            for _, row in news_df.iterrows():
                news_item = {
                    "title": str(row.get('标题', '')),
                    "content": str(row.get('内容简介', '')),
                    "source": "雪球",
                    "url": str(row.get('文章链接', '')),
                    "publish_time": str(row.get('发布时间', '')),
                    "author": str(row.get('作者', '')),
                    "read_count": int(row.get('阅读次数', 0)),
                    "category": "投资观点"
                }
                
                if query:
                    if query.lower() not in news_item['title'].lower():
                        continue
                
                news_list.append(news_item)
            
            return news_list[:limit]
            
        except Exception as e:
            print(f"获取雪球新闻失败: {e}")
            return []
    
    def _get_announcements(self, stock_code: str, days: int, limit: int) -> List[Dict[str, Any]]:
        """获取公司公告"""
        try:
            # 获取公司公告
            ann_df = ak.stock_news_em(symbol=stock_code)
            
            news_list = []
            for _, row in ann_df.iterrows():
                news_item = {
                    "title": str(row.get('公告标题', '')),
                    "content": str(row.get('公告内容', '')),
                    "source": "公司公告",
                    "url": str(row.get('公告链接', '')),
                    "publish_time": str(row.get('公告日期', '')),
                    "stock_code": stock_code,
                    "category": "公司公告"
                }
                
                news_list.append(news_item)
            
            return news_list[:limit]
            
        except Exception as e:
            print(f"获取公司公告失败: {e}")
            return []
    
    def _filter_related_news(self, news_list: List[Dict[str, Any]], stock_code: str) -> List[Dict[str, Any]]:
        """过滤与股票相关的新闻"""
        if not news_list:
            return []
        
        # 股票名称关键词（这里需要根据实际情况扩展）
        stock_keywords = [
            stock_code,
            f"{stock_code[:2]}{stock_code[2:]}",  # 去除市场前缀
            f"股票代码{stock_code}",
            f"代码{stock_code}"
        ]
        
        related_news = []
        for news in news_list:
            title = news.get('title', '').lower()
            content = news.get('content', '').lower()
            
            # 检查是否包含股票关键词
            for keyword in stock_keywords:
                if keyword.lower() in title or keyword.lower() in content:
                    related_news.append(news)
                    break
        
        return related_news
    
    def _analyze_sentiment(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析新闻情感"""
        if not news_list:
            return {
                "overall_sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        # 简单的情感关键词分析
        positive_keywords = [
            '上涨', '增长', '盈利', '利好', '突破', '创新高', '看好', '推荐',
            '买入', '增持', '牛市', '反弹', '复苏', '改善', '超预期'
        ]
        
        negative_keywords = [
            '下跌', '亏损', '利空', '跌破', '创新低', '看空', '减持',
            '卖出', '熊市', '回调', '衰退', '恶化', '不及预期', '风险'
        ]
        
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for news in news_list:
            title = news.get('title', '')
            content = news.get('content', '')
            
            text = f"{title} {content}"
            text_lower = text.lower()
            
            # 计算情感分数
            positive_score = sum(1 for keyword in positive_keywords if keyword in text)
            negative_score = sum(1 for keyword in negative_keywords if keyword in text)
            
            total_score = positive_score - negative_score
            
            if total_score > 0:
                sentiment = "POSITIVE"
                positive_count += 1
            elif total_score < 0:
                sentiment = "NEGATIVE"
                negative_count += 1
            else:
                sentiment = "NEUTRAL"
                neutral_count += 1
            
            sentiment_scores.append(total_score)
            
            # 添加情感分析结果到新闻
            news['sentiment'] = sentiment
            news['sentiment_score'] = total_score
        
        # 计算总体情感
        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        if avg_score > 0.5:
            overall_sentiment = "STRONGLY_POSITIVE"
        elif avg_score > 0:
            overall_sentiment = "POSITIVE"
        elif avg_score < -0.5:
            overall_sentiment = "STRONGLY_NEGATIVE"
        elif avg_score < 0:
            overall_sentiment = "NEGATIVE"
        else:
            overall_sentiment = "NEUTRAL"
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(avg_score, 2),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "total_news": len(news_list),
            "sentiment_distribution": {
                "positive": round(positive_count / len(news_list), 2) if news_list else 0,
                "negative": round(negative_count / len(news_list), 2) if news_list else 0,
                "neutral": round(neutral_count / len(news_list), 2) if news_list else 0
            }
        }