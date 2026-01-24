# -*- coding: utf-8 -*-
"""
Backup Task Module
Handles scheduled daily backup operations
"""

import asyncio
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)


def create_backup_task(backup_manager):
    """
    Create backup task function with dependencies

    Args:
        backup_manager: DataBackupManager instance

    Returns:
        schedule_daily_backup function
    """

    async def schedule_daily_backup():
        """每天0:00執行備份任務"""
        while True:
            try:
                # 計算到下一個0:00的時間
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (tomorrow - now).total_seconds()

                logger.info(f"⏰ 下次備份時間: {tomorrow.strftime('%Y-%m-%d %H:%M:%S')} ({sleep_seconds/3600:.1f}小時後)")

                # 等待到0:00
                await asyncio.sleep(sleep_seconds)

                # 執行備份
                logger.info("🔄 開始執行每日0:00自動備份...")
                backup_path = backup_manager.create_backup()

                if backup_path:
                    logger.info(f"✅ 每日自動備份完成: {os.path.basename(backup_path)}")
                    logger.info("📦 備份清理策略：7天內保留所有，超過7天只保留星期一備份")
                else:
                    logger.error("❌ 每日自動備份失敗")

            except Exception as e:
                logger.error(f"每日備份任務異常: {e}")
                # 等待1小時後重試
                await asyncio.sleep(3600)

    return schedule_daily_backup
