import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('7841440458:AAFwMEasA_AkaEy7CwjdKlEadLHiBBloPyI')  # подключение к боту
conn = sqlite3.connect('C:/bot/pictures.db', check_same_thread=False)  # подключение к бд
cursor = conn.cursor()


def DataBase():  # обновление данных взятых из бд
    global TableFed, TablePicFed, TableArt, TablePic, All_artists, All_pictures, All_discription, All_ID, All_pictures_avtors, Admin
    TableFed = cursor.execute("""SELECT * from feedback""").fetchall()  # вся таблица отзывов
    TablePicFed = cursor.execute("""SELECT * from picfeedback""").fetchall()  # вся таблица отзывов на картины
    TableArt = cursor.execute("""SELECT * from artists""").fetchall()  # вся таблица художников
    TablePic = cursor.execute("""SELECT * from pictures""").fetchall()  # вся таблица картин

    All_artists = []  # список всех художников
    for i in TableArt:
        All_artists.append(i[1])

    All_pictures_avtors = {}  # словарь имя картины : ее авторы
    for i in TablePic:
        All_pictures_avtors[i[2]] = i[4]

    All_pictures = {}  # словарь имя картины : путь к ней на пк
    for i in TablePic:
        All_pictures[i[2]] = i[1].replace("\\", "/").replace('"', '')

    All_discription = {}  # словарь имя картины : ее описание
    for i in TablePic:
        All_discription[i[2]] = i[3]

    All_ID = {}  # словарь имя картины : ID
    for i in TablePic:
        All_ID[i[2]] = i[0]


DataBase()
Admin = 0


@bot.message_handler(func=lambda message: message.text == 'Не Администратор')  # выход из админа
@bot.message_handler(commands=['start'])  # функция на старт
def start_message(message):
    DataBase()
    global Admin
    Admin = 0
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Каталог художников")
    button2 = types.KeyboardButton("Каталог картин")
    button3 = types.KeyboardButton("Посмотреть отзывы о выставке")
    button4 = types.KeyboardButton("Написать отзыв о выставке")
    button5 = types.KeyboardButton("Администратор")
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    keyboard.add(button5)
    bot.send_message(message.from_user.id, "ОХАЁ", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Администратор')  #
def Admin(message):
    DataBase()
    global Admin
    Admin = 1
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Каталог художников")
    button2 = types.KeyboardButton("Каталог картин")
    button3 = types.KeyboardButton("Добавить картину")
    button4 = types.KeyboardButton("Добавить художника")
    button7 = types.KeyboardButton("Не Администратор")
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    keyboard.add(button7)
    bot.send_message(message.from_user.id, "ОХАЕ", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Добавить художника')  # добавить художника этап 1
def ALL_Artists_list(message):
    bot.register_next_step_handler(message, Add_Name)
    bot.send_message(message.chat.id, "Напишите автора")


def Add_Name(message):  # добавить художника этап 2 ( добавление имени)
    global Add_art_name
    Add_art_name = message.text
    cursor.execute(f'INSERT INTO artists (creator_name) VALUES (?)', (message.text,))
    conn.commit()
    bot.register_next_step_handler(message, Add_Desc)
    bot.send_message(message.chat.id, "Напишите описание")


def Add_Desc(message):  # добавить художника этап 3 ( добавление описание)
    cursor.execute(f'UPDATE artists SET description = "{message.text}" where creator_name = "{Add_art_name}" ')
    conn.commit()
    bot.send_message(message.chat.id, f'Автор сохранён')


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'desa1')  # описание картин
def Discription_Pic(call):
    DataBase()
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id,
                     f'Название : {(call.data.split("desa1")[1])}\nАвторы: {All_pictures_avtors[(call.data.split("desa1")[1])]} \nОписание: {All_discription[(call.data.split("desa1")[1])]}')


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'desa0')  # описание художников
def Discription_Art(call):
    DataBase()
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id, TableArt[All_artists.index(call.data.split("desa0")[1])][2])


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'sfeed')  # выводит все отзывы о картине
def Seefeed(call):
    DataBase()
    message = call.message
    chat_id = message.chat.id
    b = All_ID[(call.data.split("sfeed")[1])]
    cursor.execute(f"SELECT `{b}` FROM picfeedback")
    TablePicFed = cursor.fetchall()
    c = 0
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


def Write_feedback(
        message):  # я хз как это работает но я это сделал. она ищет пустую строку в нужном столбцйе добавляет туда сообщение
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
    DataBase()
    if Admin == 0:
        for i in All_artists:
            keyboard1 = telebot.types.InlineKeyboardMarkup()
            button_save = telebot.types.InlineKeyboardButton(text="Описание", callback_data=f'desa0{i}')
            keyboard1.add(button_save)
            bot.send_message(message.from_user.id, i, reply_markup=keyboard1)
    elif Admin == 1:
        for i in All_artists:
            keyboard1 = telebot.types.InlineKeyboardMarkup()
            button1 = telebot.types.InlineKeyboardButton(text="Изменить Описание", callback_data=f'redao{i}')
            button3 = telebot.types.InlineKeyboardButton(text="Изменить Имя", callback_data=f'redan{i}')
            button2 = telebot.types.InlineKeyboardButton(text="Удалить", callback_data=f'delet{i}')
            keyboard1.add(button1, button3)
            keyboard1.add(button2)
            bot.send_message(message.from_user.id, i, reply_markup=keyboard1)


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'delet')  # удалить все о выбранной художнике]
def Delete_Artist(call):
    Name_Artists_Delete = call.data.split("delet")[1]
    cursor.execute(f'DELETE FROM artists WHERE creator_name = "{Name_Artists_Delete}"')
    conn.commit()


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'redan')  # изменить имя художника
def Redact_Artists(call):
    global Name_Artists_Readct
    Name_Artists_Readct = call.data.split("redan")[1]
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id,
                     f'Имя в данный момент: {TableArt[All_artists.index(call.data.split("redan")[1])][1]}')
    mesg = bot.send_message(message.chat.id, f'Напишите на что его заменить')
    bot.register_next_step_handler(mesg, Redact_Artists_Update1)


def Redact_Artists_Update1(message):  # изменить имя художника после получения сообщения
    cursor.execute(f'UPDATE artists SET creator_name = "{message.text}" where creator_name = "{Name_Artists_Readct}" ')
    conn.commit()
    bot.send_message(message.chat.id, f'Имя сохранено')


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'redao')  # изменить описание картины
def Redact_Artists(call):
    global Name_Artists_Readct
    Name_Artists_Readct = call.data.split("redao")[1]
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id,
                     f'Описание в данный момент: {TableArt[All_artists.index(call.data.split("redao")[1])][2]}')
    mesg = bot.send_message(message.chat.id, f'Напишите на что его заменить')
    bot.register_next_step_handler(mesg, Redact_Artists_Update)


def Redact_Artists_Update(message):  # изменить описание картины после получения сообщения
    cursor.execute(f'UPDATE artists SET description = "{message.text}" where creator_name = "{Name_Artists_Readct}" ')
    conn.commit()
    bot.send_message(message.chat.id, f'Описание сохранено')


@bot.message_handler(func=lambda message: message.text == 'Каталог картин')  # выводит список всех картин
def ALL_Artists_list(message):
    DataBase()
    if Admin == 0:
        for i, v in All_pictures.items():
            keyboard1 = telebot.types.InlineKeyboardMarkup()
            button_save = telebot.types.InlineKeyboardButton(text="Описание", callback_data=f'desa1{i}')
            button_feed = telebot.types.InlineKeyboardButton(text="Посмотреть отзывы", callback_data=f'sfeed{i}')
            button_feed1 = telebot.types.InlineKeyboardButton(text="Написать отзыв", callback_data=f'wfeed{i}')
            keyboard1.add(button_save, button_feed1)
            keyboard1.add(button_feed)
            bot.send_photo(message.from_user.id, open(v, "rb"), caption=i, reply_markup=keyboard1)
    elif Admin == 1:
        for i, v in All_pictures.items():
            keyboard1 = telebot.types.InlineKeyboardMarkup()
            button1 = telebot.types.InlineKeyboardButton(text="Изменить Описание", callback_data=f'editd{i}')
            button2 = telebot.types.InlineKeyboardButton(text="Изменить Название", callback_data=f'editn{i}')
            button3 = telebot.types.InlineKeyboardButton(text="Изменить Авторов", callback_data=f'edita{i}')
            button4 = telebot.types.InlineKeyboardButton(text="Удалить", callback_data=f'delep{i}')
            keyboard1.add(button2, button1)
            keyboard1.add(button3, button4)
            bot.send_photo(message.from_user.id, open(v, "rb"), caption=i, reply_markup=keyboard1)


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'edita')  # изменить описание картины
def Redact_Avtors(call):
    global Name_Pictures_Readct
    Name_Pictures_Readct = call.data.split("edita")[1]
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id,
                     f'Авторы картины "{Name_Pictures_Readct}" в данный момент: {All_pictures_avtors[(call.data.split("edita")[1])]}')
    mesg = bot.send_message(message.chat.id, f'Напишите новых авторов через запятую')
    bot.register_next_step_handler(mesg, Redact_Pictures_Avtors_Update)


def Redact_Pictures_Avtors_Update(message):  # изменить описание картины после получения сообщения
    cursor.execute(
        f'UPDATE pictures SET pictures_avtors = "{message.text}" where pictures_name = "{Name_Pictures_Readct}" ')
    conn.commit()
    bot.send_message(message.chat.id, f'Авторы сохранены')


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'delep')  # удалить все о выбранной картине
def Delete_Artist(call):
    Name_Pictures_Readct = call.data.split("delep")[1]
    cursor.execute(f'DELETE FROM pictures WHERE pictures_name = "{Name_Pictures_Readct}"')
    conn.commit()


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'editd')  # изменить описание картины
def Redact_Artists(call):
    global Name_Pictures_Readct
    Name_Pictures_Readct = call.data.split("editd")[1]
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id,
                     f'Описание картины "{Name_Pictures_Readct}" в данный момент: {All_discription[(call.data.split("editd")[1])]}')
    mesg = bot.send_message(message.chat.id, f'Напишите на что его заменить')
    bot.register_next_step_handler(mesg, Redact_Pictures_Update)


def Redact_Pictures_Update(message):  # изменить описание картины после получения сообщения
    cursor.execute(
        f'UPDATE pictures SET discription = "{message.text}" where pictures_name = "{Name_Pictures_Readct}" ')
    conn.commit()
    bot.send_message(message.chat.id, f'Описание сохранено')


@bot.callback_query_handler(func=lambda call: call.data[:5] == 'editn')  # изменить Название картины
def Redact_Name(call):
    global Name_Pictures_Readct
    Name_Pictures_Readct = call.data.split("editn")[1]
    message = call.message
    chat_id = message.chat.id
    bot.send_message(message.chat.id, f'Название картины в данный момент: "{Name_Pictures_Readct}"')
    mesg = bot.send_message(message.chat.id, f'Напишите на что его заменить')
    bot.register_next_step_handler(mesg, Redact_Pictures_Name_Update)


def Redact_Pictures_Name_Update(message):  # изменить Название картины после получения сообщения
    cursor.execute(
        f'UPDATE pictures SET pictures_name = "{message.text}" where pictures_name = "{Name_Pictures_Readct}" ')
    conn.commit()
    bot.send_message(message.chat.id, f'Название сохранено')


@bot.message_handler(func=lambda message: message.text == 'Посмотреть отзывы о выставке')  # вывод отзывов (5 с конца)
def See_5_feedback(message):
    DataBase()
    TableFed = cursor.execute("""SELECT * from feedback""").fetchall()
    for i in range(len(TableFed)):
        bot.send_message(message.from_user.id, f'{i + 1}) {TableFed[-1 * (i + 1)][0]}')
        if i >= 4:
            break


def save_feedback(
        message):  # добавление отзыва о всей выставке ( есть кастыль так как строку он добавлять не хочет поэтому создаю список с 1 элементом который добавляется)
    a = []
    a.append(message.text)
    cursor.execute(f'INSERT INTO feedback (feedback) VALUES (?)', (a))
    conn.commit()
    bot.send_message(message.from_user.id, "Ваш отзыв сохранён")


@bot.message_handler(func=lambda message: message.text == 'Написать отзыв о выставке')  # написать отзыв
def Write_All_Feedback(message):
    bot.send_message(message.from_user.id, "Напишите отзыв")
    bot.register_next_step_handler(message, save_feedback)


bot.infinity_polling()
