# -*- coding: utf-8 -*-
"""
系統健康監控模組
負責監控系統運行狀態、API健康度、資源使用情況等
"""

import asyncio
import aiohttp
import psutil
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import traceback

logger = logging.getLogger(__name__)


class SystemHealthMonitor:
    """系統健康監控器"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.health_history = []
        self.max_history_size = 1000  # 保留最近1000次檢查記錄
        self.last_check_time = None
        self.consecutive_failures = 0
        
        # 健康檢查配置
        self.thresholds = {
            'memory_usage_percent': 85.0,  # 記憶體使用率警告閾值
            'disk_usage_percent': 90.0,    # 磁碟使用率警告閾值
            'api_response_time_ms': 5000,  # API回應時間警告閾值(ms)
            'consecutive_api_failures': 3,  # 連續API失敗次數警告閾值
            'data_file_age_hours': 24,     # 數據文件過舊警告閾值(小時)
        }
    
    async def comprehensive_health_check(self) -> Dict:
        """全面系統健康檢查"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': [],
            'metrics': {}
        }
        
        try:
            # 1. API健康檢查
            api_health = await self.check_api_health()
            health_report['checks']['api_health'] = api_health
            
            # 2. 系統資源檢查
            resource_health = await self.check_resource_usage()
            health_report['checks']['resource_health'] = resource_health
            
            # 3. 數據完整性檢查
            data_integrity = await self.check_data_integrity()
            health_report['checks']['data_integrity'] = data_integrity
            
            # 4. 文件系統檢查
            file_system_health = await self.check_file_system()
            health_report['checks']['file_system'] = file_system_health
            
            # 5. 服務運行狀態檢查
            service_health = await self.check_service_status()
            health_report['checks']['service_status'] = service_health
            
            # 彙總健康狀態
            health_report = self._evaluate_overall_health(health_report)
            
            # 記錄到歷史
            self._add_to_history(health_report)
            
            self.last_check_time = datetime.now()
            
            logger.info(f"健康檢查完成，整體狀態: {health_report['overall_status']}")
            
        except Exception as e:
            logger.error(f"健康檢查過程中發生錯誤: {e}")
            health_report['overall_status'] = 'error'
            health_report['errors'].append(f"健康檢查異常: {str(e)}")
        
        return health_report
    
    async def check_api_health(self) -> Dict:
        """API健康檢查"""
        api_results = {
            'status': 'healthy',
            'apis': {},
            'response_times': {},
            'failures': 0
        }
        
        # 測試API列表
        apis_to_test = [
            {
                'name': 'esun_bank',
                'url': 'https://www.esunbank.com/zh-tw/personal/deposit/rate/forex/foreign-exchange-rates',
                'timeout': 10
            },
            {
                'name': 'backup_api',
                'url': 'https://api.exchangerate-api.com/v4/latest/JPY',
                'timeout': 5
            }
        ]
        
        for api_config in apis_to_test:
            api_name = api_config['name']
            try:
                start_time = time.time()
                
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=api_config['timeout'])
                ) as session:
                    async with session.get(api_config['url']) as response:
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        api_results['apis'][api_name] = {
                            'status': 'healthy' if response.status == 200 else 'warning',
                            'http_status': response.status,
                            'response_time_ms': round(response_time, 2)
                        }
                        
                        api_results['response_times'][api_name] = response_time
                        
                        # 檢查回應時間是否過慢
                        if response_time > self.thresholds['api_response_time_ms']:
                            api_results['apis'][api_name]['status'] = 'warning'
                            api_results['apis'][api_name]['warning'] = 'slow_response'
                        
                        if response.status != 200:
                            api_results['failures'] += 1
                            
            except asyncio.TimeoutError:
                api_results['apis'][api_name] = {
                    'status': 'error',
                    'error': 'timeout',
                    'response_time_ms': api_config['timeout'] * 1000
                }
                api_results['failures'] += 1
                
            except Exception as e:
                api_results['apis'][api_name] = {
                    'status': 'error',
                    'error': str(e),
                    'response_time_ms': None
                }
                api_results['failures'] += 1
        
        # 評估整體API健康狀態
        if api_results['failures'] >= len(apis_to_test):
            api_results['status'] = 'error'
        elif api_results['failures'] > 0:
            api_results['status'] = 'warning'
        
        # 更新連續失敗計數
        if api_results['status'] == 'error':
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        return api_results
    
    async def check_resource_usage(self) -> Dict:
        """系統資源使用檢查"""
        try:
            # 記憶體使用情況
            memory = psutil.virtual_memory()
            
            # 磁碟使用情況（當前目錄所在磁碟）
            disk = psutil.disk_usage(os.getcwd())
            
            # CPU使用情況
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 網路連接情況
            network_connections = len(psutil.net_connections())
            
            resource_data = {
                'status': 'healthy',
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 2)
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'network': {
                    'connections': network_connections
                },
                'warnings': []
            }
            
            # 檢查警告閾值
            if memory.percent > self.thresholds['memory_usage_percent']:
                resource_data['status'] = 'warning'
                resource_data['warnings'].append(f"記憶體使用率過高: {memory.percent:.1f}%")
            
            if resource_data['disk']['percent'] > self.thresholds['disk_usage_percent']:
                resource_data['status'] = 'warning'
                resource_data['warnings'].append(f"磁碟使用率過高: {resource_data['disk']['percent']:.1f}%")
            
            if cpu_percent > 80:  # CPU使用率警告閾值
                resource_data['status'] = 'warning'
                resource_data['warnings'].append(f"CPU使用率過高: {cpu_percent:.1f}%")
            
            return resource_data
            
        except Exception as e:
            logger.error(f"資源使用檢查失敗: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_data_integrity(self) -> Dict:
        """數據完整性檢查"""
        try:
            integrity_report = {
                'status': 'healthy',
                'data_file': {},
                'backup_files': {},
                'rate_history': {},
                'warnings': []
            }
            
            # 檢查主數據文件
            data_file_path = self.data_manager.data_file
            if os.path.exists(data_file_path):
                file_stat = os.stat(data_file_path)
                file_age_hours = (time.time() - file_stat.st_mtime) / 3600
                
                integrity_report['data_file'] = {
                    'exists': True,
                    'size_bytes': file_stat.st_size,
                    'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    'age_hours': round(file_age_hours, 2)
                }
                
                # 檢查文件是否過舊
                if file_age_hours > self.thresholds['data_file_age_hours']:
                    integrity_report['warnings'].append(f"數據文件過舊: {file_age_hours:.1f} 小時")
                    integrity_report['status'] = 'warning'
                
                # 嘗試加載和驗證JSON格式
                try:
                    with open(data_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    integrity_report['data_file']['json_valid'] = True
                    integrity_report['data_file']['servers_count'] = len([k for k in data.keys() if k != 'rate_history'])
                except json.JSONDecodeError:
                    integrity_report['data_file']['json_valid'] = False
                    integrity_report['warnings'].append("數據文件JSON格式錯誤")
                    integrity_report['status'] = 'error'
                    
            else:
                integrity_report['data_file'] = {'exists': False}
                integrity_report['warnings'].append("主數據文件不存在")
                integrity_report['status'] = 'error'
            
            # 檢查備份文件
            backup_dir = "backups"
            if os.path.exists(backup_dir):
                backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json') and f != 'backup_record.json']
                integrity_report['backup_files'] = {
                    'count': len(backup_files),
                    'latest': max(backup_files) if backup_files else None
                }
            else:
                integrity_report['backup_files'] = {'count': 0, 'latest': None}
                integrity_report['warnings'].append("備份目錄不存在")
            
            # 檢查匯率歷史數據
            try:
                rate_history = self.data_manager.get_rate_history(days=7)
                integrity_report['rate_history'] = {
                    'records_count': len(rate_history),
                    'latest_record': rate_history[-1]['timestamp'] if rate_history else None,
                    'date_range_days': 7
                }
                
                if len(rate_history) == 0:
                    integrity_report['warnings'].append("最近7天無匯率記錄")
                    integrity_report['status'] = 'warning'
                    
            except Exception as e:
                integrity_report['rate_history'] = {'error': str(e)}
                integrity_report['warnings'].append(f"匯率歷史檢查失敗: {str(e)}")
            
            return integrity_report
            
        except Exception as e:
            logger.error(f"數據完整性檢查失敗: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_file_system(self) -> Dict:
        """文件系統健康檢查"""
        try:
            file_system_report = {
                'status': 'healthy',
                'permissions': {},
                'disk_space': {},
                'important_files': {},
                'warnings': []
            }
            
            # 檢查重要文件和目錄的權限
            important_paths = [
                'main.py',
                'features/',
                'server_data.json',
                'backups/',
                'bot.log'
            ]
            
            for path in important_paths:
                if os.path.exists(path):
                    file_system_report['permissions'][path] = {
                        'readable': os.access(path, os.R_OK),
                        'writable': os.access(path, os.W_OK),
                        'executable': os.access(path, os.X_OK) if os.path.isfile(path) else None
                    }
                else:
                    file_system_report['permissions'][path] = {'exists': False}
                    if path in ['main.py', 'features/']:  # 重要文件
                        file_system_report['warnings'].append(f"重要文件/目錄不存在: {path}")
                        file_system_report['status'] = 'warning'
            
            # 檢查日誌文件大小
            log_file = 'bot.log'
            if os.path.exists(log_file):
                log_size = os.path.getsize(log_file)
                file_system_report['important_files']['bot_log'] = {
                    'size_mb': round(log_size / (1024**2), 2),
                    'size_bytes': log_size
                }
                
                # 如果日誌文件過大（超過50MB），給出警告
                if log_size > 50 * 1024 * 1024:
                    file_system_report['warnings'].append(f"日誌文件過大: {log_size / (1024**2):.1f} MB")
                    file_system_report['status'] = 'warning'
            
            return file_system_report
            
        except Exception as e:
            logger.error(f"文件系統檢查失敗: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def check_service_status(self) -> Dict:
        """服務運行狀態檢查"""
        try:
            service_report = {
                'status': 'healthy',
                'uptime': {},
                'bot_process': {},
                'warnings': []
            }
            
            # 檢查程序運行時間
            current_process = psutil.Process()
            create_time = datetime.fromtimestamp(current_process.create_time())
            uptime = datetime.now() - create_time
            
            service_report['uptime'] = {
                'start_time': create_time.isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_hours': round(uptime.total_seconds() / 3600, 2),
                'uptime_days': uptime.days
            }
            
            # 檢查程序資源使用
            memory_info = current_process.memory_info()
            service_report['bot_process'] = {
                'pid': current_process.pid,
                'memory_mb': round(memory_info.rss / (1024**2), 2),
                'cpu_percent': current_process.cpu_percent(),
                'threads': current_process.num_threads(),
                'open_files': len(current_process.open_files())
            }
            
            # 檢查是否有記憶體洩漏跡象（簡單檢查）
            if service_report['bot_process']['memory_mb'] > 500:  # 超過500MB警告
                service_report['warnings'].append(f"程序記憶體使用量較高: {service_report['bot_process']['memory_mb']} MB")
                service_report['status'] = 'warning'
            
            return service_report
            
        except Exception as e:
            logger.error(f"服務狀態檢查失敗: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _evaluate_overall_health(self, health_report: Dict) -> Dict:
        """評估整體健康狀態"""
        # 統計各項檢查的狀態
        error_count = 0
        warning_count = 0
        
        for check_name, check_result in health_report['checks'].items():
            if isinstance(check_result, dict):
                status = check_result.get('status', 'unknown')
                if status == 'error':
                    error_count += 1
                    health_report['errors'].append(f"{check_name}: {check_result.get('error', '未知錯誤')}")
                elif status == 'warning':
                    warning_count += 1
                    warnings = check_result.get('warnings', [])
                    health_report['warnings'].extend([f"{check_name}: {w}" for w in warnings])
        
        # 確定整體狀態
        if error_count > 0:
            health_report['overall_status'] = 'error'
        elif warning_count > 0:
            health_report['overall_status'] = 'warning'
        else:
            health_report['overall_status'] = 'healthy'
        
        # 添加摘要指標
        health_report['metrics'] = {
            'checks_total': len(health_report['checks']),
            'checks_healthy': len([c for c in health_report['checks'].values() 
                                 if isinstance(c, dict) and c.get('status') == 'healthy']),
            'checks_warning': warning_count,
            'checks_error': error_count,
            'consecutive_failures': self.consecutive_failures
        }
        
        return health_report
    
    def _add_to_history(self, health_report: Dict):
        """添加健康檢查記錄到歷史"""
        # 只保留關鍵信息，減少記憶體使用
        history_entry = {
            'timestamp': health_report['timestamp'],
            'overall_status': health_report['overall_status'],
            'error_count': len(health_report['errors']),
            'warning_count': len(health_report['warnings']),
            'consecutive_failures': self.consecutive_failures
        }
        
        self.health_history.append(history_entry)
        
        # 保持歷史記錄在限制範圍內
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    def get_health_summary(self, hours: int = 24) -> Dict:
        """獲取指定時間範圍內的健康狀態摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        recent_history = [
            entry for entry in self.health_history 
            if entry['timestamp'] > cutoff_str
        ]
        
        if not recent_history:
            return {
                'period_hours': hours,
                'total_checks': 0,
                'status': 'no_data'
            }
        
        # 統計狀態分布
        status_counts = {'healthy': 0, 'warning': 0, 'error': 0}
        for entry in recent_history:
            status = entry['overall_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 計算可用性百分比
        total_checks = len(recent_history)
        healthy_checks = status_counts['healthy']
        availability_percent = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        return {
            'period_hours': hours,
            'total_checks': total_checks,
            'status_distribution': status_counts,
            'availability_percent': round(availability_percent, 2),
            'latest_status': recent_history[-1]['overall_status'] if recent_history else 'unknown',
            'max_consecutive_failures': max([entry['consecutive_failures'] for entry in recent_history], default=0)
        }
    
    def is_system_healthy(self) -> bool:
        """簡單的系統健康狀態判斷"""
        if not self.health_history:
            return False  # 沒有檢查記錄，認為不健康
        
        latest_status = self.health_history[-1]['overall_status']
        return latest_status in ['healthy', 'warning']  # 錯誤狀態才認為不健康
    
    async def quick_health_check(self) -> Dict:
        """快速健康檢查（僅檢查關鍵項目）"""
        try:
            quick_report = {
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'checks': {}
            }
            
            # 快速API檢查（只檢查一個API）
            try:
                start_time = time.time()
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as session:
                    async with session.get('https://api.exchangerate-api.com/v4/latest/JPY') as response:
                        response_time = (time.time() - start_time) * 1000
                        quick_report['checks']['api'] = {
                            'status': 'healthy' if response.status == 200 else 'error',
                            'response_time_ms': round(response_time, 2)
                        }
            except Exception as e:
                logger.warning(f"API 連接檢查失敗: {e}")
                quick_report['checks']['api'] = {'status': 'error', 'error': str(e)}
            
            # 快速資源檢查
            memory = psutil.virtual_memory()
            quick_report['checks']['memory'] = {
                'status': 'healthy' if memory.percent < 90 else 'warning',
                'percent': memory.percent
            }
            
            # 快速數據文件檢查
            if os.path.exists(self.data_manager.data_file):
                quick_report['checks']['data_file'] = {'status': 'healthy'}
            else:
                quick_report['checks']['data_file'] = {'status': 'error'}
                quick_report['status'] = 'error'
            
            # 評估整體狀態
            if any(check.get('status') == 'error' for check in quick_report['checks'].values()):
                quick_report['status'] = 'error'
            elif any(check.get('status') == 'warning' for check in quick_report['checks'].values()):
                quick_report['status'] = 'warning'
            
            return quick_report
            
        except Exception as e:
            logger.error(f"快速健康檢查失敗: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }
