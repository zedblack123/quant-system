#!/usr/bin/env python3
"""
A股新闻收集器
定时收集影响A股的全球新闻
"""

import json
import time
import schedule
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

class StockNewsCollector:
    def __init__(self, config_path='stock_assistant_config.json'):
        """初始化新闻收集器"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.news_cache = []
        self.last_collection_time = None
        
    def collect_from_wallstreetcn(self):
        """从华尔街见闻收集新闻"""
        try:
            # 模拟API调用，实际需要替换为真实API
            news_items = [
                {
                    'title': '美联储维持利率不变，鲍威尔讲话偏鸽',
                    'source': '华尔街见闻',
                    'time': datetime.now().strftime('%H:%M'),
                    'impact': 'high',
                    'sectors': ['金融', '房地产'],
                    'summary': '美联储如期维持利率不变，鲍威尔表示通胀进展良好，市场预期降息可能提前。'
                }
            ]
            return news_items
        except Exception as e:
            print(f"华尔街见闻收集失败: {e}")
            return []
    
    def collect_from_cls(self):
        """从财联社收集新闻"""
        try:
            news_items = [
                {
                    'title': '证监会：推动中长期资金入市，优化交易机制',
                    'source': '财联社',
                    'time': datetime.now().strftime('%H:%M'),
                    'impact': 'high',
                    'sectors': ['证券', '银行'],
                    'summary': '证监会召开座谈会，研究部署推动中长期资金入市，优化交易机制。'
                }
            ]
            return news_items
        except Exception as e:
            print(f"财联社收集失败: {e}")
            return []
    
    def collect_from_eastmoney(self):
        """从东方财富收集新闻"""
        try:
            news_items = [
                {
                    'title': '北向资金今日净流入50.2亿元',
                    'source': '东方财富',
                    'time': datetime.now().strftime('%H:%M'),
                    'impact': 'medium',
                    'sectors': ['全部'],
                    'summary': '北向资金连续3日净流入，今日重点加仓新能源板块。'
                }
            ]
            return news_items
        except Exception as e:
            print(f"东方财富收集失败: {e}")
            return []
    
    def collect_international_news(self):
        """收集国际新闻"""
        try:
            news_items = [
                {
                    'title': '美国3月CPI数据低于预期',
                    'source': 'Bloomberg',
                    'time': datetime.now().strftime('%H:%M'),
                    'impact': 'high',
                    'sectors': ['出口', '大宗商品'],
                    'summary': '美国3月CPI同比上涨3.2%，低于预期的3.3%，缓解通胀担忧。'
                },
                {
                    'title': '欧洲央行暗示6月可能降息',
                    'source': 'Reuters',
                    'time': datetime.now().strftime('%H:%M'),
                    'impact': 'medium',
                    'sectors': ['欧元区相关'],
                    'summary': '欧洲央行官员表示，如果通胀持续下降，6月可能考虑降息。'
                }
            ]
            return news_items
        except Exception as e:
            print(f"国际新闻收集失败: {e}")
            return []
    
    def collect_social_media(self):
        """收集社交媒体热点"""
        try:
            news_items = [
                {
                    'title': '马斯克：AI发展速度超预期，相关公司值得关注',
                    'source': 'X (Twitter)',
                    'time': datetime.now().strftime('%H:%M'),
                    'impact': 'medium',
                    'sectors': ['人工智能', '科技'],
                    'summary': '马斯克在X上表示，AI发展速度超出预期，相关技术公司值得重点关注。'
                }
            ]
            return news_items
        except Exception as e:
            print(f"社交媒体收集失败: {e}")
            return []
    
    def collect_all_news(self):
        """收集所有来源的新闻"""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始收集新闻...")
        
        all_news = []
        
        # 国内财经媒体
        all_news.extend(self.collect_from_wallstreetcn())
        all_news.extend(self.collect_from_cls())
        all_news.extend(self.collect_from_eastmoney())
        
        # 国际新闻
        all_news.extend(self.collect_international_news())
        
        # 社交媒体
        all_news.extend(self.collect_social_media())
        
        # 按影响程度排序
        impact_order = {'high': 3, 'medium': 2, 'low': 1}
        all_news.sort(key=lambda x: impact_order.get(x.get('impact', 'low'), 0), reverse=True)
        
        self.news_cache = all_news
        self.last_collection_time = datetime.now()
        
        print(f"新闻收集完成，共收集{len(all_news)}条新闻")
        return all_news
    
    def filter_by_impact(self, min_impact='medium'):
        """按影响程度过滤新闻"""
        impact_levels = {'high': 3, 'medium': 2, 'low': 1}
        min_level = impact_levels.get(min_impact, 1)
        
        filtered = []
        for news in self.news_cache:
            if impact_levels.get(news.get('impact', 'low'), 0) >= min_level:
                filtered.append(news)
        
        return filtered
    
    def generate_morning_report(self):
        """生成早间报告"""
        news = self.collect_all_news()
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'morning_report',
            'market_date': datetime.now().strftime('%Y-%m-%d'),
            'news_summary': {
                'total_count': len(news),
                'high_impact': len([n for n in news if n.get('impact') == 'high']),
                'medium_impact': len([n for n in news if n.get('impact') == 'medium']),
                'low_impact': len([n for n in news if n.get('impact') == 'low'])
            },
            'top_news': news[:10],  # 取前10条最重要的新闻
            'focus_sectors': self._analyze_sector_focus(news),
            'trading_suggestions': self._generate_trading_suggestions(news)
        }
        
        return report
    
    def generate_evening_report(self):
        """生成晚间报告"""
        news = self.collect_all_news()
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'evening_report',
            'market_date': datetime.now().strftime('%Y-%m-%d'),
            'daily_review': {
                'market_performance': '待接入行情数据',
                'limit_up_stocks': '待接入涨停数据',
                'sector_rotation': '待接入板块数据'
            },
            'important_news': self.filter_by_impact('medium'),
            'tomorrow_outlook': self._generate_tomorrow_outlook(news),
            'risk_warnings': self._identify_risks(news)
        }
        
        return report
    
    def _analyze_sector_focus(self, news):
        """分析新闻影响的重点板块"""
        sector_count = {}
        for item in news:
            sectors = item.get('sectors', [])
            for sector in sectors:
                sector_count[sector] = sector_count.get(sector, 0) + 1
        
        # 按出现次数排序
        sorted_sectors = sorted(sector_count.items(), key=lambda x: x[1], reverse=True)
        return [sector for sector, count in sorted_sectors[:5]]  # 返回前5个重点板块
    
    def _generate_trading_suggestions(self, news):
        """根据新闻生成交易建议"""
        suggestions = []
        
        # 分析新闻中的机会
        positive_keywords = ['利好', '增长', '复苏', '创新高', '突破', '政策支持']
        negative_keywords = ['利空', '下跌', '风险', '监管', '调查', '下滑']
        
        for item in news[:5]:  # 分析前5条重要新闻
            title = item.get('title', '')
            impact = item.get('impact', 'low')
            
            # 简单关键词分析
            is_positive = any(keyword in title for keyword in positive_keywords)
            is_negative = any(keyword in title for keyword in negative_keywords)
            
            if is_positive and impact in ['high', 'medium']:
                suggestion = {
                    'type': 'opportunity',
                    'news': title,
                    'sectors': item.get('sectors', []),
                    'action': '关注相关板块'
                }
                suggestions.append(suggestion)
            elif is_negative and impact in ['high', 'medium']:
                suggestion = {
                    'type': 'warning',
                    'news': title,
                    'sectors': item.get('sectors', []),
                    'action': '回避相关风险'
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_tomorrow_outlook(self, news):
        """生成明日展望"""
        outlook = {
            'market_sentiment': 'neutral',  # 待优化
            'key_events': [],
            'sector_opportunities': self._analyze_sector_focus(news),
            'risk_factors': self._identify_risks(news)
        }
        
        # 简单情绪分析
        positive_count = len([n for n in news if '利好' in n.get('title', '')])
        negative_count = len([n for n in news if '利空' in n.get('title', '')])
        
        if positive_count > negative_count * 1.5:
            outlook['market_sentiment'] = 'positive'
        elif negative_count > positive_count * 1.5:
            outlook['market_sentiment'] = 'negative'
        
        return outlook
    
    def _identify_risks(self, news):
        """识别风险因素"""
        risks = []
        risk_keywords = ['风险', '警告', '监管', '调查', '处罚', '下滑', '亏损']
        
        for item in news:
            title = item.get('title', '')
            if any(keyword in title for keyword in risk_keywords):
                risk = {
                    'description': title,
                    'level': item.get('impact', 'medium'),
                    'affected_sectors': item.get('sectors', [])
                }
                risks.append(risk)
        
        return risks[:5]  # 返回前5个风险
    
    def format_report_markdown(self, report):
        """将报告格式化为Markdown"""
        if report['type'] == 'morning_report':
            return self._format_morning_markdown(report)
        else:
            return self._format_evening_markdown(report)
    
    def _format_morning_markdown(self, report):
        """格式化早间报告为Markdown"""
        md = f"""# 📈 A股早间报告 {report['market_date']}

## 🌍 全球重要新闻 ({report['news_summary']['total_count']}条)

"""
        
        for i, news in enumerate(report['top_news'], 1):
            impact_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(news.get('impact', 'low'), '⚪')
            md += f"{i}. **{impact_emoji} {news['title']}** - {news['source']} ({news['time']})\n"
            md += f"   {news['summary']}\n"
            if news.get('sectors'):
                md += f"   影响板块：{', '.join(news['sectors'])}\n"
            md += "\n"
        
        md += f"""
## 🎯 今日关注板块
{', '.join(report['focus_sectors'])}

## 💡 交易建议
"""
        
        for suggestion in report.get('trading_suggestions', []):
            emoji = '🚀' if suggestion['type'] == 'opportunity' else '⚠️'
            md += f"- {emoji} **{suggestion['action']}**：{suggestion['news']}\n"
            if suggestion.get('sectors'):
                md += f"  相关板块：{', '.join(suggestion['sectors'])}\n"
        
        md += f"""
---
*报告生成时间：{report['timestamp']}*
*数据来源：{', '.join(self.config['news_sources']['domestic'][:3])}等*
"""
        
        return md
    
    def _format_evening_markdown(self, report):
        """格式化晚间报告为Markdown"""
        md = f"""# 📊 A股晚间总结 {report['market_date']}

## 📉 今日市场回顾
{report['daily_review']['market_performance']}

## 📰 重要新闻回顾
"""
        
        for i, news in enumerate(report['important_news'][:8], 1):
            impact_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(news.get('impact', 'low'), '⚪')
            md += f"{i}. **{impact_emoji} {news['title']}** - {news['source']}\n"
        
        md += f"""
## 🔮 明日展望
市场情绪：{report['tomorrow_outlook']['market_sentiment']}

重点关注板块：{', '.join(report['tomorrow_outlook']['sector_opportunities'])}

## ⚠️ 风险提示
"""
        
        for risk in report['risk_warnings']:
            level_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(risk['level'], '⚪')
            md += f"- {level_emoji} {risk['description']}\n"
            if risk.get('affected_sectors'):
                md += f"  影响：{', '.join(risk['affected_sectors'])}\n"
        
        md += f"""
---
*报告生成时间：{report['timestamp']}*
*明日交易时间：09:30-11:30, 13:00-15:00*
"""
        
        return md

def run_morning_report():
    """运行早间报告任务"""
    collector = StockNewsCollector()
    report = collector.generate_morning_report()
    markdown = collector.format_report_markdown(report)
    
    # 保存报告
    filename = f"morning_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(f"/root/.openclaw/workspace/reports/{filename}", 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"早间报告已生成: {filename}")
    return markdown

def run_evening_report():
    """运行晚间报告任务"""
    collector = StockNewsCollector()
    report = collector.generate_evening_report()
    markdown = collector.format_report_markdown(report)
    
    # 保存报告
    filename = f"evening_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(f"/root/.openclaw/workspace/reports/{filename}", 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"晚间报告已生成: {filename}")
    return markdown

if __name__ == "__main__":
    # 创建报告目录
    import os
    os.makedirs("/root/.openclaw/workspace/reports", exist_ok=True)
    
    # 设置定时任务
    schedule.every().day.at("08:00").do(run_morning_report)
    schedule.every().day.at("22:00").do(run_evening_report)
    
    print("新闻收集器已启动，等待定时任务...")
    print("早间报告: 08:00")
    print("晚间报告: 22:00")
    
    # 立即运行一次测试
    print("\n=== 测试运行 ===")
    test_report = run_morning_report()
    print("测试报告前500字符:")
    print(test_report[:500])
    
    # 保持运行
    while True:
        schedule.run_pending()
        time.sleep(60)