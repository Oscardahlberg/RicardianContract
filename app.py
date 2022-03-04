from datetime import datetime, date
from re import S
from tokenize import group

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
from db import child, date_check, find_resources, get_provider, get_user, get_neg, neg_name_gen, change_status, \
    negotiations, offer_parent, parent, parent_acc_check, parent_info, sign_contract, update, users_collection, client, \
    save_user, data_collection, add_template, add_template1, access_collection, new_dataset, new_permi, \
    negotiations_collection, offer, get_template
import ngac
from flask_navigation import Navigation

app = Flask(__name__)
nav = Navigation(app)
dp = datepicker(app)
Bootstrap(app)

cors = CORS(app)
app.secret_key = "sfdjkafnk"
login_manager = LoginManager()
login_manager.login_view = 'user'
login_manager.init_app(app)


class InfoForm(FlaskForm):
    startdate = DateField('Start Date', format='%Y-%m-%d')
    enddate = DateField('End Date', format='%Y-%m-%d')


@app.route('/navbar')
def navbar():
    return render_template("user/navbar.html")


@app.route('/')
def home(*argv):
    return data_group_page(False, False, argv[0]) if argv else data_group_page()


@app.route('/login')
def login_page(*argv):
    return render_template("user/login.html", msg=argv[0]) if argv else render_template("user/login.html", msg="")


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
    return render_template("user/signup.html", msg=argv[0]) if argv else render_template("user/signup.html", msg="")


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

            msg = ngac.create_node(username, "U", "")
            if msg != "Success":
                return home("Error creating user node: " + msg)
        except Exception as e:
            print(e)
            return e

        return login_page("Successfully created user!")


# User logout
@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return login_page("You have been logged out")


@app.route("/search_for_user_group")
@login_required
def join_group(*args):
    msg = "" if not args else args[0]
    user_id = users_collection.find_one({"username": current_user.username})["_id"]
    return render_template("user/search_for_user_group.html", user_id=user_id, fixed=True, msg=msg)


@app.route("/search_for_user_group", methods=['POST'])
@login_required
def join_selected_group():
    group_name = request.form.get('group_name')
    gid, msg = ngac.get_id(group_name)
    if msg != "Success":
        return home("Something wrong with node system: " + msg)
    if gid == 0:
        return join_group("No groups with that name")
    is_connected, msg = ngac.get_assignment(current_user.username, group_name)
    if msg != "Success":
        return home("Something wrong with node system: " + msg)
    if is_connected:
        return home("You are already apart of this group!")

    frame_contracts = access_collection.find({"request_details.role": group_name, "status": "accepted"})
    frame_contracts = to_list.temporar(frame_contracts)
    name_list, msg = ngac.get_node_children(ngac.get_id(group_name)[0])
    if msg != "Success":
        return home("Something wrong with node database: " + msg)

    return render_template("contract/show_group_frame_contracts.html",
                           frame_contracts=frame_contracts, current=len(name_list))


# Starts a negotiation for parent contract
@app.route("/negotiate/<data_group>/parent", methods=['POST'])
@login_required
def parent_neg(data_group):
    try:
        st_date = request.form.get('startdate')
        end_date = request.form.get('enddate')
        print(st_date)
        print(end_date)
        role = request.form.get('role')
        offering = request.form.get('offer')
        node_id, message = ngac.get_id(role)
        if message != "Success":
            return home("Something wrong with node database: " + message)
        if node_id:
            is_connected, message = ngac.get_assignment(current_user.username, role)
            if message != "Success":
                return home("Something wrong with node database: " + message)
            if not is_connected:
                return new_nego(data_group)
        user_am = request.form.get('user_amount')
        # The following function may be changed to iterate if multiple roles are requested
        # neg_id=new_permi(current_user.username, item, st_date, end_date, role,offering)
        parent('parent', current_user.username, user_am, data_group, st_date, end_date, role, offering)
        return home("Negotation created! Wait for their response")
    except Exception as e:
        print(e)


# Starts negotiation for child, needs parent contract
@app.route("/negotiate/<data_group>/child", methods=['POST'])
@login_required
def child_neg(data_group):
    try:
        st_date = request.form.get('startdate')
        end_date = request.form.get('enddate')
        role = request.form.get('role')
        offer = request.form.get('offer')
        # The following function may be changed to iterate if multiple roles are requested
        parent_name = request.form.get('parent_name')
        parent_contract = parent_info(parent_name)
        if parent_acc_check(parent_contract['_id']):
            print('Parent contract ok')
        else:
            return home("The negotiation has not ended or does not exist")
        if date_check(parent_contract['_id'], st_date, end_date):
            print("date format ok")
        else:
            return home("Dates does not match")
        neg_id = child('child', parent_contract['_id'], parent_name,
                       current_user.username, data_group, st_date, end_date, role, offer)
        print(neg_id)
        return home("Negotiation created! Wait for their response")
    except Exception as e:
        print(e)


@app.route("/framecontract/<role>/<parent_name>", methods=['POST'])
@login_required
def frame(role, parent_name):
    print(role)
    print(parent_name)
    item = request.form.get("item")
    print(item)
    return render_template("contract/frame_nego.html",
                           parent_name=parent_name, role=role, form=InfoForm(), fixed=True, item=item)


@app.route("/<user_id>/nego")
@login_required
def user_negotiations(user_id):
    try:
        if not current_user.is_authenticated:
            return login_page("You need to user to use this function")

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
            return login_page("You need to user to use this function")

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


@app.route("/negotiate/<data_group>/create")
@login_required
def new_nego(data_group):
    return render_template("contract/nego.html",
                           user_id=users_collection.find_one({"username": current_user.username})["_id"],
                           data_id=data_group, msg="", form=InfoForm(), fixed=True)


@app.route("/negotiate/<req_id>/respond")
@login_required
def neg_page(req_id):
    try:
        neg_info = to_list.access_perm_to_list(get_neg(req_id))

        user_id = users_collection.find_one({"username": current_user.username})["_id"]

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
                user_am = request.form.get('user_amount')
                offer_parent(ObjectId(req_id), current_user.username, user_am, item, st_date, end_date, role, offering)
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
            sign_contract(req_id, req['type'])
            if req["type"] == "child":
                ngac.make_assignment(req["demander"], req["request_details"]["role"])
            else:
                nego = negotiations_collection.find_one({'req_id': ObjectId('{}'.format(req_id))})
                req_details = nego['request_details']
                user_grp = req_details['role']
                data_grp = req_details['item']

                if not ngac.get_id(user_grp)[0]:
                    ngac.create_node(user_grp, 'UA', "")

                if not ngac.get_assignment(req['demander'], user_grp)[0]:
                    ngac.make_assignment(req['demander'], user_grp)
                    print('created assignment to user group')

                ngac.make_association(user_grp, data_grp, True, True)

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


# This route shows the data resources available to negotiate in
@app.route("/negotiate/resources", methods=['GET'])
@login_required
def resources():
    available_data = find_resources(current_user.username)
    return available_data


# This route show the available data that users can negotiate on existing parents
@app.route("/negotiate/providers", methods=['GET'])
@login_required
def providers():
    available_data = negotiations(current_user.username)
    return available_data


@app.route("/new_data")
@login_required
def new_data_page():
    data_groups = to_list.data_dict_to_name_list(data_collection.find({"owner": current_user.username}))
    user_id = users_collection.find_one({"username": current_user.username})["_id"]

    return render_template("data/new_dataset.html", data_groups=data_groups, user_id=user_id, fixed=True)


@app.route("/new_data", methods=['POST'])
@login_required
def new_data():
    try:
        name = request.form.get('data_name')
        if ngac.get_id(name)[0]:
            return home("Data with that name already exists")

        if request.form.get('group_new_name'):
            group_name = request.form.get('group_new_name')
            group_id, msg = ngac.get_id(group_name)
            if msg != "Success":
                return home("Neo4j error trying to get node id: " + msg)
            if group_id != 0:
                return home("Data group already exists! Choose a different name")
            else:
                msg = ngac.create_node(group_name, "OA", "")
                if msg != "Success":
                    return home("Neo4j error creating node: " + msg)
                can_read = True if request.form.get('can_read') == 'Yes' else False
                can_modify = True if request.form.get('can_mod') == 'Yes' else False
                can_delete = True if request.form.get('can_delete') == 'Yes' else False

                new_dataset(group_name, current_user.username, can_read, can_modify, can_delete)
        else:
            group_name = request.form.get('group_name')

        msg = ngac.create_node(name, "O", "")
        if msg != "Success":
            return home("Neo4j error creating node: " + msg)
        msg = ngac.make_assignment(name, group_name)
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

        user_id = users_collection.find_one({"username": current_user.username})["_id"]

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
                               username=current_user.username,
                               user_id=user_id,
                               user_data_page=user_data_page,
                               msg=msg)
    except Exception as e:
        print(e)
        return e


@app.route("/search_data/<data_group>")
def data_page(data_group):
    try:
        data_group_id, msg = ngac.get_id(data_group)
        if msg != "Success":
            return home("Neo4j error with msg: " + msg)
        if data_group_id == 0:
            return home("Data group does not exist")

        data_names, msg = ngac.get_node_children(data_group_id)
        if msg != "Success":
            return home("Neo4j error with msg: " + msg)

        username = current_user.username if current_user.is_authenticated else ""
        if current_user.is_authenticated:
            data_owner, msg = ngac.get_associations_OA_UA(data_group)
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
        full_node, msg = ngac.get_id(search_word, "full")
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

        return home("Could not find anything for: " + search_word)
    except Exception as e:
        print(e)
        return e


# Data page for the data that the user has created
@app.route("/data")
def users_data_page():
    try:
        return data_group_page(
            to_list.data_to_list(data_collection.find({"owner": current_user.username})), True, False)
    except Exception as e:
        print(e)
        return e


# Data page for all the data the user is connected to
# through ngac (does not include data the user has created)
@app.route("/data_access")
def users_data_access_page():
    try:
        user_node_id, msg = ngac.get_id(current_user.username)
        if msg != "Success":
            return home("Something wrong with node database: " + msg)
        user_groups, msg = ngac.get_node_parents(user_node_id)
        if msg != "Success":
            return home("Something wrong with node database: " + msg)

        if len(user_groups) == 0:
            return home("You are not connected to any data")

        # Right now only gets the data group names, could get contract info aswell
        data_groups = []
        for user_group in user_groups:
            group_data, msg = ngac.get_associations_UA_OA(user_group)
            if msg != "Success":
                return home("Something wrong with node database: " + msg)
            if len(group_data) != 0:
                data_groups = data_groups + group_data

        user_id = users_collection.find_one({"username": current_user.username})["_id"]
        return render_template("data/user_accessible_data.html", data_groups=data_groups, user_id=user_id)
    except Exception as e:
        print(e)
        return e


def load_template():
    try:
        get_template("parent_contract")
    except TypeError:
        add_template1()
        add_template()


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    load_template()
    # ngac.sessions()
    app.run(port=8086, debug=True)
