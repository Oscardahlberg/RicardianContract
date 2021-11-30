from datetime import datetime
from re import S

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS



from db import get_user, get_neg, new_permi, offer, change_status, sign_contract, update

app = Flask(__name__)

cors = CORS(app)
app.secret_key = "sfdjkafnk"
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


#User login receives form params username and password

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return {"message":"The user {} is already authenticated".format(current_user.username)},200

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
           
            return {"message":"User {} has been authenticated".format(str(current_user.username))},200
        else:
            message = 'Failed to login!'
    return message,400

# User logout

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return {'message':'the user has logged out'},200



# Start negotiation: 
# To be done: Verify validity of inputs, for example, x permision for y database is possible

@app.route("/negotiate", methods=['POST'])
@login_required
def new_neg():
    try: 
        item=request.form.get('item')
        st_date=request.form.get('st_date')
        end_date=request.form.get('end_date')
        role=request.form.get('role')
        offering=request.form.get('offering')
        #The following function may be changed to iterate if multiple roles are requested

        neg_id=new_permi(current_user.username, item, st_date, end_date, role,offering)
        
        print(neg_id)
        return {"message":"The negotiation with id {} has been created".format(str(neg_id))},200
    except Exception as e: print(e)


# Negotiation or back and forth of proposals:
# To be done: Verify that new proposal is different to the previous one and that the porposer is different than the one who proposed the last

@app.route("/negotiate/<req_id>", methods=['GET','POST'])
@login_required
def neg(req_id):
    req=get_neg(req_id)
    print(req)
    if request.method == 'POST':
        if current_user.username in (req['provider'],req['demander']):
            if req['status'] not in ('accepted', 'rejected'):
                item=request.form.get('item')
                st_date=request.form.get('st_date')
                end_date=request.form.get('end_date')
                role=request.form.get('role')
                offering=request.form.get('offering')
                offer(ObjectId(req_id), current_user.username, item, st_date, end_date, role,offering)
                update(req_id,offering,item,st_date,end_date,role)
                change_status(req_id,1,current_user.username)
                return  {"message":"New offer submited for request with id {}".format(str(req['_id']))},200
            else:
                return  {"message":"The negotiation {} has concluded no more offers can be made".format(str(req['_id']))},403
        else:
            return{"message":'You are not part of the current negotiation'}, 403


# Only accesible to the owner of such resource, this route accepts the negotiation and begins the contract signing
@app.route("/negotiate/<req_id>/accept", methods=['GET'])
@login_required
def accept(req_id):
    req=get_neg(req_id)
    if current_user.username == req['provider']:
        change_status(req_id, 'accept',current_user.username)
        s=sign_contract(req_id)
        print(s)
        ## Add function for contract writing
        return  {"message":"The negotiation with id {} has been accepted.".format(str(req['_id'])), "Contract": "{}".format(s)},200

    else: return {"message":'You are not authorized to perform this task'},403



# Only accesible to the owner of such resource, this route cancels the negotiation.
@app.route("/negotiate/<req_id>/cancel", methods=['GET'])
@login_required
def cancel(req_id):
    req=get_neg(req_id)
    if current_user.username == req['provider']:
        change_status(req, 'reject')
        return  {"message":"The negotiation with id {} has been reject".format(str(req['_id']))},200

    else: return {"message":'You are not authorized to perform this task'},403 





@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
