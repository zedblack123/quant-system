"""
贾维斯量化系统 v3.0
基于Claude Code架构的量化投资系统

版本: 3.0.0
作者: 贾维斯团队
日期: 2026-04-03
"""

__version__ = "3.0.0"
__author__ = "JARVIS Team"

from .core.features import FeatureFlags
from .core.analytics import AnalyticsTracker
from .core.permissions import PermissionChecker
from .core.router import ModelRouter
from .tools.registry import ToolRegistry
from .hooks.manager import HookManager
from .agents.coordinator import MultiAgentCoordinator

__all__ = [
    'FeatureFlags',
    'AnalyticsTracker',
    'PermissionChecker',
    'ModelRouter',
    'ToolRegistry',
    'HookManager',
    'MultiAgentCoordinator'
]