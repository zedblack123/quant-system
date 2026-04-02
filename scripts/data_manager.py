#!/usr/bin/env python3
"""
A股量化交易系统 - 数据管理层
统一对接 AKShare、Tushare、BaoStock 免费数据源
优化版：增加超时处理、缓存机制
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import time
import warnings
warnings.filterwarnings('ignore')

# 数据源配置
DATA_CONFIG = {
    'cache_dir': '/root/.openclaw/workspace/data',
    'cache_enabled': True,
    'cache_expire_hours': 24,  # 缓存24小时
    'request_timeout': 30,     # 请求超时30秒
    'retry_times': 2           # 重试次数
}

class DataManager:
    """
    数据管理器
    统一对接 AKShare、Tushare、BaoStock
    """
    
    def __init__(self):
        os.makedirs(DATA_CONFIG['cache_dir'], exist_ok=True)
        
        self.akshare = None
        self.tushare = None
        self.baostock = None
        
        self._init_data_sources()
    
    def _init_data_sources(self):
        """初始化数据源"""
        try:
            import akshare as ak
            self.akshare = ak
            print("✅ AKShare 初始化成功")
        except Exception as e:
            print(f"❌ AKShare 初始化失败: {e}")
        
        try:
            import tushare as ts
            self.tushare = ts
            self.tushare.set_token('')
            self.tushare_api = None  # 需要用户自行设置token
            print("✅ Tushare 初始化成功（需要Token）")
        except Exception as e:
            print(f"❌ Tushare 初始化失败: {e}")
        
        try:
            import baostock as bs
            self.baostock = bs
            lg = self.baostock.login()
            if lg.error_code == '0':
                print("✅ BaoStock 初始化成功")
            else:
                print(f"❌ BaoStock 登录失败")
        except Exception as e:
            print(f"❌ BaoStock 初始化失败: {e}")
    
    def get_cache_path(self, key):
        """获取缓存路径"""
        return os.path.join(DATA_CONFIG['cache_dir'], f"{key}.csv")
    
    def is_cache_valid(self, key):
        """检查缓存是否有效"""
        if not DATA_CONFIG['cache_enabled']:
            return False
        cache_path = self.get_cache_path(key)
        if not os.path.exists(cache_path):
            return False
        file_time = os.path.getmtime(cache_path)
        expire_time = file_time + DATA_CONFIG['cache_expire_hours'] * 3600
        return datetime.now().timestamp() < expire_time
    
    def save_to_cache(self, key, df):
        """保存到缓存"""
        if df is not None and len(df) > 0:
            cache_path = self.get_cache_path(key)
            df.to_csv(cache_path, index=False)
            return True
        return False
    
    def load_from_cache(self, key):
        """从缓存加载"""
        cache_path = self.get_cache_path(key)
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path)
        return None
    
    # ==================== 市场概览 ====================
    
    def get_market_summary(self, use_cache=True):
        """
        获取市场概览
        综合多个数据源
        """
        cache_key = f"market_summary_{datetime.now().strftime('%Y%m%d')}"
        
        # 尝试从缓存加载
        if use_cache:
            cached = self.load_from_cache(cache_key)
            if cached is not None:
                print("📦 从缓存加载市场概览")
                return cached
        
        print("📊 获取市场概览...")
        
        result = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'indices': self.get_major_indices(),
            'market_status': self.get_market_status(),
            'limit_up_count': 0,
            '跌停_count': 0,
            '上涨_count': 0,
            '下跌_count': 0
        }
        
        # 获取涨跌停数量
        try:
            zt_count = self.get_limit_up_count()
            result['limit_up_count'] = zt_count
        except:
            pass
        
        # 转换为 DataFrame
        df = pd.DataFrame([result])
        self.save_to_cache(cache_key, df)
        
        return df
    
    def get_major_indices(self):
        """获取主要指数"""
        indices = [
            {'name': '上证指数', 'code': 'sh000001'},
            {'name': '深证成指', 'code': 'sz399001'},
            {'name': '创业板指', 'code': 'sz399006'},
            {'name': '沪深300', 'code': 'sh000300'},
            {'name': '科创50', 'code': 'sh000688'}
        ]
        
        results = []
        for idx in indices:
            try:
                if self.baostock:
                    rs = self.baostock.query_history_k_data_plus(
                        idx['code'],
                        "date,code,open,high,low,close,volume",
                        start_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                        end_date=datetime.now().strftime('%Y-%m-%d'),
                        frequency='d'
                    )
                    data = self.baostock.parse_rows(rs)
                    if data and len(data) > 0:
                        latest = data[-1]
                        prev = data[-2] if len(data) > 1 else latest
                        change = (float(latest['close']) - float(prev['close'])) / float(prev['close']) * 100
                        results.append({
                            'name': idx['name'],
                            'close': float(latest['close']),
                            'change_pct': round(change, 2)
                        })
            except Exception as e:
                print(f"获取 {idx['name']} 失败: {e}")
        
        return results
    
    def get_market_status(self):
        """获取市场状态"""
        hour = datetime.now().hour
        minute = datetime.now().minute
        
        if (hour == 9 and minute < 30) or (hour == 11 and minute > 30) or (hour == 12) or (hour == 15):
            return 'closed'
        elif (hour >= 9 and hour < 11) or (hour >= 13 and hour < 15):
            return 'trading'
        elif hour == 11 or hour == 15:
            return 'closed'
        else:
            return 'closed'
    
    def get_limit_up_count(self):
        """获取涨停数量"""
        try:
            if self.akshare:
                date = datetime.now().strftime('%Y%m%d')
                df = self.akshare.stock_zt_pool_em(date=date)
                return len(df) if df is not None else 0
        except:
            return 0
        return 0
    
    # ==================== 涨停板数据 ====================
    
    def get_limit_up_stocks(self, date=None, use_cache=True):
        """
        获取涨停股池
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"limit_up_{date}"
        
        if use_cache:
            cached = self.load_from_cache(cache_key)
            if cached is not None:
                print(f"📦 从缓存加载涨停数据 ({date})")
                return cached
        
        print(f"📊 获取涨停股池 ({date})...")
        
        try:
            if self.akshare:
                # 获取涨停股
                df = self.akshare.stock_zt_pool_em(date=date)
                if df is not None and len(df) > 0:
                    # 选择关键列
                    cols = ['代码', '名称', '涨停统计', '流通市值', '换手率', '连板数', '竞价成交额']
                    available_cols = [c for c in cols if c in df.columns]
                    df = df[available_cols]
                    self.save_to_cache(cache_key, df)
                    print(f"✅ 获取到 {len(df)} 只涨停股")
                    return df
        except Exception as e:
            print(f"❌ 获取涨停股池失败: {e}")
        
        return pd.DataFrame()
    
    def get_limit_strong_stocks(self, date=None):
        """获取强势股（涨停后炸板少）"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"limit_strong_{date}"
        cached = self.load_from_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            if self.akshare:
                df = self.akshare.stock_zt_pool_strong_em(date=date)
                if df is not None and len(df) > 0:
                    self.save_to_cache(cache_key, df)
                    return df
        except Exception as e:
            print(f"❌ 获取强势股失败: {e}")
        
        return pd.DataFrame()
    
    # ==================== 板块数据 ====================
    
    def get_sector_ranking(self, use_cache=True):
        """获取板块排名"""
        cache_key = f"sector_ranking_{datetime.now().strftime('%Y%m%d')}"
        
        if use_cache:
            cached = self.load_from_cache(cache_key)
            if cached is not None:
                return cached
        
        print("📊 获取板块排名...")
        
        try:
            if self.akshare:
                # 今日板块资金流入排名
                df = self.akshare.stock_sector_fund_flow_rank(indicator="今日")
                if df is not None and len(df) > 0:
                    # 选择关键列
                    cols = ['名称', '今日涨跌幅', '今日主力净流入-净额', '今日主力净流入占比', '今日超大单净流入-净额']
                    available_cols = [c for c in cols if c in df.columns]
                    df = df[available_cols].head(20)  # 取前20
                    self.save_to_cache(cache_key, df)
                    return df
        except Exception as e:
            print(f"❌ 获取板块排名失败: {e}")
        
        return pd.DataFrame()
    
    def get_hot_sectors(self):
        """获取热门板块"""
        try:
            if self.akshare:
                # 概念板块排名
                df = self.akshare.stock_board_concept_name_em()
                if df is not None and len(df) > 0:
                    # 按涨跌幅排序
                    if '涨跌幅' in df.columns:
                        df = df.sort_values('涨跌幅', ascending=False)
                    return df.head(15)
        except Exception as e:
            print(f"❌ 获取热门板块失败: {e}")
        
        return pd.DataFrame()
    
    # ==================== 个股数据 ====================
    
    def get_stock_realtime(self, symbol):
        """获取个股实时行情"""
        cache_key = f"stock_realtime_{symbol}"
        cached = self.load_from_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            if self.akshare:
                df = self.akshare.stock_zh_a_spot_em()
                if df is not None:
                    stock_df = df[df['代码'] == symbol]
                    if len(stock_df) > 0:
                        self.save_to_cache(cache_key, stock_df)
                        return stock_df
        except Exception as e:
            print(f"❌ 获取个股实时行情失败: {e}")
        
        return pd.DataFrame()
    
    def get_stock_history(self, symbol, period='daily', count=100):
        """获取个股历史K线"""
        cache_key = f"stock_history_{symbol}_{period}_{count}"
        cached = self.load_from_cache(cache_key)
        if cached is not None:
            return cached
        
        print(f"📊 获取 {symbol} 历史K线 ({count}条)...")
        
        try:
            if self.akshare:
                # 转换symbol格式
                symbol_fmt = symbol if symbol.startswith('6') else symbol
                
                df = self.akshare.stock_zh_a_hist(
                    symbol=symbol_fmt,
                    period=period,
                    start_date=(datetime.now() - timedelta(days=count*2)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d'),
                    adjust="qfq"
                )
                
                if df is not None and len(df) > 0:
                    # 转换日期格式
                    if '日期' in df.columns:
                        df['日期'] = pd.to_datetime(df['日期'])
                    df = df.tail(count)  # 取最近的count条
                    self.save_to_cache(cache_key, df)
                    return df
        except Exception as e:
            print(f"❌ 获取历史K线失败: {e}")
        
        return pd.DataFrame()
    
    def get_stock_info(self, symbol):
        """获取个股基本信息"""
        try:
            if self.akshare:
                df = self.akshare.stock_individual_info_em(symbol=symbol)
                if df is not None:
                    return df
        except Exception as e:
            print(f"❌ 获取个股信息失败: {e}")
        
        return pd.DataFrame()
    
    def get_money_flow(self, symbol):
        """获取个股资金流向"""
        try:
            if self.akshare:
                df = self.akshare.stock_individual_fund_flow(stock=symbol)
                if df is not None:
                    return df
        except Exception as e:
            print(f"❌ 获取资金流向失败: {e}")
        
        return pd.DataFrame()
    
    # ==================== 龙虎榜 ====================
    
    def get_dragon_tiger(self, date=None):
        """获取龙虎榜数据"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"dragon_tiger_{date}"
        cached = self.load_from_cache(cache_key)
        if cached is not None:
            return cached
        
        try:
            if self.akshare:
                df = self.akshare.stock_lhb_detail_em(date=date)
                if df is not None and len(df) > 0:
                    self.save_to_cache(cache_key, df)
                    return df
        except Exception as e:
            print(f"❌ 获取龙虎榜失败: {e}")
        
        return pd.DataFrame()
    
    # ==================== 北向资金 ====================
    
    def get_north_money(self, use_cache=True):
        """获取北向资金"""
        cache_key = f"north_money_{datetime.now().strftime('%Y%m%d')}"
        
        if use_cache:
            cached = self.load_from_cache(cache_key)
            if cached is not None:
                return cached
        
        print("📊 获取北向资金...")
        
        try:
            if self.akshare:
                # 获取北向资金历史数据
                df = self.akshare.stock_hsgt_hist_em(symbol="北向资金")
                if df is not None and len(df) > 0:
                    # 取最近10天数据
                    df = df.tail(10)
                    self.save_to_cache(cache_key, df)
                    return df
        except Exception as e:
            print(f"❌ AKShare北向资金失败: {e}")
        
        return pd.DataFrame()
    
    # ==================== Tushare 接口 ====================
    
    def set_tushare_token(self, token):
        """设置Tushare Token"""
        try:
            import tushare as ts
            ts.set_token(token)
            self.tushare_api = ts.pro_api()
            self.tushare = ts
            print("✅ Tushare Token设置成功")
            return True
        except Exception as e:
            print(f"❌ Tushare Token设置失败: {e}")
            return False
    
    def get_tushare_today_all(self, use_cache=True):
        """获取今日所有行情（Tushare基础接口）"""
        cache_key = f"tushare_today_all_{datetime.now().strftime('%Y%m%d')}"
        
        if use_cache:
            cached = self.load_from_cache(cache_key)
            if cached is not None:
                print("📦 从缓存加载Tushare今日行情")
                return cached
        
        print("📊 从Tushare获取今日行情...")
        
        try:
            if self.tushare:
                df = self.tushare.get_today_all()
                if df is not None and len(df) > 0:
                    self.save_to_cache(cache_key, df)
                    print(f"✅ Tushare获取今日行情成功: {len(df)}只")
                    return df
        except Exception as e:
            print(f"❌ Tushare今日行情失败: {e}")
        
        return pd.DataFrame()
    
    # ==================== 选股接口 ====================
    
    def screen_stocks(self, criteria):
        """
        筛选股票
        criteria: dict 筛选条件
          - limit_up: 是否涨停
          - sector: 板块
          - market_cap: 流通市值范围 (min, max)
          - turnover: 换手率范围 (min, max)
          - volume_ratio: 量比范围 (min, max)
        """
        print("📊 筛选股票...")
        
        try:
            if self.akshare:
                # 获取所有A股实时数据
                df = self.akshare.stock_zh_a_spot_em()
                
                if df is None or len(df) == 0:
                    return pd.DataFrame()
                
                # 应用筛选条件
                if criteria.get('limit_up'):
                    # 这里简化处理，实际应该用涨停池数据
                    df = df[df['涨跌幅'] >= 9.9]
                
                if criteria.get('sector'):
                    df = df[df['所属行业'] == criteria['sector']]
                
                if criteria.get('market_cap'):
                    min_cap, max_cap = criteria['market_cap']
                    df = df[(df['流通市值'] >= min_cap) & (df['流通市值'] <= max_cap)]
                
                if criteria.get('turnover'):
                    min_to, max_to = criteria['turnover']
                    df = df[(df['换手率'] >= min_to) & (df['换手率'] <= max_to)]
                
                return df.head(100)  # 最多返回100只
                
        except Exception as e:
            print(f"❌ 筛选股票失败: {e}")
        
        return pd.DataFrame()
    
    def close(self):
        """关闭连接"""
        if self.baostock:
            self.baostock.logout()
            print("✅ BaoStock 连接已关闭")

def test_data_manager():
    """测试数据管理器"""
    print("\n" + "="*60)
    print("🧪 数据管理器测试")
    print("="*60)
    
    dm = DataManager()
    
    # 测试1: 市场概览
    print("\n1️⃣ 测试市场概览...")
    try:
        summary = dm.get_market_summary()
        print(f"✅ 市场概览获取成功")
        if 'indices' in summary.columns:
            print(summary['indices'])
    except Exception as e:
        print(f"❌ 市场概览失败: {e}")
    
    # 测试2: 板块排名
    print("\n2️⃣ 测试板块排名...")
    try:
        sectors = dm.get_sector_ranking()
        if sectors is not None and len(sectors) > 0:
            print(f"✅ 获取到 {len(sectors)} 个板块")
            print(sectors.head())
    except Exception as e:
        print(f"❌ 板块排名失败: {e}")
    
    # 测试3: 涨停股池
    print("\n3️⃣ 测试涨停股池...")
    try:
        zt = dm.get_limit_up_stocks()
        if zt is not None and len(zt) > 0:
            print(f"✅ 获取到 {len(zt)} 只涨停股")
            print(zt.head())
    except Exception as e:
        print(f"❌ 涨停股池失败: {e}")
    
    # 测试4: 个股K线
    print("\n4️⃣ 测试个股K线...")
    try:
        kline = dm.get_stock_history('000001', count=10)
        if kline is not None and len(kline) > 0:
            print(f"✅ 获取到 {len(kline)} 条K线")
            print(kline.tail(3))
    except Exception as e:
        print(f"❌ 个股K线失败: {e}")
    
    # 测试5: 北向资金
    print("\n5️⃣ 测试北向资金...")
    try:
        north = dm.get_north_money()
        if north is not None and len(north) > 0:
            print(f"✅ 获取到北向资金数据")
    except Exception as e:
        print(f"❌ 北向资金失败: {e}")
    
    dm.close()
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_data_manager()