#!/usr/bin/env python3
"""
A股量化交易系统 - 数据管理层 V2
集成第三方Tushare API (稳定K线数据)
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
    'cache_expire_hours': 24,
}

# 第三方Tushare API配置
TUSHARE_CONFIG = {
    'token': '7f5ea280a95178113d0cb6c91e1c82fb5850d90fe0209de1348bbf47c1e6',
    'api_url': 'http://lianghua.nanyangqiankun.top'
}

class DataManagerV2:
    """
    数据管理器 V2
    支持: AKShare(基础) + 第三方Tushare(K线)
    """
    
    def __init__(self):
        os.makedirs(DATA_CONFIG['cache_dir'], exist_ok=True)
        
        self._init_tushare()
        self._init_akshare()
        
        print("✅ 数据管理器V2初始化完成")
        print(f"   Tushare API: {TUSHARE_CONFIG['api_url']}")
    
    def _init_tushare(self):
        """初始化Tushare第三方API"""
        try:
            import tushare as ts
            self.tushare = ts
            self.tushare.set_token(TUSHARE_CONFIG['token'])
            self.tushare_api = ts.pro_api(TUSHARE_CONFIG['token'])
            # 绕过官方API，使用第三方服务器
            self.tushare_api._DataApi__http_url = TUSHARE_CONFIG['api_url']
            self.tushare_api._DataApi__token = TUSHARE_CONFIG['token']
            print(f"✅ 第三方Tushare API初始化成功")
        except Exception as e:
            print(f"❌ Tushare API初始化失败: {e}")
            self.tushare = None
            self.tushare_api = None
    
    def _init_akshare(self):
        """初始化AKShare"""
        try:
            import akshare as ak
            self.akshare = ak
            print("✅ AKShare初始化成功")
        except Exception as e:
            print(f"❌ AKShare初始化失败: {e}")
            self.akshare = None
    
    def _init_baostock(self):
        """初始化BaoStock"""
        try:
            import baostock as bs
            self.baostock = bs
            lg = self.baostock.login()
            if lg.error_code == '0':
                print("✅ BaoStock初始化成功")
            else:
                print(f"❌ BaoStock登录失败")
        except Exception as e:
            print(f"❌ BaoStock初始化失败: {e}")
            self.baostock = None
    
    # ==================== Tushare API 接口 ====================
    
    def get_tushare_daily(self, ts_code, start_date, end_date):
        """
        获取日线数据（Tushare第三方API）
        ts_code: 股票代码，如 '000001.SZ'
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'
        """
        if self.tushare_api is None:
            return None
        
        cache_key = f"daily_{ts_code}_{start_date}_{end_date}"
        
        # 检查缓存
        cache_path = self.get_cache_path(cache_key)
        if os.path.exists(cache_path):
            print(f"📦 从缓存加载: {ts_code}")
            return pd.read_csv(cache_path)
        
        try:
            df = self.tushare_api.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and len(df) > 0:
                df.to_csv(cache_path, index=False)
                print(f"✅ 获取K线: {ts_code} ({len(df)}条)")
                return df
        except Exception as e:
            print(f"❌ 获取K线失败 {ts_code}: {e}")
        
        return None
    
    def get_tushare_index(self, ts_code='000001.SH', start_date=None, end_date=None):
        """
        获取指数日线数据
        """
        if self.tushare_api is None:
            return None
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"index_{ts_code}_{start_date}_{end_date}"
        cache_path = self.get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path)
        
        try:
            df = self.tushare_api.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and len(df) > 0:
                df.to_csv(cache_path, index=False)
                print(f"✅ 获取指数: {ts_code} ({len(df)}条)")
                return df
        except Exception as e:
            print(f"❌ 获取指数失败: {e}")
        
        return None
    
    def get_tushare_stock_list(self, limit=100):
        """
        获取股票列表
        """
        if self.tushare_api is None:
            return None
        
        cache_key = f"stock_list_{limit}"
        cache_path = self.get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path)
        
        try:
            df = self.tushare_api.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,industry'
            )
            
            if df is not None and len(df) > 0:
                df.to_csv(cache_path, index=False)
                print(f"✅ 获取股票列表: {len(df)}只")
                return df.head(limit) if limit else df
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
        
        return None
    
    # ==================== AKShare 接口 ====================
    
    def get_akshare_limit_up(self, date=None):
        """获取涨停股池（AKShare）"""
        if self.akshare is None:
            return None
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        cache_key = f"zt_{date}"
        cache_path = self.get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path)
        
        try:
            df = self.akshare.stock_zt_pool_em(date=date)
            if df is not None and len(df) > 0:
                df.to_csv(cache_path, index=False)
                print(f"✅ 获取涨停股: {len(df)}只")
                return df
        except Exception as e:
            print(f"❌ 获取涨停股失败: {e}")
        
        return None
    
    def get_akshare_sector(self):
        """获取板块资金流（AKShare）"""
        if self.akshare is None:
            return None
        
        cache_key = f"sector_{datetime.now().strftime('%Y%m%d')}"
        cache_path = self.get_cache_path(cache_key)
        
        if os.path.exists(cache_path):
            return pd.read_csv(cache_path)
        
        try:
            df = self.akshare.stock_sector_fund_flow_rank(indicator="今日")
            if df is not None and len(df) > 0:
                df.to_csv(cache_path, index=False)
                print(f"✅ 获取板块资金流: {len(df)}个")
                return df
        except Exception as e:
            print(f"❌ 获取板块失败: {e}")
        
        return None
    
    # ==================== 缓存管理 ====================
    
    def get_cache_path(self, key):
        """获取缓存路径"""
        return os.path.join(DATA_CONFIG['cache_dir'], f"{key}.csv")
    
    def close(self):
        """关闭连接"""
        if hasattr(self, 'baostock') and self.baostock:
            self.baostock.logout()
            print("✅ 连接已关闭")

def test_v2():
    """测试数据管理器V2"""
    print("\n" + "="*60)
    print("🧪 数据管理器V2 测试")
    print("="*60)
    
    dm = DataManagerV2()
    
    # 测试1: 获取K线数据
    print("\n📊 测试1: 获取K线数据...")
    df = dm.get_tushare_daily('000001.SZ', '20260301', '20260331')
    if df is not None and len(df) > 0:
        print(f"✅ K线数据: {len(df)}条")
        print(df[['trade_date','close','pct_chg']].head())
    
    # 测试2: 获取指数数据
    print("\n📊 测试2: 获取指数数据...")
    df = dm.get_tushare_index('000001.SH', '20260301', '20260331')
    if df is not None and len(df) > 0:
        print(f"✅ 上证指数: {len(df)}条")
        print(df[['trade_date','close','pct_chg']].head())
    
    # 测试3: 获取涨停股
    print("\n📊 测试3: 获取涨停股...")
    df = dm.get_akshare_limit_up('20260331')
    if df is not None and len(df) > 0:
        print(f"✅ 涨停股: {len(df)}只")
        cols = [c for c in df.columns if c in ['代码', '名称', '涨停统计', '连板数']]
        if cols:
            print(df[cols].head())
    
    # 测试4: 获取板块资金流
    print("\n📊 测试4: 获取板块资金流...")
    df = dm.get_akshare_sector()
    if df is not None and len(df) > 0:
        print(f"✅ 板块: {len(df)}个")
        if '名称' in df.columns:
            print(df[['名称', '今日涨跌幅']].head())
    
    dm.close()
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_v2()