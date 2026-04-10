"""
贾维斯量化系统 v3.0 - Streamlit Web应用
"""

import streamlit as st
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 页面配置
st.set_page_config(
    page_title="贾维斯量化系统 v3.0",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入页面
from web.pages.home import show_home
from web.pages.analysis import show_analysis
from web.pages.tools import show_tools
from web.pages.performance import show_performance
from web.pages.settings import show_settings

# 导入样式
from web.components.styles import apply_custom_style

# 应用自定义样式
apply_custom_style()


def main():
    """主应用"""

    # 侧边栏导航
    st.sidebar.markdown("## 🤖 贾维斯量化系统")
    st.sidebar.markdown("---")

    # 导航选项
    page_options = {
        "🏠 首页": "home",
        "📊 股票分析": "analysis",
        "🔧 工具管理": "tools",
        "📈 绩效追踪": "performance",
        "⚙️ 系统设置": "settings",
    }

    selected_page = st.sidebar.radio(
        "功能导航",
        options=list(page_options.keys()),
        index=0,
        format_func=lambda x: x
    )

    st.sidebar.markdown("---")

    # 系统状态
    st.sidebar.markdown("### 系统状态")
    st.sidebar.success("✅ 系统正常运行")

    # 版权信息
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="text-align: center; color: gray; font-size: 12px;">
        🤵 贾维斯量化系统 v3.0<br>
        Powered by Claude Code Architecture
        </div>
        """,
        unsafe_allow_html=True
    )

    # 根据选择显示页面
    page_key = page_options[selected_page]

    if page_key == "home":
        show_home()
    elif page_key == "analysis":
        show_analysis()
    elif page_key == "tools":
        show_tools()
    elif page_key == "performance":
        show_performance()
    elif page_key == "settings":
        show_settings()


if __name__ == "__main__":
    main()
