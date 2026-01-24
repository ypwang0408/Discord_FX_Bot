# -*- coding: utf-8 -*-
"""
Config Commands Module
Handles bot configuration commands: /channel, /mention, /status
"""

import discord
from discord import app_commands
import logging

from utils import require_admin_permission, EmbedBuilder, format_timestamp_display

logger = logging.getLogger(__name__)


def register_config_commands(bot, data_manager):
    """
    Register all configuration-related slash commands

    Args:
        bot: Discord bot instance
        data_manager: ServerDataManager instance
    """

    @bot.tree.command(name="channel", description="將當前頻道設為通知頻道 / Set current channel as notification channel")
    async def channel_slash(interaction: discord.Interaction):
        """設定通知頻道為當前頻道"""
        if not interaction.guild:
            await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
            return

        data_manager.set_channel_id(interaction.guild.id, interaction.channel.id)
        await interaction.response.send_message(f"✅ 已設定通知頻道為: **{interaction.channel.name}** / Notification channel set to: **{interaction.channel.name}**")

    @bot.tree.command(name="mention", description="設定是否使用@everyone通知 / Set @everyone mention notifications")
    @app_commands.describe(enable="是否啟用@everyone通知 / Whether to enable @everyone mentions")
    @require_admin_permission()
    async def mention_slash(interaction: discord.Interaction, enable: bool):
        """設定是否使用@everyone通知"""
        if not interaction.guild:
            await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
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

        # Build embed
        embed_builder = EmbedBuilder("🤖 機器人狀態 / Bot Status").info()

        embed_builder.add_field(
            "監控閾值 / Threshold",
            f"{server_data['threshold']} JPY/TWD"
        )

        channel_id = server_data['channel_id']
        embed_builder.add_field(
            "通知頻道 / Notification Channel",
            f"<#{channel_id}>" if channel_id else "未設定 / Not set"
        )

        embed_builder.add_separator()

        last_rate = server_data['last_rate']
        last_rate_time = server_data.get('last_rate_time')

        if last_rate and last_rate_time:
            rate_display = format_timestamp_display(last_rate_time, '%m-%d %H:%M')
            if rate_display != "時間格式錯誤 / Invalid time format":
                rate_display = f"{last_rate:.4f} JPY/TWD ({rate_display})"
            else:
                rate_display = f"{last_rate:.4f} JPY/TWD" if last_rate else "無 / None"
        else:
            rate_display = f"{last_rate:.4f} JPY/TWD" if last_rate else "無 / None"

        embed_builder.add_field("最後匯率 / Last Rate", rate_display)

        last_was_above = server_data['last_was_above_threshold']
        status_text = (
            "❌ 高於閾值 / Above threshold" if last_was_above
            else "⚠️ 低於閾值 / Below threshold" if last_was_above is not None
            else "❓ 未知 / Unknown"
        )
        embed_builder.add_field("上次狀態 / Last Status", status_text)

        embed_builder.add_field("監控狀態 / Monitor Status", "✅ 運行中 / Running")

        embed_builder.add_separator()

        last_notification = server_data['last_notification_time']
        if last_notification:
            notification_display = format_timestamp_display(last_notification, '%Y-%m-%d %H:%M:%S')
            embed_builder.add_field("最後通知時間 / Last Notification", notification_display)

        embed_builder.add_field(
            "@everyone 通知 / @everyone Mention",
            "啟用 / Enabled" if server_data['use_everyone_mention'] else "停用 / Disabled"
        )

        await interaction.response.send_message(embed=embed_builder.build())

    logger.info("✅ Config commands registered")
