# 玉山銀行日幣匯率監控 Discord Bot
**E.SUN Bank JPY Exchange Rate Monitor Discord Bot**

一個自動監控玉山銀行日幣匯率的Discord機器人，採用現代化模組架構設計，具備智能通知、圖表生成、健康監控、自動備份等功能。

*A Discord bot that automatically monitors E.SUN Bank's JPY exchange rate with modern modular architecture, featuring smart notifications, chart generation, health monitoring, and automatic backup.*

---

## :books: 文檔導航 / Documentation

| 文檔類型 | 描述 | 連結 |
|---------|------|------|
| :rocket: **快速開始** | 安裝、部署和初始設定指南 | [INSTALLATION.md](docs/INSTALLATION.md) |
| :video_game: **指令手冊** | 完整的 Discord 指令使用說明 | [COMMANDS.md](docs/COMMANDS.md) |
| :wrench: **Bot 管理** | 啟動、停止、狀態檢查等管理操作 | [BOT_MANAGEMENT.md](docs/BOT_MANAGEMENT.md) |
| :hospital: **健康監控** | 系統健康檢查和自動化運維功能 | [HEALTH_MONITORING.md](docs/HEALTH_MONITORING.md) |
| :alarm_clock: **精準調度** | 時間調度系統技術原理和實現 | [PRECISE_SCHEDULING.md](docs/PRECISE_SCHEDULING.md) |
| :sparkles: **功能總結** | 完整功能列表和技術架構說明 | [FEATURE_SUMMARY.md](docs/FEATURE_SUMMARY.md) |
| :sos: **故障排除** | 常見問題診斷和解決方案 | [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

---

## :sparkles: 核心特色 / Key Features

### :repeat: 智能監控系統
- **精準時間調度**: 每小時整點和30分精確執行，消除時間漂移
- **智能通知**: 避免重複訊息的三種通知條件
- **API容錯**: 主API失敗時自動切換到備用API
- **多伺服器支援**: 每個Discord伺服器獨立設定
- **任務生命週期管理**: 全域任務追蹤，支援優雅重啟

### :bar_chart: 數據可視化
- **即時圖表**: 1-30天可選的匯率趨勢圖
- **專業視覺化**: 高解析度PNG圖表，包含閾值線和趨勢分析
- **歷史記錄**: 自動保留30天匯率歷史數據

### :floppy_disk: 數據管理
- **智能備份**: 每日自動備份，超過7天只保留星期一的備份
- **數據持久化**: JSON格式存儲，支援手動備份和恢復
- **健康檢查記錄**: 自動保存系統健康狀態，便於分析系統趨勢

### :hospital: 健康監控系統
- **全面檢查**: API狀態、系統資源、數據完整性、文件系統
- **自動維護**: 日誌清理、備份管理、性能優化、任務重新調度
- **智能警報**: 自動檢測異常並記錄，支援自動恢復
- **精準調度**: 每小時15分和45分執行健康檢查

### :zap: 現代化介面
- **Slash Commands**: 完全支援Discord最新的斜線命令
- **自動補全**: 輸入`/`即可享受命令自動補全
- **多語言支援**: 中英文雙語介面

---

## :building_construction: 模組化架構

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
│   ├── health_monitor.py   # 健康監控模組
│   ├── auto_maintenance.py # 自動化運維模組
│   └── system_manager.py   # 系統整合管理模組
├── scripts/                # 輔助腳本目錄
│   ├── start.sh           # 啟動腳本
│   ├── stop.sh            # 停止腳本
│   └── status.sh          # 狀態檢查腳本
├── backups/                # 自動備份目錄
├── bot.sh                  # 統一管理腳本
└── requirements.txt        # Python依賴
```

---

## :zap: 快速開始 / Quick Start

### :clipboard: 系統需求 / System Requirements
| 項目 | 需求 | 說明 |
|------|------|------|
| **Python** | 3.8+ (推薦 3.9+) | 核心運行環境 |
| **作業系統** | Linux, macOS, Windows | 跨平台支援 |
| **Discord Bot Token** | 必須 | 需要創建 Discord Application |
| **網路連接** | 穩定連接 | 用於API調用和Discord通訊 |

### :package: 快速安裝 / Quick Installation
```bash
# 1. Clone 專案
git clone https://github.com/your-username/Discord_FX_Bot.git
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

> :information_source: **詳細安裝指南**: 請參考 [INSTALLATION.md](docs/INSTALLATION.md) 獲得完整的部署指南

---

## :video_game: 主要指令 / Main Commands

### :chart_with_upwards_trend: 基本功能 / Basic Features
| 指令 | 說明 | 使用範例 | 權限需求 |
|------|------|----------|----------|
| `/rate` | 查詢當前日幣匯率 | `/rate` | 所有用戶 |
| `/threshold` | 設定監控閾值 | `/threshold 0.21` | 管理員 |
| `/chart` | 生成匯率趨勢圖表 | `/chart days:7` | 所有用戶 |
| `/status` | 查看機器人狀態 | `/status` | 所有用戶 |
| `/channel` | 設定通知頻道 | `/channel` | 管理員 |

### :gear: 系統管理 / System Management
| 指令 | 說明 | 功能描述 | 權限需求 |
|------|------|----------|----------|
| `/system` | 系統狀態檢查 | 整體狀態、資源使用、健康監控 | 管理員 |
| `/health` | 健康監控檢查 | API狀態、系統資源、數據完整性 | 管理員 |
| `/maintenance` | 系統維護操作 | 日誌清理、備份管理、性能優化 | 管理員 |
| `/backup` | 手動創建備份 | 立即創建數據備份 | 管理員 |

> :book: **完整指令手冊**: 查看 [COMMANDS.md](docs/COMMANDS.md) 獲得所有指令的詳細說明

---

## :brain: 智能通知邏輯

### :alarm_clock: 調度時程 / Schedule
| 監控類型 | 執行時間 | 說明 |
|---------|---------|------|
| **匯率檢查** | 每小時 :00 和 :30 分 | 精準時間調度，無時間漂移 |
| **健康檢查** | 每小時 :15 和 :45 分 | 系統狀態監控 |
| **每日備份** | 每日 00:00 | 自動數據備份 |
| **每日維護** | 每日 02:00 | 系統維護和任務重新調度 |

### :bell: 通知條件 / Notification Rules
通知將在滿足以下**任一**條件時發送：

1. :chart_trending_down: **狀態變化**: 匯率從高於閾值變為低於閾值
2. :sunrise: **早晨提醒**: 每日上午9:00，且匯率低於閾值  
3. :city_sunset: **晚間提醒**: 每日晚上9:00，且匯率低於閾值

### :shield: 智能防垃圾機制
- :mute: 持續低於閾值時不會重複通知
- :bookmark: 狀態記錄確保只在關鍵時刻提醒
- :loud_sound: 可選 @everyone 群組通知

---

## :floppy_disk: 數據備份策略

### :calendar: 自動備份機制
| 項目 | 設定 | 說明 |
|------|------|------|
| **備份頻率** | 每日 00:00 執行 | 自動化無人值守 |
| **檔名格式** | `YYYYMMDD.json` | 便於識別和管理 |
| **備份內容** | 完整伺服器設定 + 匯率歷史 | 確保數據完整性 |

### :recycle: 智能清理策略
- :seven: **7天內**: 保留所有每日備份
- :calendar: **超過7天**: 僅保留星期一的備份  
- :wastebasket: **自動清理**: 避免磁碟空間不足

### :gear: 手動備份選項
- :hammer_and_wrench: 管理員可隨時使用 `/backup` 指令
- :page_facing_up: 支援 `/list_backups` 查看所有備份
- :white_check_mark: 備份驗證和完整性檢查

---

## :hammer_and_wrench: 管理工具 / Management Tools

### :dart: 統一管理腳本 / Unified Management Script
```bash
./bot.sh start    # 啟動機器人 / Start bot
./bot.sh stop     # 停止機器人 / Stop bot
./bot.sh restart  # 重啟機器人 / Restart bot
./bot.sh status   # 檢查狀態 / Check status
./bot.sh logs     # 查看即時日誌 / View logs
./bot.sh test     # 測試模組架構 / Test modules
```

> :information_source: **詳細管理指南**: 查看 [BOT_MANAGEMENT.md](docs/BOT_MANAGEMENT.md) 了解完整的管理操作

---

## :lock: 必要權限 / Required Permissions

Discord Bot 需要以下權限才能正常運作：

| 權限 | 必要性 | 說明 |
|------|-------|------|
| **Send Messages** | :white_check_mark: 必須 | 發送訊息 |
| **Use Slash Commands** | :white_check_mark: 必須 | 使用斜線命令 |
| **Embed Links** | :white_check_mark: 必須 | 嵌入連結 |
| **Read Message History** | :white_check_mark: 必須 | 讀取訊息歷史 |
| **Mention Everyone** | :warning: 可選 | @everyone 通知 |

### :link: 邀請連結範本 / Invite Link Template
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=2147633152&scope=bot%20applications.commands
```

---

## :chart_with_upwards_trend: 系統效能 / Performance Metrics

### :computer: 資源使用情況
| 資源類型 | 一般使用 | 檢查時使用 | 說明 |
|---------|---------|-----------|------|
| **記憶體** | ~50MB | ~80MB | 輕量化設計 |
| **CPU** | <1% | <5% | 高效能運算 |
| **磁碟** | ~50MB | 動態增長 | 包含日誌和備份 |
| **網路** | 最小化 | 每30分鐘 | API調用優化 |

### :globe_with_meridians: 可擴展性
- :infinity: **多伺服器**: 支援無限制數量
- :arrows_clockwise: **並發處理**: 異步處理架構
- :gear: **模組化**: 易於擴展新功能

---

## :mag: 需要幫助？ / Need Help?

### :books: 查看相關文檔 / Check Documentation
- :sos: **遇到問題**: [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 故障排除指南
- :sparkles: **了解功能**: [FEATURE_SUMMARY.md](docs/FEATURE_SUMMARY.md) - 完整功能說明  
- :hospital: **健康監控**: [HEALTH_MONITORING.md](docs/HEALTH_MONITORING.md) - 系統監控功能

### :stethoscope: 快速診斷 / Quick Diagnosis
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

---

## :robot: 開發工具 / Development Tools

本專案大量使用 **GitHub Copilot** 和 **GitHub Copilot Chat** 進行開發：

- :brain: **智能程式碼生成**: 利用 Copilot 快速生成模組化架構和複雜邏輯
- :memo: **文檔協作**: 使用 Copilot Chat 協助撰寫技術文檔和使用手冊
- :wrench: **程式碼重構**: 透過 AI 輔助將舊有程式碼重構為模組化設計
- :white_check_mark: **測試與除錯**: Copilot 協助生成測試案例和故障排除邏輯
- :dart: **最佳實踐**: AI 建議遵循 Python 和 Discord.py 的最佳實踐

---

## :new: 更新日誌 / Changelog

### v2.2.0 (2025-07-27)
- :alarm_clock: **精準時間調度系統**: 替換輪詢機制，實現精確的時間觸發
- :repeat: **任務生命週期管理**: 全域任務追蹤，支援優雅取消和重啟
- :bar_chart: **詳細健康檢查**: 維護期間包含完整的系統健康驗證
- :dart: **時間同步**: 每日重新調度任務，防止長期時間漂移
- :books: **精準調度文檔**: 新增專門的技術文檔說明調度原理

### v2.1.0 (2025-07-27)
- :sparkles: **健康監控系統**: 全面的系統健康檢查和自動維護
- :zap: **API 調用優化**: 減少50% API請求次數
- :floppy_disk: **健康檢查記錄持久化**: 自動保存健康狀態歷史
- :file_folder: **文檔重組**: 模組化文檔結構，更易於導航
- :wrench: **系統整合**: 統一的系統管理架構

### v2.0.0 (2025-07-26)
- :sparkles: 完全重構為模組化架構
- :dart: 全面支援 Slash Commands
- :bar_chart: 新增圖表生成功能
- :floppy_disk: 智能備份系統
- :wrench: 統一管理腳本

---

## :telephone_receiver: 支援與貢獻 / Support & Contributing

### :handshake: 如何貢獻 / How to Contribute
1. **Fork 專案** / Fork the project
2. **創建功能分支** / Create feature branch (`git checkout -b feature/AmazingFeature`)
3. **提交變更** / Commit changes (`git commit -m 'Add AmazingFeature'`)
4. **推送到分支** / Push to branch (`git push origin feature/AmazingFeature`)
5. **開啟 Pull Request** / Open Pull Request

### :clipboard: 問題回報 / Issue Reporting
請在 GitHub Issues 中提供以下資訊：
- :bug: 錯誤描述和重現步驟
- :gear: `./bot.sh test` 輸出結果
- :scroll: 相關日誌內容 (`bot.log`) 
- :computer: 系統環境資訊

---

## :heart: 致謝 / Acknowledgments

- **Discord.py 開發團隊** - 優秀的 Discord API 封裝
- **玉山銀行** - 提供即時匯率資料
- **GitHub Copilot** - AI 開發協助工具
- **所有貢獻者和使用者** - 持續的支持和回饋

---

**最後更新**: 2025-07-27  
**開發工具**: GitHub Copilot :robot: 
