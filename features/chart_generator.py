# -*- coding: utf-8 -*-
"""
圖表生成模組
負責生成匯率趨勢圖表和視覺化展示
"""

import matplotlib
matplotlib.use('Agg')  # 使用非互動式後端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RateChartGenerator:
    """匯率圖表生成器"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        # 設定圖表樣式
        try:
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Microsoft JhengHei']
        except:
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
    
    async def generate_rate_chart(self, guild_id, days=7):
        """生成匯率趨勢圖"""
        server_data = self.data_manager.get_server_data(guild_id)
        # 使用統一的匯率歷史而不是伺服器特定的歷史
        rate_history = self.data_manager.get_rate_history(guild_id, days)
        
        if len(rate_history) < 2:
            logger.warning("伺服器 " + str(guild_id) + " 匯率數據不足，無法生成圖表")
            return None
        
        # 過濾最近N天的數據（已經在 data_manager.get_rate_history 中處理）
        filtered_data = rate_history
        
        if len(filtered_data) < 2:
            logger.warning("伺服器 " + str(guild_id) + " 最近" + str(days) + "天的數據不足")
            return None
        
        try:
            # 準備數據
            dates = [datetime.fromisoformat(record['timestamp']) for record in filtered_data]
            rates = [record['rate'] for record in filtered_data]
            threshold = server_data['threshold']
            
            # 創建圖表
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 繪製匯率線
            ax.plot(dates, rates, 'b-', linewidth=2, label='JPY/TWD Rate', marker='o', markersize=3)
            
            # 繪製閾值線
            ax.axhline(y=threshold, color='r', linestyle='--', alpha=0.7, 
                      label='Threshold ' + str(threshold))
            
            # 標記低於閾值的區域
            below_threshold = np.array(rates) < threshold
            if np.any(below_threshold):
                ax.fill_between(dates, np.min(rates), threshold, 
                               where=below_threshold,
                               color='red', alpha=0.2, label='Below Threshold')
            
            # 設定圖表樣式
            ax.set_title('JPY/TWD Exchange Rate Trend (Last ' + str(days) + ' Days)', fontsize=16, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Exchange Rate (JPY/TWD)', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 格式化x軸日期 - 優化版本
            if days <= 3:
                # 3天內：顯示日期+時間，水平顯示
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d\n%H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
                rotation_angle = 0  # 水平顯示
            elif days <= 7:
                # 7天內：顯示日期+小時，輕微傾斜
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=8))
                rotation_angle = 15  # 輕微傾斜
            elif days <= 14:
                # 14天內：只顯示日期，水平顯示
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                rotation_angle = 0  # 水平顯示
            else:
                # 超過14天：顯示日期，間隔更大
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
                rotation_angle = 0  # 水平顯示
            
            # 設定旋轉角度 - 使用 plt.setp 來確保設定生效
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=rotation_angle, ha='center' if rotation_angle == 0 else 'right')
            plt.tight_layout()
            
            # 保存到記憶體
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            logger.info("為伺服器 " + str(guild_id) + " 生成了 " + str(days) + " 天的匯率圖表")
            return buffer
            
        except Exception as e:
            logger.error("生成圖表時發生錯誤: " + str(e))
            return None
    
    async def generate_comparison_chart(self, guild_id, comparison_days=[7, 30]):
        """生成比較圖表（多時間段對比）"""
        server_data = self.data_manager.get_server_data(guild_id)
        
        # 獲取30天的數據（足夠覆蓋所有比較期間）
        all_rate_history = self.data_manager.get_rate_history(guild_id, max(comparison_days))
        
        if len(all_rate_history) < 2:
            return None
        
        try:
            fig, axes = plt.subplots(len(comparison_days), 1, figsize=(12, 6 * len(comparison_days)))
            if len(comparison_days) == 1:
                axes = [axes]
            
            for i, days in enumerate(comparison_days):
                cutoff_date = datetime.now() - timedelta(days=days)
                filtered_data = [
                    record for record in all_rate_history
                    if datetime.fromisoformat(record['timestamp']) > cutoff_date
                ]
                
                if len(filtered_data) < 2:
                    continue
                
                dates = [datetime.fromisoformat(record['timestamp']) for record in filtered_data]
                rates = [record['rate'] for record in filtered_data]
                threshold = server_data['threshold']
                
                ax = axes[i]
                ax.plot(dates, rates, 'b-', linewidth=2, label='JPY/TWD Rate (' + str(days) + ' days)')
                ax.axhline(y=threshold, color='r', linestyle='--', alpha=0.7, label='Threshold ' + str(threshold))
                
                below_threshold = np.array(rates) < threshold
                if np.any(below_threshold):
                    ax.fill_between(dates, np.min(rates), threshold,
                                   where=below_threshold,
                                   color='red', alpha=0.2, label='Below Threshold')
                
                ax.set_title('Last ' + str(days) + ' Days', fontsize=14)
                ax.set_xlabel('Date')
                ax.set_ylabel('Exchange Rate (JPY/TWD)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # 優化的日期格式
                if days <= 3:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d\n%H:%M'))
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
                elif days <= 7:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                    ax.xaxis.set_major_locator(mdates.HourLocator(interval=8))
                else:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
                
                # 設定適合的旋轉角度
                rotation_angle = 0 if days > 7 else 15
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=rotation_angle)
            
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error("生成比較圖表時發生錯誤: " + str(e))
            return None
    
    async def generate_statistics_chart(self, guild_id, days=30):
        """生成統計圖表（包含統計信息）"""
        server_data = self.data_manager.get_server_data(guild_id)
        # 使用統一的匯率歷史
        rate_history = self.data_manager.get_rate_history(guild_id, days)
        
        if len(rate_history) < 2:
            return None
        
        try:
            # 數據已經在 data_manager.get_rate_history 中過濾了
            filtered_data = rate_history
            
            if len(filtered_data) < 2:
                return None
            
            dates = [datetime.fromisoformat(record['timestamp']) for record in filtered_data]
            rates = [record['rate'] for record in filtered_data]
            threshold = server_data['threshold']
            
            # 計算統計數據
            min_rate = min(rates)
            max_rate = max(rates)
            avg_rate = sum(rates) / len(rates)
            volatility = (max_rate - min_rate) / avg_rate * 100
            below_threshold_pct = sum(1 for rate in rates if rate < threshold) / len(rates) * 100
            
            # 創建圖表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 主圖表
            ax1.plot(dates, rates, 'b-', linewidth=2, label='JPY/TWD Rate')
            ax1.axhline(y=threshold, color='r', linestyle='--', alpha=0.7, label='Threshold ' + str(threshold))
            ax1.axhline(y=avg_rate, color='g', linestyle=':', alpha=0.7, label='Average ' + str(round(avg_rate, 4)))
            
            below_threshold = np.array(rates) < threshold
            if np.any(below_threshold):
                ax1.fill_between(dates, min_rate, threshold,
                               where=below_threshold,
                               color='red', alpha=0.2, label='Below Threshold')
            
            ax1.set_title('JPY/TWD Rate with Statistics (Last ' + str(days) + ' Days)', fontsize=16)
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Exchange Rate')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 優化統計圖表的x軸格式
            if days <= 7:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d\n%H:%M'))
                ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))
            elif days <= 14:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            else:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
            
            # 水平顯示日期標籤
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0)
            
            # 統計信息文字
            stats_text = """Statistics (Last """ + str(days) + """ Days):
Min: """ + str(round(min_rate, 4)) + """  Max: """ + str(round(max_rate, 4)) + """  Avg: """ + str(round(avg_rate, 4)) + """
Volatility: """ + str(round(volatility, 2)) + """%  Below Threshold: """ + str(round(below_threshold_pct, 1)) + """%"""
            
            ax2.text(0.05, 0.5, stats_text, transform=ax2.transAxes, fontsize=12,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
            
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error("生成統計圖表時發生錯誤: " + str(e))
            return None
