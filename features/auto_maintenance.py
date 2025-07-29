# -*- coding: utf-8 -*-
"""
自動化運維模組
負責系統自動維護、錯誤恢復、日誌管理、性能優化等
"""

import os
import json
import logging
import asyncio
import shutil
import subprocess
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import psutil
import time
import zipfile

logger = logging.getLogger(__name__)


class AutoMaintenance:
    """自動化運維管理器"""
    
    def __init__(self, data_manager, health_monitor=None):
        self.data_manager = data_manager
        self.health_monitor = health_monitor
        self.maintenance_log = []
        self.max_log_size = 500  # 保留最近500條運維記錄
        
        # 運維配置
        self.config = {
            'log_cleanup': {
                'enabled': True,
                'retention_days': 30,
                'max_file_size_mb': 100,
                'compress_old_logs': True
            },
            'backup_cleanup': {
                'enabled': True,
                'retention_days': 7,  # 保留7天內的所有備份
                'weekly_retention_weeks': 4,  # 保留4週的週一備份
                'monthly_retention_months': 3  # 保留3個月的月初備份
            },
            'auto_restart': {
                'enabled': True,
                'max_consecutive_failures': 5,
                'restart_delay_seconds': 60,
                'health_check_interval': 300  # 5分鐘
            },
            'performance_optimization': {
                'enabled': True,
                'memory_cleanup_threshold_mb': 300,
                'data_compression_enabled': True
            }
        }
    
    async def run_daily_maintenance(self) -> Dict:
        """執行每日維護任務"""
        maintenance_report = {
            'timestamp': datetime.now().isoformat(),
            'tasks_completed': [],
            'tasks_failed': [],
            'warnings': [],
            'metrics': {}
        }
        
        logger.info("🔧 開始執行每日維護任務...")
        
        try:
            # 1. 清理舊日誌
            if self.config['log_cleanup']['enabled']:
                await self._cleanup_old_logs(maintenance_report)
            
            # 2. 清理舊備份
            if self.config['backup_cleanup']['enabled']:
                await self._cleanup_old_backups(maintenance_report)
            
            # 3. 數據庫優化
            await self._optimize_data_storage(maintenance_report)
            
            # 4. 系統性能檢查
            await self._performance_check_and_optimization(maintenance_report)
            
            # 5. 健康檢查記錄維護
            if self.health_monitor:
                await self._maintain_health_history(maintenance_report)
            
            # 6. 清理健康檢查問題歷史
            await self._cleanup_health_problems(maintenance_report)
            
            # 7. 檢查磁碟空間
            await self._check_disk_space(maintenance_report)
            
            # 8. 生成維護報告
            await self._generate_maintenance_metrics(maintenance_report)
            
            # 記錄維護日誌
            self._log_maintenance_activity('daily_maintenance', 'completed', maintenance_report)
            
            logger.info(f"✅ 每日維護任務完成，共執行 {len(maintenance_report['tasks_completed'])} 項任務")
            
        except Exception as e:
            logger.error(f"每日維護任務執行失敗: {e}")
            maintenance_report['tasks_failed'].append(f"維護任務異常: {str(e)}")
            self._log_maintenance_activity('daily_maintenance', 'failed', {'error': str(e)})
        
        return maintenance_report
    
    async def _cleanup_old_logs(self, report: Dict):
        """清理舊日誌文件"""
        try:
            log_files = glob.glob("*.log") + glob.glob("logs/*.log")
            cleaned_files = []
            compressed_files = []
            
            cutoff_date = datetime.now() - timedelta(days=self.config['log_cleanup']['retention_days'])
            max_size_bytes = self.config['log_cleanup']['max_file_size_mb'] * 1024 * 1024
            
            for log_file in log_files:
                if not os.path.exists(log_file):
                    continue
                
                file_stat = os.stat(log_file)
                file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                file_size = file_stat.st_size
                
                # 如果文件過舊，刪除或壓縮
                if file_mtime < cutoff_date:
                    if self.config['log_cleanup']['compress_old_logs']:
                        # 壓縮舊日誌
                        compressed_path = f"{log_file}.{file_mtime.strftime('%Y%m%d')}.gz"
                        await self._compress_file(log_file, compressed_path)
                        compressed_files.append(log_file)
                    else:
                        # 直接刪除
                        os.remove(log_file)
                        cleaned_files.append(log_file)
                
                # 如果文件過大，進行輪轉
                elif file_size > max_size_bytes and log_file == 'bot.log':
                    await self._rotate_log_file(log_file)
                    cleaned_files.append(f"{log_file} (rotated)")
            
            report['tasks_completed'].append({
                'task': 'log_cleanup',
                'cleaned_files': len(cleaned_files),
                'compressed_files': len(compressed_files),
                'files': cleaned_files + [f"{f} (compressed)" for f in compressed_files]
            })
            
        except Exception as e:
            logger.error(f"日誌清理失敗: {e}")
            report['tasks_failed'].append(f"日誌清理失敗: {str(e)}")
    
    async def _cleanup_old_backups(self, report: Dict):
        """智慧清理舊備份"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                return
            
            backup_files = [f for f in os.listdir(backup_dir) 
                          if f.endswith('.json') and f != 'backup_record.json']
            
            # 按日期排序備份文件
            backup_files.sort()
            
            now = datetime.now()
            files_to_keep = set()
            files_to_remove = []
            
            for backup_file in backup_files:
                try:
                    # 從文件名解析日期 (YYYYMMDD.json)
                    date_str = backup_file.replace('.json', '')
                    file_date = datetime.strptime(date_str, '%Y%m%d')
                    days_old = (now - file_date).days
                    
                    # 保留策略
                    should_keep = False
                    
                    # 1. 保留最近7天的所有備份
                    if days_old <= self.config['backup_cleanup']['retention_days']:
                        should_keep = True
                        
                    # 2. 保留最近4週的週一備份
                    elif (days_old <= self.config['backup_cleanup']['weekly_retention_weeks'] * 7 
                          and file_date.weekday() == 0):  # 0 = 週一
                        should_keep = True
                        
                    # 3. 保留最近3個月的月初備份
                    elif (days_old <= self.config['backup_cleanup']['monthly_retention_months'] * 30 
                          and file_date.day == 1):  # 月初
                        should_keep = True
                    
                    if should_keep:
                        files_to_keep.add(backup_file)
                    else:
                        files_to_remove.append(backup_file)
                        
                except ValueError:
                    # 無法解析的文件名，保留以防萬一
                    files_to_keep.add(backup_file)
            
            # 執行刪除
            removed_count = 0
            for file_to_remove in files_to_remove:
                file_path = os.path.join(backup_dir, file_to_remove)
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"無法刪除備份文件 {file_to_remove}: {e}")
            
            report['tasks_completed'].append({
                'task': 'backup_cleanup',
                'total_backups': len(backup_files),
                'kept_backups': len(files_to_keep),
                'removed_backups': removed_count,
                'cleanup_strategy': 'smart_retention'
            })
            
        except Exception as e:
            logger.error(f"備份清理失敗: {e}")
            report['tasks_failed'].append(f"備份清理失敗: {str(e)}")
    
    async def _optimize_data_storage(self, report: Dict):
        """優化數據存儲"""
        try:
            optimization_results = {
                'original_size': 0,
                'optimized_size': 0,
                'space_saved': 0,
                'operations': []
            }
            
            # 獲取原始文件大小
            data_file = self.data_manager.data_file
            if os.path.exists(data_file):
                optimization_results['original_size'] = os.path.getsize(data_file)
                
                # 1. 清理空的或無效的伺服器記錄
                cleaned_data = False
                try:
                    original_data = self.data_manager.data.copy()
                    
                    # 檢查並清理無效的伺服器記錄
                    servers_to_remove = []
                    for server_id, server_data in original_data.items():
                        if server_id == 'rate_history':
                            continue
                        
                        if isinstance(server_data, dict):
                            # 如果伺服器記錄沒有設定通知頻道且沒有最近活動，考慮清理
                            if (not server_data.get('channel_id') and 
                                not server_data.get('last_notification_time') and
                                not server_data.get('last_rate_time')):
                                servers_to_remove.append(server_id)
                    
                    if servers_to_remove:
                        for server_id in servers_to_remove:
                            del self.data_manager.data[server_id]
                        self.data_manager.save_data()
                        cleaned_data = True
                        optimization_results['operations'].append(f"清理 {len(servers_to_remove)} 個無效伺服器記錄")
                
                except Exception as e:
                    logger.warning(f"數據清理過程中出現警告: {e}")
                
                # 2. 壓縮匯率歷史數據（移除重複的相鄰記錄）
                try:
                    if 'rate_history' in self.data_manager.data:
                        rate_history = self.data_manager.data['rate_history']
                        if isinstance(rate_history, dict):
                            compressed_history = {}
                            total_records_before = 0
                            total_records_after = 0
                            
                            for date, day_records in rate_history.items():
                                total_records_before += len(day_records)
                                
                                # 移除連續相同的匯率記錄
                                compressed_records = []
                                prev_rate = None
                                
                                for time_str, rate in day_records:
                                    if rate != prev_rate:  # 只保留匯率有變化的記錄
                                        compressed_records.append([time_str, rate])
                                        prev_rate = rate
                                
                                # 確保每天至少保留一條記錄
                                if not compressed_records and day_records:
                                    compressed_records = [day_records[-1]]
                                
                                compressed_history[date] = compressed_records
                                total_records_after += len(compressed_records)
                            
                            if total_records_after < total_records_before:
                                self.data_manager.data['rate_history'] = compressed_history
                                self.data_manager.save_data()
                                optimization_results['operations'].append(
                                    f"匯率歷史壓縮: {total_records_before} → {total_records_after} 記錄"
                                )
                
                except Exception as e:
                    logger.warning(f"匯率歷史壓縮過程中出現警告: {e}")
                
                # 獲取優化後的文件大小
                if os.path.exists(data_file):
                    optimization_results['optimized_size'] = os.path.getsize(data_file)
                    optimization_results['space_saved'] = (
                        optimization_results['original_size'] - optimization_results['optimized_size']
                    )
            
            report['tasks_completed'].append({
                'task': 'data_optimization',
                'results': optimization_results
            })
            
        except Exception as e:
            logger.error(f"數據優化失敗: {e}")
            report['tasks_failed'].append(f"數據優化失敗: {str(e)}")
    
    async def _performance_check_and_optimization(self, report: Dict):
        """性能檢查和優化"""
        try:
            performance_metrics = {
                'memory_before_mb': 0,
                'memory_after_mb': 0,
                'optimizations_applied': []
            }
            
            # 獲取當前記憶體使用
            current_process = psutil.Process()
            memory_before = current_process.memory_info().rss / (1024**2)
            performance_metrics['memory_before_mb'] = round(memory_before, 2)
            
            # 記憶體使用優化
            if memory_before > self.config['performance_optimization']['memory_cleanup_threshold_mb']:
                # 清理健康檢查歷史
                if self.health_monitor and hasattr(self.health_monitor, 'health_history'):
                    original_size = len(self.health_monitor.health_history)
                    # 只保留最近24小時的記錄
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    cutoff_str = cutoff_time.isoformat()
                    
                    self.health_monitor.health_history = [
                        entry for entry in self.health_monitor.health_history
                        if entry.get('timestamp', '') > cutoff_str
                    ]
                    
                    new_size = len(self.health_monitor.health_history)
                    if new_size < original_size:
                        performance_metrics['optimizations_applied'].append(
                            f"清理健康檢查歷史: {original_size} → {new_size}"
                        )
                
                # 清理維護日誌
                if len(self.maintenance_log) > self.max_log_size // 2:
                    original_size = len(self.maintenance_log)
                    self.maintenance_log = self.maintenance_log[-(self.max_log_size // 2):]
                    performance_metrics['optimizations_applied'].append(
                        f"清理維護日誌: {original_size} → {len(self.maintenance_log)}"
                    )
                
                # 強制垃圾回收
                import gc
                gc.collect()
                performance_metrics['optimizations_applied'].append("執行垃圾回收")
            
            # 獲取優化後的記憶體使用
            memory_after = current_process.memory_info().rss / (1024**2)
            performance_metrics['memory_after_mb'] = round(memory_after, 2)
            performance_metrics['memory_saved_mb'] = round(memory_before - memory_after, 2)
            
            report['tasks_completed'].append({
                'task': 'performance_optimization',
                'metrics': performance_metrics
            })
            
        except Exception as e:
            logger.error(f"性能優化失敗: {e}")
            report['tasks_failed'].append(f"性能優化失敗: {str(e)}")
    
    async def _maintain_health_history(self, report: Dict):
        """維護健康檢查歷史"""
        try:
            if not self.health_monitor:
                return
            
            maintenance_stats = {
                'original_records': len(self.health_monitor.health_history),
                'cleaned_records': 0
            }
            
            # 清理超過30天的健康檢查記錄
            cutoff_date = datetime.now() - timedelta(days=30)
            cutoff_str = cutoff_date.isoformat()
            
            original_count = len(self.health_monitor.health_history)
            self.health_monitor.health_history = [
                entry for entry in self.health_monitor.health_history
                if entry.get('timestamp', '') > cutoff_str
            ]
            
            maintenance_stats['cleaned_records'] = original_count - len(self.health_monitor.health_history)
            
            report['tasks_completed'].append({
                'task': 'health_history_maintenance',
                'stats': maintenance_stats
            })
            
        except Exception as e:
            logger.error(f"健康歷史維護失敗: {e}")
            report['tasks_failed'].append(f"健康歷史維護失敗: {str(e)}")
    
    async def _cleanup_health_problems(self, report: Dict):
        """清理健康檢查問題歷史"""
        try:
            cleaned_count = self.data_manager.cleanup_health_check_problems(days=7)
            
            report['tasks_completed'].append({
                'task': 'health_problems_cleanup',
                'cleaned_records': cleaned_count,
                'retention_days': 7
            })
            
        except Exception as e:
            logger.error(f"健康問題歷史清理失敗: {e}")
            report['tasks_failed'].append(f"健康問題歷史清理失敗: {str(e)}")
    
    async def _check_disk_space(self, report: Dict):
        """檢查磁碟空間"""
        try:
            disk_usage = psutil.disk_usage(os.getcwd())
            disk_info = {
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'usage_percent': round((disk_usage.used / disk_usage.total) * 100, 2)
            }
            
            # 磁碟空間警告
            if disk_info['usage_percent'] > 90:
                report['warnings'].append(f"磁碟空間不足: {disk_info['usage_percent']:.1f}% 已使用")
            elif disk_info['usage_percent'] > 80:
                report['warnings'].append(f"磁碟空間警告: {disk_info['usage_percent']:.1f}% 已使用")
            
            report['tasks_completed'].append({
                'task': 'disk_space_check',
                'disk_info': disk_info
            })
            
        except Exception as e:
            logger.error(f"磁碟空間檢查失敗: {e}")
            report['tasks_failed'].append(f"磁碟空間檢查失敗: {str(e)}")
    
    async def _generate_maintenance_metrics(self, report: Dict):
        """生成維護指標"""
        try:
            metrics = {
                'maintenance_duration_seconds': 0,
                'tasks_success_rate': 0,
                'total_tasks': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # 計算成功率
            total_tasks = len(report['tasks_completed']) + len(report['tasks_failed'])
            if total_tasks > 0:
                metrics['tasks_success_rate'] = round(len(report['tasks_completed']) / total_tasks * 100, 2)
            
            metrics['total_tasks'] = total_tasks
            
            report['metrics'] = metrics
            
        except Exception as e:
            logger.error(f"維護指標生成失敗: {e}")
    
    async def auto_restart_on_critical_failure(self) -> bool:
        """在關鍵故障時自動重啟"""
        try:
            if not self.config['auto_restart']['enabled']:
                return False
            
            if not self.health_monitor:
                logger.warning("無健康監控器，無法執行自動重啟檢查")
                return False
            
            # 檢查是否滿足重啟條件
            if (self.health_monitor.consecutive_failures >= 
                self.config['auto_restart']['max_consecutive_failures']):
                
                logger.warning(f"檢測到連續 {self.health_monitor.consecutive_failures} 次失敗，準備自動重啟")
                
                # 記錄重啟事件
                self._log_maintenance_activity('auto_restart', 'initiated', {
                    'consecutive_failures': self.health_monitor.consecutive_failures,
                    'reason': 'critical_failure_threshold_reached'
                })
                
                # 等待一段時間再重啟
                await asyncio.sleep(self.config['auto_restart']['restart_delay_seconds'])
                
                # 執行重啟
                return await self._execute_restart()
            
            return False
            
        except Exception as e:
            logger.error(f"自動重啟檢查失敗: {e}")
            return False
    
    async def _execute_restart(self) -> bool:
        """執行重啟操作"""
        try:
            logger.info("🔄 開始執行自動重啟...")
            
            # 創建重啟腳本
            restart_script = """#!/bin/bash
echo "自動重啟 Discord Bot..."
sleep 5
cd /home/ypwang/Discord_FX_Bot
./scripts/stop.sh
sleep 3
./scripts/start.sh
echo "重啟完成"
"""
            
            # 寫入臨時重啟腳本
            with open('/tmp/bot_restart.sh', 'w') as f:
                f.write(restart_script)
            
            os.chmod('/tmp/bot_restart.sh', 0o755)
            
            # 在背景執行重啟腳本
            subprocess.Popen(['/tmp/bot_restart.sh'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # 記錄重啟日誌
            self._log_maintenance_activity('auto_restart', 'executed', {
                'timestamp': datetime.now().isoformat(),
                'method': 'script_execution'
            })
            
            logger.info("✅ 重啟腳本已啟動")
            return True
            
        except Exception as e:
            logger.error(f"執行重啟失敗: {e}")
            self._log_maintenance_activity('auto_restart', 'failed', {'error': str(e)})
            return False
    
    async def _compress_file(self, source_path: str, target_path: str):
        """壓縮文件"""
        try:
            with open(source_path, 'rb') as f_in:
                with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(source_path, os.path.basename(source_path))
            
            # 刪除原文件
            os.remove(source_path)
            
        except Exception as e:
            logger.error(f"文件壓縮失敗 {source_path}: {e}")
            raise
    
    async def _rotate_log_file(self, log_file_path: str):
        """輪轉日誌文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{log_file_path}.{timestamp}"
            
            # 移動當前日誌
            shutil.move(log_file_path, backup_path)
            
            # 創建新的空日誌文件
            with open(log_file_path, 'w') as f:
                f.write(f"# 日誌輪轉於 {timestamp}\n")
            
        except Exception as e:
            logger.error(f"日誌輪轉失敗 {log_file_path}: {e}")
            raise
    
    def _log_maintenance_activity(self, activity_type: str, status: str, details: Dict):
        """記錄維護活動"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': activity_type,
            'status': status,
            'details': details
        }
        
        self.maintenance_log.append(log_entry)
        
        # 保持日誌大小在限制範圍內
        if len(self.maintenance_log) > self.max_log_size:
            self.maintenance_log = self.maintenance_log[-self.max_log_size:]
        
        logger.info(f"維護活動記錄: {activity_type} - {status}")
    
    def get_maintenance_summary(self, hours: int = 24) -> Dict:
        """獲取維護活動摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        recent_activities = [
            activity for activity in self.maintenance_log
            if activity.get('timestamp', '') > cutoff_str
        ]
        
        # 統計活動類型
        activity_stats = {}
        for activity in recent_activities:
            activity_type = activity.get('activity_type', 'unknown')
            status = activity.get('status', 'unknown')
            
            if activity_type not in activity_stats:
                activity_stats[activity_type] = {'completed': 0, 'failed': 0, 'initiated': 0}
            
            if status in activity_stats[activity_type]:
                activity_stats[activity_type][status] += 1
        
        return {
            'period_hours': hours,
            'total_activities': len(recent_activities),
            'activity_breakdown': activity_stats,
            'latest_activity': recent_activities[-1] if recent_activities else None
        }
    
    async def emergency_cleanup(self) -> Dict:
        """緊急清理（磁碟空間不足時使用）"""
        cleanup_report = {
            'timestamp': datetime.now().isoformat(),
            'actions_taken': [],
            'space_freed_mb': 0
        }
        
        try:
            logger.warning("🚨 執行緊急清理...")
            
            disk_before = psutil.disk_usage(os.getcwd())
            
            # 1. 立即清理所有舊日誌
            log_files = glob.glob("*.log*") + glob.glob("logs/*.log*")
            for log_file in log_files:
                if log_file != 'bot.log':  # 保留當前日誌
                    try:
                        os.remove(log_file)
                        cleanup_report['actions_taken'].append(f"刪除日誌: {log_file}")
                    except:
                        pass
            
            # 2. 清理超過3天的備份
            backup_dir = "backups"
            if os.path.exists(backup_dir):
                cutoff_date = datetime.now() - timedelta(days=3)
                for backup_file in os.listdir(backup_dir):
                    if backup_file.endswith('.json') and backup_file != 'backup_record.json':
                        try:
                            date_str = backup_file.replace('.json', '')
                            file_date = datetime.strptime(date_str, '%Y%m%d')
                            if file_date < cutoff_date:
                                os.remove(os.path.join(backup_dir, backup_file))
                                cleanup_report['actions_taken'].append(f"刪除舊備份: {backup_file}")
                        except:
                            pass
            
            # 3. 壓縮數據文件
            if os.path.exists(self.data_manager.data_file):
                await self._optimize_data_storage(cleanup_report)
            
            disk_after = psutil.disk_usage(os.getcwd())
            cleanup_report['space_freed_mb'] = round(
                (disk_before.used - disk_after.used) / (1024**2), 2
            )
            
            self._log_maintenance_activity('emergency_cleanup', 'completed', cleanup_report)
            
        except Exception as e:
            logger.error(f"緊急清理失敗: {e}")
            cleanup_report['actions_taken'].append(f"清理錯誤: {str(e)}")
        
        return cleanup_report
