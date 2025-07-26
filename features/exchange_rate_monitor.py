# -*- coding: utf-8 -*-
"""
匯率監控模組 - 簡化版本
負責從各個API獲取匯率數據
"""

import aiohttp
import asyncio
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ExchangeRateMonitor:
    """匯率監控器"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    def get_server_state(self, guild_id):
        """獲取伺服器狀態"""
        server_data = self.data_manager.get_server_data(guild_id)
        return {
            'last_rate': server_data.get('last_rate'),
            'last_notification_time': server_data.get('last_notification_time'),
            'last_was_above_threshold': server_data.get('last_was_above_threshold')
        }
    
    def update_server_state(self, guild_id, **kwargs):
        """更新伺服器狀態"""
        for key, value in kwargs.items():
            self.data_manager.update_server_data(guild_id, key, value)
    
    async def __aenter__(self):
        """異步上下文管理器進入"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15, connect=5),
            connector=aiohttp.TCPConnector(
                limit=10,           # 總連接池大小
                limit_per_host=5,   # 每個主機的連接數
                ttl_dns_cache=300,  # DNS快取時間
                use_dns_cache=True,
            ),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def get_esun_jpy_rate_with_session(self):
        """獲取玉山銀行匯率"""
        if not self.session:
            raise RuntimeError("Session not initialized.")
        
        url = "https://www.esunbank.com/zh-tw/personal/deposit/rate/forex/foreign-exchange-rates"
        
        try:
            self.logger.info("正在獲取玉山銀行匯率...")
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.text()
                
                soup = BeautifulSoup(content, 'html.parser')
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if cells:
                            first_cell_text = cells[0].get_text().strip()
                            if any(keyword in first_cell_text for keyword in ['JPY', '日幣', '日圓', 'JPN', '日本']):
                                self.logger.info("找到日幣行，共有 " + str(len(cells)) + " 個欄位")
                                
                                row_text = ' '.join([cell.get_text().strip() for cell in cells])
                                rate_pattern = r'[\d]+\.[\d]+'
                                rates = re.findall(rate_pattern, row_text.replace(',', ''))
                                self.logger.info("提取到的匯率數字: " + str(rates))
                                
                                if len(rates) >= 2:
                                    try:
                                        if len(rates) >= 4:
                                            rate_float = float(rates[3])  # 網銀賣出
                                        else:
                                            rate_float = float(rates[1])  # 備用：即期賣出
                                            
                                        if 0.1 <= rate_float <= 1.0:
                                            self.logger.info("成功獲取玉山銀行日幣匯率: " + str(rate_float))
                                            return rate_float
                                    except (ValueError, IndexError):
                                        continue
                                
                                for rate in rates:
                                    try:
                                        rate_float = float(rate)
                                        if 0.1 <= rate_float <= 1.0:
                                            self.logger.info("找到玉山銀行日幣匯率: " + str(rate_float))
                                            return rate_float
                                    except ValueError:
                                        continue
                
                self.logger.warning("無法從玉山銀行網站解析匯率，使用備用API")
                return await self.get_backup_jpy_rate_with_session()
                
        except Exception as e:
            self.logger.error("獲取玉山銀行匯率失敗: " + str(e))
            raise
    
    async def get_backup_jpy_rate_with_session(self):
        """獲取備用匯率API"""
        if not self.session:
            raise RuntimeError("Session not initialized.")
        
        url = "https://api.exchangerate-api.com/v4/latest/JPY"
        
        try:
            self.logger.info("正在獲取備用API匯率...")
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
                if 'rates' in data and 'TWD' in data['rates']:
                    jpy_to_twd = data['rates']['TWD']
                    result = round(jpy_to_twd, 4)
                    self.logger.info("成功獲取備用API匯率: " + str(result))
                    return result
                else:
                    raise ValueError("備用API回應格式錯誤")
                    
        except Exception as e:
            self.logger.error("備用匯率API失敗: " + str(e))
            raise
    
    async def get_esun_jpy_rate(self):
        """獲取玉山銀行日幣匯率（向後相容）"""
        async with self as monitor:
            return await monitor.get_rate_with_fallback()
    
    async def get_backup_jpy_rate(self):
        """獲取備用匯率（向後相容）"""
        async with self as monitor:
            try:
                return await monitor.get_backup_jpy_rate_with_session()
            except:
                return None
    
    async def get_rate_with_fallback(self):
        """獲取匯率，自動降級到備用API"""
        try:
            return await self.get_esun_jpy_rate_with_session()
        except Exception as e:
            self.logger.warning("主要API失敗，嘗試備用API: " + str(e))
            try:
                return await self.get_backup_jpy_rate_with_session()
            except Exception as backup_error:
                self.logger.error("所有API都失敗: 主要API=" + str(e) + ", 備用API=" + str(backup_error))
                return None
    
    async def get_multi_currency_rates(self):
        """獲取多種貨幣匯率（擴展功能）"""
        # 未來可擴展支援多種貨幣
        currencies = ['JPY', 'USD', 'EUR', 'KRW', 'GBP']
        rates = {}
        
        # 目前只實現JPY
        if not self.session:
            async with self as monitor:
                rates['JPY'] = await monitor.get_rate_with_fallback()
        else:
            rates['JPY'] = await self.get_rate_with_fallback()
        
        # 其他貨幣可在此處擴展
        return rates
