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


import requests
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


#----------------- Verificar alertas cerca del usuario-----------------


# Configura tu clave de API de OpenAI
client = OpenAI(api_key="sk-proj-FMwypGLECRWmeUgblRunT3BlbkFJZtkvoweoSVxjpXoemwz8")
#openai.api_key = "sk-proj-FMwypGLECRWmeUgblRunT3BlbkFJZtkvoweoSVxjpXoemwz8"
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

        # Coordenadas del usuario (obtén del tracker o usa coordenadas predeterminadas)
        user_location = (31.04, -92.63) #Emergencia
        #user_location = (31.04, -72.63) #SAVE

        # URL de la API de NOAA
        url = "https://api.weather.gov/alerts/active?urgency=Immediate&limit=500"

        try:
            # Obtener datos de la API
            response = requests.get(url)
            data = response.json()

            # Verificar que la API devolvió datos
            if "features" not in data:
                dispatcher.utter_message(text="No se encontraron alertas activas cercanas.")
                return []

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
                    event = properties.get("event", "Evento no especificado")
                    description = properties.get("description", "Descripción no disponible")

                    # Agregar la información al historial de conversación
                    conversation_history.append({
                        "role": "user",
                        "content": f"Se ha detectado una alerta cerca del usuario. Usa esta informacion para responder al usuario:\n"
                                   f"Lugar de la Emergencia: {area_desc}\n"
                                   f"Distancia del usuario al lugar de la emergencia: {distance:.2f} km\n"
                                   f"Emergency Type: {event}\n"
                                   f"Description: {description}\n"
                                   f"¿Cómo podemos ayudar al usuario, cual es el refugio mas cercano? Sigue la conversacion"
                    })

                    # Llamar a ChatGPT con el historial
                    chat_response = client.chat.completions.create(
                        model="gpt-4-0613",  #llamada al modelo de la cuenta de open ai
                        messages= conversation_history
                    )

                    # Obtener la respuesta del asistente
                    assistant_message = chat_response.choices[0].message.content

                    # Agregar la respuesta al historial
                    conversation_history.append({
                        "role": "assistant", "content": assistant_message
                    })

                    # Enviar la respuesta al usuario
                    dispatcher.utter_message(text=assistant_message)
                    return []

            # Si no hay alertas cercanas
            dispatcher.utter_message(response="utter_no_emergency_detect")
            return [FollowupAction("action_question_to_user_in_emergency")]

        except Exception as e:
            # Manejo de errores
            dispatcher.utter_message(text=f"Ocurrió un error al verificar las alertas: {str(e)}")
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

GOOGLE_API_KEY = ('AIzaSyBALG38xnhHEc7f68676YQDwxg5xiYOkNg')

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
