#!/usr/bin/env python3
"""
A股量化交易系统 - 优化版选股策略
多维度真实数据 + 健壮的网络处理
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import warnings
import time
warnings.filterwarnings('ignore')

sys.path.insert(0, '/root/.openclaw/workspace/scripts')

class OptimizedStockScreener:
    """
    优化版选股器
    - 健壮的网络处理
    - 多维度综合评分
    - 缓存加速
    """
    
    def __init__(self):
        self.cache = {}  # 数据缓存
        self.cache_time = {}  # 缓存时间
        self.cache_valid_seconds = 300  # 缓存5分钟有效
        self._init_data_manager()
        
    def _init_data_manager(self):
        """初始化数据管理器"""
        try:
            from data_manager import DataManager
            self.dm = DataManager()
            print("✅ 数据管理器初始化成功")
        except Exception as e:
            print(f"❌ 数据管理器初始化失败: {e}")
            self.dm = None
    
    def _is_cache_valid(self, key):
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        if key not in self.cache_time:
            return False
        elapsed = (datetime.now() - self.cache_time[key]).total_seconds()
        return elapsed < self.cache_valid_seconds
    
    def _set_cache(self, key, data):
        """设置缓存"""
        self.cache[key] = data
        self.cache_time[key] = datetime.now()
    
    def screen_dragon_heads(self, date=None):
        """
        综合选股策略
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n🚀 开始综合选股... ({date})")
        
        candidates = []
        
        # ==================== 1. 涨停股池 ====================
        print("📊 获取涨停股池...")
        limit_up_df = self._get_limit_up_data(date)
        
        if limit_up_df is None or len(limit_up_df) == 0:
            print("⚠️ 今日无涨停股")
            return []
        
        print(f"✅ 获取到 {len(limit_up_df)} 只涨停股")
        
        # ==================== 2. 板块资金流 ====================
        print("💰 获取板块资金流...")
        sector_flow = self._get_sector_flow_data()
        hot_sectors = self._extract_hot_sectors(sector_flow)
        
        # ==================== 3. 综合评分 ====================
        print("🎯 开始多维度评分...")
        
        scored_stocks = []
        
        for _, stock in limit_up_df.iterrows():
            try:
                candidate = self._score_stock(stock, hot_sectors, sector_flow)
                if candidate:
                    scored_stocks.append(candidate)
            except Exception as e:
                continue
        
        # 按综合评分排序
        scored_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f"\n✅ 综合评分完成，共 {len(scored_stocks)} 只候选股")
        
        # 输出评分分布
        if scored_stocks:
            print("\n📊 TOP10 候选股评分:")
            for i, c in enumerate(scored_stocks[:10], 1):
                print(f"  {i}. {c['name']}({c['code']}) - "
                      f"总分:{c['total_score']:.1f} "
                      f"(涨停:{c['dimensions']['涨停板']:.1f} "
                      f"资金:{c['dimensions']['资金流']:.1f} "
                      f"技术:{c['dimensions']['技术面']:.1f} "
                      f"题材:{c['dimensions']['题材']:.1f})")
        
        return scored_stocks
    
    def _get_limit_up_data(self, date):
        """获取涨停股数据"""
        cache_key = f'limit_up_{date}'
        
        if self._is_cache_valid(cache_key):
            print("📦 使用缓存的涨停数据")
            return self.cache[cache_key]
        
        if self.dm is None:
            return None
        
        try:
            df = self.dm.get_limit_up_stocks(date=date, use_cache=False)
            if df is not None:
                self._set_cache(cache_key, df)
            return df
        except:
            return None
    
    def _get_sector_flow_data(self):
        """获取板块资金流"""
        cache_key = 'sector_flow'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        if self.dm is None:
            return []
        
        try:
            df = self.dm.get_sector_ranking(use_cache=False)
            if df is not None and len(df) > 0:
                self._set_cache(cache_key, df)
                return df
        except:
            pass
        return None
    
    def _extract_hot_sectors(self, sector_df):
        """提取热门板块"""
        hot = set()
        if sector_df is None:
            return hot
        
        try:
            for _, row in sector_df.head(15).iterrows():
                name = str(row.get('名称', ''))
                change = float(row.get('今日涨跌幅', 0))
                
                # 涨幅大于2%或资金流入大为热门
                if change > 2 or abs(float(row.get('今日主力净流入-净额', 0))) > 5e8:
                    hot.add(name)
                    
                    # 添加相似关键词
                    if '电子' in name:
                        hot.add('电子')
                    if '医药' in name:
                        hot.add('医药')
                    if '新能源' in name:
                        hot.add('新能源')
                    if '汽车' in name:
                        hot.add('汽车')
                    if '半导体' in name:
                        hot.add('半导体')
                    if '军工' in name:
                        hot.add('军工')
        except:
            pass
        
        return hot
    
    def _score_stock(self, stock, hot_sectors, sector_df):
        """对单只股票进行多维度评分"""
        
        # 基本信息提取
        code = str(stock.get('代码', ''))
        name = str(stock.get('名称', ''))
        
        if not code or not name:
            return None
        
        # 涨停信息
        zt_stats = str(stock.get('涨停统计', '0/0'))
        zt_parts = zt_stats.split('/')
        zt_times = 0
        try:
            zt_times = int(float(zt_parts[0])) if len(zt_parts) > 0 and zt_parts[0] else 0
        except:
            zt_times = 0
        
        continuous = int(stock.get('连板数', 0)) if '连板数' in stock.index else 0
        turnover = float(stock.get('换手率', 0)) if '换手率' in stock.index else 0
        market_cap = float(stock.get('流通市值', 0)) if '流通市值' in stock.index else 0
        amount = float(stock.get('竞价成交额', 0)) if '竞价成交额' in stock.index else 0
        
        # ========== 维度1: 涨停板评分 (40分) ==========
        dim1 = self._score_limit_up(zt_times, continuous, amount)
        
        # ========== 维度2: 资金流向评分 (25分) ==========
        dim2 = self._score_money_flow(name, code, hot_sectors, sector_df)
        
        # ========== 维度3: 技术面评分 (20分) ==========
        dim3 = self._score_technical_fast(stock)
        
        # ========== 维度4: 基本面评分 (10分) ==========
        dim4 = self._score_fundamental(market_cap, turnover)
        
        # ========== 维度5: 题材概念评分 (15分) ==========
        dim5 = self._score_concept(name, code)
        
        # ========== 综合评分 ==========
        total = dim1 + dim2 + dim3 + dim4 + dim5
        
        candidate = {
            'code': code,
            'name': name,
            'total_score': total,
            'dimensions': {
                '涨停板': dim1,
                '资金流': dim2,
                '技术面': dim3,
                '基本面': dim4,
                '题材': dim5
            },
            'continuous': continuous,
            'zt_times': zt_times,
            'turnover': turnover,
            'market_cap': market_cap,
            'amount': amount,
            'strategy': self._get_strategy(continuous, dim3),
            'action': self._get_action(total, continuous, dim3)
        }
        
        return candidate
    
    def _score_limit_up(self, zt_times, continuous, amount):
        """
        维度1: 涨停板评分 (40分)
        """
        score = 0
        
        # 板数基础分
        if continuous == 1:
            score += 20  # 首板
        elif continuous == 2:
            score += 28  # 二板（溢价高）
        elif continuous == 3:
            score += 25  # 三板
        elif continuous == 4:
            score += 22  # 四板
        elif continuous >= 5:
            score += 15  # 五板以上风险大
        
        # 封单金额加分
        if amount >= 1e9:  # 1亿+
            score += 10
        elif amount >= 5000e6:  # 5000万+
            score += 8
        elif amount >= 2000e6:  # 2000万+
            score += 5
        elif amount >= 1000e6:  # 1000万+
            score += 3
        
        # 换手率加分（健康换手）
        if 5 <= self._get_turnover() <= 15:
            score += 2
        
        return min(score, 40)
    
    def _score_money_flow(self, name, code, hot_sectors, sector_df):
        """
        维度2: 资金流向评分 (25分)
        """
        score = 0
        
        # 所属热门板块
        for sector in hot_sectors:
            if sector in name:
                score += 8
                break
        
        # 检查板块资金排名
        if sector_df is not None:
            for _, row in sector_df.head(10).iterrows():
                sector_name = str(row.get('名称', ''))
                if sector_name in name:
                    score += 5
                    flow = float(row.get('今日主力净流入-净额', 0))
                    if flow > 1e9:  # 亿级以上
                        score += 5
                    elif flow > 5e8:
                        score += 3
                    break
        
        # 题材关键词加分
        hot_keywords = ['AI', '人工智能', '新能源', '半导体', '芯片', 
                       '医药', '军工', '机器人', '数字经济']
        for kw in hot_keywords:
            if kw in name:
                score += 3
                break
        
        return min(score, 25)
    
    def _score_technical_fast(self, stock):
        """
        维度3: 技术面评分 (20分) - 快速版
        基于涨停股本身的字段进行评估
        """
        score = 10  # 基础分
        
        # 换手率评估
        turnover = float(stock.get('换手率', 0)) if '换手率' in stock.index else 0
        
        if 5 <= turnover <= 15:
            score += 5  # 健康换手
        elif 15 < turnover <= 20:
            score += 3  # 偏高但可接受
        elif turnover > 25:
            score -= 3  # 过高可能有主力出货
        
        # 流通市值评估（适中更好）
        market_cap = float(stock.get('流通市值', 0)) if '流通市值' in stock.index else 0
        
        if 20e9 <= market_cap <= 100e9:
            score += 5  # 中小盘弹性好
        elif 10e9 <= market_cap <= 20e9:
            score += 3
        elif market_cap > 200e9:
            score -= 3  # 大盘股弹性差
        
        return min(max(score, 0), 20)  # 0-20分
    
    def _score_technical_with_kline(self, code):
        """
        维度3: 技术面评分 (20分) - K线版
        需要获取K线数据计算
        """
        score = 10  # 基础分
        
        if self.dm is None:
            return score
        
        # 限制K线获取数量，避免超时
        cache_key = f'kline_{code}'
        
        try:
            # 使用缓存或获取新数据
            if self._is_cache_valid(cache_key):
                kline = self.cache[cache_key]
            else:
                # 获取少量K线数据（加快速度）
                kline = self.dm.get_stock_history(code, count=10)
                if kline is not None and len(kline) >= 5:
                    self._set_cache(cache_key, kline)
                else:
                    return score
            
            if kline is None or len(kline) < 5:
                return score
            
            # 计算简化技术指标
            closes = []
            try:
                if '收盘' in kline.columns:
                    closes = [float(x) for x in kline['收盘'].values]
                elif 'close' in kline.columns:
                    closes = [float(x) for x in kline['close'].values]
            except:
                return score
            
            if len(closes) < 5:
                return score
            
            # 均线多头排列
            ma5 = np.mean(closes[-5:])
            ma10 = np.mean(closes[-10:]) if len(closes) >= 10 else ma5
            
            if ma5 > ma10:
                score += 3
            
            # 近期涨幅
            if len(closes) >= 5:
                recent_change = (closes[-1] - closes[-5]) / closes[-5] * 100
                if recent_change > 20:
                    score += 3
                elif recent_change > 10:
                    score += 2
                elif recent_change > 5:
                    score += 1
            
        except Exception as e:
            pass
        
        return min(max(score, 0), 20)
    
    def _score_fundamental(self, market_cap, turnover):
        """
        维度4: 基本面评分 (10分)
        """
        score = 0
        
        # 流通市值评分
        if 10e9 <= market_cap <= 50e9:
            score += 5
        elif 50e9 < market_cap <= 100e9:
            score += 4
        elif 100e9 < market_cap <= 200e9:
            score += 3
        elif 1e9 <= market_cap < 10e9:
            score += 2
        
        # 换手率评分
        if 3 <= turnover <= 10:
            score += 5
        elif 10 < turnover <= 15:
            score += 4
        elif 15 < turnover <= 20:
            score += 2
        elif turnover > 25:
            score -= 2  # 过高风险
        
        return min(max(score, 0), 10)
    
    def _score_concept(self, name, code):
        """
        维度5: 题材概念评分 (15分)
        """
        score = 5  # 基础分
        
        # 热门题材
        hot_concepts = {
            'AI': 8, '人工智能': 8, 'ChatGPT': 8,
            '大模型': 8, '大语言模型': 8,
            '新能源': 7, '锂电池': 7, '储能': 7, '光伏': 7,
            '半导体': 7, '芯片': 7, '集成电路': 7,
            '医药': 6, '医疗器械': 6,
            '军工': 7, '国防': 7,
            '机器人': 6, '智能制造': 6,
            '数字经济': 6, '云计算': 6, '大数据': 5,
            '元宇宙': 5, '虚拟现实': 5,
            '稀土': 5, '资源': 4,
            '碳中和': 6, '环保': 5,
            '国产替代': 7, '自主可控': 7,
            '专精特新': 6
        }
        
        max_score = 0
        for concept, weight in hot_concepts.items():
            if concept in name:
                max_score = max(max_score, weight)
        
        score += max_score
        
        return min(score, 15)
    
    def _get_strategy(self, continuous, tech_score):
        """确定策略"""
        if continuous == 1:
            return "首板打板"
        elif continuous == 2:
            return "二板接力"
        elif continuous == 3:
            return "三板博弈"
        elif continuous >= 4:
            return "妖股高危"
        else:
            return "首板打板"
    
    def _get_action(self, total_score, continuous, tech_score):
        """确定操作建议"""
        if continuous >= 5:
            return "⚠️ 风险过高，不建议"
        elif total_score >= 80:
            return "✅ 重点关注"
        elif total_score >= 70:
            if continuous <= 2:
                return "✅ 可择机介入"
            else:
                return "⚠️ 谨慎参与"
        elif total_score >= 60:
            if continuous <= 3:
                return "👌 轻仓试探"
            else:
                return "⚠️ 不建议"
        elif total_score >= 50:
            return "👀 观望为主"
        else:
            return "❌ 暂不关注"
    
    def _get_turnover(self):
        """获取当前换手率（临时存储）"""
        return 0
    
    def _format_market_cap(self, cap):
        """格式化市值"""
        if cap is None or cap == 0:
            return "-"
        if cap >= 1e9:
            return f"{cap/1e9:.1f}亿"
        return f"{cap/1e6:.0f}万"
    
    def format_report(self, candidates):
        """格式化选股报告"""
        if not candidates:
            return "# 🎯 龙头股精选报告\n\n暂无符合条件的股票\n"
        
        today = datetime.now().strftime('%Y年%m月%d日')
        
        md = f"""# 🎯 龙头股精选报告
## {today}

---

## 📊 综合评分 TOP10

| 排名 | 股票名称 | 代码 | 综合评分 | 涨停板 | 换手率 | 流通市值 | 操作建议 |
|------|----------|------|----------|--------|--------|----------|----------|
"""
        
        for i, c in enumerate(candidates[:10], 1):
            rank_emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][i-1]
            
            turnover_str = f"{c['turnover']:.2f}%" if c['turnover'] else "-"
            cap_str = self._format_market_cap(c['market_cap'])
            
            md += f"| {rank_emoji} | **{c['name']}** | {c['code']} | **{c['total_score']:.1f}** | 第{c['continuous']}板 | {turnover_str} | {cap_str} | {c['action']} |\n"
        
        md += """
---

## 📈 详细评分分析

"""
        
        for i, c in enumerate(candidates[:5], 1):
            dim = c['dimensions']
            md += f"""### {i}. {c['name']} ({c['code']})

**综合评分**: {c['total_score']:.1f}/100

| 维度 | 评分 | 满分 |
|------|------|------|
| 涨停板 | {dim['涨停板']:.1f} | 40 |
| 资金流 | {dim['资金流']:.1f} | 25 |
| 技术面 | {dim['技术面']:.1f} | 20 |
| 基本面 | {dim['基本面']:.1f} | 10 |
| 题材 | {dim['题材']:.1f} | 15 |

**策略**: {c['strategy']}
**操作**: {c['action']}

---
"""
        
        md += f"""
## ⚠️ 风险提示

1. **仓位控制**: 单票仓位不超过20%，总仓位不超过60%
2. **止损纪律**: 亏损超过8%坚决止损
3. **情绪管理**: 不要盲目追高，严格执行策略
4. **风险等级**: 市场有风险，投资需谨慎

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*数据来源: AKShare, BaoStock*
*投资有风险，决策需谨慎*
"""
        
        return md
    
    def run_and_save(self):
        """运行选股并保存报告"""
        candidates = self.screen_dragon_heads()
        report = self.format_report(candidates)
        
        filename = f"龙头股精选_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        filepath = f"/root/.openclaw/workspace/reports/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 报告已保存: {filepath}")
        
        return candidates, report

def main():
    print("="*60)
    print("🎯 优化版选股系统 - 多维度真实数据版")
    print("="*60)
    
    screener = OptimizedStockScreener()
    candidates, report = screener.run_and_save()
    
    if screener.dm:
        screener.dm.close()
    
    print("\n" + "="*60)
    print("✅ 选股完成!")
    print("="*60)
    
    print("\n📋 报告预览:")
    print("-"*40)
    print(report[:1200])

if __name__ == "__main__":
    main()