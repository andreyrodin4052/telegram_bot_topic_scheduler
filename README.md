# telegram_bot_topic_scheduler

# Steps to set up:
chmod +x topic_bot.py

sudo nano /etc/systemd/system/telegram_bot.service

# Inside :::
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/your_script_directory
ExecStart=/usr/bin/python3 /path/to/topic_bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

## Start the service manually to test it
sudo systemctl daemon-reload
sudo systemctl start telegram_bot.service
sudo systemctl status telegram_bot.service
# If all good the return will be:
elegram_bot.service - Telegram Bot Service
     Loaded: loaded (/etc/systemd/system/telegram_bot.service; enabled; vendor preset: enabled)
     Active: active (running) since ...

# Enable the service to start automatically on boot:
sudo systemctl enable telegram_bot.service
