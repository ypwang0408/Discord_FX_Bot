# -*- coding: utf-8 -*-
"""
Discord Embed Builder - Centralized embed creation with consistent styling
Provides a fluent API for creating Discord embeds with predefined color schemes
"""

import discord
from datetime import datetime
from typing import Optional


class EmbedBuilder:
    """
    Fluent builder for consistent Discord embeds

    Example:
        embed = (EmbedBuilder("Title", "Description")
            .success()
            .add_field("Field Name", "Field Value")
            .with_esun_footer()
            .build())
    """

    # Color scheme constants
    SUCCESS = 0x00ff00  # Green
    ERROR = 0xff0000    # Red
    WARNING = 0xff9900  # Orange
    INFO = 0x0099ff     # Blue

    def __init__(self, title: str, description: str = ""):
        """
        Initialize EmbedBuilder with title and optional description

        Args:
            title: Embed title
            description: Embed description (optional)
        """
        self.embed = discord.Embed(
            title=title,
            description=description,
            timestamp=datetime.now()
        )

    def success(self):
        """Set success color (green)"""
        self.embed.color = self.SUCCESS
        return self

    def error(self):
        """Set error color (red)"""
        self.embed.color = self.ERROR
        return self

    def warning(self):
        """Set warning color (orange)"""
        self.embed.color = self.WARNING
        return self

    def info(self):
        """Set info color (blue)"""
        self.embed.color = self.INFO
        return self

    def set_color(self, color: int):
        """Set custom color"""
        self.embed.color = color
        return self

    def add_field(self, name: str, value: str, inline: bool = False):
        """
        Add a field to the embed

        Args:
            name: Field name
            value: Field value
            inline: Whether field should be inline (default: False)
        """
        self.embed.add_field(name=name, value=value, inline=inline)
        return self

    def add_separator(self):
        """Add visual separator (empty field)"""
        self.embed.add_field(name="\u200b", value="\n", inline=False)
        return self

    def with_footer(self, text: str):
        """
        Set custom footer text

        Args:
            text: Footer text
        """
        self.embed.set_footer(text=text)
        return self

    def with_esun_footer(self):
        """Set E.SUN Bank standard footer"""
        return self.with_footer("資料來源: 玉山銀行 / Source: E.SUN Bank")

    def with_thumbnail(self, url: str):
        """
        Set thumbnail image

        Args:
            url: Image URL
        """
        self.embed.set_thumbnail(url=url)
        return self

    def with_image(self, url: str):
        """
        Set main image

        Args:
            url: Image URL
        """
        self.embed.set_image(url=url)
        return self

    def without_timestamp(self):
        """Remove timestamp from embed"""
        self.embed.timestamp = None
        return self

    def build(self) -> discord.Embed:
        """
        Build and return the final embed

        Returns:
            discord.Embed: The constructed embed
        """
        return self.embed
