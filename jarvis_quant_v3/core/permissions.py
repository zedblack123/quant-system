"""
权限管理系统 (PermissionChecker)
用于管理用户权限和多级确认机制
"""

import json
from enum import IntEnum
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PermissionLevel(IntEnum):
    """权限级别枚举"""
    LOW = 1      # 低权限：只能查看基本数据
    MEDIUM = 2   # 中权限：可以执行分析，不能交易
    HIGH = 3     # 高权限：可以执行交易
    ADMIN = 4    # 管理员：可以修改系统设置


@dataclass
class UserPermission:
    """用户权限数据类"""
    user_id: str
    username: str
    permission_level: PermissionLevel
    roles: Set[str] = field(default_factory=set)
    allowed_actions: Set[str] = field(default_factory=set)
    denied_actions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, required_level: PermissionLevel) -> bool:
        """检查是否有足够权限级别"""
        return self.permission_level >= required_level
    
    def can_perform(self, action: str) -> bool:
        """检查是否可以执行特定操作"""
        # 检查显式拒绝
        if action in self.denied_actions:
            return False
        
        # 检查显式允许
        if action in self.allowed_actions:
            return True
        
        # 根据权限级别检查
        if self.permission_level >= PermissionLevel.HIGH:
            # 高权限用户默认可以执行所有操作
            return True
        elif self.permission_level >= PermissionLevel.MEDIUM:
            # 中权限用户只能执行非交易操作
            non_trading_actions = {'view_data', 'run_analysis', 'generate_report'}
            return action in non_trading_actions
        else:
            # 低权限用户只能查看
            view_only_actions = {'view_data', 'view_reports'}
            return action in view_only_actions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'permission_level': self.permission_level.value,
            'roles': list(self.roles),
            'allowed_actions': list(self.allowed_actions),
            'denied_actions': list(self.denied_actions),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPermission':
        """从字典创建"""
        user = cls(
            user_id=data['user_id'],
            username=data['username'],
            permission_level=PermissionLevel(data['permission_level']),
            roles=set(data.get('roles', [])),
            allowed_actions=set(data.get('allowed_actions', [])),
            denied_actions=set(data.get('denied_actions', []))
        )
        
        if 'created_at' in data:
            user.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            user.updated_at = datetime.fromisoformat(data['updated_at'])
        
        return user


@dataclass
class ConfirmationRequest:
    """确认请求数据类"""
    request_id: str
    action: str
    user_id: str
    required_approvers: List[str]
    approvals: Dict[str, bool] = field(default_factory=dict)
    rejections: Dict[str, bool] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    status: str = "pending"  # pending, approved, rejected, expired
    
    def approve(self, user_id: str) -> bool:
        """用户批准"""
        if user_id not in self.required_approvers:
            logger.warning(f"用户 {user_id} 不是要求的批准者")
            return False
        
        self.approvals[user_id] = True
        self._update_status()
        
        logger.info(f"用户 {user_id} 批准了请求 {self.request_id}")
        return True
    
    def reject(self, user_id: str) -> bool:
        """用户拒绝"""
        if user_id not in self.required_approvers:
            logger.warning(f"用户 {user_id} 不是要求的批准者")
            return False
        
        self.rejections[user_id] = True
        self._update_status()
        
        logger.info(f"用户 {user_id} 拒绝了请求 {self.request_id}")
        return True
    
    def _update_status(self) -> None:
        """更新请求状态"""
        now = datetime.now()
        
        # 检查是否过期
        if now > self.expires_at:
            self.status = "expired"
            return
        
        # 检查是否被拒绝
        if self.rejections:
            self.status = "rejected"
            return
        
        # 检查是否已批准
        approved_count = len(self.approvals)
        required_count = len(self.required_approvers)
        
        if approved_count >= required_count:
            self.status = "approved"
        else:
            self.status = "pending"
    
    def is_approved(self) -> bool:
        """检查是否已批准"""
        return self.status == "approved"
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        return datetime.now() > self.expires_at
    
    def get_approval_progress(self) -> Tuple[int, int]:
        """获取批准进度"""
        approved = len(self.approvals)
        required = len(self.required_approvers)
        return approved, required
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'request_id': self.request_id,
            'action': self.action,
            'user_id': self.user_id,
            'required_approvers': self.required_approvers,
            'approvals': self.approvals,
            'rejections': self.rejections,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'status': self.status
        }


class PermissionChecker:
    """
    权限检查器
    管理用户权限和多级确认
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化权限检查器
        
        Args:
            config_file: 配置文件路径
        """
        self.users: Dict[str, UserPermission] = {}
        self.confirmation_requests: Dict[str, ConfirmationRequest] = {}
        self.config_file = config_file
        
        # 加载默认用户
        self._load_default_users()
        
        # 从配置文件加载
        if config_file:
            self.load_from_file(config_file)
    
    def register_user(self, user: UserPermission) -> None:
        """
        注册用户
        
        Args:
            user: 用户权限对象
        """
        self.users[user.user_id] = user
        logger.info(f"注册用户: {user.username} (权限级别: {user.permission_level.name})")
    
    def check(
        self,
        user_id: str,
        action: str,
        required_level: Optional[PermissionLevel] = None
    ) -> Dict[str, Any]:
        """
        检查用户权限
        
        Args:
            user_id: 用户ID
            action: 要执行的操作
            required_level: 要求的权限级别，如果为None则根据action自动判断
            
        Returns:
            检查结果字典
        """
        if user_id not in self.users:
            logger.warning(f"未知用户: {user_id}")
            return {
                'allowed': False,
                'reason': f"用户 {user_id} 不存在",
                'user_id': user_id,
                'action': action
            }
        
        user = self.users[user_id]
        
        # 确定要求的权限级别
        if required_level is None:
            required_level = self._get_required_level_for_action(action)
        
        # 检查权限级别
        if not user.has_permission(required_level):
            return {
                'allowed': False,
                'reason': f"权限不足: 需要 {required_level.name}, 当前 {user.permission_level.name}",
                'user_id': user_id,
                'action': action,
                'required_level': required_level.value,
                'user_level': user.permission_level.value
            }
        
        # 检查具体操作权限
        if not user.can_perform(action):
            return {
                'allowed': False,
                'reason': f"不允许执行操作: {action}",
                'user_id': user_id,
                'action': action
            }
        
        return {
            'allowed': True,
            'user_id': user_id,
            'action': action,
            'permission_level': user.permission_level.value
        }
    
    def require_multi_confirmation(
        self,
        action: str,
        user_id: str,
        required_approvers: List[str],
        context: Optional[Dict[str, Any]] = None,
        expiry_hours: int = 24
    ) -> ConfirmationRequest:
        """
        要求多级确认
        
        Args:
            action: 要确认的操作
            user_id: 发起请求的用户ID
            required_approvers: 需要的批准者列表
            context: 上下文信息
            expiry_hours: 过期时间（小时）
            
        Returns:
            确认请求对象
        """
        # 生成请求ID
        import uuid
        request_id = f"confirm_{uuid.uuid4().hex[:8]}"
        
        # 创建确认请求
        request = ConfirmationRequest(
            request_id=request_id,
            action=action,
            user_id=user_id,
            required_approvers=required_approvers,
            context=context or {},
            expires_at=datetime.now() + timedelta(hours=expiry_hours)
        )
        
        self.confirmation_requests[request_id] = request
        
        logger.info(f"创建多级确认请求: {request_id}, 操作: {action}, 需要批准者: {required_approvers}")
        
        return request
    
    def process_confirmation(
        self,
        request_id: str,
        approver_id: str,
        approve: bool
    ) -> Dict[str, Any]:
        """
        处理确认请求
        
        Args:
            request_id: 请求ID
            approver_id: 批准者ID
            approve: True表示批准，False表示拒绝
            
        Returns:
            处理结果
        """
        if request_id not in self.confirmation_requests:
            return {
                'success': False,
                'error': f"确认请求不存在: {request_id}"
            }
        
        request = self.confirmation_requests[request_id]
        
        # 检查是否过期
        if request.is_expired():
            request.status = "expired"
            return {
                'success': False,
                'error': "确认请求已过期",
                'request_id': request_id,
                'status': 'expired'
            }
        
        # 处理批准/拒绝
        if approve:
            success = request.approve(approver_id)
        else:
            success = request.reject(approver_id)
        
        if not success:
            return {
                'success': False,
                'error': f"用户 {approver_id} 不是要求的批准者"
            }
        
        # 获取当前进度
        approved, required = request.get_approval_progress()
        
        result = {
            'success': True,
            'request_id': request_id,
            'action': request.action,
            'approver_id': approver_id,
            'approved': approve,
            'current_approvals': approved,
            'required_approvals': required,
            'status': request.status
        }
        
        # 如果请求已完成，清理过期的请求
        if request.status in ['approved', 'rejected', 'expired']:
            self._cleanup_expired_requests()
        
        return result
    
    def get_confirmation_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        获取确认请求状态
        
        Args:
            request_id: 请求ID
            
        Returns:
            请求状态信息，如果不存在则返回None
        """
        if request_id not in self.confirmation_requests:
            return None
        
        request = self.confirmation_requests[request_id]
        
        approved, required = request.get_approval_progress()
        
        return {
            'request_id': request_id,
            'action': request.action,
            'user_id': request.user_id,
            'required_approvers': request.required_approvers,
            'approvals': request.approvals,
            'rejections': request.rejections,
            'current_approvals': approved,
            'required_approvals': required,
            'status': request.status,
            'created_at': request.created_at.isoformat(),
            'expires_at': request.expires_at.isoformat(),
            'is_expired': request.is_expired(),
            'is_approved': request.is_approved()
        }
    
    def list_pending_confirmations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出待处理的确认请求
        
        Args:
            user_id: 用户ID，如果提供则只列出该用户需要处理的请求
            
        Returns:
            待处理请求列表
        """
        pending = []
        
        for request_id, request in self.confirmation_requests.items():
            if request.status != "pending":
                continue
            
            if user_id and user_id not in request.required_approvers:
                continue
            
            approved, required = request.get_approval_progress()
            
            pending.append({
                'request_id': request_id,
                'action': request.action,
                'user_id': request.user_id,
                'current_approvals': approved,
                'required_approvals': required,
                'created_at': request.created_at.isoformat(),
                'expires_at': request.expires_at.isoformat(),
                'needs_my_approval': user_id in request.required_approvers if user_id else False
            })
        
        return pending
    
    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """
        保存到文件
        
        Args:
            file_path: 文件路径，如果为None则使用初始化时的路径
        """
        if file_path is None:
            file_path = self.config_file
        
        if not file_path:
            logger.warning("未指定配置文件路径")
            return
        
        # 准备数据
        data = {
            'version': '1.0',
            'updated_at': datetime.now().isoformat(),
            'users': {user_id: user.to_dict() for user_id, user in self.users.items()}
        }
        
        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"权限配置已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存权限配置失败: {e}")
    
    def load_from_file(self, file_path: str) -> None:
        """
        从文件加载
        
        Args:
            file_path: 文件路径
        """
        if not Path(file_path).exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载用户
            if 'users' in data:
                for user_id, user_data in data['users'].items():
                    try:
                        user = UserPermission.from_dict(user_data)
                        self.users[user_id] = user
                    except Exception as e:
                        logger.error(f"加载用户 {user_id} 失败: {e}")
            
            logger.info(f"从 {file_path} 加载了 {len(self.users)} 个用户")
            
        except Exception as e:
            logger.error(f"加载权限配置文件失败: {e}")
    
    def _load_default_users(self) -> None:
        """加载默认用户"""
        default_users = [
            UserPermission(
                user_id="admin",
                username="系统管理员",
                permission_level=PermissionLevel.ADMIN,
                roles={"admin", "superuser"},
                allowed_actions={"*"}
            ),
            UserPermission(
                user_id="trader1",
                username="交易员1",
                permission_level=PermissionLevel.HIGH,
                roles={"trader"},
                allowed_actions={"execute_trade", "modify_strategy"}
            ),
            UserPermission(
                user_id="analyst1",
                username="分析师1",
                permission_level=PermissionLevel.MEDIUM,
                roles={"analyst"},
                allowed_actions={"run_analysis", "generate_report"}
            ),
            UserPermission(
                user_id="viewer1",
                username="查看员1",
                permission_level=PermissionLevel.LOW,
                roles={"viewer"},
                denied_actions={"execute_trade", "modify_settings"}
            )
        ]
        
        for user in default_users:
            self.register_user(user)
        
        logger.info(f"加载了 {len(default_users)} 个默认用户")
    
    def _get_required_level_for_action(self, action: str) -> PermissionLevel:
        """根据操作获取要求的权限级别"""
        # 高风险操作需要高权限
        high_risk_actions = {
            'execute_trade', 'modify_strategy', 'change_risk_parameters',
            'withdraw_funds', 'transfer_funds'
        }
        
        # 中风险操作需要中权限
        medium_risk_actions = {
            'run_analysis', 'generate_report', 'backtest_strategy',
            'export_data', 'schedule_task'
        }
        
        if action in high_risk_actions:
            return PermissionLevel.HIGH
        elif action in medium_risk_actions:
            return PermissionLevel.MEDIUM
        else:
            # 默认低权限
            return PermissionLevel.LOW
    
    def _cleanup_expired_requests(self) -> None:
        """清理过期的确认请求"""
        now = datetime.now()
        expired_ids = []
        
        for request_id, request in self.confirmation_requests.items():
            if request.is_expired() and request.status == "pending":
                request.status = "expired"
                expired_ids.append(request_id)
        
        # 移除过期的请求（保留一段时间用于审计）
        keep_expired_hours = 72  # 保留72小时
        cutoff_time = now - timedelta(hours=keep_expired_hours)
        
        to_remove = []
        for request_id, request in self.confirmation_requests.items():
            if request.status in ['expired', 'rejected'] and request.created_at < cutoff_time:
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.confirmation_requests[request_id]
        
        if expired_ids or to_remove:
            logger.info(f"清理了 {len(expired_ids)} 个过期请求和 {len(to_remove)} 个旧请求")


# 全局权限检查器实例
permission_checker = PermissionChecker()