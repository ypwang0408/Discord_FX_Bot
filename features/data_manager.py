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

    def __init__(self, data_file="server_data.json", base_dir=None):
        # 如果提供了 base_dir，使用絕對路徑；否則使用相對路徑（向後兼容）
        if base_dir:
            self.data_file = os.path.join(base_dir, data_file)
        else:
            self.data_file = data_file
        self.data = self.load_data()
        # 初始化匯率歷史
        if 'rate_history' not in self.data:
            self.data['rate_history'] = []
        # 初始化健康檢查歷史
        if 'health_check_history' not in self.data:
            self.data['health_check_history'] = {
                'last_quick_check': None,
                'last_detailed_check': None,
                'problem_history': []
            }
        # 確保健康檢查歷史有正確的結構
        elif not isinstance(self.data['health_check_history'], dict) or 'last_quick_check' not in self.data['health_check_history']:
            # 保留現有的詳細檢查資料（如果存在）
            existing_detailed = None
            if isinstance(self.data.get('health_check_history'), dict):
                existing_detailed = self.data['health_check_history'].get('last_detailed_check')
            
            self.data['health_check_history'] = {
                'last_quick_check': None,
                'last_detailed_check': existing_detailed,  # 保留現有的詳細檢查
                'problem_history': []
            }
    
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
        """儲存伺服器數據（混合格式：伺服器資料格式化，特殊資料緊湊）"""
        try:
            # 創建一個副本來處理格式化
            data_to_save = self.data.copy()
            
            # 提取特殊鍵值
            rate_history = data_to_save.pop('rate_history', {})
            health_check_history = data_to_save.pop('health_check_history', {})
            
            # 寫入文件 - 手動格式化
            with open(self.data_file, 'w', encoding='utf-8') as f:
                f.write('{\n')
                
                # 寫入伺服器資料（格式化）
                items = list(data_to_save.items())
                for i, (key, value) in enumerate(items):
                    formatted_value = json.dumps(value, indent=2, ensure_ascii=False)
                    # 將多行縮進調整
                    formatted_value = '\n'.join('  ' + line for line in formatted_value.split('\n'))
                    f.write(f'  "{key}": {formatted_value}')
                    if items or health_check_history or rate_history:
                        f.write(',')
                    f.write('\n')
                
                # 寫入健康檢查歷史（新的簡化結構）
                if health_check_history:
                    f.write('  "health_check_history": ')
                    formatted_history = json.dumps(health_check_history, indent=2, ensure_ascii=False)
                    # 調整縮進
                    formatted_history = '\n'.join('  ' + line for line in formatted_history.split('\n'))
                    f.write(formatted_history)
                    if rate_history:
                        f.write(',')
                    f.write('\n')
                
                # 寫入 rate_history（緊湊格式）
                if rate_history:
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

    def add_health_check_record(self, health_report, check_type='quick'):
        """添加健康檢查記錄 - 簡化結構版本"""
        try:
            # 使用統一的時間精確度函數
            timestamp = get_minute_precision_timestamp()
            status = health_report.get('status', 'unknown')
            
            # 初始化新的簡化結構
            if 'health_check_history' not in self.data:
                self.data['health_check_history'] = {
                    'last_quick_check': None,
                    'last_detailed_check': None,
                    'problem_history': []
                }
            
            # 如果是舊格式，保留現有資料並補完缺失的欄位
            if not isinstance(self.data['health_check_history'], dict) or 'last_quick_check' not in self.data['health_check_history']:
                # 保留現有的詳細檢查資料（如果存在）
                existing_detailed = None
                if isinstance(self.data.get('health_check_history'), dict):
                    existing_detailed = self.data['health_check_history'].get('last_detailed_check')
                
                self.data['health_check_history'] = {
                    'last_quick_check': None,
                    'last_detailed_check': existing_detailed,  # 保留現有的詳細檢查
                    'problem_history': []
                }
            
            # 更新對應的檢查時間和狀態
            if check_type == 'quick':
                self.data['health_check_history']['last_quick_check'] = {
                    'timestamp': timestamp,
                    'status': status
                }
            elif check_type == 'detailed':
                self.data['health_check_history']['last_detailed_check'] = {
                    'timestamp': timestamp,
                    'status': status
                }
            
            # 如果有問題，添加到問題歷史
            if status != 'healthy':
                problem_record = {
                    'timestamp': timestamp,
                    'check_type': check_type,
                    'status': status,
                    'warnings': health_report.get('warnings', []),
                    'errors': health_report.get('errors', [])
                }
                self.data['health_check_history']['problem_history'].append(problem_record)
            
            self.save_data()
            logger.debug(f"健康檢查記錄已保存: {status} ({check_type})")
            
        except Exception as e:
            logger.error(f"保存健康檢查記錄失敗: {e}")
    
    def get_health_check_history(self, days=7):
        """獲取健康檢查歷史 - 新的簡化結構"""
        try:
            if 'health_check_history' not in self.data:
                return {
                    'last_quick_check': None,
                    'last_detailed_check': None,
                    'problem_history': []
                }
            
            # 如果是舊格式，直接返回空的新格式
            if not isinstance(self.data['health_check_history'], dict) or 'last_quick_check' not in self.data['health_check_history']:
                return {
                    'last_quick_check': None,
                    'last_detailed_check': None,
                    'problem_history': []
                }
            
            # 返回新格式資料
            return self.data['health_check_history']
            
        except Exception as e:
            logger.error(f"獲取健康檢查歷史失敗: {e}")
            return {
                'last_quick_check': None,
                'last_detailed_check': None,
                'problem_history': []
            }
    
    def cleanup_health_check_problems(self, days=7):
        """清理超過指定天數的問題記錄（用於維護任務）"""
        try:
            if ('health_check_history' not in self.data or 
                not isinstance(self.data['health_check_history'], dict) or
                'problem_history' not in self.data['health_check_history']):
                return 0
            
            original_count = len(self.data['health_check_history']['problem_history'])
            
            # 清理超過指定天數的問題記錄
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")
            
            self.data['health_check_history']['problem_history'] = [
                record for record in self.data['health_check_history']['problem_history']
                if record.get('timestamp', '') > cutoff_str
            ]
            
            cleaned_count = original_count - len(self.data['health_check_history']['problem_history'])
            
            if cleaned_count > 0:
                self.save_data()
                logger.info(f"清理了 {cleaned_count} 個超過 {days} 天的問題記錄")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理健康檢查問題記錄失敗: {e}")
            return 0
    
    def get_all_servers_with_channels(self):
        """獲取所有設定了通知頻道的伺服器"""
        servers_with_channels = []
        for guild_id_str, server_data in self.data.items():
            # 跳過特殊鍵值
            if guild_id_str in ['rate_history', 'health_check_history']:
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
