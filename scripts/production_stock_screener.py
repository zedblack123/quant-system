#!/usr/bin/env python3
"""
A股量化交易系统 - 完整版选股策略 V3
集成第三方Tushare K线数据 + AKShare涨停数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/root/.openclaw/workspace/scripts')

class ProductionStockScreener:
    """
    完整版选股器 V3
    使用第三方Tushare获取稳定K线数据
    """
    
    def __init__(self):
        self._init_data_manager()
        print("✅ 选股系统V3初始化完成")
    
    def _init_data_manager(self):
        """初始化数据管理器"""
        try:
            # 导入V2数据管理器
            sys.path.insert(0, '/root/.openclaw/workspace/scripts')
            from data_manager_tushare import DataManagerV2
            self.dm = DataManagerV2()
        except Exception as e:
            print(f"❌ 数据管理器初始化失败: {e}")
            self.dm = None
    
    def screen_dragon_heads(self, date=None):
        """
        综合选股 - 龙头股筛选
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        print(f"\n🚀 开始选股... ({date})")
        
        # ==================== 1. 获取涨停股池 ====================
        print("📊 获取涨停股池...")
        limit_up_df = self.dm.get_akshare_limit_up(date)
        
        if limit_up_df is None or len(limit_up_df) == 0:
            print("⚠️ 今日无涨停股")
            return []
        
        print(f"✅ 涨停股池: {len(limit_up_df)}只")
        
        # ==================== 2. 获取板块资金流 ====================
        print("💰 获取板块资金流...")
        sector_df = self.dm.get_akshare_sector()
        hot_sectors = self._extract_hot_sectors(sector_df)
        print(f"✅ 热门板块: {len(hot_sectors)}个")
        
        # ==================== 3. 获取指数数据 ====================
        print("📈 获取指数数据...")
        index_df = self.dm.get_tushare_index('000001.SH', 
            (datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
            datetime.now().strftime('%Y%m%d'))
        market_trend = self._analyze_market_trend(index_df)
        print(f"✅ 市场趋势: {market_trend}")
        
        # ==================== 4. 综合评分 ====================
        print("🎯 开始多维度评分...")
        candidates = []
        
        for _, stock in limit_up_df.iterrows():
            try:
                candidate = self._score_stock(stock, hot_sectors)
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                continue
        
        # 按综合评分排序
        candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f"\n✅ 评分完成，共 {len(candidates)} 只候选股")
        
        # 输出TOP10
        if candidates:
            print("\n📊 TOP10 候选股:")
            for i, c in enumerate(candidates[:10], 1):
                print(f"  {i}. {c['name']}({c['code']}) - "
                      f"总分:{c['total_score']:.0f} "
                      f"[涨停:{c['dimensions']['涨停板']:.0f} "
                      f"资金:{c['dimensions']['资金流']:.0f} "
                      f"技术:{c['dimensions']['技术面']:.0f}]")
        
        return candidates
    
    def _extract_hot_sectors(self, sector_df):
        """提取热门板块"""
        hot = set()
        if sector_df is None:
            return hot
        
        try:
            for _, row in sector_df.head(20).iterrows():
                name = str(row.get('名称', ''))
                change = float(row.get('今日涨跌幅', 0))
                
                if change > 2:
                    hot.add(name)
                    
                    # 添加关键词
                    keywords = ['电子', '医药', '新能源', '汽车', '半导体', '军工', 'AI', '软件', '通信']
                    for kw in keywords:
                        if kw in name:
                            hot.add(kw)
        except:
            pass
        
        return hot
    
    def _analyze_market_trend(self, index_df):
        """分析市场趋势"""
        if index_df is None or len(index_df) < 5:
            return "震荡"
        
        try:
            closes = index_df['close'].astype(float).values
            if len(closes) >= 5:
                recent_5d = closes[-5:]
                if all(recent_5d[i] > recent_5d[i-1] for i in range(1, len(recent_5d))):
                    return "上涨"
                elif all(recent_5d[i] < recent_5d[i-1] for i in range(1, len(recent_5d))):
                    return "下跌"
        except:
            pass
        
        return "震荡"
    
    def _score_stock(self, stock, hot_sectors):
        """对单只股票评分"""
        code = str(stock.get('代码', ''))
        name = str(stock.get('名称', ''))
        
        if not code or not name:
            return None
        
        # 基本数据
        zt_stats = str(stock.get('涨停统计', '0/0'))
        continuous = int(stock.get('连板数', 0)) if '连板数' in stock.index else 0
        turnover = float(stock.get('换手率', 0)) if '换手率' in stock.index else 0
        market_cap = float(stock.get('流通市值', 0)) if '流通市值' in stock.index else 0
        amount = float(stock.get('竞价成交额', 0)) if '竞价成交额' in stock.index else 0
        
        # ========== 维度1: 涨停板 (40分) ==========
        dim1 = self._score_limit_up(continuous, amount)
        
        # ========== 维度2: 资金流 (20分) ==========
        dim2 = self._score_money_flow(name, hot_sectors)
        
        # ========== 维度3: 技术面 (25分) ==========
        dim3 = self._score_technical(code)
        
        # ========== 维度4: 基本面 (10分) ==========
        dim4 = self._score_fundamental(market_cap, turnover)
        
        # ========== 维度5: 题材 (15分) ==========
        dim5 = self._score_concept(name)
        
        # ========== 综合评分 ==========
        total = dim1 + dim2 + dim3 + dim4 + dim5
        
        return {
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
            'turnover': turnover,
            'market_cap': market_cap,
            'strategy': self._get_strategy(continuous),
            'action': self._get_action(total, continuous)
        }
    
    def _score_limit_up(self, continuous, amount):
        """涨停板评分 (40分)"""
        score = 0
        
        # 板数评分
        if continuous == 1:
            score += 20  # 首板
        elif continuous == 2:
            score += 28  # 二板
        elif continuous == 3:
            score += 25  # 三板
        elif continuous == 4:
            score += 22  # 四板
        else:
            score += 15
        
        # 封单金额
        if amount >= 1e9:
            score += 10
        elif amount >= 5000e6:
            score += 8
        elif amount >= 2000e6:
            score += 5
        
        return min(score, 40)
    
    def _score_money_flow(self, name, hot_sectors):
        """资金流评分 (20分)"""
        score = 0
        
        # 热门板块
        for sector in hot_sectors:
            if sector in name:
                score += 10
                break
        
        # 题材加分
        hot_keywords = ['AI', '人工智能', '新能源', '半导体', '医药', '军工', '机器人']
        for kw in hot_keywords:
            if kw in name:
                score += 5
                break
        
        return min(score, 20)
    
    def _score_technical(self, code):
        """
        技术面评分 (25分) - 使用真实K线数据
        """
        score = 12  # 基础分
        
        if self.dm is None:
            return score
        
        # 获取K线数据
        kline = self.dm.get_tushare_daily(
            ts_code=f'{code}.SZ' if not code.startswith('6') else f'{code}.SH',
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d')
        )
        
        if kline is None or len(kline) < 10:
            return score
        
        try:
            closes = kline['close'].astype(float).values
            vols = kline['vol'].astype(float).values
            
            if len(closes) < 10:
                return score
            
            # 均线多头
            ma5 = np.mean(closes[-5:])
            ma10 = np.mean(closes[-10:])
            ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else ma10
            
            if ma5 > ma10 > ma20:
                score += 5
            elif ma5 > ma10:
                score += 2
            
            # 近期涨幅
            recent_change = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
            if recent_change > 20:
                score += 5
            elif recent_change > 10:
                score += 3
            elif recent_change > 5:
                score += 1
            
            # 成交量放大
            if len(vols) >= 5:
                avg_vol = np.mean(vols[-10:-1]) if len(vols) >= 10 else np.mean(vols[:-1])
                vol_ratio = vols[-1] / avg_vol if avg_vol > 0 else 1
                
                if vol_ratio >= 2:
                    score += 3
                elif vol_ratio >= 1.5:
                    score += 1
            
        except Exception as e:
            pass
        
        return min(score, 25)
    
    def _score_fundamental(self, market_cap, turnover):
        """基本面评分 (10分)"""
        score = 0
        
        # 市值
        if 10e9 <= market_cap <= 50e9:
            score += 5
        elif 50e9 < market_cap <= 100e9:
            score += 4
        elif 100e9 < market_cap <= 200e9:
            score += 3
        
        # 换手率
        if 5 <= turnover <= 15:
            score += 5
        elif 15 < turnover <= 20:
            score += 3
        elif turnover > 25:
            score -= 2
        
        return min(max(score, 0), 10)
    
    def _score_concept(self, name):
        """题材评分 (15分)"""
        score = 5
        
        concepts = {
            'AI': 10, '人工智能': 10, '大模型': 10,
            '新能源': 8, '锂电池': 8, '储能': 8,
            '半导体': 8, '芯片': 8,
            '医药': 7, '医疗器械': 7,
            '军工': 8, '国防': 8,
            '机器人': 7, '智能制造': 7,
            '数字经济': 6, '云计算': 6,
            '元宇宙': 5, '虚拟现实': 5,
            '碳中和': 6, '国产替代': 7
        }
        
        for concept, weight in concepts.items():
            if concept in name:
                score += weight
                break
        
        return min(score, 15)
    
    def _get_strategy(self, continuous):
        """确定策略"""
        strategies = {1: "首板打板", 2: "二板接力", 3: "三板博弈", 4: "妖股谨慎"}
        return strategies.get(continuous, "强势股")
    
    def _get_action(self, total_score, continuous):
        """确定操作"""
        if continuous >= 5:
            return "⚠️ 风险过高"
        elif total_score >= 80:
            return "✅ 重点关注"
        elif total_score >= 70:
            return "👌 可择机介入"
        elif total_score >= 60:
            return "👀 轻仓试探"
        else:
            return "❌ 观望"
    
    def format_report(self, candidates):
        """格式化报告"""
        if not candidates:
            return "# 🎯 龙头股精选\n\n暂无符合条件的股票\n"
        
        today = datetime.now().strftime('%Y年%m月%d日')
        
        md = f"""# 🎯 龙头股精选报告 V3
## {today}

> 使用第三方Tushare K线数据 + AKShare涨停数据

---

## 📊 综合评分 TOP10

| 排名 | 股票 | 代码 | 评分 | 涨停板 | 换手率 | 操作建议 |
|------|------|------|------|--------|--------|----------|
"""
        
        for i, c in enumerate(candidates[:10], 1):
            emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][i-1]
            turnover_str = f"{c['turnover']:.1f}%" if c['turnover'] else "-"
            
            md += f"| {emoji} | **{c['name']}** | {c['code']} | **{c['total_score']:.0f}** | 第{c['continuous']}板 | {turnover_str} | {c['action']} |\n"
        
        md += """
---

## 📈 详细评分

"""
        
        for i, c in enumerate(candidates[:5], 1):
            dim = c['dimensions']
            md += f"""### {i}. {c['name']} ({c['code']})

**总分**: {c['total_score']:.0f}/100

| 维度 | 评分 | 满分 |
|------|------|------|
| 涨停板 | {dim['涨停板']:.0f} | 40 |
| 资金流 | {dim['资金流']:.0f} | 20 |
| 技术面 | {dim['技术面']:.0f} | 25 |
| 基本面 | {dim['基本面']:.0f} | 10 |
| 题材 | {dim['题材']:.0f} | 15 |

**策略**: {c['strategy']}
**操作**: {c['action']}

---
"""
        
        md += f"""
## ⚠️ 风险提示

1. 仓位控制: 单票≤20%，总仓位≤60%
2. 止损纪律: 亏损≥8%坚决止损
3. 情绪管理: 不盲目追高

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*数据源: 第三方Tushare API + AKShare*
"""
        
        return md
    
    def run_and_save(self):
        """运行选股并保存"""
        candidates = self.screen_dragon_heads()
        report = self.format_report(candidates)
        
        filename = f"龙头股V3_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        filepath = f"/root/.openclaw/workspace/reports/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 报告已保存: {filepath}")
        return candidates, report

def main():
    print("="*60)
    print("🎯 选股系统V3 - 完整版")
    print("="*60)
    
    screener = ProductionStockScreener()
    candidates, report = screener.run_and_save()
    
    if screener.dm:
        screener.dm.close()
    
    print("\n" + "="*60)
    print("✅ 选股完成!")
    print("="*60)

if __name__ == "__main__":
    main()