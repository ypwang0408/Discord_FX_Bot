# -*- coding: utf-8 -*-
"""
Schedule Manager - Unified scheduling logic
統一的排程管理器
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Callable, Optional, Awaitable

logger = logging.getLogger(__name__)


class ScheduleManager:
    """
    統一的排程管理器
    提供通用的排程計算和執行邏輯
    """

    @staticmethod
    def calculate_next_run(minute_targets: List[int]) -> tuple[datetime, float]:
        """
        計算下一次執行時間

        Args:
            minute_targets: 目標分鐘列表 (例如: [0, 30] 表示整點和30分)

        Returns:
            tuple: (下次執行時間, 睡眠秒數)
        """
        now = datetime.now()
        minute_targets_sorted = sorted(minute_targets)

        # 找到下一個目標分鐘
        next_target = None
        for target in minute_targets_sorted:
            if now.minute < target:
                next_target = target
                break

        if next_target is None:
            # 所有目標分鐘都已過，使用下一小時的第一個目標
            next_target = minute_targets_sorted[0]
            next_run_time = now.replace(minute=next_target, second=0, microsecond=0) + timedelta(hours=1)
        else:
            # 使用當前小時的下一個目標
            next_run_time = now.replace(minute=next_target, second=0, microsecond=0)

        sleep_seconds = (next_run_time - now).total_seconds()

        return next_run_time, sleep_seconds

    @staticmethod
    async def run_on_schedule(
        minute_targets: List[int],
        task_func: Callable[[], Awaitable[None]],
        task_name: str = "Task"
    ) -> None:
        """
        按排程執行任務

        Args:
            minute_targets: 目標分鐘列表
            task_func: 要執行的異步任務函數
            task_name: 任務名稱（用於日誌記錄）
        """
        while True:
            try:
                # 計算下次執行時間
                next_run_time, sleep_seconds = ScheduleManager.calculate_next_run(minute_targets)

                logger.info(
                    f"⏰ {task_name} - 下次執行時間: {next_run_time.strftime('%H:%M')} "
                    f"({sleep_seconds/60:.1f}分鐘後)"
                )

                # 等待到執行時間
                await asyncio.sleep(sleep_seconds)

                # 執行任務
                await task_func()

            except asyncio.CancelledError:
                logger.info(f"🔄 {task_name} 已被取消")
                break
            except Exception as e:
                logger.error(f"❌ {task_name} 異常: {e}")
                # 等待10分鐘後重試
                await asyncio.sleep(600)
