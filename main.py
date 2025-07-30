# -*- coding: utf-8 -*-
"""
Discord 玉山銀行日幣匯率監控機器人
重新整合的模組化版本
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv

# 導入自定義模組
from features import (
    ServerDataManager,
    ExchangeRateMonitor,
    DataBackupManager,
    RateChartGenerator,
    NotificationSystem,
    SystemManager
)
from features.data_manager import get_minute_precision_timestamp

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 設定Discord Bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# 初始化功能模組
data_manager = ServerDataManager()
rate_monitor = ExchangeRateMonitor(data_manager)
backup_manager = DataBackupManager(data_manager)
chart_generator = RateChartGenerator(data_manager)
notification_system = NotificationSystem(data_manager, bot)

# 初始化整合的系統管理器
try:
    system_manager = SystemManager(data_manager)
    logger.info("✅ 系統管理器初始化成功")
except Exception as e:
    logger.error(f"❌ 系統管理器初始化失敗: {e}")
    system_manager = None

# 全域任務追蹤器
rate_check_task = None
health_check_task = None

# ====== Bot 事件 ======

@bot.event
async def on_ready():
    print(f"Log as --> {bot.user}")
    print("玉山銀行日幣匯率監控已啟動!")
    
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
    
    # 啟動匯率檢查任務（每小時整點和30分）
    global rate_check_task, health_check_task
    rate_check_task = asyncio.create_task(schedule_rate_check())
    print("✅ 匯率檢查任務已啟動（每小時整點和30分）")
    
    # 啟動健康檢查任務（每小時15分和45分）
    health_check_task = asyncio.create_task(schedule_health_check())
    print("✅ 健康檢查任務已啟動（每小時15分和45分）")
    
    # 啟動每日0:00自動備份任務
    asyncio.create_task(schedule_daily_backup())
    print("✅ 每日0:00自動備份任務已啟動")
    
    # 啟動每日凌晨2:00維護任務
    asyncio.create_task(schedule_daily_maintenance())
    print("✅ 每日凌晨2:00維護任務已啟動")

# ====== Slash Commands ======

@bot.tree.command(name="rate", description="查詢當前日幣匯率 / Check current JPY exchange rate")
async def rate_slash(interaction: discord.Interaction):
    """手動查詢當前日幣匯率"""
    if not interaction.guild:
        await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
        return
        
    await interaction.response.send_message("🔍 正在查詢玉山銀行日幣匯率... / Checking E.SUN Bank JPY rate...")
    
    rate = await rate_monitor.get_esun_jpy_rate()
    guild_id = interaction.guild.id
    threshold = data_manager.get_threshold(guild_id)
    
    if rate is not None:
        # 更新伺服器狀態
        rate_monitor.update_server_state(
            guild_id,
            last_rate=rate,
            last_rate_time=get_minute_precision_timestamp(),
            last_was_above_threshold=rate >= threshold
        )
        
        # 新增到匯率歷史
        data_manager.add_rate_history(guild_id, rate)
        
        # 創建嵌入式訊息
        embed = discord.Embed(
            title="💴 玉山銀行日幣匯率 / E.SUN Bank JPY Rate",
            color=0x00ff00 if rate >= threshold else 0xff0000,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="當前匯率 / Current Rate",
            value=f"**{rate:.4f} JPY/TWD**",
            inline=False
        )
        
        embed.add_field(
            name="監控閾值 / Threshold",
            value=f"{threshold} JPY/TWD",
            inline=False
        )
        
        status = "❌ 高於閾值 / Above threshold" if rate >= threshold else "⚠️ 低於閾值 / Below threshold"
        embed.add_field(
            name="狀態 / Status",
            value=status,
            inline=False
        )
        
        embed.set_footer(text="資料來源: 玉山銀行 / Source: E.SUN Bank")
        
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("❌ 無法獲取匯率資訊，請稍後再試。/ Cannot get exchange rate, please try again later.")

@bot.tree.command(name="threshold", description="設定匯率監控閾值 / Set exchange rate monitoring threshold")
async def threshold_slash(interaction: discord.Interaction, threshold: float):
    """設定匯率監控閾值"""
    if not interaction.guild:
        await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
        return
        
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    if 0.1 <= threshold <= 1.0:
        data_manager.set_threshold(interaction.guild.id, threshold)
        await interaction.response.send_message(f"✅ 已設定新的監控閾值: **{threshold} JPY/TWD** / New threshold set: **{threshold} JPY/TWD**")
    else:
        await interaction.response.send_message("❌ 閾值必須在 0.1 到 1.0 之間 / Threshold must be between 0.1 and 1.0")

@bot.tree.command(name="channel", description="將當前頻道設為通知頻道 / Set current channel as notification channel")
async def channel_slash(interaction: discord.Interaction):
    """設定通知頻道為當前頻道"""
    if not interaction.guild:
        await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
        return
        
    data_manager.set_channel_id(interaction.guild.id, interaction.channel.id)
    await interaction.response.send_message(f"✅ 已設定通知頻道為: **{interaction.channel.name}** / Notification channel set to: **{interaction.channel.name}**")

@bot.tree.command(name="mention", description="設定是否使用@everyone通知 / Set @everyone mention notifications")
async def mention_slash(interaction: discord.Interaction, enable: bool):
    """設定是否使用@everyone通知"""
    if not interaction.guild:
        await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
        return
        
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    data_manager.set_use_everyone_mention(interaction.guild.id, enable)
    status = "啟用 / Enabled" if enable else "停用 / Disabled"
    await interaction.response.send_message(f"✅ 已設定@everyone通知為: **{status}** / @everyone mentions set to: **{status}**")

@bot.tree.command(name="status", description="顯示機器人運行狀態 / Show bot status")
async def status_slash(interaction: discord.Interaction):
    """顯示機器人狀態"""
    if not interaction.guild:
        await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
        return
        
    guild_id = interaction.guild.id
    server_data = data_manager.get_server_data(guild_id)
    
    embed = discord.Embed(
        title="🤖 機器人狀態 / Bot Status",
        color=0x0099ff,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="監控閾值 / Threshold",
        value=f"{server_data['threshold']} JPY/TWD",
        inline=False
    )
    
    channel_id = server_data['channel_id']
    embed.add_field(
        name="通知頻道 / Notification Channel",
        value=f"{f'<#{channel_id}>' if channel_id else '未設定 / Not set'}",
        inline=False
    )
    
    # 分隔線
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    last_rate = server_data['last_rate']
    last_rate_time = server_data.get('last_rate_time')
    
    if last_rate and last_rate_time:
        try:
            rate_time = datetime.fromisoformat(last_rate_time)
            rate_display = f"{last_rate:.4f} JPY/TWD ({rate_time.strftime('%m-%d %H:%M')})"
        except:
            rate_display = f"{last_rate:.4f} JPY/TWD" if last_rate else "無 / None"
    else:
        rate_display = f"{last_rate:.4f} JPY/TWD" if last_rate else "無 / None"
    
    embed.add_field(
        name="最後匯率 / Last Rate",
        value=f"{rate_display}",
        inline=False
    )
    
    last_was_above = server_data['last_was_above_threshold']
    embed.add_field(
        name="上次狀態 / Last Status",
        value=f"{'❌ 高於閾值 / Above threshold' if last_was_above else '⚠️ 低於閾值 / Below threshold' if last_was_above is not None else '❓ 未知 / Unknown'}",
        inline=False
    )
    
    embed.add_field(
        name="監控狀態 / Monitor Status",
        value="✅ 運行中 / Running",
        inline=False
    )
    
    # 分隔線
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    last_notification = server_data['last_notification_time']
    if last_notification:
        try:
            notification_time = datetime.fromisoformat(last_notification)
            embed.add_field(
                name="最後通知時間 / Last Notification",
                value=f"{notification_time.strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )
        except:
            pass
    
    embed.add_field(
        name="@everyone 通知 / @everyone Mention",
        value=f"{'啟用 / Enabled' if server_data['use_everyone_mention'] else '停用 / Disabled'}",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="chart", description="生成匯率趨勢圖表 / Generate rate trend chart")
async def chart_slash(interaction: discord.Interaction, days: int = 7):
    """生成匯率圖表"""
    if not interaction.guild:
        await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
        return
    
    if not (1 <= days <= 30):
        await interaction.response.send_message("❌ 天數必須在1-30之間 / Days must be between 1-30")
        return
    
    await interaction.response.send_message("📊 正在生成匯率圖表... / Generating rate chart...")
    
    try:
        chart_buffer = await chart_generator.generate_rate_chart(interaction.guild.id, days)
        
        if chart_buffer is None:
            await interaction.followup.send("❌ 資料不足，無法生成圖表（需要至少2個資料點）/ Insufficient data to generate chart (need at least 2 data points)")
            return
        
        # 創建Discord文件物件
        file = discord.File(chart_buffer, filename=f"rate_chart_{days}days.png")
        
        embed = discord.Embed(
            title=f"📈 日幣匯率趨勢圖 / JPY Rate Trend (Last {days} Days)",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.set_image(url=f"attachment://rate_chart_{days}days.png")
        embed.set_footer(text="資料來源: 玉山銀行 / Source: E.SUN Bank")
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        logger.error(f"生成圖表失敗: {e}")
        await interaction.followup.send("❌ 生成圖表時發生錯誤 / Error occurred while generating chart")

@bot.tree.command(name="backup", description="手動創建數據備份 / Manually create data backup")
async def backup_slash(interaction: discord.Interaction):
    """手動備份數據"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    await interaction.response.send_message("💾 正在創建備份... / Creating backup...")
    
    try:
        backup_path = backup_manager.create_backup()
        
        if backup_path:
            embed = discord.Embed(
                title="✅ 備份創建成功 / Backup Created Successfully",
                description=f"備份檔案 / Backup File: `{os.path.basename(backup_path)}`",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # 獲取檔案大小
            file_size = os.path.getsize(backup_path)
            embed.add_field(
                name="檔案資訊 / File Info",
                value=f"大小 / Size: {file_size} bytes\n位置 / Location: `{backup_path}`",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ 備份創建失敗 / Backup creation failed")
            
    except Exception as e:
        logger.error(f"手動備份失敗: {e}")
        await interaction.followup.send("❌ 備份創建時發生錯誤 / Error occurred during backup creation")

@bot.tree.command(name="list_backups", description="列出所有備份 / List all backups")
async def list_backups_slash(interaction: discord.Interaction):
    """列出備份"""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    try:
        backups = backup_manager.list_backups()
        
        if not backups:
            await interaction.response.send_message("📂 目前沒有任何備份檔案 / No backup files currently exist")
            return
        
        embed = discord.Embed(
            title="📋 備份檔案列表 / Backup Files List",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # 只顯示最近10個備份
        recent_backups = backups[-10:]
        backup_list = []
        
        for backup in recent_backups:
            backup_time = datetime.fromisoformat(backup['timestamp'])
            backup_list.append(
                f"• `{backup['filename']}`\n"
                f"  📅 {backup_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  🗄️ {backup['servers_count']} servers | "
                f"📦 {backup['file_size']} bytes"
            )
        
        embed.add_field(
            name=f"最近 {len(recent_backups)} 個備份 / Recent {len(recent_backups)} Backups",
            value="\n\n".join(backup_list) if backup_list else "無備份 / No backups",
            inline=False
        )
        
        if len(backups) > 10:
            embed.set_footer(text=f"總共有 {len(backups)} 個備份檔案，僅顯示最近10個 / Total {len(backups)} backup files, showing recent 10 only")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"列出備份失敗: {e}")
        await interaction.response.send_message("❌ 獲取備份列表時發生錯誤 / Error occurred while getting backup list")

# 繼續在下一段添加其他slash commands...

@bot.tree.command(name="help", description="顯示幫助訊息 / Show help message")
async def help_slash(interaction: discord.Interaction):
    """顯示幫助訊息"""
    embed = discord.Embed(
        title="📚 指令說明 / Command Help",
        description="玉山銀行日幣匯率監控機器人 / E.SUN Bank JPY Rate Monitor Bot",
        color=0x00ff00
    )
    
    embed.add_field(
        name="📋 可用指令 / Available Commands",
        value="**基本功能 / Basic Functions:**\n"
              "`/rate` - 查詢當前匯率 / Check current rate\n"
              "`/threshold <value>` - 設定監控閾值 / Set threshold\n"
              "`/channel` - 設定通知頻道 / Set notification channel\n"
              "`/status` - 查看機器人狀態 / Check bot status\n"
              "`/rules` - 顯示通知規則 / Show notification rules\n"
              "`/help` - 顯示此幫助訊息 / Show this help",
        inline=False
    )
    
    embed.add_field(
        name="🔧 管理員指令 / Admin Commands",
        value="`/permissions` - 檢查機器人權限 / Check bot permissions\n"
              "`/sync` - 同步 Slash Commands / Sync Slash Commands\n"
              "`/system` - 全面系統狀態檢查 / Comprehensive system check\n"
              "`/mention <true/false>` - 設定@everyone通知 / Set @everyone notifications\n"
              "`/backup` - 手動創建數據備份 / Manual data backup\n"
              "`/list_backups` - 列出所有備份 / List all backups\n"
              "`/health [quick]` - 系統健康檢查 / System health check\n"
              "`/maintenance [operation]` - 系統維護管理 / System maintenance",
        inline=False
    )
    
    # 分隔線
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    embed.add_field(
        name="📊 進階功能 / Advanced Features",
        value="`/chart <days>` - 生成匯率趨勢圖表 / Generate rate trend chart\n"
              "• 天數範圍：1-30天 / Days range: 1-30 days\n"
              "• 顯示匯率變化和閾值線 / Shows rate changes and threshold line",
        inline=False
    )
    
    # 分隔線
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    embed.add_field(
        name="💡 使用提示 / Usage Tips",
        value="• 輸入 `/` 即可看到所有指令並自動補全 / Type `/` to see all commands with autocomplete\n"
              "• 機器人會在整點和30分自動檢查匯率 / Bot automatically checks rate at :00 and :30\n"
              "• 智慧通知系統避免重複訊息 / Smart notification system prevents spam\n"
              "• 每個伺服器有獨立的設定 / Each server has independent settings\n"
              "• 系統在15分和45分進行健康檢查 / Health checks at :15 and :45",
        inline=False
    )
    
    embed.set_footer(text="匯率檢查: 整點和30分 | 健康檢查: 15分和45分 / Rate check: :00 & :30 | Health check: :15 & :45")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rules", description="顯示通知規則 / Show notification rules")
async def rules_slash(interaction: discord.Interaction):
    """顯示通知規則"""
    embed = discord.Embed(
        title="📋 通知規則 / Notification Rules",
        description="智慧通知系統，避免重複訊息 / Smart notification system to avoid spam",
        color=0xff9900
    )
    
    embed.add_field(
        name="🕐 檢查時間 / Check Schedule",
        value="匯率檢查: 每小時的整點和30分 / Rate check: Every hour at :00 and :30\n"
              "健康檢查: 每小時的15分和45分 / Health check: Every hour at :15 and :45",
        inline=False
    )
    
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    embed.add_field(
        name="🚨 通知條件 / Notification Conditions",
        value="滿足以下任一條件時發送通知 / Notification sent when any condition is met:",
        inline=False
    )
    
    embed.add_field(
        name="條件1 / Condition 1",
        value="匯率從高於閾值變為低於閾值 / Rate drops from above to below threshold",
        inline=False
    )
    
    embed.add_field(
        name="條件2 / Condition 2", 
        value="早上9:00且匯率低於閾值 / 9:00 AM and rate is below threshold",
        inline=False
    )
    
    embed.add_field(
        name="條件3 / Condition 3",
        value="晚上9:00且匯率低於閾值 / 9:00 PM and rate is below threshold", 
        inline=False
    )
    
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    embed.add_field(
        name="💡 說明 / Note",
        value="這樣可以避免持續低於閾值時的重複通知 / This prevents spam when rate stays below threshold",
        inline=False
    )
    
    embed.set_footer(text="玉山銀行匯率監控系統 / E.SUN Bank Rate Monitor")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="permissions", description="檢查機器人權限狀態 / Check bot permissions status")
async def permissions_slash(interaction: discord.Interaction):
    """檢查機器人權限"""
    if not interaction.guild:
        await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
        return
    
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    bot_member = interaction.guild.get_member(bot.user.id)
    if not bot_member:
        await interaction.response.send_message("無法獲取機器人資訊 / Cannot get bot information")
        return
    
    perms = bot_member.guild_permissions
    
    embed = discord.Embed(
        title="🔐 機器人權限檢查 / Bot Permissions Check",
        color=0x00ff00 if perms.send_messages else 0xff0000
    )
    
    important_perms = {
        "發送訊息 / Send Messages": perms.send_messages,
        "嵌入連結 / Embed Links": perms.embed_links,
        "讀取訊息歷史 / Read Message History": perms.read_message_history,
        "提及所有人 / Mention Everyone": perms.mention_everyone,
        "使用外部表情符號 / Use External Emojis": perms.use_external_emojis,
        "新增反應 / Add Reactions": perms.add_reactions,
    }
    
    for perm_name, has_perm in important_perms.items():
        status = "✅" if has_perm else "❌"
        embed.add_field(
            name=f"{status} {perm_name}",
            value="已授權 / Granted" if has_perm else "未授權 / Not granted",
            inline=False
        )
    
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    # 檢查應用程式權限（Slash Commands相關）
    app_perms = interaction.guild.me.guild_permissions
    has_app_commands = hasattr(app_perms, 'use_application_commands') and app_perms.use_application_commands
    
    embed.add_field(
        name=f"{'✅' if has_app_commands else '❌'} 使用應用程式指令 / Use Application Commands",
        value="已授權 / Granted" if has_app_commands else "未授權 / Not granted",
        inline=False
    )
    
    if not perms.send_messages:
        embed.add_field(name="\u200b", value="\n", inline=False)
        
        embed.add_field(
            name="⚠️ 注意 / Warning",
            value="機器人需要基本權限才能正常運作\nBot needs basic permissions to function properly",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sync", description="手動同步 Slash Commands / Manually sync Slash Commands")
async def sync_slash(interaction: discord.Interaction):
    """手動同步 Slash Commands"""
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
        
    await interaction.response.send_message("正在同步 Slash Commands... / Syncing Slash Commands...")
    
    try:
        synced = await bot.tree.sync()
        embed = discord.Embed(
            title="✅ 同步成功 / Sync Successful",
            description=f"已同步 {len(synced)} 個 Slash Commands / Synced {len(synced)} Slash Commands",
            color=0x00ff00
        )
        
        if synced:
            cmd_list = "\n".join([f"• /{cmd.name}" for cmd in synced])
            embed.add_field(
                name="已同步的指令 / Synced Commands",
                value=cmd_list,
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ 同步失敗 / Sync Failed",
            description=str(e),
            color=0xff0000
        )
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="system", description="檢查系統運行狀態和API可用性 / Check system status and API availability")
async def system_slash(interaction: discord.Interaction, detailed: bool = False):
    """全面的系統狀態檢查（整合版）"""
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    # 檢查系統管理器是否可用
    if system_manager is None:
        await interaction.response.send_message("❌ 系統管理器未正確初始化，請重啟機器人")
        return
    
    if detailed:
        await interaction.response.send_message("🔍 正在執行詳細系統檢查... / Performing detailed system check...")
        try:
            system_report = await system_manager.get_comprehensive_system_report()
            title = "🔧 詳細系統狀態報告 / Detailed System Status Report"
        except Exception as e:
            logger.error(f"獲取詳細系統報告失敗: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ 系統檢查失敗: {str(e)}")
            return
    else:
        await interaction.response.send_message("⚡ 正在執行快速系統檢查... / Performing quick system check...")
        try:
            system_report = await system_manager.get_quick_system_status()
            title = "⚡ 快速系統狀態 / Quick System Status"
        except Exception as e:
            logger.error(f"獲取快速系統狀態失敗: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ 系統檢查失敗: {str(e)}")
            return
    
    # 檢查報告是否有效
    if system_report is None:
        logger.error("系統報告為 None")
        await interaction.followup.send("❌ 系統報告生成失敗，請稍後重試")
        return
        
    if not isinstance(system_report, dict):
        logger.error(f"系統報告不是字典類型: type={type(system_report)}, value={system_report}")
        await interaction.followup.send("❌ 系統報告格式錯誤，請稍後重試")
        return
    
    # 根據系統狀態設定顏色
    status_colors = {
        'healthy': 0x00ff00,
        'warning': 0xff9900,
        'error': 0xff0000,
        'unknown': 0x888888
    }
    
    # 安全地獲取狀態
    overall_status = 'unknown'
    if 'overall_status' in system_report:
        overall_status = system_report['overall_status']
    elif 'status' in system_report:
        overall_status = system_report['status']
    
    embed = discord.Embed(
        title=title,
        color=status_colors.get(overall_status, 0x888888),
        timestamp=datetime.now()
    )
    
    # 整體狀態
    status_emoji = {
        'healthy': '✅',
        'warning': '⚠️', 
        'error': '❌',
        'unknown': '❓'
    }
    
    embed.add_field(
        name="🎯 整體狀態 / Overall Status",
        value=f"{status_emoji.get(overall_status, '❓')} **{overall_status.upper()}**",
        inline=False
    )
    
    if detailed:
        # 詳細報告模式
        quick_stats = system_report.get('quick_stats', {})
        
        # 確保 quick_stats 不是 None
        if quick_stats is None:
            quick_stats = {}
        
        # 健康檢查摘要
        if quick_stats:
            embed.add_field(
                name="📊 健康檢查 / Health Checks",
                value=f"檢查項目 / Total: {quick_stats.get('health_checks_total', 0)}\n"
                      f"✅ 健康 / Healthy: {quick_stats.get('health_checks_healthy', 0)}\n"
                      f"🔄 連續失敗 / Failures: {quick_stats.get('consecutive_failures', 0)}",
                inline=False
            )
            
            # 系統資源
            memory_percent = quick_stats.get('memory_usage_percent', 0)
            disk_percent = quick_stats.get('disk_usage_percent', 0)
            memory_gb = quick_stats.get('memory_used_gb', 0)
            
            embed.add_field(
                name="💻 系統資源 / System Resources",
                value=f"記憶體 / Memory: {memory_percent:.1f}% ({memory_gb:.1f}GB)\n"
                      f"磁碟 / Disk: {disk_percent:.1f}%\n"
                      f"API狀態 / API: {quick_stats.get('api_status', 'unknown')}",
                inline=False
            )
        
        # 建議
        recommendations = system_report.get('recommendations', [])
        if recommendations is None:
            recommendations = []
        if recommendations:
            embed.add_field(
                name="💡 系統建議 / Recommendations",
                value='\n'.join([f"• {rec}" for rec in recommendations[:4]]),
                inline=False
            )
        
        # 維護統計
        maintenance_info = system_report.get('maintenance', {})
        if maintenance_info is None:
            maintenance_info = {}
        if maintenance_info and not maintenance_info.get('error'):
            latest_activity_info = maintenance_info.get('latest_activity', {})
            if latest_activity_info is None:
                latest_activity_info = {}
            embed.add_field(
                name="🔧 維護狀態 / Maintenance Status",
                value=f"24小時活動 / 24h Activities: {maintenance_info.get('total_activities', 0)}\n"
                      f"最新活動 / Latest: {latest_activity_info.get('activity_type', 'none')}",
                inline=False
            )
    
    else:
        # 快速報告模式
        embed.add_field(
            name="⏱️ 運行時間 / Uptime",
            value=f"{system_report.get('uptime_hours', 0):.1f} 小時 / hours",
            inline=False
        )
        
        embed.add_field(
            name="💾 記憶體使用 / Memory Usage", 
            value=f"{system_report.get('memory_usage_mb', 0):.1f} MB",
            inline=False
        )
        
        # 健康狀態指示
        is_healthy = system_report.get('is_healthy', False)
        health_status = "正常 / Healthy" if is_healthy else "需要注意 / Needs Attention"
        embed.add_field(
            name="🏥 健康狀態 / Health Status",
            value=health_status,
            inline=False
        )
        
        # 如果有錯誤，顯示錯誤信息
        if system_report.get('error'):
            embed.add_field(
                name="❌ 錯誤信息 / Error",
                value=system_report['error'][:200] + "..." if len(system_report['error']) > 200 else system_report['error'],
                inline=False
            )
    
    # 基本Bot資訊
    embed.add_field(name="\u200b", value="\n", inline=False)
    embed.add_field(
        name="🤖 Bot資訊 / Bot Info",
        value=f"名稱 / Name: {bot.user.name}\n"
              f"延遲 / Latency: {round(bot.latency * 1000)}ms\n"
              f"監控狀態 / Monitor: {'✅ 運行中' if rate_check_task and not rate_check_task.cancelled() else '❌ 已停止'}",
        inline=False
    )
    
    # 多伺服器統計
    total_servers = 0
    servers_with_channels = 0
    
    for key, data in data_manager.data.items():
        if key == 'rate_history':
            continue
        if isinstance(data, dict):
            total_servers += 1
            if data.get('channel_id'):
                servers_with_channels += 1
    
    embed.add_field(
        name="🌐 服務狀態 / Service Status",
        value=f"總伺服器 / Servers: {total_servers}\n"
              f"已設定通知 / Notifications: {servers_with_channels}\n"
              f"系統管理器 / System Manager: ✅ 已啟用",
        inline=False
    )
    
    # 操作提示
    if detailed:
        embed.add_field(name="\u200b", value="\n", inline=False)
        embed.add_field(
            name="🔧 快速操作 / Quick Actions",
            value="• `/system` - 快速狀態檢查\n"
                  "• `/maintenance daily` - 執行維護\n"
                  "• `/health` - 健康檢查詳情",
            inline=False
        )
    
    embed.set_footer(text="整合系統管理 v1.0 / Integrated System Management v1.0")
    
    await interaction.followup.send(embed=embed)

# ====== 系統管理輔助指令 ======

@bot.tree.command(name="health", description="系統健康檢查 / System health check")
async def health_slash(interaction: discord.Interaction, quick: bool = False):
    """系統健康檢查"""
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    if quick:
        await interaction.response.send_message("⚡ 執行快速健康檢查... / Performing quick health check...")
        health_report = await system_manager.health_monitor.quick_health_check()
        
        # 💾 保存快速健康檢查結果到持久化存儲
        if health_report and health_report.get('status'):
            formatted_report = {
                'overall_status': health_report.get('status'),
                'details': health_report.get('checks', {}),
                'timestamp': health_report.get('timestamp'),
                'warnings': health_report.get('warnings', []),
                'errors': health_report.get('errors', [])
            }
            await system_manager._save_health_check_result(formatted_report, 'quick')
        
        title = "⚡ 快速健康檢查 / Quick Health Check"
        
        embed = discord.Embed(
            title=title,
            color=0x00ff00 if health_report.get('status') == 'healthy' else 0xff9900,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎯 整體狀態 / Overall Status",
            value=f"{'✅' if health_report.get('status') == 'healthy' else '⚠️'} **{health_report.get('status', 'unknown').upper()}**",
            inline=False
        )
        
        embed.add_field(
            name="🔍 檢查項目 / Checks Performed",
            value=f"檢查數量 / Total Checks: {len(health_report.get('checks', {}))}",
            inline=False
        )
        
        # 檢查結果摘要
        if health_report.get('checks'):
            check_summary = []
            for check_name, check_result in health_report['checks'].items():
                if isinstance(check_result, dict):
                    status = check_result.get('status', 'unknown')
                    status_icon = {"healthy": "✅", "warning": "⚠️", "error": "❌"}.get(status, "❓")
                    check_summary.append(f"{status_icon} {check_name}")
                else:
                    check_summary.append(f"❓ {check_name}")
            
            embed.add_field(
                name="📋 檢查結果 / Check Results",
                value='\n'.join(check_summary),
                inline=False
            )
        
        embed.set_footer(text="提示：使用 /health 獲取詳細分析")
        await interaction.followup.send(embed=embed)
        return
    
    # 詳細健康分析
    await interaction.response.send_message("🏥 正在執行詳細健康分析... / Performing detailed health analysis...")
    
    try:
        # 獲取詳細的健康報告
        health_report = await system_manager.health_monitor.comprehensive_health_check()
        
        # 💾 保存詳細健康檢查結果到持久化存儲
        if health_report and health_report.get('overall_status'):
            formatted_report = {
                'overall_status': health_report.get('overall_status'),
                'details': health_report.get('checks', {}),
                'timestamp': health_report.get('timestamp'),
                'warnings': health_report.get('warnings', []),
                'errors': health_report.get('errors', [])
            }
            await system_manager._save_health_check_result(formatted_report, 'detailed')
        
        embed = discord.Embed(
            title="🏥 系統健康詳細分析 / Detailed Health Analysis",
            color=0x00ff00 if health_report.get('overall_status') == 'healthy' else 0xff9900,
            timestamp=datetime.now()
        )
        
        # 檢查摘要
        if 'metrics' in health_report:
            metrics = health_report['metrics']
            embed.add_field(
                name="📊 檢查摘要 / Check Summary",
                value=f"檢查項目 / Items: {metrics.get('checks_total', 0)}\n"
                      f"✅ 健康 / Healthy: {metrics.get('checks_healthy', 0)}\n"
                      f"⚠️ 警告 / Warning: {metrics.get('checks_warning', 0)}\n"
                      f"❌ 錯誤 / Error: {metrics.get('checks_error', 0)}",
                inline=False
            )
        
        # API健康狀態
        if 'checks' in health_report and 'api_health' in health_report['checks']:
            api_info = health_report['checks']['api_health']
            if isinstance(api_info, dict):
                api_summary = []
                for api_name, api_data in api_info.get('apis', {}).items():
                    status_icon = {"healthy": "✅", "warning": "⚠️", "error": "❌"}.get(api_data.get('status'), "❓")
                    response_time = api_data.get('response_time_ms', 0)
                    api_summary.append(f"{status_icon} {api_name}: {response_time:.0f}ms")
                
                embed.add_field(
                    name="🌐 API健康狀態 / API Health",
                    value='\n'.join(api_summary[:4]) if api_summary else "無API檢查數據",
                    inline=False
                )
        
        # 資源使用詳情
        if 'checks' in health_report and 'resource_health' in health_report['checks']:
            resource_info = health_report['checks']['resource_health']
            if isinstance(resource_info, dict) and resource_info.get('status') != 'error':
                memory_info = resource_info.get('memory', {})
                disk_info = resource_info.get('disk', {})
                cpu_info = resource_info.get('cpu', {})
                
                embed.add_field(
                    name="💻 系統資源 / System Resources",
                    value=f"記憶體 / Memory: {memory_info.get('percent', 0):.1f}% ({memory_info.get('used_gb', 0):.1f}GB)\n"
                          f"磁碟 / Disk: {disk_info.get('percent', 0):.1f}% ({disk_info.get('used_gb', 0):.1f}GB)\n"
                          f"CPU: {cpu_info.get('percent', 0):.1f}%",
                    inline=False
                )
        
        # 警告信息
        if health_report.get('warnings'):
            warnings_text = '\n'.join([f"• {w}" for w in health_report['warnings'][:5]])
            embed.add_field(
                name="⚠️ 系統警告 / System Warnings",
                value=warnings_text,
                inline=False
            )
        
        # 錯誤信息
        if health_report.get('errors'):
            errors_text = '\n'.join([f"• {e}" for e in health_report['errors'][:3]])
            embed.add_field(
                name="❌ 系統錯誤 / System Errors",
                value=errors_text,
                inline=False
            )
        
        embed.set_footer(text="提示：使用 /system detailed:True 獲取整合報告")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"健康分析失敗: {e}")
        await interaction.followup.send(f"❌ 健康分析失敗: {str(e)}")

@bot.tree.command(name="maintenance", description="系統維護管理 / System maintenance management")
async def maintenance_slash(interaction: discord.Interaction, operation: str = "summary"):
    """系統維護管理"""
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    valid_operations = ["summary", "daily", "emergency"]
    if operation not in valid_operations:
        await interaction.response.send_message(f"❌ 無效的維護操作。可用選項: {', '.join(valid_operations)} / Invalid operation. Available: {', '.join(valid_operations)}")
        return
    
    if operation == "summary":
        await interaction.response.send_message("� 獲取維護狀態... / Getting maintenance status...")
        
        try:
            maintenance_summary = system_manager.auto_maintenance.get_maintenance_summary(24)
            
            embed = discord.Embed(
                title="� 維護狀態摘要 / Maintenance Status Summary",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 24小時統計 / 24h Statistics",
                value=f"維護活動 / Activities: {maintenance_summary.get('total_activities', 0)}",
                inline=False
            )
            
            if maintenance_summary.get('activity_breakdown'):
                activity_text = []
                for activity_type, stats in maintenance_summary['activity_breakdown'].items():
                    completed = stats.get('completed', 0)
                    failed = stats.get('failed', 0)
                    activity_text.append(f"• {activity_type}: {completed} 成功, {failed} 失敗")
                
                embed.add_field(
                    name="🔍 活動詳情 / Activity Details",
                    value='\n'.join(activity_text[:5]) if activity_text else "無活動記錄",
                    inline=False
                )
            
            embed.add_field(
                name="🔧 可用操作 / Available Actions",
                value="• `/maintenance daily` - 執行日常維護\n"
                      "• `/maintenance emergency` - 緊急清理\n"
                      "• `/system detailed:True` - 完整系統報告",
                inline=False
            )
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ 維護狀態獲取失敗",
                description=f"錯誤: {str(e)}",
                color=0xff0000
            )
        
        await interaction.followup.send(embed=embed)
    
    else:
        # 執行維護操作
        if operation == "daily":
            await interaction.response.send_message("🔧 執行日常維護... / Performing daily maintenance...")
        else:  # emergency
            await interaction.response.send_message("🚨 執行緊急清理... / Performing emergency cleanup...")
        
        try:
            maintenance_report = await system_manager.perform_system_maintenance(operation)
            
            embed = discord.Embed(
                title=f"� {'日常維護' if operation == 'daily' else '緊急清理'}報告 / {'Daily Maintenance' if operation == 'daily' else 'Emergency Cleanup'} Report",
                color=0x00ff00 if not maintenance_report.get('error') else 0xff0000,
                timestamp=datetime.now()
            )
            
            if maintenance_report.get('error'):
                embed.add_field(
                    name="❌ 錯誤 / Error",
                    value=maintenance_report['error'],
                    inline=False
                )
            else:
                # 成功執行
                completed_tasks = len(maintenance_report.get('tasks_completed', []))
                failed_tasks = len(maintenance_report.get('tasks_failed', []))
                
                embed.add_field(
                    name="📊 執行結果 / Execution Results",
                    value=f"✅ 成功任務 / Completed: {completed_tasks}\n"
                          f"❌ 失敗任務 / Failed: {failed_tasks}",
                    inline=False
                )
                
                if operation == "emergency" and maintenance_report.get('space_freed_mb'):
                    embed.add_field(
                        name="💾 空間釋放 / Space Freed",
                        value=f"{maintenance_report['space_freed_mb']} MB",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"維護操作失敗: {e}")
            await interaction.followup.send(f"❌ 維護操作失敗: {str(e)}")

# ====== 日常維護任務調度 ======

async def schedule_rate_check():
    """每小時整點和30分執行匯率檢查"""
    while True:
        try:
            # 計算到下一個整點或30分的時間
            now = datetime.now()
            next_check_time = None
            
            if now.minute < 30:
                # 到30分
                next_check_time = now.replace(minute=30, second=0, microsecond=0)
            else:
                # 到下一個整點
                next_check_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            sleep_seconds = (next_check_time - now).total_seconds()
            
            logger.info(f"⏰ 下次匯率檢查時間: {next_check_time.strftime('%H:%M')} ({sleep_seconds/60:.1f}分鐘後)")
            
            # 等待到檢查時間
            await asyncio.sleep(sleep_seconds)
            
            # 執行匯率檢查
            await perform_rate_check()
            
        except asyncio.CancelledError:
            logger.info("🔄 匯率檢查任務已被取消")
            break
        except Exception as e:
            logger.error(f"匯率檢查任務異常: {e}")
            # 等待10分鐘後重試
            await asyncio.sleep(600)

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
                
                # 判斷是否需要發送通知
                should_notify = False
                notification_reason = ""
                
                last_was_above_threshold = server_data.get('last_was_above_threshold')
                
                # 條件1: 匯率低於閾值且之前高於閾值 (狀態改變)
                if (rate < threshold and 
                    last_was_above_threshold is not None and 
                    last_was_above_threshold):
                    should_notify = True
                    notification_reason = "匯率跌破閾值 / Rate dropped below threshold"
                
                # 條件2: 匯率低於閾值且當前時間是早上9點
                elif (rate < threshold and 
                      now.hour == 9 and now.minute == 0):
                    should_notify = True
                    notification_reason = "早上9點定時通知 / 9 AM scheduled notification"
                
                # 條件3: 匯率低於閾值且當前時間是晚上9點
                elif (rate < threshold and 
                      now.hour == 21 and now.minute == 0):
                    should_notify = True
                    notification_reason = "晚上9點定時通知 / 9 PM scheduled notification"
                
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

async def schedule_health_check():
    """每小時15分和45分執行健康檢查"""
    while True:
        try:
            # 計算到下一個15分或45分的時間
            now = datetime.now()
            next_check_time = None
            
            if now.minute < 15:
                # 到15分
                next_check_time = now.replace(minute=15, second=0, microsecond=0)
            elif now.minute < 45:
                # 到45分
                next_check_time = now.replace(minute=45, second=0, microsecond=0)
            else:
                # 到下一個小時的15分
                next_check_time = now.replace(minute=15, second=0, microsecond=0) + timedelta(hours=1)
            
            sleep_seconds = (next_check_time - now).total_seconds()
            
            logger.info(f"⏰ 下次健康檢查時間: {next_check_time.strftime('%H:%M')} ({sleep_seconds/60:.1f}分鐘後)")
            
            # 等待到檢查時間
            await asyncio.sleep(sleep_seconds)
            
            # 執行健康檢查
            await perform_health_check()
            
        except asyncio.CancelledError:
            logger.info("🔄 健康檢查任務已被取消")
            break
        except Exception as e:
            logger.error(f"健康檢查任務異常: {e}")
            # 等待10分鐘後重試
            await asyncio.sleep(600)

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
                
                # 3. 維護完成後重新調度任務，確保時間同步準確性
                logger.info("🔄 重新調度定期任務以確保時間同步...")
                try:
                    global rate_check_task, health_check_task
                    
                    # 取消現有任務
                    if rate_check_task and not rate_check_task.cancelled():
                        rate_check_task.cancel()
                        logger.info("🔄 已取消舊的匯率檢查任務")
                    
                    if health_check_task and not health_check_task.cancelled():
                        health_check_task.cancel()
                        logger.info("🔄 已取消舊的健康檢查任務")
                    
                    # 等待短暫時間確保任務完全取消
                    await asyncio.sleep(1)
                    
                    # 重新啟動匯率檢查任務
                    rate_check_task = asyncio.create_task(schedule_rate_check())
                    logger.info("✅ 匯率檢查任務已重新調度")
                    
                    # 重新啟動健康檢查任務
                    health_check_task = asyncio.create_task(schedule_health_check())
                    logger.info("✅ 健康檢查任務已重新調度")
                    
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
                    
                except Exception as e:
                    logger.error(f"❌ 重新調度任務失敗: {e}")
                
                # 4. 執行維護後的健康檢查驗證
                logger.info("🔍 執行維護後健康檢查驗證...")
                try:
                    post_maintenance_health = await system_manager.health_monitor.quick_health_check()
                    post_health_status = post_maintenance_health.get('status', 'unknown')
                    logger.info(f"📋 維護後系統狀態: {post_health_status}")
                    
                    if post_health_status == 'healthy':
                        logger.info("✅ 維護後系統狀態良好")
                    else:
                        logger.warning(f"⚠️ 維護後系統仍有問題: {post_health_status}")
                        
                except Exception as e:
                    logger.error(f"❌ 維護後健康檢查失敗: {e}")
                
                # 記錄維護完成後的狀態
                logger.info("⚙️ 每日維護任務已完成，系統繼續監控中...")
                
            else:
                logger.warning("⚠️ 系統管理器未初始化，跳過每日維護")
                
        except Exception as e:
            logger.error(f"每日運維任務異常: {e}")
            # 等待1小時後重試
            await asyncio.sleep(3600)

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
