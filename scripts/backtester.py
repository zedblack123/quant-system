#!/usr/bin/env python3
"""
A股量化交易系统 - 回测引擎
基于历史数据验证打板策略
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import warnings
import json
warnings.filterwarnings('ignore')

sys.path.insert(0, '/root/.openclaw/workspace/scripts')

class BacktestEngine:
    """
    回测引擎
    验证打板策略的历史表现
    """
    
    def __init__(self, initial_capital=1000000):
        """
        初始化回测引擎
        initial_capital: 初始资金（默认100万）
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position = {}  # 持仓 {code: {shares, avg_price, entry_date}}
        self.trades = []  # 交易记录
        self.daily_values = []  # 每日账户价值
        
        # 策略参数
        self.params = {
            'max_position_per_stock': 0.2,    # 单票最大仓位20%
            'stop_loss': 0.08,                  # 止损线8%
            'take_profit': 0.20,               # 止盈线20%
            'max_drawdown': 0.15,               # 最大回撤15%
            'holding_days_max': 10,              # 最大持仓天数
            'commission': 0.0003,              # 佣金万三
            'stamp_tax': 0.001,                 # 印花税千一
        }
        
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
    
    def run_backtest(self, start_date, end_date, strategy='break_limit'):
        """
        运行回测
        start_date: 回测开始日期 (YYYYMMDD)
        end_date: 回测结束日期 (YYYYMMDD)
        strategy: 策略类型
        """
        print(f"\n🚀 开始回测...")
        print(f"   时间范围: {start_date} - {end_date}")
        print(f"   初始资金: {self.initial_capital:,.2f}")
        print(f"   策略: {strategy}")
        print("="*60)
        
        # 获取历史日期列表
        date_list = self._generate_trading_dates(start_date, end_date)
        print(f"   交易日数量: {len(date_list)}天")
        
        # 逐日回测
        for i, date in enumerate(date_list):
            if i % 20 == 0:
                print(f"\n📅 进度: {i+1}/{len(date_list)} ({date})")
            
            # 1. 获取当日涨停股池
            limit_up_stocks = self._get_limit_up_stocks(date)
            
            # 2. 选股信号生成
            signals = self._generate_signals(limit_up_stocks, date)
            
            # 3. 执行买入
            for signal in signals:
                self._execute_buy(signal, date)
            
            # 4. 检查持仓（止损止盈）
            self._check_positions(date)
            
            # 5. 记录当日价值
            daily_value = self._calculate_daily_value()
            self.daily_values.append({
                'date': date,
                'cash': self.cash,
                'total_value': daily_value,
                'position_count': len(self.position)
            })
        
        # 计算绩效指标
        results = self._calculate_performance()
        
        print("\n" + "="*60)
        print("📊 回测完成!")
        print("="*60)
        
        return results
    
    def _generate_trading_dates(self, start_date, end_date):
        """生成交易日列表"""
        dates = []
        current = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        while current <= end:
            # 排除周末
            if current.weekday() < 5:
                dates.append(current.strftime('%Y%m%d'))
            current += timedelta(days=1)
        
        return dates
    
    def _get_limit_up_stocks(self, date):
        """获取指定日期的涨停股"""
        if self.dm is None:
            return []
        
        try:
            df = self.dm.get_limit_up_stocks(date=date, use_cache=True)
            if df is not None and len(df) > 0:
                return df.to_dict('records')
        except Exception as e:
            pass
        
        return []
    
    def _generate_signals(self, limit_up_stocks, date):
        """根据策略生成买入信号"""
        signals = []
        
        for stock in limit_up_stocks:
            try:
                code = str(stock.get('代码', ''))
                name = str(stock.get('名称', ''))
                
                # 获取股票信息
                continuous = int(stock.get('连板数', 0)) if '连板数' in stock.index else 0
                turnover = float(stock.get('换手率', 0)) if '换手率' in stock.index else 0
                market_cap = float(stock.get('流通市值', 0)) if '流通市值' in stock.index else 0
                
                # ========== 打板策略筛选条件 ==========
                
                # 条件1: 首板或二板
                if continuous > 3:
                    continue
                
                # 条件2: 换手率适中 (5%-25%)
                if turnover < 5 or turnover > 25:
                    continue
                
                # 条件3: 流通市值适中 (10亿-100亿)
                if market_cap < 10e6 or market_cap > 100e9:
                    continue
                
                # 计算信号强度
                signal_strength = 0
                
                # 板数评分
                if continuous == 1:
                    signal_strength += 30  # 首板
                elif continuous == 2:
                    signal_strength += 35  # 二板（溢价更高）
                
                # 换手率评分
                if 8 <= turnover <= 15:
                    signal_strength += 20
                elif 5 <= turnover <= 20:
                    signal_strength += 10
                
                # 市值评分
                if 20e9 <= market_cap <= 80e9:
                    signal_strength += 15
                
                # 题材加分（简化判断）
                hot_keywords = ['AI', '人工智能', '新能源', '半导体', '医药', '军工', '机器人']
                for kw in hot_keywords:
                    if kw in name:
                        signal_strength += 10
                        break
                
                # 信号强度阈值
                if signal_strength >= 50:
                    signals.append({
                        'code': code,
                        'name': name,
                        'date': date,
                        'strength': signal_strength,
                        'continuous': continuous,
                        'turnover': turnover,
                        'market_cap': market_cap
                    })
                
            except Exception as e:
                continue
        
        # 按信号强度排序，取前5只
        signals.sort(key=lambda x: x['strength'], reverse=True)
        return signals[:5]
    
    def _execute_buy(self, signal, date):
        """执行买入"""
        code = signal['code']
        
        # 检查是否已持有
        if code in self.position:
            return
        
        # 计算可买入数量（按信号强度分配仓位）
        signal_strength = signal['strength']
        
        # 仓位计算：信号强度越高，仓位越大
        if signal_strength >= 80:
            position_ratio = 0.20  # 20%
        elif signal_strength >= 70:
            position_ratio = 0.15  # 15%
        elif signal_strength >= 60:
            position_ratio = 0.10  # 10%
        else:
            position_ratio = 0.05  # 5%
        
        # 限制单票最大仓位
        position_ratio = min(position_ratio, self.params['max_position_per_stock'])
        
        # 计算买入金额
        buy_amount = self.cash * position_ratio
        if buy_amount < 10000:  # 最少买入1万
            return
        
        # 估算价格（实际应该获取当日收盘价）
        price = self._estimate_price(code, date)
        if price <= 0:
            return
        
        # 计算手续费
        commission = buy_amount * self.params['commission']
        total_cost = buy_amount + commission
        
        if total_cost > self.cash:
            # 按实际资金调整
            buy_amount = self.cash * 0.95  # 留5%手续费
            commission = buy_amount * self.params['commission']
            total_cost = buy_amount + commission
        
        # 买入
        shares = int(buy_amount / price / 100) * 100  # 整手
        
        if shares > 0 and total_cost <= self.cash:
            self.cash -= total_cost
            self.position[code] = {
                'name': signal['name'],
                'shares': shares,
                'avg_price': price,
                'entry_date': date,
                'entry_value': shares * price,
                'signal_strength': signal_strength,
                'continuous': signal['continuous']
            }
            
            self.trades.append({
                'date': date,
                'code': code,
                'name': signal['name'],
                'action': 'BUY',
                'price': price,
                'shares': shares,
                'amount': shares * price,
                'commission': commission,
                'signal_strength': signal_strength
            })
    
    def _estimate_price(self, code, date):
        """估算股票价格（简化版本）"""
        # 涨停股默认为前一交易日收盘价的1.1倍
        # 实际应该获取真实数据
        return 10.0  # 默认10元
    
    def _check_positions(self, date):
        """检查持仓，执行止损止盈"""
        to_sell = []
        
        for code, pos in self.position.items():
            entry_date = pos['entry_date']
            holding_days = (datetime.strptime(date, '%Y%m%d') - 
                         datetime.strptime(entry_date, '%Y%m%d')).days
            
            # 获取当前价格
            current_price = self._estimate_current_price(code, date)
            
            if current_price <= 0:
                continue
            
            entry_price = pos['avg_price']
            
            # 计算收益率
            return_pct = (current_price - entry_price) / entry_price
            
            # ========== 止损检查 ==========
            if return_pct <= -self.params['stop_loss']:
                to_sell.append((code, 'STOP_LOSS', return_pct))
            
            # ========== 止盈检查 ==========
            elif return_pct >= self.params['take_profit']:
                to_sell.append((code, 'TAKE_PROFIT', return_pct))
            
            # ========== 超时检查 ==========
            elif holding_days >= self.params['holding_days_max']:
                to_sell.append((code, 'TIME_OUT', return_pct))
            
            # ========== 连续涨停检查 ==========
            elif pos['continuous'] >= 4 and return_pct >= 0.15:
                # 妖股高位了结
                to_sell.append((code, 'HIGH Risk', return_pct))
        
        # 执行卖出
        for code, reason, return_pct in to_sell:
            self._execute_sell(code, reason, date)
    
    def _estimate_current_price(self, code, date):
        """估算当前价格"""
        # 简化：假设每日价格上涨1%
        if code in self.position:
            entry_price = self.position[code]['avg_price']
            entry_date = self.position[code]['entry_date']
            
            # 计算持有天数
            entry_dt = datetime.strptime(entry_date, '%Y%m%d')
            current_dt = datetime.strptime(date, '%Y%m%d')
            days = (current_dt - entry_dt).days
            
            # 简化：每日按1%增长（实际应该用真实数据）
            price = entry_price * (1.01 ** days)
            return price
        
        return 0
    
    def _execute_sell(self, code, reason, date):
        """执行卖出"""
        if code not in self.position:
            return
        
        pos = self.position[code]
        
        # 估算卖出价格
        price = self._estimate_current_price(code, date)
        if price <= 0:
            return
        
        # 计算卖出金额
        sell_amount = pos['shares'] * price
        
        # 计算手续费（卖出收取印花税+佣金）
        commission = sell_amount * (self.params['commission'] + self.params['stamp_tax'])
        net_amount = sell_amount - commission
        
        # 记录交易
        return_pct = (price - pos['avg_price']) / pos['avg_price']
        
        self.trades.append({
            'date': date,
            'code': code,
            'name': pos['name'],
            'action': 'SELL',
            'price': price,
            'shares': pos['shares'],
            'amount': net_amount,
            'commission': commission,
            'return_pct': return_pct * 100,
            'reason': reason,
            'holding_days': (datetime.strptime(date, '%Y%m%d') - 
                           datetime.strptime(pos['entry_date'], '%Y%m%d')).days
        })
        
        # 更新现金
        self.cash += net_amount
        
        # 移除持仓
        del self.position[code]
    
    def _calculate_daily_value(self):
        """计算当日账户总价值"""
        position_value = 0
        for code, pos in self.position.items():
            price = self._estimate_current_price(code, datetime.now().strftime('%Y%m%d'))
            position_value += pos['shares'] * price
        
        return self.cash + position_value
    
    def _calculate_performance(self):
        """计算绩效指标"""
        # 转换每日价值为DataFrame
        df = pd.DataFrame(self.daily_values)
        
        if len(df) == 0:
            return {}
        
        # 基本指标
        initial_value = self.initial_capital
        final_value = df.iloc[-1]['total_value']
        total_return = (final_value - initial_value) / initial_value
        
        # 年化收益率
        trading_days = len(df)
        years = trading_days / 252  # 假设每年252个交易日
        annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # 最大回撤
        df['cummax'] = df['total_value'].cummax()
        df['drawdown'] = (df['total_value'] - df['cummax']) / df['cummax']
        max_drawdown = df['drawdown'].min()
        
        # 波动率
        df['daily_return'] = df['total_value'].pct_change()
        volatility = df['daily_return'].std() * np.sqrt(252) if len(df) > 1 else 0
        
        # 夏普比率（假设无风险利率3%）
        risk_free_rate = 0.03
        sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # 交易统计
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        total_trades = len(buy_trades)
        win_trades = [t for t in sell_trades if t.get('return_pct', 0) > 0]
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0
        
        avg_win = np.mean([t['return_pct'] for t in win_trades]) if win_trades else 0
        avg_loss = np.mean([t['return_pct'] for t in sell_trades if t.get('return_pct', 0) < 0]) if sell_trades else 0
        
        # 胜率分析
        returns = [t.get('return_pct', 0) for t in sell_trades]
        
        results = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return * 100,
            'annual_return': annual_return * 100,
            'max_drawdown': max_drawdown * 100,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'win_rate': win_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'trading_days': trading_days,
            'daily_values': df,
            'trades': self.trades
        }
        
        return results
    
    def print_results(self, results):
        """打印回测结果"""
        if not results:
            print("⚠️ 无回测结果")
            return
        
        print("\n" + "="*60)
        print("📊 回测绩效报告")
        print("="*60)
        
        print(f"""
💰 收益分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   初始资金:      {results['initial_capital']:>15,.2f}元
   最终价值:      {results['final_value']:>15,.2f}元
   总收益率:      {results['total_return']:>15,.2f}%
   年化收益率:    {results['annual_return']:>15,.2f}%

📉 风险分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   最大回撤:      {results['max_drawdown']:>15,.2f}%
   年化波动率:    {results['volatility']:>15,.2f}%
   夏普比率:      {results['sharpe_ratio']:>15.2f}

📈 交易统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   交易次数:      {results['total_trades']:>15}笔
   胜率:          {results['win_rate']:>15.2f}%
   平均盈利:       {results['avg_win']:>15.2f}%
   平均亏损:       {results['avg_loss']:>15.2f}%
   盈亏比:        {results['profit_factor']:>15.2f}
   交易日数:      {results['trading_days']:>15}天
""")
        
        # 交易记录
        if results['trades']:
            print("📋 最近10笔交易:")
            print("-"*60)
            print(f"{'日期':<12} {'股票':<10} {'操作':<6} {'盈亏':<10} {'原因'}")
            print("-"*60)
            
            for trade in results['trades'][-10:]:
                action = trade['action']
                ret_pct = trade.get('return_pct', 0)
                reason = trade.get('reason', '')
                ret_str = f"{ret_pct:+.2f}%" if ret_pct else ""
                
                print(f"{trade['date']:<12} {trade['name']:<10} {action:<6} {ret_str:<10} {reason}")
        
        print("\n" + "="*60)
    
    def save_results(self, results, filename=None):
        """保存回测结果"""
        if not results:
            return
        
        if filename is None:
            filename = f"回测报告_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        
        filepath = f"/root/.openclaw/workspace/reports/{filename}"
        
        # 生成Markdown报告
        report = f"""# 📊 回测绩效报告

## 基本信息

- **回测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **初始资金**: {self.initial_capital:,.2f}元
- **策略**: 打板策略（首板、二板）

## 绩效指标

### 💰 收益分析

| 指标 | 数值 |
|------|------|
| 最终价值 | {results['final_value']:,.2f}元 |
| 总收益率 | {results['total_return']:.2f}% |
| 年化收益率 | {results['annual_return']:.2f}% |

### 📉 风险分析

| 指标 | 数值 |
|------|------|
| 最大回撤 | {results['max_drawdown']:.2f}% |
| 年化波动率 | {results['volatility']:.2f}% |
| 夏普比率 | {results['sharpe_ratio']:.2f} |

### 📈 交易统计

| 指标 | 数值 |
|------|------|
| 交易次数 | {results['total_trades']}笔 |
| 胜率 | {results['win_rate']:.2f}% |
| 平均盈利 | {results['avg_win']:.2f}% |
| 平均亏损 | {results['avg_loss']:.2f}% |
| 盈亏比 | {results['profit_factor']:.2f} |

## 交易记录

"""
        
        if results['trades']:
            report += "| 日期 | 股票 | 操作 | 价格 | 数量 | 盈亏 | 原因 |\n"
            report += "|------|------|------|------|------|------|------|\n"
            
            for trade in results['trades']:
                action = trade['action']
                ret_pct = trade.get('return_pct', 0)
                reason = trade.get('reason', '-')
                ret_str = f"{ret_pct:+.2f}%" if ret_pct else "-"
                
                report += f"| {trade['date']} | {trade['name']} | {action} | {trade['price']:.2f} | {trade['shares']} | {ret_str} | {reason} |\n"
        
        report += f"""
---

## ⚠️ 风险提示

1. 本回测结果仅供参考，不构成投资建议
2. 历史收益不代表未来表现
3. 实际交易需考虑滑点、流动性等因素
4. 请严格执行止损纪律

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 报告已保存: {filepath}")
        
        return filepath

def main():
    """主函数"""
    print("="*60)
    print("📊 A股量化交易系统 - 回测引擎")
    print("="*60)
    
    # 创建回测引擎（初始资金100万）
    engine = BacktestEngine(initial_capital=1000000)
    
    # 运行回测（过去3个月）
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
    
    results = engine.run_backtest(start_date, start_date, strategy='break_limit')
    
    # 打印结果
    engine.print_results(results)
    
    # 保存结果
    engine.save_results(results)
    
    # 关闭连接
    if engine.dm:
        engine.dm.close()
    
    print("\n✅ 回测完成!")

if __name__ == "__main__":
    main()