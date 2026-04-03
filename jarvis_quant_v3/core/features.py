"""
功能标志管理器 (FeatureFlags)
用于管理系统的功能开关和实验性功能
"""

import json
import yaml
from typing import Dict, Any, List, Set, Optional
from enum import Enum
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """功能状态枚举"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"
    BETA = "beta"
    ALPHA = "alpha"


class FeatureFlag:
    """
    功能标志类
    表示一个具体的功能开关
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        status: FeatureStatus = FeatureStatus.DISABLED,
        enabled_for: Optional[List[str]] = None,
        disabled_for: Optional[List[str]] = None,
        rollout_percentage: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        初始化功能标志
        
        Args:
            name: 功能名称
            description: 功能描述
            status: 功能状态
            enabled_for: 对哪些用户/组启用
            disabled_for: 对哪些用户/组禁用
            rollout_percentage: 灰度发布百分比 (0-100)
            start_time: 功能开始时间
            end_time: 功能结束时间
            metadata: 额外元数据
        """
        self.name = name
        self.description = description
        self.status = status
        self.enabled_for = set(enabled_for or [])
        self.disabled_for = set(disabled_for or [])
        self.rollout_percentage = max(0, min(100, rollout_percentage))
        self.start_time = start_time
        self.end_time = end_time
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def is_enabled(self, user_id: Optional[str] = None) -> bool:
        """
        检查功能是否对指定用户启用
        
        Args:
            user_id: 用户ID，如果为None则检查全局状态
            
        Returns:
            是否启用
        """
        # 检查时间范围
        now = datetime.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        
        # 检查用户特定设置
        if user_id:
            # 检查显式禁用
            if user_id in self.disabled_for:
                return False
            
            # 检查显式启用
            if user_id in self.enabled_for:
                return True
            
            # 检查灰度发布
            if self.rollout_percentage > 0:
                # 简单的基于用户ID的哈希算法
                import hashlib
                user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
                return user_hash < self.rollout_percentage
        
        # 检查全局状态
        return self.status in [FeatureStatus.ENABLED, FeatureStatus.BETA, FeatureStatus.ALPHA]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'enabled_for': list(self.enabled_for),
            'disabled_for': list(self.disabled_for),
            'rollout_percentage': self.rollout_percentage,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlag':
        """从字典创建"""
        # 解析时间字段
        start_time = None
        if data.get('start_time'):
            start_time = datetime.fromisoformat(data['start_time'])
        
        end_time = None
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time'])
        
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        
        flag = cls(
            name=data['name'],
            description=data.get('description', ''),
            status=FeatureStatus(data['status']),
            enabled_for=data.get('enabled_for', []),
            disabled_for=data.get('disabled_for', []),
            rollout_percentage=data.get('rollout_percentage', 0),
            start_time=start_time,
            end_time=end_time,
            metadata=data.get('metadata', {})
        )
        
        flag.created_at = created_at
        flag.updated_at = updated_at
        
        return flag


class FeatureFlags:
    """
    功能标志管理器
    管理所有功能开关
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化功能标志管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.flags: Dict[str, FeatureFlag] = {}
        self.config_file = config_file
        
        # 加载默认功能
        self._load_default_flags()
        
        # 从配置文件加载
        if config_file:
            self.load_from_file(config_file)
    
    def register(self, flag: FeatureFlag) -> None:
        """
        注册功能标志
        
        Args:
            flag: 功能标志
        """
        self.flags[flag.name] = flag
        logger.info(f"注册功能标志: {flag.name} ({flag.status.value})")
    
    def is_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """
        检查功能是否启用
        
        Args:
            feature_name: 功能名称
            user_id: 用户ID
            
        Returns:
            是否启用
        """
        if feature_name not in self.flags:
            logger.warning(f"未知的功能标志: {feature_name}")
            return False
        
        flag = self.flags[feature_name]
        return flag.is_enabled(user_id)
    
    def enable(self, feature_name: str, user_id: Optional[str] = None) -> None:
        """
        启用功能
        
        Args:
            feature_name: 功能名称
            user_id: 用户ID，如果为None则全局启用
        """
        if feature_name not in self.flags:
            logger.warning(f"未知的功能标志: {feature_name}")
            return
        
        flag = self.flags[feature_name]
        
        if user_id:
            # 为用户启用
            flag.enabled_for.add(user_id)
            flag.disabled_for.discard(user_id)
            logger.info(f"为用户 {user_id} 启用功能: {feature_name}")
        else:
            # 全局启用
            flag.status = FeatureStatus.ENABLED
            logger.info(f"全局启用功能: {feature_name}")
        
        flag.updated_at = datetime.now()
    
    def disable(self, feature_name: str, user_id: Optional[str] = None) -> None:
        """
        禁用功能
        
        Args:
            feature_name: 功能名称
            user_id: 用户ID，如果为None则全局禁用
        """
        if feature_name not in self.flags:
            logger.warning(f"未知的功能标志: {feature_name}")
            return
        
        flag = self.flags[feature_name]
        
        if user_id:
            # 为用户禁用
            flag.disabled_for.add(user_id)
            flag.enabled_for.discard(user_id)
            logger.info(f"为用户 {user_id} 禁用功能: {feature_name}")
        else:
            # 全局禁用
            flag.status = FeatureStatus.DISABLED
            logger.info(f"全局禁用功能: {feature_name}")
        
        flag.updated_at = datetime.now()
    
    def set_rollout(self, feature_name: str, percentage: int) -> None:
        """
        设置灰度发布百分比
        
        Args:
            feature_name: 功能名称
            percentage: 灰度百分比 (0-100)
        """
        if feature_name not in self.flags:
            logger.warning(f"未知的功能标志: {feature_name}")
            return
        
        flag = self.flags[feature_name]
        flag.rollout_percentage = max(0, min(100, percentage))
        flag.updated_at = datetime.now()
        
        logger.info(f"设置功能 {feature_name} 灰度发布: {percentage}%")
    
    def get_flag(self, feature_name: str) -> Optional[FeatureFlag]:
        """获取功能标志"""
        return self.flags.get(feature_name)
    
    def list_flags(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        列出所有功能标志
        
        Args:
            user_id: 用户ID，用于检查每个功能的启用状态
            
        Returns:
            功能标志字典
        """
        result = {}
        for name, flag in self.flags.items():
            flag_dict = flag.to_dict()
            flag_dict['enabled_for_user'] = flag.is_enabled(user_id) if user_id else None
            result[name] = flag_dict
        
        return result
    
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
            'flags': {name: flag.to_dict() for name, flag in self.flags.items()}
        }
        
        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"功能标志已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存功能标志失败: {e}")
    
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
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # 加载功能标志
            if 'flags' in data:
                for name, flag_data in data['flags'].items():
                    try:
                        flag = FeatureFlag.from_dict(flag_data)
                        self.flags[name] = flag
                    except Exception as e:
                        logger.error(f"加载功能标志 {name} 失败: {e}")
            
            logger.info(f"从 {file_path} 加载了 {len(self.flags)} 个功能标志")
            
        except Exception as e:
            logger.error(f"加载功能标志文件失败: {e}")
    
    def _load_default_flags(self) -> None:
        """加载默认功能标志"""
        default_flags = [
            FeatureFlag(
                name="advanced_technical_analysis",
                description="高级技术分析功能",
                status=FeatureStatus.ENABLED
            ),
            FeatureFlag(
                name="ai_sentiment_analysis",
                description="AI情感分析",
                status=FeatureStatus.EXPERIMENTAL,
                rollout_percentage=50
            ),
            FeatureFlag(
                name="real_time_trading",
                description="实时交易功能",
                status=FeatureStatus.BETA,
                enabled_for=["admin", "trader1"]
            ),
            FeatureFlag(
                name="multi_agent_coordination",
                description="多智能体协同",
                status=FeatureStatus.ALPHA
            ),
            FeatureFlag(
                name="risk_management_dashboard",
                description="风险管理仪表板",
                status=FeatureStatus.ENABLED
            ),
            FeatureFlag(
                name="performance_analytics",
                description="性能分析功能",
                status=FeatureStatus.ENABLED
            ),
            FeatureFlag(
                name="automated_reporting",
                description="自动报告生成",
                status=FeatureStatus.EXPERIMENTAL,
                rollout_percentage=30
            )
        ]
        
        for flag in default_flags:
            self.register(flag)
        
        logger.info(f"加载了 {len(default_flags)} 个默认功能标志")


# 全局功能标志管理器实例
feature_flags = FeatureFlags()