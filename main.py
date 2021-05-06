import os
import pyshorteners
import json
import requests
from uuid import uuid4
from telegram.ext import Updater, CommandHandler, ConversationHandler, Filters, CallbackQueryHandler, InlineQueryHandler, ChosenInlineResultHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, ParseMode, InlineQueryResultArticle, InputTextMessageContent

# Stages
INPUT_TEXT = 0
FIRST = 1

municipality_send = 0
url_base = 'https://sibucan-frontend-staging.herokuapp.com/services/'
offset = 1

#Get the cities from json file
def getCities():
    with open("json/cities.json") as jsonFile:
        jsonObject = json.load(jsonFile)
        jsonFile.close()   

    cities = {}

    for city in jsonObject:
        cities[city['name']]=city['id']

    return cities

#Get the municipalities from json file
def getMunicipalities():   
    with open("json/municipalities.json") as jsonFile:
        jsonObject = json.load(jsonFile)
        jsonFile.close()    

    municipalities = {}

    for id in cities.values():
        municipalities[id]=getMunicipalitiesByCity(id)

    return municipalities

#Get the municipalities from json file with city
def getMunicipalitiesByCity(city):   
    with open("json/municipalities.json") as jsonFile:
        jsonObject = json.load(jsonFile)
        jsonFile.close()
    
    municipalities = {}

    for municipality in jsonObject:
        if municipality['city'] == city:
            municipalities[municipality['name']]=municipality['id']

    return municipalities

def start(update, context):
    update.message.reply_text(
        text = "👋 Hola, soy un bot para realizar búsquedas en la plataforma Sibucan.\n ⁉️ Consulta la /ayuda para que aprenda como utilizarme"
    )

def help(update, context):
    update.message.reply_text(
        text = '''<b>Ayuda del Bot</b>
⁉️ ¿Cómo buscar? 👇
@sibucan_bot <em><u>texto</u></em> Buscar en Sibucan, sustituya <em><u>texto</u></em> por el término que desea buscar
<b>Comandos: </b>
/elegir_municipio Elegir un municipio para filtrar las búsquedas
/borrar_municipio Elimina el filtro de municipio para las búsquedas
/nosotros Información sobre la plataforma Sibucan
/emprendedores Información para los emprendedores
/clientes Información para los clientes''',
        parse_mode=ParseMode.HTML
    )

def about(update, context):
    update.message.reply_text(
        text = '''<b>📌 Sobre nosotros</b>
<b>SIBUCAN</b> es un proyecto que busca estimular la iniciativa de los emprendedores cubanos y promover la calidad de los servicios y productos recibidos por los clientes.
A través de nuestra plataforma, los usuarios pueden ofrecer y recibir servicios, expresar su nivel de satisfacción, encontrar ofertas de trabajo y más.''',
        parse_mode=ParseMode.HTML
    )

def entrepreneurs(update, context):
    update.message.reply_text(
        text = '''<b>📌 Para Emprendedores</b>
Solo tienes que dar el primer paso. Una vez que haya iniciado su proyecto empresarial, SIBUCAN le ofrece la posibilidad de ofrecer sus servicios y recibir las opiniones de sus clientes de forma dinámica. Cuanto mejor sea tu oferta, mayor será la demanda. ¡Así de simple!
Para hacerlo aún más atractivo, se puede acceder a nuestra plataforma desde cualquier parte del mundo, lo que brinda la posibilidad de que esté conectado a clientes de diferentes latitudes.''',
        parse_mode=ParseMode.HTML
    )

def customers(update, context):
    update.message.reply_text(
        text = '''<b>📌 Para Clientes</b>
¿Desea disfrutar de un buen servicio y al mismo tiempo contribuir al desarrollo de iniciativas de negocios locales?
SIBUCAN lo pone en contacto directo con miles de emprendedores locales y le permite evaluar el servicio recibido. ¡Su opinión cuenta! Al mismo tiempo, puede hacer reservas con anticipación, acordar precios y comparar ofertas.''',
        parse_mode=ParseMode.HTML
    )

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

def erase_municipality_handler(update,context):   
    global municipality_send
    municipality_send = 0
    update.message.reply_text("Ahora puede comenzar a utilizar el comando @sibucan_bot para buscar.",parse_mode = ParseMode.HTML)

def erase_municipality(update,context):   
    global municipality_send
    municipality_send = 0
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="Ahora puede comenzar a utilizar el comando @sibucan_bot para buscar.", parse_mode = ParseMode.HTML)
    return FIRST

def search_services(update,context):
    query = update.callback_query    
    global municipality_send
    municipality_send = int(query.data.split()[1])
    query.answer()
    query.edit_message_text(text="Ahora puede comenzar a utilizar el comando @sibucan_bot para buscar en el municipio elegido.")
    return FIRST

def inlinequery(update, context):
    global offset

    query = update.inline_query.query
    
    results = []
    
    if municipality_send == 0:
        params = {'search': query, 'sort': 'top-rated', 'page_size': 10, 'page': offset}
    else:        
        params = {'municipality':municipality_send, 'search': query, 'sort': 'top-rated', 'page_size': 10, 'page': offset}

    if query == "":
        offset = 1
        results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Escriba un texto para buscar en Sibucan",
                    input_message_content=InputTextMessageContent("Debe escribir un texto para buscar en Sibucan.\nPor ejemplo: @sibucan_bot carpintero")
                )
        )
        update.inline_query.answer(results)
        return FIRST

    response = requests.get('http://sibucan-backend-staging.herokuapp.com/services/', params=params)
    
    if response.status_code == 200:
        if response.json()['count'] != 0:
            services = response.json()['results']
            for service in services:
                url_service = url_base+str(service["id"])+"/"
                # url_short = short_url(url_base+str(service["id"])+"/")
                if service["open_now"] == True:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid4()),
                            title=service["name"],
                            thumb_url = service["logo"],
                            url = url_service,
                            hide_url = True,
                            description = "Teléfonos: " + service["telephone"] + ' ' + service["telephone"]+'\n'+"Ver más",
                            input_message_content=InputTextMessageContent("<b>"+service["name"]+"</b>\n"+"☎️Teléfonos: " + service["telephone"] + ' ' + service["telephone"]+"\n"+"🕐 Abierto: Sí"+"\n"+"⭐️ "+str(service["average_rating"])+"\n"+"🌐 "+url_service,parse_mode=ParseMode.HTML),
                        )
                    )    
                else: 
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid4()),
                            title=service["name"],
                            thumb_url = service["logo"],
                            url = url_service,
                            hide_url = True,
                            offset = 4,
                            description = "Teléfonos: " + service["telephone"] + ' ' + service["telephone"]+'\n'+"Ver más",
                            input_message_content=InputTextMessageContent("<b>"+service["name"]+"</b>\n"+"☎️ Teléfonos: " + service["telephone"] + ' ' + service["telephone"]+"\n"+"🕐 Abierto: No"+"\n"+"⭐️ "+str(service["average_rating"])+"\n"+"🌐 "+url_service,parse_mode=ParseMode.HTML),
                        )
                    )    
            offset = offset + 1
            update.inline_query.offset=offset
            update.inline_query.answer(results,next_offset=offset)
        else:
            results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title="No se han encontrado resultados.",
                        description = "Más detalles",
                        input_message_content=InputTextMessageContent("Intenta cambiar de municipio o modificar el término de su búsqueda.")
                    )
            )
            update.inline_query.answer(results,next_offset=None)
    else:
        offset = 1
        results = []
        update.inline_query.answer(results,next_offset=None)
        return FIRST   
    
    return FIRST

def short_url(url):
    s = pyshorteners.Shortener()
    short_u = s.chilpit.short(url)
    return short_u

if __name__ == '__main__':    
    cities = getCities()
    municipalities = getMunicipalities()
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
            CommandHandler('elegir_municipio', search_command_handler),
            CommandHandler('borrar_municipio', erase_municipality_handler),            
        ],
        states = {
            FIRST: [ 
                CommandHandler('elegir_municipio', search_command_handler),
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