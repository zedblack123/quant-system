#!/usr/bin/env python3
"""
多源财经新闻爬取模块 V2
整合国内+国外新闻源 + 社交媒体舆情
"""

import requests
import re
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

class MultiSourceNewsCollector:
    """多源新闻收集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, application/xml',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.cache = {}
        self.cache_valid_minutes = 15
        
    def _is_cache_valid(self, key):
        if key not in self.cache:
            return False
        elapsed = (datetime.now() - self.cache[key]['time']).total_seconds()
        return elapsed < self.cache_valid_minutes * 60
    
    def _set_cache(self, key, data):
        self.cache[key] = {'data': data, 'time': datetime.now()}
    
    # ========== 国内新闻源 ==========
    
    def get_tonghuashun_news(self):
        """同花顺财经新闻"""
        cache_key = 'tonghuashun'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        try:
            url = 'https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=&track=website&pagesize=20'
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('data', {}).get('list', [])
                for item in items:
                    news_list.append({
                        'source': '同花顺',
                        'title': item.get('title', ''),
                        'time': datetime.fromtimestamp(int(item.get('ctime', 0))).strftime('%H:%M'),
                        'url': item.get('url', ''),
                        'impact': self._estimate_impact(item.get('title', ''))
                    })
        except Exception as e:
            print(f"同花顺新闻失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    # ========== 国外新闻源 ==========
    
    def get_cnbc_news(self):
        """CNBC美国财经新闻"""
        cache_key = 'cnbc'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        try:
            url = 'https://www.cnbc.com/id/100003114/device/rss/rss.html'
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)
                for item in items[:10]:
                    title = re.search(r'<title>(.*?)</title>', item)
                    link = re.search(r'<link>(.*?)</link>', item)
                    if title and title.group(1) != 'US Top News and Analysis':
                        news_list.append({
                            'source': 'CNBC',
                            'title': title.group(1).strip(),
                            'time': datetime.now().strftime('%H:%M'),
                            'url': link.group(1).strip() if link else '',
                            'impact': self._estimate_impact(title.group(1))
                        })
        except Exception as e:
            print(f"CNBC新闻失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_bbc_world_news(self):
        """BBC国际新闻"""
        cache_key = 'bbc_world'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        try:
            url = 'https://feeds.bbci.co.uk/news/world/rss.xml'
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
                descriptions = re.findall(r'<description><!\[CDATA\[(.*?)\]\]></description>', resp.text)
                for i, title in enumerate(titles[2:12]):  # 跳过前两个(BBC News和标题)
                    if len(title) > 10:
                        news_list.append({
                            'source': 'BBC',
                            'title': title,
                            'time': datetime.now().strftime('%H:%M'),
                            'url': '',
                            'impact': self._estimate_impact(title)
                        })
        except Exception as e:
            print(f"BBC新闻失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_google_news_china(self):
        """Google News中国新闻"""
        cache_key = 'google_news'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        try:
            url = 'https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans'
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                items = re.findall(r'<item>(.*?)</item>', resp.text, re.DOTALL)
                for item in items[:15]:
                    title = re.search(r'<title>(.*?)</title>', item)
                    link = re.search(r'<link>(.*?)</link>', item)
                    if title:
                        t = title.group(1).replace('<![CDATA[', '').replace(']]>', '')
                        if 'Google 新闻' not in t and len(t) > 10:
                            news_list.append({
                                'source': 'Google News',
                                'title': t,
                                'time': datetime.now().strftime('%H:%M'),
                                'url': link.group(1) if link else '',
                                'impact': self._estimate_impact(t)
                            })
        except Exception as e:
            print(f"Google新闻失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    # ========== 社交媒体 ==========
    
    def get_twitter_trending(self):
        """Twitter/X 热门话题 (通过Nitter镜像)"""
        cache_key = 'twitter'
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        keywords = ['stock market', 'bitcoin', 'economy', 'Fed', 'inflation']
        
        try:
            # 搜索股市相关热门推文
            for kw in keywords[:2]:
                url = f'https://nitter.net/search?f=tweets&q={kw}&since=&until=&near='
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    tweets = soup.find_all('div', class_='tweet-content')[:3]
                    for tweet in tweets:
                        text = tweet.get_text().strip()
                        if len(text) > 20:
                            news_list.append({
                                'source': 'X/Twitter',
                                'title': text[:100],
                                'time': datetime.now().strftime('%H:%M'),
                                'url': '',
                                'impact': self._estimate_impact(text)
                            })
        except Exception as e:
            print(f"Twitter获取失败: {e}")
        
        self._set_cache(cache_key, news_list[:10])
        return news_list[:10]
    
    # ========== 工具方法 ==========
    
    def _estimate_impact(self, text):
        """简单判断新闻影响方向"""
        text_lower = text.lower()
        
        # 利好关键词
        bullish = ['涨', '涨超', '大涨', '利好', '突破', '增长', '新高', '反弹', '拉升', '买入', '看好', 'surge', 'rise', 'gain', 'bullish', 'rally']
        # 利空关键词  
        bearish = ['跌', '跌超', '大跌', '利空', '破发', '下降', '新低', '跳水', '抛售', '看空', '下跌', 'fall', 'drop', 'crash', 'bearish', 'plunge']
        
        bullish_count = sum(1 for k in bullish if k in text_lower)
        bearish_count = sum(1 for k in bearish if k in text_lower)
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        return 'neutral'
    
    def get_all_news(self):
        """获取所有新闻"""
        all_news = []
        
        print("📰 采集国内新闻...")
        all_news.extend(self.get_tonghuashun_news())
        all_news.extend(self.get_google_news_china())
        
        print("🌍 采集国际新闻...")
        all_news.extend(self.get_cnbc_news())
        all_news.extend(self.get_bbc_world_news())
        
        print("🐦 采集社交媒体...")
        all_news.extend(self.get_twitter_trending())
        
        # 按影响排序：利好 > 利空 > 中性
        impact_order = {'bullish': 0, 'bearish': 1, 'neutral': 2}
        all_news.sort(key=lambda x: (impact_order.get(x.get('impact', 'neutral'), 2), x.get('time', '')))
        
        return all_news
    
    def format_report(self, news_list, title="📊 财经新闻汇总"):
        """格式化新闻报告"""
        now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        
        report = f"""{title}
📅 {now}
{'='*50}

"""
        
        # 按来源分组
        by_source = {}
        for n in news_list:
            src = n.get('source', '其他')
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(n)
        
        for source, items in by_source.items():
            report += f"\n【{source}】\n"
            for item in items[:5]:  # 每个来源最多5条
                impact_icon = {'bullish': '🟢', 'bearish': '🔴', 'neutral': '🟡'}.get(item.get('impact', 'neutral'), '•')
                report += f"{impact_icon} {item.get('title', '')[:60]}\n"
        
        report += f"""
{'='*50}
📊 共 {len(news_list)} 条新闻
🔄 每15分钟自动更新
"""
        return report


def main():
    """测试"""
    collector = MultiSourceNewsCollector()
    
    print("="*60)
    print("📰 多源新闻采集测试")
    print("="*60)
    
    news = collector.get_all_news()
    print(f"\n共采集到 {len(news)} 条新闻")
    
    report = collector.format_report(news)
    print(report)


if __name__ == "__main__":
    main()