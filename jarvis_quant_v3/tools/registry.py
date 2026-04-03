"""
工具注册表
单例模式管理所有工具
"""

import threading
from typing import Dict, List, Optional, Type, Any
from .base import BaseTool, PermissionLevel


class ToolRegistry:
    """工具注册表（单例）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化工具注册表"""
        if not self._initialized:
            self._tools: Dict[str, BaseTool] = {}
            self._tool_classes: Dict[str, Type[BaseTool]] = {}
            self._initialized = True
    
    def register(self, tool: BaseTool) -> None:
        """
        注册工具实例
        
        Args:
            tool: 工具实例
        """
        if tool.name in self._tools:
            raise ValueError(f"工具 '{tool.name}' 已注册")
        
        self._tools[tool.name] = tool
        print(f"✅ 工具注册成功: {tool.name} v{tool.version}")
    
    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """
        注册工具类
        
        Args:
            tool_class: 工具类
        """
        tool_name = tool_class.__name__
        if tool_name in self._tool_classes:
            raise ValueError(f"工具类 '{tool_name}' 已注册")
        
        self._tool_classes[tool_name] = tool_class
        print(f"✅ 工具类注册成功: {tool_name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例或None
        """
        return self._tools.get(name)
    
    def get_tool_class(self, name: str) -> Optional[Type[BaseTool]]:
        """
        获取工具类
        
        Args:
            name: 工具类名称
            
        Returns:
            工具类或None
        """
        return self._tool_classes.get(name)
    
    def create_tool(self, tool_class_name: str, **kwargs) -> BaseTool:
        """
        创建工具实例
        
        Args:
            tool_class_name: 工具类名称
            **kwargs: 工具初始化参数
            
        Returns:
            工具实例
        """
        tool_class = self.get_tool_class(tool_class_name)
        if not tool_class:
            raise ValueError(f"工具类 '{tool_class_name}' 未注册")
        
        return tool_class(**kwargs)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册工具
        
        Returns:
            工具信息列表
        """
        tools_info = []
        for name, tool in self._tools.items():
            schema = tool.get_schema()
            tools_info.append({
                "name": name,
                "description": tool.description,
                "version": tool.version,
                "permission_level": tool.get_permission_level().name,
                "tags": schema.tags
            })
        
        return tools_info
    
    def list_tool_classes(self) -> List[str]:
        """
        列出所有已注册工具类
        
        Returns:
            工具类名称列表
        """
        return list(self._tool_classes.keys())
    
    def get_tools_by_permission(self, level: PermissionLevel) -> List[BaseTool]:
        """
        根据权限级别获取工具
        
        Args:
            level: 权限级别
            
        Returns:
            工具列表
        """
        return [
            tool for tool in self._tools.values()
            if tool.get_permission_level().value <= level.value
        ]
    
    def get_tools_by_tag(self, tag: str) -> List[BaseTool]:
        """
        根据标签获取工具
        
        Args:
            tag: 标签
            
        Returns:
            工具列表
        """
        return [
            tool for tool in self._tools.values()
            if tag in tool.get_schema().tags
        ]
    
    def unregister(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            print(f"🗑️ 工具注销成功: {name}")
            return True
        return False
    
    def unregister_class(self, name: str) -> bool:
        """
        注销工具类
        
        Args:
            name: 工具类名称
            
        Returns:
            是否成功注销
        """
        if name in self._tool_classes:
            del self._tool_classes[name]
            print(f"🗑️ 工具类注销成功: {name}")
            return True
        return False
    
    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        self._tool_classes.clear()
        print("🧹 所有工具已清空")
    
    @property
    def tool_count(self) -> int:
        """获取工具数量"""
        return len(self._tools)
    
    @property
    def tool_class_count(self) -> int:
        """获取工具类数量"""
        return len(self._tool_classes)
    
    def __contains__(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools
    
    def __len__(self) -> int:
        """获取工具数量"""
        return len(self._tools)
    
    def __str__(self) -> str:
        """注册表字符串表示"""
        return f"ToolRegistry({self.tool_count} tools, {self.tool_class_count} classes)"
    
    def __repr__(self) -> str:
        """注册表表示"""
        return f"<ToolRegistry tools={self.tool_count} classes={self.tool_class_count}>"