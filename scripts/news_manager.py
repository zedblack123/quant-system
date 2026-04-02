#!/usr/bin/env python3
"""
A股量化交易系统 - 新闻模块
集成多源财经新闻
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/root/.openclaw/workspace/scripts')

class NewsManager:
    """
    新闻管理器
    集成AKShare多源财经新闻
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_valid_minutes = 30  # 缓存30分钟
        self._init_akshare()
    
    def _init_akshare(self):
        """初始化AKShare"""
        try:
            import akshare as ak
            self.ak = ak
            print("✅ AKShare 新闻模块初始化成功")
        except Exception as e:
            print(f"❌ AKShare 初始化失败: {e}")
            self.ak = None
    
    def _is_cache_valid(self, key):
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        elapsed = (datetime.now() - self.cache[key]['time']).total_seconds()
        return elapsed < self.cache_valid_minutes * 60
    
    def _set_cache(self, key, data):
        """设置缓存"""
        self.cache[key] = {
            'data': data,
            'time': datetime.now()
        }
    
    def get_all_news(self, date=None):
        """
        获取所有新闻
        date: 日期 (YYYYMMDD)，默认今日
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        all_news = []
        
        # 1. 获取财经要闻（主要来源）
        print("📰 获取财经要闻...")
        finance_news = self.get_finance_news_fast()
        all_news.extend(finance_news)
        
        # 2. 获取国际市场新闻
        print("🌏 获取国际市场新闻...")
        global_news = self.get_global_news_fast()
        all_news.extend(global_news)
        
        # 按时间排序
        all_news.sort(key=lambda x: x.get('time', ''), reverse=True)
        
        return all_news
    
    def get_finance_news_fast(self):
        """快速获取财经要闻"""
        cache_key = 'finance_news_fast'
        
        if self._is_cache_valid(cache_key):
            print("📦 使用缓存")
            return self.cache[cache_key]['data']
        
        news_list = []
        
        if self.ak is None:
            return news_list
        
        try:
            # 获取央视财经新闻
            date_str = datetime.now().strftime('%Y%m%d')
            df = self.ak.news_cctv(date=date_str)
            
            if df is not None and len(df) > 0:
                for _, row in df.head(8).iterrows():
                    try:
                        title = str(row.get('title', ''))
                        content = str(row.get('content', ''))[:150]
                        
                        if len(title) < 10:
                            continue
                        
                        news_list.append({
                            'type': 'finance',
                            'title': title,
                            'content': content,
                            'source': 'CCTV',
                            'time': date_str,
                            'impact': self._assess_impact(title, content)
                        })
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ 央视新闻失败: {e}")
        
        # 获取东方财富财经新闻
        try:
            df = self.ak.stock_news_em(symbol='财经')
            if df is not None and len(df) > 0:
                for _, row in df.head(5).iterrows():
                    try:
                        title = str(row.get('新闻标题', ''))
                        content = str(row.get('新闻内容', ''))[:150]
                        source = str(row.get('文章来源', '东方财富'))
                        pub_time = str(row.get('发布时间', ''))
                        
                        if len(title) < 10:
                            continue
                        
                        news_list.append({
                            'type': 'finance',
                            'title': title,
                            'content': content,
                            'source': source,
                            'time': pub_time,
                            'impact': self._assess_impact(title, content)
                        })
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ 东方财富新闻失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_global_news_fast(self):
        """快速获取国际市场新闻"""
        cache_key = 'global_news_fast'
        
        if self._is_cache_valid(cache_key):
            print("📦 使用缓存")
            return self.cache[cache_key]['data']
        
        news_list = []
        
        if self.ak is None:
            return news_list
        
        try:
            # 获取国际市场新闻
            global_keywords = ['美股', '港股', '原油', '黄金', '美联储']
            
            for kw in global_keywords[:3]:
                try:
                    df = self.ak.stock_news_em(symbol=kw)
                    if df is not None and len(df) > 0:
                        for _, row in df.head(3).iterrows():
                            try:
                                title = str(row.get('新闻标题', ''))
                                content = str(row.get('新闻内容', ''))[:150]
                                source = str(row.get('文章来源', '财经'))
                                pub_time = str(row.get('发布时间', ''))
                                
                                if len(title) < 10:
                                    continue
                                
                                news_list.append({
                                    'type': 'global',
                                    'title': title,
                                    'content': content,
                                    'source': source,
                                    'time': pub_time,
                                    'impact': self._assess_impact(title, content),
                                    'region': kw
                                })
                            except:
                                continue
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 国际新闻失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_finance_news(self):
        """获取财经要闻"""
        cache_key = 'finance_news'
        
        if self._is_cache_valid(cache_key):
            print("📦 使用缓存的财经要闻")
            return self.cache[cache_key]['data']
        
        news_list = []
        
        if self.ak is None:
            return news_list
        
        try:
            # 获取央视财经新闻
            date_str = datetime.now().strftime('%Y%m%d')
            df = self.ak.news_cctv(date=date_str)
            
            if df is not None and len(df) > 0:
                for _, row in df.iterrows():
                    try:
                        title = str(row.get('title', ''))
                        content = str(row.get('content', ''))
                        
                        # 过滤太短的新闻
                        if len(title) < 10:
                            continue
                        
                        news_list.append({
                            'type': 'finance',
                            'title': title,
                            'content': content[:200] + '...' if len(content) > 200 else content,
                            'source': 'CCTV',
                            'time': date_str,
                            'impact': self._assess_impact(title, content)
                        })
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ 央视新闻获取失败: {e}")
        
        # 获取东方财富财经新闻
        try:
            keywords = ['财经', '股市', 'A股', '大盘', '市场']
            for kw in keywords:
                df = self.ak.stock_news_em(symbol=kw)
                if df is not None and len(df) > 0:
                    for _, row in df.iterrows():
                        try:
                            title = str(row.get('关键词', ''))
                            news_title = str(row.get('新闻标题', ''))
                            content = str(row.get('新闻内容', ''))[:200]
                            source = str(row.get('文章来源', '东方财富'))
                            pub_time = str(row.get('发布时间', ''))
                            
                            if len(news_title) < 10:
                                continue
                            
                            news_list.append({
                                'type': 'finance',
                                'title': news_title,
                                'content': content,
                                'source': source,
                                'time': pub_time,
                                'impact': self._assess_impact(news_title, content)
                            })
                        except:
                            continue
        except Exception as e:
            print(f"⚠️ 东方财富新闻获取失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_macro_news(self):
        """获取宏观新闻"""
        cache_key = 'macro_news'
        
        if self._is_cache_valid(cache_key):
            print("📦 使用缓存的宏观新闻")
            return self.cache[cache_key]['data']
        
        news_list = []
        
        if self.ak is None:
            return news_list
        
        try:
            # 获取宏观经济新闻
            keywords = ['央行', '美联储', 'CPI', 'GDP', '利率', '货币', '财政', '政策', '统计局']
            
            for kw in keywords[:5]:  # 限制数量
                try:
                    df = self.ak.stock_news_em(symbol=kw)
                    if df is not None and len(df) > 0:
                        for _, row in df.head(3).iterrows():
                            try:
                                title = str(row.get('新闻标题', ''))
                                content = str(row.get('新闻内容', ''))[:200]
                                source = str(row.get('文章来源', '财经'))
                                pub_time = str(row.get('发布时间', ''))
                                
                                if len(title) < 10:
                                    continue
                                
                                news_list.append({
                                    'type': 'macro',
                                    'title': title,
                                    'content': content,
                                    'source': source,
                                    'time': pub_time,
                                    'impact': self._assess_impact(title, content),
                                    'keywords': kw
                                })
                            except:
                                continue
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 宏观新闻获取失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_industry_news(self):
        """获取行业新闻"""
        cache_key = 'industry_news'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        
        if self.ak is None:
            return news_list
        
        try:
            # 获取行业新闻
            industries = ['新能源', '半导体', '医药', '白酒', '人工智能', '新能源汽车', '军工', '房地产']
            
            for industry in industries[:4]:  # 限制数量
                try:
                    df = self.ak.stock_news_em(symbol=industry)
                    if df is not None and len(df) > 0:
                        for _, row in df.head(2).iterrows():
                            try:
                                title = str(row.get('新闻标题', ''))
                                content = str(row.get('新闻内容', ''))[:200]
                                source = str(row.get('文章来源', '财经'))
                                pub_time = str(row.get('发布时间', ''))
                                
                                if len(title) < 10:
                                    continue
                                
                                news_list.append({
                                    'type': 'industry',
                                    'title': title,
                                    'content': content,
                                    'source': source,
                                    'time': pub_time,
                                    'impact': self._assess_impact(title, content),
                                    'industry': industry
                                })
                            except:
                                continue
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 行业新闻获取失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_company_news(self):
        """获取公司新闻"""
        cache_key = 'company_news'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        
        if self.ak is None:
            return news_list
        
        try:
            # 获取热点公司新闻
            companies = ['宁德时代', '比亚迪', '华为', '腾讯', '阿里巴巴']
            
            for company in companies[:3]:
                try:
                    df = self.ak.stock_news_em(symbol=company)
                    if df is not None and len(df) > 0:
                        for _, row in df.head(2).iterrows():
                            try:
                                title = str(row.get('新闻标题', ''))
                                content = str(row.get('新闻内容', ''))[:200]
                                source = str(row.get('文章来源', '财经'))
                                pub_time = str(row.get('发布时间', ''))
                                
                                if len(title) < 10:
                                    continue
                                
                                news_list.append({
                                    'type': 'company',
                                    'title': title,
                                    'content': content,
                                    'source': source,
                                    'time': pub_time,
                                    'impact': self._assess_impact(title, content),
                                    'company': company
                                })
                            except:
                                continue
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 公司新闻获取失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def get_global_news(self):
        """获取国际市场新闻"""
        cache_key = 'global_news'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        news_list = []
        
        if self.ak is None:
            return news_list
        
        try:
            # 获取国际新闻
            global_keywords = ['美国', '欧洲', '日本', '美联储', '美股', '港股', '原油', '黄金', '汇率']
            
            for kw in global_keywords[:5]:
                try:
                    df = self.ak.stock_news_em(symbol=kw)
                    if df is not None and len(df) > 0:
                        for _, row in df.head(2).iterrows():
                            try:
                                title = str(row.get('新闻标题', ''))
                                content = str(row.get('新闻内容', ''))[:200]
                                source = str(row.get('文章来源', '国际'))
                                pub_time = str(row.get('发布时间', ''))
                                
                                if len(title) < 10:
                                    continue
                                
                                news_list.append({
                                    'type': 'global',
                                    'title': title,
                                    'content': content,
                                    'source': source,
                                    'time': pub_time,
                                    'impact': self._assess_impact(title, content),
                                    'region': kw
                                })
                            except:
                                continue
                except:
                    continue
        except Exception as e:
            print(f"⚠️ 国际新闻获取失败: {e}")
        
        self._set_cache(cache_key, news_list)
        return news_list
    
    def _assess_impact(self, title, content):
        """
        评估新闻对A股的影响
        返回: high, medium, low
        """
        text = (title + content).lower()
        
        # 高影响关键词
        high_keywords = [
            '央行', '降息', '加息', '货币政策', '财政部', '证监会', '银保监会',
            '救市', '重大利好', '重大利空', '暂停ipo', '熔断',
            '中美', '贸易战', '关税', '制裁', '战争'
        ]
        
        # 中等影响关键词
        medium_keywords = [
            '回购', '增持', '减持', '业绩', '财报', '分红', '并购',
            '上市', '科创板', '创业板', '注册制', '北向资金',
            '外资', '净流入', '净流出'
        ]
        
        for kw in high_keywords:
            if kw in text:
                return 'high'
        
        for kw in medium_keywords:
            if kw in text:
                return 'medium'
        
        return 'low'
    
    def get_important_news(self, min_impact='medium'):
        """获取重要新闻（按影响程度过滤）"""
        all_news = self.get_all_news()
        
        impact_order = {'high': 3, 'medium': 2, 'low': 1}
        min_level = impact_order.get(min_impact, 1)
        
        filtered = [n for n in all_news if impact_order.get(n.get('impact', 'low'), 0) >= min_level]
        
        return filtered
    
    def format_news_report(self, news_list, title="财经要闻"):
        """格式化新闻报告"""
        if not news_list:
            return f"# {title}\n\n暂无新闻数据\n"
        
        today = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        
        md = f"""# {title}
## {today}

---
"""
        
        # 按类型分组
        by_type = {}
        for news in news_list:
            news_type = news.get('type', 'other')
            if news_type not in by_type:
                by_type[news_type] = []
            by_type[news_type].append(news)
        
        # 类型名称映射
        type_names = {
            'finance': '📰 财经要闻',
            'macro': '🌍 宏观要闻',
            'industry': '🏭 行业动态',
            'company': '🏢 公司新闻',
            'global': '🌏 国际市场'
        }
        
        for news_type, type_name in type_names.items():
            if news_type in by_type and by_type[news_type]:
                md += f"\n### {type_name}\n\n"
                
                for news in by_type[news_type][:5]:  # 每类最多5条
                    impact = news.get('impact', 'low')
                    impact_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(impact, '⚪')
                    
                    md += f"- **{impact_emoji} {news.get('title', '')}**\n"
                    md += f"  {news.get('content', '')[:100]}...\n"
                    md += f"  来源: {news.get('source', '')} | 时间: {news.get('time', '')}\n\n"
        
        md += f"""
---
*数据来源: AKShare (东方财富, CCTV)*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return md

def test_news():
    """测试新闻模块"""
    print("="*60)
    print("📰 新闻模块测试")
    print("="*60)
    
    nm = NewsManager()
    
    # 获取所有新闻
    print("\n📊 获取所有新闻...")
    all_news = nm.get_all_news()
    print(f"✅ 共获取 {len(all_news)} 条新闻")
    
    # 按类型统计
    by_type = {}
    for news in all_news:
        t = news.get('type', 'other')
        by_type[t] = by_type.get(t, 0) + 1
    
    print("\n📈 新闻分类统计:")
    for t, count in by_type.items():
        print(f"   {t}: {count}条")
    
    # 高影响新闻
    print("\n🔴 高影响新闻:")
    high_news = [n for n in all_news if n.get('impact') == 'high']
    for news in high_news[:5]:
        print(f"   - {news.get('title', '')[:50]}")
    
    # 格式化报告
    print("\n📋 生成新闻报告...")
    report = nm.format_news_report(all_news[:20])
    
    # 保存报告
    filename = f"财经新闻_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    filepath = f"/root/.openclaw/workspace/reports/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存: {filepath}")
    
    # 显示报告预览
    print("\n📄 报告预览:")
    print("-"*40)
    print(report[:800])
    
    return nm, all_news

if __name__ == "__main__":
    nm, news = test_news()
    print("\n✅ 新闻模块测试完成!")