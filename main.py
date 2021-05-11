import os
import pyshorteners
import json
import requests
import sqlite3
from sqlite3 import Error
from uuid import uuid4
from telegram.ext import Updater, CommandHandler, ConversationHandler, Filters, CallbackQueryHandler, InlineQueryHandler, ChosenInlineResultHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, ParseMode, InlineQueryResultArticle, InputTextMessageContent

#Stages
INPUT_TEXT = 0
FIRST = 1

#URL services
url_base = 'https://sibucan-frontend-staging.herokuapp.com/services/'

#Paginate
offset = 1

#Get the cities
def getCities():
    response = requests.get('http://sibucan-backend-staging.herokuapp.com/cities/')
    jsonObject = response.json()

    cities = {}

    for city in jsonObject:
        cities[city['name']]=city['id']

    print('Devolviendo provincias')
    return cities

#Get the municipalities
def getMunicipalities():   
    municipalities = {}

    for id in cities.values():
        municipalities[id]=getMunicipalitiesByCity(id)

    print('Devolviendo municipios')
    return municipalities

#Get the municipalities with city
def getMunicipalitiesByCity(city):  
    response = requests.get('http://sibucan-backend-staging.herokuapp.com/municipalities/')
    jsonObject = response.json()

    municipalities = {}

    for municipality in jsonObject:
        if municipality['city'] == city:
            municipalities[municipality['name']]=municipality['id']

    return municipalities

#Start bot
def start(update, context):
    values = (int(update.message.chat['id']),0)
    sql_insert(values)
    update.message.reply_text(
        text = "👋 Hola, soy un bot para realizar búsquedas en la plataforma Sibucan.\n ⁉️ Consulta la /ayuda para que aprenda como utilizarme"
    )

#Help
def help(update, context):
    update.message.reply_text(
        text = '''⁉️ ¿Cómo buscar? 👇
        
📍 Use /filtro_provincia_municipio para buscar en un el municipio que desee
❌ Para buscar sin filtro de municipio, utilice /borrar_filtro
✏️ Escriba @sibucan_bot <em><u>texto</u></em>
🔎 Sustituya <em><u>texto</u></em> por el término que desea buscar

<b>Comandos: </b>
/filtro_provincia_municipio Elegir provincia y municipio para filtrar las búsquedas
/borrar_filtro Elimina el filtro de municipio para las búsquedas
/nosotros Información sobre la plataforma Sibucan
/emprendedores Información para los emprendedores
/clientes Información para los clientes''',
        parse_mode=ParseMode.HTML
    )

#About, us.
def about(update, context): 
    update.message.reply_text(
        text = '''<b>📌 Sobre nosotros</b>
<b>SIBUCAN</b> es un proyecto que busca estimular la iniciativa de los emprendedores cubanos y promover la calidad de los servicios y productos recibidos por los clientes.
A través de nuestra plataforma, los usuarios pueden ofrecer y recibir servicios, expresar su nivel de satisfacción, encontrar ofertas de trabajo y más.''',
        parse_mode=ParseMode.HTML
    )

#Entrepreneurs info
def entrepreneurs(update, context):
    update.message.reply_text(
        text = '''<b>📌 Para Emprendedores</b>
Solo tienes que dar el primer paso. Una vez que haya iniciado su proyecto empresarial, SIBUCAN le ofrece la posibilidad de ofrecer sus servicios y recibir las opiniones de sus clientes de forma dinámica. Cuanto mejor sea tu oferta, mayor será la demanda. ¡Así de simple!
Para hacerlo aún más atractivo, se puede acceder a nuestra plataforma desde cualquier parte del mundo, lo que brinda la posibilidad de que esté conectado a clientes de diferentes latitudes.''',
        parse_mode=ParseMode.HTML
    )

#Customers info
def customers(update, context):
    update.message.reply_text(
        text = '''<b>📌 Para Clientes</b>
¿Desea disfrutar de un buen servicio y al mismo tiempo contribuir al desarrollo de iniciativas de negocios locales?
SIBUCAN lo pone en contacto directo con miles de emprendedores locales y le permite evaluar el servicio recibido. ¡Su opinión cuenta! Al mismo tiempo, puede hacer reservas con anticipación, acordar precios y comparar ofertas.''',
        parse_mode=ParseMode.HTML
    )

#Municipalities Buttons
def keyboard_municipalities(update,context):    
    query = update.callback_query
    city = int(query.data.split()[1])

    keyboard_municipalities = []

    for id,mun in municipalities.items():
        if id == city: 
            for municipality,ident in mun.items():
                keyboard_municipalities.append(
                    [
                        InlineKeyboardButton(municipality, callback_data='search '+str(ident)+'')
                    ]
                )      

    query.answer()

    keyboard_municipalities.append(
        [
            InlineKeyboardButton('⬅️ Atrás', callback_data='atras')
        ]
    )      
           
    reply_markup = InlineKeyboardMarkup(keyboard_municipalities)

    query.edit_message_text(text=f"<b>🚩 Selecciona un municipio: </b>", reply_markup=reply_markup,parse_mode = ParseMode.HTML)

    return FIRST

#Provinces Buttons
def search_command_handler(update,context):    
    keyboard_cities = []

    for name,ident in cities.items():
        keyboard_cities.append(
            [
                InlineKeyboardButton(name, callback_data='keyboard_municipalities '+str(ident)+'')
            ]
        )
    
    keyboard_cities.append(
        [
            InlineKeyboardButton('🗑 Limpiar', callback_data='erase_municipality')
        ]
    )    

    reply_markup = InlineKeyboardMarkup(keyboard_cities)

    update.message.reply_text('<b>📍 Selecciona una provincia:</b>', reply_markup=reply_markup,parse_mode = ParseMode.HTML)
    return FIRST

#Provinces Buttons back
def search_command_handler_back(update,context):    
    query = update.callback_query
    keyboard_cities = []

    for name,ident in cities.items():
        keyboard_cities.append(
            [
                InlineKeyboardButton(name, callback_data='keyboard_municipalities '+str(ident)+'')
            ]
        )
    
    keyboard_cities.append(
        [
            InlineKeyboardButton('🗑 Limpiar', callback_data='erase_municipality')
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard_cities)

    query.answer()

    query.edit_message_text(text=f"<b>📍 Selecciona una provincia</b>", reply_markup=reply_markup, parse_mode = ParseMode.HTML)
    return FIRST

#Command erase municipality filter
def erase_municipality_handler(update,context):   
    chat_id = update.message.chat['id']
    values = (0,chat_id)
    sql_update(values)
    update.message.reply_text("Ahora puede comenzar a utilizar el comando @sibucan_bot para buscar.",parse_mode = ParseMode.HTML)

#Action erase municipality filter from button
def erase_municipality(update,context):   
    query = update.callback_query
    chat_id = query['message']['chat']['id']
    values = (0,chat_id)
    sql_update(values)   
    query.answer()
    query.edit_message_text(text="Ahora puede comenzar a utilizar el comando @sibucan_bot para buscar.", parse_mode = ParseMode.HTML)
    return FIRST

#Ready to search with municipality
def search_services(update,context):
    query = update.callback_query    
    chat_id = query['message']['chat']['id']
    values = (int(query.data.split()[1]),chat_id)
    sql_update(values)
    query.answer()
    query.edit_message_text(text='''Ahora puede comenzar a utilizar el comando @sibucan_bot para buscar en el municipio elegido.\nSi desea quitar la selección usa /borrar_filtro''')
    return FIRST

#Search
def inlinequery(update, context):
    global offset

    query = update.inline_query.query

    chat_id = (update.inline_query.from_user.id,)

    municipality_id = sql_select(chat_id)

    results = []

    if query == "":
        offset = 1
        results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Escriba un texto para buscar en Sibucan",
                    input_message_content=InputTextMessageContent("Debe escribir un texto para buscar en Sibucan.\nPor ejemplo: @sibucan_bot carpintero")
                )
        )
        update.inline_query.answer(results,cache_time=1)
        return FIRST
    else: 
        text = query                   

        if municipality_id == 0:
            params = {'search': text, 'sort': 'top-rated', 'page_size': 10, 'page': offset}
        else:        
            params = {'municipality':municipality_id, 'search': text, 'sort': 'top-rated', 'page_size': 10, 'page': offset}

        response = requests.get('http://sibucan-backend-staging.herokuapp.com/services/', params=params)
        
        if response.status_code == 200:
            print("Mun",municipality_id,"Resultados",response.json()['count'])               
            if response.json()['count'] != 0:
                services = response.json()['results']
                for service in services:
                    url_service = url_base+str(service["id"])+"/"
                    #Code line to use url short
                    #url_short = short_url(url_base+str(service["id"])+"/")
                    status_service = "🕐 Abierto" if service["open_now"] == True else "🕐 Cerrado"
                    telephone = "☎️ " + service["telephone"] if service["telephone"] != "" else "☎️ "+"No" 
                    cellphone = "📱 " + service["cellphone"] if service["cellphone"] != "" else "📱 "+"No"
                    description = '⭐️ '+str(service["average_rating"])+ "\n" + telephone + cellphone
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid4()),
                            title= "🔰 "+service["name"],
                            thumb_url = service["logo"],
                            url = url_service,
                            hide_url = True,
                            description = description,
                            input_message_content=InputTextMessageContent("🔰 "+"<b>"+service["name"]+"</b>\n"+telephone+'\n'+cellphone+"\n"+status_service+"\n"+"⭐️ "+str(service["average_rating"])+"\n"+"🌐 "+url_service,parse_mode=ParseMode.HTML),
                        )
                    )                         
                offset = offset + 1
                update.inline_query.offset=offset
                update.inline_query.answer(results,next_offset=offset,cache_time=1)
            else:
                results.append(
                        InlineQueryResultArticle(
                            id=str(uuid4()),
                            title="No se han encontrado resultados.",
                            description = "Más detalles",
                            input_message_content=InputTextMessageContent("Intenta cambiar de municipio o modificar el término de su búsqueda.")
                        )
                )
                update.inline_query.answer(results,next_offset=None,cache_time=1)
        else:
            offset = 1
            results = []
            update.inline_query.answer(results,next_offset=None,cache_time=1)
            return FIRST   

        return FIRST

#Short URL
def short_url(url):
    s = pyshorteners.Shortener()
    short_u = s.chilpit.short(url)
    return short_u

#Create Table
def create_table():    
    cursorObj.execute("CREATE TABLE IF NOT EXISTS data(id integer PRIMARY KEY, chat_id integer, municipality integer)")
    con.commit()

#Connection with database
def sql_connection():    
    try:
        con = sqlite3.connect('config.db',check_same_thread=False)
        print("Connection is established.")
        return con
    except Error:
        print(Error)

#Insert query
def sql_insert(values):    
    cursorObj.execute('INSERT INTO data(chat_id, municipality) VALUES(?, ?)', values)    
    con.commit()

#Update query
def sql_update(values): 
    cursorObj.execute('UPDATE data SET municipality = ? where chat_id = ?', values)    
    con.commit()

#Select query
def sql_select(value):
    cursorObj.execute('SELECT municipality FROM data where chat_id = ?',value)
    municipality = cursorObj.fetchall()[0][0]
    return municipality

#Main
if __name__ == '__main__':    
    cities = getCities()
    municipalities = getMunicipalities()

    con = sql_connection()
    cursorObj = con.cursor()    
    create_table()

    updater = Updater(token='1775317884:AAEXOrL96uPN5mW-ECgrYjMR3yMAUXllHtk', use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('iniciar',start))
    dp.add_handler(CommandHandler('start',start))
    dp.add_handler(CommandHandler('ayuda',help))
    dp.add_handler(CommandHandler('help',help))
    dp.add_handler(CommandHandler('nosotros',about))
    dp.add_handler(CommandHandler('emprendedores',entrepreneurs))
    dp.add_handler(CommandHandler('clientes',customers))  
    dp.add_handler(InlineQueryHandler(inlinequery))  
    dp.add_handler(ConversationHandler(
        entry_points = [
            CommandHandler('filtro_provincia_municipio', search_command_handler),
            CommandHandler('borrar_filtro', erase_municipality_handler),            
        ],
        states = {
            FIRST: [ 
                CommandHandler('borrar_filtro', erase_municipality_handler),  
                CommandHandler('filtro_provincia_municipio', search_command_handler),
                CallbackQueryHandler(erase_municipality, pattern='erase_municipality'),
                CallbackQueryHandler(search_services, pattern='search '+'*'),
                CallbackQueryHandler(keyboard_municipalities, pattern='keyboard_municipalities '+'*'),
                CallbackQueryHandler(search_command_handler_back, pattern='atras'),                
            ],
        },
        fallbacks=[],
    ))

    updater.start_polling()
    updater.idle()