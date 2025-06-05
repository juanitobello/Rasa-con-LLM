# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import FollowupAction
from rasa_sdk.events import SlotSet

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut


import requests
import json
from geopy.distance import geodesic
import openai
from openai import OpenAI

import google.generativeai as genai



class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World! from Actions")

        return []


# -----------------------    GLOBAL VARIABLES ------------------------------------------------------------------------------------------------
GLOBAL_DESCRIPTION = ""
GLOBAL_INSTRUCTION = ""
GLOBAL_POLIGONO_EMERGENCY=""
event_type=""
# Coordenadas del usuario (obtén del tracker o usa coordenadas predeterminadas)
#user_location = (31.04, -92.63) #Emergencia


#user_locationYES= (34.33326608179874, -96.05193590073877)

#Ejemplo Listo:
user_location= ""
#user_location = (31.04, -72.63) #SAVE



def ejmplos_case(x):
    match x:
        case 1:
            print("Ejemplo Usuario fuera pero en situacion de peligro:")
            user_location= (32.218962876030375, -95.49631395372396)

            return "uno"
        case 2:
            return "dos"
        case _:
            return "desconocido"





#---------------------------FUNCIONES CHEVERES-----------------------------------------------------------------------------------------

def get_coordenates_from_address(address):
    geolocator = Nominatim(user_agent="mi_app_unica_12345")
    location = geolocator.geocode(str(address))

    if location:
        print(location.latitude, location.longitude)
        return location
    else:
        print("No se encontró la dirección")
        return []
    return[]


def get_address_from_coordinates(user_location):
    """
    Convierte coordenadas geográficas a una dirección legible.
    
    Parámetros:
        user_location (tuple): Una tupla con latitud y longitud (lat, lon)
    
    Retorna:
        str: Dirección en texto o un mensaje de error si falla.
    """
    try:
        geolocator = Nominatim(user_agent="emergency_assistant")
        location = geolocator.reverse(user_location, timeout=10)
        if location and location.address:
            return location.address
        else:
            return "Dirección no disponible para estas coordenadas."
    except GeocoderTimedOut:
        return "Error: el servicio de geolocalización ha tardado demasiado."
    except Exception as e:
        return f"Error al obtener la dirección: {str(e)}"
    
def extraer_direccion(cadena):
    # Divide la cadena en partes usando la primera coma
    partes = cadena.split(",", 1)
    # Si hay al menos una coma, devuelve la parte después de ella (elimina espacios al inicio)
    if len(partes) > 1:
        return partes[1].strip()
    else:
        return cadena  # Si no hay coma, devuelve la cadena completa


# def mostrarAlertaenMapa(data, event):
#     polygon_coords = [
#     [lat, lon] for lon, lat in data["geometry"]["coordinates"][0]
#     ]
#     # URL del backend Flask
#     flask_url = "http://192.168.137.1:5000/alerta-poligono"

#     # JSON para enviar
#     payload = {
#         "poligono": polygon_coords,
#         "tipo":  event,
#         "descripcion": "Tornado detected in the area",
#         "usuario": "Juan Francisco"
#     }

#     # Enviar POST
#     response = requests.post(flask_url, json=payload)

#     if response.status_code == 200:
#         print("Polígono enviado al mapa correctamente.")
#     else:
#         print(f"Error al enviar polígono: {response.status_code}")

#     return


def mostrarAlertaenMapa(data, event):
    try:
        # Asegurar que `data` sea un diccionario, no un string JSON
        if isinstance(data, str):
            data = json.loads(data)

        # Extraer coordenadas en formato [lat, lon]
        polygon_coords = [
            [lat, lon] for lon, lat in data["coordinates"][0]
        ]
        polygon_coords = [[32.3, -95.45], [32.33, -95.4599999], [32.36, -95.45], [32.4799999, -95.59], [32.56, -95.59], [32.690000000000005, -94.66], [32.21000000000001, -94.58], [32.13000000000001, -94.99], [32.13000000000001, -95.4599999], [32.14000000000001, -95.47], [32.20000000000001, -95.4599999], [32.24000000000001, -95.49], [32.25000000000001, -95.47], [32.3, -95.45]]
        # URL del backend Flask
        flask_url = "http://192.168.137.1:5000/alerta-poligono"

        # Crear el JSON a enviar
        payload = {
            "poligono": polygon_coords,
            "tipo": event,
            "descripcion": "Tornado detected in the area",
            "usuario": "Juan Francisco"
        }

        # Enviar POST
        response = requests.post(flask_url, json=payload)

        if response.status_code == 200:
            print("✅ Polígono enviado al mapa correctamente.")
        else:
            print(f"❌ Error al enviar polígono: {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ Error en mostrarAlertaenMapa: {str(e)}")
    return polygon_coords



def llamada_a_chtGPT(prompt):
    # Llamar a ChatGPT con el historial
    chat_response = client.chat.completions.create(
        model="gpt-4-0613",  #llamada al modelo de la cuenta de open ai
        messages= [
            {"role": "system", "content": prompt}
        ],
    )

    # Obtener la respuesta del asistente
    assistant_message = chat_response.choices[0].message.content

    return assistant_message

def text_a_json(content):
    try:
        json_result= json.loads(content)
    except json.JSONDecodeError as json_err:
        print("❌ Error al convertir la respuesta en JSON:", json_err)
        print("Respuesta cruda del modelo:", content)
        return {
            "Refugios": [],
            "evitar": [],
            "recomendaciones": [],
            "error": "Respuesta malformateada por el modelo"
        }
    return json_result




def enviar_datos_a_flask_para_ruta(user_location, shelter_location, poligono):
    if isinstance(poligono, str):
            poligono = json.loads(poligono)

    # Extraer coordenadas en formato [lat, lon]
    polygon_coords = [
        [lat, lon] for lon, lat in poligono["coordinates"][0]
    ]

    flask_url = "http://192.168.137.1:5000/calcular-ruta"  # Flask endpoint

    # payload = {
    #     "origen": list(user_location),
    #     "destino": list(shelter_location),
    #     "poligono": polygon_coords  # [[lat, lon], [lat, lon], ...]
    # }
    payload = {
        "user_location": list(user_location),
        "shelter_location": list(shelter_location),
        "polygon": polygon_coords
    }

    try:
        response = requests.post(flask_url, json=payload)
        if response.status_code == 200:
            print("Ruta solicitada correctamente.")
        else:
            print(f"Error al enviar datos al servidor Flask: {response.status_code}")
    except Exception as e:
        print(f"Error de conexión con Flask: {str(e)}")





#---------------------------FIN funciones---------------------------------------------



#----------------- Verificar alertas cerca del usuario-----------------

# Configura tu clave de API de OpenAI

#openai.api_key = ""
promptGPT=""" 
Eres un asistente experto en emergencias naturales con acceso a información geoespacial en tiempo real. Tu función principal es ayudar a los usuarios a identificar rutas de evacuación, localizar refugios cercanos y brindar orientación sobre desplazamientos seguros durante desastres naturales. 

Pa1ra cada solicitud:
- Recibirás la ubicación del usuario.
- Utiliza datos geoespaciales y mapas en tiempo real para proporcionar direcciones precisas.
- Verifica siempre la seguridad de las rutas antes de sugerirlas, evitando áreas peligrosas o afectadas.
- Considera factores como tráfico, cierres de carreteras y condiciones climáticas al ofrecer recomendaciones.

Recuerda:
- Mantén un tono calmado y claro, indicando pasos fáciles de seguir.
- Si la situación es crítica, sugiere contactar a servicios de emergencia locales.
- Siempre pregunta por la ubicación del usuario y el tipo de emergencia para proporcionar la mejor asistencia posible.

Ejemplo de respuesta:
“Detecto una alerta de huracán en tu área. ¿Estás en un lugar seguro?”
“Hay un incendio forestal/deslizamiento de tierra cerca de tu ubicación. ¿Necesitas ayuda para evacuar?”
“Alerta de inundación/tsunami en tu área. Es crítico que te muevas a un terreno más alto.”
“Un terremoto se ha detectado cerca de ti. ¿Estás bien? ¿Necesitas asistencia para evacuar?”
"Te recomiendo evacuar hacia el refugio más cercano, ubicado a 2 km al norte en la calle Main Street. Hay reportes de inundaciones al sur, así que evita esa ruta. ¿Te gustaría recibir instrucciones paso a paso para llegar al refugio?"


"""



# Historial de conversación para mantener el contexto
conversation_history = [
    {"role": "system", "content": promptGPT}
]

class CheckNearbyAlertAndChatGPT(Action):
    def name(self) -> str:
        return "action_check_alert_and_chatgpt"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        global conversation_history      
        global GLOBAL_DESCRIPTION
        global GLOBAL_INSTRUCTION
        global GLOBAL_POLIGONO_EMERGENCY
        global event_type

        # URL de la API de NOAA
        url = "https://api.weather.gov/alerts/active?urgency=Immediate"

        try:
            # Obtener datos de la API
            response = requests.get(url)
            data = response.json()

            # Verificar que la API devolvió datos
            if "features" not in data:
                dispatcher.utter_message(response="utter_nooa_unavailable")
                return [FollowupAction("action_question_to_user_in_emergency")]

            # Iterar sobre las alertas para encontrar una cercana
            for feature in data["features"]:
                geometry = feature.get("geometry")
                if not geometry or geometry["type"] != "Polygon":
                    continue

                # Obtener la primera coordenada del polígono
                coordinates = geometry["coordinates"][0][0]  # Primer punto del polígono
                polygon_point = (coordinates[1], coordinates[0])  # Formato (latitud, longitud)

                # Calcular la distancia entre el usuario y el primer punto del polígono
                distance = geodesic(user_location, polygon_point).kilometers

                if distance < 20:
                    # Recuperar la información de la alerta
                    properties = feature.get("properties", {})
                    area_desc = properties.get("areaDesc", "Descripción no disponible")
                    event_type = properties.get("event", "Evento no especificado")
                    GLOBAL_DESCRIPTION = properties.get("description", "Descripción no disponible")
                    GLOBAL_INSTRUCTION = properties.get("instruction","No evacuar")
                    #POLIGONO_EMERGENCY=geometry.get("geometry")
                    #GLOBAL_POLIGONO_EMERGENCY=json.dumps(POLIGONO_EMERGENCY)
                    GLOBAL_POLIGONO_EMERGENCY = json.dumps(geometry)  # geometry ya es el objeto


                    # Agregar la información al historial de conversación
                    user_address= get_address_from_coordinates(user_location)
                    conversation_history.append({
                        "role": "user",
                        "content": f"Se ha detectado una alerta cerca del usuario. Usa esta informacion para responder al usuario:\n"
                                   f"User location:{user_address}"
                                   f"Lugar de la Emergencia: {area_desc}\n"
                                   f"Distancia del usuario al lugar de la emergencia: {distance:.2f} km\n"
                                   f"Emergency Type: {event_type}\n"
                                   f"Description: {GLOBAL_DESCRIPTION}\n"
                                   f"Instrucciones para el usuario: {GLOBAL_INSTRUCTION}"
                                   f"¿Cómo podemos ayudar al usuario, cual es el refugio mas cercano? Sigue la conversacion"
                    })

                    # # Llamar a ChatGPT con el historial
                    # chat_response = client.chat.completions.create(
                    #     model="gpt-4-0613",  #llamada al modelo de la cuenta de open ai
                    #     messages= conversation_history
                    # )

                    # # Obtener la respuesta del asistente
                    # assistant_message = chat_response.choices[0].message.content

                    # # Agregar la respuesta al historial
                    # conversation_history.append({
                    #     "role": "assistant", "content": assistant_message
                    # })
                    assistant_message='ChatGPT perfecto'
                    # Enviar la respuesta al usuario
                    dispatcher.utter_message(text=assistant_message)
                    mostrarAlertaenMapa(GLOBAL_POLIGONO_EMERGENCY,event_type)
                    return [FollowupAction("action_button_make_route")]

            # Si no hay alertas cercanas
            dispatcher.utter_message(response="utter_no_emergency_detect")
            return [FollowupAction("action_question_to_user_in_emergency")]

        except Exception as e:
            # Manejo de errores
            print(str(e))
            dispatcher.utter_message(text=f"Ocurrió un error al verificar las alertas: {str(e)}")
            return [FollowupAction("action_question_to_user_in_emergency")]
        


class ActionButtonMakeRoute(Action):

    def name(self) -> Text:
        return "action_button_make_route"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        buttons=[
            {"payload":'/int_make_route', "title": "Make route on map."},
        ]
        
        dispatcher.utter_message(
            text="Press the button to see route:", 
            buttons=buttons)

        return []





class ActionMakeRouteInstruction(Action):

    def name(self) -> Text:
        return "action_make_route_instructions"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # prompt_json_extraction_shelter_location = f"""
        # Eres un asistente especializado en análisis de emergencias naturales. A partir de los textos de descripción e instrucciones de una alerta oficial, tu tarea es identificar:

        # 1. Refugios sugeridos o mencionados, incluyendo nombre completo y dirección completa (formato: nombre, calle y número, ciudad, estado).
        # 2. Zonas, calles, avenidas, carreteras o sectores que afectados.
        # 3. Recomendaciones clave para el usuario derivadas de la información disponible.

        # Formato de salida esperado (en JSON):

        # {{
        # "Refugios": [],
        # "zonas_afectadas": [],
        # "recomendaciones": []
        # }}

        # Reglas:
        # - Si no hay información clara sobre un refugio suguiere un refugio cerca del usuario en el formato nombre, calle y número, ciudad, estado.
        # - No inventes direcciones. 
        # - Solo responde con el JSON estructurado.

        # Descripción:
        # {GLOBAL_DESCRIPTION}

        # Instrucciones:
        # {GLOBAL_INSTRUCTION}

        # Por favor, analiza y responde con el JSON estructurado.
        # """
        desde = get_address_from_coordinates(user_location)
        prompt_json_extraction_shelter_location= f"""
        Eres un asistente especializado en emergencias naturales.
        A partir de la ubicación exacta del usuario y el texto de una alerta oficial, tu tarea es identificar la dirección de un refugio cercano al usuario en caso de emergencia.

        Formato de respuesta obligatorio:
        nombre, calle y número, ciudad, estado

        No proporciones explicaciones ni contexto adicional. Solo responde con la dirección en el formato solicitado.

        Ubicación del usuario: {desde}
        Texto de la alerta:
        {GLOBAL_DESCRIPTION}
        """
        
        #print(prompt_json_extraction_shelter_location)
        
    
        #Crear funcion para extrar ubicacion del refugio y obtener coordenadas 
        # ahora si con las coordenadas de inicio y fin del usuario 
        #crear funcion para crear ruta Enviar post al server Geo
        #refugio= "Buscando ubicacion"    



        # shelter_location=[]
        # while isinstance(shelter_location, list):
        #     refugio_address=llamada_a_chtGPT(prompt_json_extraction_shelter_location) #texto de chatgpt
        #     shelter_location=get_coordenates_from_address(extraer_direccion(refugio_address))
            
        # print((shelter_location.latitude))
        refugio_address="500-598 Wildewood Dr, Chandler, TX 75758, Estados Unidos"
        shelter_location= (32.22991, -95.496589)
        enviar_datos_a_flask_para_ruta(user_location, shelter_location, GLOBAL_POLIGONO_EMERGENCY)


        dispatcher.utter_message(text=f"From: {desde} to: {refugio_address}")
        dispatcher.utter_message(response= "utter_show_route")
        
        return []




##------------------------------------Actions Emergency NO in realtime------------------------------

class ActionQuestionToUserAreInEmergency(Action):

    def name(self) -> Text:
        return "action_question_to_user_in_emergency"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        buttons=[
            {"payload":'/int_i_am_in_emergency{"emergency_state":"True"}', "title": "I am in Emergency"},
            {"payload":'/int_notify_no_emergency{"emergency_state":"False"}', "title": "No Emergency"},
        ]
        
        dispatcher.utter_message(
            text="Are you in a Emergency?\n(choose the option)", 
            buttons=buttons)
        

        return []

class ActionChooseEmergencyType(Action):

    def name(self) -> Text:
        return "action_choose_emergency_type"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        buttons=[
            {"payload":'/int_notify_hurricane_or_thunderstorm{"tipo_emergencia":"hurricane"}', "title": "Hurricane or Thunderstorm"},
            {"payload":'/int_notify_forest_fire{"tipo_emergencia":"forest fire"}', "title": "Forest Fire"},
            {"payload":'/int_notify_earthquake{"tipo_emergencia":"earthquake"}', "title": "Earthquake"},
            {"payload":'/int_notify_flood_or_tsunami{"tipo_emergencia":"flood or Tsunami"}', "title": "Flood or Tsumani"},
        ]
        
        dispatcher.utter_message(text=f"What is your Emergency?\n(choose the option)", buttons=buttons)
    
        return []


#Gemini Call With chat history--------------------------------------------
promptGemini = """ 
Eres un asistente de emergencia con especialización en manejo emocional durante desastres naturales. Tu objetivo es ayudar a los usuarios a mantener la calma y brindar información clara y tranquilizadora. Ten en cuenta que las personas pueden estar experimentando ansiedad o miedo extremo.
Para cada respuesta:
- Utiliza un tono empático, reconociendo la situación y ofreciendo apoyo emocional antes de brindar instrucciones.
- Evita sobrecargar al usuario con demasiada información. Da un solo paso a la vez y verifica si necesitan más ayuda antes de continuar.
- Nunca uses lenguaje alarmante o que pueda aumentar el pánico.
Contexto:
"""



genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class ActionCallGemini(Action):
    def name(self) -> Text:
        return "action_call_gemini_for_emergency"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Obtén el historial de la conversación
        tipo_emergencia = " el tipo de emergencia es:  " + tracker.get_slot("tipo_emergencia") + " responder acorde al historial:\n"
        conversation_history = "" + tipo_emergencia
        for event in tracker.events:
            if event['event'] == 'user':
                conversation_history += f"User: {event['text']}\n"
            elif event['event'] == 'bot':
                conversation_history += f"Bot: {event['text']}\n"

        # Obtén la entrada del usuario
        user_input = tracker.latest_message['text']

        # Construye el prompt con el historial
        prompt = promptGemini + f"Historial de la conversación: {conversation_history}\nUsuario: {user_input}\nGemini:"

        # Llama a la API de Gemini
        response = model.generate_content(prompt)

        # Envía la respuesta de Gemini al usuario
        dispatcher.utter_message(text=response.text)

        # Verifica si el usuario está a salvo
        if tracker.get_slot("safe_status"):
            dispatcher.utter_message(text="Gracias por confirmar que estás a salvo. Si necesitas más ayuda, házmelo saber.")
            return [SlotSet("safe_status", True)]

        # Pide al usuario confirmar si está a salvo
        dispatcher.utter_message(text="¿Estás a salvo ahora? Por favor confirma.")
        return []

class ActionCheckSafetyStatus(Action):
    def name(self) -> Text:
        return "action_check_safety_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if tracker.get_slot("safe_status"):
            dispatcher.utter_message(text="Gracias por confirmar que estás a salvo. Cuídate mucho.")
            return []

        # Llama nuevamente a la acción para continuar brindando asistencia
        return [FollowupAction("action_call_gemini_for_emergency")]
