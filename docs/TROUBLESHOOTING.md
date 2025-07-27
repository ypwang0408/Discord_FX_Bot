# 🔧 故障排除與維護指南

## 🚨 常見問題診斷

### 問題分類快速檢查表

| 問題類型 | 快速檢查指令 | 解決方案文檔 |
|---------|-------------|-------------|
| 啟動失敗 | `./bot.sh test` | [啟動問題](#啟動問題) |
| 通知異常 | `/status` + `/permissions` | [通知問題](#通知問題) |
| API 錯誤 | `/health` | [API問題](#api問題) |
| 資料問題 | `/system detailed:True` | [資料問題](#資料問題) |
| 效能問題 | `htop` + `/system` | [效能問題](#效能問題) |

## 🔥 緊急問題處理

### 🚨 Bot 完全無回應
```bash
# 1. 檢查進程狀態
ps aux | grep main.py

# 2. 檢查 tmux 會話
tmux list-sessions

# 3. 檢查系統日誌
tail -20 bot.log

# 4. 強制重啟
./bot.sh stop
sleep 5
./bot.sh start

# 5. 如果仍無效，強制清理
pkill -f main.py
tmux kill-session -t discord-bot
./bot.sh start
```

### ⚡ Discord API 限制
```bash
# 症狀：大量 429 錯誤
# 解決方案：
1. 等待限制解除 (通常1-5分鐘)
2. 檢查是否有程式碼錯誤導致過度請求
3. 如有必要，聯繫 Discord 支援
```

### 💾 資料檔案損壞
```bash
# 1. 檢查檔案完整性
python3 -c "
import json
try:
    with open('server_data.json', 'r') as f:
        data = json.load(f)
    print('✅ 資料檔案正常')
except Exception as e:
    print('❌ 資料檔案損壞:', e)
"

# 2. 從備份恢復
ls -la backups/
cp backups/20250727.json server_data.json

# 3. 重新初始化 (最後手段)
cp server_data.json server_data_broken.json
echo '{}' > server_data.json
./bot.sh restart
```

## 🔧 具體問題解決方案

### 啟動問題

#### 問題: 虛擬環境錯誤
```bash
# 錯誤訊息: "No module named 'discord'"
# 解決方案:
source venv/bin/activate
pip install -r requirements.txt

# 如果虛擬環境損壞，重建：
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 問題: Discord Token 無效
```bash
# 錯誤訊息: "Improper token has been passed"
# 解決方案:
1. 檢查 .env 檔案格式
cat .env
# 應該是: DISCORD_BOT_TOKEN=your_actual_token

2. 確認 Token 有效性
# 前往 Discord Developer Portal 重新生成 Token

3. 確認沒有額外字符
sed -i 's/[[:space:]]*$//' .env  # 移除結尾空格
```

#### 問題: 模組導入錯誤
```bash
# 錯誤訊息: "ModuleNotFoundError: No module named 'features'"
# 解決方案:
1. 檢查檔案結構
ls -la features/
ls -la features/__init__.py

2. 檢查 Python 路徑
python3 -c "import sys; print(sys.path)"

3. 確認在正確目錄
pwd  # 應該在 Discord_FX_Bot 根目錄
```

### 通知問題

#### 問題: 通知未發送
```bash
# 診斷步驟:
1. 檢查基本設定
   /status  # 在 Discord 中執行

2. 檢查權限
   /permissions

3. 檢查匯率閾值邏輯
   /rules
   /rate  # 查看當前匯率

4. 檢查伺服器配置
   tail -20 bot.log | grep "threshold\|notification"
```

#### 問題: @everyone 通知無效
```bash
# 解決方案:
1. 確認 Bot 有 Mention Everyone 權限
2. 使用 /mention 指令啟用功能
3. 確認 Discord 伺服器設定允許 @everyone

# 測試權限:
/permissions  # 檢查權限狀態
```

#### 問題: 通知頻道設定錯誤
```bash
# 診斷:
python3 -c "
import json
with open('server_data.json', 'r') as f:
    data = json.load(f)
for guild_id, config in data.items():
    if isinstance(config, dict) and 'channel_id' in config:
        print(f'伺服器 {guild_id}: 頻道 {config[\"channel_id\"]}')
"

# 解決: 在正確頻道重新執行 /channel
```

### API問題

#### 問題: 匯率獲取失敗
```bash
# 診斷網路連線:
curl -I https://www.esunbank.com.tw/bank/personal/deposit/rate/foreign-exchange-rates

# 檢查 API 狀態:
/health quick:False

# 查看詳細錯誤:
grep -i "api\|rate\|esun" bot.log | tail -10
```

#### 問題: API 回應格式變更
```bash
# 症狀: 程式運行但匯率為 None
# 解決方案:
1. 檢查玉山銀行網站是否改版
2. 更新 exchange_rate_monitor.py 中的解析邏輯
3. 聯繫開發者更新程式碼

# 臨時解決方案: 使用備用 API
# 在程式碼中可能已自動切換
```

### 資料問題

#### 問題: 匯率歷史資料遺失
```bash
# 檢查資料檔案:
python3 -c "
import json
with open('server_data.json', 'r') as f:
    data = json.load(f)
if 'rate_history' in data:
    total_records = sum(len(records) for records in data['rate_history'].values())
    print(f'匯率記錄數量: {total_records}')
else:
    print('⚠️  匯率歷史資料遺失')
"

# 從備份恢復:
./list_backups
# 選擇適當的備份檔案恢復
```

#### 問題: 健康檢查記錄異常
```bash
# 檢查健康檢查資料:
python3 -c "
import json
with open('server_data.json', 'r') as f:
    data = json.load(f)
if 'health_check_history' in data:
    total_records = sum(len(records) for records in data['health_check_history'].values())
    print(f'健康檢查記錄數量: {total_records}')
else:
    print('⚠️  健康檢查記錄不存在')
"

# 重新初始化健康檢查:
python3 -c "
from features.data_manager import ServerDataManager
dm = ServerDataManager('server_data.json')
# 健康檢查記錄會自動初始化
dm.save_data()
print('✅ 健康檢查記錄已初始化')
"
```

### 效能問題

#### 問題: 記憶體使用過高
```bash
# 診斷記憶體使用:
ps aux | grep main.py | awk '{print $4, $6}' # RSS 記憶體

# 檢查是否有記憶體洩漏:
/system detailed:True  # 查看記憶體使用趨勢

# 解決方案:
1. 重啟 Bot: ./bot.sh restart
2. 檢查日誌檔案大小: ls -lh bot.log
3. 清理日誌: ./maintenance operation:daily
```

#### 問題: CPU 使用率過高
```bash
# 診斷 CPU 使用:
top -p $(pgrep -f main.py)

# 可能原因:
1. API 請求過於頻繁
2. 圖表生成過程中的 CPU 密集操作
3. 日誌寫入過多

# 解決方案:
1. 檢查 API 調用頻率設定
2. 暫時停用圖表功能測試
3. 調整日誌等級
```

#### 問題: 磁碟空間不足
```bash
# 檢查磁碟使用:
df -h
du -sh Discord_FX_Bot/

# 清理空間:
1. 清理舊日誌: ./maintenance operation:emergency
2. 清理舊備份: find backups/ -name "*.json" -mtime +30 -delete
3. 清理 Python 快取: find . -name "__pycache__" -type d -exec rm -rf {} +
```

## 🛠️ 預防性維護

### 📅 每日維護檢查清單
```bash
# 1. 系統狀態檢查
./bot.sh status

# 2. 健康檢查
/system  # 在 Discord 中執行

# 3. 日誌檢查 (查看是否有異常)
tail -50 bot.log | grep -E "(ERROR|WARNING|❌)"

# 4. 備份驗證
ls -la backups/ | tail -5

# 5. 資源使用檢查
df -h | grep -E "(/$|home)"
ps aux | grep main.py
```

### 📊 每週維護檢查清單
```bash
# 1. 執行系統維護
/maintenance operation:daily

# 2. 檢查系統效能趨勢
/health quick:False

# 3. 備份清理
find backups/ -name "*.json" -mtime +7 | wc -l

# 4. 更新檢查
git status
git log --oneline -5

# 5. 安全性檢查
ls -la .env server_data.json
```

### 🔄 每月維護檢查清單
```bash
# 1. 完整系統備份
tar -czf ../discord_bot_full_backup_$(date +%Y%m%d).tar.gz . --exclude=venv

# 2. 依賴套件更新檢查
pip list --outdated

# 3. 系統日誌輪轉
mv bot.log bot_$(date +%Y%m%d).log
touch bot.log

# 4. 效能分析報告
/system detailed:True

# 5. 文檔更新檢查
ls -la docs/*.md
```

## 📈 監控與警報

### 🔍 重要指標監控
```bash
# 創建監控腳本
cat > monitor.sh << 'EOF'
#!/bin/bash
LOG_FILE="monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 檢查 Bot 進程
if pgrep -f main.py > /dev/null; then
    echo "[$DATE] ✅ Bot 進程正常" >> $LOG_FILE
else
    echo "[$DATE] ❌ Bot 進程異常" >> $LOG_FILE
    ./bot.sh start
fi

# 檢查記憶體使用 (超過 200MB 警報)
MEM_USAGE=$(ps aux | grep main.py | grep -v grep | awk '{print $6}')
if [ "$MEM_USAGE" -gt 200000 ]; then
    echo "[$DATE] ⚠️  記憶體使用過高: ${MEM_USAGE}KB" >> $LOG_FILE
fi

# 檢查磁碟空間 (少於 1GB 警報)
DISK_FREE=$(df / | awk 'NR==2 {print $4}')
if [ "$DISK_FREE" -lt 1000000 ]; then
    echo "[$DATE] ⚠️  磁碟空間不足: ${DISK_FREE}KB" >> $LOG_FILE
fi
EOF

chmod +x monitor.sh

# 設定每5分鐘執行一次
# crontab -e
# */5 * * * * /path/to/Discord_FX_Bot/monitor.sh
```

### 📊 效能基準測試
```bash
# 創建效能測試腳本
cat > benchmark.sh << 'EOF'
#!/bin/bash
echo "=== Discord FX Bot 效能測試 ==="
echo "測試時間: $(date)"
echo

# 記憶體使用
echo "📊 記憶體使用:"
ps aux | grep main.py | grep -v grep | awk '{print "RSS:", $6 "KB", "VSZ:", $5 "KB"}'

# CPU 使用 (5秒平均)
echo "🖥️  CPU 使用 (5秒平均):"
top -b -n 1 -p $(pgrep -f main.py) | tail -1 | awk '{print "CPU:", $9 "%"}'

# 磁碟使用
echo "💽 磁碟使用:"
du -sh . | awk '{print "Bot 目錄:", $1}'
df -h / | tail -1 | awk '{print "根目錄可用:", $4}'

# API 回應時間測試
echo "🌐 API 回應時間:"
time curl -s -o /dev/null -w "%{time_total}s\n" \
  "https://www.esunbank.com.tw/bank/personal/deposit/rate/foreign-exchange-rates"

echo "=== 測試完成 ==="
EOF

chmod +x benchmark.sh
```

## 🔒 安全性維護

### 🛡️ 安全檢查清單
```bash
# 1. 檔案權限檢查
ls -la .env server_data.json
# .env 應該是 600, server_data.json 應該是 600 或 644

# 2. Token 安全性檢查
grep -r "DISCORD_BOT_TOKEN" . --exclude-dir=venv 2>/dev/null | grep -v ".env:"
# 不應該有除了 .env 之外的文件包含 Token

# 3. 網路連接檢查
netstat -tulpn | grep python

# 4. 日誌敏感資訊檢查
grep -i "token\|password\|secret" bot.log | head -5
# 不應該記錄敏感資訊

# 5. 更新系統套件
sudo apt update && sudo apt list --upgradable
```

## 📞 技術支援

### 🆘 何時尋求幫助
- Bot 無法啟動超過 30 分鐘
- 資料檔案反覆損壞
- 記憶體或 CPU 使用異常持續超過 1 小時
- 收到 Discord API 濫用警告
- 安全性相關問題

### 📋 尋求幫助時請提供
1. **錯誤描述**: 具體的錯誤現象和時間
2. **系統資訊**: `./bot.sh test` 的輸出
3. **日誌檔案**: 最近的 `bot.log` 內容
4. **環境資訊**: 作業系統、Python 版本等
5. **復現步驟**: 如何重現問題

### 📧 聯繫方式
- GitHub Issues: [專案議題追蹤](https://github.com/your-repo/issues)
- 技術文檔: 查看 `docs/` 目錄中的其他文檔
- 社群支援: Discord 伺服器或相關論壇

---

*故障排除指南最後更新: 2025-07-27*
