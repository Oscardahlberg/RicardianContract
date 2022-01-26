import socket
import jpysocket
import requests
import json

PORT = 49000


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

def sessions():
    url = "http://localhost:8080/pm/api/sessions"
    headers = {'Content-Type': 'application/json'}
    body = json.dumps({"username" : "super", "password" : "super"})
    response = requests.post(url, headers = headers, data = body)
    return response.json()["entity"]

def createNode(name, type, desc, prop1, prop2):
    url ="http://localhost:8080/pm/api/nodes?session=E159D282E2014CDBA40F680E659395B9"
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

#Hämtar nod id baserat på nodens namn
def getId(name):
    url = "http://localhost:8080/pm/api/nodes?session=E159D282E2014CDBA40F680E659395B9&name={}".format(name)
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers = headers)
    data = response.json()["entity"]
    nid = data[0]["id"]
    print(nid)