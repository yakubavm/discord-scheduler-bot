# Discord Message Scheduler Bot

A powerful and flexible Discord bot designed to schedule and manage message queues for your server.  
Plan messages with customizable intervals, attach files, and maintain persistence with seamless data storage.  
Perfect for server announcements, reminders, or automated content posting.

---

## ✨ Features

- **Asynchronous Operation**: Efficiently handles tasks without blocking, optimized for performance.  
- **Data Persistence**: Saves queue and settings to JSON files, ensuring continuity after restarts.  
- **File Attachments**: Supports up to 10 attachments (images, documents, etc.) per message.  
- **Flexible Management**: Comprehensive slash commands for channel setup, interval configuration, and queue management.  
- **Interactive UI**: Utilizes slash commands, confirmation buttons, and context menus for intuitive interaction.  
- **Import/Export**: Easily back up or restore your queue with JSON file support.  
- **Detailed Logging**: Monitor bot activity and troubleshoot with detailed logs in `scheduler_bot.log`.  

---

## 🚀 Getting Started

### Prerequisites
- Python **3.11+** installed  
- A Discord account and server  
- A bot token from the **[Discord Developer Portal](https://discord.com/developers/applications)**  

### Installation

**Clone the Repository**
```bash
git clone https://github.com/yakubavm/discord-scheduler-bot.git
cd discord-scheduler-bot
````

**Set Up a Virtual Environment (recommended)**

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

**Install Dependencies**

Using `requirements.txt`:

```bash
pip install -r requirements.txt
```

Or, if using `pyproject.toml`:

```bash
pip install .
```

**Configure the Bot**

Create a `.env` file in the project directory:

```env
DISCORD_BOT_TOKEN="YOUR_COPIED_TOKEN_HERE"
```

---

### Discord Developer Portal Setup

1. Visit the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new application and navigate to the **Bot** tab.
3. Click **Reset Token** to generate a token and copy it into your `.env` file.
4. Enable **Privileged Gateway Intents** → `MESSAGE CONTENT INTENT`.
5. In **OAuth2 > URL Generator** select:

   * **Scopes**: `bot`, `applications.commands`
   * **Bot Permissions**: Send Messages, Attach Files, Read Message History, Use Application Commands, Administrator (recommended)
6. Use the generated URL to invite the bot to your server.

---

### Running the Bot

**Windows**

```bash
python discord_scheduler_bot.py
```

**Linux/macOS**

```bash
python3 discord_scheduler_bot.py
```

**Continuous Operation (Server/VDS)**

Using `screen`:

```bash
screen -S discord_bot
python3 discord_scheduler_bot.py
# Press Ctrl+A, then D to detach
# Reattach with: screen -r discord_bot
```

Using `nohup`:

```bash
nohup python3 discord_scheduler_bot.py &
```

**NAS (Synology/QNAP)**

1. Install Python 3 via your NAS package center.
2. Upload `discord_scheduler_bot.py` and the `bot_data` folder.
3. In Task Scheduler, create a new task with:

```bash
/usr/bin/python3 /volume1/path/to/your/script/discord_scheduler_bot.py
```

---

## 📜 Commands

The bot uses **slash commands** for seamless interaction:

| Command                                                 | Description                                                       | Arguments                                             |
| ------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------- |
| `/set_channel [channel]`                                | Set the text channel for scheduled messages.                      | `channel`: The target text channel                    |
| `/add_message [content] [attachment1 ... attachment10]` | Add a message with optional files to the queue.                   | `content`: Message text, `attachment`: Up to 10 files |
| **Add to Queue (Context Menu)**                         | Right-click a message → Apps → Add to Queue.                      | None                                                  |
| `/set_interval [minutes]`                               | Set the interval (in minutes) between messages (min 1).           | `minutes`: Interval in minutes                        |
| `/view_queue`                                           | Display queue status, including message count and next post time. | None                                                  |
| `/delete_message [message_id]`                          | Remove a specific message from the queue.                         | `message_id`: ID from `/view_queue`                   |
| `/clear_queue`                                          | Clear the entire queue (requires confirmation).                   | None                                                  |
| `/pause`                                                | Pause message publishing.                                         | None                                                  |
| `/resume`                                               | Resume message publishing.                                        | None                                                  |
| `/status`                                               | View current settings (channel, interval, queue size, status).    | None                                                  |
| `/export_queue`                                         | Save the queue and settings to `queue_backup.json`.               | None                                                  |
| `/import_queue [file]`                                  | Import a queue from a `.json` file.                               | `file`: Exported `.json` file                         |

---

## 📂 Project Structure

```
discord-scheduler-bot/
├── .env                        # Bot token configuration
├── .gitignore                  # Git ignore file
├── discord_scheduler_bot.py    # Main bot script
├── LICENSE                     # MIT License
├── pyproject.toml              # Project configuration
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── uv.lock                     # Lock file for dependency versions
```

---

## 💡 Tips

* **Secure your `.env` file**: Never share your bot token or commit `.env` to GitHub.
* **Check bot status**: Use `/status` to verify settings.
* **Backup regularly**: Export your queue with `/export_queue` to avoid data loss.
* **Monitor logs**: Check `scheduler_bot.log` in the `bot_data` folder for troubleshooting.
* **Dependencies**: Use `uv.lock` for reproducible builds or `requirements.txt` for simplicity.

---

## 📬 Contact

For questions, suggestions, or support, reach out:

* **Email**: [yakubavm@gmail.com](mailto:yakubavm@gmail.com) | [yakubavm@outlook.com](mailto:yakubavm@outlook.com)
* **Telegram**: [t.me/yakubavm](https://t.me/yakubavm)
* **Discord**: yakubavm

---

## 📝 License

This project is licensed under the **MIT License**.
See the [LICENSE](./LICENSE) file for details.

---

## 🙌 Contributing

Contributions are welcome!
Feel free to **open issues** or **submit pull requests** on GitHub.
