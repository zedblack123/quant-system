"""
系统设置页面
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def show_settings():
    """显示设置页面"""

    st.markdown("## ⚙️ 系统设置")
    st.markdown("配置系统参数、Feature Flags和API设置")

    # Feature Flags
    st.markdown("### 🚩 Feature Flags")

    st.info("Feature Flags 用于控制系统中各功能的启用/禁用，支持灰度发布和A/B测试。")

    # Feature Flag 开关
    col1, col2, col3 = st.columns(3)

    with col1:
        new_strategy_v2 = st.toggle("🔬 新策略v2", value=False)
        if new_strategy_v2:
            st.success("已启用")
        else:
            st.warning("已禁用")

    with col2:
        multi_factor_model = st.toggle("📊 多因子模型", value=False)
        if multi_factor_model:
            st.success("已启用")
        else:
            st.warning("已禁用")

    with col3:
        ai_sentiment = st.toggle("🤖 AI情绪分析", value=True)
        if ai_sentiment:
            st.success("已启用")
        else:
            st.warning("已禁用")

    col1, col2, col3 = st.columns(3)

    with col1:
        risk_control_v2 = st.toggle("🛡️ 风险控制v2", value=False)
        if risk_control_v2:
            st.success("已启用")
        else:
            st.warning("已禁用")

    with col2:
        auto_trade = st.toggle("⚡ 自动交易", value=False)
        if auto_trade:
            st.error("已启用 - 注意风险")
        else:
            st.warning("已禁用")

    with col3:
        debug_mode = st.toggle("🔍 调试模式", value=False)

    st.markdown("---")

    # API配置
    st.markdown("### 🔑 API配置")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### LLM API")

        deepseek_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            value="••••••••••••••••",
            help="输入您的DeepSeek API密钥"
        )

        deepseek_url = st.text_input(
            "DeepSeek API URL",
            value="https://api.deepseek.com"
        )

        openai_key = st.text_input(
            "OpenAI API Key (可选)",
            type="password",
            value="••••••••••••••••",
            help="用于支持更多模型"
        )

    with col2:
        st.markdown("#### 数据API")

        tushare_token = st.text_input(
            "Tushare Token (可选)",
            type="password",
            value="••••••••••••••••",
            help="用于获取更完整的数据"
        )

        ak_share_key = st.text_input(
            "AKShare Key (可选)",
            type="password",
            value="••••••••••••••••"
        )

    if st.button("💾 保存API配置"):
        st.success("✅ API配置已保存（演示模式，未实际保存）")

    st.markdown("---")

    # 权限配置
    st.markdown("### 🔐 权限配置")

    st.markdown("#### 用户权限等级")

    permission_col1, permission_col2, permission_col3, permission_col4 = st.columns(4)

    with permission_col1:
        st.metric("LOW", "1级", "查看/分析")

    with permission_col2:
        st.metric("MEDIUM", "2级", "小额交易")

    with permission_col3:
        st.metric("HIGH", "3级", "大额交易")

    with permission_col4:
        st.metric("ADMIN", "4级", "完全权限")

    st.markdown("#### 交易限额配置")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.number_input(
            "LOW级单笔限额",
            value=0,
            max_value=10000,
            step=1000,
            help="LOW权限的单笔最大交易金额"
        )

    with col2:
        st.number_input(
            "MEDIUM级单笔限额",
            value=100000,
            max_value=1000000,
            step=10000,
            help="MEDIUM权限的单笔最大交易金额"
        )

    with col3:
        st.number_input(
            "HIGH级单笔限额",
            value=1000000,
            max_value=10000000,
            step=100000,
            help="HIGH权限的单笔最大交易金额"
        )

    st.markdown("---")

    # 模型配置
    st.markdown("### 🧭 模型路由配置")

    st.markdown("配置不同任务使用的模型")

    model_config = {
        "fundamental_analysis": {"provider": "DeepSeek", "model": "deepseek-chat", "temperature": 0.3},
        "technical_analysis": {"provider": "DeepSeek", "model": "deepseek-chat", "temperature": 0.5},
        "sentiment_analysis": {"provider": "DeepSeek", "model": "deepseek-chat", "temperature": 0.7},
        "risk_assessment": {"provider": "DeepSeek", "model": "deepseek-chat", "temperature": 0.2},
        "final_decision": {"provider": "DeepSeek", "model": "deepseek-chat", "temperature": 0.4},
    }

    for task, config in model_config.items():
        with st.expander(f"📝 {task}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.selectbox(
                    "Provider",
                    options=["DeepSeek", "OpenAI", "Anthropic"],
                    index=["DeepSeek", "OpenAI", "Anthropic"].index(config["provider"]),
                    key=f"provider_{task}"
                )

            with col2:
                st.text_input("Model", value=config["model"], key=f"model_{task}")

            with col3:
                st.slider("Temperature", min_value=0.0, max_value=1.0, value=config["temperature"], step=0.1, key=f"temp_{task}")

    st.markdown("---")

    # 系统信息
    st.markdown("### ℹ️ 系统信息")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **版本信息**
        - 系统版本: v3.0
        - 构建日期: 2026-04-03
        - Claude架构版本: 1.0
        """)

    with col2:
        st.markdown("""
        **运行环境**
        - Python: 3.10+
        - Streamlit: 1.0+
        - 操作系统: Linux
        - 时区: Asia/Shanghai
        """)

    st.markdown("---")

    # 保存设置
    if st.button("💾 保存所有设置", type="primary", use_container_width=True):
        st.success("✅ 设置已保存！")
        st.balloons()
