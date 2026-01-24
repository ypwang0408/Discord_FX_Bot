# -*- coding: utf-8 -*-
"""
Rate Commands Module
Handles exchange rate related commands: /rate, /threshold, /chart
"""

import discord
from discord import app_commands
import logging

from utils import require_admin_permission, EmbedBuilder
from features.data_manager import get_minute_precision_timestamp

logger = logging.getLogger(__name__)


def register_rate_commands(bot, data_manager, rate_monitor, chart_generator):
    """
    Register all rate-related slash commands

    Args:
        bot: Discord bot instance
        data_manager: ServerDataManager instance
        rate_monitor: ExchangeRateMonitor instance
        chart_generator: RateChartGenerator instance
    """

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
            status = "❌ 高於閾值 / Above threshold" if rate >= threshold else "⚠️ 低於閾值 / Below threshold"

            embed_builder = EmbedBuilder("💴 玉山銀行日幣匯率 / E.SUN Bank JPY Rate")
            if rate >= threshold:
                embed_builder.success()
            else:
                embed_builder.error()

            embed = (embed_builder
                .add_field("當前匯率 / Current Rate", f"**{rate:.4f} JPY/TWD**")
                .add_field("監控閾值 / Threshold", f"{threshold} JPY/TWD")
                .add_field("狀態 / Status", status)
                .with_esun_footer()
                .build())

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ 無法獲取匯率資訊，請稍後再試。/ Cannot get exchange rate, please try again later.")

    @bot.tree.command(name="threshold", description="設定匯率監控閾值 / Set exchange rate monitoring threshold")
    @app_commands.describe(threshold="監控閾值 (0.1-1.0) / Monitoring threshold (0.1-1.0)")
    @require_admin_permission()
    async def threshold_slash(interaction: discord.Interaction, threshold: float):
        """設定匯率監控閾值"""
        if not interaction.guild:
            await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
            return

        if 0.1 <= threshold <= 1.0:
            data_manager.set_threshold(interaction.guild.id, threshold)
            await interaction.response.send_message(f"✅ 已設定新的監控閾值: **{threshold} JPY/TWD** / New threshold set: **{threshold} JPY/TWD**")
        else:
            await interaction.response.send_message("❌ 閾值必須在 0.1 到 1.0 之間 / Threshold must be between 0.1 and 1.0")

    @bot.tree.command(name="chart", description="生成匯率趨勢圖表 / Generate rate trend chart")
    @app_commands.describe(days="天數範圍 (1-30天) / Days range (1-30 days)")
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

            embed = (EmbedBuilder(f"📈 日幣匯率趨勢圖 / JPY Rate Trend (Last {days} Days)")
                .success()
                .with_image(f"attachment://rate_chart_{days}days.png")
                .with_esun_footer()
                .build())

            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            logger.error(f"生成圖表失敗: {e}")
            await interaction.followup.send("❌ 生成圖表時發生錯誤 / Error occurred while generating chart")

    logger.info("✅ Rate commands registered")
