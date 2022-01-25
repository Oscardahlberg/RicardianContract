from datetime import datetime
from re import S

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS

import to_list
from db import get_user, get_neg, new_permi, offer, change_status, sign_contract, update, save_user, data_collection, \
    new_dataset, users_collection, negotiations_collection, access_collection, get_template, add_template
import client

app = Flask(__name__)

cors = CORS(app)
app.secret_key = "sfdjkafnk"
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


# User login receives form params username and password


@app.route('/')
def home(*argv):
    msg = argv[0] if argv else ""

    name = ""
    user_id = ""
    if current_user.is_authenticated:
        name = current_user.username
        try:
            user_id = users_collection.find({"username": "" + name})[0]["_id"]
        except Exception as e:
            print(e)
            return e

    return render_template("index.html", user=name, user_id=user_id, msg=msg)


@app.route('/login')
def login_page():
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return home("The user {} is already authenticated".format(current_user.username))
        # return {"message": "The user {} is already authenticated".format(current_user.username)}, 200

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)

            return home("User {} has been authenticated".format(str(current_user.username)))
            # return {"message": "User {} has been authenticated".format(str(current_user.username))}, 200
        else:
            message = 'Failed to login!'
    return home(message)


# Create a new user

@app.route('/create')
def create_page():
    return render_template("createAcc.html")


@app.route('/create', methods=['POST'])
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        try:
            if users_collection.find_one({"username": username}):
                return home("User with that name already exists")

            email = request.form.get('email')
            password = request.form.get('password')
            save_user(username, email, password, password)
        except Exception as e:
            print(e)
            return e

        return home("User successfully created")
        # return {'message': "User successfully created"}, 200


# User logout

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return home("You have logged out")


# Start negotiation:
# To be done: Verify validity of inputs, for example, x permision for y database is possible

@app.route("/<user_id>/nego")
@login_required
def user_negotiations(user_id):
    try:
        nego_as_demander = access_collection.find(
            {"demander": users_collection.find_one({"_id": ObjectId(user_id)})["username"]})
        demander_list = to_list.access_perms_to_list(nego_as_demander, ("submitted", "counter_offer", "new_offer"))

        nego_as_provider = access_collection.find(
            {"provider": users_collection.find_one({"_id": ObjectId(user_id)})["username"]})
        provider_list = to_list.access_perms_to_list(nego_as_provider, ("submitted", "counter_offer", "new_offer"))

    except Exception as e:
        print(e)
        return e

    combined_list = demander_list + provider_list
    if not len(combined_list):
        return render_template("user_nego.html", title="No negotiations")

    return render_template("user_nego.html", nego_list=combined_list,
                           title="Pending negotations", user=current_user.username)


@app.route("/<user_id>/completed")
@login_required
def user_completed_negosiations(user_id):
    try:
        nego_as_demander = access_collection.find(
            {"demander": users_collection.find_one({"_id": ObjectId(user_id)})["username"]})
        demander_list = to_list.access_perms_to_list(nego_as_demander, ("accepted", "rejected"))

        nego_as_provider = access_collection.find(
            {"provider": users_collection.find_one({"_id": ObjectId(user_id)})["username"]})
        provider_list = to_list.access_perms_to_list(nego_as_provider, ("accepted", "rejected"))
    except Exception as e:
        print(e)
        return e

    combined_list = demander_list + provider_list
    if not len(combined_list):
        return render_template("user_nego.html", title="No completed negotiations")

    return render_template("user_nego.html", nego_list=combined_list, title="Completed negotiations",
                           user=current_user.username)


@app.route("/negotiate/<data_id>/create")
@login_required
def new_nego(data_id):
    return render_template("nego.html", data_id=data_id)


@app.route("/negotiate/<data_id>/submit", methods=['POST'])
@login_required
def new_nego_req(data_id):
    try:
        data_name = data_collection.find_one({"_id": ObjectId(data_id)})["name"]
        st_date = request.form.get('st_date')
        end_date = request.form.get('end_date')
        role = request.form.get('role')
        offering = request.form.get('offering')
        # The following function may be changed to iterate if multiple roles are requested

        new_permi(current_user.username, data_name, st_date, end_date, role, offering)

        return home("A negotation has been created")
        # return {"message": "The negotiation with id {} has been created".format(str(neg_id))}, 200
    except Exception as e:
        print(e)


@app.route("/negotiate/<req_id>/respond")
@login_required
def neg_page(req_id):

    try:
        neg = get_neg(req_id)
        neg_info = to_list.access_perm_to_list(neg)

        return render_template("counter_nego.html",
                               req_id=neg_info[0],
                               demander=neg_info[1],
                               date=neg_info[3],
                               offer=neg_info[4],
                               item=neg_info[5],
                               start_date=neg_info[6],
                               end_date=neg_info[7],
                               role=neg_info[8])
    except Exception as e:
        print(e)
        return e


# Negotiation or back and forth of proposals:
# To be done: Verify that new proposal is different to
# the previous one and that the porposer is different from the one who proposed the last

@app.route("/negotiate/<req_id>/respond", methods=['GET', 'POST'])
@login_required
def neg(req_id):
    try:
        req = get_neg(req_id)
    except Exception as e:
        print(e)
        return e

    if request.method == 'POST':
        if current_user.username in (req['provider'], req['demander']):
            if req['status'] not in ('accepted', 'rejected'):
                item = request.form.get('item')
                st_date = request.form.get('st_date')
                end_date = request.form.get('end_date')
                role = request.form.get('role')
                offering = request.form.get('offering')
                offer(ObjectId(req_id), current_user.username, item, st_date, end_date, role, offering)
                update(req_id, offering, item, st_date, end_date, role)
                change_status(req_id, 1, current_user.username)
                return home("New offer has been submitted")
                # return {"message": "New offer submited for request with id {}".format(str(req['_id']))}, 200
            else:
                return home("No more offers can be made")
                # return {"message": "The negotiation {} has concluded no more offers can be made".format(
                #    str(req['_id']))}, 403
        else:
            return home("You are not part of the current negotiation")
            # return {"message": 'You are not part of the current negotiation'}, 403


# Only accesible to the owner of such resource, this route accepts the negotiation and begins the contract signing
@app.route("/negotiate/<req_id>/accept", methods=['GET'])
@login_required
def accept(req_id):
    try:
        req = get_neg(req_id)
        if current_user.username in (req['provider'] or req['demander']):
            change_status(req_id, 'accept', current_user.username)
            s = sign_contract(req_id)
            # Add function for contract writing
            return home("The negotiation with id {} has been accepted.")

        else:
            return home("You are not authorized to perform this task")
    except Exception as e:
        print(e)
        return e


# Only accesible to the owner of such resource, this route cancels the negotiation.
@app.route("/negotiate/<req_id>/cancel", methods=['GET'])
@login_required
def cancel(req_id):
    try:
        req = get_neg(req_id)
        if current_user.username == req['provider']:
            print(req["provider"])
            change_status(req_id, 'reject', current_user.username)
            print(req["provider"])
            return home("The contract has been rejected")
            # return {"message": "The negotiation with id {} has been reject".format(str(req['_id']))}, 200
        else:
            return home("You are not authorized to perform this task")
            # return {"message": 'You are not authorized to perform this task'}, 403
    except Exception as e:
        print(e)
        return e


@app.route("/new_data")
@login_required
def new_data_page():
    return render_template("new_dataset.html")


# Only accesible to the owner of such resource, this route cancels the negotiation.
@app.route("/new_data", methods=['POST'])
@login_required
def new_data():
    try:
        name = request.form.get('data_name')

        if data_collection.find_one({"name": name}):
            return home("Data with that name already exists")

        can_read = True if request.form.get('can_read') == 'Yes' else False
        can_modify = True if request.form.get('can_mod') == 'Yes' else False
        can_delete = True if request.form.get('can_del') == 'Yes' else False

        new_dataset(name, current_user.username, can_read, can_modify, can_delete)

        return home("New dataset has been created")
        # return {"message": "New dataset has been created"}, 200
    except Exception as e:
        print(e)
        return e


@app.route("/search_data")
def data_page():
    try:
        return render_template("datasets.html",
                               data_list=to_list.data_to_list(data_collection.find()),
                               title="Available data for contract",
                               username=current_user.username)
    except Exception as e:
        print(e)
        return e


@app.route("/<user_id>/data")
def users_data_page(user_id):
    try:
        user_data = data_collection.find({"owner": users_collection.find_one({"_id": ObjectId(user_id)})["username"]})
        return render_template("datasets.html",
                               data_list=to_list.data_to_list(user_data),
                               title="Data owned by: " + current_user.username,
                               username=current_user.username)
    except Exception as e:
        print(e)
        return e


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    try:
        get_template("single_buyer")
    except TypeError as a:
        add_template()
    app.run(host='0.0.0.0', debug=True)
