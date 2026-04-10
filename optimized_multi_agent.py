"""
优化后的多智能体选股系统 - 贾维斯 v2.0
整合 TradingAgents-CN 架构，增强多智能体能力

架构特点：
1. 融合贾维斯原有系统和 TradingAgents-CN
2. 支持多种 LLM 提供商 (DeepSeek, OpenAI, Anthropic, Google, DashScope)
3. 模块化设计，易于扩展
4. 统一的配置管理
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# 添加 TradingAgents-CN 到路径
trading_agents_path = "/root/.openclaw/workspace/TradingAgents-CN"
if trading_agents_path not in sys.path:
    sys.path.insert(0, trading_agents_path)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 数据类定义 ====================

@dataclass
class AnalysisResult:
    """分析结果数据类"""
    stock_code: str
    stock_name: str
    analysis_time: str
    decision: str  # BUY/SELL/HOLD/STRONG_BUY/STRONG_SELL
    decision_cn: str  # 中文决策
    confidence: float  # 置信度 0-1
    reasoning: str  # 推理过程
    reports: Dict[str, str]  # 各智能体报告
    metadata: Dict[str, Any]  # 元数据
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class AgentConfig:
    """智能体配置"""
    name: str
    model_provider: str  # deepseek, openai, anthropic, google, dashscope
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: str = ""
    enabled: bool = True


# ==================== 模型管理器 ====================

class ModelManager:
    """模型管理器 - 统一管理各种 LLM"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.clients = {}
        self._initialize_clients()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        config = {
            "api_keys": {
                "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
                "openai": os.getenv("OPENAI_API_KEY", ""),
                "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
                "google": os.getenv("GOOGLE_API_KEY", ""),
                "dashscope": os.getenv("DASHSCOPE_API_KEY", "")
            },
            "base_urls": {
                "deepseek": "https://api.deepseek.com",
                "openai": "https://api.openai.com/v1",
                "anthropic": "https://api.anthropic.com",
                "google": "https://generativelanguage.googleapis.com",
                "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1"
            },
            "default_model": "deepseek-chat"
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
            except Exception as e:
                logger.warning(f"无法加载配置文件 {config_path}: {e}")
        
        return config
    
    def _initialize_clients(self):
        """初始化各种 LLM 客户端"""
        try:
            # 尝试导入 TradingAgents-CN 的 LLM 适配器
            from tradingagents.llm_adapters.deepseek_adapter import ChatDeepSeek
            from tradingagents.llm_adapters.openai_compatible_base import create_openai_compatible_llm
            
            # 初始化 DeepSeek
            deepseek_key = self.config["api_keys"]["deepseek"]
            if deepseek_key:
                self.clients["deepseek"] = ChatDeepSeek(
                    model="deepseek-chat",
                    api_key=deepseek_key,
                    base_url=self.config["base_urls"]["deepseek"]
                )
                logger.info("✅ DeepSeek 客户端初始化成功")
            
            # 初始化 OpenAI 兼容客户端
            for provider in ["openai", "anthropic", "google", "dashscope"]:
                api_key = self.config["api_keys"][provider]
                if api_key:
                    try:
                        client = create_openai_compatible_llm(
                            provider=provider,
                            model=f"{provider}-default",
                            api_key=api_key,
                            base_url=self.config["base_urls"][provider]
                        )
                        self.clients[provider] = client
                        logger.info(f"✅ {provider} 客户端初始化成功")
                    except Exception as e:
                        logger.warning(f"⚠️  {provider} 客户端初始化失败: {e}")
                        
        except ImportError as e:
            logger.warning(f"无法导入 TradingAgents-CN LLM 适配器: {e}")
            logger.info("将使用简单的 HTTP 客户端")
            self._initialize_simple_clients()
    
    def _initialize_simple_clients(self):
        """初始化简单的 HTTP 客户端"""
        import requests
        
        class SimpleClient:
            def __init__(self, provider, api_key, base_url):
                self.provider = provider
                self.api_key = api_key
                self.base_url = base_url
            
            def chat(self, messages, system=None, temperature=0.7):
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                full_messages = []
                if system:
                    full_messages.append({"role": "system", "content": system})
                full_messages.extend(messages)
                
                payload = {
                    "model": "default",
                    "messages": full_messages,
                    "temperature": temperature
                }
                
                try:
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    response.raise_for_status()
                    return response.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    return f"{self.provider} API 调用失败: {str(e)}"
        
        for provider in ["deepseek", "openai"]:
            api_key = self.config["api_keys"][provider]
            if api_key:
                self.clients[provider] = SimpleClient(
                    provider=provider,
                    api_key=api_key,
                    base_url=self.config["base_urls"][provider]
                )
                logger.info(f"✅ {provider} 简单客户端初始化成功")
    
    def get_client(self, provider: str):
        """获取指定提供商的客户端"""
        return self.clients.get(provider)
    
    def chat(self, provider: str, messages: List[Dict], system: str = None, temperature: float = 0.7) -> str:
        """使用指定提供商进行聊天"""
        client = self.get_client(provider)
        if not client:
            return f"❌ {provider} 客户端未初始化"
        
        try:
            if hasattr(client, 'chat'):
                return client.chat(messages, system=system, temperature=temperature)
            else:
                # 对于 TradingAgents-CN 的 LLM 对象
                from langchain_core.messages import HumanMessage, SystemMessage
                
                full_messages = []
                if system:
                    full_messages.append(SystemMessage(content=system))
                for msg in messages:
                    if msg["role"] == "user":
                        full_messages.append(HumanMessage(content=msg["content"]))
                
                response = client.invoke(full_messages)
                return response.content
        except Exception as e:
            logger.error(f"{provider} 聊天失败: {e}")
            return f"❌ {provider} 聊天失败: {str(e)}"


# ==================== 智能体基类 ====================

class BaseAgent:
    """智能体基类"""
    
    def __init__(self, name: str, model_manager: ModelManager, config: AgentConfig):
        self.name = name
        self.model_manager = model_manager
        self.config = config
        self.system_prompt = config.system_prompt
    
    def analyze(self, stock_code: str, stock_name: str, context: Dict = None) -> str:
        """
        分析股票
        子类需要实现此方法
        """
        raise NotImplementedError("子类必须实现 analyze 方法")
    
    def _call_llm(self, prompt: str, context: str = "") -> str:
        """调用 LLM"""
        messages = [{"role": "user", "content": prompt}]
        if context:
            messages.insert(0, {"role": "system", "content": context})
        
        return self.model_manager.chat(
            provider=self.config.model_provider,
            messages=messages,
            system=self.system_prompt,
            temperature=self.config.temperature
        )


# ==================== 具体智能体 ====================

class FundamentalAgent(BaseAgent):
    """基本面分析智能体"""
    
    def __init__(self, model_manager: ModelManager):
        config = AgentConfig(
            name="fundamental",
            model_provider="deepseek",
            model_name="deepseek-chat",
            system_prompt="""你是一位资深基本面分析师，专注于公司财务分析。
关注指标：营收增长、净利润、PE、PB、ROE、现金流、负债率
分析维度：行业地位、竞争力、成长性、风险点
请用中文输出专业分析报告。"""
        )
        super().__init__("fundamental", model_manager, config)
    
    def analyze(self, stock_code: str, stock_name: str, context: Dict = None) -> str:
        prompt = f"""分析 {stock_name} ({stock_code}) 的基本面状况：
        
请从以下维度进行分析：
1. 所处行业及行业地位
2. 营收和净利润增长趋势
3. 主要财务指标（PE、PB、ROE）
4. 竞争优势和风险点
5. 综合评分（1-10分）

请输出详细的中文分析报告。"""
        
        return self._call_llm(prompt)


class TechnicalAgent(BaseAgent):
    """技术面分析智能体"""
    
    def __init__(self, model_manager: ModelManager):
        config = AgentConfig(
            name="technical",
            model_provider="deepseek",
            model_name="deepseek-chat",
            system_prompt="""你是一位技术分析专家，擅长K线和技术指标分析。
分析指标：MACD、KDJ、RSI、布林带、均线系统、成交量
分析维度：趋势判断、支撑阻力、买卖信号
请用中文输出专业分析报告。"""
        )
        super().__init__("technical", model_manager, config)
    
    def analyze(self, stock_code: str, stock_name: str, context: Dict = None) -> str:
        prompt = f"""分析 {stock_name} ({stock_code}) 的技术面状况：

请从以下维度进行分析：
1. 当前价格位置（相对历史高低点）
2. 均线系统状态（多头/空头排列）
3. MACD指标信号
4. KDJ指标状态
5. 成交量变化
6. 支撑位和压力位
7. 综合评分（1-10分）

请输出详细的中文分析报告。"""
        
        return self._call_llm(prompt)


class SentimentAgent(BaseAgent):
    """情绪面分析智能体"""
    
    def __init__(self, model_manager: ModelManager):
        config = AgentConfig(
            name="sentiment",
            model_provider="minimax",  # 可以使用 MiniMax 或 Anthropic
            model_name="MiniMax-M2.7",
            system_prompt="""你是一位市场情绪分析师，专注于消息面和情绪分析。
分析维度：政策利好/利空、行业动态、主力动向、舆情监控
判断市场整体情绪：乐观/中性/悲观
请用中文输出专业分析报告。"""
        )
        super().__init__("sentiment", model_manager, config)
    
    def analyze(self, stock_code: str, stock_name: str, context: Dict = None) -> str:
        prompt = f"""分析 {stock_name} ({stock_code}) 相关的市场情绪：

请从以下维度进行分析：
1. 近期是否有重大利好/利空消息
2. 板块整体氛围
3. 主力资金动向
4. 市场关注度
5. 情绪评分（乐观/中性/悲观）

请输出详细的中文分析报告。"""
        
        return self._call_llm(prompt)


class RiskAgent(BaseAgent):
    """风险评估智能体"""
    
    def __init__(self, model_manager: ModelManager):
        config = AgentConfig(
            name="risk",
            model_provider="deepseek",
            model_name="deepseek-chat",
            system_prompt="""你是一位资深风控专家，专注于风险评估。
评估维度：市场风险、行业风险、个股风险、流动性风险
给出仓位建议：轻仓/半仓/重仓/空仓
请用中文输出专业风险评估报告。"""
        )
        super().__init__("risk", model_manager, config)
    
    def analyze(self, stock_code: str, stock_name: str, context: Dict = None) -> str:
        prompt = f"""评估 {stock_name} ({stock_code}) 的风险：

请评估：
1. 市场风险等级（高/中/低）
2. 行业风险等级（高/中/低）
3. 个股风险等级（高/中/低）
4. 建议仓位（0-100%）
5. 止损位建议

请输出详细的中文风险评估报告。"""
        
        return self._call_llm(prompt)


class TradingAgentsWrapper:
    """TradingAgents-CN 包装器"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.ta_available = False
        self.graph = None
        
        self._initialize_trading_agents()
    
    def _initialize_trading_agents(self):
        """初始化 TradingAgents-CN"""
        try:
            from tradingagents.graph.trading_graph import TradingAgentsGraph
            
            # 获取 DeepSeek API 密钥
            deepseek_key = self.model_manager.config["api_keys"]["deepseek"]
            
            if not deepseek_key:
                logger.warning("⚠️ DeepSeek API 密钥未设置，TradingAgents-CN 将无法使用")
                return
            
            # 创建 TradingAgentsGraph
            self.graph = TradingAgentsGraph(
                selected_analysts=["market", "social", "news", "fundamentals"],
                debug=False,
                config={
                    "llm_provider": "deepseek",
                    "deep_think_llm": "deepseek-chat",
                    "quick_think_llm": "deepseek-chat",
                    "api_key": deepseek_key
                }
            )
            
            self.ta_available = True
            logger.info("✅ TradingAgents-CN 初始化成功")
            
        except ImportError as e:
            logger.warning(f"❌ 无法导入 TradingAgents-CN: {e}")
        except Exception as e:
            logger.error(f"❌ TradingAgents-CN 初始化失败: {e}")
    
    def analyze(self, stock_code: str, stock_name: str) -> Dict[str, Any]:
        """使用 TradingAgents-CN 分析股票"""
        if not self.ta_available or not self.graph:
            return {
                "error": "TradingAgents-CN 未初始化",
                "available": False
            }
        
        try:
            # 设置股票代码
            self.graph.ticker = stock_code
            
            # 执行分析
            final_state, processed_signal = self.graph.propagate(stock_name, date.today().isoformat())
            
            # 提取关键信息
            result = {
                "available": True,
                "decision": processed_signal.get("decision", "HOLD"),
                "confidence": processed_signal.get("confidence", 0.5),
                "reasoning": self._extract_reasoning(final_state),
                "reports": {
                    "market": final_state.get("market_report", ""),
                    "sentiment": final_state.get("sentiment_report", ""),
                    "news": final_state.get("news_report", ""),
                    "fundamentals": final_state.get("fundamentals_report", ""),
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ TradingAgents-CN 分析失败: {e}")
            return {
                "error": str(e),
                "available": False
            }
    
    def _extract_reasoning(self, state: Dict[str, Any]) -> str:
        """从状态中提取推理过程"""
        reasoning_parts = []
        
        for report_type in ["market_report", "sentiment_report", "news_report", "fundamentals_report"]:
            if report_type in state and state[report_type]:
                content = state[report_type]
                if len(content) > 200:
                    content = content[:200] + "..."
                reasoning_parts.append(f"{report_type.replace('_report', '')}: {content}")
        
        return "\n\n".join(reasoning_parts)


# ==================== 多智能体协调器 ====================

class MultiAgentCoordinator:
    """多智能体协调器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.model_manager = ModelManager(config_path)
        self.agents = {}
        self.ta_wrapper = None
        
        self._initialize_agents()
        self._initialize_trading_agents()
    
    def _initialize_agents(self):
        """初始化智能体"""
        # 创建各个智能体
        self.agents["fundamental"] = FundamentalAgent(self.model_manager)
        self.agents["technical"] = TechnicalAgent(self.model_manager)
        self.agents["sentiment"] = SentimentAgent(self.model_manager)
        self.agents["risk"] = RiskAgent(self.model_manager)
        
        logger.info(f"✅ 初始化了 {len(self.agents)} 个智能体")
    
    def _initialize_trading_agents(self):
        """初始化 TradingAgents-CN"""
        try:
            self.ta_wrapper = TradingAgentsWrapper(self.model_manager)
            if self.ta_wrapper.ta_available:
                logger.info("✅ TradingAgents-CN 包装器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ TradingAgents-CN 包装器初始化失败: {e}")
    
    def analyze_stock(self, stock_code: str, stock_name: str = None) -> AnalysisResult:
        """
        综合分析一只股票
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            
        Returns:
            分析结果
        """
        name = stock_name or stock_code
        
        logger.info(f"🔍 开始分析: {name} ({stock_code})")
        
        # 并行执行各个智能体分析
        reports = {}
        for agent_name, agent in self.agents.items():
            if agent.config.enabled:
                logger.info(f"  🤖 {agent_name} 分析中...")
                try:
                    report = agent.analyze(stock_code, name)
                    reports[agent_name] = report
                    logger.info(f"  ✅ {agent_name} 分析完成")
                except Exception as e:
                    logger.error(f"  ❌ {agent_name} 分析失败: {e}")
                    reports[agent_name] = f"{agent_name} 分析失败: {str(e)}"
        
        # 执行 TradingAgents-CN 分析
        ta_result = None
        if self.ta_wrapper and self.ta_wrapper.ta_available:
            logger.info("  🤖 TradingAgents-CN 分析中...")
            try:
                ta_result = self.ta_wrapper.analyze(stock_code, name)
                if ta_result.get("available", False):
                    reports["trading_agents"] = ta_result
                    logger.info("  ✅ TradingAgents-CN 分析完成")
                else:
                    logger.warning("  ⚠️ TradingAgents-CN 分析不可用")
            except Exception as e:
                logger.error(f"  ❌ TradingAgents-CN 分析失败: {e}")
        
        # 综合决策
        decision, confidence, reasoning = self._make_decision(reports, ta_result)
        
        # 创建结果对象
        result = AnalysisResult(
            stock_code=stock_code,
            stock_name=name,
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            decision=decision,
            decision_cn=self._translate_decision(decision),
            confidence=confidence,
            reasoning=reasoning,
            reports=reports,
            metadata={
                "agents_used": list(self.agents.keys()),
                "trading_agents_used": ta_result is not None and ta_result.get("available", False),
                "model_providers": {
                    agent_name: agent.config.model_provider 
                    for agent_name, agent in self.agents.items()
                }
            }
        )
        
        logger.info(f"✅ 分析完成: {stock_code} -> {result.decision_cn} (置信度: {confidence:.2f})")
        return result
    
    def _make_decision(self, reports: Dict, ta_result: Optional[Dict]) -> Tuple[str, float, str]:
        """基于所有分析做出综合决策"""
        # 收集各个智能体的决策信号
        signals = []
        
        # 从基本面分析中提取信号
        if "fundamental" in reports:
            fundamental_text = reports["fundamental"]
            signals.append(self._extract_signal_from_text(fundamental_text, "fundamental"))
        
        # 从技术面分析中提取信号
        if "technical" in reports:
            technical_text = reports["technical"]
            signals.append(self._extract_signal_from_text(technical_text, "technical"))
        
        # 从情绪面分析中提取信号
        if "sentiment" in reports:
            sentiment_text = reports["sentiment"]
            signals.append(self._extract_signal_from_text(sentiment_text, "sentiment"))
        
        # 从风险评估中提取信号
        if "risk" in reports:
            risk_text = reports["risk"]
            signals.append(self._extract_signal_from_text(risk_text, "risk"))
        
        # 从 TradingAgents-CN 中获取信号
        if ta_result and ta_result.get("available", False):
            ta_decision = ta_result.get("decision", "HOLD")
            ta_confidence = ta_result.get("confidence", 0.5)
            signals.append({
                "source": "trading_agents",
                "decision": ta_decision,
                "confidence": ta_confidence,
                "weight": 0.4  # TradingAgents 权重
            })
        
        # 计算加权决策
        decision_scores = {
            "STRONG_BUY": 2,
            "BUY": 1,
            "HOLD": 0,
            "SELL": -1,
            "STRONG_SELL": -2
        }
        
        total_score = 0
        total_weight = 0
        
        for signal in signals:
            decision = signal.get("decision", "HOLD")
            confidence = signal.get("confidence", 0.5)
            weight = signal.get("weight", 0.15)  # 默认权重
            
            score = decision_scores.get(decision, 0)
            weighted_score = score * confidence * weight
            
            total_score += weighted_score
            total_weight += weight
        
        # 归一化
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0
        
        # 根据分数决定最终决策
        if normalized_score >= 1.5:
            final_decision = "STRONG_BUY"
            confidence = min(0.9, (normalized_score - 1.0) / 2.0 + 0.7)
        elif normalized_score >= 0.5:
            final_decision = "BUY"
            confidence = min(0.8, normalized_score / 2.0 + 0.5)
        elif normalized_score <= -1.5:
            final_decision = "STRONG_SELL"
            confidence = min(0.9, (-normalized_score - 1.0) / 2.0 + 0.7)
        elif normalized_score <= -0.5:
            final_decision = "SELL"
            confidence = min(0.8, -normalized_score / 2.0 + 0.5)
        else:
            final_decision = "HOLD"
            confidence = 0.5
        
        # 生成推理过程
        reasoning = self._generate_reasoning(signals, final_decision, normalized_score)
        
        return final_decision, confidence, reasoning
    
    def _extract_signal_from_text(self, text: str, source: str) -> Dict:
        """从文本中提取决策信号"""
        # 简单的关键词匹配
        text_lower = text.lower()
        
        if "强烈买入" in text or "强烈推荐" in text or "强力买入" in text:
            decision = "STRONG_BUY"
            confidence = 0.8
        elif "买入" in text or "推荐" in text or "看好" in text:
            decision = "BUY"
            confidence = 0.7
        elif "卖出" in text or "减持" in text or "看空" in text:
            decision = "SELL"
            confidence = 0.7
        elif "强烈卖出" in text or "强烈减持" in text:
            decision = "STRONG_SELL"
            confidence = 0.8
        else:
            decision = "HOLD"
            confidence = 0.5
        
        # 尝试从文本中提取置信度
        if "高" in text and "风险" in text:
            confidence *= 0.8
        if "低" in text and "风险" in text:
            confidence *= 1.2
        
        return {
            "source": source,
            "decision": decision,
            "confidence": min(max(confidence, 0.1), 0.9),
            "weight": 0.15  # 每个智能体默认权重
        }
    
    def _generate_reasoning(self, signals: List[Dict], final_decision: str, score: float) -> str:
        """生成推理过程"""
        reasoning_parts = [f"综合评分: {score:.2f}"]
        reasoning_parts.append(f"最终决策: {self._translate_decision(final_decision)}")
        reasoning_parts.append("")
        reasoning_parts.append("各智能体贡献:")
        
        for signal in signals:
            source = signal["source"]
            decision = signal["decision"]
            confidence = signal["confidence"]
            weight = signal["weight"]
            
            reasoning_parts.append(
                f"- {source}: {self._translate_decision(decision)} "
                f"(置信度: {confidence:.2f}, 权重: {weight:.2f})"
            )
        
        return "\n".join(reasoning_parts)
    
    def _translate_decision(self, decision: str) -> str:
        """翻译决策为中文"""
        decision_map = {
            "BUY": "买入",
            "SELL": "卖出", 
            "HOLD": "持有",
            "STRONG_BUY": "强烈买入",
            "STRONG_SELL": "强烈卖出"
        }
        return decision_map.get(decision, decision)
    
    def format_report(self, result: AnalysisResult) -> str:
        """格式化分析报告"""
        report = f"""
{'='*80}
🤖 贾维斯优化多智能体分析报告 v2.0
{'='*80}

📈 股票: {result.stock_name} ({result.stock_code})
⏰ 分析时间: {result.analysis_time}

{'='*80}
🎯 综合决策
{'='*80}
📊 最终决策: {result.decision_cn} ({result.decision})
📈 置信度: {result.confidence:.2%}
📝 推理过程:
{result.reasoning}

{'='*80}
📋 详细分析
{'='*80}
"""
        
        # 添加各个智能体报告
        for agent_name, report_text in result.reports.items():
            if agent_name == "trading_agents":
                continue  # TradingAgents 单独处理
            
            report += f"\n📊 {agent_name.upper()} 分析:\n"
            if isinstance(report_text, str):
                # 截取前300字符
                if len(report_text) > 300:
                    report_text = report_text[:300] + "..."
                report += f"{report_text}\n"
        
        # 添加 TradingAgents-CN 分析
        if "trading_agents" in result.reports:
            ta_result = result.reports["trading_agents"]
            if isinstance(ta_result, dict) and ta_result.get("available", False):
                report += f"\n{'='*80}\n"
                report += "🤖 TradingAgents-CN 分析\n"
                report += f"{'='*80}\n"
                report += f"📊 决策: {self._translate_decision(ta_result.get('decision', 'HOLD'))}\n"
                report += f"📈 置信度: {ta_result.get('confidence', 0.5):.2%}\n"
                
                reasoning = ta_result.get("reasoning", "")
                if reasoning and len(reasoning) > 300:
                    reasoning = reasoning[:300] + "..."
                report += f"📝 分析摘要: {reasoning}\n"
        
        report += f"""
{'='*80}
⚠️ 风险提示
{'='*80}
1. 本分析由多智能体系统生成，仅供参考
2. 股市有风险，投资需谨慎
3. 请结合自身风险承受能力做出决策
4. 建议设置止损位，控制仓位

{'='*80}
🤵 贾维斯出品 | 优化多智能体系统 v2.0
{'='*80}
"""
        return report


# ==================== 主程序 ====================

def main():
    """主程序"""
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     贾维斯优化多智能体选股系统 v2.0                  ║
    ║     融合 TradingAgents-CN 架构                      ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # 初始化协调器
    print("🚀 初始化多智能体系统...")
    coordinator = MultiAgentCoordinator()
    
    # 测试股票
    test_stocks = [
        ("002202", "金风科技"),
        ("000858", "五粮液"),
        ("300750", "宁德时代")
    ]
    
    for stock_code, stock_name in test_stocks:
        print(f"\n{'='*60}")
        print(f"📊 分析: {stock_name} ({stock_code})")
        print(f"{'='*60}")
        
        try:
            # 分析股票
            result = coordinator.analyze_stock(stock_code, stock_name)
            
            # 打印报告
            print(coordinator.format_report(result))
            
            # 保存结果
            output_file = f"/tmp/{stock_code}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"💾 分析结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
    
    print("\n✅ 所有分析完成！")


if __name__ == "__main__":
    main()
