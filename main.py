from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
import telebot
from telebot import types
import lxml

# change your token
token = 'your_token'

bot = telebot.TeleBot(token)

date_now = date.today()


def get_raw_news(date_:date=date_now, number:int=20) -> dict[tuple[str, str], ResultSet[Tag]]:
    """ recieves date and number of news

    """
    html = requests.get(
        url=f'https://kaktus.media/?lable=8&date={date_}&order=time'
    )
    soup = BeautifulSoup(html.text, 'lxml')
    cards = soup.find_all('div', 'ArticleItem--data ArticleItem--data--withImage')[:number]
    return {(f'news{id}', card.find('a', class_ = 'ArticleItem--name').text.strip())
    : card for id, card in enumerate(cards, start=1)}


def get_news20(news:dict[tuple[str, str], ResultSet[Tag]]) -> dict[tuple[str, str], ResultSet[Tag]]:
    """ recieves raw news dict and returns exactly 20 last news
    
    """
    if len(news) < 20:
        yest_day = date_now - timedelta(days=1)
        rest_news = get_raw_news(yest_day, number=20-len(news))
        return {**news, **rest_news}
    else:
        return news


news = get_news20(get_raw_news())


@bot.message_handler(commands=['start'])
def start_news(message: types.Message):
    """ reacts to start command and sends last news
    
    """
    markup = types.InlineKeyboardMarkup()
    for id, title in news.keys():
        inline_button = types.InlineKeyboardButton(title, callback_data=id)
        markup.add(inline_button)
    bot.send_message(message.chat.id, 'Greetings', reply_markup=goodbye)
    bot.send_message(message.chat.id, 'Here I have last 20 news from kaktus',
    reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: callback.data in [key[0] for key in news])
def message_news(callback: types.CallbackQuery):
    """ reacts after certain news button was pressed
    
    sends news title, url and buttons

    """
    markup = types.InlineKeyboardMarkup()
    for key, tag in news.items():
        if key[0] == callback.data:
            url =tag.find('a', class_ = 'ArticleItem--name').get('href')
            markup.row(types.InlineKeyboardButton(text="Description", callback_data=f"{key[0]}desc"),
                       types.InlineKeyboardButton(text="Photo", callback_data=f"{key[0]}photo"))
            bot.send_message(callback.message.chat.id, f'{key[1]}\n{url}', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: 'desc' in callback.data)
def news_desc(callback: types.CallbackQuery):
    """ reacts when "Description" button was pressed
    
    sends description of news
    """
    for key, tag in news.items():
        if key[0] == callback.data[:-4]:
            desc_html = requests.get(tag.a.get('href')).text
            soup = BeautifulSoup(desc_html, 'lxml')
            bot.send_message(callback.message.chat.id, soup.find('p').text)


@bot.callback_query_handler(func=lambda callback: 'photo' in callback.data)
def news_photo(callback: types.CallbackQuery):
    """ reacts when "Photo" button was pressed
    
    sends photo of news
    """
    for key, tag in news.items():
        if key[0] == callback.data[:-5]:
            desc_html = requests.get(tag.a.get('href')).text
            soup = BeautifulSoup(desc_html, 'lxml')
            bot.send_photo(callback.message.chat.id,
            soup.find('meta', {'property': "og:image"}).get('content'))



goodbye = types.ReplyKeyboardMarkup(resize_keyboard=True)
button = types.KeyboardButton('Quit')
goodbye.add(button)

@bot.message_handler(func=lambda mes: mes.text == 'Quit')
def bye(message: types.Message):
    """ bye :,( 
    
    """
    bot.send_message(message.chat.id, 'До свидания!', reply_markup=types.ReplyKeyboardRemove())


bot.polling()
