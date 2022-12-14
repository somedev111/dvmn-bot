import requests
import os
import textwrap
import logging
from time import sleep
from dotenv import load_dotenv

import telegram


logger = logging.getLogger('bot')


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def start_bot(tg_bot, chat_id, dvmn_token):

    logger.warning('Бот запущен.')

    headers = {"Authorization": dvmn_token}

    url = "https://dvmn.org/api/long_polling/"
    while True:
        try:
            payload = {}
            response = requests.get(url, headers=headers, params=payload)

            reviews = response.json()

            status = reviews.get('status')

            if status == 'timeout':
                timestamp_to_request = reviews.get('timestamp_to_request')
                payload['timestamp'] = timestamp_to_request

            if status == 'found':
                last_attempt_timestamp = reviews.get('last_attempt_timestamp')
                payload['timestamp'] = last_attempt_timestamp

                new_attempts = reviews.get('new_attempts')
                if new_attempts:
                    msg_text = "Проверенные работы:\n\n"

                    for attempt in new_attempts:
                        result = "Урок пройден!"
                        if attempt.get('is_negative'):
                            result = f"Есть доработки"

                        msg_text += f"""\
                        Урок: {attempt.get('lesson_title')}
                        Результат проверки: {result}
                        Ссылка на урок: {attempt.get('lesson_url')}
                        """
                        msg_text += "\n\n"

                    tg_bot.send_message(text=textwrap.dedent(msg_text), chat_id=chat_id)

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            logger.critical('ConnectionError')
            sleep(7200)
            continue
        except Exception as err:
            logger.warning('Бот упал с ошибкой:')
            logger.exception(err)
            break


if __name__ == '__main__':
    load_dotenv()

    tg_token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    dvmn_token = os.getenv("DVMN_TOKEN")

    tg_bot = telegram.Bot(tg_token)

    tg_logs_handler = TelegramLogsHandler(tg_bot, chat_id)
    tg_logs_handler.setLevel(logging.WARNING)
    logger.addHandler(tg_logs_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    logger.addHandler(stream_handler)

    start_bot(tg_bot, chat_id, dvmn_token)
