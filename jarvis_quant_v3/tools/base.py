"""
工具基类定义
所有工具必须继承自BaseTool
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class PermissionLevel(Enum):
    """权限级别枚举"""
    LOW = 1      # 低风险操作，如数据查询
    MEDIUM = 2   # 中等风险操作，如技术分析
    HIGH = 3     # 高风险操作，如模拟交易
    ADMIN = 4    # 管理员操作，如真实交易


@dataclass
class ToolSchema:
    """工具模式定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_permission: PermissionLevel
    returns: Dict[str, Any]
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
            version: 工具版本
        """
        self.name = name
        self.description = description
        self.version = version
        self._schema = None
        
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具操作
        
        Returns:
            执行结果字典
        """
        pass
    
    @abstractmethod
    def get_permission_level(self) -> PermissionLevel:
        """
        获取工具所需权限级别
        
        Returns:
            权限级别
        """
        pass
    
    def get_schema(self) -> ToolSchema:
        """
        获取工具模式
        
        Returns:
            工具模式对象
        """
        if self._schema is None:
            self._schema = self._create_schema()
        return self._schema
    
    def _create_schema(self) -> ToolSchema:
        """
        创建工具模式
        
        Returns:
            工具模式对象
        """
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self._get_parameters_schema(),
            required_permission=self.get_permission_level(),
            returns=self._get_returns_schema(),
            version=self.version,
            tags=self._get_tags()
        )
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数模式
        
        Returns:
            参数模式字典
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def _get_returns_schema(self) -> Dict[str, Any]:
        """
        获取返回模式
        
        Returns:
            返回模式字典
        """
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "data": {"type": "object"},
                "error": {"type": "string", "optional": True}
            }
        }
    
    def _get_tags(self) -> List[str]:
        """
        获取工具标签
        
        Returns:
            标签列表
        """
        return []
    
    def validate_input(self, **kwargs) -> bool:
        """
        验证输入参数
        
        Args:
            **kwargs: 输入参数
            
        Returns:
            验证是否通过
        """
        schema = self.get_schema()
        required_params = schema.parameters.get("required", [])
        
        for param in required_params:
            if param not in kwargs:
                return False
        
        return True
    
    def __str__(self) -> str:
        """工具字符串表示"""
        return f"{self.name} v{self.version} - {self.description}"
    
    def __repr__(self) -> str:
        """工具表示"""
        return f"<BaseTool name='{self.name}' version='{self.version}'>"