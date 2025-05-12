import requests
from geopy.distance import geodesic

# Coordenadas del usuario (latitud, longitud)
#user_location = (29.07, -82.39)
user_location = (31.04, -92.63)

# URL de la API
url = "https://api.weather.gov/alerts/active?urgency=Immediate&limit=500"

# Obtener datos de la API
response = requests.get(url)
data = response.json()

# Verificar que la API devolvió datos
if "features" not in data:
    print("No se encontraron datos en la respuesta de la API.")
    exit()

# Iterar sobre las alertas para calcular la distancia y recuperar el área si está cerca
for feature in data["features"]:
    # Verificar que la alerta tenga geometría y coordenadas
    geometry = feature.get("geometry")
    if not geometry or geometry["type"] != "Polygon":
        continue

    # Obtener la primera coordenada del polígono
    coordinates = geometry["coordinates"][0][0]  # Primer punto del polígono
    polygon_point = (coordinates[1], coordinates[0])  # Formato (latitud, longitud)

    # Calcular la distancia entre la ubicación del usuario y el primer punto del polígono
    distance = geodesic(user_location, polygon_point).kilometers

    # Si la distancia es menor a 20 km, recuperar el área
    if distance < 20:
        area_desc = feature["properties"].get("areaDesc", "Descripción no disponible")
        print(f"El área {area_desc} está a {distance:.2f} km del usuario.")
    

