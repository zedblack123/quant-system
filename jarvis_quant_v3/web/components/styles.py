"""
自定义样式组件
"""

import streamlit as st


def apply_custom_style():
    """应用自定义样式"""

    st.markdown("""
    <style>
        /* 主色调 */
        :root {
            --primary-color: #1E88E5;
            --secondary-color: #43A047;
            --accent-color: #FF9800;
            --background-color: #0D1117;
            --text-color: #E6EDF3;
        }

        /* 全局字体 */
        * {
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
        }

        /* 标题样式 */
        h1, h2, h3 {
            color: var(--text-color);
        }

        /* 卡片样式 */
        .stCard {
            background-color: #161B22;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
        }

        /* 成功样式 */
        .success-box {
            background-color: rgba(67, 160, 71, 0.1);
            border-left: 4px solid #43A047;
            padding: 15px;
            border-radius: 0 5px 5px 0;
            margin: 10px 0;
        }

        /* 警告样式 */
        .warning-box {
            background-color: rgba(255, 152, 0, 0.1);
            border-left: 4px solid #FF9800;
            padding: 15px;
            border-radius: 0 5px 5px 0;
            margin: 10px 0;
        }

        /* 错误样式 */
        .error-box {
            background-color: rgba(229, 57, 53, 0.1);
            border-left: 4px solid #E53935;
            padding: 15px;
            border-radius: 0 5px 5px 0;
            margin: 10px 0;
        }

        /* 指标卡片 */
        .metric-card {
            background: linear-gradient(135deg, #1E88E5 0%, #43A047 100%);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            color: white;
        }

        /* 导航栏 */
        .nav-bar {
            background-color: #161B22;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        /* 表格样式 */
        .dataframe {
            background-color: #161B22 !important;
        }

        /* 按钮样式 */
        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border-radius: 5px;
            padding: 10px 25px;
            border: none;
            transition: all 0.3s;
        }

        .stButton > button:hover {
            background-color: #1565C0;
            transform: translateY(-2px);
        }

        /* 侧边栏样式 */
        .css-1d391kg {
            background-color: #161B22;
        }

        /* 输入框样式 */
        .stTextInput > div > div > input {
            background-color: #0D1117;
            color: var(--text-color);
            border: 1px solid #30363D;
            border-radius: 5px;
        }

        /* 进度条样式 */
        .stProgress > div > div > div {
            background-color: var(--primary-color);
        }

        /* Tab样式 */
        .stTabs > div > div {
            background-color: #161B22;
            border-radius: 5px;
        }

        /* 扩展样式 */
        .report-section {
            background-color: #161B22;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
        }

        .section-title {
            color: var(--primary-color);
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--primary-color);
        }

        /* 决策标签 */
        .decision-strong-buy {
            background-color: #2E7D32;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
            font-weight: bold;
        }

        .decision-buy {
            background-color: #43A047;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
        }

        .decision-hold {
            background-color: #FF9800;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
        }

        .decision-sell {
            background-color: #E53935;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
        }

        .decision-strong-sell {
            background-color: #B71C1C;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
