#!/bin/bash
# 定时任务日志
LOG="/root/.openclaw/workspace/logs/cron.log"

# 创建日志目录
mkdir -p /root/.openclaw/workspace/logs

echo "["$(date +"%Y-%m-%d %H:%M:%S")"] 执行定时任务" >> $LOG

# 执行报告生成
cd /root/.openclaw/workspace
python3 scripts/auto_report_sender.py --morning >> $LOG 2>&1 &
python3 scripts/auto_report_sender.py --evening >> $LOG 2>&1 &

echo "["$(date +"%Y-%m-%d %H:%M:%S")"] 定时任务已触发" >> $LOG
