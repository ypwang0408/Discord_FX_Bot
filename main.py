# -*- coding: utf-8 -*-
"""
Discord 玉山銀行日幣匯率監控機器人
重新整合的模組化版本 - Phase 4 Refactored
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import logging
from dotenv import load_dotenv

# 獲取腳本所在目錄的絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 導入自定義模組
from features import (
    ServerDataManager,
    ExchangeRateMonitor,
    DataBackupManager,
    RateChartGenerator,
    NotificationSystem,
    SystemManager
)

# 導入工具模組
from utils import (
    require_admin_permission,
    require_guild,
    EmbedBuilder,
    parse_timestamp_safe,
    format_timestamp_display,
    get_time_difference_display,
    ScheduleManager,
    NotificationHelper
)

# 導入命令模組
from commands import (
    register_rate_commands,
    register_config_commands,
    register_admin_commands,
    register_system_commands,
    register_help_commands
)

# 導入任務模組
from tasks import (
    create_rate_check_task,
    create_health_check_task,
    create_backup_task,
    create_maintenance_task
)

# 載入環境變數
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 設定日誌 - 使用日誌輪轉
from logging.handlers import TimedRotatingFileHandler
import sys

# 創建logs目錄（如果不存在）
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# 配置日誌格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_level = logging.INFO

# 創建日誌處理器
# 1. 按日輪轉的文件處理器（每天午夜輪轉，保留30天）
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(BASE_DIR, 'logs', 'bot.log'),
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(log_format))
file_handler.setLevel(log_level)

# 2. 控制台處理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(log_format))
console_handler.setLevel(log_level)

# 配置根日誌記錄器
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

# 設定Discord Bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# 初始化功能模組
data_manager = ServerDataManager(base_dir=BASE_DIR)
rate_monitor = ExchangeRateMonitor(data_manager)
backup_manager = DataBackupManager(data_manager, base_dir=BASE_DIR)
chart_generator = RateChartGenerator(data_manager)
notification_system = NotificationSystem(data_manager, bot)

# 初始化整合的系統管理器
try:
    system_manager = SystemManager(data_manager, base_dir=BASE_DIR)
    logger.info("✅ 系統管理器初始化成功")
except Exception as e:
    logger.error(f"❌ 系統管理器初始化失敗: {e}")
    system_manager = None

# 任務管理器類，替代全域變數避免競態條件
class TaskManager:
    def __init__(self):
        self.rate_check_task = None
        self.health_check_task = None

    async def cancel_all_tasks(self):
        """安全地取消所有任務"""
        if self.rate_check_task and not self.rate_check_task.done():
            self.rate_check_task.cancel()
            try:
                await self.rate_check_task
            except asyncio.CancelledError:
                pass

        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

    async def start_tasks(self):
        """啟動所有定期任務"""
        await self.cancel_all_tasks()

        # 創建任務函數
        schedule_rate_check, perform_rate_check = create_rate_check_task(
            data_manager, rate_monitor, notification_system
        )
        schedule_health_check, perform_health_check = create_health_check_task(
            system_manager
        )

        # 啟動任務
        self.rate_check_task = asyncio.create_task(schedule_rate_check())
        self.health_check_task = asyncio.create_task(schedule_health_check())
        logger.info("✅ 定期任務已啟動")

# 全域任務管理器實例
task_manager = TaskManager()

# ====== Bot 事件 ======

@bot.event
async def on_ready():
    print(f"Log as --> {bot.user}")
    print("玉山銀行日幣匯率監控已啟動!")

    # 註冊所有命令
    register_rate_commands(bot, data_manager, rate_monitor, chart_generator)
    register_config_commands(bot, data_manager)
    register_admin_commands(bot, backup_manager)
    register_system_commands(bot, data_manager, system_manager, task_manager)
    register_help_commands(bot)

    # 同步 slash commands
    try:
        print("正在同步 Slash Commands...")
        synced = await bot.tree.sync()
        print(f"✅ 成功同步了 {len(synced)} 個 Slash Commands")
        for cmd in synced:
            print(f"  - /{cmd.name}: {cmd.description}")
    except Exception as e:
        print(f"❌ 同步 Slash Commands 失敗: {e}")
        print("提示：確保機器人有 'applications.commands' 權限")

    # 創建任務函數
    schedule_rate_check, perform_rate_check = create_rate_check_task(
        data_manager, rate_monitor, notification_system
    )
    schedule_health_check, perform_health_check = create_health_check_task(
        system_manager
    )
    schedule_daily_backup = create_backup_task(backup_manager)
    schedule_daily_maintenance = create_maintenance_task(
        system_manager, data_manager, backup_manager, task_manager
    )

    # 啟動匯率檢查任務（每小時整點和30分）
    task_manager.rate_check_task = asyncio.create_task(schedule_rate_check())
    print("✅ 匯率檢查任務已啟動（每小時整點和30分）")

    # 啟動健康檢查任務（每小時15分和45分）
    task_manager.health_check_task = asyncio.create_task(schedule_health_check())
    print("✅ 健康檢查任務已啟動（每小時15分和45分）")

    # 啟動每日0:00自動備份任務
    asyncio.create_task(schedule_daily_backup())
    print("✅ 每日0:00自動備份任務已啟動")

    # 啟動每日凌晨2:00維護任務
    asyncio.create_task(schedule_daily_maintenance())
    print("✅ 每日凌晨2:00維護任務已啟動")

# ====== 錯誤處理 ======

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """處理 Slash Command 錯誤"""
    logger.error(f"Slash Command 錯誤: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message(f"❌ 執行指令時發生錯誤: {error}", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ 執行指令時發生錯誤: {error}", ephemeral=True)

# ====== 主程式入口 ======

if __name__ == "__main__":
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ 請設定環境變數 DISCORD_BOT_TOKEN")
        logger.error("❌ Please set environment variable DISCORD_BOT_TOKEN")
        exit(1)

    try:
        logger.info("🚀 啟動Discord機器人...")
        bot.run(bot_token)
    except Exception as e:
        logger.error(f"❌ 機器人啟動失敗: {e}")
        exit(1)
