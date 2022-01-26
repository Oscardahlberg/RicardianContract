import socket
import jpysocket
import json
import requests

PORT = 49000
#Skapa en session och byt ut till din här!
session = "E159D282E2014CDBA40F680E659395B9"

def post(msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), PORT))
    s.send(jpysocket.jpyencode(msg))
    s.close()


def get(msg):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), PORT))
    s.send(jpysocket.jpyencode(msg))

    msg = s.recv(1024)
    msg = jpysocket.jpydecode(msg)
    print("Received: ", msg)
    s.close()
    
#Skapa en session!
def sessions():
    url = "http://localhost:8080/pm/api/sessions"
    headers = {'Content-Type': 'application/json'}
    body = json.dumps({"username" : "super", "password" : "super"})
    response = requests.post(url, headers = headers, data = body)
    print(response.json()["entity"])
    return response.json()["entity"]

#Skapa nod!
def createNode(name, type, desc, prop1, prop2):
    url ="http://localhost:8080/pm/api/nodes?session={}".format(session)
    headers = {'Content-Type': 'application/json'}
    body = json.dumps({
  "name": "{}".format(name),
  "type": "{}".format(type),
  "description": "{}".format(desc),
  "properties": [
    {
      "key": "{}".format(prop1),
      "value": "{}".format(prop2)
    }
  ]
}
)
    print(url)
    response = requests.post(url, headers = headers, data = body)
    print(response.json())

#Hämta nodens ID baserat på nodens namn
def getId(name):
    url = "http://localhost:8080/pm/api/nodes?session={}&name={}".format(session, name)
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers = headers)
    data = response.json()["entity"]
    nId = data[0]["id"]
    print(nId)
    return nId
