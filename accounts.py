from flask_restful import Resource, Api, reqparse
from flask import jsonify
import requests
import connection
from flasgger import Swagger
from flasgger import swag_from
from flask_swagger_ui import get_swaggerui_blueprint
import random
from flask import Flask, send_from_directory, make_response
from flask_httpauth import HTTPBasicAuth
import decimal
from decimal import Decimal
from datetime import date

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)
auth = HTTPBasicAuth()

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.json"
swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config = {
            'app_name': "Accounts API"
        }
    )
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


user_args = reqparse.RequestParser()
user_args.add_argument("userid", type=int, help="", required=False)
user_args.add_argument("accountno", type=str, help="", required=False)
user_args.add_argument("accountname", type=str, help="", required=True)
user_args.add_argument("status", type=bool, help="", required=True)

deposit = reqparse.RequestParser()
deposit.add_argument("amount", type=int, help="", required=True)
deposit.add_argument("description", type=str)

@app.route('/api/accounts', methods=['POST'])
@auth.login_required
def create():
    cur, conn = connection.get_connection()
    request = user_args.parse_args()
    accountno = GetAccountNo(request["userid"])
    cur.execute('insert into accounts (userid, accountno, accountname, status, balance) values (%s,%s,%s,%s,%s) RETURNING "id"', [request["userid"],accountno,request["accountname"],request["status"],0])
    conn.commit()
    user = cur.fetchone()
    response = {
      "user_id": user[0],
      "accountno": accountno,
      "success": True
      }
    return jsonify(response), 201


@app.route('/api/accounts/<id>', methods=['GET'])
@auth.login_required
def Get(id):
    cur, conn = connection.get_connection()
    cur.execute('select accounts.id,accounts.accountno,accounts.accountname,users.first_name,users.last_name,users.email,balance from accounts inner join users on accounts.userid=users.id where accounts.id = %s', [id])
    conn.commit()
    user = cur.fetchone()
    if cur.rowcount == 0:
        return jsonify({"error": "Account does not exist", "success": False}), 404
    user = {
      "id": user[0],
      "accountno": user[1],
      "accountname": user[2],
      "firstname": user[3],
      "lastname": user[4],
      "email": user[5],
      "balance": user[6]
    }
    return jsonify(user)


@app.route('/api/accounts', methods=['GET'])
@auth.login_required
def GetAccounts():
    cur, conn = connection.get_connection()
    cur.execute('select accounts.id,accounts.accountno,accounts.accountname,users.first_name,users.last_name,users.email,balance from accounts inner join users on accounts.userid=users.id')
    conn.commit()
    users = cur.fetchall()
    allusers = []
    for user in users:
      allusers.append({
        "id": user[0],
        "accountno": user[1],
        "accountname": user[2],
        "firstname": user[3],
        "lastname": user[4],
        "email": user[5],
        "balance": user[6]
      })
    return jsonify(allusers)


@app.route('/api/accounts/<userid>', methods=['PUT'])
@auth.login_required
def updateAccount(userid):
    cur, conn = connection.get_connection()
    request = user_args.parse_args()

    cur.execute('select * from accounts where id = %s', [int(userid)])
    conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Account does not exist", "success": False}), 404

    cur.execute('update accounts set accountname=%s, status=%s where id = %s', [request["accountname"],request["status"],int(userid)])
    conn.commit()
    response = {
      "account_id": userid,
      "success": True
      }
    return jsonify(response), 200


@app.route('/api/accounts/<id>', methods=['DELETE'])
@auth.login_required
def deleteAccount(id):
    cur, conn = connection.get_connection()

    cur.execute('select * from accounts where id = %s', [id])
    conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Account does not exist", "success": False}), 404

    cur.execute('delete from accounts where id=%s', [id])
    conn.commit()
    response = {
      "account_id": id,
      "success": True
      }
    return jsonify(response), 204


@app.route('/api/accounts/<id>/debit', methods=['POST'])
@auth.login_required
def debit(id):
    cur, conn = connection.get_connection()
    balance = 0
    cur.execute('select balance from accounts where id = %s', [id])
    conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Account does not exist", "success": False}), 404
    else:
        acc = cur.fetchone()
        balance = acc[0]

    request = deposit.parse_args()
    balance = balance - request['amount']
    cur.execute('update accounts set balance=%s where id=%s', [balance,id])
    conn.commit()

    #get IP
    ip_response = requests.request("GET",'https://api.ipify.org?format=json', headers={}, data={})
    ip_response = ip_response.json()
    ip = ip_response['ip']

    cur.execute('insert into transactions (amount, description, ip, date_created,accountid,type) values (%s,%s,%s,%s,%s,%s)', [request['amount'],request['description'],ip,str(date.today()),id,"debit"])
    conn.commit()

    response = {
      "account_id": id,
      "balance": balance,
      "success": True
      }
    return jsonify(response), 200


@app.route('/api/accounts/<id>/credit', methods=['POST'])
@auth.login_required
def credit(id):
    cur, conn = connection.get_connection()
    balance = 0
    cur.execute('select balance from accounts where id = %s', [id])
    conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Account does not exist", "success": False}), 404
    else:
        acc = cur.fetchone()
        balance = acc[0]

    request = deposit.parse_args()
    balance = balance + request['amount']
    cur.execute('update accounts set balance=%s where id=%s', [balance,id])
    conn.commit()

    #get IP
    ip_response = requests.request("GET",'https://api.ipify.org?format=json', headers={}, data={})
    ip_response = ip_response.json()
    ip = ip_response['ip']

    cur.execute('insert into transactions (amount, description, ip, date_created,accountid,type) values (%s,%s,%s,%s,%s,%s)', [request['amount'],request['description'],ip,str(date.today()),id,"credit"])
    conn.commit()

    response = {
      "account_id": id,
      "balance": balance,
      "success": True
      }
    return jsonify(response), 200


@app.route('/api/accounts/<id>/transactions', methods=['GET'])
@auth.login_required
def GetTransactions(id):
    cur, conn = connection.get_connection()
    cur.execute('select accounts.accountno,accounts.accountname,transactions.* from transactions left outer join accounts on transactions.accountid=accounts.id where accountid=%s',[id])
    conn.commit()
    trans = cur.fetchall()
    alltrans = []
    for item in trans:
      alltrans.append({
        "accountno": item[0],
        "accountname": item[1],
        "amount": item[3],
        "description": item[4],
        "ip": item[5],
        "type": item[7],
        "date": item[6]
      })
    return jsonify(alltrans)


def GetAccountNo(userid):
    accountno = str(userid)
    length = 10 - len(str(userid))
    for i in range(length):
        accountno += str(random.randint(0, 9))
    return accountno


@auth.verify_password
def authenticate(username, password):
    if username == 'admin' and password == 'admin':
        return True
    else:
        return False

if __name__ == "__main__":
    app.run(debug=True)