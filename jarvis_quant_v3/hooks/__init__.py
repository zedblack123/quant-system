"""
钩子系统模块
"""

from .manager import HookManager
from .builtins import (
    risk_check_hook,
    permission_check_hook,
    trade_log_hook,
    performance_track_hook
)

__all__ = [
    'HookManager',
    'risk_check_hook',
    'permission_check_hook',
    'trade_log_hook',
    'performance_track_hook',
]
