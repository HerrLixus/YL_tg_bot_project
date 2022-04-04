import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

from utils import read_config
from searching_stuff import get_random_url
from get_capitals import get_capitals
from data.score import Scores
from data import db_session

capitals = None
bot = telebot.TeleBot(read_config()['token'])


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    get_score_button = telebot.types.InlineKeyboardButton('Посмотреть счёт', callback_data='get_score')
    add_score_button = telebot.types.InlineKeyboardButton('Добавить счёт', callback_data='add_score')
    send_picture_button = telebot.types.InlineKeyboardButton("Показать картинку", callback_data='send_picture')
    play_game_button = telebot.types.InlineKeyboardButton('Сыграть в игру', callback_data='play_game')
    keyboard.add(get_score_button)
    keyboard.add(add_score_button)
    keyboard.add(send_picture_button)
    keyboard.add(play_game_button)

    bot.send_message(message.from_user.id, 'Выберите действие', reply_markup=keyboard)


@bot.callback_query_handler(lambda call: True)
def button_handler(call: telebot.types.CallbackQuery):
    if call.data == 'get_score':
        bot.send_message(call.from_user.id, str(get_score(call.from_user.id)))
    elif call.data == 'add_score':
        bot.send_message(call.from_user.id, 'Введите счёт')
        bot.register_next_step_handler_by_chat_id(call.from_user.id, add_score)
    elif call.data == 'send_picture':
        bot.send_message(call.from_user.id, "Введите запрос")
        bot.register_next_step_handler_by_chat_id(call.from_user.id, send_picture)
    elif call.data == 'play_game':
        play_game(call.from_user.id)
    elif call.data == 'correct':

        keyboard = InlineKeyboardMarkup()
        for row in call.message.reply_markup.keyboard:
            for key in row:
                new_key = InlineKeyboardButton(key.text, callback_data='something_else')
                keyboard.add(new_key)
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=keyboard)

        bot.send_message(call.from_user.id, "you're goddamn right")
    elif call.data == 'wrong':
        keyboard = InlineKeyboardMarkup()
        for row in call.message.reply_markup.keyboard:
            for key in row:
                new_key = InlineKeyboardButton(key.text, callback_data='something_else')
                keyboard.add(new_key)
        bot.edit_message_reply_markup(call.from_user.id, call.message.id, reply_markup=keyboard)

        bot.send_message(call.from_user.id, 'Wrong!')


def get_score(user_id):
    session = db_session.create_session()
    result = session.query(Scores).filter(Scores.user_id == user_id).first()
    if result is not None:
        return result.score
    else:
        return 0


@bot.message_handler()
def add_score(message: telebot.types.Message):
    try:
        score = int(message.text)
        session = db_session.create_session()
        result = session.query(Scores).filter(Scores.user_id == message.from_user.id).first()
        if result is not None:
            result.score += score
        else:
            result = Scores()
            result.user_id = message.from_user.id
            result.score = score
            session.add(result)
        session.commit()
        bot.register_next_step_handler(message, add_score)
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)
    bot.send_message(message.from_user.id, 'Введите счёт')


@bot.message_handler()
def send_picture(message: telebot.types.Message):
    try:
        url = get_random_url(message.text)
        bot.send_photo(message.from_user.id, photo=url)
        bot.register_next_step_handler(message, send_picture)
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)
        send_picture(message)


def play_game(user_id):
    try:
        options = random.choices(capitals, k=3)
        choice = random.choice(options)
        url = get_random_url(choice[1])
        bot.send_photo(user_id, photo=url)

        keyboard = InlineKeyboardMarkup()
        keys = [InlineKeyboardButton(i[0], callback_data='correct' if i == choice else 'wrong') for i in options]
        for key in keys:
            keyboard.add(key)
        bot.send_message(user_id, choice[0], reply_markup=keyboard)
    except Exception as exc:
        print('Что-то пошло не так')
        print(type(exc).__name__)
        play_game(user_id)


def initialize():
    global capitals
    db_session.global_init('db/score.db')
    capitals = get_capitals()
    bot.polling(non_stop=True, interval=0)


if __name__ == '__main__':
    initialize()
