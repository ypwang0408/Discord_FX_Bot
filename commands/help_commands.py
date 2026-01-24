# -*- coding: utf-8 -*-
"""
Help Commands Module
Handles help and documentation commands: /help, /rules
"""

import discord
import logging

from utils import EmbedBuilder

logger = logging.getLogger(__name__)


def register_help_commands(bot):
    """
    Register all help and documentation slash commands

    Args:
        bot: Discord bot instance
    """

    @bot.tree.command(name="help", description="顯示幫助訊息 / Show help message")
    async def help_slash(interaction: discord.Interaction):
        """顯示幫助訊息"""
        embed = (EmbedBuilder(
                "📚 指令說明 / Command Help",
                "玉山銀行日幣匯率監控機器人 / E.SUN Bank JPY Rate Monitor Bot"
            )
            .success()
            .add_field(
                "📋 可用指令 / Available Commands",
                "**基本功能 / Basic Functions:**\n"
                "`/rate` - 查詢當前匯率 / Check current rate\n"
                "`/threshold <value>` - 設定監控閾值 / Set threshold\n"
                "`/channel` - 設定通知頻道 / Set notification channel\n"
                "`/status` - 查看機器人狀態 / Check bot status\n"
                "`/rules` - 顯示通知規則 / Show notification rules\n"
                "`/help` - 顯示此幫助訊息 / Show this help"
            )
            .add_field(
                "🔧 管理員指令 / Admin Commands",
                "`/permissions` - 檢查機器人權限 / Check bot permissions\n"
                "`/sync` - 同步 Slash Commands / Sync Slash Commands\n"
                "`/system` - 全面系統狀態檢查 / Comprehensive system check\n"
                "`/mention <true/false>` - 設定@everyone通知 / Set @everyone notifications\n"
                "`/backup` - 手動創建數據備份 / Manual data backup\n"
                "`/list_backups` - 列出所有備份 / List all backups\n"
                "`/health [quick]` - 系統健康檢查 / System health check\n"
                "`/maintenance [operation]` - 系統維護管理 / System maintenance"
            )
            .add_separator()
            .add_field(
                "📊 進階功能 / Advanced Features",
                "`/chart <days>` - 生成匯率趨勢圖表 / Generate rate trend chart\n"
                "• 天數範圍：1-30天 / Days range: 1-30 days\n"
                "• 顯示匯率變化和閾值線 / Shows rate changes and threshold line"
            )
            .add_separator()
            .add_field(
                "💡 使用提示 / Usage Tips",
                "• 輸入 `/` 即可看到所有指令並自動補全 / Type `/` to see all commands with autocomplete\n"
                "• 機器人會在整點和30分自動檢查匯率 / Bot automatically checks rate at :00 and :30\n"
                "• 智慧通知系統避免重複訊息 / Smart notification system prevents spam\n"
                "• 每個伺服器有獨立的設定 / Each server has independent settings\n"
                "• 系統在15分和45分進行健康檢查 / Health checks at :15 and :45"
            )
            .with_footer("匯率檢查: 整點和30分 | 健康檢查: 15分和45分 / Rate check: :00 & :30 | Health check: :15 & :45")
            .build())

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="rules", description="顯示通知規則 / Show notification rules")
    async def rules_slash(interaction: discord.Interaction):
        """顯示通知規則"""
        embed = (EmbedBuilder(
                "📋 通知規則 / Notification Rules",
                "智慧通知系統，避免重複訊息 / Smart notification system to avoid spam"
            )
            .warning()
            .add_field(
                "🕐 檢查時間 / Check Schedule",
                "匯率檢查: 每小時的整點和30分 / Rate check: Every hour at :00 and :30\n"
                "健康檢查: 每小時的15分和45分 / Health check: Every hour at :15 and :45"
            )
            .add_separator()
            .add_field(
                "🚨 通知條件 / Notification Conditions",
                "滿足以下任一條件時發送通知 / Notification sent when any condition is met:"
            )
            .add_field(
                "條件1 / Condition 1",
                "匯率從高於閾值變為低於閾值 / Rate drops from above to below threshold"
            )
            .add_field(
                "條件2 / Condition 2",
                "早上9:00且匯率低於閾值 / 9:00 AM and rate is below threshold"
            )
            .add_field(
                "條件3 / Condition 3",
                "晚上9:00且匯率低於閾值 / 9:00 PM and rate is below threshold"
            )
            .add_separator()
            .add_field(
                "💡 說明 / Note",
                "這樣可以避免持續低於閾值時的重複通知 / This prevents spam when rate stays below threshold"
            )
            .with_footer("玉山銀行匯率監控系統 / E.SUN Bank Rate Monitor")
            .build())

        await interaction.response.send_message(embed=embed)

    logger.info("✅ Help commands registered")
