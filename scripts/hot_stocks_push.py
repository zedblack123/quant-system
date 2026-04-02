#!/usr/bin/env python3
"""
热点股份/板块/概念 早间推送脚本
每天 9:25 集合竞价结束后推送当天热点信息
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
        
        payload = {
            "receive_id": FEISHU_CONFIG['user_open_id'],
            "msg_type": "text",
            "content": json.dumps({"text": content})
        }
        
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

def get_hot_data():
    """获取热点数据"""
    from scripts.data_manager_tushare import DataManagerV2
    from scripts.news_manager import NewsManager
    
    dm = DataManagerV2()
    today = datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    result = {
        'limit_up': None,      # 涨停股
        'hot_sectors': None,   # 热门板块
        'fund_flow': None,     # 资金流向
    }
    
    # 获取涨停股（今日）
    print("📊 获取今日涨停股...")
    try:
        zt_df = dm.get_akshare_limit_up(today)
        if zt_df is not None and len(zt_df) > 0:
            result['limit_up'] = zt_df
            print(f"   涨停股: {len(zt_df)}只")
    except Exception as e:
        print(f"   ⚠️ 获取涨停股失败: {e}")
    
    # 获取板块资金流
    print("📊 获取板块资金流...")
    try:
        sector_df = dm.get_akshare_sector()
        if sector_df is not None and len(sector_df) > 0:
            result['fund_flow'] = sector_df
            print(f"   板块数据: {len(sector_df)}个")
    except Exception as e:
        print(f"   ⚠️ 获取板块失败: {e}")
    
    dm.close()
    return result

def format_hot_report(data):
    """格式化热点报告"""
    now = datetime.now()
    date_str = now.strftime('%Y年%m月%d日')
    time_str = now.strftime('%H:%M')
    
    report = f"""🔥 A股热点速递
📅 {date_str} {time_str}（集合竞价结束）
{'='*40}

"""
    
    # 1. 涨停股统计
    zt_df = data.get('limit_up')
    if zt_df is not None and len(zt_df) > 0:
        # 统计涨停相关
        zt_count = len(zt_df)
        
        # 筛选涨停股（排除ST）
        zt_stocks = zt_df[~zt_df.get('名称', '').str.contains('ST', na=False)] if '名称' in zt_df.columns else zt_df
        
        # 首板和连板
        first_limit = zt_stocks[zt_stocks.get('连板数', 0) == 1] if '连板数' in zt_stocks.columns else zt_stocks
        consecutive = zt_stocks[zt_stocks.get('连板数', 0) > 1] if '连板数' in zt_stocks.columns else None
        
        report += f"📈 涨停股\n"
        report += f"   涨停总数: {zt_count}只\n"
        report += f"   首板: {len(first_limit)}只\n"
        if consecutive is not None and len(consecutive) > 0:
            report += f"   连板: {len(consecutive)}只\n"
        
        # 显示热门涨停股
        report += f"\n   热门涨停:\n"
        
        # 按成交量/封单排序取前5
        sort_col = '成交额' if '成交额' in zt_stocks.columns else ('涨跌幅' if '涨跌幅' in zt_stocks.columns else None)
        if sort_col:
            top_stocks = zt_stocks.nlargest(5, sort_col) if sort_col in zt_stocks.columns else zt_stocks.head(5)
        else:
            top_stocks = zt_stocks.head(5)
        
        for _, row in top_stocks.iterrows():
            name = str(row.get('名称', ''))[:6]
            code = str(row.get('代码', ''))
            board = row.get('连板数', 0)
            zt_time = str(row.get('涨停时间', ''))[:5] if '涨停时间' in row.index else '--:--'
            board_str = f" 第{int(board)}板" if board > 1 else ""
            report += f"   • {name}({code}){board_str} 涨停时间{zt_time}\n"
    else:
        report += f"📈 涨停股\n   暂无数据\n"
    
    report += f"\n"
    
    # 2. 热门板块
    sector_df = data.get('fund_flow')
    if sector_df is not None and len(sector_df) > 0:
        report += f"🏆 热门板块（按资金流）\n"
        
        # 东方财富板块格式
        if '名称' in sector_df.columns and '今日主力净流入-净额' in sector_df.columns:
            # 按主力净流入排序
            money_col = '今日主力净流入-净额'
            if money_col in sector_df.columns:
                top_sectors = sector_df.nlargest(8, money_col)
                for _, row in top_sectors.iterrows():
                    name = str(row.get('名称', ''))[:8]
                    money = row.get(money_col, 0)
                    if money and money > 0:
                        report += f"   • {name} +{money/1e8:.2f}亿\n"
        elif '板块名称' in sector_df.columns:
            # 另一种格式
            top_sectors = sector_df.head(8)
            for _, row in top_sectors.iterrows():
                name = str(row.get('板块名称', ''))[:8]
                change = row.get('涨跌幅', 0)
                report += f"   • {name} {change:+.2f}%\n"
        else:
            # 显示前8个
            top_sectors = sector_df.head(8)
            cols = top_sectors.columns.tolist()
            name_col = cols[0] if cols else 'unknown'
            for _, row in top_sectors.iterrows():
                name = str(row.get(name_col, ''))[:8]
                report += f"   • {name}\n"
    
    report += f"\n"
    
    # 3. 概念题材
    if zt_df is not None and len(zt_df) > 0 and '所属行业' in zt_df.columns:
        report += f"💡 概念题材\n"
        # 统计各行业涨停数
        industry_count = zt_df['所属行业'].value_counts().head(5)
        for industry, count in industry_count.items():
            report += f"   • {industry}: {count}只涨停\n"
    elif zt_df is not None and len(zt_df) > 0:
        # 尝试从股票名称提取概念
        concepts = []
        for _, row in zt_df.head(10).iterrows():
            name = str(row.get('名称', ''))
            # 简单提取概念关键词
            concept_kw = []
            kw_map = {
                'AI': ['AI', '人工智能'],
                '新能源': ['新能源', '锂电', '光伏'],
                '芯片': ['芯片', '半导体', '集成电路'],
                '军工': ['军工', '航天'],
                '医药': ['医药', '医疗'],
                '机器人': ['机器人', '人工智能'],
            }
            for kw, words in kw_map.items():
                if any(w in name for w in words):
                    concept_kw.append(kw)
            concepts.extend(concept_kw)
        
        if concepts:
            from collections import Counter
            top_concepts = Counter(concepts).most_common(5)
            report += f"   热门概念:\n"
            for concept, count in top_concepts:
                report += f"   • {concept}: {count}只\n"
    
    report += f"\n{'='*40}\n"
    report += f"⏰ 推送时间: {now.strftime('%H:%M:%S')}\n"
    report += f"📊 数据来源: 东方财富/AKShare"
    
    return report

def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"🔥 热点推送脚本 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 检查是否为交易日（周一到周五）
    weekday = datetime.now().weekday()
    if weekday >= 5:  # 周六、周日
        print("📅 周末休市，跳过推送")
        return
    
    try:
        # 获取数据
        print("📡 获取热点数据...")
        data = get_hot_data()
        
        # 格式化报告
        report = format_hot_report(data)
        print(f"\n📝 生成的报告:\n{report}")
        
        # 保存报告
        reports_dir = '/root/.openclaw/workspace/reports'
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"热点推送_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存: {filepath}")
        
        # 发送到飞书
        print("\n📤 发送到飞书...")
        send_feishu_message(report)
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()