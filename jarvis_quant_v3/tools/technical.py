"""
技术分析工具
提供各种技术指标计算和分析
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from .base import BaseTool, PermissionLevel
from .stock_data import StockDataTool


class TechnicalAnalysisTool(BaseTool):
    """技术分析工具"""
    
    def __init__(self):
        """初始化技术分析工具"""
        super().__init__(
            name="technical_analysis",
            description="技术指标计算和分析，包括MACD、RSI、KDJ、布林带等",
            version="1.0.0"
        )
        self.stock_tool = StockDataTool()
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行技术分析
        
        Args:
            stock_code: 股票代码
            indicators: 技术指标列表 (如 ['MACD', 'RSI', 'KDJ', 'BOLL'])
            period: 分析周期 ('daily', 'weekly', 'monthly')
            lookback_days: 回看天数 (默认250)
            
        Returns:
            技术分析结果
        """
        try:
            stock_code = kwargs.get('stock_code')
            indicators = kwargs.get('indicators', ['MACD', 'RSI', 'KDJ', 'BOLL'])
            period = kwargs.get('period', 'daily')
            lookback_days = kwargs.get('lookback_days', 250)
            
            if not stock_code:
                return {
                    "success": False,
                    "error": "股票代码不能为空",
                    "data": None
                }
            
            # 获取历史数据
            end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=lookback_days)).strftime('%Y-%m-%d')
            
            stock_data = self.stock_tool.execute(
                operation='history',
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                period=period
            )
            
            if not stock_data['success']:
                return stock_data
            
            # 转换为DataFrame
            df = pd.DataFrame(stock_data['data']['data'])
            if df.empty:
                return {
                    "success": False,
                    "error": "没有可用的历史数据",
                    "data": None
                }
            
            # 确保列名正确
            df.columns = [col.strip() for col in df.columns]
            
            # 重命名列
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '换手率': 'turnover'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # 确保必要的列存在
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    return {
                        "success": False,
                        "error": f"数据缺少必要列: {col}",
                        "data": None
                    }
            
            # 转换数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # 计算技术指标
            results = {}
            for indicator in indicators:
                if indicator == 'MACD':
                    results['MACD'] = self._calculate_macd(df)
                elif indicator == 'RSI':
                    results['RSI'] = self._calculate_rsi(df)
                elif indicator == 'KDJ':
                    results['KDJ'] = self._calculate_kdj(df)
                elif indicator == 'BOLL':
                    results['BOLL'] = self._calculate_boll(df)
                elif indicator == 'MA':
                    results['MA'] = self._calculate_ma(df)
                elif indicator == 'VOLUME':
                    results['VOLUME'] = self._analyze_volume(df)
            
            # 生成技术信号
            signals = self._generate_signals(df, results)
            
            return {
                "success": True,
                "data": {
                    "stock_code": stock_code,
                    "period": period,
                    "lookback_days": lookback_days,
                    "indicators": results,
                    "signals": signals,
                    "latest_data": df.iloc[-1].to_dict() if not df.empty else {},
                    "summary": self._generate_summary(signals)
                },
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"技术分析失败: {str(e)}",
                "data": None
            }
    
    def get_permission_level(self) -> PermissionLevel:
        """获取权限级别"""
        return PermissionLevel.MEDIUM
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        return {
            "type": "object",
            "properties": {
                "stock_code": {
                    "type": "string",
                    "description": "股票代码"
                },
                "indicators": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["MACD", "RSI", "KDJ", "BOLL", "MA", "VOLUME"]
                    },
                    "description": "技术指标列表"
                },
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "分析周期"
                },
                "lookback_days": {
                    "type": "integer",
                    "minimum": 30,
                    "maximum": 1000,
                    "description": "回看天数"
                }
            },
            "required": ["stock_code"]
        }
    
    def _get_tags(self) -> List[str]:
        """获取标签"""
        return ["technical", "analysis", "indicators", "trading"]
    
    def _calculate_macd(self, df: pd.DataFrame, 
                       fast_period: int = 12, 
                       slow_period: int = 26, 
                       signal_period: int = 9) -> Dict[str, Any]:
        """计算MACD指标"""
        close = df['close']
        
        # 计算EMA
        ema_fast = close.ewm(span=fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=slow_period, adjust=False).mean()
        
        # 计算DIF和DEA
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal_period, adjust=False).mean()
        macd = (dif - dea) * 2
        
        # 生成信号
        signals = []
        for i in range(1, len(df)):
            if dif.iloc[i] > dea.iloc[i] and dif.iloc[i-1] <= dea.iloc[i-1]:
                signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "BUY"})
            elif dif.iloc[i] < dea.iloc[i] and dif.iloc[i-1] >= dea.iloc[i-1]:
                signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "SELL"})
        
        return {
            "DIF": dif.iloc[-20:].tolist(),
            "DEA": dea.iloc[-20:].tolist(),
            "MACD": macd.iloc[-20:].tolist(),
            "current_dif": float(dif.iloc[-1]),
            "current_dea": float(dea.iloc[-1]),
            "current_macd": float(macd.iloc[-1]),
            "signals": signals[-5:] if signals else [],
            "trend": "BULLISH" if dif.iloc[-1] > dea.iloc[-1] else "BEARISH"
        }
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """计算RSI指标"""
        close = df['close']
        delta = close.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 生成信号
        signals = []
        for i in range(1, len(df)):
            if pd.notna(rsi.iloc[i]):
                if rsi.iloc[i] < 30 and rsi.iloc[i-1] >= 30:
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "OVERSOLD_BUY"})
                elif rsi.iloc[i] > 70 and rsi.iloc[i-1] <= 70:
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "OVERBOUGHT_SELL"})
        
        return {
            "RSI": rsi.iloc[-20:].tolist(),
            "current_rsi": float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None,
            "signals": signals[-5:] if signals else [],
            "status": self._get_rsi_status(float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None)
        }
    
    def _calculate_kdj(self, df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> Dict[str, Any]:
        """计算KDJ指标"""
        low_min = df['low'].rolling(window=n).min()
        high_max = df['high'].rolling(window=n).max()
        
        rsv = 100 * ((df['close'] - low_min) / (high_max - low_min))
        rsv = rsv.fillna(50)
        
        k = rsv.ewm(alpha=1/m1, adjust=False).mean()
        d = k.ewm(alpha=1/m2, adjust=False).mean()
        j = 3 * k - 2 * d
        
        # 生成信号
        signals = []
        for i in range(1, len(df)):
            if pd.notna(k.iloc[i]) and pd.notna(d.iloc[i]):
                if k.iloc[i] > d.iloc[i] and k.iloc[i-1] <= d.iloc[i-1]:
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "GOLDEN_CROSS_BUY"})
                elif k.iloc[i] < d.iloc[i] and k.iloc[i-1] >= d.iloc[i-1]:
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "DEATH_CROSS_SELL"})
        
        return {
            "K": k.iloc[-20:].tolist(),
            "D": d.iloc[-20:].tolist(),
            "J": j.iloc[-20:].tolist(),
            "current_k": float(k.iloc[-1]) if pd.notna(k.iloc[-1]) else None,
            "current_d": float(d.iloc[-1]) if pd.notna(d.iloc[-1]) else None,
            "current_j": float(j.iloc[-1]) if pd.notna(j.iloc[-1]) else None,
            "signals": signals[-5:] if signals else [],
            "trend": "BULLISH" if k.iloc[-1] > d.iloc[-1] else "BEARISH"
        }
    
    def _calculate_boll(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, Any]:
        """计算布林带指标"""
        close = df['close']
        
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        # 生成信号
        signals = []
        for i in range(1, len(df)):
            if pd.notna(upper.iloc[i]) and pd.notna(lower.iloc[i]):
                if close.iloc[i] < lower.iloc[i] and close.iloc[i-1] >= lower.iloc[i-1]:
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "LOWER_BAND_BUY"})
                elif close.iloc[i] > upper.iloc[i] and close.iloc[i-1] <= upper.iloc[i-1]:
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "UPPER_BAND_SELL"})
        
        return {
            "upper": upper.iloc[-20:].tolist(),
            "middle": middle.iloc[-20:].tolist(),
            "lower": lower.iloc[-20:].tolist(),
            "current_price": float(close.iloc[-1]),
            "current_upper": float(upper.iloc[-1]) if pd.notna(upper.iloc[-1]) else None,
            "current_middle": float(middle.iloc[-1]) if pd.notna(middle.iloc[-1]) else None,
            "current_lower": float(lower.iloc[-1]) if pd.notna(lower.iloc[-1]) else None,
            "band_width": ((upper.iloc[-1] - lower.iloc[-1]) / middle.iloc[-1]) if pd.notna(middle.iloc[-1]) else None,
            "signals": signals[-5:] if signals else [],
            "position": self._get_boll_position(float(close.iloc[-1]), 
                                               float(upper.iloc[-1]) if pd.notna(upper.iloc[-1]) else None,
                                               float(lower.iloc[-1]) if pd.notna(lower.iloc[-1]) else None)
        }
    
    def _calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> Dict[str, Any]:
        """计算移动平均线"""
        close = df['close']
        
        ma_results = {}
        for period in periods:
            ma = close.rolling(window=period).mean()
            ma_results[f"MA{period}"] = {
                "values": ma.iloc[-20:].tolist(),
                "current": float(ma.iloc[-1]) if pd.notna(ma.iloc[-1]) else None
            }
        
        # 检查均线排列
        current_prices = {f"MA{period}": ma_results[f"MA{period}"]["current"] for period in periods}
        sorted_mas = sorted([(period, price) for period, price in current_prices.items() if price is not None], 
                           key=lambda x: x[1], reverse=True)
        
        return {
            "moving_averages": ma_results,
            "arrangement": [period for period, _ in sorted_mas],
            "trend": "BULLISH" if len(sorted_mas) >= 2 and sorted_mas[0][0] == "MA5" else "BEARISH"
        }
    
    def _analyze_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析成交量"""
        volume = df['volume']
        close = df['close']
        
        # 计算成交量均线
        volume_ma5 = volume.rolling(window=5).mean()
        volume_ma10 = volume.rolling(window=10).mean()
        
        # 量价关系分析
        price_change = close.pct_change()
        volume_change = volume.pct_change()
        
        # 生成信号
        signals = []
        for i in range(1, len(df)):
            if pd.notna(price_change.iloc[i]) and pd.notna(volume_change.iloc[i]):
                if price_change.iloc[i] > 0 and volume_change.iloc[i] > 0.5:  # 价涨量增
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "VOLUME_CONFIRM_BUY"})
                elif price_change.iloc[i] < 0 and volume_change.iloc[i] > 0.5:  # 价跌量增
                    signals.append({"date": df['date'].iloc[i].strftime('%Y-%m-%d'), "signal": "VOLUME_CONFIRM_SELL"})
        
        return {
            "current_volume": float(volume.iloc[-1]),
            "volume_ma5": float(volume_ma5.iloc[-1]) if pd.notna(volume_ma5.iloc[-1]) else None,
            "volume_ma10": float(volume_ma10.iloc[-1]) if pd.notna(volume_ma10.iloc[-1]) else None,
            "volume_ratio": float(volume.iloc[-1] / volume_ma5.iloc[-1]) if pd.notna(volume_ma5.iloc[-1]) else None,
            "signals": signals[-5:] if signals else [],
            "status": "HIGH_VOLUME" if volume.iloc[-1] > volume_ma5.iloc[-1] * 1.5 else "NORMAL_VOLUME"
        }
    
    def _generate_signals(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成综合技术信号"""
        signals = []
        
        # 从各个指标中收集信号
        for indicator_name, indicator_data in indicators.items():
            if 'signals' in indicator_data:
                for signal in indicator_data['signals']:
                    signals.append({
                        **signal,
                        "indicator": indicator_name
                    })
        
        # 按日期排序
        signals.sort(key=lambda x: x['date'])
        
        return signals[-10:]  # 返回最近10个信号
    
    def _generate_summary(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成技术分析摘要"""
        if not signals:
            return {"overall": "NEUTRAL", "confidence": 0.5, "recommendation": "HOLD"}
        
        # 统计信号类型
        buy_signals = [s for s in signals if 'BUY' in s['signal']]
        sell_signals = [s for s in signals if 'SELL' in s['signal']]
        
        buy_count = len(buy_signals)
        sell_count = len(sell_signals)
        
        # 计算总体信号
        if buy_count > sell_count * 1.5:
            overall = "BULLISH"
            confidence = min(0.9, buy_count / (buy_count + sell_count))
            recommendation = "BUY"
        elif sell_count > buy_count * 1.5:
            overall = "BEARISH"
            confidence = min(0.9, sell_count / (buy_count + sell_count))
            recommendation = "SELL"
        else:
            overall = "NEUTRAL"
            confidence = 0.5
            recommendation = "HOLD"
        
        return {
            "overall": overall,
            "confidence": round(confidence, 2),
            "recommendation": recommendation,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "total_signals": len(signals),
            "latest_signal": signals[-1] if signals else None
        }
    
    def _get_rsi_status(self, rsi_value: Optional[float]) -> str:
        """获取RSI状态"""
        if rsi_value is None:
            return "UNKNOWN"
        elif rsi_value < 30:
            return "OVERSOLD"
        elif rsi_value > 70:
            return "OVERBOUGHT"
        elif 30 <= rsi_value <= 40:
            return "NEAR_OVERSOLD"
        elif 60 <= rsi_value <= 70:
            return "NEAR_OVERBOUGHT"
        else:
            return "NORMAL"
    
    def _get_boll_position(self, price: float, upper: Optional[float], lower: Optional[float]) -> str:
        """获取布林带位置"""
        if upper is None or lower is None:
            return "UNKNOWN"
        
        band_width = upper - lower
        if band_width == 0:
            return "UNKNOWN"
        
        position = (price - lower) / band_width
        
        if position < 0.2:
            return "LOWER_BAND"
        elif position > 0.8:
            return "UPPER_BAND"
        elif 0.2 <= position <= 0.3:
            return "NEAR_LOWER_BAND"
        elif 0.7 <= position <= 0.8:
            return "NEAR_UPPER_BAND"
        else:
            return "MIDDLE_BAND"