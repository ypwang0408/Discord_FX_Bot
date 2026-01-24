# -*- coding: utf-8 -*-
"""
Maintenance Task Module
Handles scheduled daily maintenance operations
"""

import asyncio
from datetime import datetime, timedelta
import os
import logging

from utils import parse_timestamp_safe

logger = logging.getLogger(__name__)


def create_maintenance_task(system_manager, data_manager, backup_manager, task_manager):
    """
    Create maintenance task function with dependencies

    Args:
        system_manager: SystemManager instance
        data_manager: ServerDataManager instance
        backup_manager: DataBackupManager instance
        task_manager: TaskManager instance

    Returns:
        schedule_daily_maintenance function
    """

    async def schedule_daily_maintenance():
        """每天凌晨2:00執行維護任務"""
        while True:
            try:
                # 計算到下午2:00的時間
                now = datetime.now()
                target_time = now.replace(hour=2, minute=0, second=0, microsecond=0)

                # 如果現在已經過了今天的2:00，設定為明天的2:00
                if now.hour >= 2:
                    target_time += timedelta(days=1)

                sleep_seconds = (target_time - now).total_seconds()

                logger.info(f"⏰ 下次維護時間: {target_time.strftime('%Y-%m-%d %H:%M:%S')} ({sleep_seconds/3600:.1f}小時後)")

                # 等待到2:00
                await asyncio.sleep(sleep_seconds)

                # 執行維護任務
                logger.info("🔧 開始執行每日自動運維任務...")

                if system_manager:
                    # 1. 執行詳細的健康檢查
                    logger.info("🏥 執行維護前詳細健康檢查...")
                    try:
                        detailed_health_report = await system_manager.health_monitor.comprehensive_health_check()
                        health_status = detailed_health_report.get('overall_status', 'unknown')
                        logger.info(f"📊 系統健康狀態: {health_status}")

                        # 💾 保存詳細健康檢查結果到持久化存儲
                        if detailed_health_report and detailed_health_report.get('overall_status'):
                            formatted_report = {
                                'overall_status': detailed_health_report.get('overall_status'),
                                'details': detailed_health_report.get('checks', {}),
                                'timestamp': detailed_health_report.get('timestamp'),
                                'warnings': detailed_health_report.get('warnings', []),
                                'errors': detailed_health_report.get('errors', [])
                            }
                            await system_manager._save_health_check_result(formatted_report, 'detailed')
                            logger.info("✅ 詳細健康檢查結果已保存")

                            # 🔍 驗證詳細檢查結果是否正確保存
                            saved_check = data_manager.data.get('health_check_history', {}).get('last_detailed_check')
                            if saved_check and saved_check.get('timestamp'):
                                logger.info(f"✅ 確認詳細檢查已記錄: {saved_check['timestamp']}")
                            else:
                                logger.warning("⚠️ 詳細檢查保存驗證失敗，將重試...")
                                # 重試保存
                                data_manager.record_health_check(formatted_report, 'detailed')
                                data_manager.save_data()
                        else:
                            logger.warning("⚠️ 詳細健康檢查報告無效，無法保存")

                        if health_status != 'healthy':
                            logger.warning(f"⚠️ 發現系統健康問題，將在維護中處理")
                            if detailed_health_report.get('errors'):
                                logger.error(f"❌ 健康檢查錯誤: {detailed_health_report['errors'][:3]}")
                            if detailed_health_report.get('warnings'):
                                logger.warning(f"⚠️ 健康檢查警告: {detailed_health_report['warnings'][:3]}")
                        else:
                            logger.info("✅ 系統健康狀態良好")

                    except Exception as e:
                        logger.error(f"❌ 詳細健康檢查失敗: {e}")
                        health_status = 'error'

                    # 2. 執行日常維護任務
                    maintenance_report = await system_manager.auto_maintenance.run_daily_maintenance()

                    # 記錄維護結果
                    completed_tasks = len(maintenance_report.get('tasks_completed', []))
                    failed_tasks = len(maintenance_report.get('tasks_failed', []))
                    warnings = len(maintenance_report.get('warnings', []))

                    logger.info(f"✅ 每日運維完成: {completed_tasks} 成功, {failed_tasks} 失敗, {warnings} 警告")

                    # 如果有失敗的任務，記錄詳細信息
                    if failed_tasks > 0:
                        logger.warning(f"⚠️ 運維任務失敗項目: {maintenance_report.get('tasks_failed', [])}")

                    # 4. 🔍 維護完成狀態驗證 - 確保所有工作都正確完成並記錄
                    logger.info("🔍 驗證維護工作完成狀態...")
                    maintenance_validation_passed = True
                    validation_issues = []

                    try:
                        # 驗證詳細健康檢查是否已正確記錄
                        health_history = data_manager.data.get('health_check_history', {})
                        last_detailed = health_history.get('last_detailed_check')

                        if not last_detailed or not last_detailed.get('timestamp'):
                            maintenance_validation_passed = False
                            validation_issues.append("詳細健康檢查結果未正確保存")
                            logger.error("❌ 詳細健康檢查結果驗證失敗")
                        else:
                            # 檢查時間戳是否是最近的（1小時內）
                            timestamp_str = last_detailed['timestamp'].replace('Z', '+00:00')
                            check_time = parse_timestamp_safe(timestamp_str)
                            if check_time:
                                time_diff = (datetime.now() - check_time.replace(tzinfo=None)).total_seconds()
                                if time_diff > 3600:  # 超過1小時
                                    maintenance_validation_passed = False
                                    validation_issues.append(f"詳細健康檢查時間過舊 ({time_diff/60:.1f}分鐘前)")
                                else:
                                    logger.info(f"✅ 詳細健康檢查記錄驗證通過: {last_detailed['timestamp']}")
                            else:
                                maintenance_validation_passed = False
                                validation_issues.append("詳細健康檢查時間戳解析失敗")
                                logger.error("❌ 詳細健康檢查時間戳解析失敗")

                        # 驗證維護任務是否都成功完成
                        if failed_tasks > 0:
                            maintenance_validation_passed = False
                            validation_issues.append(f"有 {failed_tasks} 個維護任務失敗")
                            logger.warning(f"⚠️ 維護任務驗證: 有失敗項目")
                        else:
                            logger.info(f"✅ 維護任務驗證通過: {completed_tasks} 個任務全部成功")

                        # 驗證數據文件完整性
                        if not os.path.exists(data_manager.data_file):
                            maintenance_validation_passed = False
                            validation_issues.append("主數據文件不存在")
                        else:
                            file_size = os.path.getsize(data_manager.data_file)
                            if file_size < 100:  # 文件太小可能有問題
                                maintenance_validation_passed = False
                                validation_issues.append(f"數據文件異常小 ({file_size} bytes)")
                            else:
                                logger.info(f"✅ 數據文件驗證通過: {file_size} bytes")

                        if maintenance_validation_passed:
                            logger.info("✅ 維護工作完成狀態驗證通過，準備進行備份和重新調度")
                        else:
                            logger.error(f"❌ 維護工作驗證失敗: {', '.join(validation_issues)}")
                            logger.error("❌ 將延遲備份和重新調度，等待問題解決")

                    except Exception as e:
                        logger.error(f"❌ 維護完成狀態驗證過程異常: {e}")
                        maintenance_validation_passed = False
                        validation_issues.append(f"驗證過程異常: {str(e)}")

                    # 5. 💾 只有在驗證通過後才執行備份
                    if maintenance_validation_passed:
                        logger.info("💾 維護工作已完成並驗證，開始創建備份...")
                        try:
                            backup_path = backup_manager.create_backup()
                            if backup_path:
                                logger.info(f"✅ 維護後備份創建成功: {os.path.basename(backup_path)}")
                            else:
                                logger.warning("⚠️ 維護後備份創建失敗")
                        except Exception as e:
                            logger.error(f"❌ 維護後備份創建異常: {e}")
                    else:
                        logger.warning("⚠️ 由於驗證失敗，跳過備份創建")

                    # 6. 執行維護後的健康檢查驗證（在重新調度之前）
                    logger.info("🔍 執行維護後健康檢查驗證...")
                    try:
                        post_maintenance_health = await system_manager.health_monitor.quick_health_check()
                        post_health_status = post_maintenance_health.get('status', 'unknown')
                        logger.info(f"📋 維護後系統狀態: {post_health_status}")

                        if post_health_status == 'healthy':
                            logger.info("✅ 維護後系統狀態良好")
                        else:
                            logger.warning(f"⚠️ 維護後系統仍有問題: {post_health_status}")
                            # 如果系統狀態不佳，也影響重新調度決策
                            if maintenance_validation_passed:  # 只有在之前驗證通過時才更新狀態
                                maintenance_validation_passed = False
                                validation_issues.append(f"維護後系統狀態不佳: {post_health_status}")

                    except Exception as e:
                        logger.error(f"❌ 維護後健康檢查失敗: {e}")

                    # 7. 只有在所有驗證都通過後才重新調度任務
                    if maintenance_validation_passed:
                        logger.info("🔄 所有維護工作已完成並驗證，開始重新調度定期任務...")
                    else:
                        logger.warning(f"⚠️ 維護驗證未通過({', '.join(validation_issues)})，延遲重新調度")
                        logger.info("⏰ 將在1小時後重新檢查並嘗試重新調度")
                        await asyncio.sleep(3600)  # 等待1小時後重試
                        continue  # 回到循環開始，重新檢查狀態
                    # 8. 重新調度定期任務（只有在驗證通過時執行）
                    logger.info("🔄 重新調度定期任務以確保時間同步準確性...")
                    try:
                        # 使用 TaskManager 重新調度任務
                        await task_manager.start_tasks()
                        logger.info("✅ 所有定期任務已重新調度")

                        # 計算下次檢查時間並記錄
                        now = datetime.now()

                        # 下次匯率檢查時間
                        if now.minute < 30:
                            next_rate_check = now.replace(minute=30, second=0, microsecond=0)
                        else:
                            next_rate_check = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

                        # 下次健康檢查時間
                        if now.minute < 15:
                            next_health_check = now.replace(minute=15, second=0, microsecond=0)
                        elif now.minute < 45:
                            next_health_check = now.replace(minute=45, second=0, microsecond=0)
                        else:
                            next_health_check = now.replace(minute=15, second=0, microsecond=0) + timedelta(hours=1)

                        logger.info(f"📅 下次匯率檢查: {next_rate_check.strftime('%H:%M')}")
                        logger.info(f"📅 下次健康檢查: {next_health_check.strftime('%H:%M')}")

                        # 記錄成功完成的維護
                        logger.info("⚙️ 完整的每日維護循環已成功完成")
                        logger.info("✅ 所有維護工作已完成、驗證、備份並重新調度")

                    except Exception as e:
                        logger.error(f"❌ 重新調度任務失敗: {e}")

                    # 記錄維護完成後的狀態
                    logger.info("⚙️ 每日維護任務已完成，系統繼續監控中...")

                    # 計算並記錄下次維護時間
                    tomorrow = datetime.now() + timedelta(days=1)
                    next_maintenance_time = tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)
                    logger.info(f"⏰ 下次維護時間: {next_maintenance_time.strftime('%Y-%m-%d %H:%M:%S')} (24.0小時後)")

                else:
                    logger.warning("⚠️ 系統管理器未初始化，跳過每日維護")

            except Exception as e:
                logger.error(f"每日運維任務異常: {e}")
                # 等待1小時後重試
                await asyncio.sleep(3600)

    return schedule_daily_maintenance
