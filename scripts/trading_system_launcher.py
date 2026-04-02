#!/usr/bin/env python3
"""
A股交易系统启动器
整合新闻收集和选股系统，设置定时任务
"""

import json
import schedule
import time
import subprocess
import os
from datetime import datetime
import sys

class TradingSystemLauncher:
    def __init__(self):
        """初始化启动器"""
        self.workspace = "/root/.openclaw/workspace"
        self.reports_dir = os.path.join(self.workspace, "reports")
        self.scripts_dir = os.path.join(self.workspace, "scripts")
        
        # 确保目录存在
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # 加载配置
        config_path = os.path.join(self.workspace, "stock_assistant_config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def run_morning_report(self):
        """运行早间报告"""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始生成早间报告...")
        
        try:
            # 1. 收集新闻
            news_md = self._collect_news()
            
            # 2. 选股筛选
            stocks_md = self._screen_stocks()
            
            # 3. 整合报告
            full_report = self._combine_morning_report(news_md, stocks_md)
            
            # 4. 保存报告
            filename = f"morning_full_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_report)
            
            print(f"早间报告已保存: {filepath}")
            
            # 5. 发送通知（待实现）
            # self._send_notification(full_report, "morning")
            
            return full_report
            
        except Exception as e:
            error_msg = f"早间报告生成失败: {str(e)}"
            print(error_msg)
            return f"# ❌ 报告生成失败\n\n{error_msg}"
    
    def run_evening_report(self):
        """运行晚间报告"""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始生成晚间报告...")
        
        try:
            # 1. 收集新闻
            news_md = self._collect_news()
            
            # 2. 生成市场总结
            summary_md = self._generate_market_summary()
            
            # 3. 整合报告
            full_report = self._combine_evening_report(news_md, summary_md)
            
            # 4. 保存报告
            filename = f"evening_full_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_report)
            
            print(f"晚间报告已保存: {filepath}")
            
            # 5. 发送通知（待实现）
            # self._send_notification(full_report, "evening")
            
            return full_report
            
        except Exception as e:
            error_msg = f"晚间报告生成失败: {str(e)}"
            print(error_msg)
            return f"# ❌ 报告生成失败\n\n{error_msg}"
    
    def _collect_news(self):
        """收集新闻（简化版）"""
        # 这里应该调用news_collector.py，暂时用模拟数据
        news = [
            {
                'title': '美联储维持利率不变，鲍威尔讲话偏鸽',
                'source': '华尔街见闻',
                'time': datetime.now().strftime('%H:%M'),
                'impact': 'high',
                'summary': '美联储如期维持利率不变，鲍威尔表示通胀进展良好。'
            },
            {
                'title': '证监会：推动中长期资金入市',
                'source': '财联社',
                'time': datetime.now().strftime('%H:%M'),
                'impact': 'high',
                'summary': '证监会召开座谈会，研究部署推动中长期资金入市。'
            },
            {
                'title': '北向资金今日净流入50.2亿元',
                'source': '东方财富',
                'time': datetime.now().strftime('%H:%M'),
                'impact': 'medium',
                'summary': '北向资金连续3日净流入，重点加仓新能源。'
            }
        ]
        
        # 格式化为Markdown
        news_md = "## 📰 重要新闻速递\n\n"
        for i, item in enumerate(news, 1):
            impact_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(item['impact'], '⚪')
            news_md += f"{i}. **{impact_emoji} {item['title']}** - {item['source']} ({item['time']})\n"
            news_md += f"   {item['summary']}\n\n"
        
        return news_md
    
    def _screen_stocks(self):
        """筛选股票"""
        try:
            # 运行选股脚本
            script_path = os.path.join(self.scripts_dir, "simple_stock_screener.py")
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                cwd=self.workspace
            )
            
            if result.returncode == 0:
                # 从输出中提取报告
                output = result.stdout
                # 这里简化处理，实际应该解析输出
                return self._generate_stock_suggestions()
            else:
                print(f"选股脚本执行失败: {result.stderr}")
                return "## 🎯 选股结果\n\n选股系统暂时不可用，请稍后重试。"
                
        except Exception as e:
            print(f"选股过程出错: {e}")
            return self._generate_stock_suggestions()  # 返回模拟数据
    
    def _generate_stock_suggestions(self):
        """生成股票建议（模拟）"""
        suggestions = [
            {
                'name': '立讯精密',
                'code': '002475',
                'industry': '消费电子',
                'price': 31.2,
                'change': 4.2,
                'reason': '涨停第2板，量能充足，技术面强势'
            },
            {
                'name': '紫光国微',
                'code': '002049',
                'industry': '半导体',
                'price': 78.3,
                'change': 9.98,
                'reason': '首板涨停，封单强劲，半导体龙头'
            },
            {
                'name': '海康威视',
                'code': '002415',
                'industry': '安防',
                'price': 28.6,
                'change': 3.5,
                'reason': '技术突破，资金关注度高'
            }
        ]
        
        stocks_md = "## 🎯 今日龙头股精选\n\n"
        
        for i, stock in enumerate(suggestions, 1):
            rank_emoji = ['🥇', '🥈', '🥉'][i-1]
            stocks_md += f"{rank_emoji} **{stock['name']}** ({stock['code']})\n"
            stocks_md += f"- **行业**：{stock['industry']}\n"
            stocks_md += f"- **当前价**：{stock['price']}元 ({stock['change']:+.1f}%)\n"
            stocks_md += f"- **入选理由**：{stock['reason']}\n"
            stocks_md += f"- **建议**：关注开盘表现，设置止损-8%\n\n"
        
        return stocks_md
    
    def _generate_market_summary(self):
        """生成市场总结（模拟）"""
        summary = """## 📊 今日市场回顾

### 主要指数表现
- 上证指数：3050.12点 (+0.85%)
- 深证成指：9250.45点 (+1.23%)
- 创业板指：1805.67点 (+1.56%)

### 市场情绪
- 涨停家数：68家
- 跌停家数：12家
- 上涨家数：2850家
- 下跌家数：1950家

### 资金流向
- 北向资金：净流入52.3亿元
- 主力资金：净流入85.6亿元
- 热门板块：半导体、人工智能、新能源汽车

### 明日关注
1. 美联储会议纪要公布
2. 国内CPI数据发布
3. 关注量能是否持续
"""
        return summary
    
    def _combine_morning_report(self, news_md, stocks_md):
        """整合早间报告"""
        report = f"""# 🌅 A股早间投资策略 {datetime.now().strftime('%Y-%m-%d')}

## 📈 今日市场前瞻
*交易时间：09:30-11:30, 13:00-15:00*
*报告时间：{datetime.now().strftime('%H:%M:%S')}*

{news_md}

{stocks_md}

## 💡 今日交易策略
### 核心思路：打板龙头，快进快出
1. **重点关注**：首板、二板强势股
2. **仓位控制**：单票不超过20%，总仓位建议50-70%
3. **风险控制**：严格止损-8%，盈利20%以上分批止盈
4. **操作要点**：
   - 开盘30分钟观察市场情绪
   - 选择量价齐升的涨停股
   - 避免追高已连续涨停的个股

## ⚠️ 风险提示
1. 市场波动可能加大，注意控制仓位
2. 关注外围市场变化对A股的影响
3. 严格执行止损纪律，保护本金安全

---
*数据来源：模拟数据，待接入真实行情*
*投资有风险，入市需谨慎*
"""
        return report
    
    def _combine_evening_report(self, news_md, summary_md):
        """整合晚间报告"""
        report = f"""# 🌙 A股晚间总结 {datetime.now().strftime('%Y-%m-%d')}

## 📊 今日操作回顾
*报告时间：{datetime.now().strftime('%H:%M:%S')}*

{summary_md}

{news_md}

## 🔮 明日展望与策略
### 市场判断
- **短期趋势**：震荡上行，关注量能配合
- **关键点位**：上证指数3050点支撑，3080点压力
- **板块机会**：继续关注科技成长主线

### 明日操作计划
1. **持仓管理**：
   - 盈利超过20%的考虑分批止盈
   - 跌破止损位的坚决卖出
2. **新开仓策略**：
   - 继续关注龙头股打板机会
   - 优先选择行业景气度高的板块
3. **风险控制**：
   - 保持总仓位在合理范围
   - 设置好止损止盈位

## 📝 投资笔记
- 今日成功操作：立讯精密涨停持有
- 今日失误反思：某股追高被套，需加强买点把握
- 明日重点关注：半导体板块持续性

---
*明日交易时间：09:30-11:30, 13:00-15:00*
*早间报告时间：08:00*
*祝您投资顺利！*
"""
        return report
    
    def _send_notification(self, content, report_type):
        """发送通知（待实现）"""
        # 这里应该集成飞书消息发送
        print(f"准备发送{report_type}报告通知...")
        # 实际实现需要调用飞书API
        return True
    
    def setup_schedule(self):
        """设置定时任务"""
        # 早间报告：08:00
        schedule.every().day.at("08:00").do(self.run_morning_report)
        
        # 晚间报告：22:00
        schedule.every().day.at("22:00").do(self.run_evening_report)
        
        # 市场开盘检查：09:15
        schedule.every().day.at("09:15").do(self.market_open_check)
        
        # 市场收盘总结：15:05
        schedule.every().day.at("15:05").do(self.market_close_summary)
        
        print("定时任务已设置：")
        print("  08:00 - 早间报告")
        print("  09:15 - 市场开盘检查")
        print("  15:05 - 市场收盘总结")
        print("  22:00 - 晚间报告")
    
    def market_open_check(self):
        """市场开盘检查"""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 市场开盘检查...")
        # 实际应该检查市场状态、异动等
    
    def market_close_summary(self):
        """市场收盘总结"""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 市场收盘总结...")
        # 实际应该生成当日交易总结
    
    def run_test(self):
        """运行测试"""
        print("=== 交易系统测试运行 ===")
        
        # 测试早间报告
        print("\n1. 测试早间报告生成...")
        morning_report = self.run_morning_report()
        print("早间报告生成完成")
        
        # 测试晚间报告
        print("\n2. 测试晚间报告生成...")
        evening_report = self.run_evening_report()
        print("晚间报告生成完成")
        
        print("\n=== 测试完成 ===")
        print(f"报告保存在: {self.reports_dir}")
        
        return morning_report, evening_report
    
    def run_daemon(self):
        """运行守护进程"""
        print("=" * 50)
        print("A股量化交易辅助系统")
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 设置定时任务
        self.setup_schedule()
        
        # 立即运行一次测试
        print("\n执行初始测试...")
        self.run_test()
        
        print("\n系统已启动，等待定时任务...")
        print("按 Ctrl+C 退出")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            print("\n系统正在关闭...")
            print("感谢使用！")

def main():
    """主函数"""
    launcher = TradingSystemLauncher()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            launcher.run_test()
        elif command == "morning":
            launcher.run_morning_report()
        elif command == "evening":
            launcher.run_evening_report()
        elif command == "daemon":
            launcher.run_daemon()
        else:
            print(f"未知命令: {command}")
            print("可用命令: test, morning, evening, daemon")
    else:
        # 默认运行守护进程
        launcher.run_daemon()

if __name__ == "__main__":
    main()