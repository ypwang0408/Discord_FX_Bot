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
    NotificationSystem
)

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
    
    # 啟動定期檢查任務
    if not check_exchange_rate.is_running():
        check_exchange_rate.start()
        print("✅ 定期檢查任務已啟動")
    
    # 啟動自動備份任務
    if not auto_backup.is_running():
        auto_backup.start()
        print("✅ 自動備份任務已啟動")

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
            last_rate_time=datetime.now().isoformat(),
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
            inline=True
        )
        
        status = "✅ 高於閾值 / Above threshold" if rate >= threshold else "⚠️ 低於閾值 / Below threshold"
        embed.add_field(
            name="狀態 / Status",
            value=status,
            inline=True
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
        value=f"{'高於閾值 / Above threshold' if last_was_above else '低於閾值 / Below threshold' if last_was_above is not None else '未知 / Unknown'}",
        inline=False
    )
    
    embed.add_field(
        name="監控狀態 / Monitor Status",
        value=f"{'✅ 運行中 / Running' if check_exchange_rate.is_running() else '❌ 已停止 / Stopped'}",
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
              "`/list_backups` - 列出所有備份 / List all backups",
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
              "• 每個伺服器有獨立的設定 / Each server has independent settings",
        inline=False
    )
    
    embed.set_footer(text="機器人在整點和30分檢查匯率，智慧通知避免重複 / Bot checks rate at :00 and :30, smart notifications to avoid spam")
    
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
        value="每小時的整點和30分 / Every hour at :00 and :30",
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
async def system_slash(interaction: discord.Interaction):
    """詳細的系統狀態檢查"""
    # 檢查用戶是否為管理員
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 此指令需要管理員權限 / This command requires administrator permission")
        return
    
    await interaction.response.send_message("🔍 正在檢查系統狀態... / Checking system status...")
    
    embed = discord.Embed(
        title="🔧 系統狀態報告 / System Status Report",
        color=0x0099ff,
        timestamp=datetime.now()
    )
    
    # 基本Bot資訊
    embed.add_field(
        name="🤖 Bot資訊 / Bot Info",
        value=f"名稱 / Name: {bot.user.name}\nID: {bot.user.id}\n連線延遲 / Latency: {round(bot.latency * 1000)}ms",
        inline=False
    )
    
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    # 測試玉山銀行API
    esun_status = "❌ 失敗 / Failed"
    esun_rate = None
    try:
        esun_rate = await rate_monitor.get_esun_jpy_rate()
        if esun_rate is not None:
            esun_status = f"✅ 成功 / Success ({esun_rate:.4f})"
        else:
            esun_status = "⚠️ 無資料 / No data"
    except Exception as e:
        esun_status = f"❌ 錯誤 / Error: {str(e)[:50]}"
    
    # 測試備用API
    backup_status = "❌ 失敗 / Failed"
    try:
        backup_rate = await rate_monitor.get_backup_jpy_rate()
        if backup_rate is not None:
            backup_status = f"✅ 成功 / Success ({backup_rate:.4f})"
        else:
            backup_status = "⚠️ 無資料 / No data"
    except Exception as e:
        backup_status = f"❌ 錯誤 / Error: {str(e)[:50]}"
    
    embed.add_field(
        name="🌐 API狀態 / API Status",
        value=f"玉山銀行 / E.SUN Bank: {esun_status}\n備用API / Backup API: {backup_status}",
        inline=False
    )
    
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    # 監控狀態
    monitor_status = "✅ 運行中 / Running" if check_exchange_rate.is_running() else "❌ 已停止 / Stopped"
    next_check = "未知 / Unknown"
    if check_exchange_rate.is_running():
        now = datetime.now()
        if now.minute < 30:
            next_check = f"{now.hour:02d}:30"
        else:
            next_hour = (now.hour + 1) % 24
            next_check = f"{next_hour:02d}:00"
    
    embed.add_field(
        name="⏰ 監控狀態 / Monitor Status",
        value=f"狀態 / Status: {monitor_status}\n下次檢查 / Next Check: {next_check}",
        inline=False
    )
    
    embed.add_field(name="\u200b", value="\n", inline=False)
    
    # 多伺服器統計
    total_servers = len(data_manager.data)
    servers_with_channels = sum(1 for data in data_manager.data.values() if data.get('channel_id'))
    
    embed.add_field(
        name="🌐 多伺服器狀態 / Multi-Server Status",
        value=f"總伺服器 / Total Servers: {total_servers}\n已設定通知 / With Notifications: {servers_with_channels}",
        inline=False
    )
    
    embed.set_footer(text="系統狀態檢查 / System Status Check")
    
    await interaction.followup.send(embed=embed)

# ====== 定期任務 ======

@tasks.loop(minutes=1)  # 每分鐘檢查一次，但只在特定時間執行
async def check_exchange_rate():
    """定期檢查匯率並發送通知"""
    # 取得當前時間
    now = datetime.now()
    
    # 只在整點或30分時執行
    if now.minute not in [0, 30]:
        return
    
    # 檢查所有有設定通知頻道的伺服器
    servers_with_channels = data_manager.get_all_servers_with_channels()
    
    for server_info in servers_with_channels:
        guild_id = server_info['guild_id']
        channel_id = server_info['channel_id']
        threshold = server_info['threshold']
        use_everyone_mention = server_info['use_everyone_mention']
        server_data = server_info['server_data']
        
        try:
            rate = await rate_monitor.get_esun_jpy_rate()
            
            if rate is not None:
                current_above_threshold = rate >= threshold
                
                # 更新匯率狀態和時間戳記
                rate_monitor.update_server_state(
                    guild_id, 
                    last_rate=rate,
                    last_rate_time=datetime.now().isoformat()
                )
                
                # 新增到匯率歷史
                data_manager.add_rate_history(guild_id, rate)
                
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
                            last_notification_time=datetime.now().isoformat()
                        )
                        
                        logger.info(f"發送匯率警報到伺服器 {guild_id}: {rate:.4f} < {threshold}, 原因: {notification_reason}")
                
        except Exception as e:
            logger.error(f"檢查伺服器 {guild_id} 匯率時發生錯誤: {e}")

@tasks.loop(hours=24)  # 每24小時（每天）自動備份
async def auto_backup():
    """自動備份任務 - 每天執行一次"""
    try:
        backup_path = backup_manager.create_backup()
        
        if backup_path:
            logger.info(f"✅ 每日自動備份完成: {os.path.basename(backup_path)}")
            
            # 智能清理舊備份（已在create_backup中執行）
            logger.info("� 備份清理策略：7天內保留所有，超過7天只保留星期一備份")
        else:
            logger.error("❌ 每日自動備份失敗")
    except Exception as e:
        logger.error(f"自動備份任務異常: {e}")

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
