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


def get_minute_precision_timestamp():
    """獲取精確到分鐘的時間戳字符串（不包含秒數）"""
    return datetime.now().replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


class ServerDataManager:
    """伺服器數據管理器"""
    
    def __init__(self, data_file="server_data.json"):
        self.data_file = data_file
        self.data = self.load_data()
        # 初始化全域匯率歷史
        if 'global_rate_history' not in self.data:
            self.data['global_rate_history'] = []
    
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
                # 移除個別伺服器的 rate_history，改用全域 global_rate_history
                # 移除未使用的擴展功能欄位以簡化數據結構
            }
            self.save_data()
        else:
            # 清理舊的未使用欄位（如果存在）
            server_data = self.data[guild_id]
            unused_fields = [
                'rate_history',  # 已改用全域歷史
                'daily_report_enabled',  # 未實現的功能
                'weekly_notifications',  # 未實現的功能
                'currency_subscriptions',  # 未實現的功能
                'user_subscriptions'  # 未實現的功能
            ]
            
            cleaned = False
            for field in unused_fields:
                if field in server_data:
                    del server_data[field]
                    cleaned = True
            
            if cleaned:
                self.save_data()
                logger.info(f"清理伺服器 {guild_id} 的未使用欄位")
        
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
        """新增匯率歷史記錄到全域歷史（優化版本）"""
        # 使用統一的時間精確度函數
        timestamp_str = get_minute_precision_timestamp()
        
        # 確保全域匯率歷史存在
        if 'global_rate_history' not in self.data:
            self.data['global_rate_history'] = []
        
        # 檢查最後一筆記錄，避免重複添加相同時間的記錄
        if (self.data['global_rate_history'] and 
            self.data['global_rate_history'][-1]['timestamp'] == timestamp_str):
            # 如果匯率有變化，更新記錄；否則跳過
            if self.data['global_rate_history'][-1]['rate'] != rate:
                self.data['global_rate_history'][-1]['rate'] = rate
                self.save_data()
            return
        
        # 添加新記錄
        self.data['global_rate_history'].append({
            'rate': rate,
            'timestamp': timestamp_str
        })
        
        # 只保留最近30天的記錄，減少存儲空間
        cutoff_date = datetime.now() - timedelta(days=30)
        self.data['global_rate_history'] = [
            record for record in self.data['global_rate_history']
            if datetime.fromisoformat(record['timestamp']) > cutoff_date
        ]
        
        self.save_data()
    
    def get_rate_history(self, guild_id=None, days=30):
        """獲取匯率歷史記錄（從全域歷史）"""
        # guild_id 參數保留以維持 API 兼容性，但現在使用全域歷史
        global_history = self.data.get('global_rate_history', [])
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            global_history = [
                record for record in global_history
                if datetime.fromisoformat(record['timestamp']) > cutoff_date
            ]
        
        return global_history
    
    def get_all_servers_with_channels(self):
        """獲取所有設定了通知頻道的伺服器"""
        servers_with_channels = []
        for guild_id_str, server_data in self.data.items():
            # 跳過全域匯率歷史記錄
            if guild_id_str == 'global_rate_history':
                continue
                
            if isinstance(server_data, dict) and server_data.get('channel_id'):
                servers_with_channels.append({
                    'guild_id': int(guild_id_str),
                    'channel_id': server_data['channel_id'],
                    'threshold': server_data['threshold'],
                    'use_everyone_mention': server_data['use_everyone_mention'],
                    'server_data': server_data
                })
        return servers_with_channels
