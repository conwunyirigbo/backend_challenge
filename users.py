import requests
from flask_restful import Resource, Api, reqparse
from flask import Flask, send_from_directory, make_response
import json
from flask import jsonify
import psycopg2
import connection
import hashlib
from flasgger import Swagger
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

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
user_args.add_argument("firstname", type=str, help="Firstname is required", required=True)
user_args.add_argument("lastname", type=str, help="lastname is required", required=True)
user_args.add_argument("email", type=str, help="email is required", required=True)
user_args.add_argument("phone", type=str, help="phone is required", required=True)
user_args.add_argument("password", type=str, help="password is required")

@app.route('/api/users', methods=['POST'])
def create():
    cur, conn = connection.get_connection()
    request = user_args.parse_args()
    password = hashlib.sha256(request["password"].encode()).hexdigest()
    cur.execute('insert into users (first_name, last_name, email, phone, pword) values (%s,%s,%s,%s,%s) RETURNING "id"', [request["firstname"],request["lastname"],request["email"],request["phone"],password])
    conn.commit()
    user = cur.fetchone()
    response = {
      "user_id": user[0],
      "success": True
      }
    return json.dumps(response), 201


@app.route('/api/users/<id>', methods=['GET'])
def Get(id):
    cur, conn = connection.get_connection()
    cur.execute('select * from users  where id = %s', [id])
    conn.commit()
    user = cur.fetchone()
    user = {
      "id": user[0],
      "firstname": user[1],
      "lastname": user[2],
      "email": user[3],
      "phone": user[4]
    }
    return jsonify(user)


@app.route('/api/users', methods=['GET'])
def GetUsers():
    cur, conn = connection.get_connection()
    cur.execute('select * from users')
    conn.commit()
    users = cur.fetchall()
    allusers = []
    for user in users:
      allusers.append({
        "id": user[0],
        "firstname": user[1],
        "lastname": user[2],
        "email": user[3],
        "phone": user[4]
      })
    return jsonify(allusers)


@app.route('/api/users/<id>', methods=['PUT'])
def updateUser(id):
    cur, conn = connection.get_connection()
    request = user_args.parse_args()

    cur.execute('select * from users where id = %s', [id])
    conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "User does not exist", "success": False}), 404

    cur.execute('update users set first_name=%s, last_name=%s, email=%s, phone=%s where id = %s', [request["firstname"],request["lastname"],request["email"],request["phone"],id])
    conn.commit()
    response = {
      "user_id": id,
      "success": True
      }
    return jsonify(response), 200

@app.route('/api/users/<id>', methods=['DELETE'])
def deleteUser(id):
    cur, conn = connection.get_connection()

    cur.execute('select * from users where id = %s', [id])
    conn.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "User does not exist", "success": False}), 404

    cur.execute('delete from users where id=%s', [id])
    conn.commit()
    response = {
      "user_id": id,
      "success": True
      }
    return jsonify(response), 204

if __name__ == "__main__":
    app.run(debug=True)