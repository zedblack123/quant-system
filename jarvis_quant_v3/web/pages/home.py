"""
首页 - 系统概览
"""

import streamlit as st
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def show_home():
    """显示首页"""

    st.markdown("## 🤖 贾维斯量化系统 v3.0")
    st.markdown("### 基于 Claude Code 架构的智能量化分析平台")

    # 系统概览
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🕐 系统状态",
            value="运行中",
            delta="正常"
        )

    with col2:
        st.metric(
            label="📊 注册工具",
            value="8",
            delta="已激活"
        )

    with col3:
        st.metric(
            label="🤖 运行Agent",
            value="4",
            delta="全部在线"
        )

    with col4:
        st.metric(
            label="📈 今日分析",
            value="12",
            delta="较昨日+3"
        )

    st.markdown("---")

    # 快捷功能
    st.markdown("### 🚀 快捷功能")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="report-section">
            <div class="section-title">📊 股票分析</div>
            <p>输入股票代码，获取多维度AI量化分析</p>
            <p style="color: gray; font-size: 12px;">支持：基本面、技术面、情绪面、风险评估</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="report-section">
            <div class="section-title">🔧 工具管理</div>
            <p>管理系统工具，配置权限和参数</p>
            <p style="color: gray; font-size: 12px;">8个核心工具已注册并运行</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="report-section">
            <div class="section-title">📈 绩效追踪</div>
            <p>查看Agent表现和交易记录</p>
            <p style="color: gray; font-size: 12px;">Analytics数据驱动优化</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 系统架构
    st.markdown("### 🏗️ 系统架构")

    st.markdown("""
    | 模块 | 功能 | 状态 |
    |------|------|------|
    | 🤖 Agent系统 | 多智能体协同分析 | ✅ 运行中 |
    | 🔧 工具系统 | 标准化工具注册与调用 | ✅ 8工具 |
    | 🪝 Hook系统 | 生命周期钩子管理 | ✅ 4钩子 |
    | 📦 上下文压缩 | 长对话上下文管理 | ✅ 已启用 |
    | 🚩 Feature Flags | 特性开关控制 | ✅ 已配置 |
    | 📊 Analytics | 绩效追踪与分析 | ✅ 运行中 |
    | 🔐 权限系统 | 分级权限控制 | ✅ 已启用 |
    | 🧭 模型路由 | 智能模型选择 | ✅ 已配置 |
    """)

    st.markdown("---")

    # 核心特性
    st.markdown("### ✨ 核心特性")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### 🎯 多Agent协同
        - **基本面Agent**: 财务分析、估值判断
        - **技术面Agent**: 趋势分析、指标计算
        - **情绪面Agent**: 新闻情绪、社交媒体
        - **风险Agent**: 多维度风险评估
        """)

    with col2:
        st.markdown("""
        #### 🔒 安全机制
        - **权限分级**: LOW/MEDIUM/HIGH/ADMIN
        - **Hook系统**: 交易前检查、交易后记录
        - **Analytics追踪**: 持续监控Agent表现
        - **Feature Flags**: 灰度发布，降低风险
        """)

    st.markdown("---")

    # 最新动态
    st.markdown("### 📰 最新动态")

    st.info("""
    🤵 **贾维斯 v3.0 发布**

    基于 Claude Code 架构重构，新增：
    - 工具注册表系统
    - 生命周期钩子
    - 上下文压缩
    - 多模型路由
    - Streamlit前端界面
    """)

    # 版权
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: gray; font-size: 12px;">
        🤖 贾维斯量化系统 v3.0 | 基于 Claude Code 架构设计<br>
        为人山先生提供专业的量化投资辅助
        </div>
        """,
        unsafe_allow_html=True
    )
