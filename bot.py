import telebot
import sqlite3
import qrcode
from telebot import types
from io import BytesIO
from botocore.client import Config
import boto3
import os
from uuid import uuid4
import hashlib
import base64

conn = sqlite3.connect('C:/bot/pictures.db', check_same_thread=False)  # подключение к бд

cursor = conn.cursor()

s3 = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id='YCAJENyY1xC2xpg97hE4AdDXI',
    aws_secret_access_key='YCM6LGz6LnaD4AB4L5QqgeAPGGM8hS_ySSpUUVAr',
    region_name='ru-central1',
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'virtual'}
    )
)


def upload_to_s3(file_path, bucket_name='arts-bot'):
    """Загружает файл в S3 и возвращает URL"""
    try:
        # уникальное имя файла
        file_ext = os.path.splitext(file_path)[1]
        s3_key = f"{uuid4()}{file_ext}"

        # Читаем файл и вычисляем MD5 в правильном формате
        with open(file_path, 'rb') as f:
            content = f.read()
            md5_digest = base64.b64encode(hashlib.md5(content).digest()).decode('utf-8')

        # Загружаем файл
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            ContentType='image/jpeg',
            ContentMD5=md5_digest,
            ACL='public-read'
        )

        # Формируем URL
        return f"https://storage.yandexcloud.net/{bucket_name}/{s3_key}"

    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return None


# Проверка и создание таблиц при старте
def init_database():
    try:
        # Создаем таблицу pictures с нужными колонками
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pictures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pictures TEXT NOT NULL,
            pictures_name TEXT,
            discription TEXT,
            pictures_avtors TEXT
        )""")

        # Проверяем существование колонки pictures
        cursor.execute("PRAGMA table_info(pictures)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'pictures' not in columns:
            # Если колонки нет - добавляем
            cursor.execute("ALTER TABLE pictures ADD COLUMN pictures TEXT")

        conn.commit()
        print("База данных успешно инициализирована")
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")


# Вызываем при старте
init_database()


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

    All_pictures = {}  # словарь имя картины : URL в S3
    for i in TablePic:
        All_pictures[i[2]] = i[1]
    print(TablePic)
    All_discription = {}  # словарь имя картины : ее описание
    for i in TablePic:
        All_discription[i[2]] = i[3]

    All_ID = {}  # словарь имя картины : ID
    for i in TablePic:
        All_ID[i[2]] = i[0]


DataBase()
Admin = 0


@bot.message_handler(func=lambda message: message.text == 'Посетитель')  # выход из админа
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
    button5 = types.KeyboardButton("QR-код")
    button6 = types.KeyboardButton("Администратор")
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    keyboard.add(button5, button6)
    bot.send_message(message.from_user.id, "Бот запущен в режиме посетителя", reply_markup=keyboard)


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
    button7 = types.KeyboardButton("Посетитель")
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    keyboard.add(button7)
    bot.send_message(message.from_user.id, "Запущен режим администратора", reply_markup=keyboard)


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


@bot.message_handler(func=lambda message: message.text == 'Добавить картину')
def add_picture(message):
    msg = bot.send_message(message.chat.id, "Отправьте фотографию картины")
    bot.register_next_step_handler(msg, process_picture_step)


def process_picture_step(message):
    try:
        # Проверяем, что это фото
        if not message.photo:
            bot.send_message(message.chat.id, "Пожалуйста, отправьте фотографию")
            return

        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Сохраняем временно
        temp_path = f"temp_{file_info.file_id}.jpg"
        with open(temp_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Загружаем в S3
        image_url = upload_to_s3(temp_path)

        if image_url:
            # Удаляем временный файл
            os.remove(temp_path)

            # Запрашиваем остальные данные
            msg = bot.send_message(message.chat.id, "Введите название картины")
            bot.register_next_step_handler(msg, lambda m: get_picture_name(m, image_url))
        else:
            bot.send_message(message.chat.id, "Ошибка загрузки изображения")

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")


def get_picture_name(message, image_url):
    try:
        picture_name = message.text
        msg = bot.send_message(message.chat.id, "Введите описание картины")
        bot.register_next_step_handler(msg, lambda m: get_picture_desc(m, image_url, picture_name))
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")


def get_picture_desc(message, image_url, picture_name):
    try:
        description = message.text
        msg = bot.send_message(message.chat.id, "Введите авторов через запятую")
        bot.register_next_step_handler(msg, lambda m: save_picture_to_db(m, image_url, picture_name, description))
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")


def save_picture_to_db(message, image_url, picture_name, description):
    try:
        authors = message.text

        # Сохраняем в базу данных
        cursor.execute(
            """INSERT INTO pictures (pictures, pictures_name, discription, pictures_avtors) 
            VALUES (?, ?, ?, ?)""",
            (image_url, picture_name, description, authors)
        )
        conn.commit()

        bot.send_message(message.chat.id, "Картина успешно добавлена!")
        DataBase()  # Обновляем кэш

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка сохранения: {str(e)}")


@bot.message_handler(content_types=['photo'])
def handle_photo_upload(message):
    try:
        # Получаем файл
        file_info = bot.get_file(message.photo[-1].file_id)
        file_bytes = bot.download_file(file_info.file_path)
        file_ext = os.path.splitext(file_info.file_path)[1] or '.jpg'

        # Загружаем в S3
        image_url = upload_to_s3(file_bytes, file_ext, bucket_name='arts-bot')

        if image_url:
            # Сохраняем в БД с ВСЕМИ полями
            cursor.execute(
                """INSERT INTO pictures 
                (pictures, pictures_name, discription, pictures_avtors) 
                VALUES (?, ?, ?, ?)""",
                (image_url, "Название по умолчанию", "Описание по умолчанию", "Автор не указан")
            )
            conn.commit()

            bot.reply_to(message, f"Фото загружено! URL: {image_url}\n"
                                  "Теперь введите команду /edit для добавления информации")
        else:
            bot.reply_to(message, "Ошибка загрузки в облачное хранилище")

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")


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
            print(i, v)
            keyboard1 = telebot.types.InlineKeyboardMarkup()
            button_save = telebot.types.InlineKeyboardButton(text="Описание", callback_data=f'desa1{i}')
            button_feed = telebot.types.InlineKeyboardButton(text="Посмотреть отзывы", callback_data=f'sfeed{i}')
            button_feed1 = telebot.types.InlineKeyboardButton(text="Написать отзыв", callback_data=f'wfeed{i}')
            keyboard1.add(button_save, button_feed1)
            keyboard1.add(button_feed)
            bot.send_photo(message.from_user.id, v, caption=i, reply_markup=keyboard1)
    elif Admin == 1:
        for i, v in All_pictures.items():
            keyboard1 = telebot.types.InlineKeyboardMarkup()
            button1 = telebot.types.InlineKeyboardButton(text="Изменить Описание", callback_data=f'editd{i}')
            button2 = telebot.types.InlineKeyboardButton(text="Изменить Название", callback_data=f'editn{i}')
            button3 = telebot.types.InlineKeyboardButton(text="Изменить Авторов", callback_data=f'edita{i}')
            button4 = telebot.types.InlineKeyboardButton(text="Удалить", callback_data=f'delep{i}')
            keyboard1.add(button2, button1)
            keyboard1.add(button3, button4)
            bot.send_photo(message.from_user.id, v, caption=i, reply_markup=keyboard1)


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


@bot.callback_query_handler(func=lambda call: call.data.startswith('qr_'))
def handle_qr_request(call):
    name = call.data[3:]  # Извлекаем название картины
    if name in All_pictures:
        url = All_pictures[name]

        # Генерация QR-кода
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        bot.send_photo(
            call.message.chat.id,
            img_bytes,
            caption=f"QR-код для картины: {name}\nСсылка: {url}"
        )
    else:
        bot.send_message(call.message.chat.id, "Ошибка: картина не найдена")


@bot.message_handler(func=lambda message: message.text == "QR-код")
def qr_menu(message):
    DataBase()
    if not All_pictures:
        bot.send_message(message.chat.id, "В каталоге пока нет картин")
        start_message(message)  # Возврат в меню
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for name in All_pictures.keys():
        markup.add(types.KeyboardButton(name))
    markup.add(types.KeyboardButton("◀️ Назад"))

    bot.send_message(message.chat.id, "Выберите картину:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "◀️ Назад")
def back_to_menu(message):
    start_message(message)


@bot.message_handler(func=lambda message: message.text in All_pictures.keys())
def handle_picture_selection(message):
    generate_qr(message)
    start_message(message)  # Возврат в меню после генерации


def generate_qr(message):
    # Получаем СВЕЖИЕ данные из БД перед генерацией
    conn = sqlite3.connect('C:/bot/pictures.db', check_same_thread=False)  # подключение к бд
    cursor = conn.cursor()
    cursor.execute(
        "SELECT pictures FROM pictures WHERE pictures_name = ?",
        (message.text,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        bot.send_message(message.chat.id, "Данные картины не найдены")
        start_message(message)
        return

    url = result[0]

    if not url or not isinstance(url, str) or not url.startswith('http'):
        bot.send_message(message.chat.id, "Некорректный URL картины")
        start_message(message)
        return

    # Генерация QR-кода
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Отправка с возвратом в меню
    bot.send_photo(
        message.chat.id,
        img_bytes,
        caption=f"QR-код для: {message.text}\nURL: {url}"
    )


bot.infinity_polling()
