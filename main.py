import html
import json
import logging
import re
from datetime import datetime
from os import environ
from os.path import isfile

import anitopy
import Levenshtein
import requests
from dotenv import load_dotenv

# Set up logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)


# Set up envs
load_dotenv()

MAL_TARGET = "https://myanimelist.net/animelist/" + environ["MAL_TARGET_USER"]
REFRESH_MAL_ANIME_DATA_EVERY_MINUTES = 15

NYAA_URL = "https://nyaa.si/?c=1_2"
NYAA_REWRITE = environ["NYAA_REWRITE"].split(",")

TELEGRAM_API_TOKEN = environ["TELEGRAM_API_TOKEN"]
TELEGRAM_CHAT_ID = environ["TELEGRAM_CHAT_ID"]

DATA_JSON_PATH = "./data.json"


def get_mal_data():
    MAL_REGEX = r'data-items="(.+?)" data-broadcast'
    return json.loads(
        html.unescape(re.findall(MAL_REGEX, requests.get(MAL_TARGET).text)[0])
    )


def get_mal_watching_anime():
    return [x for x in get_mal_data() if x["status"] == 1]


def _anitopy_try_parse(text):
    try:
        return anitopy.parse(text)
    except Exception:
        return None


def get_nyaa_anime():
    NYAA_REGEX = r'title="\[(.+)"'
    res = [
        _anitopy_try_parse("[" + x)
        for x in re.findall(NYAA_REGEX, requests.get(NYAA_URL).text)
    ]
    return [x for x in res if x is not None]


def load_data():
    if not isfile(DATA_JSON_PATH):
        save_data({})

    with open(DATA_JSON_PATH, "r") as f:
        return json.loads(f.read())


def send_telegram_text(anime, mal_anime):
    now = datetime.now().strftime("%A, %d/%m/%Y %H:%M")
    episode_name = mal_anime["anime_title_eng"]
    episode_name = mal_anime["anime_title"] if not episode_name else episode_name
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"[{now}] Episode {int(anime['episode_number'])} has been aired for '{episode_name}'!",
        },
    ).raise_for_status()


def save_data(data):
    with open(DATA_JSON_PATH, "w") as f:
        f.write(json.dumps(data, indent=2))


def test_anime_title_match(title1, title2):
    def _format_title(title):
        return re.sub("[^a-zA-Z0-9]", "", str(title)).lower()

    title1, title2 = _format_title(title1), _format_title(title2)

    return Levenshtein.distance(title1, title2) <= 1


def main():
    data = load_data()
    if (
        "mal_anime_cache" not in data
        or datetime.now().minute % REFRESH_MAL_ANIME_DATA_EVERY_MINUTES == 0
    ):
        try:
            data["mal_anime_cache"] = get_mal_watching_anime()
        except Exception as e:
            if "mal_anime_cache" not in data:
                logging.error("Could not get MAL data.", exc_info=True)
                return
            else:
                logging.warning(
                    "Could not get MAL data, MAL might be in maintenance.",
                    exc_info=True,
                )

    mal_anime = data["mal_anime_cache"]

    logging.info("Getting anime listings from Nyaa")
    newest_anime = get_nyaa_anime()
    sent_notification_count = 0
    for anime in newest_anime:
        for rewrite in NYAA_REWRITE:
            if rewrite not in anime["file_name"]:
                continue
            anime["anime_title"], anime["anime_title_eng"] = rewrite, rewrite

        mal_matching_anime = next(
            (
                x
                for x in mal_anime
                if (
                    test_anime_title_match(x["anime_title"], anime["anime_title"])
                    or test_anime_title_match(
                        x["anime_title_eng"], anime["anime_title"]
                    )
                )
            ),
            None,
        )
        if mal_matching_anime is None or (
            mal_matching_anime["anime_end_date_string"] is not None
            and (
                datetime.now()
                - datetime.strptime(
                    mal_matching_anime["anime_end_date_string"], "%m-%d-%y"
                )
            ).days
            > 7
        ):
            continue

        mal_title = mal_matching_anime["anime_title"]
        if "episode_number" not in anime:
            continue
        anime_episode_number = int(anime["episode_number"])

        if "anime_episodes" not in data:
            data["anime_episodes"] = {}
        if mal_title not in data["anime_episodes"]:
            data["anime_episodes"][mal_title] = -1

        if data["anime_episodes"][mal_title] < anime_episode_number:
            data["anime_episodes"][mal_title] = anime_episode_number
            try:
                send_telegram_text(anime, mal_matching_anime)
                logging.info(f"Sent anime notification for '{anime['anime_title']}'")
                sent_notification_count += 1
            except Exception:
                logging.error(
                    f"Failed to notify Telegram for '{anime['anime_title']}'",
                    exc_info=True,
                )
    save_data(data)
    if sent_notification_count > 0:
        logging.info(f"Done, sent {sent_notification_count} notifications!")
    else:
        logging.info("Done, sent no notifications!")


main()
