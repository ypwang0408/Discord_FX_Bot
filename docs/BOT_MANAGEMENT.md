# :robot: Discord Bot 管理指南

## 快速啟動

### 1. 使用統一管理腳本 (推薦)
```bash
# 啟動bot
./bot.sh start

# 檢查狀態  
./bot.sh status

# 查看即時日誌
./bot.sh logs

# 重啟bot
./bot.sh restart

# 停止bot
./bot.sh stop

# 測試模組架構
./bot.sh test
```

### 2. 使用個別腳本
```bash
# 啟動
./scripts/start.sh

# 檢查狀態
./scripts/status.sh

# 停止
./scripts/stop.sh
```

## :clipboard: 腳本說明

### `bot.sh` - 統一管理腳本
- **功能**: 所有bot管理操作的統一入口
- **優點**: 簡單易用，功能完整
- **推薦**: 日常使用的主要工具

### `scripts/start.sh` - 啟動腳本
- **功能**: 在tmux會話中啟動模組化bot
- **檢查**: 自動檢查 main.py、features目錄、虛擬環境
- **會話名稱**: `discord-bot`

### `scripts/status.sh` - 狀態檢查腳本  
- **功能**: 檢查bot運行狀態和進程資訊
- **顯示**: tmux會話狀態、進程PID、管理命令

### `scripts/stop.sh` - 停止腳本
- **功能**: 安全停止bot和清理進程
- **清理**: 終止tmux會話和相關進程

## :wrench: tmux 常用命令

```bash
# 查看所有會話
tmux list-sessions

# 連接到bot會話
tmux attach -t discord-bot

# 在會話內分離 (不停止bot)
Ctrl+B, 然後按 D

# 直接終止會話
tmux kill-session -t discord-bot
```

## :bar_chart: 模組架構

```
features/
├── __init__.py              # 模組初始化
├── data_manager.py          # 數據管理
├── exchange_rate_monitor.py # 匯率監控  
├── backup_manager.py        # 備份管理(每日一次，檔名YYYYMMDD.json)
├── chart_generator.py       # 圖表生成
├── notification_system.py   # 通知系統
├── health_monitor.py        # 健康監控系統 :new:
├── auto_maintenance.py      # 自動化運維 :new:
└── system_manager.py        # 系統整合管理 :new:
```

## :alarm_clock: 自動化任務調度 :new:

### 精準時間調度系統
- **匯率檢查**: 每小時整點和30分 (10:00, 10:30, 11:00...)
- **健康檢查**: 每小時15分和45分 (10:15, 10:45, 11:15...)  
- **每日備份**: 每天0:00自動執行
- **每日維護**: 每天2:00自動執行，包含：
  - 詳細健康檢查
  - 系統清理和優化
  - 任務重新調度（防止時間漂移）
  - 維護後健康檢查驗證

### 任務生命週期管理
- **全域追蹤**: 使用任務變數追蹤運行狀態
- **優雅取消**: 支援任務安全取消和重啟
- **狀態監控**: 透過 `/status` 查看任務實際狀態

## :rocket: 首次設置

1. **確保環境變數設定**:
   ```bash
   # 確認 .env 文件存在且包含
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```

2. **安裝依賴**:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **啟動bot**:
   ```bash
   ./bot.sh start
   ```

## :mag: 故障排除

### Bot無法啟動
```bash
# 檢查依賴和環境
./bot.sh test

# 查看詳細錯誤
./bot.sh logs
```

### 進程殘留
```bash
# 查看相關進程
ps aux | grep main.py

# 強制終止
pkill -f main.py
```

### tmux會話問題
```bash
# 查看所有會話
tmux list-sessions

# 清理所有會話
tmux kill-server
```

## :sparkles: 特色功能

- **精準時間調度**: 完全消除輪詢機制，使用計算睡眠時間實現精確觸發 :new:
- **任務生命週期管理**: 全域任務追蹤，支援優雅取消和重啟 :new:
- **模組化架構**: 易於維護和擴展
- **智慧啟動**: 自動檢查環境和依賴
- **安全停止**: 完整清理進程和會話
- **統一管理**: 單一腳本處理所有操作
- **狀態監控**: 即時查看運行狀態
- **智能備份**: 每日備份，超過7天只保留星期一
- **錯誤處理**: 完善的異常處理機制
- **系統整合**: 健康監控和自動維護完整整合 :new:

## :iphone: Discord 指令

啟動後，在Discord中可使用以下斜線命令：

### 基本功能
- `/rate` - 查詢當前匯率
- `/threshold` - 設定監控閾值
- `/status` - 查看bot狀態  
- `/chart` - 生成匯率圖表
- `/backup` - 手動創建備份
- `/list_backups` - 列出所有備份
- `/help` - 查看完整指令說明

### 系統管理功能 :new:
- `/system [detailed]` - 系統狀態檢查 (快速/詳細)
- `/health [quick]` - 健康監控檢查 (快速/全面)
- `/maintenance [operation]` - 系統維護管理 (摘要/每日/緊急)

---
**注意**: 使用 `main.py` 作為主程式，這是重新設計的模組化版本。
