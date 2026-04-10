"""
风险计算工具
计算投资组合风险指标和风险评估
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
from .base import BaseTool, PermissionLevel
from .stock_data import StockDataTool


class RiskCalcTool(BaseTool):
    """风险计算工具"""
    
    def __init__(self):
        """初始化风险计算工具"""
        super().__init__(
            name="risk_calculation",
            description="计算投资组合风险指标、风险评估和压力测试",
            version="1.0.0"
        )
        self.stock_tool = StockDataTool()
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行风险计算
        
        Args:
            operation: 操作类型 ('portfolio_risk', 'var', 'cvar', 'stress_test', 'risk_assessment')
            portfolio: 投资组合字典 {股票代码: 权重}
            confidence_level: 置信水平 (默认0.95)
            time_horizon: 时间周期 (天，默认1)
            historical_days: 历史数据天数 (默认250)
            market_condition: 市场条件 ('normal', 'crisis', 'recovery')
            
        Returns:
            风险计算结果
        """
        try:
            operation = kwargs.get('operation', 'portfolio_risk')
            
            if operation == 'portfolio_risk':
                result = self._calculate_portfolio_risk(**kwargs)
            elif operation == 'var':
                result = self._calculate_var(**kwargs)
            elif operation == 'cvar':
                result = self._calculate_cvar(**kwargs)
            elif operation == 'stress_test':
                result = self._stress_test(**kwargs)
            elif operation == 'risk_assessment':
                result = self._risk_assessment(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作类型: {operation}",
                    "data": None
                }
            
            return {
                "success": True,
                "data": result,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"风险计算失败: {str(e)}",
                "data": None
            }
    
    def get_permission_level(self) -> PermissionLevel:
        """获取权限级别"""
        return PermissionLevel.HIGH
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["portfolio_risk", "var", "cvar", "stress_test", "risk_assessment"],
                    "description": "操作类型"
                },
                "portfolio": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "description": "投资组合 {股票代码: 权重}"
                },
                "confidence_level": {
                    "type": "number",
                    "minimum": 0.5,
                    "maximum": 0.999,
                    "description": "置信水平"
                },
                "time_horizon": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 365,
                    "description": "时间周期 (天)"
                },
                "historical_days": {
                    "type": "integer",
                    "minimum": 30,
                    "maximum": 1000,
                    "description": "历史数据天数"
                },
                "market_condition": {
                    "type": "string",
                    "enum": ["normal", "crisis", "recovery"],
                    "description": "市场条件"
                },
                "portfolio_value": {
                    "type": "number",
                    "minimum": 0,
                    "description": "投资组合价值 (用于VaR计算)"
                }
            },
            "required": ["operation"]
        }
    
    def _get_tags(self) -> List[str]:
        """获取标签"""
        return ["risk", "portfolio", "var", "cvar", "stress_test", "financial"]
    
    def _calculate_portfolio_risk(self, **kwargs) -> Dict[str, Any]:
        """计算投资组合风险"""
        portfolio = kwargs.get('portfolio', {})
        historical_days = kwargs.get('historical_days', 250)
        
        if not portfolio:
            return {"error": "投资组合不能为空"}
        
        # 获取各股票的历史收益率
        returns_data = {}
        for stock_code, weight in portfolio.items():
            returns = self._get_stock_returns(stock_code, historical_days)
            if returns is not None:
                returns_data[stock_code] = returns
        
        if not returns_data:
            return {"error": "无法获取股票收益率数据"}
        
        # 创建收益率DataFrame
        returns_df = pd.DataFrame(returns_data)
        
        # 计算基本统计量
        portfolio_stats = self._calculate_portfolio_statistics(returns_df, portfolio)
        
        # 计算风险指标
        risk_metrics = self._calculate_risk_metrics(returns_df, portfolio)
        
        # 计算相关性矩阵
        correlation_matrix = returns_df.corr().round(3).to_dict()
        
        # 风险评估
        risk_assessment = self._assess_portfolio_risk(portfolio_stats, risk_metrics)
        
        return {
            "portfolio": portfolio,
            "statistics": portfolio_stats,
            "risk_metrics": risk_metrics,
            "correlation_matrix": correlation_matrix,
            "risk_assessment": risk_assessment,
            "historical_days": historical_days,
            "analysis_date": pd.Timestamp.now().strftime('%Y-%m-%d')
        }
    
    def _calculate_var(self, **kwargs) -> Dict[str, Any]:
        """计算在险价值 (VaR)"""
        portfolio = kwargs.get('portfolio', {})
        confidence_level = kwargs.get('confidence_level', 0.95)
        time_horizon = kwargs.get('time_horizon', 1)
        portfolio_value = kwargs.get('portfolio_value', 1000000)  # 默认100万
        historical_days = kwargs.get('historical_days', 250)
        
        if not portfolio:
            return {"error": "投资组合不能为空"}
        
        # 获取投资组合收益率
        portfolio_returns = self._get_portfolio_returns(portfolio, historical_days)
        if portfolio_returns is None:
            return {"error": "无法计算投资组合收益率"}
        
        # 计算VaR (历史模拟法)
        var_historical = self._calculate_historical_var(
            portfolio_returns, confidence_level, portfolio_value
        )
        
        # 计算VaR (参数法，假设正态分布)
        var_parametric = self._calculate_parametric_var(
            portfolio_returns, confidence_level, portfolio_value
        )
        
        # 计算VaR (蒙特卡洛模拟法 - 简化版)
        var_monte_carlo = self._calculate_monte_carlo_var(
            portfolio_returns, confidence_level, portfolio_value, time_horizon
        )
        
        return {
            "portfolio_value": portfolio_value,
            "confidence_level": confidence_level,
            "time_horizon": time_horizon,
            "var_historical": var_historical,
            "var_parametric": var_parametric,
            "var_monte_carlo": var_monte_carlo,
            "recommended_var": var_historical,  # 通常使用历史模拟法
            "interpretation": self._interpret_var(
                var_historical, portfolio_value, confidence_level, time_horizon
            )
        }
    
    def _calculate_cvar(self, **kwargs) -> Dict[str, Any]:
        """计算条件在险价值 (CVaR)"""
        portfolio = kwargs.get('portfolio', {})
        confidence_level = kwargs.get('confidence_level', 0.95)
        portfolio_value = kwargs.get('portfolio_value', 1000000)
        historical_days = kwargs.get('historical_days', 250)
        
        if not portfolio:
            return {"error": "投资组合不能为空"}
        
        # 获取投资组合收益率
        portfolio_returns = self._get_portfolio_returns(portfolio, historical_days)
        if portfolio_returns is None:
            return {"error": "无法计算投资组合收益率"}
        
        # 计算CVaR
        cvar = self._calculate_historical_cvar(
            portfolio_returns, confidence_level, portfolio_value
        )
        
        # 计算对应的VaR
        var = self._calculate_historical_var(
            portfolio_returns, confidence_level, portfolio_value
        )
        
        return {
            "portfolio_value": portfolio_value,
            "confidence_level": confidence_level,
            "cvar": cvar,
            "var": var,
            "cvar_var_ratio": cvar / var if var != 0 else None,
            "interpretation": self._interpret_cvar(cvar, var, portfolio_value, confidence_level)
        }
    
    def _stress_test(self, **kwargs) -> Dict[str, Any]:
        """压力测试"""
        portfolio = kwargs.get('portfolio', {})
        market_condition = kwargs.get('market_condition', 'crisis')
        portfolio_value = kwargs.get('portfolio_value', 1000000)
        historical_days = kwargs.get('historical_days', 250)
        
        if not portfolio:
            return {"error": "投资组合不能为空"}
        
        # 定义压力情景
        stress_scenarios = {
            'normal': {
                'description': '正常市场条件',
                'market_return': -0.01,  # -1%
                'volatility_multiplier': 1.0
            },
            'crisis': {
                'description': '金融危机情景',
                'market_return': -0.20,  # -20%
                'volatility_multiplier': 2.5
            },
            'recovery': {
                'description': '复苏市场条件',
                'market_return': 0.05,  # +5%
                'volatility_multiplier': 1.5
            }
        }
        
        scenario = stress_scenarios.get(market_condition, stress_scenarios['normal'])
        
        # 获取投资组合基本信息
        portfolio_returns = self._get_portfolio_returns(portfolio, historical_days)
        if portfolio_returns is None:
            return {"error": "无法计算投资组合收益率"}
        
        # 计算基准风险指标
        base_metrics = self._calculate_base_metrics(portfolio_returns, portfolio_value)
        
        # 应用压力情景
        stressed_metrics = self._apply_stress_scenario(base_metrics, scenario)
        
        # 计算压力损失
        stress_loss = self._calculate_stress_loss(base_metrics, stressed_metrics, portfolio_value)
        
        return {
            "scenario": scenario,
            "portfolio_value": portfolio_value,
            "base_metrics": base_metrics,
            "stressed_metrics": stressed_metrics,
            "stress_loss": stress_loss,
            "risk_assessment": self._assess_stress_test(stress_loss, portfolio_value)
        }
    
    def _risk_assessment(self, **kwargs) -> Dict[str, Any]:
        """综合风险评估"""
        portfolio = kwargs.get('portfolio', {})
        portfolio_value = kwargs.get('portfolio_value', 1000000)
        
        if not portfolio:
            return {"error": "投资组合不能为空"}
        
        # 计算各种风险指标
        portfolio_risk = self._calculate_portfolio_risk(**kwargs)
        var_result = self._calculate_var(**kwargs)
        cvar_result = self._calculate_cvar(**kwargs)
        stress_result = self._stress_test(**kwargs)
        
        # 综合风险评估
        overall_risk = self._assess_overall_risk(
            portfolio_risk, var_result, cvar_result, stress_result
        )
        
        return {
            "portfolio_analysis": portfolio_risk,
            "var_analysis": var_result,
            "cvar_analysis": cvar_result,
            "stress_test": stress_result,
            "overall_risk_assessment": overall_risk,
            "recommendations": self._generate_risk_recommendations(overall_risk)
        }
    
    def _get_stock_returns(self, stock_code: str, days: int) -> Optional[pd.Series]:
        """获取股票收益率序列"""
        try:
            # 获取历史数据
            end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=days*2)).strftime('%Y-%m-%d')
            
            stock_data = self.stock_tool.execute(
                operation='history',
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                period='daily'
            )
            
            if not stock_data['success']:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(stock_data['data']['data'])
            if df.empty:
                return None
            
            # 提取收盘价
            if '收盘' in df.columns:
                close_prices = pd.to_numeric(df['收盘'], errors='coerce')
            elif 'close' in df.columns:
                close_prices = pd.to_numeric(df['close'], errors='coerce')
            else:
                return None
            
            # 计算日收益率
            returns = close_prices.pct_change().dropna()
            
            # 确保有足够的数据
            if len(returns) < 30:
                return None
            
            return returns.tail(days).reset_index(drop=True)
            
        except Exception as e:
            print(f"获取股票收益率失败 {stock_code}: {e}")
            return None
    
    def _get_portfolio_returns(self, portfolio: Dict[str, float], days: int) -> Optional[pd.Series]:
        """获取投资组合收益率"""
        returns_data = {}
        
        for stock_code, weight in portfolio.items():
            returns = self._get_stock_returns(stock_code, days)
            if returns is not None:
                returns_data[stock_code] = returns
        
        if not returns_data:
            return None
        
        # 创建DataFrame并确保长度一致
        min_length = min(len(r) for r in returns_data.values())
        aligned_returns = {code: returns[:min_length] for code, returns in returns_data.items()}
        
        returns_df = pd.DataFrame(aligned_returns)
        
        # 计算投资组合收益率
        weights = np.array([portfolio[code] for code in returns_df.columns])
        portfolio_returns = returns_df.dot(weights)
        
        return portfolio_returns
    
    def _calculate_portfolio_statistics(self, returns_df: pd.DataFrame, 
                                       portfolio: Dict[str, float]) -> Dict[str, Any]:
        """计算投资组合统计量"""
        weights = np.array([portfolio[code] for code in returns_df.columns])
        
        # 计算各资产统计量
        asset_stats = {}
        for code in returns_df.columns:
            returns = returns_df[code]
            asset_stats[code] = {
                "mean_return": float(returns.mean() * 252),  # 年化
                "volatility": float(returns.std() * np.sqrt(252)),  # 年化
                "sharpe_ratio": float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0,
                "skewness": float(returns.skew()),
                "kurtosis": float(returns.kurtosis()),
                "max_drawdown": float(self._calculate_max_drawdown(returns))
            }
        
        # 计算投资组合统计量
        portfolio_returns = returns_df.dot(weights)
        
        return {
            "asset_statistics": asset_stats,
            "portfolio_statistics": {
                "mean_return": float(portfolio_returns.mean() * 252),
                "volatility": float(portfolio_returns.std() * np.sqrt(252)),
                "sharpe_ratio": float(portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)) 
                               if portfolio_returns.std() > 0 else 0,
                "skewness": float(portfolio_returns.skew()),
                "kurtosis": float(portfolio_returns.kurtosis()),
                "max_drawdown": float(self._calculate_max_drawdown(portfolio_returns)),
                "information_ratio": self._calculate_information_ratio(portfolio_returns),
                "sortino_ratio": self._calculate_sortino_ratio(portfolio_returns)
            }
        }
    
    def _calculate_risk_metrics(self, returns_df: pd.DataFrame, 
                               portfolio: Dict[str, float]) -> Dict[str, Any]:
        """计算风险指标"""
        weights = np.array([portfolio[code] for code in returns_df.columns])
        portfolio_returns = returns_df.dot(weights)
        
        # 计算协方差矩阵
        cov_matrix = returns_df.cov() * 252  # 年化
        
        # 计算投资组合波动率
        portfolio_volatility = np.sqrt(weights.T @ cov_matrix.values @ weights)
        
        # 计算Beta (需要市场数据，这里简化)
        # 在实际应用中，需要获取市场指数数据
        
        # 计算下行风险
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_risk = np.sqrt((downside_returns ** 2).mean()) * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        # 计算风险价值 (VaR) - 历史法
        var_95 = np.percentile(portfolio_returns, 5)  # 95%置信水平
        
        return {
            "portfolio_volatility": float(portfolio_volatility),
            "downside_risk": float(downside_risk),
            "var_95": float(var_95),
            "expected_shortfall_95": float(portfolio_returns[portfolio_returns <= var_95].mean()) 
                                   if len(portfolio_returns[portfolio_returns <= var_95]) > 0 else 0,
            "tracking_error": 0.0,  # 需要基准数据
            "beta": 1.0,  # 需要市场数据
            "alpha": 0.0,  # 需要市场数据
            "treynor_ratio": 0.0  # 需要市场数据
        }
    
    def