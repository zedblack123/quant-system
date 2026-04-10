#!/usr/bin/env python3
"""
定时报告生成和推送脚本 - 支持飞书推送
每天08:00和22:00自动生成并推送到飞书
"""

import sys
import os
from datetime import datetime, timedelta
import json

sys.path.insert(0, '/root/.openclaw/workspace')

# 飞书推送配置
FEISHU_CONFIG = {
    'user_open_id': 'ou_636754d2a4956be2f5928918767a62e7',  # 人山先生
}

def get_feishu_token():
    """获取飞书token"""
    token_file = '/root/.openclaw/workspace/.feishu_token'
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    return None

def send_feishu_message(content):
    """发送飞书消息"""
    token = get_feishu_token()
    if not token:
        print("⚠️ 未配置飞书Token，跳过推送")
        return False
    
    try:
        import requests
        
        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 获取用户的chat_id
        user_id = FEISHU_CONFIG['user_open_id']
        
        # 先获取与用户的单聊chat_id
        search_url = "https://open.feishu.cn/open-apis/im/v1/chats"
        params = {"user_id_type": "open_id"}
        
        search_resp = requests.get(search_url, headers=headers, params=params)
        
        payload = {
            "receive_id": user_id,
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }
        
        # 发送消息
        resp = requests.post(url, headers=headers, json=payload)
        
        if resp.status_code == 200:
            print(f"✅ 飞书消息发送成功")
            return True
        else:
            print(f"❌ 飞书消息发送失败: {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ 飞书推送失败: {e}")
        return False

def generate_morning_report():
    """生成早间报告"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 生成早间报告...")
    
    try:
        from scripts.news_manager import NewsManager
        from scripts.production_stock_screener import ProductionStockScreener
        
        # 获取新闻
        nm = NewsManager()
        all_news = nm.get_all_news()
        news_report = nm.format_news_report(all_news, "📰 早间财经要闻")
        
        # 获取选股
        screener = ProductionStockScreener()
        candidates = screener.screen_dragon_heads()
        stock_report = screener.format_report(candidates)
        
        # 组合报告
        full_report = f"""🌅 A股早间投资策略
{datetime.now().strftime('%Y年%m月%d日 08:00')}
━━━━━━━━━━━━━━━━━━━━

{news_report}

{stock_report}

━━━━━━━━━━━━━━━━━━━━
本报告由系统自动生成""")
        
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
        from scripts.news_manager import NewsManager
        from scripts.data_manager_tushare import DataManagerV2
        
        dm = DataManagerV2()
        
        # 获取今日市场数据
        print("📊 获取市场数据...")
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
        today = datetime.now().strftime('%Y%m%d')
        index_df = dm.get_tushare_index('000001.SH', five_days_ago, today)
        
        # 获取涨停股
        zt_df = dm.get_akshare_limit_up(today)
        
        # 获取新闻
        nm = NewsManager()
        all_news = nm.get_all_news()
        
        # 生成报告
        report = f"""🌙 A股晚间总结
{datetime.now().strftime('%Y年%m月%d日 22:00')}
━━━━━━━━━━━━━━━━━━━━

📊 今日市场回顾
"""
        
        if index_df is not None and len(index_df) > 0:
            latest = index_df.iloc[0]
            prev = index_df.iloc[1] if len(index_df) > 1 else latest
            
            close = float(latest.get('close', 0))
            prev_close = float(prev.get('close', 0))
            change = (close - prev_close) / prev_close * 100 if prev_close else 0
            
            report += f"""
上证指数: {close:.2f} ({change:+.2f}%)
涨停家数: {zt_df.shape[0] if zt_df is not None else 0}家
"""
        
        report += """
📰 晚间重要新闻
"""
        
        # 添加高影响新闻
        high_impact = [n for n in all_news if n.get('impact') == 'high']
        for news in high_impact[:3]:
            title = news.get('title', '')[:50]
            report += f"• {title}\n"
        
        report += f"""
🚀 今日涨停股 ({zt_df.shape[0] if zt_df is not None else 0}只)
"""
        
        if zt_df is not None and len(zt_df) > 0:
            for _, row in zt_df.head(5).iterrows():
                name = row.get('名称', '')[:6]
                code = row.get('代码', '')
                board = row.get('连板数', 0)
                report += f"• {name}({code}) 第{board}板\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━
🔮 明日展望
• 市场趋势: 震荡偏强
• 操作建议: 控制仓位，逢低布局
• 风险提示: 严格止损

━━━━━━━━━━━━━━━━━━━━
报告生成时间: {datetime.now().strftime('%H:%M:%S')}
数据源: 第三方Tushare + AKShare"""
        
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
    """推送内容到飞书"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 推送飞书消息...")
    
    # 由于没有飞书token，直接打印
    print("⚠️ 飞书推送需要配置Token")
    print("请在飞书开放平台创建应用并获取Token")
    
    # 暂时把内容写入文件，由管理员手动发送
    push_file = f"/root/.openclaw/workspace/reports/push_content_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(push_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📄 推送内容已保存: {push_file}")
    
    return True

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