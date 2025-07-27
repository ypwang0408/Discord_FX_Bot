# 玉山銀行日幣匯率監控 Discord 機器人
# E.SUN Bank JPY Exchange Rate Monitor Discord Bot

一個自動監控玉山銀行日幣匯率的Discord機器人，採用現代化模組架構設計，具備智能通知、圖表生成、健康監控、自動備份等功能。

A Discord bot that automatically monitors E.SUN Bank's JPY exchange rate with modern modular architecture, featuring smart notifications, chart generation, health monitoring, and automatic backup.

## 📚 文檔導航 / Documentation

| 📖 文檔 | 📝 描述 | 🔗 連結 |
|---------|---------|---------|
| **快速開始** | 安裝、部署和初始設定指南 | [📦 INSTALLATION.md](docs/INSTALLATION.md) |
| **指令手冊** | 完整的 Discord 指令使用說明 | [🎮 COMMANDS.md](docs/COMMANDS.md) |
| **Bot 管理** | 啟動、停止、狀態檢查等管理操作 | [🤖 BOT_MANAGEMENT.md](docs/BOT_MANAGEMENT.md) |
| **健康監控** | 系統健康檢查和自動化運維功能 | [🏥 HEALTH_MONITORING.md](docs/HEALTH_MONITORING.md) |
| **功能總結** | 完整功能列表和技術架構說明 | [🎯 FEATURE_SUMMARY.md](docs/FEATURE_SUMMARY.md) |
| **故障排除** | 常見問題診斷和解決方案 | [🔧 TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

## ✨ 核心特色 / Key Features

### 🔄 智能監控系統
- **自動檢查**: 每小時整點和30分自動檢查匯率
- **智能通知**: 避免重複訊息的三種通知條件
- **API容錯**: 主API失敗時自動切換到備用API
- **多伺服器支援**: 每個Discord伺服器獨立設定

### 📊 數據可視化
- **即時圖表**: 1-30天可選的匯率趨勢圖
- **專業視覺化**: 高解析度PNG圖表，包含閾值線和趨勢分析
- **歷史記錄**: 自動保留30天匯率歷史數據

### 💾 數據管理
- **智能備份**: 每日自動備份，超過7天只保留星期一的備份
- **數據持久化**: JSON格式存儲，支援手動備份和恢復
- **健康檢查記錄**: 自動保存系統健康狀態，便於分析系統趨勢

### 🏥 健康監控系統
- **全面檢查**: API狀態、系統資源、數據完整性、文件系統
- **自動維護**: 日誌清理、備份管理、性能優化
- **智能警報**: 自動檢測異常並記錄，支援自動恢復

### ⚡ 現代化介面
- **Slash Commands**: 完全支援Discord最新的斜線命令
- **自動補全**: 輸入`/`即可享受命令自動補全
- **多語言支援**: 中英文雙語介面

## 🏗️ 模組化架構

```
discord-bot/
├── main.py                  # 主程式入口
├── features/               # 功能模組目錄
│   ├── __init__.py         # 模組初始化
│   ├── data_manager.py     # 數據管理模組 (含健康檢查記錄)
│   ├── exchange_rate_monitor.py  # 匯率監控模組 (API優化)
│   ├── backup_manager.py   # 備份管理模組
│   ├── chart_generator.py  # 圖表生成模組
│   ├── notification_system.py    # 通知系統模組
│   ├── health_monitor.py   # 健康監控模組 (新增)
│   ├── auto_maintenance.py # 自動化運維模組 (新增)
│   └── system_manager.py   # 系統整合管理模組 (新增)
├── scripts/                # 輔助腳本目錄
│   ├── start.sh           # 啟動腳本
│   ├── stop.sh            # 停止腳本
│   └── status.sh          # 狀態檢查腳本
├── backups/                # 自動備份目錄
├── bot.sh                  # 統一管理腳本
└── requirements.txt        # Python依賴
```

## 🚀 快速開始 / Quick Start

### 📋 系統需求 / Requirements
- **Python**: 3.8+ (推薦 3.9+)
- **作業系統**: Linux, macOS, Windows
- **Discord Bot Token**: 需要創建 Discord Application
- **網路連接**: 穩定的網際網路連接

### ⚡ 快速安裝 / Quick Installation
```bash
# 1. Clone 專案
git clone <your-repo-url>
cd Discord_FX_Bot

# 2. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 設定環境變數
echo "DISCORD_BOT_TOKEN=your_bot_token_here" > .env

# 5. 啟動 Bot
./bot.sh start
```

> 📖 **詳細安裝指南**: 請參考 [INSTALLATION.md](docs/INSTALLATION.md) 獲得完整的部署指南

## 🎮 主要指令 / Main Commands

### 📊 基本功能 / Basic Features
| 指令 | 說明 | 範例 |
|------|------|------|
| `/rate` | 查詢當前日幣匯率 | `/rate` |
| `/threshold` | 設定監控閾值 | `/threshold 0.21` |
| `/chart` | 生成匯率趨勢圖表 | `/chart days:7` |
| `/status` | 查看機器人狀態 | `/status` |

### 🔧 系統管理 / System Management
| 指令 | 說明 | 功能描述 |
|------|------|----------|
| `/system` | 系統狀態檢查 | 整體狀態、資源使用、健康監控 |
| `/health` | 健康監控檢查 | API狀態、系統資源、數據完整性 |
| `/maintenance` | 系統維護操作 | 日誌清理、備份管理、性能優化 |

> 📖 **完整指令手冊**: 查看 [COMMANDS.md](docs/COMMANDS.md) 獲得所有指令的詳細說明

## 🧠 智能通知邏輯

### ⏰ 檢查時程
- **檢查頻率**: 每小時的 :00 和 :30 分
- **檢查範圍**: 所有已設定通知頻道的伺服器

### 🚨 通知條件 (滿足任一即發送)
1. **狀態變化**: 匯率從高於閾值變為低於閾值
2. **早晨提醒**: 每日上午9:00，且匯率低於閾值
3. **晚間提醒**: 每日晚上9:00，且匯率低於閾值

### 💡 智能防垃圾
- 持續低於閾值時不會重複通知
- 狀態記錄確保只在關鍵時刻提醒
- 可選@everyone群組通知

## 📊 備份策略

### 🗓️ 自動備份
- **頻率**: 每日執行一次
- **檔名格式**: `YYYYMMDD.json`
- **執行時間**: 24小時循環

### 🧹 智能清理
- **7天內**: 保留所有每日備份
- **超過7天**: 僅保留星期一的備份
- **檔案結構**: 包含完整伺服器設定和匯率歷史

### 💾 手動備份
- 管理員可隨時使用 `/backup` 指令
- 支援 `/list_backups` 查看所有備份
- 備份驗證和完整性檢查

## 🛠️ 管理工具 / Management Tools

### 🎯 統一管理腳本 / Unified Management Script
```bash
./bot.sh start    # 啟動機器人 / Start bot
./bot.sh stop     # 停止機器人 / Stop bot
./bot.sh restart  # 重啟機器人 / Restart bot
./bot.sh status   # 檢查狀態 / Check status
./bot.sh logs     # 查看即時日誌 / View logs
./bot.sh test     # 測試模組架構 / Test modules
```

> � **詳細管理指南**: 查看 [BOT_MANAGEMENT.md](docs/BOT_MANAGEMENT.md) 了解完整的管理操作

## 🔐 必要權限 / Required Permissions

Discord Bot 需要以下權限才能正常運作：
- ✅ **Send Messages** - 發送訊息
- ✅ **Use Slash Commands** - 使用斜線命令  
- ✅ **Embed Links** - 嵌入連結
- ✅ **Read Message History** - 讀取訊息歷史
- 🔔 **Mention Everyone** - @everyone 通知 (可選)

### 📝 邀請連結 / Invite Link
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=2147633152&scope=bot%20applications.commands
```

### 🔗 邀請連結範例
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=2147633152&scope=bot%20applications.commands
```

## 📈 資料來源與格式

### 🏦 主要資料來源
- **玉山銀行官網**: 即時匯率資料
- **備用API**: 國際匯率API (容錯機制)

## 🔍 需要幫助？ / Need Help?

### � 查看相關文檔 / Check Documentation
- **遇到問題**: [🔧 TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 故障排除指南
- **了解功能**: [🎯 FEATURE_SUMMARY.md](docs/FEATURE_SUMMARY.md) - 完整功能說明  
- **健康監控**: [🏥 HEALTH_MONITORING.md](docs/HEALTH_MONITORING.md) - 系統監控功能

### � 快速診斷 / Quick Diagnosis
```bash
# 1. 檢查系統狀態
./bot.sh status

# 2. 測試模組完整性  
./bot.sh test

# 3. 查看即時日誌
./bot.sh logs

# 4. 在 Discord 中檢查
/system detailed:True
```

### � 系統效能 / Performance Metrics
- **記憶體使用**: ~50MB
- **CPU 使用**: <1% (平時), <5% (檢查時)
- **API 頻率**: 每30分鐘 1次 (已優化)
- **多伺服器**: 支援無限制數量

## 🆕 更新日誌 / Changelog

### v2.1.0 (2025-07-27) 🆕
- ✨ **健康監控系統**: 全面的系統健康檢查和自動維護
- ⚡ **API 調用優化**: 減少50% API請求次數
- 💾 **健康檢查記錄持久化**: 自動保存健康狀態歷史
- 📁 **文檔重組**: 模組化文檔結構，更易於導航
- 🔧 **系統整合**: 統一的系統管理架構

### v2.0.0 (2025-07-26)
- ✨ 完全重構為模組化架構
- 🎯 全面支援 Slash Commands
- 📊 新增圖表生成功能
- 💾 智能備份系統
- 🔧 統一管理腳本

## 📞 支援與貢獻 / Support & Contributing

### 🤝 如何貢獻 / How to Contribute
1. Fork 專案 / Fork the project
2. 創建功能分支 / Create feature branch (`git checkout -b feature/AmazingFeature`)
3. 提交變更 / Commit changes (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 / Push to branch (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request / Open Pull Request

### 📋 問題回報 / Issue Reporting
在 GitHub Issues 中提供以下資訊：
- 錯誤描述和重現步驟
- `./bot.sh test` 輸出結果
- 相關日誌內容 (`bot.log`)
- 系統環境資訊

### 📋 問題回報
請在 GitHub Issues 中提供:
- 錯誤描述和重現步驟
- 相關日誌內容 (`bot.log`)
- 系統環境資訊 (`./bot.sh test` 輸出)

---

## 📄 授權
本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝
- Discord.py 開發團隊
- 玉山銀行提供匯率資料
- 所有貢獻者和使用者

---

*最後更新: 2025-07-26*
