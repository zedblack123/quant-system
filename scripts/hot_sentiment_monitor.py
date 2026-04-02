#!/usr/bin/env python3
"""
热门舆情监控脚本
每10分钟检查一次，有热门关键字就推送
"""

import sys
import os
sys.path.insert(0, '/root/.openclaw/workspace')

from scripts.news_collector_v2 import MultiSourceNewsCollector
from datetime import datetime

# 热门关键字配置
HOT_KEYWORDS = [
    # A股相关
    '涨停', '跌停', '暴涨', '暴跌', '闪崩', '停牌', '复牌',
    '龙头', '妖股', '牛股', '白马',
    # 重大政策
    '降准', '加息', '印花税', '证监会', '央行', '财政部',
    # 国际市场
    '美联储', '非农', 'CPI', 'GDP', '战争', '制裁',
    # 行业重大
    '新能源', '半导体', '人工智能', '芯片', '医药集采',
    # 突发
    '黑天鹅', '利空', '利好', '业绩暴增', '业绩暴雷',
    # 大宗商品/期货（重要！）
    '合约暴跌', '合约大涨', '期货暴跌', '期货涨停', '期货跌停',
    '原油暴跌', '原油大涨', '黄金暴跌', '黄金大涨',
    '上期所', '大商所', '郑商所', '集运', '燃油',
]

# 恐慌/热度指标
PANIC_KEYWORDS = [
    '崩盘', '股灾', '清仓', '踩踏', '做空', '爆仓',
    '外资出逃', '主力砸盘', '大规模减持',
    '暴跌', '闪崩', '跌停',
]

def check_hot_sentiment():
    """检查热门舆情"""
    collector = MultiSourceNewsCollector()
    all_news = collector.get_all_news()
    
    hot_items = []
    panic_items = []
    
    for news in all_news:
        title = news.get('title', '').lower()
        source = news.get('source', '')
        
        # 检查热门关键字
        for kw in HOT_KEYWORDS:
            if kw.lower() in title:
                hot_items.append(news)
                break
        
        # 检查恐慌关键字
        for kw in PANIC_KEYWORDS:
            if kw.lower() in title:
                panic_items.append(news)
                break
    
    return hot_items, panic_items, all_news

def format_push_message(hot_items, panic_items, all_news):
    """格式化推送消息"""
    now = datetime.now().strftime('%H:%M')
    
    # 判断热度等级
    if panic_items:
        level = "🔴 恐慌舆情"
    elif len(hot_items) >= 5:
        level = "🟠 高度活跃"
    elif len(hot_items) >= 3:
        level = "🟡 热门动态"
    elif hot_items:
        level = "🟢 热门线索"
    else:
        return None  # 无热门，不推送
    
    report = f"""{level}
📅 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
━━━━━━━━━━━━━━━━━━━━
"""
    
    # 恐慌舆情优先显示
    if panic_items:
        report += "\n⚠️ 恐慌/异常预警:\n"
        for item in panic_items[:3]:
            report += f"🔴 {item.get('title', '')[:50]}\n"
            report += f"   来源:{item.get('source', '')} | {item.get('time', '')}\n"
    
    # 热门舆情
    if hot_items:
        report += f"\n🔥 热门关键字 ({len(hot_items)}条):\n"
        for item in hot_items[:8]:
            impact = {'bullish': '🟢', 'bearish': '🔴', 'neutral': '🟡'}.get(item.get('impact', 'neutral'), '•')
            report += f"{impact} {item.get('title', '')[:50]}\n"
            report += f"   {item.get('source', '')} | {item.get('time', '')}\n"
    
    # 总结
    total = len(all_news)
    bullish = sum(1 for n in all_news if n.get('impact') == 'bullish')
    bearish = sum(1 for n in all_news if n.get('impact') == 'bearish')
    
    report += f"""
━━━━━━━━━━━━━━━━━━━━
📊 舆情概览: 共{total}条 | 🟢{bullish}利好 🔴{bearish}利空
⏰ 检测时间: {now}
"""
    
    return report

def main():
    print(f"\n{'='*50}")
    print(f"🔥 热门舆情监控 - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}\n")
    
    hot_items, panic_items, all_news = check_hot_sentiment()
    
    print(f"检测到 {len(all_news)} 条新闻")
    print(f"热门关键字匹配: {len(hot_items)} 条")
    print(f"恐慌预警匹配: {len(panic_items)} 条")
    
    # 总是保存检测结果
    os.makedirs('/root/.openclaw/workspace/reports', exist_ok=True)
    log_file = f"/root/.openclaw/workspace/reports/sentiment_log_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总新闻: {len(all_news)}\n")
        f.write(f"热门匹配: {len(hot_items)}\n")
        f.write(f"恐慌预警: {len(panic_items)}\n\n")
        f.write("热门新闻:\n")
        for item in hot_items:
            f.write(f"  [{item.get('source')}] {item.get('title')}\n")
    
    print(f"📝 日志已保存: {log_file}")
    
    # 如果有热门或恐慌，返回消息内容
    if hot_items or panic_items:
        msg = format_push_message(hot_items, panic_items, all_news)
        print(f"\n📤 准备推送...")
        return msg
    else:
        print(f"\n⏭️ 无热门舆情，跳过推送")
        return None

if __name__ == "__main__":
    result = main()
    if result:
        print("\n" + result)