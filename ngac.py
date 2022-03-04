import socket
import jpysocket
import json
import requests

import to_list

PORT = 49000
# Create a session for NGAC rest API
session = "7584FDDFA40148E6A0A5DA164D36C097"


# Method to create a new session!
def sessions():
    url = "http://localhost:8080/pm/api/sessions"
    headers = {'Content-Type': 'application/json'}
    body = json.dumps({"username": "super", "password": "super"})

    response = requests.post(url, headers=headers, data=body)
    print(response.json()["entity"])
    session = response.json()["entity"]
    return response.json()["entity"]


# Create a node in NGAC
# The last variable is not needed, ex: create_node("namn", "U", "desc...")
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


# Get the nodes Id based on its name
def get_id(name, *args):
    url = "http://localhost:8080/pm/api/nodes?session={}&name={}".format(session, name)
    headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)

    data = response.json()["entity"]
    if response.json()["message"] != "Success":
        return 0, response.json()["message"]

    if len(data) < 1:
        return 0, response.json()["message"]

    nId = data[0]["id"]

    if args:
        if args[0] == "full":
            print(response.json()["message"])
            return data, response.json()["message"]
    print(response.json()["message"])
    return nId, response.json()["message"]


# Create an assignment between a childnode and a parentnode
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


# Create an association, ex make_association("osci", "LTU_STUDENT", True, False)
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

# Get all associations connected to a User attribute node
def get_associations_UA_OA(node_name):
    node_id, msg = get_id(node_name)
    if msg != "Success":
        return "Error getting node_id" + msg

    url = "http://localhost:8080/pm/api/associations/" \
          "subjects/{}?session={}".format(node_id, session)
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)
    print(response.json())
    return to_list.parent_list(response.json()["entity"]), response.json()["message"]

# Get all associations connected to a Object attribute node
def get_associations_OA_UA(node_name):
    node_id, msg = get_id(node_name)
    if msg != "Success":
        return "Error getting node_id" + msg

    url = "http://localhost:8080/pm/api/associations?" \
          "targetId={}&session={}".format(node_id, session)
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)
    print(response.json())
    return to_list.child_list(response.json()["entity"]), response.json()["message"]

# Get all parent nodes connected to a node
def get_node_parents(node_id):
    url = "http://localhost:8080/pm/api/nodes/" \
          "{}/parents?&session={}".format(node_id, session)
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)
    print(response.json())
    return to_list.node_list(response.json()["entity"]), response.json()["message"]

# Get all child nodes connected to a node
def get_node_children(node_id):
    url = "http://localhost:8080/pm/api/nodes/" \
          "{}/children?&session={}".format(node_id, session)
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)
    print(response.json())
    return to_list.node_list(response.json()["entity"]), response.json()["message"]

# Get all nodes with the specified type
def get_nodes_with_type(node_type):
    if node_type not in ("U", "UA", "O", "OA", "S", "PC"):
        print("Wrong node type, has to be one of U, UA, O, OA, S, PC")
        return 0, "Wrong node type"

    url = "http://localhost:8080/pm/api/nodes?" \
          "type={}&session={}".format(node_type, session)
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)
    print(response.json())
    return to_list.node_list(response.json()["entity"]), response.json()["message"]

# Get the assignment between the child node and parent node
def get_assignment(child_name, parent_name):
    child_id, msg = get_id(child_name)
    if not child_id:
        return False, "Error getting node_id" + msg

    parent_id, msg = get_id(parent_name)
    if not parent_id:
        return False, "Error getting group_id" + msg

    url = "http://localhost:8080/pm/api/assignments?" \
          "session={}&childId={}&parentId={}".format(session, child_id, parent_id)
    print(url)
    headers = {'Content-Type': 'application/json'}

    response = requests.get(url, headers=headers)
    print(response.json())
    if response.json()["entity"]:
        return True, response.json()["message"]
    return False, response.json()["message"]
