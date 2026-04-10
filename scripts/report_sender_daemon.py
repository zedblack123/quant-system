#!/usr/bin/env python3
"""
贾维斯定时推送守护进程
检查reports目录，有新报告就发送到我(人山先生)的飞书
"""
import os
import sys
import time
import requests
import glob

# OpenClaw Gateway配置
GATEWAY_TOKEN = "7c8a50ba1197309b310a8cb6e9f4190660e82aff203b1a39"
GATEWAY_PORT = 18789
USER_OPEN_ID = "ou_636754d2a4956be2f5928918767a62e7"

REPORTS_DIR = "/root/.openclaw/workspace/reports"
PROCESSED_FILE = "/root/.openclaw/workspace/reports/.sent_history"

def get_processed_ids():
    """获取已处理的报告ID"""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, 'r') as f:
        return set(line.strip() for line in f)

def add_processed_id(report_id):
    """标记已处理"""
    with open(PROCESSED_FILE, 'a') as f:
        f.write(report_id + '\n')

def send_to_feishu(content):
    """通过OpenClaw gateway发送"""
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
        return resp.status_code in [200, 201, 204]
    except Exception as e:
        print(f"发送失败: {e}")
        return False

def check_and_send():
    """检查并发送新报告"""
    processed = get_processed_ids()
    
    # 查找新的报告
    for filepath in sorted(glob.glob(f"{REPORTS_DIR}/*.md")):
        report_id = os.path.basename(filepath)
        
        # 跳过已处理的
        if report_id in processed:
            continue
        
        # 跳过非报告文件
        basename = os.path.basename(filepath)
        if basename.startswith('.'):
            continue
        
        # 读取报告内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取纯文本（去掉markdown格式）
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            # 跳过图片和链接
            if line.startswith('![') or line.startswith('[!['):
                continue
            # 清理markdown
            line = line.replace('**', '').replace('*', '')
            clean_lines.append(line)
        
        # 发送到飞书
        if send_to_feishu('\n'.join(clean_lines)):
            add_processed_id(report_id)
            print(f"已发送: {report_id}")
    
    # 查找新的txt报告
    for filepath in sorted(glob.glob(f"{REPORTS_DIR}/*.txt")):
        report_id = os.path.basename(filepath)
        
        if report_id in processed:
            continue
        
        if report_id.startswith('.'):
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if send_to_feishu(content):
            add_processed_id(report_id)
            print(f"已发送: {report_id}")

def main():
    print("="*50)
    print("贾维斯守护进程启动")
    print(f"监控目录: {REPORTS_DIR}")
    print("每分钟检查一次新报告")
    print("="*50)
    
    while True:
        try:
            check_and_send()
        except Exception as e:
            print(f"检查出错: {e}")
        
        time.sleep(60)  # 每分钟检查

if __name__ == "__main__":
    main()
