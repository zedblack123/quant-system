# 贾维斯量化系统优化方案
## 借鉴 Claude Code 架构

---

## 一、现状分析

### 当前系统架构
```
MultiAgentCoordinator
├── ModelManager (多模型支持)
├── FundamentalAgent (基本面)
├── TechnicalAgent (技术面)
├── SentimentAgent (情绪面)
├── RiskAgent (风险评估)
└── TradingAgents-CN (外部整合)
```

### Claude Code 可借鉴的架构

| Claude Code 设计 | 当前系统缺失 | 可借鉴程度 |
|----------------|------------|----------|
| 57个专业工具注册表 | 无统一工具系统 | ⭐⭐⭐⭐⭐ |
| 70+ React Hooks | 无生命周期钩子 | ⭐⭐⭐⭐ |
| 上下文压缩 | 长对话无压缩 | ⭐⭐⭐⭐ |
| Feature Flags | 无灰度发布 | ⭐⭐⭐ |
| Analytics + GrowthBook | 无策略追踪 | ⭐⭐⭐⭐ |
| 权限分级系统 | 无交易权限控制 | ⭐⭐⭐ |
| MCP协议扩展 | 无外部集成框架 | ⭐⭐⭐⭐ |

---

## 二、优化方案

### 1. 工具系统化 (Tool Architecture) ⭐⭐⭐⭐⭐

**目标**: 像 Claude Code 一样，建立统一的工具注册表

**当前问题**:
- 工具硬编码在Agent里
- 难以复用和组合
- 缺少标准化的输入输出

**优化方案**:

```python
# 工具基类
class BaseTool:
    name: str  # 工具名称
    description: str  # 工具描述
    input_schema: dict  # 输入schema (JSON Schema)
    output_schema: dict  # 输出schema
    
    async def execute(self, params: dict) -> dict:
        """执行工具逻辑"""
        pass
    
    def get_permission_level(self) -> str:
        """获取工具权限等级"""
        pass
```

**核心工具清单**:

| 工具名称 | 功能 | 权限等级 | 依赖 |
|---------|-----|---------|------|
| `StockDataTool` | 获取股票数据 | LOW | Tushare/AKShare |
| `TechnicalAnalysisTool` | 技术指标计算 | LOW | Talib |
| `NewsSearchTool` | 新闻搜索 | LOW | 东方财富 |
| `SocialMediaTool` | 社交媒体情绪 | LOW | 东财/淘股吧 |
| `RiskCalcTool` | 风险计算 | MEDIUM | 内部算法 |
| `TradeExecuteTool` | 执行交易 | HIGH | 券商API |
| `PortfolioTool` | 持仓管理 | HIGH | 账户系统 |
| `BacktestTool` | 回测工具 | LOW | 历史数据 |

**工具注册表**:

```python
class ToolRegistry:
    """工具注册表 - 单例模式"""
    
    _instance = None
    _tools = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        logger.info(f"✅ 工具已注册: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)
    
    def list_tools(self, permission_level: str = None) -> List[BaseTool]:
        """列出工具"""
        tools = self._tools.values()
        if permission_level:
            tools = [t for t in tools if t.get_permission_level() <= permission_level]
        return list(tools)
```

---

### 2. 生命周期钩子 (Hook System) ⭐⭐⭐⭐

**目标**: 在关键节点插入可插拔的逻辑

```python
class TradeLifecycle:
    """交易生命周期钩子"""
    
    HOOKS = {
        'pre_analysis': [],    # 分析前
        'post_analysis': [],   # 分析后
        'pre_decision': [],   # 决策前
        'post_decision': [],  # 决策后
        'pre_trade': [],      # 交易前
        'post_trade': [],     # 交易后
        'on_error': [],       # 错误时
    }
    
    def register_hook(self, stage: str, hook_func: Callable):
        """注册钩子"""
        if stage in self.HOOKS:
            self.HOOKS[stage].append(hook_func)
    
    async def execute_hook(self, stage: str, context: dict):
        """执行钩子"""
        for hook in self.HOOKS.get(stage, []):
            result = await hook(context)
            if result is False:
                logger.warning(f"⚠️ 钩子 {hook.__name__} 返回 False，终止流程")
                return False
        return True
```

**预置钩子**:

```python
# 1. 风险检查钩子
async def risk_check_hook(context):
    """交易前风险检查"""
    position = context.get('position', 0)
    if position > config.MAX_POSITION:
        logger.warning(f"⚠️ 仓位超限: {position} > {config.MAX_POSITION}")
        return False  # 阻止交易
    return True

# 2. 权限验证钩子
async def permission_check_hook(context):
    """验证交易权限"""
    user_level = context.get('user_permission', 'LOW')
    trade_tool = context.get('tool_name', '')
    required_level = TOOL_PERMISSIONS.get(trade_tool, 'HIGH')
    return user_level >= required_level

# 3. 交易记录钩子
async def trade_log_hook(context):
    """记录交易日志"""
    logger.info(f"📊 交易记录: {context}")

# 4. 绩效追踪钩子
async def performance_track_hook(context):
    """追踪交易绩效"""
    # 上报到 analytics 系统
    track_event('trade_executed', context)
```

---

### 3. 上下文压缩 (Context Compaction) ⭐⭐⭐⭐

**目标**: 长对话中自动压缩历史，保留关键信息

```python
class ContextCompactor:
    """上下文压缩器"""
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
    
    def should_compact(self, messages: List[dict]) -> bool:
        """判断是否需要压缩"""
        total_tokens = sum(self.count_tokens(m) for m in messages)
        return total_tokens > self.max_tokens
    
    def compact(self, messages: List[dict]) -> List[dict]:
        """压缩上下文"""
        # 1. 识别关键决策点
        key_decisions = self.extract_key_decisions(messages)
        
        # 2. 保留最近 N 条消息
        recent = messages[-10:]
        
        # 3. 生成摘要替换旧消息
        summary = self.generate_summary(messages[:-10])
        
        return [
            {"role": "system", "content": f"历史摘要: {summary}"},
            {"role": "system", "content": f"关键决策: {key_decisions}"},
        ] + recent
    
    def extract_key_decisions(self, messages: List[dict]) -> str:
        """提取关键决策"""
        decisions = []
        for m in messages:
            if 'decision' in m.get('content', '').lower():
                decisions.append(m.get('content', '')[:100])
        return "; ".join(decisions[-5:])  # 保留最近5条
    
    def generate_summary(self, messages: List[dict]) -> str:
        """生成摘要"""
        # 使用模型生成摘要
        prompt = f"请总结以下对话的要点（不超过200字）:\n{messages}"
        return call_llm(prompt)
```

---

### 4. Feature Flags (特性开关) ⭐⭐⭐

**目标**: 支持策略灰度发布、A/B测试

```python
class FeatureFlags:
    """特性开关系统"""
    
    _flags = {
        'new_strategy_v2': False,      # 新策略v2
        'multi_factor_model': False,    # 多因子模型
        'ai_sentiment': True,           # AI情绪分析
        'risk_control_v2': False,        # 风险控制v2
    }
    
    _growthbook_url = "https://api.growthbook.com"
    
    @classmethod
    def is_enabled(cls, flag: str, context: dict = None) -> bool:
        """检查特性是否启用"""
        # 优先从GrowthBook获取（远程实验）
        value = cls._get_from_growthbook(flag, context)
        if value is not None:
            return value
        
        # 回退到本地配置
        return cls._flags.get(flag, False)
    
    @classmethod
    def enable(cls, flag: str):
        """启用特性"""
        cls._flags[flag] = True
        logger.info(f"✅ 特性已启用: {flag}")
    
    @classmethod
    def disable(cls, flag: str):
        """禁用特性"""
        cls._flags[flag] = False
        logger.info(f"❌ 特性已禁用: {flag}")
    
    @classmethod
    def set_for_user(cls, flag: str, user_id: str, enabled: bool):
        """针对特定用户设置"""
        # 用于灰度发布
        key = f"user_{user_id}_{flag}"
        cls._flags[key] = enabled
```

**使用示例**:

```python
# 在策略选择中
if FeatureFlags.is_enabled('new_strategy_v2', {'user_id': user_id}):
    result = await new_strategy_v2(stock)
else:
    result = await old_strategy(stock)

# 在回测中支持A/B测试
for group in ['A', 'B']:
    context = {'ab_group': group, 'user_id': user_id}
    if FeatureFlags.is_enabled('multi_factor_model', context):
        # A组使用多因子
    else:
        # B组使用单因子
```

---

### 5. Analytics + 绩效追踪 ⭐⭐⭐⭐

**目标**: 追踪每个Agent的表现，持续优化

```python
@dataclass
class AgentMetrics:
    """智能体指标"""
    agent_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    avg_latency: float  # ms
    avg_confidence: float
    decision_accuracy: float  # 回测准确率
    
    # 新增：决策分布
    buy_signals: int
    sell_signals: int
    hold_signals: int

class AnalyticsTracker:
    """分析追踪器"""
    
    def __init__(self):
        self.metrics = defaultdict(AgentMetrics)
        self.trades = []
    
    def record_agent_call(self, agent_name: str, latency: float, 
                         confidence: float, decision: str):
        """记录Agent调用"""
        m = self.metrics[agent_name]
        m.total_calls += 1
        m.successful_calls += 1
        m.avg_latency = (m.avg_latency * (m.total_calls - 1) + latency) / m.total_calls
        m.avg_confidence = (m.avg_confidence * (m.total_calls - 1) + confidence) / m.total_calls
        
        if decision == 'BUY':
            m.buy_signals += 1
        elif decision == 'SELL':
            m.sell_signals += 1
        else:
            m.hold_signals += 1
    
    def record_trade(self, trade: dict):
        """记录交易"""
        self.trades.append(trade)
    
    def generate_report(self) -> str:
        """生成分析报告"""
        report = "📊 Agent 绩效报告\n" + "="*50 + "\n"
        for name, m in self.metrics.items():
            accuracy = (m.successful_calls / m.total_calls * 100) if m.total_calls > 0 else 0
            report += f"""
{name}:
  - 总调用: {m.total_calls}
  - 成功率: {accuracy:.1f}%
  - 平均延迟: {m.avg_latency:.0f}ms
  - 置信度: {m.avg_confidence:.2f}
  - 信号分布: 买{m.buy_signals} 卖{m.sell_signals} 持{m.hold_signals}
"""
        return report
    
    def get_best_agent(self, metric: str = 'accuracy') -> str:
        """获取最佳Agent"""
        if metric == 'accuracy':
            return max(self.metrics.keys(), 
                      key=lambda k: self.metrics[k].avg_confidence)
        return None
```

---

### 6. 权限分级系统 ⭐⭐⭐

**目标**: 交易权限分级，大额交易需要多重确认

```python
class PermissionLevel:
    """权限等级"""
    LOW = 1      # 查看、分析
    MEDIUM = 2   # 小额交易
    HIGH = 3     # 大额交易
    ADMIN = 4    # 管理功能

class PermissionChecker:
    """权限检查器"""
    
    @staticmethod
    def check(required_level: int, user_level: int) -> bool:
        """检查权限"""
        return user_level >= required_level
    
    @staticmethod
    def require_multi_confirmation(trade_amount: float) -> bool:
        """是否需要多重确认"""
        thresholds = {
            100000: 1,   # 10万以上需要1次确认
            500000: 2,   # 50万以上需要2次确认
            1000000: 3,  # 100万以上需要3次确认
        }
        
        confirmations = 0
        for threshold, count in thresholds.items():
            if trade_amount >= threshold:
                confirmations = max(confirmations, count)
        
        return confirmations
```

---

### 7. 多模型协同 ⭐⭐⭐⭐

**目标**: 不同任务分配给最擅长的模型

```python
class ModelRouter:
    """模型路由 - 借鉴Claude Code的多Agent模型分配"""
    
    MODEL_CONFIG = {
        'fundamental_analysis': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'reasoning': True,
            'temperature': 0.3,
        },
        'technical_analysis': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'reasoning': True,
            'temperature': 0.5,
        },
        'sentiment_analysis': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'reasoning': True,
            'temperature': 0.7,
        },
        'risk_assessment': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'reasoning': True,
            'temperature': 0.2,
        },
        'final_decision': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'reasoning': True,
            'temperature': 0.4,
        },
    }
    
    async def route(self, task_type: str, prompt: str) -> str:
        """路由到合适的模型"""
        config = self.MODEL_CONFIG.get(task_type, self.MODEL_CONFIG['final_decision'])
        
        client = ModelManager.get_client(config['provider'])
        response = await client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=get_system_prompt(task_type),
            temperature=config['temperature']
        )
        
        return response
```

---

## 三、实施计划

### Phase 1: 工具系统化 (1周)
- [ ] 定义 BaseTool 基类
- [ ] 实现核心工具类
- [ ] 建立工具注册表
- [ ] 重构现有 Agent 使用工具系统

### Phase 2: 生命周期钩子 (1周)
- [ ] 实现 HookManager
- [ ] 编写预置钩子（风控、权限、日志）
- [ ] 集成到现有系统

### Phase 3: 上下文压缩 (3天)
- [ ] 实现 ContextCompactor
- [ ] 集成到 Agent 对话流程
- [ ] 验证压缩效果

### Phase 4: Feature Flags (3天)
- [ ] 实现 FeatureFlags 类
- [ ] 集成 GrowthBook API
- [ ] 支持 A/B 测试

### Phase 5: Analytics (1周)
- [ ] 实现 AnalyticsTracker
- [ ] 建立 Dashboard
- [ ] 自动化报告生成

---

## 四、架构对比

### 优化前
```
User -> Coordinator -> [Agent1, Agent2, Agent3] -> Decision
                                    ↓
                              硬编码逻辑
```

### 优化后
```
User -> Coordinator -> ToolRegistry 
                      -> HookManager (pre/post)
                      -> AnalyticsTracker
                      -> FeatureFlags
                      -> [Agent1(Tool1), Agent2(Tool2), Agent3(Tool3)]
                          ↓
                    ContextCompactor
                          ↓
                      Decision
                          ↓
                    PermissionCheck -> Trade
```

---

## 五、核心价值

| 优化点 | 价值 |
|-------|-----|
| 工具系统化 | 提高复用性，标准化接口 |
| Hook系统 | 灵活插入风控、权限逻辑 |
| 上下文压缩 | 支持更长周期的分析 |
| Feature Flags | 支持灰度发布，降低风险 |
| Analytics | 数据驱动，持续优化 |
| 权限分级 | 安全第一，大额交易多重确认 |

---

*优化方案基于 Claude Code 架构设计*
*贾维斯量化系统 v3.0*
