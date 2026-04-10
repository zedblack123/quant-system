#!/usr/bin/env python3
"""
简化版A股龙头股筛选器
不依赖pandas，纯Python实现
"""

import json
from datetime import datetime

class SimpleStockScreener:
    def __init__(self, config_path='stock_assistant_config.json'):
        """初始化筛选器"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.selection_criteria = self.config['stock_selection']
    
    def load_mock_data(self):
        """加载模拟股票数据"""
        stocks = [
            {
                'code': '002415',
                'name': '海康威视',
                'industry': '安防',
                'market_cap': 280000000000,
                'float_market_cap': 210000000000,
                'current_price': 28.6,
                'change_pct': 3.5,
                'volume': 80000000,
                'turnover': 0.08,
                'limit_up': True,
                'limit_up_days': 1,
                'seal_amount': 120000000,
                'volume_ratio': 2.1,
                'technical_score': 78
            },
            {
                'code': '002475',
                'name': '立讯精密',
                'industry': '消费电子',
                'market_cap': 220000000000,
                'float_market_cap': 180000000000,
                'current_price': 31.2,
                'change_pct': 4.2,
                'volume': 120000000,
                'turnover': 0.15,
                'limit_up': True,
                'limit_up_days': 2,
                'seal_amount': 85000000,
                'volume_ratio': 3.2,
                'technical_score': 85
            },
            {
                'code': '002049',
                'name': '紫光国微',
                'industry': '半导体',
                'market_cap': 95000000000,
                'float_market_cap': 85000000000,
                'current_price': 78.3,
                'change_pct': 9.98,
                'volume': 65000000,
                'turnover': 0.18,
                'limit_up': True,
                'limit_up_days': 1,
                'seal_amount': 520000000,
                'volume_ratio': 4.5,
                'technical_score': 92
            },
            {
                'code': '603501',
                'name': '韦尔股份',
                'industry': '半导体',
                'market_cap': 120000000000,
                'float_market_cap': 110000000000,
                'current_price': 95.6,
                'change_pct': 6.3,
                'volume': 38000000,
                'turnover': 0.12,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 2.2,
                'technical_score': 75
            },
            {
                'code': '000001',
                'name': '平安银行',
                'industry': '银行',
                'market_cap': 350000000000,
                'float_market_cap': 280000000000,
                'current_price': 10.5,
                'change_pct': 1.2,
                'volume': 50000000,
                'turnover': 0.03,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 1.2,
                'technical_score': 65
            }
        ]
        return stocks
    
    def screen_dragon_heads(self):
        """筛选龙头股"""
        stocks = self.load_mock_data()
        dragon_heads = []
        
        for stock in stocks:
            score = 0
            reasons = []
            
            # 1. 涨停筛选
            if stock['limit_up']:
                score += 40
                reasons.append(f"涨停(第{stock['limit_up_days']}板)")
                
                # 封单金额
                if stock['seal_amount'] >= 50000000:
                    score += 20
                    reasons.append(f"封单{stock['seal_amount']/10000:.0f}万")
            else:
                score += 10
                reasons.append("未涨停")
            
            # 2. 量能筛选
            if stock['volume_ratio'] >= 1.5:
                score += 15
                reasons.append(f"量比{stock['volume_ratio']:.1f}")
            
            # 3. 技术面
            if stock['technical_score'] >= 80:
                score += 20
                reasons.append(f"技术强({stock['technical_score']}分)")
            
            # 4. 行业关注
            focus_sectors = self.selection_criteria['sector_focus']
            if stock['industry'] in focus_sectors:
                score += 10
                reasons.append(f"热门{stock['industry']}")
            
            # 总分筛选
            if score >= 70:
                stock['score'] = score
                stock['reasons'] = reasons
                dragon_heads.append(stock)
        
        # 按分数排序
        dragon_heads.sort(key=lambda x: x['score'], reverse=True)
        return dragon_heads
    
    def generate_suggestions(self, dragon_heads, capital=1000000):
        """生成交易建议"""
        suggestions = []
        
        for i, stock in enumerate(dragon_heads[:3]):  # 只取前3个
            # 计算建议仓位（15%-25%）
            position_ratio = 0.15 + (0.05 * i)
            suggested_amount = capital * position_ratio
            shares = int(suggested_amount / stock['current_price'] / 100) * 100
            
            suggestion = {
                'rank': i + 1,
                'code': stock['code'],
                'name': stock['name'],
                'industry': stock['industry'],
                'price': stock['current_price'],
                'change': stock['change_pct'],
                'score': stock['score'],
                'reasons': stock['reasons'],
                'suggested_shares': shares,
                'suggested_amount': suggested_amount,
                'stop_loss': stock['current_price'] * 0.92,  # -8%
                'take_profit': stock['current_price'] * 1.20  # +20%
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def format_report(self, suggestions):
        """格式化报告"""
        if not suggestions:
            return "暂无符合条件的龙头股"
        
        report = f"""# 🎯 A股龙头股精选报告
*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 精选股票 ({len(suggestions)}只)

"""
        
        for sug in suggestions:
            rank_emoji = ['🥇', '🥈', '🥉'][sug['rank'] - 1]
            
            report += f"""{rank_emoji} **{sug['name']}** ({sug['code']})
- **行业**：{sug['industry']}
- **当前价**：{sug['price']}元 ({sug['change']:+.1f}%)
- **综合评分**：{sug['score']}/100

**入选理由**：
"""
            for reason in sug['reasons']:
                report += f"  - {reason}\n"
            
            report += f"""
**交易建议**：
  - 建议买入：{sug['suggested_shares']}股
  - 建议金额：{sug['suggested_amount']:,.0f}元
  - 止损价：{sug['stop_loss']:.2f}元
  - 止盈价：{sug['take_profit']:.2f}元

"""
        
        report += """## ⚠️ 风险提示
1. 以上为模拟选股结果，实际投资需谨慎
2. 建议单票仓位不超过20%
3. 严格执行止损纪律
4. 关注市场整体风险

---
*策略：打板龙头股策略*
*数据：模拟数据，待接入真实行情*
"""
        
        return report

def main():
    """主函数"""
    import os
    os.makedirs("/root/.openclaw/workspace/reports", exist_ok=True)
    
    print("开始选股筛选...")
    
    screener = SimpleStockScreener()
    
    # 筛选龙头股
    dragon_heads = screener.screen_dragon_heads()
    print(f"筛选出{len(dragon_heads)}只龙头股")
    
    # 生成建议
    suggestions = screener.generate_suggestions(dragon_heads)
    
    # 生成报告
    report = screener.format_report(suggestions)
    
    # 保存报告
    filename = f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    filepath = f"/root/.openclaw/workspace/reports/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已保存: {filepath}")
    print("\n=== 报告预览 ===")
    print(report[:800])

if __name__ == "__main__":
    main()