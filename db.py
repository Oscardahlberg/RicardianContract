from ctypes import string_at
import re
from string import Template
from bson.json_util import object_hook
from pymongo import MongoClient
from datetime import datetime
from werkzeug import datastructures
from werkzeug.security import generate_password_hash
import uuid
import hashlib
from user import User
import json
from bson import ObjectId
import certifi

# Change this to your mongodb cluster (in case you want to use it) for you to see and modify the database
#client = MongoClient("mongodb+srv://oscar:test123@cluster0.6hczg.mongodb.net/myFirstDatabase?retryWrites=true&w=majority",
                     #ssl=True)
ca = certifi.where()
client = MongoClient("mongodb+srv://tony:tony@d0020e.5xsx8.mongodb.net/Nego2?retryWrites=true&w=majority", ssl=True,tlsCAFile = ca)


# This will allow you to access the databases, in case more databases are needed add them here, no need to create a
# struture a priori like SQL, when data is added to a non existing database it will create it.

nego2 = client.get_database("Nego2")
users_collection = nego2.get_collection("users")
access_collection = nego2.get_collection("access_permissions")
negotiations_collection = nego2.get_collection("negotiations")
templates_collection = nego2.get_collection("templates")
contracts_collection = nego2.get_collection("contracts")
# Write how to specify regarding the access giving permisions
data_collection = nego2.get_collection("datasets")


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId) or isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


# Run this function when you want to create a new user,
# you can also create a registration view in the api which call this function, is up to you.
def save_user(username, email, password, sign):
    password_hash = generate_password_hash(password)
    salt = uuid.uuid4().hex
    hashsign = hashlib.sha256(salt.encode() + sign.encode()).hexdigest() + ':' + salt
    user_id = users_collection.insert_one(
        {'username': username, 'email': email, 'password': password_hash, 'sign': hashsign})
    return user_id


# In case you want to create aditional templates you would need to modify and run this function.
def add_template():
    temp_type = 'single_buyer'
    temp = "Hereby I $seller authorize the access to $buyer for the following databases: "\
           "$data from $start_date to $end_date for the following roles $authorized_roles. "\
           "Seller signature $seller_sign, Buyer signature $buyer_sign"

    templates_collection.insert_one({'temp_type': temp_type, 'template': temp})


# Gets the user data, used for the login system
def get_user(username):
    user_data = users_collection.find_one({'username': username})
    return User(user_data['username'], user_data['email'], user_data['password'],
                user_data['sign']) if user_data else None


# Creates a new permission request and creates the first offer of the negotiation
def new_permi(username, item, st_date, end_date, role, offering):
    status = 'submitted'
    access_req = access_collection.insert_one(
        {'demander': username, 'provider': get_provider(item), 'creation_date': datetime.now(),
         'offer': offering, 'request_details':
             {'item': item, 'start_date': st_date, 'end_date': end_date, 'role': role}, 'status': status}).inserted_id

    # Add new nego
    offer(access_req, username, item, st_date, end_date, role, offering)
    return access_req


# Function that creates orders
def offer(req_id, username, item, st_date, end_date, role, offering):
    dataset = data_collection.find_one({'name': item})
    negotiations_collection.insert_one(
        {'req_id': ObjectId(req_id), 'demander': username, 'provider': get_provider(item),
         'creation_date': datetime.now(), 'offer': offering, 'request_details':
             {'item_id': dataset['_id'], 'item': item, 'start_date': st_date, 'end_date': end_date, 'role': role}})


# This will get the provider of the specified resource name
def get_provider(name):
    dataset = data_collection.find_one({'name': name})
    owner = dataset['owner']
    return owner


# changes the status of the access permission depending on what is sent and who sends it.
def change_status(req_id, flag, user):
    # The hard coded posibilities is the acceptance and rejection
    access_request = get_neg(req_id)
    if flag == 'accept':
        access_collection.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'accepted'}})
        print('accepted')
    elif flag == 'reject':
        access_collection.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'rejected'}})
        print('rejected')
    else:
        if user == get_provider(access_request['request_details']['item']):
            access_collection.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'counter_offer'}})
            print('counter offer')
        else:
            access_collection.update_one({'_id': ObjectId(req_id)}, {'$set': {'status': 'new_offer'}})
            print('new offer')
    return 'finished'


# This is used to add new datasets to the database
def new_dataset(name, owner, read, modify, delete):
    data_collection.insert_one(
        {'name': name, 'owner': owner, 'permissions': {'read': read, 'modify': modify, 'delete': delete}})


# Gets the access permission data based on the id
def get_neg(req_id):
    neg = access_collection.find_one({'_id': ObjectId(req_id)})
    return neg


# Gets the template based on the name
def get_template(temp_type):
    temp_id = templates_collection.find_one({'temp_type': temp_type})
    return temp_id['template']


# Get the signature of the user by its username
def get_sign(uid):
    user_info = users_collection.find_one({'username': uid})
    return user_info['sign']


# Updates the access permission
def update(req_id, offer, item, start_date, end_date, role):
    access_collection.update_one({'_id': ObjectId(req_id)}, {'$set': {'offer': offer,
                                                                      'request_details.item': item,
                                                                      'request_details.start_date': start_date,
                                                                      'request_details.end_date': end_date,
                                                                      'request_details.role': role}})


# Signs the contract and returns it
def sign_contract(req_id):
    neg = access_collection.find_one({'_id': ObjectId(req_id)})
    temp_type = "single_buyer"  # currently hardcoded
    temp = Template(get_template(temp_type))
    d = dict(seller=neg['provider'], buyer=neg['demander'], data=neg['request_details']['item'],
             start_date=neg['request_details']['start_date'], end_date=neg['request_details']['end_date'],
             authorized_roles=neg['request_details']['role'], seller_sign=get_sign(neg['provider']),
             buyer_sign=get_sign(neg['demander']))
    signed_c = temp.safe_substitute(d)
    contracts_collection.insert_one(
        {'req_id': ObjectId(req_id), 'provider': neg['provider'], 'demander': neg['demander'],
         'creation_date': datetime.now(), 'contract': signed_c})
    return signed_c
