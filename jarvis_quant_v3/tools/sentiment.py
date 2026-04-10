"""
社交媒体情感分析工具
分析雪球、股吧等社交媒体的情感倾向
"""

import akshare as ak
import pandas as pd
import jieba
import jieba.analyse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from .base import BaseTool, PermissionLevel


class SocialMediaTool(BaseTool):
    """社交媒体情感分析工具"""
    
    def __init__(self):
        """初始化社交媒体工具"""
        super().__init__(
            name="social_media_sentiment",
            description="分析雪球、东方财富股吧等社交媒体的情感倾向",
            version="1.0.0"
        )
        
        # 初始化jieba
        jieba.initialize()
        
        # 情感词典
        self.positive_words = self._load_sentiment_words('positive')
        self.negative_words = self._load_sentiment_words('negative')
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行社交媒体情感分析
        
        Args:
            stock_code: 股票代码
            platform: 平台 ('xueqiu', 'eastmoney', 'all')
            days: 分析最近几天的数据 (默认3)
            limit: 获取帖子数量限制 (默认100)
            analyze_comments: 是否分析评论 (默认True)
            
        Returns:
            情感分析结果
        """
        try:
            stock_code = kwargs.get('stock_code')
            platform = kwargs.get('platform', 'all')
            days = kwargs.get('days', 3)
            limit = kwargs.get('limit', 100)
            analyze_comments = kwargs.get('analyze_comments', True)
            
            if not stock_code:
                return {
                    "success": False,
                    "error": "股票代码不能为空",
                    "data": None
                }
            
            # 获取社交媒体数据
            posts = []
            if platform in ['all', 'xueqiu']:
                xueqiu_posts = self._get_xueqiu_posts(stock_code, days, limit)
                posts.extend(xueqiu_posts)
            
            if platform in ['all', 'eastmoney']:
                eastmoney_posts = self._get_eastmoney_posts(stock_code, days, limit)
                posts.extend(eastmoney_posts)
            
            if not posts:
                return {
                    "success": True,
                    "data": {
                        "stock_code": stock_code,
                        "platform": platform,
                        "total_posts": 0,
                        "sentiment_analysis": {
                            "overall_sentiment": "NEUTRAL",
                            "sentiment_score": 0.0,
                            "positive_count": 0,
                            "negative_count": 0,
                            "neutral_count": 0
                        },
                        "hot_topics": [],
                        "influential_users": [],
                        "timestamp": datetime.now().isoformat()
                    },
                    "error": None
                }
            
            # 分析情感
            sentiment_results = self._analyze_posts_sentiment(posts)
            
            # 提取热门话题
            hot_topics = self._extract_hot_topics(posts)
            
            # 识别有影响力的用户
            influential_users = self._identify_influential_users(posts)
            
            # 如果需要，分析评论情感
            comment_analysis = None
            if analyze_comments and len(posts) > 0:
                # 获取评论数据（这里简化处理，实际需要调用API）
                comment_analysis = self._analyze_comments_sentiment(posts[:10])  # 分析前10个帖子的评论
            
            return {
                "success": True,
                "data": {
                    "stock_code": stock_code,
                    "platform": platform,
                    "total_posts": len(posts),
                    "posts_sample": posts[:10],  # 返回前10个帖子作为样本
                    "sentiment_analysis": sentiment_results,
                    "hot_topics": hot_topics,
                    "influential_users": influential_users,
                    "comment_analysis": comment_analysis,
                    "timestamp": datetime.now().isoformat()
                },
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"社交媒体分析失败: {str(e)}",
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
                "stock_code": {
                    "type": "string",
                    "description": "股票代码"
                },
                "platform": {
                    "type": "string",
                    "enum": ["xueqiu", "eastmoney", "all"],
                    "description": "社交媒体平台"
                },
                "days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                    "description": "分析最近几天的数据"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 500,
                    "description": "获取帖子数量限制"
                },
                "analyze_comments": {
                    "type": "boolean",
                    "description": "是否分析评论"
                }
            },
            "required": ["stock_code"]
        }
    
    def _get_tags(self) -> List[str]:
        """获取标签"""
        return ["social_media", "sentiment", "xueqiu", "股吧", "情感分析"]
    
    def _load_sentiment_words(self, sentiment_type: str) -> set:
        """加载情感词典"""
        # 这里可以加载外部情感词典文件
        # 为了简化，我们先使用内置词典
        
        if sentiment_type == 'positive':
            return {
                '涨', '上涨', '大涨', '暴涨', '拉升', '突破', '创新高', '看好',
                '推荐', '买入', '增持', '牛市', '反弹', '复苏', '利好', '机会',
                '价值', '低估', '优质', '龙头', '成长', '业绩', '盈利', '超预期',
                '强势', '主升', '行情', '机会', '黄金', '钻石', '牛股', '黑马'
            }
        else:  # negative
            return {
                '跌', '下跌', '大跌', '暴跌', '跌破', '创新低', '看空', '减持',
                '卖出', '熊市', '回调', '衰退', '利空', '风险', '亏损', '暴雷',
                '问题', '危机', '警告', '谨慎', '回避', '垃圾', '泡沫', '崩盘',
                '套牢', '割肉', '跑路', '骗局', '造假', '退市', 'st', '*st'
            }
    
    def _get_xueqiu_posts(self, stock_code: str, days: int, limit: int) -> List[Dict[str, Any]]:
        """获取雪球帖子"""
        try:
            # 使用akshare获取雪球讨论
            # 注意：akshare可能没有直接的雪球帖子接口，这里使用简化方法
            posts = []
            
            # 获取雪球热门讨论
            hot_df = ak.stock_news_em()
            
            for _, row in hot_df.iterrows():
                title = str(row.get('标题', ''))
                content = str(row.get('内容简介', ''))
                
                # 检查是否包含股票代码
                if stock_code in title or stock_code in content:
                    post = {
                        "platform": "雪球",
                        "title": title,
                        "content": content,
                        "author": str(row.get('作者', '')),
                        "publish_time": str(row.get('发布时间', '')),
                        "read_count": int(row.get('阅读次数', 0)),
                        "like_count": int(row.get('点赞数', 0)),
                        "comment_count": int(row.get('评论数', 0)),
                        "url": str(row.get('文章链接', ''))
                    }
                    posts.append(post)
                    
                    if len(posts) >= limit:
                        break
            
            return posts
            
        except Exception as e:
            print(f"获取雪球帖子失败: {e}")
            return []
    
    def _get_eastmoney_posts(self, stock_code: str, days: int, limit: int) -> List[Dict[str, Any]]:
        """获取东方财富股吧帖子"""
        try:
            # 获取股吧讨论
            guba_df = ak.stock_guba_sina(symbol=stock_code)
            
            posts = []
            for _, row in guba_df.iterrows():
                post = {
                    "platform": "东方财富股吧",
                    "title": str(row.get('title', '')),
                    "content": str(row.get('content', '')),
                    "author": str(row.get('author', '')),
                    "publish_time": str(row.get('create_time', '')),
                    "read_count": int(row.get('read', 0)),
                    "like_count": int(row.get('like', 0)),
                    "comment_count": int(row.get('comment', 0)),
                    "url": f"https://guba.eastmoney.com/list,{stock_code}.html"
                }
                posts.append(post)
                
                if len(posts) >= limit:
                    break
            
            return posts
            
        except Exception as e:
            print(f"获取股吧帖子失败: {e}")
            return []
    
    def _analyze_posts_sentiment(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析帖子情感"""
        if not posts:
            return {
                "overall_sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "sentiment_trend": "STABLE"
            }
        
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # 分析每个帖子的情感
        for post in posts:
            title = post.get('title', '')
            content = post.get('content', '')
            
            text = f"{title} {content}"
            
            # 计算情感分数
            sentiment_score = self._calculate_text_sentiment(text)
            sentiment_scores.append(sentiment_score)
            
            # 分类
            if sentiment_score > 0.1:
                sentiment = "POSITIVE"
                positive_count += 1
            elif sentiment_score < -0.1:
                sentiment = "NEGATIVE"
                negative_count += 1
            else:
                sentiment = "NEUTRAL"
                neutral_count += 1
            
            post['sentiment'] = sentiment
            post['sentiment_score'] = sentiment_score
        
        # 计算总体情感
        avg_score = sum(sentiment_scores) / len(sentiment_scores)
        
        if avg_score > 0.3:
            overall_sentiment = "STRONGLY_POSITIVE"
        elif avg_score > 0.1:
            overall_sentiment = "POSITIVE"
        elif avg_score < -0.3:
            overall_sentiment = "STRONGLY_NEGATIVE"
        elif avg_score < -0.1:
            overall_sentiment = "NEGATIVE"
        else:
            overall_sentiment = "NEUTRAL"
        
        # 分析情感趋势（如果有时间数据）
        sentiment_trend = self._analyze_sentiment_trend(posts)
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(avg_score, 3),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "sentiment_distribution": {
                "positive": round(positive_count / len(posts), 3),
                "negative": round(negative_count / len(posts), 3),
                "neutral": round(neutral_count / len(posts), 3)
            },
            "sentiment_trend": sentiment_trend,
            "score_range": {
                "min": round(min(sentiment_scores), 3),
                "max": round(max(sentiment_scores), 3),
                "std": round(pd.Series(sentiment_scores).std(), 3) if len(sentiment_scores) > 1 else 0
            }
        }
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """计算文本情感分数"""
        if not text:
            return 0.0
        
        # 分词
        words = jieba.lcut(text)
        
        # 统计情感词
        positive_count = 0
        negative_count = 0
        
        for word in words:
            if word in self.positive_words:
                positive_count += 1
            elif word in self.negative_words:
                negative_count += 1
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        # 计算情感分数
        sentiment_score = (positive_count - negative_count) / total_words
        
        return sentiment_score
    
    def _analyze_sentiment_trend(self, posts: List[Dict[str, Any]]) -> str:
        """分析情感趋势"""
        if len(posts) < 5:
            return "INSUFFICIENT_DATA"
        
        # 按时间排序（假设有publish_time字段）
        try:
            time_sorted_posts = sorted(
                [p for p in posts if 'publish_time' in p],
                key=lambda x: x['publish_time']
            )
            
            if len(time_sorted_posts) < 3:
                return "STABLE"
            
            # 计算早期和晚期的平均情感
            early_posts = time_sorted_posts[:len(time_sorted_posts)//3]
            late_posts = time_sorted_posts[-len(time_sorted_posts)//3:]
            
            early_avg = sum(p.get('sentiment_score', 0) for p in early_posts) / len(early_posts)
            late_avg = sum(p.get('sentiment_score', 0) for p in late_posts) / len(late_posts)
            
            if late_avg - early_avg > 0.1:
                return "IMPROVING"
            elif early_avg - late_avg > 0.1:
                return "DETERIORATING"
            else:
                return "STABLE"
                
        except:
            return "UNKNOWN"
    
    def _extract_hot_topics(self, posts: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        """提取热门话题"""
        if not posts:
            return []
        
        all_text = ' '.join([f"{p.get('title', '')} {p.get('content', '')}" for p in posts])
        
        # 使用TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(
            all_text, 
            topK=top_n, 
            withWeight=True,
            allowPOS=('n', 'vn', 'v', 'nr', 'ns', 'nt', 'nz')
        )
        
        hot_topics = []
        for keyword, weight in keywords:
            # 统计关键词出现频率
            frequency = sum(1 for p in posts if keyword in p.get('title', '') or keyword in p.get('content', ''))
            
            hot_topics.append({
                "keyword": keyword,
                "weight": round(weight, 4),
                "frequency": frequency,
                "sentiment": self._calculate_topic_sentiment(posts, keyword)
            })
        
        return hot_topics
    
    def _calculate_topic_sentiment(self, posts: List[Dict[str, Any]], keyword: str) -> str:
        """计算话题情感"""
        related_posts = [p for p in posts if keyword in p.get('title', '') or keyword in p.get('content', '')]
        
        if not related_posts:
            return "NEUTRAL"
        
        avg_score = sum(p.get('sentiment_score', 0) for p in related_posts) / len(related_posts)
        
        if avg_score > 0.1:
            return "POSITIVE"
        elif avg_score < -0.1:
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    def _identify_influential_users(self, posts: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        """识别有影响力的用户"""
        if not posts:
            return []
        
        user_stats = {}
        
        for post in posts:
            author = post.get('author', '')
            if not author:
                continue
            
            if author not in user_stats:
                user_stats[author] = {
                    "post_count": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_reads": 0,
                    "avg_sentiment": 0,
                    "sentiment_scores": []
                }
            
            stats = user_stats[author]
            stats["post_count"] += 1
            stats["total_likes"] += post.get('like_count', 0)
            stats["total_comments"] += post.get('comment_count', 0)
            stats["total_reads"] += post.get('read_count', 0)
            stats["sentiment_scores"].append(post.get('sentiment_score', 0))
        
        # 计算平均情感
        for author, stats in user_stats.items():
            if stats["sentiment_scores"]:
                stats["avg_sentiment"] = sum(stats["sentiment_scores"]) / len(stats["sentiment_scores"])
            else:
                stats["avg_sentiment"] = 0
        
        # 计算影响力分数
        influential_users = []
        for author, stats in user_stats.items():
            # 影响力分数 = 帖子数 * 0.2 + 点赞数 * 0.3 + 评论数 * 0.3 + 阅读数 * 0.2
            influence_score = (
                stats["post_count"] * 0.2 +
                stats["total_likes"] * 0.3 +
                stats["total_comments"] * 0.3 +
                stats["total_reads"] * 0.0001  # 阅读数权重较低
            )
            
            influential_users.append({
                "author": author,
                "influence_score": round(influence_score, 2),
                "post_count": stats["post_count"],
                "total_likes": stats["total_likes"],
                "total_comments": stats["total_comments"],
                "total_reads": stats["total_reads"],
                "avg_sentiment": round(stats["avg_sentiment"], 3),
                "sentiment_tendency": "POSITIVE" if stats["avg_sentiment"] > 0.1 else 
                                     "NEGATIVE" if stats["avg_sentiment"] < -0.1 else "NEUTRAL"
            })
        
        # 按影响力分数排序
        influential_users.sort(key=lambda x: x["influence_score"], reverse=True)
        
        return influential_users[:top_n]
    
    def _analyze_comments_sentiment(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析评论情感（简化版）"""
        # 注意：实际应用中需要获取评论数据
        # 这里返回一个模拟结果
        
        return {
            "total_comments_analyzed": 0,  # 实际应用中应该是获取的评论数
            "comment_sentiment": "NEUTRAL",
            "comment_sentiment_score": 0.0,
            "note": "评论分析需要调用具体平台的API获取评论数据"
        }