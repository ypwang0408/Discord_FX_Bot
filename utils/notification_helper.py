# -*- coding: utf-8 -*-
"""
Notification Helper - Unified notification decision logic
統一的通知決策邏輯
"""

from datetime import datetime
from typing import Optional, Tuple


class NotificationHelper:
    """
    通知決策輔助類
    集中處理通知條件判斷邏輯
    """

    @staticmethod
    def should_notify_rate_alert(
        rate: float,
        threshold: float,
        last_was_above_threshold: Optional[bool],
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        判斷是否應該發送匯率警報通知

        通知規則:
        1. 匯率從高於閾值變為低於閾值 (狀態改變)
        2. 早上9:00且匯率低於閾值
        3. 晚上9:00且匯率低於閾值

        Args:
            rate: 當前匯率
            threshold: 閾值
            last_was_above_threshold: 上次匯率是否高於閾值
            current_time: 當前時間 (如果為None則使用當前系統時間)

        Returns:
            tuple: (是否通知, 通知原因)
        """
        if current_time is None:
            current_time = datetime.now()

        # 條件1: 匯率低於閾值且之前高於閾值 (狀態改變)
        if (rate < threshold and
            last_was_above_threshold is not None and
            last_was_above_threshold):
            return True, "匯率跌破閾值 / Rate dropped below threshold"

        # 條件2: 匯率低於閾值且當前時間是早上9點整
        if (rate < threshold and
            current_time.hour == 9 and current_time.minute == 0):
            return True, "早上9點定時通知 / 9 AM scheduled notification"

        # 條件3: 匯率低於閾值且當前時間是晚上9點整
        if (rate < threshold and
            current_time.hour == 21 and current_time.minute == 0):
            return True, "晚上9點定時通知 / 9 PM scheduled notification"

        # 不滿足任何通知條件
        return False, ""
