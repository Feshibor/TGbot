import telebot;
import sqlite3
bot = telebot.TeleBot('')
conn = sqlite3.connect('C:/bot/pictures.db', check_same_thread=False)
cursorArt = conn.cursor()
cursorPic = conn.cursor()
cursorFed = conn.cursor()

def db_table_val(feedback: str):
	cursorFed.execute('INSERT INTO feedback (feedback) VALUES (?)', (feedback))
	conn.commit()

#таблица художников
sqlite1 = """SELECT * from artists"""
cursorArt.execute(sqlite1)
TableArt = cursorArt.fetchall()

#таблица картин
sqlite2 = """SELECT * from pictures"""
cursorPic.execute(sqlite2)
TablePic = cursorPic.fetchall()

PicturesAll=[]
for i in range(len(TablePic)):
    PicturesAll.append(TablePic[i][1].replace("\\","/").replace('"',''))

NamePicturesAll=[]
for i in range(len(TablePic)):
    NamePicturesAll.append(TablePic[i][2])

ArtistsAll=[]
for i in range(len(TableArt)):
    ArtistsAll.append(TableArt[i][1])

help="напишите: \n/artists - список всех художников \n/pictures - список всех картин \nнапишите название название картины или художника (с большой буквы) чтобы увидить описание"

@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    if message.text.lower() == '/artists':
        for i in ArtistsAll:
            bot.send_message(message.from_user.id, i)
    elif message.text in ArtistsAll:
        bot.send_message(message.from_user.id, TableArt[ArtistsAll.index(message.text)][2])

    elif message.text.lower() == "/pictures":
        for i in range(len(PicturesAll)):
            bot.send_photo(message.from_user.id, open(PicturesAll[i],"rb") , caption=TablePic[i][2])
    elif message.text in NamePicturesAll:
        bot.send_message(message.from_user.id, TablePic[NamePicturesAll.index(message.text)][3])

    elif '/feedback' in message.text.lower() :
        a=[]
        b=message.text.split('/feedback ')
        a.append(b[-1])
        bot.send_message(message.from_user.id, "Ваш отзыв был сохранен")
        db_table_val(feedback=a)
    elif message.text == "/help":
        bot.send_message(message.from_user.id, help)
    elif message.text == "/start":
        bot.send_message(message.from_user.id, "Напишите команду или /help")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


bot.polling(none_stop=True)
