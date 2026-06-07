# 启动网站
cd ~/walmart-crawler
source ~/crewai-env/bin/activate
python app.py
# → 浏览器打开 http://localhost:5000

# 爬取新商品后导入
python main.py "商品关键词"     # 爬取
python import_data.py           # 导入到网站

# 新数据刷新网页即可看到
