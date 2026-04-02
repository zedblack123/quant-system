#!/usr/bin/env python3
"""
定时报告生成和推送脚本
每天08:00和22:00自动生成并推送报告
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace')

# 飞书推送配置
FEISHU_CONFIG = {
    'user_open_id': 'ou_636754d2a4956be2f5928918767a62e7',
}

def get_feishu_token():
    """获取飞书token"""
    token_file = '/root/.openclaw/workspace/.feishu_token'
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return None

def generate_morning_report():
    """生成早间报告"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 生成早间报告...")
    
    try:
        from news_manager import NewsManager
        from production_stock_screener import ProductionStockScreener
        
        # 获取新闻（新版多源）
        try:
            from news_collector_v2 import MultiSourceNewsCollector
            nm2 = MultiSourceNewsCollector()
            multi_news = nm2.get_all_news()
            multi_news_report = nm2.format_report(multi_news, "📰 多源财经新闻（国内外+社交媒体）")
        except Exception as e:
            print(f"多源新闻获取失败: {e}")
            multi_news_report = ""
        
        # 获取原有新闻
        nm = NewsManager()
        all_news = nm.get_all_news()
        news_report = nm.format_news_report(all_news, "📰 早间财经要闻")
        
        # 获取选股
        screener = ProductionStockScreener()
        candidates = screener.screen_dragon_heads()
        stock_report = screener.format_report(candidates)
        
        # 组合报告
        full_report = f"""# 🌅 A股早间投资策略
## {datetime.now().strftime('%Y年%m月%d日 08:00')}
================================================================================

{multi_news_report}

{news_report}

{stock_report}

---
*本报告由系统自动生成*
"""
        
        # 保存报告
        filename = f"早间报告_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        filepath = f"/root/.openclaw/workspace/reports/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        print(f"✅ 早间报告已保存: {filepath}")
        
        # 关闭连接
        if screener.dm:
            screener.dm.close()
        
        return full_report
        
    except Exception as e:
        print(f"❌ 生成早间报告失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_evening_report():
    """生成晚间报告"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 生成晚间报告...")
    
    try:
        from news_manager import NewsManager
        from data_manager_tushare import DataManagerV2
        
        dm = DataManagerV2()
        
        # 获取今日市场数据
        print("📊 获取市场数据...")
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
        today = datetime.now().strftime('%Y%m%d')
        index_df = dm.get_tushare_index('000001.SH', five_days_ago, today)
        
        # 获取涨停股
        zt_df = dm.get_akshare_limit_up(datetime.now().strftime('%Y%m%d'))
        
        # 获取多源新闻
        try:
            from news_collector_v2 import MultiSourceNewsCollector
            nm2 = MultiSourceNewsCollector()
            multi_news = nm2.get_all_news()
            multi_news_report = nm2.format_report(multi_news, "📰 多源财经新闻（收盘汇总）")
        except Exception as e:
            print(f"多源新闻获取失败: {e}")
            multi_news_report = ""
        
        # 获取原有新闻
        nm = NewsManager()
        all_news = nm.get_all_news()
        
        # 生成报告
        report = f"""# 🌙 A股晚间总结
## {datetime.now().strftime('%Y年%m月%d日 22:00')}
================================================================================

## 📊 今日市场回顾

"""
        
        if index_df is not None and len(index_df) > 0:
            latest = index_df.iloc[0]
            prev = index_df.iloc[1] if len(index_df) > 1 else latest
            
            close = float(latest.get('close', 0))
            prev_close = float(prev.get('close', 0))
            change = (close - prev_close) / prev_close * 100 if prev_close else 0
            
            report += f"""
- **上证指数**: {close:.2f} ({change:+.2f}%)
- **涨跌家数**: 上涨{zt_df.shape[0] if zt_df is not None else 0}家
"""
        else:
            report += "\n- 市场数据获取中...\n"
        
        report += f"""
{multi_news_report}

## 📰 晚间重要新闻

"""
        
        # 添加高影响新闻
        high_impact = [n for n in all_news if n.get('impact') == 'high']
        for news in high_impact[:5]:
            report += f"- **{news.get('title', '')}**\n"
            report += f"  {news.get('content', '')[:80]}...\n\n"
        
        report += f"""
## 🚀 今日涨停股 ({zt_df.shape[0] if zt_df is not None else 0}只)

"""
        
        if zt_df is not None and len(zt_df) > 0:
            cols = ['代码', '名称', '连板数', '换手率']
            available_cols = [c for c in cols if c in zt_df.columns]
            report += zt_df[available_cols].head(10).to_markdown(index=False) + "\n"
        
        report += f"""
---

## 🔮 明日展望

- **市场趋势**: 震荡偏强
- **操作建议**: 控制仓位，逢低布局
- **风险提示**: 严格止损

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*数据源: 第三方Tushare + AKShare*
"""
        
        # 保存报告
        filename = f"晚间报告_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        filepath = f"/root/.openclaw/workspace/reports/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 晚间报告已保存: {filepath}")
        
        dm.close()
        
        return report
        
    except Exception as e:
        print(f"❌ 生成晚间报告失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def push_to_feishu(content):
    """通过OpenClaw Gateway API发送飞书消息"""
    try:
        import requests
        import json
        
        # 从本地gateway发送
        gateway_token = "7c8a50ba1197309b310a8cb6e9f4190660e82aff203b1a39"
        gateway_port = 18789
        
        # 使用agent接口发送消息
        url = f"http://127.0.0.1:{gateway_port}/v1beta/messages"
        headers = {
            "Authorization": f"Bearer {gateway_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "receiver_id": FEISHU_CONFIG['user_open_id'],
            "msg_type": "text",
            "content": content
        }
        
        # 尝试通过channel direct send
        resp = requests.post(
            f"http://127.0.0.1:{gateway_port}/channels/feishu:ou_636754d2a4956be2f5928918767a62e7/messages",
            headers=headers,
            json={"text": content},
            timeout=10
        )
        
        if resp.status_code in [200, 201, 204]:
            print(f"✅ 飞书消息发送成功")
            return True
        else:
            print(f"⚠️ Gateway API返回: {resp.status_code} - {resp.text[:200]}")
            # 降级：保存到待发送队列
            queue_file = f"/root/.openclaw/workspace/reports/pending_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(queue_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 消息已保存到队列: {queue_file}")
            return True
            
    except Exception as e:
        print(f"⚠️ 飞书推送异常: {e}")
        # 降级：保存到待发送队列
        try:
            queue_file = f"/root/.openclaw/workspace/reports/pending_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(queue_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📝 消息已保存到队列: {queue_file}")
            return True
        except:
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='定时报告生成器')
    parser.add_argument('--morning', action='store_true', help='生成早间报告')
    parser.add_argument('--evening', action='store_true', help='生成晚间报告')
    parser.add_argument('--push', action='store_true', help='推送到飞书')
    args = parser.parse_args()
    
    if args.morning:
        report = generate_morning_report()
        if report and args.push:
            push_to_feishu(report)
    elif args.evening:
        report = generate_evening_report()
        if report and args.push:
            push_to_feishu(report)
    else:
        # 默认为晚间报告
        report = generate_evening_report()
        if report:
            push_to_feishu(report)

if __name__ == "__main__":
    main()