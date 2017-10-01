# Bot to fill quinielas

Dependencies:
```bash
pip install python-telegram-bot --upgrade
pip install requests
pip install lxml
pip install beautifulsoup4
```

Under development. Launch it using:
```bash
cp status_orig.json status.json; nohup python quiniela_bot.py > /tmp/quiniela.log 2>&1 &
```
