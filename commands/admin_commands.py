# -*- coding: utf-8 -*-
"""
Admin Commands Module
Handles admin commands: /backup, /list_backups, /permissions, /sync
"""

import discord
from discord import app_commands
import os
import logging

from utils import require_admin_permission, EmbedBuilder, format_timestamp_display

logger = logging.getLogger(__name__)


def register_admin_commands(bot, backup_manager):
    """
    Register all admin-related slash commands

    Args:
        bot: Discord bot instance
        backup_manager: DataBackupManager instance
    """

    @bot.tree.command(name="backup", description="手動創建數據備份 / Manually create data backup")
    @require_admin_permission()
    async def backup_slash(interaction: discord.Interaction):
        """手動備份數據"""

        await interaction.response.send_message("💾 正在創建備份... / Creating backup...")

        try:
            backup_path = backup_manager.create_backup()

            if backup_path:
                # 獲取檔案大小
                file_size = os.path.getsize(backup_path)

                embed = (EmbedBuilder(
                        "✅ 備份創建成功 / Backup Created Successfully",
                        f"備份檔案 / Backup File: `{os.path.basename(backup_path)}`"
                    )
                    .success()
                    .add_field(
                        "檔案資訊 / File Info",
                        f"大小 / Size: {file_size} bytes\n位置 / Location: `{backup_path}`"
                    )
                    .build())

                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ 備份創建失敗 / Backup creation failed")

        except Exception as e:
            logger.error(f"手動備份失敗: {e}")
            await interaction.followup.send("❌ 備份創建時發生錯誤 / Error occurred during backup creation")

    @bot.tree.command(name="list_backups", description="列出所有備份 / List all backups")
    @require_admin_permission()
    async def list_backups_slash(interaction: discord.Interaction):
        """列出備份"""

        try:
            backups = backup_manager.list_backups()

            if not backups:
                await interaction.response.send_message("📂 目前沒有任何備份檔案 / No backup files currently exist")
                return

            # 只顯示最近10個備份
            recent_backups = backups[-10:]
            backup_list = []

            for backup in recent_backups:
                backup_time_str = format_timestamp_display(backup['timestamp'], '%Y-%m-%d %H:%M:%S')
                backup_list.append(
                    f"• `{backup['filename']}`\n"
                    f"  📅 {backup_time_str}\n"
                    f"  🗄️ {backup['servers_count']} servers | "
                    f"📦 {backup['file_size']} bytes"
                )

            embed_builder = (EmbedBuilder("📋 備份檔案列表 / Backup Files List")
                .info()
                .add_field(
                    f"最近 {len(recent_backups)} 個備份 / Recent {len(recent_backups)} Backups",
                    "\n\n".join(backup_list) if backup_list else "無備份 / No backups"
                ))

            if len(backups) > 10:
                embed_builder.with_footer(f"總共有 {len(backups)} 個備份檔案，僅顯示最近10個 / Total {len(backups)} backup files, showing recent 10 only")

            await interaction.response.send_message(embed=embed_builder.build())

        except Exception as e:
            logger.error(f"列出備份失敗: {e}")
            await interaction.response.send_message("❌ 獲取備份列表時發生錯誤 / Error occurred while getting backup list")

    @bot.tree.command(name="permissions", description="檢查機器人權限狀態 / Check bot permissions status")
    @require_admin_permission()
    async def permissions_slash(interaction: discord.Interaction):
        """檢查機器人權限"""
        if not interaction.guild:
            await interaction.response.send_message("此指令只能在伺服器中使用 / This command can only be used in a server")
            return

        bot_member = interaction.guild.get_member(bot.user.id)
        if not bot_member:
            await interaction.response.send_message("無法獲取機器人資訊 / Cannot get bot information")
            return

        perms = bot_member.guild_permissions

        embed_builder = EmbedBuilder("🔐 機器人權限檢查 / Bot Permissions Check")
        if perms.send_messages:
            embed_builder.success()
        else:
            embed_builder.error()

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
            embed_builder.add_field(
                f"{status} {perm_name}",
                "已授權 / Granted" if has_perm else "未授權 / Not granted"
            )

        embed_builder.add_separator()

        # 檢查應用程式權限（Slash Commands相關）
        app_perms = interaction.guild.me.guild_permissions
        has_app_commands = hasattr(app_perms, 'use_application_commands') and app_perms.use_application_commands

        embed_builder.add_field(
            f"{'✅' if has_app_commands else '❌'} 使用應用程式指令 / Use Application Commands",
            "已授權 / Granted" if has_app_commands else "未授權 / Not granted"
        )

        if not perms.send_messages:
            embed_builder.add_separator()
            embed_builder.add_field(
                "⚠️ 注意 / Warning",
                "機器人需要基本權限才能正常運作\nBot needs basic permissions to function properly"
            )

        await interaction.response.send_message(embed=embed_builder.build())

    @bot.tree.command(name="sync", description="手動同步 Slash Commands / Manually sync Slash Commands")
    @require_admin_permission()
    async def sync_slash(interaction: discord.Interaction):
        """手動同步 Slash Commands"""

        await interaction.response.send_message("正在同步 Slash Commands... / Syncing Slash Commands...")

        try:
            synced = await bot.tree.sync()
            embed_builder = EmbedBuilder(
                "✅ 同步成功 / Sync Successful",
                f"已同步 {len(synced)} 個 Slash Commands / Synced {len(synced)} Slash Commands"
            ).success()

            if synced:
                cmd_list = "\n".join([f"• /{cmd.name}" for cmd in synced])
                embed_builder.add_field("已同步的指令 / Synced Commands", cmd_list)

            await interaction.followup.send(embed=embed_builder.build())

        except Exception as e:
            embed = (EmbedBuilder("❌ 同步失敗 / Sync Failed", str(e))
                .error()
                .build())
            await interaction.followup.send(embed=embed)

    logger.info("✅ Admin commands registered")
