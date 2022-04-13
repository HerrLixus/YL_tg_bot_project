import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

from utils import read_config
from searching_stuff import get_random_url
from get_capitals import get_capitals
from data.score import Scores
from data import db_session

capitals = None
user_context = dict()
bot = telebot.TeleBot(read_config()['token'])

"""Core functions"""


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    send_menu(message.from_user.id)


def send_menu(user_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    get_score_button = telebot.types.InlineKeyboardButton('Посмотреть счёт', callback_data='get_score')
    play_game_button = telebot.types.InlineKeyboardButton('Сыграть в игру', callback_data='play_game')
    send_picture_button = telebot.types.InlineKeyboardButton("Показать картинку", callback_data='send_picture')

    keyboard.add(get_score_button)
    keyboard.add(play_game_button)
    keyboard.add(send_picture_button)

    set_next_handler(user_id, 'empty')
    bot.send_message(user_id, 'Выберите действие', reply_markup=keyboard)


def set_next_handler(user_id: int, name: str):
    global user_context
    if user_id in user_context.keys():
        user_context[user_id]['next_handler'] = name
    else:
        user_context[user_id] = {'next_handler': name}


def check_handler(user_id, name):
    return user_context[user_id]['next_handler'] == name if user_id in user_context.keys() else True


@bot.message_handler(func=lambda message: check_handler(message.from_user.id, 'empty'))
def empty_handler(message):
    set_next_handler(message.from_user.id, 'empty')


@bot.callback_query_handler(lambda call: True)  # looks terrible, still works
def button_handler(call: telebot.types.CallbackQuery):
    if call.data == 'get_score':
        bot.send_message(call.from_user.id, str(get_score(call.from_user.id)))
    elif call.data == 'play_game':
        play_game(call.from_user.id)
    elif call.data == 'send_picture':
        bot.send_message(call.from_user.id, 'Введите запрос')
        set_next_handler(call.from_user.id, 'send_picture')
    elif call.data == 'open_menu':
        send_menu(call.from_user.id)

    elif call.data == 'correct':
        shut_answer_keyboard_down(call)
        bot.send_message(call.from_user.id, "Правильно!")
        add_score(call.from_user.id, 1)
        play_game(call.from_user.id)
    elif call.data == 'wrong':
        shut_answer_keyboard_down(call)
        bot.send_message(call.from_user.id, 'Неправильно!')
        play_game(call.from_user.id)


@bot.message_handler(content_types=['text'], func=lambda message: check_handler(message.from_user.id, 'send_picture'))
def send_picture(message: telebot.types.Message):
    try:
        url = get_random_url(message.text)
        if url is None:
            bot.send_message(message.from_user.id, 'произошла непредвиденная ошибка')
            return
        bot.send_photo(message.from_user.id, photo=url)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Показать меню", callback_data='open_menu')]])
        bot.send_message(message.from_user.id, 'Введите запрос', reply_markup=keyboard)
        set_next_handler(message.from_user.id, 'send_picture')
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)
        send_picture(message)


"""Scoring logic"""


def get_score(user_id):
    session = db_session.create_session()
    result = session.query(Scores).filter(Scores.user_id == user_id).first()
    if result is not None:
        return result.score
    else:
        return 0


def add_score(user_id, score: int):
    try:
        session = db_session.create_session()
        result = session.query(Scores).filter(Scores.user_id == user_id).first()
        if result is not None:
            result.score += score
        else:
            result = Scores()
            result.user_id = user_id
            result.score = score
            session.add(result)
        session.commit()
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)


"""Guessing game logic"""


def play_game(user_id):
    try:
        options = random.choices(capitals, k=3)
        choice = random.choice(options)
        url = get_random_url(choice[1] + ' город')
        if url is None:
            bot.send_message(user_id, 'произошла непредвиденная ошибка')
            return
        bot.send_photo(user_id, photo=url)

        keyboard = InlineKeyboardMarkup()
        keys = [InlineKeyboardButton(i[0], callback_data='correct' if i == choice else 'wrong') for i in options]
        for key in keys:
            keyboard.add(key)
        keyboard.add(InlineKeyboardButton('Прекратить играть', callback_data='open_menu'))
        bot.send_message(user_id, "Чья это столица?", reply_markup=keyboard)
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)
        play_game(user_id)


def shut_answer_keyboard_down(call):
    keyboard = InlineKeyboardMarkup()
    for row in call.message.reply_markup.keyboard:
        for key in row:
            new_key = InlineKeyboardButton(
                key.text + (' ✔' if key.callback_data == 'correct' else ' ️❌'),
                callback_data='something_else')
            keyboard.add(new_key)
    bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=keyboard)


"""Initialization"""


def initialize():
    global capitals
    db_session.global_init('db/score.db')
    capitals = get_capitals()
    bot.polling(non_stop=True, interval=0)


if __name__ == '__main__':
    initialize()
