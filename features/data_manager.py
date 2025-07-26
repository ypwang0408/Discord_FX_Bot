# -*- coding: utf-8 -*-
"""
數據管理模組
負責伺服器數據的載入、儲存和管理
"""

import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ServerDataManager:
    """伺服器數據管理器"""
    
    def __init__(self, data_file="server_data.json"):
        self.data_file = data_file
        self.data = self.load_data()
    
    def load_data(self):
        """載入伺服器數據"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error("載入數據文件失敗: " + str(e))
            return {}
    
    def save_data(self):
        """儲存伺服器數據"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("儲存數據文件失敗: " + str(e))
    
    def get_server_data(self, guild_id):
        """獲取特定伺服器的數據"""
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "threshold": 0.2,  # 預設閾值
                "channel_id": None,  # 通知頻道ID
                "use_everyone_mention": True,  # 是否使用@everyone
                "last_rate": None,  # 最後匯率
                "last_rate_time": None,  # 最後匯率更新時間
                "last_notification_time": None,  # 最後通知時間
                "last_was_above_threshold": None,  # 上次是否高於閾值
                "rate_history": [],  # 匯率歷史記錄
                "daily_report_enabled": False,  # 每日報告開關
                "weekly_notifications": 0,  # 週通知計數
                "currency_subscriptions": {},  # 多幣種訂閱
                "user_subscriptions": {}  # 用戶個人訂閱
            }
            self.save_data()
        else:
            # 向後兼容性：確保所有必需的欄位都存在
            server_data = self.data[guild_id]
            updated = False
            
            # 檢查並添加缺失的欄位
            default_fields = {
                "rate_history": [],
                "daily_report_enabled": False,
                "weekly_notifications": 0,
                "currency_subscriptions": {},
                "user_subscriptions": {}
            }
            
            for field, default_value in default_fields.items():
                if field not in server_data:
                    server_data[field] = default_value
                    updated = True
            
            if updated:
                self.save_data()
        
        return self.data[guild_id]
    
    def update_server_data(self, guild_id, key, value):
        """更新特定伺服器的數據"""
        guild_id = str(guild_id)
        server_data = self.get_server_data(guild_id)
        server_data[key] = value
        self.save_data()
    
    def get_threshold(self, guild_id):
        """獲取伺服器閾值"""
        return self.get_server_data(guild_id)["threshold"]
    
    def set_threshold(self, guild_id, threshold):
        """設定伺服器閾值"""
        self.update_server_data(guild_id, "threshold", threshold)
    
    def get_channel_id(self, guild_id):
        """獲取通知頻道ID"""
        return self.get_server_data(guild_id)["channel_id"]
    
    def set_channel_id(self, guild_id, channel_id):
        """設定通知頻道ID"""
        self.update_server_data(guild_id, "channel_id", channel_id)
    
    def get_use_everyone_mention(self, guild_id):
        """獲取是否使用@everyone"""
        return self.get_server_data(guild_id)["use_everyone_mention"]
    
    def set_use_everyone_mention(self, guild_id, use_mention):
        """設定是否使用@everyone"""
        self.update_server_data(guild_id, "use_everyone_mention", use_mention)
    
    def add_rate_history(self, guild_id, rate):
        """新增匯率歷史記錄"""
        server_data = self.get_server_data(guild_id)
        
        # 確保 rate_history 欄位存在
        if 'rate_history' not in server_data:
            server_data['rate_history'] = []
        
        server_data['rate_history'].append({
            'rate': rate,
            'timestamp': datetime.now().isoformat()
        })
        
        # 只保留最近30天的記錄
        cutoff_date = datetime.now() - timedelta(days=30)
        server_data['rate_history'] = [
            record for record in server_data['rate_history']
            if datetime.fromisoformat(record['timestamp']) > cutoff_date
        ]
        self.save_data()
    
    def get_rate_history(self, guild_id, days=30):
        """獲取匯率歷史記錄"""
        server_data = self.get_server_data(guild_id)
        rate_history = server_data.get('rate_history', [])
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            rate_history = [
                record for record in rate_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_date
            ]
        
        return rate_history
    
    def get_all_servers_with_channels(self):
        """獲取所有設定了通知頻道的伺服器"""
        servers_with_channels = []
        for guild_id_str, server_data in self.data.items():
            if server_data.get('channel_id'):
                servers_with_channels.append({
                    'guild_id': int(guild_id_str),
                    'channel_id': server_data['channel_id'],
                    'threshold': server_data['threshold'],
                    'use_everyone_mention': server_data['use_everyone_mention'],
                    'server_data': server_data
                })
        return servers_with_channels
