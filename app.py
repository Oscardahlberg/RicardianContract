from datetime import datetime, date
from re import S

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS

from flask_wtf import FlaskForm
from wtforms import SubmitField, DateField, StringField
from flask_bootstrap import Bootstrap
from flask_datepicker import datepicker

import to_list
from db import get_user, get_neg, new_permi, offer, change_status, sign_contract, update, save_user, data_collection, \
    new_dataset, users_collection, access_collection, get_template, add_template, negotiations_collection
import client
from flask_navigation import Navigation

app = Flask(__name__)
nav = Navigation(app)
dp = datepicker(app)
Bootstrap(app)


cors = CORS(app)
app.secret_key = "sfdjkafnk"
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@app.route('/')
def home(*argv):
    return data_group_page(False, False, argv[0]) if argv else data_group_page()


@app.route('/login')
def login_page(*argv):
    return render_template("login/login.html", msg=argv[0]) if argv else render_template("login/login.html", msg="")


@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return home("The user {} is already authenticated".format(current_user.username))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return home("User {} has been authenticated".format(str(current_user.username)))

        else:
            return login_page("Username or password incorrect")
    return home(message)


# Create a new user

@app.route('/create')
def create_page(*argv):
    return render_template("login/signup.html", msg=argv[0]) if argv else render_template("login/signup.html", msg="")


@app.route('/create', methods=['POST'])
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        try:
            if users_collection.find_one({"username": username}):
                return create_page("User with that name already exists")

            email = request.form.get('email')
            password = request.form.get('password')
            save_user(username, email, password, password)

            msg = client.create_node(username, "U", "")
            if msg != "Success":
                return home("Error creating user node: " + msg)
        except Exception as e:
            print(e)
            return e

        return home("User successfully created")


# User logout

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return login_page("You have been logged out")


@app.route("/<user_id>/nego")
@login_required
def user_negotiations(user_id):
    try:
        if not current_user.is_authenticated:
            return login_page("You need to login to use this function")

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
        return render_template("contract/user_nego.html", msg="No negotiations", user_id=user_id)

    return render_template("contract/user_nego.html", nego_list=combined_list,
                           msg="Pending negotations", user=current_user.username, user_id=user_id)


@app.route("/<user_id>/completed")
@login_required
def user_completed_negosiations(user_id):
    try:
        if not current_user.is_authenticated:
            return login_page("You need to login to use this function")

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
        return render_template("contract/user_nego.html", msg="No completed negotiations", user_id=user_id)

    return render_template("contract/user_nego.html",
                           nego_list=combined_list,
                           msg="Completed negotiations",
                           user=current_user.username,
                           user_id=user_id)


class InfoForm(FlaskForm):
    startdate = DateField('Start Date', format='%Y-%m-%d')
    enddate = DateField('End Date', format='%Y-%m-%d')
    role = StringField('Role')
    offer = StringField('Offer')
    submit = SubmitField('Submit')
    todayDate = "2022-02-25"


@app.route("/negotiate/<data_group>/create")
@login_required
def new_nego(data_group):
    form = InfoForm()
    return render_template("contract/nego.html",
                           user_id=users_collection.find_one({"username": current_user.username})["_id"],
                           data_id=data_group, form=form, msg="", fixed=True)


@app.route("/negotiate/<data_group>/submit", methods=['POST'])
@login_required
def new_nego_req(data_group):
    try:
        st_date = request.form.get('startdate')
        end_date = request.form.get('enddate')

        role = request.form.get('role')
        offer = request.form.get('offer')

        # The following function may be changed to iterate if multiple roles are requested

        new_permi(current_user.username, data_group, st_date, end_date, role, offer)

        return home("A negotation has been created")
    except Exception as e:
        print(e)


@app.route("/negotiate/<req_id>/respond")
@login_required
def neg_page(req_id):
    try:
        neg_info = to_list.access_perm_to_list(get_neg(req_id))

        username = current_user.username
        user_id = users_collection.find_one({"username": username})["_id"]

        return render_template("contract/counter_nego.html",
                               req_id=neg_info[0],
                               demander=neg_info[1],
                               date=neg_info[3],
                               offer=neg_info[4],
                               item=neg_info[5],
                               start_date=neg_info[6],
                               end_date=neg_info[7],
                               role=neg_info[8],
                               fixed=True,
                               user_id=user_id)
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
            else:
                return home("No more offers can be made")
        else:
            return home("You are not part of the current negotiation")


# Only accesible to the owner of such resource, this route accepts the negotiation and begins the contract signing
@app.route("/negotiate/<req_id>/accept", methods=['GET'])
@login_required
def accept(req_id):
    try:
        req = get_neg(req_id)
        if current_user.username in (req['provider'], req['demander']):
            change_status(req_id, 'accept', current_user.username)  # 3d argument does nothing
            sign_contract(req_id)
            nego = negotiations_collection.find_one({'req_id': ObjectId('{}'.format(req_id))})
            req_details = nego['request_details']
            user_grp = req_details['role']
            data_grp = req_details['item']
            # Kollar om gruppen inte finns
            if not client.get_id(user_grp)[0]:
                client.create_node(user_grp, 'UA', "")

            # Kollar om användaren inte är med i gruppen
            if not client.get_assignment(req['demander'], user_grp)[0]:
                client.make_assignment(req['demander'], user_grp)

            client.make_association(user_grp, data_grp, True, True)

            # Skapa gruppen om den inte redan finns

            return home("The negotiation has been accepted.")

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
        change_status(req_id, 'reject', current_user.username)
        return home("The contract has been rejected")
    except Exception as e:
        print(e)
        return e


@app.route("/new_data")
@login_required
def new_data_page():
    data_groups = to_list.data_dict_to_name_list(data_collection.find({"owner": current_user.username}))

    username = current_user.username
    user_id = users_collection.find_one({"username": username})["_id"]

    return render_template("data/new_dataset.html", data_groups=data_groups, user_id=user_id, fixed=True)


@app.route("/new_data", methods=['POST'])
@login_required
def new_data():
    try:
        name = request.form.get('data_name')

        if client.get_id(name)[0]:
            return home("Data with that name already exists")

        if request.form.get('group_new_name'):
            group_name = request.form.get('group_new_name')
            group_id, msg = client.get_id(group_name)
            if msg != "Success":
                return home("Neo4j error trying to get node id: " + msg)
            if group_id != 0:
                return home("Data group already exists! Choose a different name")
            else:
                msg = client.create_node(group_name, "OA", "")
                if msg != "Success":
                    return home("Neo4j error creating node: " + msg)
                can_read = True if request.form.get('can_read') == 'Yes' else False
                can_modify = True if request.form.get('can_mod') == 'Yes' else False
                can_delete = True if request.form.get('can_delete') == 'Yes' else False

                new_dataset(group_name, current_user.username, can_read, can_modify, can_delete)
        else:
            group_name = request.form.get('group_name')

        msg = client.create_node(name, "O", "")
        if msg != "Success":
            return home("Neo4j error creating node: " + msg)
        msg = client.make_assignment(name, group_name)
        if msg != "Success":
            return home("Neo4j error creating assignment: " + msg)

        return home("New dataset has been created")

    except Exception as e:
        print(e)
        return e


@app.route("/search_data")
def data_group_page(*argv):
    try:
        if not current_user.is_authenticated:
            return login_page()

        username = current_user.username
        user_id = users_collection.find_one({"username": username})["_id"]

        user_data_page = False
        if argv:
            if argv[0] and argv[1]:
                data_groups = argv[0]
                user_data_page = argv[1]
            elif argv[0]:
                data_groups = argv[0]
            else:
                data_groups = to_list.data_to_list(data_collection.find())
        else:
            data_groups = to_list.data_to_list(data_collection.find())

        msg = argv[2] if argv else ""

        return render_template("data/data_groups_to_buy.html",
                               data_groups=data_groups,
                               username=username,
                               user_id=user_id,
                               user_data_page=user_data_page,
                               msg=msg)
    except Exception as e:
        print(e)
        return e


@app.route("/search_data/<data_group>")
def data_page(data_group):
    try:
        data_group_id, msg = client.get_id(data_group)
        if msg != "Success":
            return home("Neo4j error with msg: " + msg)
        if data_group_id == 0:
            return home("Data group does not exist")

        data_names, msg = client.get_node_children(data_group_id)
        if msg != "Success":
            return home("Neo4j error with msg: " + msg)

        username = current_user.username if current_user.is_authenticated else ""
        if current_user.is_authenticated:
            data_owner, msg = client.get_associations_OA_UA(data_group)
            if msg != "Success":
                return home("Neo4j error with msg: " + msg)

        data_group_info = to_list.data_to_list([data_collection.find_one({"name": data_group})])

        return render_template("data/datasets.html",
                               data_list=data_names,
                               data_group_info=data_group_info,
                               username=username)
    except Exception as e:
        print(e)
        return e


@app.route("/search_data/search", methods=["POST"])
def data_search_page():
    try:
        search_word = "" + request.form.get("search")
        full_node, msg = client.get_id(search_word, "full")
        if msg != "Success":
            return home("Something wrong with node server: " + msg)

        if not full_node:
            return home("No data found")
        if full_node[0]["type"] == "OA":
            return data_group_page(to_list.data_to_list(data_collection.find(
                {"name": search_word})), False, "Showing data with name: " + search_word)
        elif full_node[0]["type"] == "U":
            return data_group_page(to_list.data_to_list(data_collection.find(
                {"owner": search_word})), False, "Showing data with owner: " + search_word)

        return home("Searched for: " + search_word)
        # user_name = users_collection.find_one({"_id": ObjectId(user_id)})["username"]
        # return data_group_page(to_list.data_to_list(data_collection.find({"owner": user_name})), True, False)
    except Exception as e:
        print(e)
        return e


@app.route("/<user_id>/data")
def users_data_page(user_id):
    try:
        user_name = users_collection.find_one({"_id": ObjectId(user_id)})["username"]
        return data_group_page(to_list.data_to_list(data_collection.find({"owner": user_name})), True, False)
    except Exception as e:
        print(e)
        return e


def load_template():
    try:
        get_template("single_buyer")
    except TypeError:
        add_template()


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    load_template()
    # client.sessions()
    app.run(port=8086, debug=True)
