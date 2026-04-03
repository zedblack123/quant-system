"""
工具管理页面
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def show_tools():
    """显示工具管理页面"""

    st.markdown("## 🔧 工具管理")
    st.markdown("管理系统工具，配置权限和参数")

    # 导入工具系统
    from jarvis_quant_v3.tools.registry import ToolRegistry

    registry = ToolRegistry.get_instance()

    # 工具列表
    st.markdown("### 📦 已注册工具")

    tools_data = [
        {"名称": "StockDataTool", "功能": "获取股票数据", "权限等级": "LOW", "状态": "✅ 正常"},
        {"名称": "TechnicalAnalysisTool", "功能": "技术指标计算", "权限等级": "LOW", "状态": "✅ 正常"},
        {"名称": "NewsSearchTool", "功能": "新闻搜索", "权限等级": "LOW", "状态": "✅ 正常"},
        {"名称": "SocialMediaTool", "功能": "社交媒体情绪", "权限等级": "LOW", "状态": "✅ 正常"},
        {"名称": "RiskCalcTool", "功能": "风险计算", "权限等级": "MEDIUM", "状态": "✅ 正常"},
        {"名称": "TradeExecuteTool", "功能": "执行交易", "权限等级": "HIGH", "状态": "✅ 正常"},
        {"名称": "PortfolioTool", "功能": "持仓管理", "权限等级": "HIGH", "状态": "✅ 正常"},
        {"名称": "BacktestTool", "功能": "回测工具", "权限等级": "LOW", "状态": "✅ 正常"},
    ]

    st.table(tools_data)

    st.markdown("---")

    # 权限配置
    st.markdown("### 🔐 权限等级说明")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.info("""
        **LOW (1级)**
        - 查看数据
        - 分析功能
        - 无交易权限
        """)

    with col2:
        st.warning("""
        **MEDIUM (2级)**
        - 小额交易
        - 策略调整
        - 限额10万
        """)

    with col3:
        st.error("""
        **HIGH (3级)**
        - 大额交易
        - 权限申请
        - 限额100万
        """)

    with col4:
        st.error("""
        **ADMIN (4级)**
        - 完全权限
        - 系统管理
        - 无限制
        """)

    st.markdown("---")

    # 工具详情
    st.markdown("### 📋 工具详情")

    selected_tool = st.selectbox(
        "选择工具查看详情",
        options=[t["名称"] for t in tools_data]
    )

    if selected_tool:
        tool_info = {
            "StockDataTool": {
                "名称": "StockDataTool",
                "功能": "获取股票实时和历史数据",
                "权限等级": "LOW",
                "输入参数": ["stock_code", "data_type", "start_date", "end_date"],
                "输出": "股票价格、成交量、财务数据等",
                "依赖": "AKShare / Tushare"
            },
            "TechnicalAnalysisTool": {
                "名称": "TechnicalAnalysisTool",
                "功能": "计算技术分析指标",
                "权限等级": "LOW",
                "输入参数": ["stock_code", "indicators"],
                "输出": "MA, MACD, KDJ, RSI, BOLL等",
                "依赖": "Pandas, NumPy, TA-Lib"
            },
            "NewsSearchTool": {
                "名称": "NewsSearchTool",
                "功能": "搜索股票相关新闻",
                "权限等级": "LOW",
                "输入参数": ["stock_code", "stock_name", "max_results"],
                "输出": "新闻标题、摘要、时间",
                "依赖": "东方财富API"
            },
            "SocialMediaTool": {
                "名称": "SocialMediaTool",
                "功能": "获取社交媒体情绪数据",
                "权限等级": "LOW",
                "输入参数": ["stock_code", "platforms"],
                "输出": "讨论量、情感倾向、热度指数",
                "依赖": "东财、淘股吧API"
            },
            "RiskCalcTool": {
                "名称": "RiskCalcTool",
                "功能": "计算多维度风险指标",
                "权限等级": "MEDIUM",
                "输入参数": ["stock_code", "position"],
                "输出": "VaR, Beta, 波动率, 流动性指标",
                "依赖": "内部算法"
            },
            "TradeExecuteTool": {
                "名称": "TradeExecuteTool",
                "功能": "执行股票交易",
                "权限等级": "HIGH",
                "输入参数": ["stock_code", "direction", "quantity", "price"],
                "输出": "交易结果、成交价格",
                "依赖": "券商API"
            },
            "PortfolioTool": {
                "名称": "PortfolioTool",
                "功能": "管理持仓和资金",
                "权限等级": "HIGH",
                "输入参数": ["action", "stock_code", "quantity"],
                "输出": "持仓明细、资金余额",
                "依赖": "账户系统"
            },
            "BacktestTool": {
                "名称": "BacktestTool",
                "功能": "策略回测",
                "权限等级": "LOW",
                "输入参数": ["strategy", "start_date", "end_date", "initial_capital"],
                "输出": "回测报告、收益率、夏普比率",
                "依赖": "历史数据库"
            }
        }

        info = tool_info.get(selected_tool, {})

        if info:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                **功能**: {info.get('功能', 'N/A')}
                **权限等级**: {info.get('权限等级', 'N/A')}
                """)

            with col2:
                st.markdown(f"""
                **输入参数**: {', '.join(info.get('输入参数', []))}
                **依赖**: {info.get('依赖', 'N/A')}
                """)

            st.markdown(f"""
            **输出**: {info.get('输出', 'N/A')}
            """)

    st.markdown("---")

    # 工具注册日志
    st.markdown("### 📜 工具注册日志")

    logs = [
        {"时间": "2026-04-03 18:46:00", "工具": "StockDataTool", "操作": "注册", "状态": "✅ 成功"},
        {"时间": "2026-04-03 18:46:01", "工具": "TechnicalAnalysisTool", "操作": "注册", "状态": "✅ 成功"},
        {"时间": "2026-04-03 18:46:02", "工具": "NewsSearchTool", "操作": "注册", "状态": "✅ 成功"},
        {"时间": "2026-04-03 18:46:03", "工具": "SocialMediaTool", "操作": "注册", "状态": "✅ 成功"},
        {"时间": "2026-04-03 18:46:04", "工具": "RiskCalcTool", "操作": "注册", "状态": "✅ 成功"},
        {"时间": "2026-04-03 18:46:05", "工具": "TradeExecuteTool", "操作": "注册", "状态": "✅ 成功"},
        {"时间": "2026-04-03 18:46:06", "工具": "PortfolioTool", "操作": "注册", "状态": "✅ 成功"},
        {"时间": "2026-04-03 18:46:07", "工具": "BacktestTool", "操作": "注册", "状态": "✅ 成功"},
    ]

    st.table(logs)
