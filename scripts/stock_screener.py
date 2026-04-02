#!/usr/bin/env python3
"""
A股龙头股筛选器
基于打板策略筛选龙头股
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class DragonHeadScreener:
    def __init__(self, config_path='stock_assistant_config.json'):
        """初始化筛选器"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.selection_criteria = self.config['stock_selection']
        
    def load_mock_data(self):
        """加载模拟数据（实际需要接入真实数据源）"""
        # 模拟股票数据
        stocks = [
            {
                'code': '000001',
                'name': '平安银行',
                'industry': '银行',
                'market_cap': 350000000000,  # 3500亿
                'float_market_cap': 280000000000,  # 2800亿
                'current_price': 10.5,
                'change_pct': 1.2,
                'volume': 50000000,
                'turnover': 0.03,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 1.2,
                'technical_score': 65
            },
            {
                'code': '002415',
                'name': '海康威视',
                'industry': '安防',
                'market_cap': 280000000000,  # 2800亿
                'float_market_cap': 210000000000,  # 2100亿
                'current_price': 28.6,
                'change_pct': 3.5,
                'volume': 80000000,
                'turnover': 0.08,
                'limit_up': True,
                'limit_up_days': 1,
                'seal_amount': 120000000,  # 1.2亿
                'volume_ratio': 2.1,
                'technical_score': 78
            },
            {
                'code': '300750',
                'name': '宁德时代',
                'industry': '新能源',
                'market_cap': 850000000000,  # 8500亿
                'float_market_cap': 680000000000,  # 6800亿
                'current_price': 185.3,
                'change_pct': 2.8,
                'volume': 25000000,
                'turnover': 0.12,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 1.5,
                'technical_score': 72
            },
            {
                'code': '002475',
                'name': '立讯精密',
                'industry': '消费电子',
                'market_cap': 220000000000,  # 2200亿
                'float_market_cap': 180000000000,  # 1800亿
                'current_price': 31.2,
                'change_pct': 4.2,
                'volume': 120000000,
                'turnover': 0.15,
                'limit_up': True,
                'limit_up_days': 2,
                'seal_amount': 85000000,  # 8500万
                'volume_ratio': 3.2,
                'technical_score': 85
            },
            {
                'code': '603259',
                'name': '药明康德',
                'industry': '医药',
                'market_cap': 180000000000,  # 1800亿
                'float_market_cap': 150000000000,  # 1500亿
                'current_price': 52.8,
                'change_pct': -1.2,
                'volume': 35000000,
                'turnover': 0.05,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 0.8,
                'technical_score': 58
            },
            {
                'code': '000858',
                'name': '五粮液',
                'industry': '白酒',
                'market_cap': 620000000000,  # 6200亿
                'float_market_cap': 500000000000,  # 5000亿
                'current_price': 128.5,
                'change_pct': 0.8,
                'volume': 18000000,
                'turnover': 0.02,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 0.9,
                'technical_score': 62
            },
            {
                'code': '002049',
                'name': '紫光国微',
                'industry': '半导体',
                'market_cap': 95000000000,  # 950亿
                'float_market_cap': 85000000000,  # 850亿
                'current_price': 78.3,
                'change_pct': 9.98,
                'volume': 65000000,
                'turnover': 0.18,
                'limit_up': True,
                'limit_up_days': 1,
                'seal_amount': 520000000,  # 5.2亿
                'volume_ratio': 4.5,
                'technical_score': 92
            },
            {
                'code': '300059',
                'name': '东方财富',
                'industry': '证券',
                'market_cap': 320000000000,  # 3200亿
                'float_market_cap': 280000000000,  # 2800亿
                'current_price': 14.2,
                'change_pct': 3.1,
                'volume': 95000000,
                'turnover': 0.09,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 1.8,
                'technical_score': 70
            },
            {
                'code': '002594',
                'name': '比亚迪',
                'industry': '新能源汽车',
                'market_cap': 720000000000,  # 7200亿
                'float_market_cap': 600000000000,  # 6000亿
                'current_price': 206.8,
                'change_pct': 2.5,
                'volume': 42000000,
                'turnover': 0.07,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 1.3,
                'technical_score': 68
            },
            {
                'code': '603501',
                'name': '韦尔股份',
                'industry': '半导体',
                'market_cap': 120000000000,  # 1200亿
                'float_market_cap': 110000000000,  # 1100亿
                'current_price': 95.6,
                'change_pct': 6.3,
                'volume': 38000000,
                'turnover': 0.12,
                'limit_up': False,
                'limit_up_days': 0,
                'seal_amount': 0,
                'volume_ratio': 2.2,
                'technical_score': 75
            }
        ]
        
        return pd.DataFrame(stocks)
    
    def identify_dragon_heads(self, stock_data):
        """识别龙头股"""
        criteria = self.selection_criteria['dragon_head_criteria']
        
        filtered_stocks = []
        
        for _, stock in stock_data.iterrows():
            score = 0
            reasons = []
            
            # 1. 市值筛选（小盘股优先）
            market_cap = stock['float_market_cap']
            if 1000000000 <= market_cap <= 20000000000:  # 10亿-200亿
                score += 30
                reasons.append("市值适中(10-200亿)")
            elif market_cap < 1000000000:
                score += 10
                reasons.append("市值过小(<10亿)")
            else:
                score += 20
                reasons.append("市值偏大(>200亿)")
            
            # 2. 涨停情况
            if stock['limit_up']:
                score += 40
                reasons.append(f"今日涨停(第{stock['limit_up_days']}板)")
                
                # 封单金额
                if stock['seal_amount'] >= 50000000:  # 5000万以上
                    score += 20
                    reasons.append(f"封单强劲({stock['seal_amount']/10000:.0f}万)")
                else:
                    score += 10
                    reasons.append(f"封单一般({stock['seal_amount']/10000:.0f}万)")
            else:
                score += 5
                reasons.append("未涨停")
            
            # 3. 成交量筛选
            if stock['volume_ratio'] >= 1.5:
                score += 15
                reasons.append(f"量能充足(量比{stock['volume_ratio']:.1f})")
            elif stock['volume_ratio'] >= 1.0:
                score += 10
                reasons.append(f"量能正常(量比{stock['volume_ratio']:.1f})")
            else:
                score += 5
                reasons.append(f"量能不足(量比{stock['volume_ratio']:.1f})")
            
            # 4. 换手率筛选
            if 0.05 <= stock['turnover'] <= 0.20:
                score += 15
                reasons.append(f"换手合理({stock['turnover']*100:.1f}%)")
            elif stock['turnover'] > 0.20:
                score += 10
                reasons.append(f"换手偏高({stock['turnover']*100:.1f}%)")
            else:
                score += 5
                reasons.append(f"换手偏低({stock['turnover']*100:.1f}%)")
            
            # 5. 技术面评分
            if stock['technical_score'] >= 80:
                score += 20
                reasons.append(f"技术强势({stock['technical_score']}分)")
            elif stock['technical_score'] >= 60:
                score += 15
                reasons.append(f"技术中性({stock['technical_score']}分)")
            else:
                score += 10
                reasons.append(f"技术偏弱({stock['technical_score']}分)")
            
            # 6. 行业关注度（模拟）
            focus_sectors = self.selection_criteria['sector_focus']
            if stock['industry'] in focus_sectors:
                score += 10
                reasons.append(f"热门板块({stock['industry']})")
            
            # 7. 价格走势
            if stock['change_pct'] > 0:
                score += 5
                reasons.append(f"今日上涨({stock['change_pct']:.1f}%)")
            
            # 添加到筛选结果
            if score >= 80:  # 总分阈值
                filtered_stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'industry': stock['industry'],
                    'current_price': stock['current_price'],
                    'change_pct': stock['change_pct'],
                    'score': score,
                    'reasons': reasons,
                    'limit_up': stock['limit_up'],
                    'limit_up_days': stock['limit_up_days'],
                    'seal_amount': stock['seal_amount'],
                    'volume_ratio': stock['volume_ratio'],
                    'turnover': stock['turnover']
                })
        
        # 按分数排序
        filtered_stocks.sort(key=lambda x: x['score'], reverse=True)
        return filtered_stocks
    
    def apply_break_limit_strategy(self, dragon_heads):
        """应用打板策略"""
        strategy_params = self.selection_criteria['break_limit_strategy']
        
        break_limit_candidates = []
        
        for stock in dragon_heads:
            # 检查是否符合打板策略
            is_candidate = True
            strategy_reasons = []
            
            # 1. 涨停板数
            if stock['limit_up_days'] not in [1, 2]:  # 只关注首板、二板
                is_candidate = False
                continue
            
            # 2. 封单金额
            if stock['seal_amount'] < strategy_params['min_seal_amount']:
                is_candidate = False
                continue
            else:
                strategy_reasons.append(f"封单{stock['seal_amount']/10000:.0f}万")
            
            # 3. 换手率范围
            turnover = stock['turnover']
            min_turnover, max_turnover = strategy_params['turnover_range']
            if min_turnover <= turnover <= max_turnover:
                strategy_reasons.append(f"换手{turnover*100:.1f}%合理")
            else:
                is_candidate = False
                continue
            
            # 4. 量比要求
            if stock['volume_ratio'] >= strategy_params['volume_ratio_min']:
                strategy_reasons.append(f"量比{stock['volume_ratio']:.1f}充足")
            else:
                is_candidate = False
                continue
            
            # 5. 流通市值
            # 这里需要实际市值数据，暂时用模拟逻辑
            
            if is_candidate:
                stock['strategy_type'] = 'break_limit'
                stock['strategy_reasons'] = strategy_reasons
                stock['priority'] = self._calculate_priority(stock)
                break_limit_candidates.append(stock)
        
        # 按优先级排序
        break_limit_candidates.sort(key=lambda x: x['priority'], reverse=True)
        return break_limit_candidates
    
    def _calculate_priority(self, stock):
        """计算优先级分数"""
        priority = stock['score']  # 基础分数
        
        # 涨停板数加分（首板>二板>三板）
        if stock['limit_up_days'] == 1:
            priority += 30
        elif stock['limit_up_days'] == 2:
            priority += 20
        else:
            priority += 10
        
        # 封单金额加分
        seal_ratio = stock['seal_amount'] / 100000000  # 亿元为单位
        if seal_ratio >= 1:
            priority += 25
        elif seal_ratio >= 0.5:
            priority += 20
        elif seal_ratio >= 0.1:
            priority += 15
        else:
            priority += 10
        
        # 量比加分
        if stock['volume_ratio'] >= 3:
            priority += 20
        elif stock['volume_ratio'] >= 2:
            priority += 15
        elif stock['volume_ratio'] >= 1.5:
            priority += 10
        
        # 换手率加分（适中最好）
        if 0.08 <= stock['turnover'] <= 0.15:
            priority += 15
        elif 0.05 <= stock['turnover'] <= 0.20:
            priority += 10
        else:
            priority += 5
        
        return priority
    
    def generate_trading_suggestions(self, candidates, capital=1000000):
        """生成交易建议"""
        risk_config = self.config['risk_management']
        
        suggestions = []
        
        for i, stock in enumerate(candidates[:5]):  # 只取前5个
            # 计算建议仓位
            max_position = capital * risk_config['position_sizing']['max_per_stock']
            
            # 根据优先级分配仓位
            position_ratio = 0.15 + (0.05 * (5 - i))  # 15%-35%
            suggested_position = min(max_position, capital * position_ratio)
            
            # 计算建议股数
            shares = int(suggested_position / stock['current_price'] / 100) * 100  # 整手
            
            # 止损止盈价格
            stop_loss_price = stock['current_price'] * (1 + risk_config['stop_loss']['individual_stock'])
            take_profit_price = stock['current_price'] * (1 + risk_config['take_profit']['level2'])
            
            suggestion = {
                'rank': i + 1,
                'code': stock['code'],
                'name': stock['name'],
                'industry': stock['industry'],
                'current_price': stock['current_price'],
                'score': stock['score'],
                'priority': stock['priority'],
                'strategy': stock.get('strategy_type', 'dragon_head'),
                'reasons': stock.get('reasons', [])[:3],  # 取前3个理由
                'strategy_reasons': stock.get('strategy_reasons', []),
                'suggested_action': 'BUY',
                'suggested_shares': shares,
                'suggested_amount': shares * stock['current_price'],
                'stop_loss': stop_loss_price,
                'take_profit': take_profit_price,
                'risk_reward_ratio': abs((take_profit_price - stock['current_price']) / 
                                        (stock['current_price'] - stop_loss_price))
            }
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def format_suggestions_markdown(self, suggestions):
        """将建议格式化为Markdown"""
        if not suggestions:
            return "## 🎯 今日选股结果\n\n暂无符合条件的龙头股"
        
        md = f"""## 🎯 今日龙头股精选 ({len(suggestions)}只)

"""
        
        for suggestion in suggestions:
            rank_emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][suggestion['rank'] - 1]
            
            md += f"""{rank_emoji} **{suggestion['name']}** ({suggestion['code']})
   - **行业**：{suggestion['industry']}
   - **当前价**：{suggestion['current_price']}元
   - **综合评分**：{suggestion['score']}/150
   - **策略**：{suggestion['strategy']}
   
   **入选理由**：
"""
            
            for reason in suggestion['reasons']:
                md += f"   - {reason}\n"
            
            if suggestion.get('strategy_reasons'):
                md += "   \n   **打板策略**：\n"
                for s_reason in suggestion['strategy_reasons']:
                    md += f"   - {s_reason}\n"
            
            md += f"""
   **交易建议**：
   - 操作：{suggestion['suggested_action']}
   - 建议数量：{suggestion['suggested_shares']}股
   - 建议金额：{suggestion['suggested_amount']:,.0f}元
   - 止损价：{suggestion['stop_loss']:.2f}元 (-8%)
   - 止盈价：{suggestion['take_profit']:.2f}元 (+20%)
   - 风险收益比：{suggestion['risk_reward_ratio']:.1f}:1
   
"""
        
        md += """
## ⚠️ 风险提示
1. 以上建议仅供参考，不构成投资建议
2. 股市有风险，投资需谨慎
3. 建议仓位控制：单票不超过总资金20%
4. 严格执行止损纪律

---
*选股时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*策略：打板龙头股策略*
"""
        
        return md.format(datetime=datetime)

def run_screening():
    """运行选股筛选"""
    screener = DragonHeadScreener()
    
    print("开始选股筛选...")
    
    # 加载数据
    stock_data = screener.load_mock_data()
    print(f"加载{len(stock_data)}只股票数据")
    
    # 识别龙头股
    dragon_heads = screener.identify_dragon_heads(stock_data)
    print(f"识别出{len(dragon_heads)}只龙头股候选")
    
    # 应用打板策略
    break_limit_candidates = screener.apply_break_limit_strategy(dragon_heads)
    print(f"打板策略筛选出{len(break_limit_candidates)}只候选股")
    
    # 生成交易建议（假设资金100万）
    suggestions = screener.generate_trading_suggestions(break_limit_candidates, capital=1000000)
    
    # 格式化输出
    markdown = screener.format_suggestions_markdown(suggestions)
    
    # 保存结果
    filename = f"stock_suggestions_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(f"/root/.openclaw/workspace/reports/{filename}", 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"选股报告已生成: {filename}")
    return markdown

if __name__ == "__main__":
    # 创建报告目录
    import os
    os.makedirs("/root/.openclaw/workspace/reports", exist_ok=True)
    
    # 测试运行
    print("=== 选股系统测试运行 ===")
    result = run_screening()
    print("\n选股结果前500字符:")
    print(result[:500])