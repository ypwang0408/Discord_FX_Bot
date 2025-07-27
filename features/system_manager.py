# -*- coding: utf-8 -*-
"""
系統管理整合模組
整合健康監控、自動化運維和系統報告功能
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .health_monitor import SystemHealthMonitor
from .auto_maintenance import AutoMaintenance

logger = logging.getLogger(__name__)


class SystemManager:
    """系統管理器 - 整合健康監控和自動化運維"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        
        # 初始化子模組
        self.health_monitor = SystemHealthMonitor(data_manager)
        self.auto_maintenance = AutoMaintenance(data_manager, self.health_monitor)
        
        # 系統狀態快取
        self._last_health_check = None
        self._last_maintenance_report = None
        
    async def get_comprehensive_system_report(self) -> Dict:
        """獲取全面的系統報告（整合健康狀態和運維信息）"""
        try:
            # 並行執行健康檢查和獲取維護摘要
            health_task = asyncio.create_task(self.health_monitor.comprehensive_health_check())
            maintenance_task = asyncio.create_task(self._get_maintenance_summary())
            
            health_report, maintenance_summary = await asyncio.gather(
                health_task, maintenance_task, return_exceptions=True
            )
            
            # 處理可能的異常
            if isinstance(health_report, Exception):
                logger.error(f"健康檢查失敗: {health_report}")
                health_report = {'overall_status': 'error', 'error': str(health_report)}
            
            if isinstance(maintenance_summary, Exception):
                logger.error(f"維護摘要獲取失敗: {maintenance_summary}")
                maintenance_summary = {'error': str(maintenance_summary)}
            
            # 🔄 儲存健康檢查結果到持久化存儲
            if health_report and 'overall_status' in health_report:
                await self._save_health_check_result(health_report)
            
            # 整合報告
            integrated_report = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': health_report.get('overall_status', 'unknown'),
                'health': health_report,
                'maintenance': maintenance_summary,
                'recommendations': self._generate_recommendations(health_report, maintenance_summary),
                'quick_stats': self._extract_quick_stats(health_report, maintenance_summary)
            }
            
            # 快取結果
            self._last_health_check = health_report
            self._last_maintenance_report = maintenance_summary
            
            return integrated_report
            
        except Exception as e:
            logger.error(f"系統報告生成失敗: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': f"系統報告生成失敗: {str(e)}",
                'recommendations': ['請檢查系統日誌以獲取更多信息'],
                'quick_stats': {}
            }
    
    async def get_quick_system_status(self) -> Dict:
        """獲取快速系統狀態（用於頻繁檢查）"""
        try:
            quick_health = await self.health_monitor.quick_health_check()
            maintenance_summary = self.auto_maintenance.get_maintenance_summary(hours=1)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'status': quick_health.get('status', 'unknown'),
                'health_checks': len(quick_health.get('checks', {})),
                'recent_maintenance': maintenance_summary.get('total_activities', 0),
                'uptime_hours': self._calculate_uptime_hours(),
                'memory_usage_mb': self._get_current_memory_usage(),
                'is_healthy': quick_health.get('status') in ['healthy', 'warning']
            }
        except Exception as e:
            logger.error(f"快速狀態檢查失敗: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e),
                'is_healthy': False
            }
    
    async def perform_system_maintenance(self, maintenance_type: str = "daily") -> Dict:
        """執行系統維護並返回結果"""
        try:
            if maintenance_type == "daily":
                return await self.auto_maintenance.run_daily_maintenance()
            elif maintenance_type == "emergency":
                return await self.auto_maintenance.emergency_cleanup()
            else:
                return {
                    'error': f"不支援的維護類型: {maintenance_type}",
                    'supported_types': ['daily', 'emergency']
                }
        except Exception as e:
            logger.error(f"系統維護執行失敗: {e}")
            return {
                'error': f"維護執行失敗: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_system_health_and_maintain(self) -> Dict:
        """檢查系統健康並在必要時執行維護"""
        try:
            # 先執行健康檢查
            health_report = await self.health_monitor.comprehensive_health_check()
            
            # 根據健康狀態決定是否需要維護
            maintenance_needed = False
            maintenance_type = "daily"
            
            if health_report.get('overall_status') == 'error':
                maintenance_needed = True
                maintenance_type = "emergency"
            elif len(health_report.get('warnings', [])) >= 3:
                maintenance_needed = True
                maintenance_type = "daily"
            
            result = {
                'health_check': health_report,
                'maintenance_performed': False,
                'maintenance_report': None,
                'recommendations': []
            }
            
            # 如果需要維護，執行維護
            if maintenance_needed:
                logger.info(f"系統健康檢查建議執行 {maintenance_type} 維護")
                maintenance_report = await self.perform_system_maintenance(maintenance_type)
                result['maintenance_performed'] = True
                result['maintenance_report'] = maintenance_report
                result['recommendations'].append(f"已自動執行 {maintenance_type} 維護")
            
            return result
            
        except Exception as e:
            logger.error(f"健康檢查和維護流程失敗: {e}")
            return {
                'error': f"檢查和維護流程失敗: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_recommendations(self, health_report: Dict, maintenance_summary: Dict) -> List[str]:
        """根據健康和維護狀態生成建議"""
        recommendations = []
        
        try:
            # 基於健康狀態的建議
            if health_report.get('overall_status') == 'error':
                recommendations.append("🚨 系統存在嚴重問題，建議立即檢查錯誤日誌")
                if health_report.get('errors'):
                    recommendations.append("📋 重點關注: " + "; ".join(health_report['errors'][:2]))
            
            elif health_report.get('overall_status') == 'warning':
                recommendations.append("⚠️ 系統有警告，建議執行維護任務")
                if health_report.get('warnings'):
                    recommendations.append("📝 需要注意: " + "; ".join(health_report['warnings'][:2]))
            
            # 基於資源使用的建議
            if 'checks' in health_report and 'resource_health' in health_report['checks']:
                resource_info = health_report['checks']['resource_health']
                if isinstance(resource_info, dict):
                    memory_percent = resource_info.get('memory', {}).get('percent', 0)
                    disk_percent = resource_info.get('disk', {}).get('percent', 0)
                    
                    if memory_percent > 80:
                        recommendations.append(f"💾 記憶體使用率較高 ({memory_percent:.1f}%)，建議執行記憶體清理")
                    
                    if disk_percent > 85:
                        recommendations.append(f"💽 磁碟使用率較高 ({disk_percent:.1f}%)，建議清理舊文件")
            
            # 基於維護歷史的建議
            if isinstance(maintenance_summary, dict):
                total_activities = maintenance_summary.get('total_activities', 0)
                if total_activities == 0:
                    recommendations.append("🔧 建議執行定期維護任務以保持系統健康")
                
                activity_breakdown = maintenance_summary.get('activity_breakdown', {})
                if 'daily_maintenance' in activity_breakdown:
                    daily_stats = activity_breakdown['daily_maintenance']
                    if daily_stats.get('failed', 0) > 0:
                        recommendations.append("⚡ 最近的維護任務有失敗項目，建議檢查維護日誌")
            
            # 如果沒有特別建議，給出通用建議
            if not recommendations:
                recommendations.append("✅ 系統運行正常，建議保持定期檢查和維護")
            
        except Exception as e:
            logger.warning(f"生成建議時出現錯誤: {e}")
            recommendations.append("📊 建議定期檢查系統狀態以確保穩定運行")
        
        return recommendations[:5]  # 最多返回5個建議
    
    def _extract_quick_stats(self, health_report: Dict, maintenance_summary: Dict) -> Dict:
        """提取關鍵統計信息"""
        stats = {}
        
        try:
            # 健康統計
            if 'metrics' in health_report:
                metrics = health_report['metrics']
                stats['health_checks_total'] = metrics.get('checks_total', 0)
                stats['health_checks_healthy'] = metrics.get('checks_healthy', 0)
                stats['consecutive_failures'] = metrics.get('consecutive_failures', 0)
            
            # 維護統計
            if isinstance(maintenance_summary, dict):
                stats['maintenance_activities_24h'] = maintenance_summary.get('total_activities', 0)
            
            # 系統資源統計
            if ('checks' in health_report and 
                'resource_health' in health_report['checks'] and
                isinstance(health_report['checks']['resource_health'], dict)):
                
                resource_info = health_report['checks']['resource_health']
                stats['memory_usage_percent'] = resource_info.get('memory', {}).get('percent', 0)
                stats['disk_usage_percent'] = resource_info.get('disk', {}).get('percent', 0)
                stats['memory_used_gb'] = resource_info.get('memory', {}).get('used_gb', 0)
            
            # API統計
            if ('checks' in health_report and 
                'api_health' in health_report['checks'] and
                isinstance(health_report['checks']['api_health'], dict)):
                
                api_info = health_report['checks']['api_health']
                stats['api_failures'] = api_info.get('failures', 0)
                stats['api_status'] = api_info.get('status', 'unknown')
        
        except Exception as e:
            logger.warning(f"提取統計信息時出現錯誤: {e}")
        
        return stats
    
    async def _get_maintenance_summary(self) -> Dict:
        """獲取維護摘要"""
        try:
            return self.auto_maintenance.get_maintenance_summary(24)
        except Exception as e:
            logger.error(f"獲取維護摘要失敗: {e}")
            return {'error': str(e)}
    
    def _calculate_uptime_hours(self) -> float:
        """計算系統運行時間（小時）"""
        try:
            import psutil
            current_process = psutil.Process()
            create_time = datetime.fromtimestamp(current_process.create_time())
            uptime = datetime.now() - create_time
            return round(uptime.total_seconds() / 3600, 2)
        except:
            return 0.0
    
    def _get_current_memory_usage(self) -> float:
        """獲取當前記憶體使用量（MB）"""
        try:
            import psutil
            current_process = psutil.Process()
            memory_info = current_process.memory_info()
            return round(memory_info.rss / (1024**2), 2)
        except:
            return 0.0
    
    async def _save_health_check_result(self, health_report: Dict):
        """保存健康檢查結果到持久化存儲"""
        try:
            # 轉換健康報告格式以符合 data_manager 的期望
            formatted_report = {
                'status': health_report.get('overall_status', 'unknown'),
                'checks': health_report.get('details', {}),
                'warnings': [],
                'errors': []
            }
            
            # 提取警告和錯誤
            for check_name, check_result in health_report.get('details', {}).items():
                if isinstance(check_result, dict) and 'status' in check_result:
                    status = check_result['status']
                    message = check_result.get('message', '')
                    
                    if status == 'warning':
                        formatted_report['warnings'].append(f"{check_name}: {message}")
                    elif status == 'critical':
                        formatted_report['errors'].append(f"{check_name}: {message}")
            
            # 使用 data_manager 保存健康檢查記錄
            self.data_manager.add_health_check_record(formatted_report)
            
            logger.info(f"✅ 健康檢查結果已保存: {health_report.get('overall_status')}")
            
        except Exception as e:
            logger.error(f"❌ 保存健康檢查結果時發生錯誤: {e}")
    
    # 提供統一的任務接口
    async def periodic_health_check(self):
        """定期健康檢查任務"""
        return await self.health_monitor.quick_health_check()
    
    async def periodic_maintenance(self):
        """定期維護任務"""
        now = datetime.now()
        if now.hour == 2:  # 凌晨2點執行
            return await self.auto_maintenance.run_daily_maintenance()
        return None
    
    async def auto_recovery_check(self):
        """自動恢復檢查"""
        return await self.auto_maintenance.auto_restart_on_critical_failure()
    
    def get_system_manager_info(self) -> Dict:
        """獲取系統管理器信息"""
        return {
            'version': '1.0',
            'components': ['health_monitor', 'auto_maintenance'],
            'features': [
                'comprehensive_health_checks',
                'automated_maintenance',
                'system_recovery',
                'integrated_reporting'
            ],
            'supported_commands': ['/system', '/health', '/maintenance']
        }
