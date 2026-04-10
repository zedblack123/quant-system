"""
股票分析页面
"""

import streamlit as st
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def show_analysis():
    """显示分析页面"""

    st.markdown("## 📊 股票分析")
    st.markdown("输入股票代码，获取多维度AI量化分析")

    # 股票输入
    col1, col2 = st.columns([3, 1])

    with col1:
        stock_code = st.text_input(
            "股票代码",
            placeholder="例如: 000001, 600519",
            help="输入6位股票代码"
        )

    with col2:
        stock_name = st.text_input(
            "股票名称（可选）",
            placeholder="例如: 平安银行"
        )

    # 分析选项
    with st.expander("⚙️ 分析选项"):
        col1, col2, col3 = st.columns(3)

        with col1:
            include_fundamental = st.checkbox("基本面分析", value=True)
            include_technical = st.checkbox("技术面分析", value=True)

        with col2:
            include_sentiment = st.checkbox("情绪面分析", value=True)
            include_risk = st.checkbox("风险评估", value=True)

        with col3:
            user_permission = st.selectbox(
                "用户权限",
                options=[1, 2, 3, 4],
                format_func=lambda x: {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "ADMIN"}.get(x, "LOW"),
                index=1
            )

    # 分析按钮
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        analyze_button = st.button("🚀 开始分析", type="primary", use_container_width=True)

    # 分析结果
    if analyze_button and stock_code:
        with st.spinner("🤖 AI正在分析..."):
            try:
                # 导入并初始化协调器
                from jarvis_quant_v3.agents.coordinator import MultiAgentCoordinator

                coordinator = MultiAgentCoordinator()

                # 运行分析
                async def run_analysis():
                    return await coordinator.analyze_stock(
                        stock_code=stock_code,
                        stock_name=stock_name or stock_code,
                        user_permission=user_permission
                    )

                result = asyncio.run(run_analysis())

                # 显示结果
                st.success("✅ 分析完成！")

                # 决策显示
                st.markdown("---")
                st.markdown("### 🎯 分析结果")

                col1, col2, col3 = st.columns(3)

                decision_emoji = {
                    "STRONG_BUY": "🟢 强烈买入",
                    "BUY": "🟢 买入",
                    "HOLD": "🟡 持有",
                    "SELL": "🔴 卖出",
                    "STRONG_SELL": "🔴 强烈卖出"
                }

                with col1:
                    st.metric(
                        label="📊 投资决策",
                        value=decision_emoji.get(result.decision, result.decision),
                    )

                with col2:
                    st.metric(
                        label="📈 置信度",
                        value=f"{result.confidence:.1%}",
                    )

                with col3:
                    st.metric(
                        label="⏰ 分析时间",
                        value=result.analysis_time,
                    )

                st.markdown("---")

                # 推理过程
                st.markdown("### 📝 推理过程")
                st.code(result.reasoning, language="markdown")

                st.markdown("---")

                # 详细报告
                st.markdown("### 📋 各维度分析")

                tabs = st.tabs(["📊 基本面", "📈 技术面", "💬 情绪面", "⚠️ 风险"])

                with tabs[0]:
                    if "fundamental" in result.reports:
                        st.markdown(result.reports["fundamental"])
                    else:
                        st.info("未启用基本面分析")

                with tabs[1]:
                    if "technical" in result.reports:
                        st.markdown(result.reports["technical"])
                    else:
                        st.info("未启用技术面分析")

                with tabs[2]:
                    if "sentiment" in result.reports:
                        st.markdown(result.reports["sentiment"])
                    else:
                        st.info("未启用情绪面分析")

                with tabs[3]:
                    if "risk" in result.reports:
                        st.markdown(result.reports["risk"])
                    else:
                        st.info("未启用风险评估")

                # 保存报告
                st.markdown("---")
                if st.button("💾 保存报告"):
                    import json
                    from datetime import datetime

                    report_data = result.to_dict()
                    filename = f"/tmp/{stock_code}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(report_data, f, ensure_ascii=False, indent=2)

                    st.success(f"✅ 报告已保存到: {filename}")

            except Exception as e:
                st.error(f"❌ 分析失败: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    elif analyze_button and not stock_code:
        st.warning("⚠️ 请输入股票代码")

    # 使用说明
    st.markdown("---")
    with st.expander("📖 使用说明"):
        st.markdown("""
        ### 如何使用股票分析

        1. **输入股票代码**: 输入6位股票代码，如 `000001`（平安银行）或 `600519`（贵州茅台）
        2. **选择分析维度**: 勾选需要分析的项目
        3. **设置权限等级**: 根据您的账户类型选择相应权限
        4. **点击分析**: 系统将调用多Agent进行协同分析

        ### 分析维度说明

        - **基本面分析**: 财务指标、盈利能力、估值水平
        - **技术面分析**: 均线系统、MACD、KDJ等技术指标
        - **情绪面分析**: 新闻舆情、社交媒体讨论
        - **风险评估**: 市场风险、流动性风险、财务风险
        """)
