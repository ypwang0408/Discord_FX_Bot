# :wrench: 故障排除與維護指南

## :rotating_light: 常見問題診斷

### 問題分類快速檢查表

| 問題類型 | 快速檢查指令 | 解決方案文檔 |
|---------|-------------|-------------|
| 啟動失敗 | `./bot.sh test` | [啟動問題](#啟動問題) |
| 通知異常 | `/status` + `/permissions` | [通知問題](#通知問題) |
| API 錯誤 | `/health` | [API問題](#api問題) |
| 資料問題 | `/system detailed:True` | [資料問題](#資料問題) |
| 效能問題 | `htop` + `/system` | [效能問題](#效能問題) |
| 調度問題 :new: | `/status` + 日誌檢查 | [調度問題](#調度問題) |

## :new: 新系統特定問題

### :clock10: 精準時間調度問題
```bash
# 症狀：檢查時間不準確或任務未執行
# 1. 檢查任務狀態
/status  # 在Discord中執行，查看任務運行狀態

# 2. 檢查日誌中的調度信息
./bot.sh logs | grep -E "(下次.*檢查時間|任務.*調度)"

# 3. 檢查全域任務變數
./bot.sh logs | grep -E "(rate_check_task|health_check_task)"

# 4. 手動觸發維護重新調度
/maintenance daily  # 在Discord中執行
```

### :hospital: 健康監控問題
```bash
# 症狀：健康檢查失敗或無結果
# 1. 執行快速健康檢查
/health quick:True

# 2. 執行全面健康檢查
/health

# 3. 查看健康檢查歷史
/system detailed:True

# 4. 檢查系統管理器狀態
./bot.sh logs | grep -E "(SystemManager|健康.*檢查)"
```

## :fire: 緊急問題處理

### :rotating_light: Bot 完全無回應
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

### :zap: Discord API 限制
```bash
# 症狀：大量 429 錯誤
# 解決方案：
1. 等待限制解除 (通常1-5分鐘)
2. 檢查是否有程式碼錯誤導致過度請求
3. 如有必要，聯繫 Discord 支援
```

### :floppy_disk: 資料檔案損壞
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

## :wrench: 具體問題解決方案

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
   /status  # 在 Discord 中執行，現在顯示任務狀態 :new:

2. 檢查權限
   /permissions

3. 檢查匯率閾值邏輯
   /rules
   /rate  # 查看當前匯率

4. 檢查調度狀態 :new:
   ./bot.sh logs | grep "匯率檢查.*完成"
   
5. 檢查伺服器配置
   tail -20 bot.log | grep "threshold\|notification"
```

#### 問題: 檢查時間不準確
```bash
# 症狀：通知時間與預期不符
# 診斷:
1. 檢查調度日誌
   ./bot.sh logs | grep "下次.*檢查時間"

2. 檢查任務狀態
   /status  # 查看任務運行狀態

3. 檢查系統時間
   date
   
4. 如果時間偏移嚴重，執行維護重新調度
   /maintenance daily
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
    history = data['health_check_history']
    if isinstance(history, dict) and 'last_quick_check' in history:
        # 新格式（簡化結構）
        print(f'上次快速檢查: {history.get("last_quick_check")}')
        print(f'上次詳細檢查: {history.get("last_detailed_check")}')
        print(f'問題記錄數量: {len(history.get("problem_history", []))}')
        
        # 顯示最近的問題
        problems = history.get("problem_history", [])
        if problems:
            print("最近問題:")
            for p in problems[-3:]:  # 顯示最近3個問題
                print(f"  {p.get('timestamp')} - {p.get('status')} ({p.get('check_type')})")
    else:
        # 舊格式（已棄用）
        total_records = sum(len(records) for records in history.values())
        print(f'健康檢查記錄數量: {total_records}')
else:
    print('⚠️  健康檢查記錄不存在')
"

# 使用新的健康檢查指令診斷
/health             # 全面健康檢查
/health quick:True  # 快速健康檢查

# 檢查系統管理器狀態
./bot.sh logs | grep "系統管理器"

# 重新初始化健康檢查:
python3 -c "
from features.data_manager import ServerDataManager
dm = ServerDataManager('server_data.json')
# 健康檢查記錄會自動初始化
dm.save_data()
print('✅ 健康檢查記錄已初始化')
"
```

#### 問題: 調度任務狀態異常
```bash
# 症狀：任務顯示已停止或時間不準確
# 診斷:
1. 檢查全域任務變數狀態
   ./bot.sh logs | grep -E "(rate_check_task|health_check_task)"

2. 檢查任務取消日誌
   ./bot.sh logs | grep "任務.*取消"

3. 檢查維護日誌
   ./bot.sh logs | grep "重新調度"

# 解決方案:
1. 執行維護重新調度
   /maintenance daily

2. 重啟bot（如果維護無效）
   ./bot.sh restart
```

### 效能問題

#### 問題: 記憶體使用過高
```bash
# 診斷記憶體使用
ps aux | grep main.py | awk '{print $4, $6}'

# 使用系統監控指令
/system detailed:True
/health

# 解決方案
/maintenance daily      # 執行自動維護清理
/maintenance emergency  # 執行緊急清理
```

#### 問題: 調度效能問題
```bash
# 診斷調度精確性
./bot.sh logs | grep "下次.*檢查時間"
/status  # 查看任務狀態

# 解決方案
/maintenance daily   # 重新調度任務
/system detailed:True # 檢查系統資源
./bot.sh restart    # 如果問題持續
```

## :wrench: 預防性維護

### :calendar: 每日維護檢查清單
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

### :bar_chart: 每週維護檢查清單
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

## :lock: 安全性維護

### 安全檢查清單
```bash
# 檔案權限檢查
ls -la .env server_data.json

# Token 安全性檢查
grep -r "DISCORD_BOT_TOKEN" . --exclude-dir=venv

# 日誌敏感資訊檢查
grep -i "token\|password\|secret" bot.log | head -5

# 系統套件更新
sudo apt update && sudo apt list --upgradable
```

---

*文檔最後更新: 2025-07-27*
```

### :arrows_clockwise: 每月維護檢查清單
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

## :chart_with_upwards_trend: 監控與警報

### 系統監控腳本
```bash
# 創建監控腳本
cat > monitor.sh << 'EOF'
#!/bin/bash
LOG_FILE="monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 檢查 Bot 進程
if pgrep -f main.py > /dev/null; then
    echo "[$DATE] Bot 進程正常" >> $LOG_FILE
else
    echo "[$DATE] Bot 進程異常" >> $LOG_FILE
    ./bot.sh start
fi

# 檢查記憶體使用
MEM_USAGE=$(ps aux | grep main.py | grep -v grep | awk '{print $6}')
if [ "$MEM_USAGE" -gt 200000 ]; then
    echo "[$DATE] 記憶體使用過高: ${MEM_USAGE}KB" >> $LOG_FILE
fi

# 檢查磁碟空間
DISK_FREE=$(df / | awk 'NR==2 {print $4}')
if [ "$DISK_FREE" -lt 1000000 ]; then
    echo "[$DATE] 磁碟空間不足: ${DISK_FREE}KB" >> $LOG_FILE
fi
EOF

chmod +x monitor.sh
```

### :bar_chart: 效能基準測試
```bash
# 創建效能測試腳本
cat > benchmark.sh << 'EOF'
#!/bin/bash
echo "=== Discord FX Bot 效能測試 ==="
echo "測試時間: $(date)"

# 記憶體使用
echo "記憶體使用:"
ps aux | grep main.py | grep -v grep | awk '{print "RSS:", $6 "KB"}'

# 磁碟使用
echo "磁碟使用:"
du -sh . && df -h | grep -E "/$"

# 調度精度測試
echo "調度精度測試:"
./bot.sh logs | grep "下次.*檢查時間" | tail -3
EOF

chmod +x benchmark.sh
```

## :telephone_receiver: 技術支援

### 🆘 何時尋求幫助
- Bot 無法啟動超過 30 分鐘
- 資料檔案反覆損壞
- 記憶體或 CPU 使用異常持續超過 1 小時
- 收到 Discord API 濫用警告
- 安全性相關問題

### :clipboard: 尋求幫助時請提供
1. **錯誤描述**: 具體的錯誤現象和時間
2. **系統資訊**: `./bot.sh test` 的輸出
3. **日誌檔案**: 最近的 `bot.log` 內容
4. **環境資訊**: 作業系統、Python 版本等
5. **復現步驟**: 如何重現問題

### :email: 聯繫方式
- GitHub Issues: [專案議題追蹤](https://github.com/your-repo/issues)
- 技術文檔: 查看 `docs/` 目錄中的其他文檔
- 社群支援: Discord 伺服器或相關論壇

---

*故障排除指南版本: v2.0*  
*最後更新: 2025-07-27*  
*新增: 精準調度問題診斷、健康監控故障排除、增強版監控腳本*
