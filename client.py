import socket
import jpysocket
import json
import requests

PORT = 49000
# Skapa en session och byt ut till din här!
session = "43D39E76E4F94E0BAD39409E97521F83"


# Skapa en session!
def sessions():
    url = "http://localhost:8080/pm/api/sessions"
    headers = {'Content-Type': 'application/json'}
    body = json.dumps({"username": "super", "password": "super"})
    response = requests.post(url, headers=headers, data=body)
    print(response.json()["entity"])
    return response.json()["entity"]


# Skapa nod!
# Den sista variabeln är frivilig, ex: create_node("namn", "U", "desc...")
def create_node(name, type, desc, *argv):
    url = "http://localhost:8080/pm/api/nodes?session={}".format(session)
    headers = {'Content-Type': 'application/json'}
    if argv:
        body = json.dumps({
            "name": name,
            "type": type,
            "description": desc,
            "properties": [
                {
                    "key": argv[0],
                    "value": argv[1]
                }
            ]
        })
    else:
        body = json.dumps({
            "name": name,
            "type": type,
            "description": desc,
            "properties": []
        })

    response = requests.post(url, headers=headers, data=body)
    print(response.json())
    return response.json()["message"]


# Hämta nodens ID baserat på nodens namn
def get_id(name):
    url = "http://localhost:8080/pm/api/nodes?session={}&name={}".format(session, name)
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    data = response.json()["entity"]
    nId = data[0]["id"]

    print(response.json()["code"])
    return nId, response.json()["entity"][0]["msg"]


# Skapa ett assignment mellan en child nod och en parent nod
def make_assignment(node_name, group_name):
    node_id, msg = get_id(node_name)
    if not msg == "Success":
        return "Error getting node_id" + msg

    group_id, msg = get_id(group_name)
    if not msg == "Success":
        return "Error getting group_id" + msg

    url = "http://localhost:8080/pm/api/assignments?session=" + format(session)
    body = json.dumps({
        "childId": node_id,
        "parentId": group_id
    })
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=body)
    return print(response.json()["message"])
