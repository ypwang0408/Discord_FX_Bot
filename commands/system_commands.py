# -*- coding: utf-8 -*-
"""
System Commands Module
Handles system management commands: /system, /health, /maintenance
"""

import discord
from discord import app_commands
from datetime import datetime
import logging

from utils import require_admin_permission, EmbedBuilder, parse_timestamp_safe

logger = logging.getLogger(__name__)


def register_system_commands(bot, data_manager, system_manager, task_manager):
    """
    Register all system management slash commands

    Args:
        bot: Discord bot instance
        data_manager: ServerDataManager instance
        system_manager: SystemManager instance
        task_manager: TaskManager instance
    """

    @bot.tree.command(name="system", description="檢查系統運行狀態和API可用性 / Check system status and API availability")
    @app_commands.describe(mode="檢查模式 / Check mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="快速檢查 / Quick Check", value="quick"),
        app_commands.Choice(name="詳細檢查 / Detailed Check", value="detailed")
    ])
    @require_admin_permission()
    async def system_slash(interaction: discord.Interaction, mode: str = "quick"):
        """全面的系統狀態檢查（整合版）"""

        # 檢查系統管理器是否可用
        if system_manager is None:
            await interaction.response.send_message("❌ 系統管理器未正確初始化，請重啟機器人")
            return

        if mode == "detailed":
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

        # Build embed with appropriate color
        embed_builder = EmbedBuilder(title)
        embed_builder.set_color(status_colors.get(overall_status, 0x888888))

        # 整體狀態
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'error': '❌',
            'unknown': '❓'
        }

        embed_builder.add_field(
            "🎯 整體狀態 / Overall Status",
            f"{status_emoji.get(overall_status, '❓')} **{overall_status.upper()}**"
        )

        if mode == "detailed":
            # 詳細報告模式
            quick_stats = system_report.get('quick_stats', {})

            # 確保 quick_stats 不是 None
            if quick_stats is None:
                quick_stats = {}

            # 健康檢查摘要
            if quick_stats:
                embed_builder.add_field(
                    "📊 健康檢查 / Health Checks",
                    f"檢查項目 / Total: {quick_stats.get('health_checks_total', 0)}\n"
                    f"✅ 健康 / Healthy: {quick_stats.get('health_checks_healthy', 0)}\n"
                    f"🔄 連續失敗 / Failures: {quick_stats.get('consecutive_failures', 0)}"
                )

                # 系統資源
                memory_percent = quick_stats.get('memory_usage_percent', 0)
                disk_percent = quick_stats.get('disk_usage_percent', 0)
                memory_gb = quick_stats.get('memory_used_gb', 0)

                embed_builder.add_field(
                    "💻 系統資源 / System Resources",
                    f"記憶體 / Memory: {memory_percent:.1f}% ({memory_gb:.1f}GB)\n"
                    f"磁碟 / Disk: {disk_percent:.1f}%\n"
                    f"API狀態 / API: {quick_stats.get('api_status', 'unknown')}"
                )

            # 建議
            recommendations = system_report.get('recommendations', [])
            if recommendations is None:
                recommendations = []
            if recommendations:
                embed_builder.add_field(
                    "💡 系統建議 / Recommendations",
                    '\n'.join([f"• {rec}" for rec in recommendations[:4]])
                )

            # 維護統計
            maintenance_info = system_report.get('maintenance', {})
            if maintenance_info is None:
                maintenance_info = {}
            if maintenance_info and not maintenance_info.get('error'):
                latest_activity_info = maintenance_info.get('latest_activity', {})
                if latest_activity_info is None:
                    latest_activity_info = {}
                embed_builder.add_field(
                    "🔧 維護狀態 / Maintenance Status",
                    f"24小時活動 / 24h Activities: {maintenance_info.get('total_activities', 0)}\n"
                    f"最新活動 / Latest: {latest_activity_info.get('activity_type', 'none')}"
                )

        else:
            # 快速報告模式
            embed_builder.add_field(
                "⏱️ 運行時間 / Uptime",
                f"{system_report.get('uptime_hours', 0):.1f} 小時 / hours"
            )

            embed_builder.add_field(
                "💾 記憶體使用 / Memory Usage",
                f"{system_report.get('memory_usage_mb', 0):.1f} MB"
            )

            # 健康狀態指示
            is_healthy = system_report.get('is_healthy', False)
            health_status = "正常 / Healthy" if is_healthy else "需要注意 / Needs Attention"
            embed_builder.add_field("🏥 健康狀態 / Health Status", health_status)

            # 如果有錯誤，顯示錯誤信息
            if system_report.get('error'):
                error_msg = system_report['error']
                error_display = error_msg[:200] + "..." if len(error_msg) > 200 else error_msg
                embed_builder.add_field("❌ 錯誤信息 / Error", error_display)

        # 基本Bot資訊
        embed_builder.add_separator()
        monitor_status = '✅ 運行中' if task_manager.rate_check_task and not task_manager.rate_check_task.cancelled() else '❌ 已停止'
        embed_builder.add_field(
            "🤖 Bot資訊 / Bot Info",
            f"名稱 / Name: {bot.user.name}\n"
            f"延遲 / Latency: {round(bot.latency * 1000)}ms\n"
            f"監控狀態 / Monitor: {monitor_status}"
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

        embed_builder.add_field(
            "🌐 服務狀態 / Service Status",
            f"總伺服器 / Servers: {total_servers}\n"
            f"已設定通知 / Notifications: {servers_with_channels}\n"
            f"系統管理器 / System Manager: ✅ 已啟用"
        )

        # 操作提示
        if mode == "detailed":
            embed_builder.add_separator()
            embed_builder.add_field(
                "🔧 快速操作 / Quick Actions",
                "• `/system` - 快速狀態檢查\n"
                "• `/maintenance daily` - 執行維護\n"
                "• `/health` - 健康檢查詳情"
            )

        embed_builder.with_footer("整合系統管理 v1.0 / Integrated System Management v1.0")

        await interaction.followup.send(embed=embed_builder.build())

    @bot.tree.command(name="health", description="系統健康檢查 / System health check")
    @app_commands.describe(check_type="檢查類型 / Check type")
    @app_commands.choices(check_type=[
        app_commands.Choice(name="快速檢查 / Quick Check", value="quick"),
        app_commands.Choice(name="詳細檢查 / Detailed Check", value="detailed")
    ])
    @require_admin_permission()
    async def health_slash(interaction: discord.Interaction,
                          check_type: str = "quick"):
        """
        系統健康檢查
        check_type: "quick" 為快速檢查，"detailed" 為詳細檢查
        """

        # 參數驗證
        if check_type not in ["quick", "detailed"]:
            await interaction.response.send_message("❌ 檢查類型必須是 'quick' 或 'detailed' / Check type must be 'quick' or 'detailed'")
            return

        if check_type == "quick":
            await interaction.response.send_message("⚡ 執行快速健康檢查... / Performing quick health check...")
            health_report = await system_manager.health_monitor.quick_health_check()
            title = "⚡ 快速健康檢查 / Quick Health Check"

            # 💾 保存快速健康檢查結果到持久化存儲
            if health_report and health_report.get('status'):
                formatted_report = {
                    'overall_status': health_report.get('status'),
                    'details': health_report.get('checks', {}),
                    'timestamp': health_report.get('timestamp', datetime.now().isoformat()),
                    'warnings': health_report.get('warnings', []),
                    'errors': health_report.get('errors', [])
                }
                await system_manager._save_health_check_result(formatted_report, 'quick')

        else:  # detailed
            await interaction.response.send_message("🔍 執行詳細健康檢查... / Performing comprehensive health check...")
            health_report = await system_manager.health_monitor.comprehensive_health_check()
            title = "🔍 詳細健康檢查 / Comprehensive Health Check"

            # 💾 保存詳細健康檢查結果到持久化存儲
            if health_report and health_report.get('overall_status'):
                formatted_report = {
                    'overall_status': health_report.get('overall_status'),
                    'details': health_report.get('checks', {}),
                    'timestamp': health_report.get('timestamp', datetime.now().isoformat()),
                    'warnings': health_report.get('warnings', []),
                    'errors': health_report.get('errors', [])
                }
                await system_manager._save_health_check_result(formatted_report, 'detailed')
                logger.info("✅ 手動詳細健康檢查已完成並保存")

                # 🔍 立即驗證保存結果
                health_history = data_manager.data.get('health_check_history', {})
                last_detailed = health_history.get('last_detailed_check')
                if last_detailed and last_detailed.get('timestamp'):
                    logger.info(f"✅ 詳細檢查保存驗證成功: {last_detailed['timestamp']}")
                else:
                    logger.error("❌ 詳細檢查保存驗證失敗")

        # 統一的結果顯示
        status_key = 'overall_status' if check_type == 'detailed' else 'status'
        status = health_report.get(status_key, 'unknown')

        embed_builder = EmbedBuilder(title)
        if status == 'healthy':
            embed_builder.success()
        elif status == 'error':
            embed_builder.error()
        else:
            embed_builder.warning()

        # 狀態欄位
        status_icons = {"healthy": "✅", "warning": "⚠️", "error": "❌", "unknown": "❓"}

        embed_builder.add_field(
            "🎯 整體狀態 / Overall Status",
            f"{status_icons.get(status, '❓')} **{status.upper()}**"
        )

        embed_builder.add_field(
            "🔍 檢查項目 / Checks Performed",
            f"檢查數量 / Total Checks: {len(health_report.get('checks', {}))}"
        )

        # 檢查結果摘要
        if health_report.get('checks'):
            check_summary = []
            for check_name, check_result in health_report['checks'].items():
                if isinstance(check_result, dict):
                    check_status = check_result.get('status', 'unknown')
                    status_icon = status_icons.get(check_status, "❓")
                    check_summary.append(f"{status_icon} {check_name}")
                else:
                    check_summary.append(f"❓ {check_name}")

            embed_builder.add_field(
                "📋 檢查結果 / Check Results",
                '\n'.join(check_summary[:10]) if check_summary else "無檢查項目 / No checks"
            )

            if len(check_summary) > 10:
                embed_builder.with_footer(f"顯示前10項，共{len(check_summary)}項檢查 / Showing 10 of {len(check_summary)} checks")

        # 顯示警告和錯誤（僅詳細檢查）
        if check_type == "detailed":
            warnings = health_report.get('warnings', [])
            errors = health_report.get('errors', [])

            if warnings:
                warning_text = '\n'.join(warnings[:5]) + ('\n...' if len(warnings) > 5 else '')
                embed_builder.add_field("⚠️ 警告 / Warnings", warning_text)

            if errors:
                error_text = '\n'.join(errors[:5]) + ('\n...' if len(errors) > 5 else '')
                embed_builder.add_field("❌ 錯誤 / Errors", error_text)

        # 顯示檢查完成時間
        timestamp = health_report.get('timestamp', datetime.now().isoformat())
        embed_builder.add_field("🕒 檢查時間 / Check Time", f"`{timestamp}`")

        # 添加使用提示
        if check_type == "quick":
            embed_builder.with_footer("提示：使用 /health detailed 獲取詳細分析 / Tip: Use /health detailed for comprehensive analysis")
        else:
            # 顯示保存狀態
            health_history = data_manager.data.get('health_check_history', {})
            last_detailed = health_history.get('last_detailed_check')
            if last_detailed and last_detailed.get('timestamp'):
                embed_builder.with_footer("✅ 詳細檢查已保存到系統記錄 / Detailed check saved to system records")
            else:
                embed_builder.with_footer("⚠️ 檢查結果保存可能有問題 / Check result saving may have issues")

        await interaction.followup.send(embed=embed_builder.build())

    @bot.tree.command(name="maintenance", description="系統維護管理 / System maintenance management")
    @app_commands.describe(operation="維護操作類型 / Maintenance operation type")
    @app_commands.choices(operation=[
        app_commands.Choice(name="維護摘要 / Summary", value="summary"),
        app_commands.Choice(name="每日維護 / Daily Maintenance", value="daily"),
        app_commands.Choice(name="緊急清理 / Emergency Cleanup", value="emergency")
    ])
    @require_admin_permission()
    async def maintenance_slash(interaction: discord.Interaction, operation: str = "summary"):
        """系統維護管理"""

        valid_operations = ["summary", "daily", "emergency"]
        if operation not in valid_operations:
            await interaction.response.send_message(f"❌ 無效的維護操作。可用選項: {', '.join(valid_operations)} / Invalid operation. Available: {', '.join(valid_operations)}")
            return

        if operation == "summary":
            await interaction.response.send_message("📊 獲取維護狀態... / Getting maintenance status...")

            try:
                maintenance_summary = system_manager.auto_maintenance.get_maintenance_summary(24)

                embed = discord.Embed(
                    title="📊 維護狀態摘要 / Maintenance Status Summary",
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
                embed = (EmbedBuilder("❌ 維護狀態獲取失敗", f"錯誤: {str(e)}")
                    .error()
                    .build())

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
                    title=f"🔧 {'日常維護' if operation == 'daily' else '緊急清理'}報告 / {'Daily Maintenance' if operation == 'daily' else 'Emergency Cleanup'} Report",
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

    logger.info("✅ System commands registered")
