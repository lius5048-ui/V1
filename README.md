# Walmart Crawler — 新电脑部署指南

## 前置需求

| 软件 | 说明 |
|------|------|
| **Windows 10/11** | 需开启 WSL 2 |
| **Ubuntu (WSL)** | 运行环境 |
| **Python 3.12+** | 项目依赖 |

---

## 第一步：安装 WSL + Ubuntu

在 Windows **管理员 PowerShell** 中运行：

```powershell
wsl --install -d Ubuntu
```

重启电脑。完成后设置 Ubuntu 用户名密码。

---

## 第二步：克隆项目

```bash
# 进入 WSL
wsl ~ -d Ubuntu

# 安装 git（如果没有）
sudo apt update && sudo apt install git -y

# 克隆仓库
git clone https://github.com/lius5048-ui/V1.git ~/walmart-crawler
cd ~/walmart-crawler
```

---

## 第三步：创建 Python 虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv ~/crewai-env

# 激活并安装依赖
source ~/crewai-env/bin/activate

# 安装项目依赖
pip install flask flask-sqlalchemy openpyxl curl_cffi python-dotenv openai
```

---

## 第四步：配置 API Key

```bash
# 创建 .env 文件
nano ~/walmart-crawler/.env
```

粘贴以下内容：
```
DEEPSEEK_API_KEY=sk-b31e0bcc330d4adaa7b1775880f2a075
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

按 `Ctrl+X` → `Y` → `Enter` 保存。

> 如果要用你自己的 API Key，把 `sk-...` 替换掉即可。

---

## 第五步：启动网站

```bash
# 激活环境 + 启动
source ~/crewai-env/bin/activate
cd ~/walmart-crawler
python app.py
```

浏览器打开 http://localhost:5000

---

## 使用命令速查

```bash
# 启动网站
source ~/crewai-env/bin/activate
cd ~/walmart-crawler
python app.py
```

```bash
# 爬取新商品（网站运行中也可执行）
source ~/crewai-env/bin/activate
cd ~/walmart-crawler
python main.py "商品关键词"
python import_data.py
```

---

## 完整一键脚本

首次部署时，把这些命令逐条复制执行即可：

```bash
# 1. 进入 WSL
wsl ~ -d Ubuntu

# 2. 安装工具
sudo apt update && sudo apt install git python3-pip -y

# 3. 下载代码
git clone https://github.com/lius5048-ui/V1.git ~/walmart-crawler

# 4. 创建环境
python3 -m venv ~/crewai-env
source ~/crewai-env/bin/activate
pip install flask flask-sqlalchemy openpyxl curl_cffi python-dotenv openai

# 5. 写入 API Key
echo "DEEPSEEK_API_KEY=sk-b31e0bcc330d4adaa7b1775880f2a075" > ~/walmart-crawler/.env
echo "DEEPSEEK_BASE_URL=https://api.deepseek.com/v1" >> ~/walmart-crawler/.env

# 6. 启动
cd ~/walmart-crawler
python app.py
```

---

## 常见问题

**网站启动后 Windows 浏览器打不开？**
- WSL 默认在 `localhost:5000` 监听，直接访问即可
- 如果端口冲突，修改 `app.py` 最后的 `port=5000` 为其他端口

**爬虫返回空结果？**
- Walmart 可能对爬取做了限制，等待几秒重试
- 也可以直接使用商品 ID 爬取，在主站搜索框输入数字 ID

**数据库没有数据？**
- 新 clone 的仓库没有数据缓存，用关键词搜索后导入即可
