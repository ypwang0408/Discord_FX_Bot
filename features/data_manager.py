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
        # 初始化匯率歷史
        if 'rate_history' not in self.data:
            self.data['rate_history'] = []
    
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
        """儲存伺服器數據（混合格式：伺服器資料格式化，rate_history 緊湊）"""
        try:
            # 創建一個副本來處理格式化
            data_to_save = self.data.copy()
            
            # 如果有 rate_history，需要特殊處理
            if 'rate_history' in data_to_save:
                rate_history = data_to_save['rate_history']
                
                # 先保存沒有 rate_history 的部分
                temp_data = {k: v for k, v in data_to_save.items() if k != 'rate_history'}
                
                # 寫入文件 - 手動格式化
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    f.write('{\n')
                    
                    # 寫入伺服器資料（格式化）
                    items = list(temp_data.items())
                    for i, (key, value) in enumerate(items):
                        formatted_value = json.dumps(value, indent=2, ensure_ascii=False)
                        # 將多行縮進調整
                        formatted_value = '\n'.join('  ' + line for line in formatted_value.split('\n'))
                        f.write(f'  "{key}": {formatted_value}')
                        f.write(',\n')
                    
                    # 寫入 rate_history（每個日期的記錄陣列在同一行）
                    f.write('  "rate_history": {\n')
                    date_items = list(rate_history.items())
                    for i, (date, records) in enumerate(date_items):
                        # 整個記錄陣列在同一行
                        records_str = json.dumps(records, separators=(',', ':'))
                        f.write(f'    "{date}": {records_str}')
                        if i < len(date_items) - 1:
                            f.write(',')
                        f.write('\n')
                    f.write('  }\n')
                    
                    f.write('}\n')
            else:
                # 沒有 rate_history 時使用標準格式
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                    
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
                'rate_history',  # 已改用統一的匯率歷史
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
        """新增匯率歷史記錄到統一的匯率歷史（優化版本 - 日期分組格式）"""
        # 使用統一的時間精確度函數
        timestamp_str = get_minute_precision_timestamp()
        date_part = timestamp_str[:10]  # YYYY-MM-DD
        time_part = timestamp_str[11:16]  # HH:MM
        
        # 確保匯率歷史存在且為字典格式
        if 'rate_history' not in self.data:
            self.data['rate_history'] = {}
        
        # 確保當前日期的記錄存在
        if date_part not in self.data['rate_history']:
            self.data['rate_history'][date_part] = []
        
        current_day_records = self.data['rate_history'][date_part]
        
        # 檢查最後一筆記錄，避免重複添加相同時間的記錄
        if (current_day_records and 
            current_day_records[-1][0] == time_part):
            # 如果匯率有變化，更新記錄；否則跳過
            if current_day_records[-1][1] != rate:
                current_day_records[-1][1] = rate
                self.save_data()
            return
        
        # 添加新記錄 [time, rate]
        current_day_records.append([time_part, rate])
        
        # 清理超過30天的舊記錄
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_date_str = cutoff_date.strftime("%Y-%m-%d")
        
        dates_to_remove = []
        for date_key in self.data['rate_history'].keys():
            if date_key < cutoff_date_str:
                dates_to_remove.append(date_key)
        
        for date_key in dates_to_remove:
            del self.data['rate_history'][date_key]
        
        self.save_data()
    
    def get_rate_history(self, guild_id=None, days=30):
        """獲取匯率歷史記錄（從統一的匯率歷史 - 日期分組格式）"""
        # guild_id 參數保留以維持 API 兼容性，但現在使用統一的匯率歷史
        rate_history_dict = self.data.get('rate_history', {})
        
        # 轉換為原始格式以保持兼容性
        rate_history = []
        
        # 處理不同格式的兼容性
        if isinstance(rate_history_dict, list):
            # 舊格式 - 直接使用
            rate_history = rate_history_dict
        else:
            # 新格式 - 轉換為原始格式
            for date_str, day_records in rate_history_dict.items():
                for time_str, rate in day_records:
                    timestamp = f"{date_str}T{time_str}"
                    rate_history.append({
                        'rate': rate,
                        'timestamp': timestamp
                    })
        
        # 按時間戳排序
        rate_history.sort(key=lambda x: x['timestamp'])
        
        # 過濾指定天數
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
            # 跳過匯率歷史記錄
            if guild_id_str == 'rate_history':
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
