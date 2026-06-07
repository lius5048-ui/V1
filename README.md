# Walmart Crawler — 新电脑部署指南

## 前置需求

| 软件 | 说明 |
|------|------|
| **Windows 10/11** | 需开启 WSL 2 |
| **Ubuntu (WSL)** | 运行环境 |

---

## 一键部署

在 Windows **管理员 PowerShell** 中运行：

```powershell
wsl --install -d Ubuntu
```

重启后进入 WSL（`wsl ~ -d Ubuntu`），逐条执行：

```bash
# 1. 下载代码
sudo apt update && sudo apt install git python3-pip -y
git clone https://github.com/lius5048-ui/V1.git ~/walmart-crawler

# 2. 创建环境
python3 -m venv ~/crewai-env
source ~/crewai-env/bin/activate
pip install flask flask-sqlalchemy openpyxl curl_cffi

# 3. 启动网站
cd ~/walmart-crawler
python app.py
```

浏览器打开 **http://localhost:5000**

---

## 使用

```bash
# 每次启动
source ~/crewai-env/bin/activate
cd ~/walmart-crawler
python app.py
```

爬取商品直接在网页内操作：输入关键词 → 搜索 → 勾选 → 导入。

---

## 注意

- 本项目**不需要 API Key**，纯离线运行。
- 首次 clone 后数据库为空，需自行搜索导入商品。
- `.env` 文件可选，不创建不影响任何功能。
