# -*- coding: utf-8 -*-
"""
Health Check Task Module
Handles scheduled system health monitoring
"""

import logging

from utils import ScheduleManager

logger = logging.getLogger(__name__)


def create_health_check_task(system_manager):
    """
    Create health check task functions with dependencies

    Args:
        system_manager: SystemManager instance

    Returns:
        Tuple of (schedule_health_check, perform_health_check) functions
    """

    async def schedule_health_check():
        """每小時15分和45分執行健康檢查"""
        await ScheduleManager.run_on_schedule(
            minute_targets=[15, 45],
            task_func=perform_health_check,
            task_name="健康檢查"
        )

    async def perform_health_check():
        """執行健康檢查（使用快速檢查以提高效率）"""
        try:
            if system_manager:
                # 使用快速健康檢查以提高效率
                health_report = await system_manager.health_monitor.quick_health_check()

                # 💾 保存快速健康檢查結果
                if health_report and health_report.get('status'):
                    # 轉換格式以符合 system_manager 的期望
                    formatted_report = {
                        'overall_status': health_report.get('status'),
                        'details': health_report.get('checks', {}),
                        'timestamp': health_report.get('timestamp')
                    }
                    await system_manager._save_health_check_result(formatted_report, 'quick')

                # 記錄系統狀態
                overall_status = health_report.get('status', 'unknown')
                if overall_status != 'healthy':
                    logger.warning(f"⚠️ 系統健康狀態: {overall_status}")

                    # 如果狀態嚴重，執行詳細檢查
                    if overall_status == 'error':
                        logger.warning("🔍 執行詳細健康檢查...")
                        detailed_report = await system_manager.health_monitor.comprehensive_health_check()
                        logger.error(f"❌ 系統健康檢查發現問題: {detailed_report.get('errors', [])}")

                        # 如果狀態嚴重，啟動自動維護
                        if detailed_report.get('overall_status') == 'critical':
                            logger.error(f"❌ 系統處於嚴重狀態，啟動自動維護程序")
                            maintenance_result = await system_manager.perform_system_maintenance()

                            if maintenance_result.get('recovery_attempted'):
                                logger.info(f"🔄 自動恢復已啟動: {maintenance_result.get('recovery_actions', [])}")

                    # 檢查是否需要自動重啟
                    if system_manager.health_monitor.consecutive_failures >= 3:
                        logger.warning(f"🔄 連續失敗 {system_manager.health_monitor.consecutive_failures} 次，考慮自動重啟")
                        restart_attempted = await system_manager.auto_maintenance.auto_restart_on_critical_failure()
                        if restart_attempted:
                            logger.info("🔄 已啟動自動重啟程序")
                else:
                    logger.info(f"✅ 系統健康狀態正常")
            else:
                logger.warning("⚠️ 系統管理器未初始化，跳過健康檢查")

        except Exception as e:
            logger.error(f"健康檢查異常: {e}")

    return schedule_health_check, perform_health_check
