# 🚀 安裝與部署指南

## 📋 系統需求

### 硬體需求
- **CPU**: 1核心以上 (推薦 2核心)
- **記憶體**: 最少 512MB (推薦 1GB)
- **硬碟**: 200MB 可用空間
- **網路**: 穩定的網際網路連接

### 軟體需求
- **作業系統**: Linux (Ubuntu 18.04+, CentOS 7+) 或 macOS
- **Python**: 3.8+ (推薦 3.9+)
- **Git**: 用於程式碼管理
- **tmux**: 用於後台執行 (可選但推薦)

## 🔧 環境準備

### 1. 更新系統套件
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git tmux

# CentOS/RHEL
sudo yum update -y
sudo yum install -y python3 python3-pip git tmux

# macOS (使用 Homebrew)
brew update
brew install python git tmux
```

### 2. 創建專用使用者 (推薦)
```bash
# 創建 discord-bot 使用者
sudo useradd -m -s /bin/bash discord-bot

# 切換到該使用者
sudo su - discord-bot
```

## 📦 安裝步驟

### 1. 下載程式碼
```bash
# Clone 專案 (替換為實際的 repo URL)
git clone https://github.com/your-username/Discord_FX_Bot.git
cd Discord_FX_Bot

# 檢查檔案結構
ls -la
```

### 2. 建立虛擬環境
```bash
# 創建虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 升級 pip
pip install --upgrade pip
```

### 3. 安裝依賴套件
```bash
# 安裝必要套件
pip install -r requirements.txt

# 驗證安裝
pip list | grep discord
```

### 4. 配置環境變數
```bash
# 創建 .env 檔案
cp .env.example .env  # 如果有範例檔案
# 或直接創建
cat > .env << EOF
DISCORD_BOT_TOKEN=your_bot_token_here
EOF

# 設定檔案權限 (安全性)
chmod 600 .env
```

## 🤖 Discord Bot 設定

### 1. 創建 Discord Application
1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 點擊「New Application」
3. 輸入應用程式名稱，如「FX Rate Monitor」
4. 點擊「Create」

### 2. 創建 Bot
1. 在左側選單點擊「Bot」
2. 點擊「Add Bot」
3. 確認創建
4. 複製「Token」並貼到 `.env` 檔案中

### 3. 設定 Bot 權限
在「Bot」頁面中設定：
- ✅ **Public Bot**: 關閉 (更安全)
- ✅ **Requires OAuth2 Code Grant**: 關閉
- ✅ **Presence Intent**: 開啟
- ✅ **Server Members Intent**: 開啟 (如果需要)
- ✅ **Message Content Intent**: 開啟

### 4. 生成邀請連結
1. 點擊左側「OAuth2」→「URL Generator」
2. 在「Scopes」中選擇：
   - ✅ `bot`
   - ✅ `applications.commands`
3. 在「Bot Permissions」中選擇：
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Mention Everyone (可選)
4. 複製生成的 URL 並邀請 Bot 到伺服器

## 🔧 初始測試

### 1. 測試模組完整性
```bash
# 測試所有模組
./bot.sh test

# 預期輸出應該包含：
# ✅ 主程式 main.py 存在
# ✅ features 目錄結構正確
# ✅ 所有模組可正常導入
# ✅ 虛擬環境配置正確
```

### 2. 測試環境變數
```bash
# 檢查 .env 檔案
cat .env | grep -v '^#'

# 測試 Python 能否讀取
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('DISCORD_BOT_TOKEN', 'NOT_FOUND')
print('Token 狀態:', 'OK' if token != 'NOT_FOUND' and len(token) > 50 else 'ERROR')
"
```

### 3. 測試網路連線
```bash
# 測試玉山銀行 API
python3 -c "
import asyncio
import aiohttp

async def test_api():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://www.esunbank.com.tw/bank/personal/deposit/rate/foreign-exchange-rates') as response:
                print('玉山銀行 API:', 'OK' if response.status == 200 else f'ERROR {response.status}')
        except Exception as e:
            print('玉山銀行 API: ERROR -', str(e))

asyncio.run(test_api())
"
```

## 🚀 啟動服務

### 1. 首次啟動
```bash
# 使用統一管理腳本啟動
./bot.sh start

# 預期輸出：
# 🚀 啟動 Discord 機器人...
# ✅ 環境檢查通過
# ✅ 在 tmux 會話 'discord-bot' 中啟動機器人
# 📋 使用 './bot.sh status' 檢查狀態
# 📋 使用 './bot.sh logs' 查看即時日誌
```

### 2. 驗證運行狀態
```bash
# 檢查狀態
./bot.sh status

# 查看即時日誌
./bot.sh logs

# 或查看歷史日誌
tail -f bot.log
```

### 3. 在 Discord 中測試
在邀請 Bot 的 Discord 伺服器中：
```
/rate    # 測試基本功能
/help    # 查看所有指令
/status  # 檢查 Bot 狀態
```

## 🔄 系統服務化 (可選)

### 1. 創建 systemd 服務檔案
```bash
sudo tee /etc/systemd/system/discord-fx-bot.service > /dev/null << EOF
[Unit]
Description=Discord FX Rate Monitor Bot
After=network.target

[Service]
Type=simple
User=discord-bot
WorkingDirectory=/home/discord-bot/Discord_FX_Bot
Environment=PATH=/home/discord-bot/Discord_FX_Bot/venv/bin
ExecStart=/home/discord-bot/Discord_FX_Bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 2. 啟用並啟動服務
```bash
# 重載 systemd 配置
sudo systemctl daemon-reload

# 啟用服務 (開機自動啟動)
sudo systemctl enable discord-fx-bot

# 啟動服務
sudo systemctl start discord-fx-bot

# 檢查狀態
sudo systemctl status discord-fx-bot
```

### 3. 服務管理指令
```bash
# 查看服務狀態
sudo systemctl status discord-fx-bot

# 查看服務日誌
sudo journalctl -u discord-fx-bot -f

# 重啟服務
sudo systemctl restart discord-fx-bot

# 停止服務
sudo systemctl stop discord-fx-bot

# 停用服務
sudo systemctl disable discord-fx-bot
```

## 🛡️ 安全性設定

### 1. 檔案權限
```bash
# 設定適當的檔案權限
chmod 600 .env                    # 環境變數檔案
chmod 644 server_data.json        # 數據檔案 (可讀寫)
chmod +x bot.sh                   # 管理腳本可執行
chmod +x scripts/*.sh             # 所有腳本可執行
```

### 2. 防火牆設定 (如果需要)
```bash
# Ubuntu UFW
sudo ufw allow ssh
sudo ufw enable

# CentOS firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 3. 定期備份設定
```bash
# 創建備份腳本
cat > backup_bot.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/discord-bot/backups/system"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)

# 備份重要檔案
tar -czf "$BACKUP_DIR/bot_backup_$DATE.tar.gz" \
    .env server_data.json bot.log \
    --exclude='venv' --exclude='__pycache__'

# 清理超過 30 天的備份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "備份完成: bot_backup_$DATE.tar.gz"
EOF

# 設定執行權限
chmod +x backup_bot.sh

# 設定 crontab (每日備份)
crontab -e
# 添加以下行：
# 0 2 * * * /home/discord-bot/Discord_FX_Bot/backup_bot.sh
```

## 🔍 故障排除

### 常見問題 1: Python 版本問題
```bash
# 檢查 Python 版本
python3 --version

# 如果版本太舊，更新 Python
# Ubuntu
sudo apt install python3.9 python3.9-venv python3.9-pip
python3.9 -m venv venv

# 或使用 pyenv
curl https://pyenv.run | bash
pyenv install 3.9.16
pyenv local 3.9.16
```

### 常見問題 2: 套件安裝失敗
```bash
# 清理快取重新安裝
pip cache purge
pip install --no-cache-dir -r requirements.txt

# 或使用指定索引
pip install -i https://pypi.org/simple/ -r requirements.txt
```

### 常見問題 3: 權限問題
```bash
# 檢查檔案所有者
ls -la

# 修正所有者
sudo chown -R $(whoami):$(whoami) .

# 修正權限
find . -type f -name "*.py" -exec chmod 644 {} \;
find . -type f -name "*.sh" -exec chmod +x {} \;
```

### 常見問題 4: Discord Token 無效
1. 確認 Token 正確複製 (不包含額外空格)
2. 檢查 Bot 是否被重置或刪除
3. 確認 .env 檔案格式正確
4. 重新生成 Token

## 📊 效能監控

### 1. 系統資源監控
```bash
# 檢查 CPU 和記憶體使用
htop
# 或
ps aux | grep python

# 檢查磁碟使用
df -h
du -sh Discord_FX_Bot/
```

### 2. 應用程式監控
```bash
# 使用內建指令
./bot.sh status

# 或在 Discord 中
/system detailed:True
/health quick:False
```

### 3. 日誌分析
```bash
# 分析錯誤日誌
grep -i error bot.log | tail -20

# 分析 API 調用
grep -i "api" bot.log | tail -20

# 統計成功率
grep "✅" bot.log | wc -l
grep "❌" bot.log | wc -l
```

---

*安裝指南最後更新: 2025-07-27*
