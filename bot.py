import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('7841440458:AAFwMEasA_AkaEy7CwjdKlEadLHiBBloPyI') # подключение к боту
conn = sqlite3.connect('C:/bot/pictures.db', check_same_thread=False) # подключение к бд
cursor = conn.cursor()

TableFed = cursor.execute("""SELECT * from feedback""").fetchall() # вся таблица отзывов
TablePicFed = cursor.execute("""SELECT * from picfeedback""").fetchall() # вся таблица отзывов на картины
TableArt = cursor.execute("""SELECT * from artists""").fetchall()  # вся таблица художников
TablePic = cursor.execute("""SELECT * from pictures""").fetchall() # вся таблица картин

All_artists = []  # список всех художников
for i in TableArt:
    All_artists.append(i[1])


All_pictures = {}  # словарь имя картины : путь к ней на пк
for i in TablePic:
    All_pictures[i[2]] = i[1].replace("\\", "/").replace('"', '')

All_discription = {}  # словарь имя картины : ее описание
for i in TablePic:
    All_discription[i[2]] = i[3]

All_ID = {}  # словарь имя картины : ID
for i in TablePic:
    All_ID[i[2]] = i[0]


@bot.message_handler(commands=['start']) # функция на старт
def start_message(message): 
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Каталог художников")
    button2 = types.KeyboardButton("Каталог картин")
    button3 = types.KeyboardButton("Посмотреть отзывы о выставке")
    button4 = types.KeyboardButton("Написать отзыв о выставке")
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    bot.send_message(message.from_user.id, "ОХАЕ", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'desa1')  # описание картин
def Discription_Pic(call):
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id, All_discription[(call.data.split("desa1")[1])])


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'desa0')  # описание художников
def Discription_Art(call):
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id, TableArt[All_artists.index(call.data.split("desa0")[1])][2])


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'sfeed')  # выводит все отзывы о картине
def Seefeed(call):
    message = call.message
    chat_id = message.chat.id
    b = All_ID[(call.data.split("sfeed")[1])]
    cursor.execute(f"SELECT `{b}` FROM picfeedback")
    TablePicFed = cursor.fetchall()
    c=0
    bot.send_message(message.chat.id, f'Отзывы о картине "{(call.data.split("sfeed")[1])}" :')
    for i in TablePicFed:
        if i[0] is not None:
            c += 1
            bot.send_message(message.chat.id, f'{c}) {i[0]}')
        if c == 5:
            break


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'wfeed')  # написать отзыв о картине
def Writefeed(call):
    global where
    where = (call.data)
    mesg = bot.send_message(call.from_user.id, "Напишите отзыв")
    bot.register_next_step_handler(mesg, Write_feedback)


def Write_feedback(message):  # я хз как это работает но я это сделал. она ищет пустую строку в нужном столбцйе добавляет туда сообщение
    per1 = where.split("wfeed")[1]
    for i in range(len(TablePic)):
        if TablePic[i][2] == per1:
            existing_columns = TablePic[i][0]
    cursor.execute("PRAGMA table_info(picfeedback)")
    ids = [column[1] for column in cursor.fetchall()]
    if str(existing_columns) not in ids:
        cursor.execute(f'''ALTER TABLE picfeedback ADD COLUMN `{existing_columns}` TEXT ''')
    query = f'SELECT ROWID  FROM picfeedback WHERE "{existing_columns}" IS NULL LIMIT 1'
    cursor.execute(query)
    row = cursor.fetchone()
    if row:
        cursor.execute(f'UPDATE picfeedback SET "{existing_columns}" = ? WHERE rowid = ?', (message.text, row[0]))
    else:
        cursor.execute(f'INSERT INTO picfeedback ("{existing_columns}") VALUES (?)', (message.text,))
    conn.commit()
    mesg = bot.send_message(message.chat.id, 'Ваш отзыв сохранён')


@bot.message_handler(func=lambda message: message.text == 'Каталог художников')  # выводит список всех художников
def ALL_Pictures_list(message):
    for i in All_artists:
        keyboard1 = telebot.types.InlineKeyboardMarkup()
        button_save = telebot.types.InlineKeyboardButton(text="Описание", callback_data=f'desa0{i}')
        keyboard1.add(button_save)
        bot.send_message(message.from_user.id, i, reply_markup=keyboard1)


@bot.message_handler(func=lambda message: message.text == 'Каталог картин')  # выводит список всех картин
def ALL_Artists_list(message):
    for i, v in All_pictures.items():
        keyboard1 = telebot.types.InlineKeyboardMarkup()
        button_save = telebot.types.InlineKeyboardButton(text="Описание", callback_data=f'desa1{i}')
        button_feed = telebot.types.InlineKeyboardButton(text="Посмотреть отзывы", callback_data=f'sfeed{i}')
        button_feed1 = telebot.types.InlineKeyboardButton(text="Написать отзыв", callback_data=f'wfeed{i}')
        keyboard1.add(button_save, button_feed1)
        keyboard1.add(button_feed)
        bot.send_photo(message.from_user.id, open(v, "rb"), caption=i, reply_markup=keyboard1)


@bot.message_handler(func=lambda message: message.text == 'Посмотреть отзывы о выставке')  # вывод отзывов (5 с конца)
def See_5_feedback(message):
    TableFed = cursor.execute("""SELECT * from feedback""").fetchall()
    for i in range(len(TableFed)):
        bot.send_message(message.from_user.id,f'{i+1}) {TableFed[-1 * (i + 1)][0]}')
        if i >= 4:
            break


def save_feedback(message):  # добавление отзыва о всей выставке ( есть кастыль так как строку он добавлять не хочет поэтому создаю список с 1 элементом который добавляется)
    a = []
    a.append(message.text)
    cursor.execute(f'INSERT INTO feedback (feedback) VALUES (?)', (a))
    conn.commit()
    bot.send_message(message.from_user.id, "Ваш отзыв сохранён")


@bot.message_handler(func=lambda message: message.text == 'Написать отзыв о выставке')  # написать отзыв 
def write_to_support(message):
    bot.send_message(message.from_user.id, "Напишите отзыв")
    bot.register_next_step_handler(message, save_feedback)


bot.infinity_polling()
