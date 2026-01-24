# -*- coding: utf-8 -*-
"""
Time parsing and formatting utilities
Provides safe timestamp parsing with error handling
"""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_timestamp_safe(timestamp_str: Optional[str]) -> Optional[datetime]:
    """
    Safely parse timestamp string with error handling

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        datetime object if parsing succeeds, None otherwise

    Example:
        >>> dt = parse_timestamp_safe("2025-01-24T10:30:00")
        >>> dt.strftime("%Y-%m-%d")
        '2025-01-24'
    """
    if not timestamp_str:
        return None

    try:
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"解析時間戳失敗: {e}, timestamp: {timestamp_str}")
        return None


def format_timestamp_display(
    timestamp_str: Optional[str],
    format_str: str = "%m-%d %H:%M"
) -> str:
    """
    Format timestamp for display with fallback on error

    Args:
        timestamp_str: ISO format timestamp string
        format_str: strftime format string (default: "%m-%d %H:%M")

    Returns:
        Formatted timestamp string or error message

    Example:
        >>> format_timestamp_display("2025-01-24T10:30:00")
        '01-24 10:30'
        >>> format_timestamp_display("2025-01-24T10:30:00", "%Y/%m/%d")
        '2025/01/24'
    """
    dt = parse_timestamp_safe(timestamp_str)
    if dt:
        return dt.strftime(format_str)
    return "時間格式錯誤 / Invalid time format"


def get_time_difference_display(timestamp_str: Optional[str]) -> str:
    """
    Get human-readable time difference from now

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        Human-readable time difference string

    Example:
        >>> get_time_difference_display("2025-01-24T10:00:00")  # If now is 10:30
        '30 分鐘前'
        >>> get_time_difference_display("2025-01-23T10:00:00")  # If now is next day
        '1 天前'
    """
    dt = parse_timestamp_safe(timestamp_str)
    if not dt:
        return "未知 / Unknown"

    diff = datetime.now() - dt
    total_seconds = diff.total_seconds()

    if total_seconds < 60:
        return "剛剛 / Just now"
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = int(total_seconds / 60)
        return f"{minutes} 分鐘前 / {minutes} min ago"
    elif total_seconds < 86400:  # Less than 1 day
        hours = int(total_seconds / 3600)
        return f"{hours} 小時前 / {hours} hours ago"
    else:
        days = diff.days
        return f"{days} 天前 / {days} days ago"
