"""
钩子管理器 (HookManager)
用于在量化系统的不同阶段执行预定义的钩子函数
"""

from typing import Dict, List, Callable, Any, Optional
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class HookStage(Enum):
    """钩子执行阶段枚举"""
    PRE_ANALYSIS = "pre_analysis"
    POST_ANALYSIS = "post_analysis"
    PRE_DECISION = "pre_decision"
    POST_DECISION = "post_decision"
    PRE_TRADE = "pre_trade"
    POST_TRADE = "post_trade"
    ON_ERROR = "on_error"


class HookManager:
    """
    钩子管理器类
    负责注册和执行不同阶段的钩子函数
    """
    
    def __init__(self):
        """初始化钩子管理器"""
        self._hooks: Dict[str, List[Callable]] = {
            stage.value: [] for stage in HookStage
        }
        self._context_cache: Dict[str, Any] = {}
        
    def register_hook(self, stage: str, func: Callable) -> None:
        """
        注册钩子函数
        
        Args:
            stage: 钩子阶段 (pre_analysis, post_analysis, pre_decision, post_decision, pre_trade, post_trade, on_error)
            func: 钩子函数，接收context参数并返回修改后的context或None
        """
        if stage not in self._hooks:
            raise ValueError(f"无效的钩子阶段: {stage}")
        
        self._hooks[stage].append(func)
        logger.info(f"注册钩子: {func.__name__} -> {stage}")
        
    def execute_hook(self, stage: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定阶段的所有钩子函数
        
        Args:
            stage: 钩子阶段
            context: 上下文数据字典
            
        Returns:
            更新后的上下文数据
        """
        if stage not in self._hooks:
            logger.warning(f"未知的钩子阶段: {stage}")
            return context
        
        logger.info(f"执行钩子阶段: {stage}, 钩子数量: {len(self._hooks[stage])}")
        
        # 缓存原始上下文用于错误处理
        original_context = context.copy()
        
        try:
            for hook_func in self._hooks[stage]:
                try:
                    result = hook_func(context)
                    # 如果钩子返回了新的上下文，使用它
                    if result is not None:
                        context = result
                    # 更新缓存
                    self._context_cache[stage] = context.copy()
                except Exception as e:
                    logger.error(f"钩子执行失败: {hook_func.__name__}, 错误: {e}")
                    # 继续执行其他钩子
                    continue
                    
        except Exception as e:
            logger.error(f"钩子阶段执行失败: {stage}, 错误: {e}")
            # 执行错误处理钩子
            if self._hooks[HookStage.ON_ERROR.value]:
                error_context = {
                    "original_context": original_context,
                    "current_context": context,
                    "stage": stage,
                    "error": str(e)
                }
                self.execute_hook(HookStage.ON_ERROR.value, error_context)
        
        return context
    
    def get_hook_count(self, stage: str) -> int:
        """获取指定阶段的钩子数量"""
        return len(self._hooks.get(stage, []))
    
    def clear_hooks(self, stage: Optional[str] = None) -> None:
        """
        清除钩子
        
        Args:
            stage: 指定阶段，如果为None则清除所有阶段的钩子
        """
        if stage is None:
            for stage_key in self._hooks:
                self._hooks[stage_key] = []
            logger.info("清除所有钩子")
        elif stage in self._hooks:
            self._hooks[stage] = []
            logger.info(f"清除阶段 {stage} 的钩子")
        else:
            logger.warning(f"未知的钩子阶段: {stage}")
    
    def list_hooks(self) -> Dict[str, List[str]]:
        """列出所有注册的钩子"""
        result = {}
        for stage, hooks in self._hooks.items():
            result[stage] = [func.__name__ for func in hooks]
        return result


# 全局钩子管理器实例
hook_manager = HookManager()