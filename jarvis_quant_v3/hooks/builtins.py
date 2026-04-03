"""
预置钩子函数
包含系统内置的常用钩子实现
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from .manager import HookStage

logger = logging.getLogger(__name__)


def risk_check_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    风险检查钩子 - 在决策前检查风险
    
    Args:
        context: 上下文数据
        
    Returns:
        更新后的上下文数据
    """
    logger.info("执行风险检查钩子")
    
    # 检查必要的风险参数
    required_risk_params = ['max_drawdown', 'position_size', 'stop_loss']
    missing_params = [p for p in required_risk_params if p not in context]
    
    if missing_params:
        logger.warning(f"风险参数缺失: {missing_params}")
        context['risk_check_passed'] = False
        context['risk_check_message'] = f"缺失风险参数: {missing_params}"
        return context
    
    # 执行风险检查逻辑
    max_drawdown = context.get('max_drawdown', 0.1)  # 默认最大回撤10%
    position_size = context.get('position_size', 0.0)
    stop_loss = context.get('stop_loss', 0.0)
    
    # 简单的风险检查规则
    risk_passed = True
    risk_messages = []
    
    # 检查仓位大小
    if position_size > 0.3:  # 单笔交易不超过总资金的30%
        risk_passed = False
        risk_messages.append(f"仓位过大: {position_size:.2%}")
    
    # 检查止损设置
    if stop_loss > 0.1:  # 止损不超过10%
        risk_passed = False
        risk_messages.append(f"止损过大: {stop_loss:.2%}")
    
    # 检查最大回撤
    if max_drawdown > 0.2:  # 最大回撤不超过20%
        risk_passed = False
        risk_messages.append(f"最大回撤过大: {max_drawdown:.2%}")
    
    context['risk_check_passed'] = risk_passed
    context['risk_check_messages'] = risk_messages
    
    if not risk_passed:
        logger.warning(f"风险检查未通过: {risk_messages}")
    else:
        logger.info("风险检查通过")
    
    return context


def permission_check_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    权限检查钩子 - 检查操作权限
    
    Args:
        context: 上下文数据
        
    Returns:
        更新后的上下文数据
    """
    logger.info("执行权限检查钩子")
    
    # 获取用户权限级别
    user_permission = context.get('user_permission', 1)  # 默认低权限
    required_permission = context.get('required_permission', 1)
    
    # 检查权限
    permission_passed = user_permission >= required_permission
    
    context['permission_check_passed'] = permission_passed
    context['permission_check_details'] = {
        'user_permission': user_permission,
        'required_permission': required_permission,
        'passed': permission_passed
    }
    
    if not permission_passed:
        logger.warning(f"权限检查未通过: 用户权限{user_permission} < 所需权限{required_permission}")
    else:
        logger.info(f"权限检查通过: 用户权限{user_permission} >= 所需权限{required_permission}")
    
    return context


def trade_log_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    交易日志钩子 - 记录交易信息
    
    Args:
        context: 上下文数据
        
    Returns:
        更新后的上下文数据
    """
    logger.info("执行交易日志钩子")
    
    # 提取交易信息
    trade_info = {
        'timestamp': datetime.now().isoformat(),
        'symbol': context.get('symbol', '未知'),
        'action': context.get('action', '未知'),
        'quantity': context.get('quantity', 0),
        'price': context.get('price', 0.0),
        'total_value': context.get('total_value', 0.0),
        'commission': context.get('commission', 0.0),
        'user_id': context.get('user_id', '未知'),
        'strategy': context.get('strategy', '未知'),
        'risk_level': context.get('risk_level', '中等')
    }
    
    # 记录到上下文
    if 'trade_logs' not in context:
        context['trade_logs'] = []
    
    context['trade_logs'].append(trade_info)
    
    # 记录到文件（实际项目中应该使用数据库）
    try:
        log_entry = json.dumps(trade_info, ensure_ascii=False)
        logger.info(f"交易记录: {log_entry}")
        
        # 这里可以添加文件写入逻辑
        # with open('trade_log.json', 'a') as f:
        #     f.write(log_entry + '\n')
            
    except Exception as e:
        logger.error(f"交易日志记录失败: {e}")
    
    return context


def performance_track_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    性能跟踪钩子 - 跟踪系统性能指标
    
    Args:
        context: 上下文数据
        
    Returns:
        更新后的上下文数据
    """
    logger.info("执行性能跟踪钩子")
    
    # 初始化性能跟踪数据
    if 'performance_metrics' not in context:
        context['performance_metrics'] = {
            'start_time': datetime.now().isoformat(),
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }
    
    metrics = context['performance_metrics']
    
    # 更新交易统计
    trade_result = context.get('trade_result', {})
    if trade_result:
        metrics['total_trades'] += 1
        
        if trade_result.get('success', False):
            metrics['successful_trades'] += 1
            pnl = trade_result.get('pnl', 0.0)
            metrics['total_pnl'] += pnl
            metrics['max_profit'] = max(metrics['max_profit'], pnl)
        else:
            metrics['failed_trades'] += 1
            loss = abs(trade_result.get('pnl', 0.0))
            metrics['max_loss'] = max(metrics['max_loss'], loss)
    
    # 计算胜率
    if metrics['total_trades'] > 0:
        metrics['win_rate'] = metrics['successful_trades'] / metrics['total_trades']
    
    # 记录性能指标
    context['performance_metrics'] = metrics
    
    # 记录性能快照
    if 'performance_snapshots' not in context:
        context['performance_snapshots'] = []
    
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics.copy()
    }
    context['performance_snapshots'].append(snapshot)
    
    logger.info(f"性能指标更新: 总交易{metrics['total_trades']}, 胜率{metrics['win_rate']:.2%}")
    
    return context


def error_handling_hook(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    错误处理钩子 - 处理系统错误
    
    Args:
        context: 上下文数据
        
    Returns:
        更新后的上下文数据
    """
    logger.error("执行错误处理钩子")
    
    error_info = {
        'timestamp': datetime.now().isoformat(),
        'stage': context.get('stage', '未知'),
        'error': context.get('error', '未知错误'),
        'original_context': context.get('original_context', {}),
        'current_context': context.get('current_context', {})
    }
    
    # 记录错误日志
    logger.error(f"系统错误: {json.dumps(error_info, ensure_ascii=False)}")
    
    # 发送警报（这里可以集成邮件、钉钉等通知）
    # send_alert(f"量化系统错误: {error_info['error']}")
    
    # 尝试恢复或回滚
    recovery_successful = False
    try:
        # 这里可以添加恢复逻辑
        # 例如：回滚交易、重置状态等
        recovery_successful = True
    except Exception as e:
        logger.error(f"错误恢复失败: {e}")
    
    context['error_handled'] = True
    context['error_recovery_successful'] = recovery_successful
    context['error_details'] = error_info
    
    return context


# 导出所有预置钩子
__all__ = [
    'risk_check_hook',
    'permission_check_hook',
    'trade_log_hook',
    'performance_track_hook',
    'error_handling_hook'
]