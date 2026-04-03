"""
模型路由器 (ModelRouter)
根据任务类型路由到不同的AI模型
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    FINAL_DECISION = "final_decision"
    GENERAL_QUERY = "general_query"
    CODE_GENERATION = "code_generation"
    DATA_PROCESSING = "data_processing"


class ModelProvider(Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    MINIMAX = "minimax"
    LOCAL = "local"


class ModelConfig:
    """模型配置类"""
    
    def __init__(
        self,
        provider: ModelProvider,
        model_name: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        system_prompt: Optional[str] = None,
        cost_per_token: float = 0.0
    ):
        """
        初始化模型配置
        
        Args:
            provider: 模型提供商
            model_name: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            top_p: top_p参数
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
            system_prompt: 系统提示词
            cost_per_token: 每token成本（美元）
        """
        self.provider = provider
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.system_prompt = system_prompt
        self.cost_per_token = cost_per_token
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'provider': self.provider.value,
            'model_name': self.model_name,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'system_prompt': self.system_prompt,
            'cost_per_token': self.cost_per_token
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建"""
        return cls(
            provider=ModelProvider(data['provider']),
            model_name=data['model_name'],
            max_tokens=data.get('max_tokens', 4096),
            temperature=data.get('temperature', 0.7),
            top_p=data.get('top_p', 0.9),
            frequency_penalty=data.get('frequency_penalty', 0.0),
            presence_penalty=data.get('presence_penalty', 0.0),
            system_prompt=data.get('system_prompt'),
            cost_per_token=data.get('cost_per_token', 0.0)
        )


class ModelRouter:
    """
    模型路由器
    根据任务类型选择合适的AI模型
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化模型路由器
        
        Args:
            config_file: 配置文件路径
        """
        self.task_routing: Dict[TaskType, ModelConfig] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.fallback_config: Optional[ModelConfig] = None
        
        # 加载默认配置
        self._load_default_configs()
        
        # 从配置文件加载
        if config_file:
            self.load_from_file(config_file)
    
    def route(self, task_type: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        路由任务到合适的模型
        
        Args:
            task_type: 任务类型字符串
            prompt: 用户提示词
            **kwargs: 额外参数
            
        Returns:
            路由结果字典
        """
        try:
            # 解析任务类型
            task = TaskType(task_type)
        except ValueError:
            logger.warning(f"未知的任务类型: {task_type}, 使用默认路由")
            task = TaskType.GENERAL_QUERY
        
        # 获取模型配置
        model_config = self.task_routing.get(task)
        if not model_config:
            logger.warning(f"任务类型 {task.value} 没有配置模型，使用回退配置")
            model_config = self.fallback_config
        
        if not model_config:
            raise ValueError(f"没有可用的模型配置用于任务类型: {task.value}")
        
        # 准备请求参数
        request_params = self._prepare_request_params(model_config, prompt, task, **kwargs)
        
        # 记录路由决策
        routing_decision = {
            'task_type': task.value,
            'model_provider': model_config.provider.value,
            'model_name': model_config.model_name,
            'estimated_tokens': len(prompt) // 4,  # 简单估算
            'estimated_cost': (len(prompt) // 4) * model_config.cost_per_token,
            'timestamp': self._get_timestamp()
        }
        
        logger.info(f"路由决策: {task.value} -> {model_config.provider.value}/{model_config.model_name}")
        
        return {
            'success': True,
            'routing_decision': routing_decision,
            'model_config': model_config.to_dict(),
            'request_params': request_params
        }
    
    def register_task_route(self, task_type: TaskType, model_config: ModelConfig) -> None:
        """
        注册任务路由
        
        Args:
            task_type: 任务类型
            model_config: 模型配置
        """
        self.task_routing[task_type] = model_config
        logger.info(f"注册任务路由: {task_type.value} -> {model_config.provider.value}/{model_config.model_name}")
    
    def register_model(self, name: str, model_config: ModelConfig) -> None:
        """
        注册模型配置
        
        Args:
            name: 模型配置名称
            model_config: 模型配置
        """
        self.model_configs[name] = model_config
        logger.info(f"注册模型配置: {name} -> {model_config.provider.value}/{model_config.model_name}")
    
    def set_fallback(self, model_config: ModelConfig) -> None:
        """
        设置回退模型配置
        
        Args:
            model_config: 回退模型配置
        """
        self.fallback_config = model_config
        logger.info(f"设置回退模型: {model_config.provider.value}/{model_config.model_name}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取所有可用模型"""
        models = []
        
        for name, config in self.model_configs.items():
            model_info = config.to_dict()
            model_info['name'] = name
            models.append(model_info)
        
        return models
    
    def get_task_routes(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务路由"""
        routes = {}
        
        for task_type, config in self.task_routing.items():
            routes[task_type.value] = {
                'task_type': task_type.value,
                'model_config': config.to_dict()
            }
        
        return routes
    
    def save_to_file(self, file_path: str) -> None:
        """
        保存到文件
        
        Args:
            file_path: 文件路径
        """
        data = {
            'version': '1.0',
            'updated_at': self._get_timestamp(),
            'fallback_config': self.fallback_config.to_dict() if self.fallback_config else None,
            'model_configs': {name: config.to_dict() for name, config in self.model_configs.items()},
            'task_routing': {task.value: config.to_dict() for task, config in self.task_routing.items()}
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"模型路由配置已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存模型路由配置失败: {e}")
    
    def load_from_file(self, file_path: str) -> None:
        """
        从文件加载
        
        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载模型配置
            if 'model_configs' in data:
                for name, config_data in data['model_configs'].items():
                    try:
                        config = ModelConfig.from_dict(config_data)
                        self.model_configs[name] = config
                    except Exception as e:
                        logger.error(f"加载模型配置 {name} 失败: {e}")
            
            # 加载回退配置
            if data.get('fallback_config'):
                try:
                    self.fallback_config = ModelConfig.from_dict(data['fallback_config'])
                except Exception as e:
                    logger.error(f"加载回退配置失败: {e}")
            
            # 加载任务路由
            if 'task_routing' in data:
                for task_str, config_data in data['task_routing'].items():
                    try:
                        task = TaskType(task_str)
                        config = ModelConfig.from_dict(config_data)
                        self.task_routing[task] = config
                    except Exception as e:
                        logger.error(f"加载任务路由 {task_str} 失败: {e}")
            
            logger.info(f"从 {file_path} 加载了模型路由配置")
            
        except Exception as e:
            logger.error(f"加载模型路由配置文件失败: {e}")
    
    def _load_default_configs(self) -> None:
        """加载默认配置"""
        # 定义默认模型配置
        default_models = {
            'deepseek-chat': ModelConfig(
                provider=ModelProvider.DEEPSEEK,
                model_name='deepseek-chat',
                max_tokens=8192,
                temperature=0.7,
                system_prompt='你是一个专业的量化分析助手，擅长股票分析和投资决策。',
                cost_per_token=0.000001  # 示例价格
            ),
            'gpt-4': ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name='gpt-4',
                max_tokens=4096,
                temperature=0.7,
                system_prompt='你是一个专业的金融分析师，擅长基本面分析。',
                cost_per_token=0.00003  # 示例价格
            ),
            'claude-3': ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name='claude-3-opus',
                max_tokens=4096,
                temperature=0.7,
                system_prompt='你是一个风险评估专家，擅长识别和评估投资风险。',
                cost_per_token=0.00006  # 示例价格
            ),
            'gemini-pro': ModelConfig(
                provider=ModelProvider.GOOGLE,
                model_name='gemini-pro',
                max_tokens=4096,
                temperature=0.7,
                system_prompt='你是一个技术分析专家，擅长图表分析和指标计算。',
                cost_per_token=0.00000125  # 示例价格
            ),
            'minimax-m2': ModelConfig(
                provider=ModelProvider.MINIMAX,
                model_name='MiniMax-M2.7',
                max_tokens=4096,
                temperature=0.7,
                system_prompt='你是一个情感分析专家，擅长分析市场情绪和舆论。',
                cost_per_token=0.000002  # 示例价格
            )
        }
        
        # 注册模型配置
        for name, config in default_models.items():
            self.register_model(name, config)
        
        # 设置默认任务路由
        self.register_task_route(
            TaskType.FUNDAMENTAL_ANALYSIS,
            default_models['gpt-4']
        )
        self.register_task_route(
            TaskType.TECHNICAL_ANALYSIS,
            default_models['gemini-pro']
        )
        self.register_task_route(
            TaskType.SENTIMENT_ANALYSIS,
            default_models['minimax-m2']
        )
        self.register_task_route(
            TaskType.RISK_ASSESSMENT,
            default_models['claude-3']
        )
        self.register_task_route(
            TaskType.FINAL_DECISION,
            default_models['deepseek-chat']
        )
        self.register_task_route(
            TaskType.CODE_GENERATION,
            default_models['deepseek-chat']
        )
        self.register_task_route(
            TaskType.DATA_PROCESSING,
            default_models['deepseek-chat']
        )
        self.register_task_route(
            TaskType.GENERAL_QUERY,
            default_models['deepseek-chat']
        )
        
        # 设置回退配置
        self.set_fallback(default_models['deepseek-chat'])
        
        logger.info("加载了默认模型路由配置")
    
    def _prepare_request_params(
        self,
        model_config: ModelConfig,
        prompt: str,
        task: TaskType,
        **kwargs
    ) -> Dict[str, Any]:
        """准备请求参数"""
        base_params = {
            'model': model_config.model_name,
            'messages': self._prepare_messages(model_config, prompt, task),
            'max_tokens': model_config.max_tokens,
            'temperature': model_config.temperature,
            'top_p': model_config.top_p,
            'frequency_penalty': model_config.frequency_penalty,
            'presence_penalty': model_config.presence_penalty
        }
        
        # 添加额外参数
        base_params.update(kwargs)
        
        return base_params
    
    def _prepare_messages(
        self,
        model_config: ModelConfig,
        prompt: str,
        task: TaskType
    ) -> List[Dict[str, str]]:
        """准备消息列表"""
        messages = []
        
        # 添加系统提示词
        if model_config.system_prompt:
            messages.append({
                'role': 'system',
                'content': model_config.system_prompt
            })
        
        # 添加任务特定提示词
        task_prompt = self._get_task_specific_prompt(task)
        if task_prompt:
            messages.append({
                'role': 'system',
                'content': task_prompt
            })
        
        # 添加用户提示词
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        return messages
    
    def _get_task_specific_prompt(self, task: TaskType) -> str:
        """获取任务特定提示词"""
        task_prompts = {
            TaskType.FUNDAMENTAL_ANALYSIS: """
            请进行基本面分析，重点关注：
            1. 公司财务状况（营收、利润、现金流）
            2. 行业地位和竞争优势
            3. 管理团队和公司治理
            4. 估值水平（PE、PB、PEG等）
            5. 增长前景和风险因素
            请提供详细的分析报告。
            """,
            TaskType.TECHNICAL_ANALYSIS: """
            请进行技术分析，重点关注：
            1. 价格趋势和形态
            2. 关键支撑位和阻力位
            3. 技术指标（MACD、RSI、布林带等）
            4. 成交量分析
            5. 市场情绪和资金流向
            请提供详细的技术分析报告。
            """,
            TaskType.SENTIMENT_ANALYSIS: """
            请进行情感分析，重点关注：
            1. 新闻和社交媒体情绪
            2. 分析师评级和预期
            3. 市场舆论和投资者情绪
            4. 重大事件影响
            5. 情绪指标和趋势
            请提供详细的情感分析报告。
            """,
            TaskType.RISK_ASSESSMENT: """
            请进行风险评估，重点关注：
            1. 市场风险（系统性风险）
            2. 信用风险（违约风险）
            3. 流动性风险
            4. 操作风险
            5. 合规风险
            请提供详细的风险评估报告。
            """,
            TaskType.FINAL_DECISION: """
            请基于所有分析结果做出最终投资决策，包括：
            1. 投资建议（买入/持有/卖出）
            2. 目标价位和止损位
            3. 仓位建议
            4. 投资逻辑和理由
            5. 风险提示和注意事项
            请提供明确的投资建议。
            """
        }
        
        return task_prompts.get(task, "")
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 全局模型路由器实例
model_router = ModelRouter()