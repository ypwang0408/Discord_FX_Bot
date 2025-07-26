# 玉山銀行日幣匯率監控 Discord 機器人
# E.SUN Bank JPY Exchange Rate Monitor Discord Bot

一個自動監控玉山銀行日幣匯率的Discord機器人，採用現代化模組架構設計，具備智能通知、圖表生成、自動備份等功能。

A Discord bot that automatically monitors E.SUN Bank's JPY exchange rate with modern modular architecture, featuring smart notifications, chart generation, and automatic backup.

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
- **完整記錄**: 包含時間戳、檔案大小、伺服器數量等詳細信息

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
│   ├── data_manager.py     # 數據管理模組
│   ├── exchange_rate_monitor.py  # 匯率監控模組
│   ├── backup_manager.py   # 備份管理模組
│   ├── chart_generator.py  # 圖表生成模組
│   └── notification_system.py    # 通知系統模組
├── scripts/                # 輔助腳本目錄
│   ├── start.sh           # 啟動腳本
│   ├── stop.sh            # 停止腳本
│   └── status.sh          # 狀態檢查腳本
├── backups/                # 自動備份目錄
├── bot.sh                  # 統一管理腳本
└── requirements.txt        # Python依賴
```

## 🚀 快速開始

### 📋 系統需求
- Python 3.8+
- Discord Bot Token
- 穩定的網路連接

### ⚙️ 安裝步驟

1. **Clone專案並進入目錄**
   ```bash
   git clone <your-repo>
   cd discord-bot
   ```

2. **設定虛擬環境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **配置環境變數**
   ```bash
   # 創建 .env 檔案
   echo "DISCORD_BOT_TOKEN=your_bot_token_here" > .env
   ```

4. **啟動機器人**
   ```bash
   # 推薦使用統一管理腳本
   ./bot.sh start
   
   # 或使用基本啟動腳本
   ./scripts/start.sh
   ```

5. **驗證運行狀態**
   ```bash
   ./bot.sh status
   ```

## 🎮 Discord 指令完整列表

### 📊 基本功能
| 指令 | 說明 | 範例 | 權限需求 |
|------|------|------|----------|
| `/rate` | 查詢當前日幣匯率 | `/rate` | 無 |
| `/threshold` | 設定監控閾值 | `/threshold 0.21` | 管理員 |
| `/channel` | 設定通知頻道為當前頻道 | `/channel` | 無 |
| `/status` | 查看機器人運行狀態 | `/status` | 無 |
| `/help` | 顯示幫助訊息 | `/help` | 無 |
| `/rules` | 顯示通知規則說明 | `/rules` | 無 |

### 📈 進階功能
| 指令 | 說明 | 範例 | 參數說明 |
|------|------|------|----------|
| `/chart` | 生成匯率趨勢圖表 | `/chart days:7` | days: 1-30天 |
| `/backup` | 手動創建數據備份 | `/backup` | 管理員限定 |
| `/list_backups` | 列出所有備份檔案 | `/list_backups` | 管理員限定 |

### 🔧 系統管理
| 指令 | 說明 | 功能描述 |
|------|------|----------|
| `/system` | 全面系統狀態檢查 | API狀態、監控狀態、多伺服器統計 |
| `/permissions` | 檢查機器人權限 | 驗證必要權限是否正確設定 |
| `/sync` | 手動同步Slash Commands | 重新註冊所有斜線命令 |
| `/mention` | 設定@everyone通知 | 啟用/停用群組通知功能 |

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

## 🛠️ 管理工具

### 🎯 統一管理腳本 (`./bot.sh`)
```bash
./bot.sh start    # 啟動機器人
./bot.sh stop     # 停止機器人  
./bot.sh restart  # 重啟機器人
./bot.sh status   # 檢查狀態
./bot.sh logs     # 查看即時日誌
./bot.sh test     # 測試模組架構
```

### 📋 獨立腳本
- `scripts/start.sh` - 啟動腳本 (含環境檢查)
- `scripts/stop.sh` - 安全停止腳本 (含進程清理)
- `scripts/status.sh` - 狀態檢查腳本 (含PID資訊)

### 🖥️ tmux會話管理
```bash
# 連接到bot會話
tmux attach -t discord-bot

# 分離會話 (不停止bot)
Ctrl+B, 然後按 D

# 查看所有會話
tmux list-sessions

# 直接終止會話
tmux kill-session -t discord-bot
```

## 🔐 權限設定

### 🎯 Discord Bot 權限需求
**必要權限**:
- ✅ Send Messages (發送訊息)
- ✅ Use Slash Commands (使用斜線命令)
- ✅ Embed Links (嵌入連結)
- ✅ Read Message History (讀取訊息歷史)

**可選權限**:
- 🔔 Mention Everyone (@everyone通知功能)

### 📝 OAuth2 設定
```
Scopes: bot + applications.commands
Permissions: 2147502080 (基本) 或 2147633152 (含@everyone)
```

### 🔗 邀請連結範例
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=2147633152&scope=bot%20applications.commands
```

## 📈 資料來源與格式

### 🏦 主要資料來源
- **玉山銀行官網**: 即時匯率資料
- **備用API**: 國際匯率API (容錯機制)

### 💱 匯率格式說明
- **格式**: JPY/TWD (1日圓 = X台幣)
- **預設閾值**: 0.2 (當1日圓 < 0.2台幣時通知)
- **精度**: 小數點後4位

### 📊 歷史資料管理
- **保存期限**: 30天
- **更新頻率**: 每次檢查時自動更新
- **用途**: 圖表生成和趨勢分析

## 🐛 故障排除

### ❌ 常見問題

**1. Bot無法啟動**
```bash
# 檢查模組是否正常
./bot.sh test

# 查看詳細錯誤日誌
./bot.sh logs

# 檢查環境變數
cat .env
```

**2. 匯率無法獲取**
```bash
# 檢查系統狀態
/system  # 在Discord中執行

# 查看API狀態
tail -f bot.log | grep "API"
```

**3. 通知未發送**
```bash
# 檢查權限設定
/permissions  # 在Discord中執行

# 確認頻道設定
/status  # 在Discord中執行
```

**4. 進程殘留問題**
```bash
# 查看相關進程
ps aux | grep main.py

# 強制終止
pkill -f main.py

# 清理tmux會話
tmux kill-server
```

### 🔧 維護建議

**定期檢查**:
- 每週檢查備份檔案狀態
- 定期查看 `bot.log` 日誌
- 監控磁碟空間使用情況

**更新流程**:
1. 停止機器人: `./bot.sh stop`
2. 備份當前數據: `cp server_data.json server_data_backup.json`
3. 更新程式碼
4. 測試模組: `./bot.sh test`
5. 重新啟動: `./bot.sh start`

## 📊 效能指標

### ⚡ 系統效能
- **記憶體使用**: ~50MB (包含虛擬環境)
- **CPU使用**: 平時 <1%, 檢查時 <5%
- **磁碟使用**: ~100MB (包含依賴和備份)

### 🌐 網路需求
- **API請求頻率**: 每30分鐘 1-2次
- **資料傳輸量**: <1KB per request
- **容錯機制**: 3次重試 + 備用API

### 📈 擴展性
- **多伺服器支援**: 無限制
- **用戶並發**: Discord API限制內
- **資料增長**: 線性增長，自動清理舊資料

## 🆕 更新日誌

### v2.0.0 (2025-07-26)
- ✨ 完全重構為模組化架構
- 🎯 全面支援Slash Commands
- 📊 新增圖表生成功能
- 💾 智能備份系統 (每日+智能清理)
- 🔧 統一管理腳本
- 🐛 修復rate_history KeyError問題

### v1.x (Legacy)
- 🔄 基本匯率監控功能
- 📢 簡單通知系統

## 📞 支援與貢獻

### 🤝 如何貢獻
1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

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
