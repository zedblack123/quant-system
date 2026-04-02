#!/usr/bin/env python3
"""
热门舆情监控 - 持续运行版
每10分钟检查一次，有热门就通过飞书推送
"""

import sys
import os
import time
import json
import requests
sys.path.insert(0, '/root/.openclaw/workspace')

from scripts.news_collector_v2 import MultiSourceNewsCollector
from datetime import datetime

# 配置
CHECK_INTERVAL = 600  # 10分钟
GATEWAY_TOKEN = "7c8a50ba1197309b310a8cb6e9f4190660e82aff203b1a39"
GATEWAY_PORT = 18789
USER_OPEN_ID = "ou_636754d2a4956be2f5928918767a62e7"

# 热门关键字
HOT_KEYWORDS = [
    '涨停', '跌停', '暴涨', '暴跌', '闪崩', '停牌', '复牌',
    '龙头', '妖股', '牛股', '白马', '降准', '加息', 
    '印花税', '证监会', '央行', '财政部', '美联储', 
    '非农', 'CPI', '战争', '制裁', '新能源', '半导体', 
    '人工智能', '芯片', '医药集采', '黑天鹅', '利空', 
    '利好', '业绩暴增', '业绩暴雷', '崩盘', '股灾',
]

PANIC_KEYWORDS = [
    '崩盘', '股灾', '清仓', '踩踏', '做空', '爆仓',
    '外资出逃', '主力砸盘', '大规模减持',
]

def send_feishu_message(content):
    """通过OpenClaw gateway发送飞书消息"""
    try:
        url = f"http://127.0.0.1:{GATEWAY_PORT}/v1beta/messages"
        headers = {
            "Authorization": f"Bearer {GATEWAY_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "receiver_id": USER_OPEN_ID,
            "msg_type": "text",
            "content": content
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if resp.status_code in [200, 201, 204]:
            print(f"✅ 消息发送成功")
            return True
        else:
            print(f"⚠️ Gateway返回: {resp.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ 发送失败: {e}")
        return False

def check_and_push():
    """检查舆情并推送"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 检查热门舆情...")
    
    try:
        collector = MultiSourceNewsCollector()
        all_news = collector.get_all_news()
        
        hot_items = []
        panic_items = []
        
        for news in all_news:
            title = news.get('title', '').lower()
            
            for kw in HOT_KEYWORDS:
                if kw.lower() in title:
                    hot_items.append(news)
                    break
            
            for kw in PANIC_KEYWORDS:
                if kw.lower() in title:
                    panic_items.append(news)
                    break
        
        print(f"   总新闻: {len(all_news)} | 热门: {len(hot_items)} | 恐慌: {len(panic_items)}")
        
        # 有热门或恐慌才推送
        if not hot_items and not panic_items:
            print("   ⏭️ 无热门舆情，跳过")
            return False
        
        # 格式化消息 - 降低阈值，更容易推送
        if panic_items:
            level = "🔴 恐慌舆情预警"
        elif len(hot_items) >= 3:
            level = "🟠 热门动态"
        elif hot_items:
            level = "🟢 热门线索"
        
        msg = f"""{level}
📅 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
━━━━━━━━━━━━━━━━━━━━
"""
        
        if panic_items:
            msg += "\n⚠️ 恐慌/异常预警:\n"
            for item in panic_items[:3]:
                msg += f"🔴 {item.get('title', '')[:50]}\n"
                msg += f"   来源:{item.get('source', '')} | {item.get('time', '')}\n"
        
        if hot_items:
            msg += f"\n🔥 热门关键字 ({len(hot_items)}条):\n"
            for item in hot_items[:8]:
                impact = {'bullish': '🟢', 'bearish': '🔴', 'neutral': '🟡'}.get(item.get('impact', 'neutral'), '•')
                msg += f"{impact} {item.get('title', '')[:50]}\n"
                msg += f"   {item.get('source', '')} | {item.get('time', '')}\n"
        
        total = len(all_news)
        bullish = sum(1 for n in all_news if n.get('impact') == 'bullish')
        bearish = sum(1 for n in all_news if n.get('impact') == 'bearish')
        msg += f"\n━━━━━━━━━━━━━━━━━━━━\n📊 舆情: {total}条 | 🟢{bullish} 🔴{bearish}\n"
        
        # 发送
        success = send_feishu_message(msg)
        if success:
            print(f"   ✅ 已推送")
        else:
            print(f"   ⚠️ 推送失败，保存到队列")
            queue_file = f"/root/.openclaw/workspace/reports/sentiment_queue_{datetime.now().strftime('%H%M%S')}.txt"
            with open(queue_file, 'w', encoding='utf-8') as f:
                f.write(msg)
        
        return success
        
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        return False

def main():
    print(f"="*50)
    print(f"🔥 热门舆情监控已启动")
    print(f"⏰ 检查间隔: {CHECK_INTERVAL//60}分钟")
    print(f"="*50)
    
    # 启动后立即检查一次
    check_and_push()
    
    # 持续运行
    while True:
        time.sleep(CHECK_INTERVAL)
        
        # 只在交易时间检查 (9:30 - 15:00)
        now = datetime.now()
        weekday = now.weekday()
        
        if weekday >= 5:  # 周末
            continue
        
        hour = now.hour
        if hour < 9 or hour >= 15:
            continue
        
        check_and_push()

if __name__ == "__main__":
    main()