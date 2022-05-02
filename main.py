import sqlalchemy
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

from utils import read_config, get_user_name
from searching_stuff import get_random_url
from get_capitals import get_capitals
from data.score import Scores
from data import db_session

capitals = list()
user_context = dict()
bot = telebot.TeleBot(read_config()['token'])

"""Core functions"""


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    send_menu(message)


def send_menu(call):
    keyboard = telebot.types.InlineKeyboardMarkup()
    buttons = {'Посмотреть счёт': 'get_score',
               'Посмотреть таблицу лидеров': 'send_leaderboard',
               'Сыграть в игру': 'play_game',
               "Показать картинку": 'send_picture'
               }
    keyboard.keyboard = [[InlineKeyboardButton(item[0], callback_data=item[1])] for item in buttons.items()]

    set_next_handler(call.from_user.id, 'empty')
    bot.send_message(call.from_user.id, 'Выберите действие', reply_markup=keyboard)


@bot.message_handler(func=lambda message: check_handler(message.from_user.id, 'empty'))
def empty_handler(message):
    set_next_handler(message.from_user.id, 'empty')


@bot.callback_query_handler(lambda call: True)
def button_handler(call: telebot.types.CallbackQuery):
    functions = {'get_score': send_score,
                 'play_game': play_game,
                 'send_picture': init_send_picture,
                 'open_menu': send_menu,
                 'send_leaderboard': send_leaderboard,

                 'correct': process_correct_answer,
                 'wrong': process_wrong_answer}
    functions[call.data](call)


""" Working with user context """


def set_next_handler(user_id: int, name: str):
    global user_context
    if user_id in user_context.keys():
        user_context[user_id]['next_handler'] = name
    else:
        user_context[user_id] = {'next_handler': name}


def check_handler(user_id, name):
    return user_context[user_id]['next_handler'] == name if user_id in user_context.keys() else True


"""Sending pictures"""


def init_send_picture(call):
    bot.send_message(call.from_user.id, 'Введите запрос')
    set_next_handler(call.from_user.id, 'send_picture')


@bot.message_handler(content_types=['text'], func=lambda message: check_handler(message.from_user.id, 'send_picture'))
def send_picture(message: telebot.types.Message):
    try:
        # find and send picture
        url = get_random_url(message.text)
        if url is None:
            bot.send_message(message.from_user.id, 'произошла непредвиденная ошибка')
            return
        bot.send_photo(message.from_user.id, photo=url)

        # send open menu button
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Показать меню", callback_data='open_menu')]])
        bot.send_message(message.from_user.id, 'Введите запрос', reply_markup=keyboard)
        set_next_handler(message.from_user.id, 'send_picture')
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)
        send_picture(message)


"""Working with score"""


def get_score(user_id):
    session = db_session.create_session()
    result = session.query(Scores).filter(Scores.user_id == user_id).first()
    if result is not None:
        return result.right, result.wrong
    else:
        return 0, 0


def add_score(user_id, category):
    try:
        session = db_session.create_session()
        result = session.query(Scores).filter(Scores.user_id == user_id).first()
        if result is not None:
            if category == 'right':
                result.right += 1
            elif category == 'wrong':
                result.wrong += 1
        else:
            result = Scores()
            result.user_id = user_id
            if category == 'right':
                result.right = 1
            elif category == 'wrong':
                result.wrong = 1
            session.add(result)
        session.commit()
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)


def send_score(call):
    username = get_user_name(call.from_user)
    score = get_score(call.from_user.id)
    text = f"{username}, Ваш счёт:\nПравильных: {score[0]}, Неправильных: {score[1]}"
    bot.send_message(call.from_user.id, text)


def get_leaderboard():
    session = db_session.create_session()
    result = session.query(Scores).order_by(sqlalchemy.desc(Scores.right), Scores.wrong).all()[:5]
    return [(index, get_user_name(bot.get_chat(user.user_id)),
             user.right, user.wrong)
            for index, user in enumerate(result)]


def send_leaderboard(call):
    bot.send_message(call.from_user.id, f'Таблица лидеров:\n' +
                     '\n\n'.join([f"{user[0]+1}.{user[1]}:\n"
                                  f"Правильных: {user[2]}, Неправильных: {user[3]}" for user in get_leaderboard()]))


"""Guessing game logic"""


def play_game(call):
    user_id = call.from_user.id
    try:
        # choose and send photo
        options = random.choices(capitals, k=3)
        choice = random.choice(options)
        url = get_random_url(choice[1] + ' город')
        if url is None:
            bot.send_message(user_id, 'произошла непредвиденная ошибка')
            send_menu(call)
            return
        bot.send_photo(user_id, photo=url)

        # send keyboard
        keyboard = InlineKeyboardMarkup()
        keys = [InlineKeyboardButton(i[0], callback_data='correct' if i == choice else 'wrong') for i in options]
        for key in keys:
            keyboard.add(key)
        keyboard.add(InlineKeyboardButton('Прекратить играть', callback_data='open_menu'))
        bot.send_message(user_id, "Чья это столица?", reply_markup=keyboard)
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)
        play_game(call)


def shut_answer_keyboard_down(call):
    keyboard = InlineKeyboardMarkup()
    for row in call.message.reply_markup.keyboard:
        for key in row:
            new_key = InlineKeyboardButton(
                key.text + (' ✅' if key.callback_data == 'correct' else ' ️❌'),
                callback_data='something_else')
            keyboard.add(new_key)
    bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=keyboard)


def process_correct_answer(call):
    shut_answer_keyboard_down(call)
    bot.send_message(call.from_user.id, "Правильно! ✅")
    add_score(call.from_user.id, 'right')
    play_game(call)


def process_wrong_answer(call):
    shut_answer_keyboard_down(call)
    bot.send_message(call.from_user.id, 'Неправильно! ️❌')
    add_score(call.from_user.id, 'wrong')
    play_game(call)


"""Initialization"""


def initialize():
    global capitals
    db_session.global_init('db/score.db')
    capitals = get_capitals()
    bot.polling(non_stop=True, interval=0)


if __name__ == '__main__':
    initialize()
