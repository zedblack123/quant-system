"""
绩效追踪页面
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def show_performance():
    """显示绩效追踪页面"""

    st.markdown("## 📈 绩效追踪")
    st.markdown("查看Agent表现和交易记录")

    # Analytics数据
    st.markdown("### 🤖 Agent表现")

    # Agent指标
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 总调用次数",
            value="1,234",
            delta="今日 +56"
        )

    with col2:
        st.metric(
            label="✅ 平均成功率",
            value="94.2%",
            delta="较上周 +2.1%"
        )

    with col3:
        st.metric(
            label="⚡ 平均延迟",
            value="320ms",
            delta="较上周 -15ms"
        )

    with col4:
        st.metric(
            label="🎯 平均置信度",
            value="78.5%",
            delta="较上周 +1.2%"
        )

    st.markdown("---")

    # Agent详情表格
    st.markdown("### 📋 Agent详情")

    agent_data = pd.DataFrame({
        "Agent": ["FundamentalAgent", "TechnicalAgent", "SentimentAgent", "RiskAgent"],
        "总调用": [456, 389, 234, 155],
        "成功": [432, 371, 218, 141],
        "失败": [24, 18, 16, 14],
        "成功率": ["94.7%", "95.4%", "93.2%", "91.0%"],
        "平均延迟(ms)": [280, 350, 420, 230],
        "置信度": ["82%", "76%", "71%", "85%"]
    })

    st.table(agent_data)

    # 可视化
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 调用分布")

        # 饼图
        fig = px.pie(
            agent_data,
            values="总调用",
            names="Agent",
            title="Agent调用分布",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(
            paper_bgcolor="#161B22",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### ⚡ 响应时间")

        # 柱状图
        fig = px.bar(
            agent_data,
            x="Agent",
            y="平均延迟(ms)",
            title="Agent平均响应时间",
            color="平均延迟(ms)",
            color_continuous_scale="RdYlGn_r"
        )
        fig.update_layout(
            paper_bgcolor="#161B22",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 交易记录
    st.markdown("### 💹 交易记录")

    trade_data = pd.DataFrame({
        "时间": ["2026-04-03 10:30", "2026-04-03 11:15", "2026-04-03 14:20", "2026-04-03 15:00"],
        "股票": ["000001", "600519", "000002", "300750"],
        "方向": ["买入", "买入", "卖出", "买入"],
        "数量": [1000, 100, 500, 200],
        "价格": [12.50, 1680.00, 28.30, 580.00],
        "金额": ["12,500", "168,000", "14,150", "116,000"],
        "状态": ["✅ 成功", "✅ 成功", "✅ 成功", "✅ 成功"]
    })

    st.table(trade_data)

    # 交易统计
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 今日买入",
            value="296,500",
            delta="4笔"
        )

    with col2:
        st.metric(
            label="💵 今日卖出",
            value="14,150",
            delta="1笔"
        )

    with col3:
        st.metric(
            label="📈 胜率",
            value="75.0%",
            delta="较上周 +5%"
        )

    with col4:
        st.metric(
            label="🎯 盈亏比",
            value="1.85",
            delta="+0.15"
        )

    st.markdown("---")

    # 收益率曲线
    st.markdown("### 📈 收益率曲线")

    # 模拟收益率数据
    dates = pd.date_range(start="2026-03-01", end="2026-04-03", freq="D")
    returns = [0]
    for i in range(1, len(dates)):
        daily_return = (hash(str(dates[i])) % 100 - 45) / 1000
        returns.append(returns[-1] * (1 + daily_return))

    df = pd.DataFrame({
        "日期": dates,
        "收益率": [f"{(r-1)*100:.2f}%" for r in returns],
        "累计收益": returns
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["日期"],
        y=[(r-1)*100 for r in df["累计收益"]],
        mode="lines+markers",
        name="累计收益率",
        line=dict(color="#1E88E5", width=2)
    ))

    fig.update_layout(
        title="累计收益率曲线",
        xaxis_title="日期",
        yaxis_title="收益率 (%)",
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        font_color="white"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Analytics报告
    st.markdown("### 📊 Analytics报告")

    with st.expander("📋 查看完整报告"):
        st.code("""
========================================
🤖 贾维斯量化系统 Analytics报告
========================================

报告时间: 2026-04-03 18:00:00

Agent表现统计:
----------------------------------------
FundamentalAgent:
  - 总调用: 456次
  - 成功率: 94.7%
  - 平均延迟: 280ms
  - 置信度: 82%
  - 信号分布: 买(180) 卖(90) 持(186)

TechnicalAgent:
  - 总调用: 389次
  - 成功率: 95.4%
  - 平均延迟: 350ms
  - 置信度: 76%
  - 信号分布: 买(155) 卖(78) 持(156)

SentimentAgent:
  - 总调用: 234次
  - 成功率: 93.2%
  - 平均延迟: 420ms
  - 置信度: 71%
  - 信号分布: 买(98) 卖(52) 持(84)

RiskAgent:
  - 总调用: 155次
  - 成功率: 91.0%
  - 平均延迟: 230ms
  - 置信度: 85%
  - 信号分布: 买(45) 卖(38) 持(72)

交易统计:
----------------------------------------
总交易次数: 5
成功: 5 (100%)
失败: 0 (0%)
胜率: 75.0%
盈亏比: 1.85

建议:
----------------------------------------
1. FundamentalAgent 表现最佳，建议提高权重
2. TechnicalAgent 延迟较高，考虑优化
3. SentimentAgent 置信度偏低，需改进模型
4. RiskAgent 风险控制良好，继续保持
        """)
