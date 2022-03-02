from datetime import datetime
from re import S
from tokenize import group

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS
import ngac
import to_list

from db import child, date_check, find_resources, get_provider, get_user, get_neg, neg_name_gen, change_status, \
    negotiations, offer_parent, parent, parent_acc_check, parent_info, sign_contract, update, users_collection, client, \
    save_user, data_collection, add_template, add_template1, access_collection, new_dataset, new_permi, negotiations_collection

app = Flask(__name__)

cors = CORS(app)
app.secret_key = "sfdjkafnk"
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@app.route("/join_group")
@login_required
def join_group():
    print(ngac.get_nodes_with_type("UA"))
    return render_template("join_group.html", user_groups=ngac.get_nodes_with_type("UA")[0])

@app.route("/join_group", methods=['POST'])
@login_required
def join_selected_group():
    group_name = request.form.get('group_name')
    # TODO, fix time expiration
    print(group_name)
    frame_contracts = access_collection.find({"request_details.role" : group_name, "status" : "accepted"})
    frame_contracts = to_list.temporar(frame_contracts, "accepted")
    print(frame_contracts)

    return render_template("show_group_frame_contracts.html", frame_contracts=frame_contracts)

@app.route('/framecontract', methods=['POST'])
@login_required
def frame():
    parent_name = request.form.get("parent_name")
    item = request.form.get("item")
    role = request.form.get("role")
    return render_template("frame_nego.html",parent_name = parent_name ,item = item, role = role)

@app.route('/navbar')
def navbar():
    return render_template("navbar.html")

@app.route('/')
def home(*argv):
    msg = argv[0] if argv else ""

    name = ""
    user_id = ""
    if current_user.is_authenticated:
        _id, message = ngac.get_id(current_user.username)
        if message != "Success":
            print("Not success: " + message)

        name = current_user.username
        try:
            user_id = users_collection.find_one({"username": name})["_id"]
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
            # skapar noden för user

            msg = ngac.create_node(username, "U", "")
            if msg != "Success":
                return home("Error creating user node: " + msg)
        except Exception as e:
            print(e)
            return e

        # TODO:CALL TO CREATE USER IN GRAPH

        return home("User successfully created")

# User logout

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return home("You have logged out")

@app.route("/negotiate/<data_id>/create")
@login_required
def new_nego(data_id):
    return render_template("nego.html", data_id=data_id)
    
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


# Start negotiation:
@app.route("/negotiate/parent", methods=['POST']) #Starts a negotiation for parent contract
@login_required
def parent_neg():
    try: 
        item=request.form.get('item')
        nag_type='parent'
        st_date=request.form.get('st_date')
        end_date=request.form.get('end_date')
        role=request.form.get('role')
        offering=request.form.get('offering')
        user=current_user.username
        print(current_user.username)
        user_amm=request.form.get('user_ammount')
        #The following function may be changed to iterate if multiple roles are requested
        
        #neg_id=new_permi(current_user.username, item, st_date, end_date, role,offering)
        print("1")
        neg_id = parent(nag_type,user,user_amm,item,st_date,end_date,role,offering)
        print(neg_id)
        return {"message":"The negotiation with id {} has been created".format(str(neg_id))},200
    except Exception as e: print(e)

@app.route("/negotiate/child", methods=['POST']) #Starts negotiation for child, needs parent contract
@login_required
def child_neg():
    try: 
        item=request.form.get('item')
        nag_type='child'
        st_date=request.form.get('st_date')
        end_date=request.form.get('end_date')
        role=request.form.get('role')
        offering=request.form.get('offering')
        user=current_user.username
        #The following function may be changed to iterate if multiple roles are requested
        parent_name=request.form.get('parent_name')
        print("1")
        print(parent_name)
        parent_contract=parent_info(parent_name)
        print(2)
        if parent_acc_check(parent_contract['_id']):
            print('Parent contract ok')
        else:
            return {"message":"The negotiation hasnt ended or does not exist"},403
        print(3)
        if date_check(parent_contract['_id'],st_date,end_date):
            print("date format ok")
        else:
            return {"message":"The requested dates does not match with parent contract date frames"},403
        print(4)
        neg_id=child(nag_type,parent_contract['_id'],parent_name,user,item,st_date,end_date,role,offering)
        print(neg_id)
        return {"message":"The negotiation with id {} has been created".format(str(neg_id))},200
    except Exception as e: print(e)

# Negotiation or back and forth of proposals: (only for parents)
# To be done: Verify that new proposal is different to the previous one and that the porposer is different than the one who proposed the last

@app.route("/negotiate/<req_id>", methods=['GET','POST'])
@login_required
def neg(req_id):
    req=get_neg(req_id)
    print(req)
    if request.method == 'POST':
        if req['type']=='parent':
            if current_user.username in (req['provider'],req['demander']):
                if req['status'] not in ('accepted', 'rejected'):
                    item=request.form.get('item')
                    st_date=request.form.get('st_date')
                    end_date=request.form.get('end_date')
                    role=request.form.get('role')
                    offering=request.form.get('offering')
                    user_amm=request.form.get('user_ammount')
                    offer_parent(ObjectId(req_id), current_user.username,user_amm, item, st_date, end_date, role,offering)
                    update(req_id,offering,item,st_date,end_date,role)
                    change_status(req_id,1,current_user.username)
                    return  {"message":"New offer submited for request with id {}".format(str(req['_id']))},200
                else:
                    return  {"message":"The negotiation {} has concluded no more offers can be made".format(str(req['_id']))},403
            else:
                return{"message":'You are not part of the current negotiation'}, 403
        else: 
            return  {"message":"Cannot bid on child negotiation {}".format(str(req['_id']))},403

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
                # Kollar om gruppen inte finns
                if not ngac.get_id(user_grp)[0]:
                    ngac.create_node(user_grp, 'UA', "")
                    print('created the user group')

                # Kollar om användaren inte är med i gruppen
                if not ngac.get_assignment(req['demander'], user_grp)[0]:
                    ngac.make_assignment(req['demander'], user_grp)
                    print('created assignment to user group')

                ngac.make_association(user_grp, data_grp, True, True)

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
    print(1)

    req=get_neg(req_id)
    print(req)
    if current_user.username == req['provider']:
        change_status(req_id, 'reject',current_user.username)
        return  {"message":"The negotiation with id {} has been reject".format(str(req['_id']))},200

    else: return {"message":'You are not authorized to perform this task'},403 


#This route shows the data resources available to negotiate in
@app.route("/negotiate/resources", methods=['GET'])
@login_required
def resources():
    available_data=find_resources(current_user.username)
    return available_data

#This route show the available data that users can negotiate on existing parents
@app.route("/negotiate/providers", methods=['GET'])
@login_required
def providers():
    available_data=negotiations(current_user.username)
    return available_data

@app.route("/new_data")
@login_required
def new_data_page():
    data_groups = to_list.data_dict_to_name_list(data_collection.find({"owner": current_user.username}))

    return render_template("new_dataset.html", data_groups=data_groups)


@app.route("/new_data", methods=['POST'])
@login_required
def new_data():
    try:
        name = request.form.get('data_name')
        print("1")
        if ngac.get_id(name)[0]:
            return home("Data with that name already exists")
        print("2")
        if request.form.get('group_new_name'):
            group_name = request.form.get('group_new_name')
            group_id, msg = ngac.get_id(group_name)
            if msg != "Success":
                return home("Neo4j error trying to get node id: " + msg)
            print("3")
            if group_id != 0:
                return home("Data group already exists! Choose a different name")
            else:
                msg = ngac.create_node(group_name, "OA", "")
                if msg != "Success":
                    return home("Neo4j error creating node: " + msg)
                can_read = True if request.form.get('can_read') == 'Yes' else False
                can_modify = True if request.form.get('can_mod') == 'Yes' else False
                can_delete = True if request.form.get('can_delete') == 'Yes' else False
                print("4")
                new_dataset(group_name, current_user.username, can_read, can_modify, can_delete)
        else:
            group_name = request.form.get('group_name')
        print("5")
        msg = ngac.create_node(name, "O", "")
        if msg != "Success":
            return home("Neo4j error creating node: " + msg)
        msg = ngac.make_assignment(name, group_name)
        print("6")
        if msg != "Success":
            return home("Neo4j error creating assignment: " + msg)

        return home("New dataset has been created")

    except Exception as e:
        print(e)
        return e

@app.route("/search_data")
def data_group_page(*args):
    try:
        username = current_user.username if current_user.is_authenticated else ""

        if not args:
            data_groups = to_list.data_to_list(data_collection.find())
            title = "Availabe data groups for contract" if current_user.is_authenticated else "Login to make a contract"
        else:
            title = args[1]
            data_groups = args[0]

        if len(data_groups) == 0:
            return home("There is no data")

        return render_template("data_groups_to_buy.html",
                               data_groups=data_groups,
                               title=title,
                               username=username)
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
            title = "Availabe data for contract"
            data_owner, msg = ngac.get_associations_OA_UA(data_group)
            if msg != "Success":
                return home("Neo4j error with msg: " + msg)
            if data_owner == username:
                title = "Data owned by: " + username
        else:
            title = "Login to make a contract"
        return render_template("datasets.html",
                               data_list=data_names,
                               title=title,
                               username=username)
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

@app.route("/negotiate/<data_group>/submit", methods=['POST'])
@login_required
def new_nego_req(data_group):
    try:
        st_date = request.form.get('st_date')
        end_date = request.form.get('end_date')
        role = request.form.get('role')
        offering = request.form.get('offering')
        # The following function may be changed to iterate if multiple roles are requested

        new_permi(current_user.username, data_group, st_date, end_date, role, offering)

        return home("A negotation has been created")
        # return {"message": "The negotiation with id {} has been created".format(str(neg_id))}, 200
    except Exception as e:
        print(e)


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    #ngac.sessions()
    app.run(port=5000, debug=True)
