"""
上下文压缩器 (ContextCompactor)
用于压缩和优化上下文数据，减少内存占用和传输开销
"""

import json
import zlib
import pickle
from typing import Dict, Any, Optional, Union
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContextCompactor:
    """
    上下文压缩器类
    提供多种压缩和优化策略
    """
    
    def __init__(self, compression_level: int = 6):
        """
        初始化压缩器
        
        Args:
            compression_level: 压缩级别 (0-9, 0=不压缩, 9=最大压缩)
        """
        self.compression_level = compression_level
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(hours=1)  # 缓存有效期1小时
        
    def compact(self, context: Dict[str, Any], strategy: str = 'smart') -> Dict[str, Any]:
        """
        压缩上下文数据
        
        Args:
            context: 原始上下文数据
            strategy: 压缩策略 ('smart', 'aggressive', 'conservative')
            
        Returns:
            压缩后的上下文数据
        """
        if not context:
            return {}
        
        start_size = self._estimate_size(context)
        logger.debug(f"压缩前上下文大小: {start_size} bytes")
        
        compacted = context.copy()
        
        if strategy == 'aggressive':
            compacted = self._aggressive_compact(compacted)
        elif strategy == 'conservative':
            compacted = self._conservative_compact(compacted)
        else:  # smart
            compacted = self._smart_compact(compacted)
        
        end_size = self._estimate_size(compacted)
        compression_ratio = (1 - end_size / start_size) * 100 if start_size > 0 else 0
        
        logger.debug(f"压缩后上下文大小: {end_size} bytes, 压缩率: {compression_ratio:.1f}%")
        
        # 添加压缩元数据
        compacted['_compaction_meta'] = {
            'original_size': start_size,
            'compacted_size': end_size,
            'compression_ratio': compression_ratio,
            'strategy': strategy,
            'timestamp': datetime.now().isoformat()
        }
        
        return compacted
    
    def decompact(self, compacted_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        解压缩上下文数据
        
        Args:
            compacted_context: 压缩后的上下文数据
            
        Returns:
            解压缩后的上下文数据
        """
        if not compacted_context:
            return {}
        
        # 移除压缩元数据
        decompacted = compacted_context.copy()
        decompacted.pop('_compaction_meta', None)
        
        # 这里可以添加解压缩逻辑
        # 例如：恢复被压缩的数据结构
        
        return decompacted
    
    def compress_binary(self, data: bytes) -> bytes:
        """
        二进制压缩
        
        Args:
            data: 原始二进制数据
            
        Returns:
            压缩后的二进制数据
        """
        return zlib.compress(data, level=self.compression_level)
    
    def decompress_binary(self, compressed_data: bytes) -> bytes:
        """
        二进制解压缩
        
        Args:
            compressed_data: 压缩后的二进制数据
            
        Returns:
            解压缩后的二进制数据
        """
        return zlib.decompress(compressed_data)
    
    def serialize(self, context: Dict[str, Any]) -> bytes:
        """
        序列化上下文数据
        
        Args:
            context: 上下文数据
            
        Returns:
            序列化后的字节数据
        """
        # 先压缩再序列化
        compacted = self.compact(context)
        return pickle.dumps(compacted)
    
    def deserialize(self, serialized_data: bytes) -> Dict[str, Any]:
        """
        反序列化上下文数据
        
        Args:
            serialized_data: 序列化后的字节数据
            
        Returns:
            反序列化后的上下文数据
        """
        context = pickle.loads(serialized_data)
        return self.decompact(context)
    
    def cache_context(self, key: str, context: Dict[str, Any]) -> None:
        """
        缓存上下文数据
        
        Args:
            key: 缓存键
            context: 上下文数据
        """
        self.cache[key] = {
            'data': context,
            'timestamp': datetime.now()
        }
        
        # 清理过期缓存
        self._cleanup_cache()
    
    def get_cached_context(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的上下文数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的上下文数据，如果不存在或过期则返回None
        """
        if key not in self.cache:
            return None
        
        cache_entry = self.cache[key]
        cache_age = datetime.now() - cache_entry['timestamp']
        
        if cache_age > self.cache_ttl:
            # 缓存过期，删除
            del self.cache[key]
            return None
        
        return cache_entry['data']
    
    def _smart_compact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """智能压缩策略"""
        compacted = {}
        
        for key, value in context.items():
            # 跳过内部字段
            if key.startswith('_'):
                continue
            
            # 根据数据类型选择压缩策略
            if isinstance(value, dict):
                if len(value) > 10:  # 大字典进行压缩
                    compacted[key] = self._compress_dict(value)
                else:
                    compacted[key] = value
            elif isinstance(value, list):
                if len(value) > 20:  # 大列表进行压缩
                    compacted[key] = self._compress_list(value)
                else:
                    compacted[key] = value
            elif isinstance(value, str) and len(value) > 100:
                # 长字符串进行压缩
                compacted[key] = self._compress_string(value)
            else:
                compacted[key] = value
        
        return compacted
    
    def _aggressive_compact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """激进压缩策略"""
        compacted = {}
        
        for key, value in context.items():
            if key.startswith('_'):
                continue
            
            if isinstance(value, (dict, list)):
                # 所有字典和列表都压缩
                serialized = json.dumps(value).encode('utf-8')
                compressed = self.compress_binary(serialized)
                compacted[key] = {
                    '_compressed': True,
                    'data': compressed.hex()
                }
            elif isinstance(value, str) and len(value) > 50:
                compressed = self.compress_binary(value.encode('utf-8'))
                compacted[key] = {
                    '_compressed': True,
                    'data': compressed.hex()
                }
            else:
                compacted[key] = value
        
        return compacted
    
    def _conservative_compact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """保守压缩策略"""
        # 只移除明显冗余的数据
        compacted = context.copy()
        
        # 移除空值
        keys_to_remove = []
        for key, value in compacted.items():
            if value is None or value == '':
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del compacted[key]
        
        return compacted
    
    def _compress_dict(self, data: Dict) -> Dict:
        """压缩字典"""
        # 这里可以实现更复杂的字典压缩逻辑
        return data
    
    def _compress_list(self, data: list) -> list:
        """压缩列表"""
        # 这里可以实现更复杂的列表压缩逻辑
        return data
    
    def _compress_string(self, data: str) -> str:
        """压缩字符串"""
        # 简单的字符串截断
        if len(data) > 500:
            return data[:500] + '... [截断]'
        return data
    
    def _estimate_size(self, data: Any) -> int:
        """估算数据大小"""
        try:
            serialized = json.dumps(data)
            return len(serialized.encode('utf-8'))
        except:
            # 如果无法JSON序列化，使用pickle估算
            try:
                return len(pickle.dumps(data))
            except:
                return 0
    
    def _cleanup_cache(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            cache_age = now - entry['timestamp']
            if cache_age > self.cache_ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        if keys_to_remove:
            logger.debug(f"清理了 {len(keys_to_remove)} 个过期缓存")


# 全局压缩器实例
context_compactor = ContextCompactor()