# Telegram Anime Notifier

A simple script that sends notifications for new anime episodes via Telegram webhooks.

## Prerequisites

- Python
- Telegram API token
- MyAnimeList account

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/furkan-bilgin/telegram-anime-notifier.git
   ```
2. Navigate to the project directory:
   ```sh
   cd telegram-anime-notifier
   ```
3. Install the required dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
4. Copy the `example.env` file to `.env` and modify the values as needed

## Usage

1. Run the script periodically using a scheduler or a cron job. For example, you can use the `crontab` command to schedule the script to run every minute:

   ```sh
   crontab -e
   ```

   Add the following line to the file:

   ```sh
    * * * * * /path/to/telegram-anime-notifier/venv/bin/python /path/to/telegram-anime-notifier/main.py
   ```

   Replace `/path/to/telegram-anime-notifier` with the actual path to the project directory.

- On Windows, you can use the `schtasks` command to schedule the script to run every minute.

2. The script will automatically fetch the latest anime episodes and send notifications for any new episodes.

## License

This project is licensed under the GPLv3 License. See the [LICENSE](LICENSE) file for more information.
