# -*- coding: utf-8 -*-
"""
Bot utilities - Decorators for common patterns
Provides reusable decorators for Discord command handlers
"""

from functools import wraps
import discord


def require_admin_permission():
    """
    Decorator to check admin permissions for slash commands

    Usage:
        @bot.tree.command(name="example")
        @require_admin_permission()
        async def example_command(interaction: discord.Interaction):
            # Command implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ 此指令需要管理員權限 / This command requires administrator permission",
                    ephemeral=True
                )
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator


def require_guild():
    """
    Decorator to ensure command is used in a guild (not in DMs)

    Usage:
        @bot.tree.command(name="example")
        @require_guild()
        async def example_command(interaction: discord.Interaction):
            # Command implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            if not interaction.guild:
                await interaction.response.send_message(
                    "此指令只能在伺服器中使用 / This command can only be used in a server",
                    ephemeral=True
                )
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator
