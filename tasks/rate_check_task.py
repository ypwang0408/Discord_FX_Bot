# -*- coding: utf-8 -*-
"""
Rate Check Task Module
Handles scheduled exchange rate monitoring
"""

from datetime import datetime
import logging

from utils import ScheduleManager, NotificationHelper
from features.data_manager import get_minute_precision_timestamp

logger = logging.getLogger(__name__)


def create_rate_check_task(data_manager, rate_monitor, notification_system):
    """
    Create rate check task functions with dependencies

    Args:
        data_manager: ServerDataManager instance
        rate_monitor: ExchangeRateMonitor instance
        notification_system: NotificationSystem instance

    Returns:
        Tuple of (schedule_rate_check, perform_rate_check) functions
    """

    async def schedule_rate_check():
        """每小時整點和30分執行匯率檢查"""
        await ScheduleManager.run_on_schedule(
            minute_targets=[0, 30],
            task_func=perform_rate_check,
            task_name="匯率檢查"
        )

    async def perform_rate_check():
        """執行匯率檢查和通知"""
        # 檢查所有有設定通知頻道的伺服器
        servers_with_channels = data_manager.get_all_servers_with_channels()

        if not servers_with_channels:
            return

        try:
            # 🔥 優化：API只調用一次
            rate = await rate_monitor.get_esun_jpy_rate()

            if rate is None:
                logger.warning("無法獲取匯率，跳過本次檢查")
                return

            # 📊 統一添加到匯率歷史（只需要做一次）
            data_manager.add_rate_history("global", rate)

            logger.info(f"📈 獲取匯率成功: {rate:.4f} (將通知 {len(servers_with_channels)} 個伺服器)")

            # 🔄 處理所有伺服器的通知邏輯
            now = datetime.now()
            for server_info in servers_with_channels:
                guild_id = server_info['guild_id']
                channel_id = server_info['channel_id']
                threshold = server_info['threshold']
                use_everyone_mention = server_info['use_everyone_mention']
                server_data = server_info['server_data']

                try:
                    current_above_threshold = rate >= threshold

                    # 更新匯率狀態和時間戳記
                    rate_monitor.update_server_state(
                        guild_id,
                        last_rate=rate,
                        last_rate_time=get_minute_precision_timestamp()
                    )

                    # 判斷是否需要發送通知（使用NotificationHelper統一邏輯）
                    last_was_above_threshold = server_data.get('last_was_above_threshold')
                    should_notify, notification_reason = NotificationHelper.should_notify_rate_alert(
                        rate, threshold, last_was_above_threshold, now
                    )

                    # 更新狀態記錄
                    rate_monitor.update_server_state(
                        guild_id,
                        last_was_above_threshold=current_above_threshold
                    )

                    # 發送通知
                    if should_notify:
                        success = await notification_system.send_rate_alert(
                            channel_id, rate, threshold, guild_id,
                            notification_reason, use_everyone_mention
                        )

                        if success:
                            # 更新最後通知時間
                            rate_monitor.update_server_state(
                                guild_id,
                                last_notification_time=get_minute_precision_timestamp()
                            )

                            logger.info(f"✅ 發送匯率警報到伺服器 {guild_id}: {rate:.4f} < {threshold}, 原因: {notification_reason}")

                except Exception as e:
                    logger.error(f"❌ 處理伺服器 {guild_id} 通知時發生錯誤: {e}")

        except Exception as e:
            logger.error(f"❌ 檢查匯率時發生全域錯誤: {e}")

    return schedule_rate_check, perform_rate_check
