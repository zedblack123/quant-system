"""
股票数据工具
使用akshare获取A股行情数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base import BaseTool, PermissionLevel


class StockDataTool(BaseTool):
    """股票数据获取工具"""
    
    def __init__(self):
        """初始化股票数据工具"""
        super().__init__(
            name="stock_data",
            description="获取A股股票行情数据、财务数据、历史K线等",
            version="1.0.0"
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行股票数据查询
        
        Args:
            operation: 操作类型 ('realtime', 'history', 'financial', 'basic_info')
            stock_code: 股票代码 (如 '000001')
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: K线周期 ('daily', 'weekly', 'monthly')
            
        Returns:
            股票数据
        """
        try:
            operation = kwargs.get('operation', 'realtime')
            stock_code = kwargs.get('stock_code')
            
            if not stock_code:
                return {
                    "success": False,
                    "error": "股票代码不能为空",
                    "data": None
                }
            
            if operation == 'realtime':
                data = self._get_realtime_data(stock_code)
            elif operation == 'history':
                data = self._get_history_data(
                    stock_code,
                    kwargs.get('start_date'),
                    kwargs.get('end_date'),
                    kwargs.get('period', 'daily')
                )
            elif operation == 'financial':
                data = self._get_financial_data(stock_code)
            elif operation == 'basic_info':
                data = self._get_basic_info(stock_code)
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作类型: {operation}",
                    "data": None
                }
            
            return {
                "success": True,
                "data": data,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取股票数据失败: {str(e)}",
                "data": None
            }
    
    def get_permission_level(self) -> PermissionLevel:
        """获取权限级别"""
        return PermissionLevel.LOW
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数模式"""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["realtime", "history", "financial", "basic_info"],
                    "description": "操作类型"
                },
                "stock_code": {
                    "type": "string",
                    "description": "股票代码 (如 '000001')"
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "开始日期 (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "结束日期 (YYYY-MM-DD)"
                },
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "K线周期"
                }
            },
            "required": ["operation", "stock_code"]
        }
    
    def _get_returns_schema(self) -> Dict[str, Any]:
        """获取返回模式"""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "data": {
                    "type": "object",
                    "description": "股票数据"
                },
                "error": {"type": "string", "optional": True}
            }
        }
    
    def _get_tags(self) -> List[str]:
        """获取标签"""
        return ["stock", "data", "akshare", "china"]
    
    def _get_realtime_data(self, stock_code: str) -> Dict[str, Any]:
        """获取实时行情数据"""
        # 获取实时行情
        stock_zh_a_spot_df = ak.stock_zh_a_spot()
        
        # 查找指定股票
        stock_data = stock_zh_a_spot_df[
            stock_zh_a_spot_df['代码'] == f'sz{stock_code}' if stock_code.startswith('0') else f'sh{stock_code}'
        ]
        
        if stock_data.empty:
            return {"error": "股票代码不存在"}
        
        # 转换为字典
        data = stock_data.iloc[0].to_dict()
        
        # 获取分时数据
        try:
            time_share_df = ak.stock_zh_a_minute(
                symbol=stock_code, 
                period='1', 
                adjust="qfq"
            )
            time_share = time_share_df.tail(10).to_dict('records')
        except:
            time_share = []
        
        return {
            "realtime": data,
            "time_share": time_share,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_history_data(self, stock_code: str, start_date: Optional[str], 
                         end_date: Optional[str], period: str) -> Dict[str, Any]:
        """获取历史K线数据"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        # 转换日期格式
        start_date = start_date.replace('-', '')
        end_date = end_date.replace('-', '')
        
        # 获取历史数据
        if period == 'daily':
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        elif period == 'weekly':
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="weekly",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        else:  # monthly
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="monthly",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        
        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "data": df.to_dict('records'),
            "count": len(df)
        }
    
    def _get_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """获取财务数据"""
        try:
            # 获取财务指标
            financial_df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            
            # 获取资产负债表
            balance_df = ak.stock_balance_sheet_by_report_em(symbol=stock_code)
            
            # 获取利润表
            income_df = ak.stock_profit_sheet_by_report_em(symbol=stock_code)
            
            # 获取现金流量表
            cashflow_df = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code)
            
            return {
                "financial_indicators": financial_df.tail(5).to_dict('records'),
                "balance_sheet": balance_df.tail(5).to_dict('records'),
                "income_statement": income_df.tail(5).to_dict('records'),
                "cash_flow": cashflow_df.tail(5).to_dict('records')
            }
        except Exception as e:
            return {"error": f"获取财务数据失败: {str(e)}"}
    
    def _get_basic_info(self, stock_code: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            # 获取股票基本信息
            info_df = ak.stock_individual_info_em(symbol=stock_code)
            
            # 获取公司概况
            profile_df = ak.stock_profile_cninfo(symbol=stock_code)
            
            # 获取行业信息
            industry_df = ak.stock_board_industry_name_em()
            
            return {
                "basic_info": info_df.to_dict('records') if not info_df.empty else [],
                "company_profile": profile_df.to_dict('records') if not profile_df.empty else [],
                "industry_info": industry_df.head(10).to_dict('records')
            }
        except Exception as e:
            return {"error": f"获取基本信息失败: {str(e)}"}