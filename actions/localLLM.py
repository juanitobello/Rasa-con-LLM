import requests

url = "http://192.168.137.1:11434/api/generate"
data = {
    "model": "IAemergencias3",
    "prompt": "How to create an evacuation plan?",
    "stream": False
}
texto_a_leer= ''
response = requests.post(url, json=data)
texto_a_leer = texto_a_leer + response.json()["response"] 
print(response.json()["response"])