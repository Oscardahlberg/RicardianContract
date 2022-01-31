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
def create_node(node_name, node_type, desc, *argv):
    url = "http://localhost:8080/pm/api/nodes?session={}".format(session)
    headers = {'Content-Type': 'application/json'}
    if argv:
        body = json.dumps({
            "name": node_name,
            "type": node_type,
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
            "name": node_name,
            "type": node_type,
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
    if response.json()["message"] != "Success":
        return 0, response.json()["message"]

    if len(data) < 1:
        return 0, "Success"

    nId = data[0]["id"]

    print(response.json()["message"])
    return nId, response.json()["message"]


# Skapa ett assignment mellan en child nod och en parent nod
def make_assignment(node_name, group_name):
    node_id, msg = get_id(node_name)
    if msg != "Success":
        return "Error getting node_id" + msg

    group_id, msg = get_id(group_name)
    if msg != "Success":
        return "Error getting group_id" + msg

    url = "http://localhost:8080/pm/api/assignments?session=" + format(session)
    body = json.dumps({
        "childId": node_id,
        "parentId": group_id
    })
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=body)
    print(response.json()["message"])
    return response.json()["message"]


# Gör en association, ex make_association("osci", "LTU_STUDENT", True, False)
def make_association(user_group_name, data_group_name, r, w):
    user_group_id, msg = get_id(user_group_name)
    if msg != "Success":
        return "Error getting node_id" + msg

    data_group_id, msg = get_id(data_group_name)
    if msg != "Success":
        return "Error getting group_id" + msg

    ops_list = []
    if r:
        ops_list.append("read")
    if w:
        ops_list.append("write")

    url = "http://localhost:8080/pm/api/associations?session=" + format(session)
    body = json.dumps({
        "uaId": user_group_id,
        "targetId": data_group_id,
        "ops": ops_list
    })
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=body)
    print(response.json())
    return response.json()["message"]


def get_associations(node_name):
    node_id, msg = get_id(node_name)
    if msg != "Success":
        return "Error getting node_id" + msg

    url = "http://localhost:8080/pm/api/associations?" \
          "session={}&targetId={}".format(session, node_id)
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)
    print(response.json())
    return response.json()["entity"], response.json()["message"]


# Kollar om username har en nod som heter username_seller
def is_seller(username):
    seller_id, msg = get_id(username + "_seller")
    if seller_id == 0:
        return "no nodes found"
    return msg
