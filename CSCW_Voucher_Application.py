from flask import Flask
from flask import request
from flask import jsonify
from bigchaindb import Bigchain
from bigchaindb import crypto
import rethinkdb as r
import time
from enum import Enum

app = Flask(__name__)


class UserType(Enum):
    DONOR = 1
    CONSUMER = 2
    COMPANY = 3

b = Bigchain()
conn = r.connect("localhost", 28015)
userTable = "user_table"

def checkIfTheUserExists(userName):
    return_data = r.db("bigchain").table("user_table").get(userName).count().run(conn)
    if(return_data >0):
        return True
    else:
        return False

def constructUserTuple(username, password, type, public_key,private_key):
    data = {}
    data["userName"] = username
    data["password"] = password
    data["type"] = type
    data["public_key"] = public_key
    data["private_key"] = private_key
    return data

def getTupleFromDB(tableName,primary_key):
    return r.db("bigchain").table(tableName).get(primary_key);

def insertData(tableName,data):
    r.db("bigchain").table(tableName).insert(data).run(conn)


@app.route('/voucherApp/createUser', methods=['POST'])
def createUser(username=request.args.get('username'),password=request.args.get('password'),type = request.args.get('type')):
    if(not checkIfTheUserExists(username)):
        user_priv, user_pub = crypto.generate_key_pair()
        userTuple = constructUserTuple(username,password,type,user_priv,user_pub)
        insertData(userTable,userTuple)
        return jsonify(status="success",publicKey=user_pub,privateKey=user_priv)
    else:
        return jsonify(status="error", errorMessage="Username Already Exists!")


@app.route('/voucherApp/signIn',methods=['POST'])
def signIn(username = request.args.get('username'),password=request.args.get('password')):
    if(checkIfTheUserExists(username)):
        tupleData = getTupleFromDB(userTable,username)
        if(tupleData["password"] == password):
            return jsonify(status="success",publicKey=tupleData["public_key"],privateKey=tupleData["private_key"])
        else:
            return jsonify(status="error",errorMessage="Password Incorrect!")
    else:
        return jsonify(status="error", errorMessage="User doesn't exist!")


@app.route('/voucherApp/createVoucher',methods=['POST'])
def createVoucher(voucherName = request.args.get('voucher_name'),username=request.args.get('username'), value = request.args.get('value')):
    if(not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    else:
        voucherPayload = {}
        voucherPayload["name"] = voucherName
        voucherPayload["value"] = value
        user_pub_key = getTupleFromDB(userTable,username)["public_key"]
        tx = b.create_transaction(b.me, user_pub_key, None, 'CREATE', payload=voucherPayload)
        tx_signed = b.sign_transaction(tx, b.me_private)
        b.write_transaction(tx_signed)
        time.sleep(5)
        return jsonify(status="success",message="Voucher Created Successfully")


@app.route('/voucherApp/getOwnedIDs',methods=['GET'])
def getOwnedIDs(username=request.args.get('username')):
    if (not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    else:
        user_pub_key = getTupleFromDB(userTable, username)["public_key"]
        return b.get_owned_ids(user_pub_key)


@app.route('/voucherApp/transferVoucher',methods=['POST'])
def getOwnedIDs(source_username=request.args.get('source_username'),target_username=request.args.get('target_username'),sourceuser_priv_key = request.args.get('source_private_key'),asset_id=request.args.get('asset_id')):
    if (not checkIfTheUserExists(target_username)):
        return jsonify(status="error", errorMessage="Target User doesn't exist!")
    elif(not checkIfTheUserExists(source_username)):
        return jsonify(status="error", errorMessage="Source User doesn't exist!")
    else:
        target_user_pub_key = getTupleFromDB(userTable, target_username)["public_key"]
        source_user_pub_key = getTupleFromDB(userTable, source_username)["public_key"]
        tx_transfer = b.create_transaction(source_user_pub_key, target_user_pub_key, asset_id, 'TRANSFER')
        tx_transfer_signed = b.sign_transaction(tx_transfer, sourceuser_priv_key)
        b.write_transaction(tx_transfer_signed)
        time.sleep(5)
        return jsonify(status="success", errorMessage="Voucher Successfully Trasferred")




if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)



