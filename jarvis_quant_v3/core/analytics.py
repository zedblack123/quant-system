"""
分析跟踪器 (AnalyticsTracker)
用于跟踪系统性能指标和智能体调用统计
"""

import json
import sqlite3
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """智能体类型枚举"""
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    RISK = "risk"
    COORDINATOR = "coordinator"
    UNKNOWN = "unknown"


class TradeDirection(Enum):
    """交易方向枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class AgentMetrics:
    """智能体指标数据类"""
    agent_type: str
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_response_time: float = 0.0  # 总响应时间（秒）
    avg_response_time: float = 0.0    # 平均响应时间
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    total_tokens_used: int = 0
    avg_tokens_per_call: float = 0.0
    last_called: Optional[datetime] = None
    
    def update(self, success: bool, response_time: float, tokens_used: int = 0) -> None:
        """
        更新指标
        
        Args:
            success: 是否成功
            response_time: 响应时间（秒）
            tokens_used: 使用的token数量
        """
        self.call_count += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        self.total_response_time += response_time
        self.avg_response_time = self.total_response_time / self.call_count
        self.min_response_time = min(self.min_response_time, response_time)
        self.max_response_time = max(self.max_response_time, response_time)
        
        self.total_tokens_used += tokens_used
        self.avg_tokens_per_call = self.total_tokens_used / self.call_count
        
        self.last_called = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['success_rate'] = self.success_count / self.call_count if self.call_count > 0 else 0.0
        result['failure_rate'] = self.failure_count / self.call_count if self.call_count > 0 else 0.0
        return result


@dataclass
class TradeMetrics:
    """交易指标数据类"""
    trade_id: str
    symbol: str
    direction: str
    quantity: int
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    pnl_percentage: float = 0.0
    commission: float = 0.0
    strategy: str = "unknown"
    risk_level: str = "medium"
    status: str = "open"  # open, closed, cancelled
    
    def close(self, exit_price: float, exit_time: Optional[datetime] = None) -> None:
        """
        关闭交易
        
        Args:
            exit_price: 退出价格
            exit_time: 退出时间，如果为None则使用当前时间
        """
        self.exit_price = exit_price
        self.exit_time = exit_time or datetime.now()
        self.status = "closed"
        
        # 计算盈亏
        if self.direction == "buy":
            self.pnl = (exit_price - self.entry_price) * self.quantity - self.commission
        else:  # sell
            self.pnl = (self.entry_price - exit_price) * self.quantity - self.commission
        
        self.pnl_percentage = (self.pnl / (self.entry_price * self.quantity)) * 100 if self.entry_price > 0 else 0.0


class AnalyticsTracker:
    """
    分析跟踪器
    跟踪系统性能指标和智能体调用统计
    """
    
    def __init__(self, db_path: str = "analytics.db"):
        """
        初始化分析跟踪器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.trade_metrics: Dict[str, TradeMetrics] = {}
        self._init_database()
        self._load_from_database()
        
        # 初始化默认智能体指标
        self._init_default_agents()
    
    def _init_database(self) -> None:
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建智能体指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_type TEXT NOT NULL,
                    call_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    total_response_time REAL DEFAULT 0.0,
                    avg_response_time REAL DEFAULT 0.0,
                    min_response_time REAL DEFAULT 0.0,
                    max_response_time REAL DEFAULT 0.0,
                    total_tokens_used INTEGER DEFAULT 0,
                    avg_tokens_per_call REAL DEFAULT 0.0,
                    last_called TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建交易指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_metrics (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    pnl REAL DEFAULT 0.0,
                    pnl_percentage REAL DEFAULT 0.0,
                    commission REAL DEFAULT 0.0,
                    strategy TEXT,
                    risk_level TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建系统指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"分析数据库已初始化: {self.db_path}")
            
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
    
    def _load_from_database(self) -> None:
        """从数据库加载数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 加载智能体指标
            cursor.execute('SELECT * FROM agent_metrics')
            rows = cursor.fetchall()
            
            for row in rows:
                agent_type = row[1]
                metrics = AgentMetrics(
                    agent_type=agent_type,
                    call_count=row[2],
                    success_count=row[3],
                    failure_count=row[4],
                    total_response_time=row[5],
                    avg_response_time=row[6],
                    min_response_time=row[7],
                    max_response_time=row[8],
                    total_tokens_used=row[9],
                    avg_tokens_per_call=row[10],
                    last_called=datetime.fromisoformat(row[11]) if row[11] else None
                )
                self.agent_metrics[agent_type] = metrics
            
            # 加载交易指标
            cursor.execute('SELECT * FROM trade_metrics')
            rows = cursor.fetchall()
            
            for row in rows:
                trade_id = row[0]
                trade = TradeMetrics(
                    trade_id=trade_id,
                    symbol=row[1],
                    direction=row[2],
                    quantity=row[3],
                    entry_price=row[4],
                    exit_price=row[5],
                    entry_time=datetime.fromisoformat(row[6]),
                    exit_time=datetime.fromisoformat(row[7]) if row[7] else None,
                    pnl=row[8],
                    pnl_percentage=row[9],
                    commission=row[10],
                    strategy=row[11],
                    risk_level=row[12],
                    status=row[13]
                )
                self.trade_metrics[trade_id] = trade
            
            conn.close()
            logger.info(f"从数据库加载了 {len(self.agent_metrics)} 个智能体指标和 {len(self.trade_metrics)} 个交易指标")
            
        except Exception as e:
            logger.error(f"从数据库加载数据失败: {e}")
    
    def _init_default_agents(self) -> None:
        """初始化默认智能体指标"""
        default_agents = [
            AgentType.FUNDAMENTAL.value,
            AgentType.TECHNICAL.value,
            AgentType.SENTIMENT.value,
            AgentType.RISK.value,
            AgentType.COORDINATOR.value
        ]
        
        for agent_type in default_agents:
            if agent_type not in self.agent_metrics:
                self.agent_metrics[agent_type] = AgentMetrics(agent_type=agent_type)
    
    def record_agent_call(
        self,
        agent_type: str,
        success: bool,
        response_time: float,
        tokens_used: int = 0
    ) -> None:
        """
        记录智能体调用
        
        Args:
            agent_type: 智能体类型
            success: 是否成功
            response_time: 响应时间（秒）
            tokens_used: 使用的token数量
        """
        if agent_type not in self.agent_metrics:
            self.agent_metrics[agent_type] = AgentMetrics(agent_type=agent_type)
        
        metrics = self.agent_metrics[agent_type]
        metrics.update(success, response_time, tokens_used)
        
        # 保存到数据库
        self._save_agent_metrics(metrics)
        
        logger.debug(f"记录智能体调用: {agent_type}, 成功: {success}, 响应时间: {response_time:.3f}s")
    
    def record_trade(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        quantity: int,
        entry_price: float,
        commission: float = 0.0,
        strategy: str = "unknown",
        risk_level: str = "medium"
    ) -> None:
        """
        记录交易
        
        Args:
            trade_id: 交易ID
            symbol: 交易标的
            direction: 交易方向 (buy/sell)
            quantity: 数量
            entry_price: 入场价格
            commission: 手续费
            strategy: 策略名称
            risk_level: 风险等级
        """
        trade = TradeMetrics(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            entry_price=entry_price,
            commission=commission,
            strategy=strategy,
            risk_level=risk_level
        )
        
        self.trade_metrics[trade_id] = trade
        
        # 保存到数据库
        self._save_trade_metrics(trade)
        
        logger.info(f"记录交易: {trade_id}, {symbol} {direction} {quantity}@{entry_price}")
    
    def update_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: Optional[datetime] = None
    ) -> Optional[TradeMetrics]:
        """
        更新交易（平仓）
        
        Args:
            trade_id: 交易ID
            exit_price: 退出价格
            exit_time: 退出时间
            
        Returns:
            更新后的交易指标，如果交易不存在则返回None
        """
        if trade_id not in self.trade_metrics:
            logger.warning(f"交易不存在: {trade_id}")
            return None
        
        trade = self.trade_metrics[trade_id]
        trade.close(exit_price, exit_time)
        
        # 更新数据库
        self._save_trade_metrics(trade)
        
        logger.info(f"更新交易: {trade_id}, 盈亏: {trade.pnl:.2f} ({trade.pnl_percentage:.2f}%)")
        
        return trade
    
    def generate_report(
        self,
        report_type: str = "summary",
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        生成分析报告
        
        Args:
            report_type: 报告类型 (summary, detailed, agent, trade)
            time_range: 时间范围
            
        Returns:
            分析报告字典
        """
        if report_type == "summary":
            return self._generate_summary_report()
        elif report_type == "detailed":
            return self._generate_detailed_report(time_range)
        elif report_type == "agent":
            return self._generate_agent_report()
        elif report_type == "trade":
            return self._generate_trade_report(time_range)
        else:
            logger.warning(f"未知的报告类型: {report_type}")
            return {"error": f"未知的报告类型: {report_type}"}
    
    def _generate_summary_report(self) -> Dict[str, Any]:
        """生成摘要报告"""
        total_calls = sum(m.call_count for m in self.agent_metrics.values())
        total_success = sum(m.success_count for m in self.agent_metrics.values())
        overall_success_rate = total_success / total_calls if total_calls > 0 else 0.0
        
        open_trades = [t for t in self.trade_metrics.values() if t.status == "open"]
        closed_trades = [t for t in self.trade_metrics.values() if t.status == "closed"]
        
        total_pnl = sum(t.pnl for t in closed_trades)
        avg_pnl = total_pnl / len(closed_trades) if closed_trades else 0.0
        
        return {
            "report_type": "summary",
            "timestamp": datetime.now().isoformat(),
            "agent_metrics": {
                "total_calls": total_calls,
                "total_success": total_success,
                "overall_success_rate": overall_success_rate,
                "agent_count": len(self.agent_metrics)
            },
            "trade_metrics": {
                "total_trades": len(self.trade_metrics),
                "open_trades": len(open_trades),
                "closed_trades": len(closed_trades),
                "total_pnl": total_pnl,
                "avg_pnl": avg_pnl
            },
            "system_status": "healthy" if overall_success_rate > 0.8 else "warning"
        }
    
    def _generate_detailed_report(self, time_range: Optional[Tuple[datetime, datetime]]) -> Dict[str, Any]:
        """生成详细报告"""
        summary = self._generate_summary_report()
        
        # 添加详细的智能体指标
        agent_details = {}
        for agent_type, metrics in self.agent_metrics.items():
            agent_details[agent_type] = metrics.to_dict()
        
        # 添加交易详情
        trade_details = []
        for trade in self.trade_metrics.values():
            trade_dict = asdict(trade)
            trade_details.append(trade_dict)
        
        summary["agent_details"] = agent_details
        summary["trade_details"] = trade_details
        
        return summary
    
    def _generate_agent_report(self) -> Dict[str, Any]:
        """生成智能体报告"""
        report = {
            "report_type": "agent",
            "timestamp": datetime.now().isoformat(),
            "agents": {}
        }
        
        for agent_type, metrics in self.agent_metrics.items():
            report["agents"][agent_type] = metrics.to_dict()
        
        return report
    
    def _generate_trade_report(self, time_range: Optional[Tuple[datetime, datetime]]) -> Dict[str, Any]:
        """生成交易报告"""
        # 过滤时间范围内的交易
        filtered_trades = []
        if time_range:
            start_time, end_time = time_range
            for trade in self.trade_metrics.values():
                if start_time <= trade.entry_time <= end_time:
                    filtered_trades.append(trade)
        else:
            filtered_trades = list(self.trade_metrics.values())
        
        # 按状态分组
        open_trades = [t for t in filtered_trades if t.status == "open"]
        closed_trades = [t for t in filtered_trades if t.status == "closed"]
        
        # 计算统计指标
        total_pnl = sum(t.pnl for t in closed_trades)
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0.0
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        return {
            "report_type": "trade",
            "timestamp": datetime.now().isoformat(),
            "time_range": {
                "start": time_range[0].isoformat() if time_range else None,
                "end": time_range[1].isoformat() if time_range else None
            },
            "summary": {
                "total_trades": len(filtered_trades),
                "open_trades": len(open_trades),
                "closed_trades": len(closed_trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "total_pnl": total_pnl,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            },
            "trades": [asdict(t) for t in filtered_trades]
        }
    
    def _save_agent_metrics(self, metrics: AgentMetrics) -> None:
        """保存智能体指标到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                'SELECT id FROM agent_metrics WHERE agent_type = ?',
                (metrics.agent_type,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新
                cursor.execute('''
                    UPDATE agent_metrics SET
                        call_count = ?,
                        success_count = ?,
                        failure_count = ?,
                        total_response_time = ?,
                        avg_response_time = ?,
                        min_response_time = ?,
                        max_response_time = ?,
                        total_tokens_used = ?,
                        avg_tokens_per_call = ?,
                        last_called = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE agent_type = ?
                ''', (
                    metrics.call_count,
                    metrics.success_count,
                    metrics.failure_count,
                    metrics.total_response_time,
                    metrics.avg_response_time,
                    metrics.min_response_time,
                    metrics.max_response_time,
                    metrics.total_tokens_used,
                    metrics.avg_tokens_per_call,
                    metrics.last_called.isoformat() if metrics.last_called else None,
                    metrics.agent_type
                ))
            else:
                # 插入
                cursor.execute('''
                    INSERT INTO agent_metrics (
                        agent_type, call_count, success_count, failure_count,
                        total_response_time, avg_response_time, min_response_time,
                        max_response_time, total_tokens_used, avg_tokens_per_call,
                        last_called
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.agent_type,
                    metrics.call_count,
                    metrics.success_count,
                    metrics.failure_count,
                    metrics.total_response_time,
                    metrics.avg_response_time,
                    metrics.min_response_time,
                    metrics.max_response_time,
                    metrics.total_tokens_used,
                    metrics.avg_tokens_per_call,
                    metrics.last_called.isoformat() if metrics.last_called else None
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存智能体指标失败: {e}")
    
    def _save_trade_metrics(self, trade: TradeMetrics) -> None:
        """保存交易指标到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                'SELECT trade_id FROM trade_metrics WHERE trade_id = ?',
                (trade.trade_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新
                cursor.execute('''
                    UPDATE trade_metrics SET
                        symbol = ?,
                        direction = ?,
                        quantity = ?,
                        entry_price = ?,
                        exit_price = ?,
                        entry_time = ?,
                        exit_time = ?,
                        pnl = ?,
                        pnl_percentage = ?,
                        commission = ?,
                        strategy = ?,
                        risk_level = ?,
                        status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE trade_id = ?
                ''', (
                    trade.symbol,
                    trade.direction,
                    trade.quantity,
                    trade.entry_price,
                    trade.exit_price,
                    trade.entry_time.isoformat(),
                    trade.exit_time.isoformat() if trade.exit_time else None,
                    trade.pnl,
                    trade.pnl_percentage,
                    trade.commission,
                    trade.strategy,
                    trade.risk_level,
                    trade.status,
                    trade.trade_id
                ))
            else:
                # 插入
                cursor.execute('''
                    INSERT INTO trade_metrics (
                        trade_id, symbol, direction, quantity, entry_price,
                        exit_price, entry_time, exit_time, pnl, pnl_percentage,
                        commission, strategy, risk_level, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.trade_id,
                    trade.symbol,
                    trade.direction,
                    trade.quantity,
                    trade.entry_price,
                    trade.exit_price,
                    trade.entry_time.isoformat(),
                    trade.exit_time.isoformat() if trade.exit_time else None,
                    trade.pnl,
                    trade.pnl_percentage,
                    trade.commission,
                    trade.strategy,
                    trade.risk_level,
                    trade.status
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存交易指标失败: {e}")
    
    def record_system_metric(self, metric_name: str, metric_value: float) -> None:
        """
        记录系统指标
        
        Args:
            metric_name: 指标名称
            metric_value: 指标值
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics (metric_name, metric_value)
                VALUES (?, ?)
            ''', (metric_name, metric_value))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"记录系统指标: {metric_name} = {metric_value}")
            
        except Exception as e:
            logger.error(f"记录系统指标失败: {e}")
    
    def get_system_metrics(
        self,
        metric_name: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取系统指标
        
        Args:
            metric_name: 指标名称，如果为None则获取所有指标
            time_range: 时间范围
            
        Returns:
            系统指标列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = 'SELECT metric_name, metric_value, timestamp FROM system_metrics'
            params = []
            
            conditions = []
            if metric_name:
                conditions.append('metric_name = ?')
                params.append(metric_name)
            
            if time_range:
                start_time, end_time = time_range
                conditions.append('timestamp BETWEEN ? AND ?')
                params.extend([start_time.isoformat(), end_time.isoformat()])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY timestamp DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            return [
                {
                    'metric_name': row[0],
                    'metric_value': row[1],
                    'timestamp': datetime.fromisoformat(row[2])
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return []
    
    def clear_old_data(self, days_to_keep: int = 30) -> int:
        """
        清理旧数据
        
        Args:
            days_to_keep: 保留天数
            
        Returns:
            删除的记录数
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除旧的系统指标
            cursor.execute(
                'DELETE FROM system_metrics WHERE timestamp < ?',
                (cutoff_date.isoformat(),)
            )
            system_deleted = cursor.rowcount
            
            # 删除旧的已完成交易（保留30天以上但已完成的交易）
            cursor.execute(
                'DELETE FROM trade_metrics WHERE status = "closed" AND entry_time < ?',
                (cutoff_date.isoformat(),)
            )
            trade_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            total_deleted = system_deleted + trade_deleted
            logger.info(f"清理了 {total_deleted} 条旧数据（系统指标: {system_deleted}, 交易: {trade_deleted}）")
            
            return total_deleted
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return 0


# 全局分析跟踪器实例
analytics_tracker = AnalyticsTracker()