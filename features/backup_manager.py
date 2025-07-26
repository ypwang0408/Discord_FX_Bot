# -*- coding: utf-8 -*-
"""
數據備份管理模組
負責數據的備份、恢復和管理
"""

import json
import os
import shutil
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataBackupManager:
    """數據備份管理器"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.backup_dir = "backups"
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """確保備份目錄存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self):
        """創建數據備份 - 每天一個備份"""
        # 使用日期作為備份文件名，簡化格式
        date_str = datetime.now().strftime("%Y%m%d")
        backup_filename = date_str + ".json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # 如果今天的備份已存在，先刪除舊的
            if os.path.exists(backup_path):
                os.remove(backup_path)
                logger.info("替換今天的備份: " + str(backup_filename))
            
            # 複製當前數據文件
            shutil.copy2(self.data_manager.data_file, backup_path)
            
            # 記錄備份信息
            backup_info = {
                "timestamp": datetime.now().isoformat(),
                "filename": backup_filename,
                "date": date_str,
                "servers_count": len(self.data_manager.data),
                "file_size": os.path.getsize(backup_path)
            }
            
            # 更新備份記錄
            self.update_backup_record(backup_info)
            
            # 清理舊備份（每次備份後執行）
            self.cleanup_old_backups_smart()
            
            logger.info("創建備份成功: " + str(backup_path))
            return backup_path
        except Exception as e:
            logger.error("創建備份失敗: " + str(e))
            return None
    
    def update_backup_record(self, backup_info):
        """更新備份記錄"""
        record_file = os.path.join(self.backup_dir, "backup_record.json")
        
        try:
            if os.path.exists(record_file):
                with open(record_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            else:
                records = []
            
            records.append(backup_info)
            
            # 只保留最近30個備份記錄
            records = records[-30:]
            
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error("更新備份記錄失敗: " + str(e))
    
    def list_backups(self):
        """列出所有備份"""
        record_file = os.path.join(self.backup_dir, "backup_record.json")
        
        try:
            if os.path.exists(record_file):
                with open(record_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error("讀取備份記錄失敗: " + str(e))
            return []
    
    def restore_from_backup(self, backup_filename):
        """從備份恢復數據"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            logger.error("備份檔案不存在: " + str(backup_path))
            return False
        
        try:
            # 先備份當前數據
            current_backup = "pre_restore_backup_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".json"
            current_backup_path = os.path.join(self.backup_dir, current_backup)
            shutil.copy2(self.data_manager.data_file, current_backup_path)
            
            # 恢復數據
            shutil.copy2(backup_path, self.data_manager.data_file)
            
            # 重新載入數據
            self.data_manager.data = self.data_manager.load_data()
            
            logger.info("從備份恢復成功: " + str(backup_filename))
            return True
        except Exception as e:
            logger.error("恢復備份失敗: " + str(e))
            return False
    
    def cleanup_old_backups(self, keep_days=30):
        """清理舊備份"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cleaned_count = 0
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("server_data_backup_") and filename.endswith(".json"):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.info("清理舊備份: " + str(filename))
                        except Exception as e:
                            logger.error("刪除舊備份失敗 " + str(filename) + ": " + str(e))
        except Exception as e:
            logger.error("清理舊備份時發生錯誤: " + str(e))
        
        return cleaned_count
    
    def cleanup_old_backups_smart(self):
        """智能清理舊備份 - 7天內保留所有，超過7天只保留星期一的備份"""
        cutoff_date = datetime.now() - timedelta(days=7)
        cleaned_count = 0
        
        try:
            backup_files = []
            
            # 收集所有備份文件信息
            for filename in os.listdir(self.backup_dir):
                if filename.endswith(".json") and filename != "backup_record.json":
                    # 解析日期格式 YYYYMMDD.json
                    if len(filename) == 13:  # YYYYMMDD.json (8+4+1=13)
                        date_str = filename[:-5]  # 移除.json
                        try:
                            file_date = datetime.strptime(date_str, "%Y%m%d")
                            file_path = os.path.join(self.backup_dir, filename)
                            
                            backup_files.append({
                                'filename': filename,
                                'date': file_date,
                                'path': file_path,
                                'weekday': file_date.weekday()  # 0=Monday, 6=Sunday
                            })
                        except ValueError:
                            # 忽略無法解析日期的檔案
                            continue
            
            # 清理邏輯：超過7天的備份，只保留星期一的
            for backup in backup_files:
                if backup['date'] < cutoff_date:
                    # 超過7天的備份
                    if backup['weekday'] != 0:  # 不是星期一
                        try:
                            os.remove(backup['path'])
                            cleaned_count += 1
                            logger.info("清理非星期一舊備份: " + str(backup['filename']))
                        except Exception as e:
                            logger.error("刪除舊備份失敗 " + str(backup['filename']) + ": " + str(e))
                    else:
                        # 星期一的備份保留，但記錄保留信息
                        logger.info("保留星期一備份: " + str(backup['filename']))
                        
        except Exception as e:
            logger.error("智能清理舊備份時發生錯誤: " + str(e))
        
        if cleaned_count > 0:
            logger.info("智能清理完成，清理了 " + str(cleaned_count) + " 個舊備份")
        
        return cleaned_count
    
    def get_backup_info(self, backup_filename):
        """獲取備份檔案信息"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            return None
        
        try:
            file_stat = os.stat(backup_path)
            return {
                'filename': backup_filename,
                'size': file_stat.st_size,
                'created_time': datetime.fromtimestamp(file_stat.st_ctime),
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime),
                'path': backup_path
            }
        except Exception as e:
            logger.error("獲取備份信息失敗: " + str(e))
            return None
    
    def validate_backup(self, backup_filename):
        """驗證備份檔案的完整性"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            return False, "備份檔案不存在"
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查基本結構
            if not isinstance(data, dict):
                return False, "備份檔案格式錯誤"
            
            # 可以添加更多驗證邏輯
            return True, "備份檔案有效"
            
        except json.JSONDecodeError:
            return False, "JSON格式錯誤"
        except Exception as e:
            return False, "驗證失敗: " + str(e)
