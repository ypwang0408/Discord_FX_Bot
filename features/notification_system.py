# -*- coding: utf-8 -*-
"""
通知系統模組
負責發送各種通知和管理通知邏輯
"""

import discord
from datetime import datetime
import logging
from utils import EmbedBuilder

logger = logging.getLogger(__name__)


class NotificationSystem:
    """通知系統管理器"""
    
    def __init__(self, data_manager, bot):
        self.data_manager = data_manager
        self.bot = bot
    
    async def send_rate_alert(self, channel_id, rate, threshold, guild_id, notification_reason="", use_everyone_mention=True):
        """發送匯率警報通知"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error("找不到頻道 ID: " + str(channel_id))
                return False
            
            embed_builder = EmbedBuilder() \
                .error() \
                .set_title("🚨 日幣匯率警報 / JPY Rate Alert") \
                .set_description("玉山銀行日幣匯率已低於設定閾值！/ E.SUN Bank JPY rate is below threshold!") \
                .add_field(
                    name="當前匯率 / Current Rate",
                    value="**" + str(round(rate, 4)) + " JPY/TWD**",
                    inline=False
                ) \
                .add_field(
                    name="設定閾值 / Threshold",
                    value="**" + str(threshold) + " JPY/TWD**",
                    inline=False
                ) \
                .add_field(name="\u200b", value="\n", inline=False)

            if notification_reason:
                embed_builder.add_field(
                    name="通知原因 / Notification Reason",
                    value=notification_reason,
                    inline=False
                )

            embed = embed_builder \
                .add_field(
                    name="建議 / Suggestion",
                    value="💡 現在可能是換匯的好時機！/ Good time for currency exchange!",
                    inline=False
                ) \
                .with_footer(text="玉山銀行匯率監控系統 / E.SUN Bank Rate Monitor") \
                .build()
            
            # 根據設定決定是否使用@everyone
            if use_everyone_mention:
                await channel.send("@everyone", embed=embed)
            else:
                await channel.send(embed=embed)
            
            logger.info("發送匯率警報到頻道 " + str(channel_id) + ": " + str(round(rate, 4)) + " < " + str(threshold))
            return True
            
        except Exception as e:
            logger.error("發送匯率警報失敗: " + str(e))
            return False
    
    async def send_daily_report(self, channel_id, report_data):
        """發送每日報告"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return False
            
            # 漲跌情況
            rate_change = report_data['rate_change']
            change_emoji = "📈" if rate_change > 0 else "📉" if rate_change < 0 else "➡️"
            change_text = change_emoji + " " + str(round(rate_change, 4))

            embed = EmbedBuilder() \
                .info() \
                .set_title("📊 每日匯率摘要報告 / Daily Rate Summary") \
                .set_description("日期 / Date: " + str(report_data['date'])) \
                .add_field(
                    name="匯率範圍 / Rate Range",
                    value="最低 / Low: " + str(report_data['min_rate']) + "\n最高 / High: " + str(report_data['max_rate']),
                    inline=False
                ) \
                .add_field(
                    name="平均匯率 / Average Rate",
                    value=str(round(report_data['avg_rate'], 4)),
                    inline=False
                ) \
                .add_field(
                    name="當前匯率 / Current Rate",
                    value=str(round(report_data['current_rate'], 4)),
                    inline=False
                ) \
                .add_field(
                    name="日變化 / Daily Change",
                    value=change_text,
                    inline=False
                ) \
                .add_field(
                    name="閾值比較 / Threshold Comparison",
                    value="設定值 / Set: " + str(round(report_data['threshold'], 4)) + "\n低於次數 / Below: " + str(report_data['below_threshold_count']) + "/" + str(report_data['total_checks']),
                    inline=False
                ) \
                .with_footer(text="每日報告 / Daily Report") \
                .build()
            
            await channel.send(embed=embed)
            logger.info("發送每日報告到頻道 " + str(channel_id))
            return True
            
        except Exception as e:
            logger.error("發送每日報告失敗: " + str(e))
            return False
    
    async def send_weekly_report(self, channel_id, report_data):
        """發送週報"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return False
            
            embed = EmbedBuilder() \
                .success() \
                .set_title("📈 週匯率報告 / Weekly Rate Report") \
                .set_description("期間 / Period: " + str(report_data['period'])) \
                .add_field(
                    name="匯率統計 / Rate Statistics",
                    value="最低 / Min: " + str(round(report_data['min_rate'], 4)) + "\n最高 / Max: " + str(round(report_data['max_rate'], 4)) + "\n平均 / Avg: " + str(round(report_data['avg_rate'], 4)) + "\n中位數 / Median: " + str(round(report_data['median_rate'], 4)),
                    inline=False
                ) \
                .add_field(
                    name="波動性 / Volatility",
                    value="標準差 / Std Dev: " + str(round(report_data['std_dev'], 4)) + "\n波動率 / Volatility: " + str(round(report_data['volatility'], 2)) + "%",
                    inline=False
                ) \
                .add_field(
                    name="閾值分析 / Threshold Analysis",
                    value="設定閾值 / Threshold: " + str(round(report_data['threshold'], 4)) + "\n低於閾值比例 / Below %: " + str(round(report_data['below_threshold_percentage'], 1)) + "%",
                    inline=False
                ) \
                .add_field(
                    name="通知統計 / Notification Stats",
                    value="本週通知次數 / Notifications: " + str(report_data['notifications_sent']),
                    inline=False
                ) \
                .with_footer(text="週報告 / Weekly Report") \
                .build()
            
            await channel.send(embed=embed)
            logger.info("發送週報告到頻道 " + str(channel_id))
            return True
            
        except Exception as e:
            logger.error("發送週報告失敗: " + str(e))
            return False
    
    async def send_system_status(self, channel_id, status_data):
        """發送系統狀態通知"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return False
            
            embed_builder = EmbedBuilder()
            if status_data['status'] == 'healthy':
                embed_builder.success()
            else:
                embed_builder.error()

            embed_builder.set_title("🔧 系統狀態通知 / System Status Notification") \
                .set_description(status_data.get('description', '系統狀態更新'))

            for field_name, field_value in status_data.get('fields', {}).items():
                embed_builder.add_field(name=field_name, value=field_value, inline=False)

            embed = embed_builder.with_footer(text="系統監控 / System Monitor").build()
            
            await channel.send(embed=embed)
            logger.info("發送系統狀態到頻道 " + str(channel_id))
            return True
            
        except Exception as e:
            logger.error("發送系統狀態失敗: " + str(e))
            return False
    
    async def send_user_dm_notification(self, user_id, title, description, fields=None):
        """發送用戶私訊通知"""
        try:
            user = self.bot.get_user(user_id)
            if not user:
                logger.error("找不到用戶 ID: " + str(user_id))
                return False
            
            embed_builder = EmbedBuilder() \
                .info() \
                .set_title(title) \
                .set_description(description)

            if fields:
                for field in fields:
                    embed_builder.add_field(
                        name=field.get('name', 'Field'),
                        value=field.get('value', 'Value'),
                        inline=field.get('inline', False)
                    )

            embed = embed_builder.with_footer(text="個人通知 / Personal Notification").build()
            
            await user.send(embed=embed)
            logger.info("發送私訊通知給用戶 " + str(user_id))
            return True
            
        except Exception as e:
            logger.error("發送私訊通知失敗: " + str(e))
            return False
    
    async def broadcast_to_all_servers(self, message, embed=None):
        """廣播訊息到所有設定了通知頻道的伺服器"""
        servers_with_channels = self.data_manager.get_all_servers_with_channels()
        success_count = 0
        
        for server_info in servers_with_channels:
            try:
                channel = self.bot.get_channel(server_info['channel_id'])
                if channel:
                    if embed:
                        await channel.send(message, embed=embed)
                    else:
                        await channel.send(message)
                    success_count += 1
            except Exception as e:
                logger.error("廣播到伺服器 " + str(server_info['guild_id']) + " 失敗: " + str(e))
        
        logger.info("廣播訊息到 " + str(success_count) + "/" + str(len(servers_with_channels)) + " 個伺服器")
        return success_count
