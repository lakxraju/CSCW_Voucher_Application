from flask import Flask
from flask import request
from flask import jsonify
from bigchaindb import Bigchain
from bigchaindb import crypto
from flask_restful import reqparse
import rethinkdb as r
import time
from enum import Enum

app = Flask(__name__)


class UserAttributes(Enum):
    PUBLIC_KEY = "public_key"
    PRIVATE_KEY = "private_key"
    USERNAME = "username"
    PASSWORD = "password"
    TYPE = "type"
    SOURCE_USERNAME = "source_username"
    TARGET_USERNAME = "target_username"


class UserType(Enum):
    DONOR = 1
    CONSUMER = 2
    COMPANY = 3

class Operations(Enum):
    CREATE = "CREATE"
    TRANSFER = "TRANSFER"

class TableNames(Enum):
    USER = "user_table"
    BIGCHAIN = "bigchain"

b = Bigchain()
conn = r.connect("localhost", 28015)


@app.route('/voucherApp/createUser', methods=['POST'])
def createUser():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME,required=True, type=str)
    parser.add_argument(UserAttributes.PASSWORD, required=True, type=str)
    parser.add_argument(UserAttributes.TYPE, required=True, type=str)


    username = request.args.get(UserAttributes.USERNAME)
    password = request.args.get(UserAttributes.PASSWORD)
    type = request.args.get(UserAttributes.TYPE)

    if(not checkIfTheUserExists(username)):
        user_priv, user_pub = crypto.generate_key_pair()
        userTuple = constructUserTuple(username,password,type,user_priv,user_pub)
        insertData(TableNames.USER,userTuple)
        return jsonify(status="success",publicKey=user_pub,privateKey=user_priv)
    else:
        return jsonify(status="error", errorMessage="Username Already Exists!")


@app.route('/voucherApp/signIn',methods=['POST'])
def signIn():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME, required=True, type=str)
    parser.add_argument(UserAttributes.PASSWORD, required=True, type=str)

    username = request.args.get(UserAttributes.USERNAME)
    password = request.args.get(UserAttributes.PASSWORD)

    if(checkIfTheUserExists(username)):
        tupleData = getTupleFromDB(TableNames.USER,username)
        if(tupleData[UserAttributes.PASSWORD] == password):
            return jsonify(status="success",publicKey=tupleData[UserAttributes.PUBLIC_KEY],privateKey=tupleData[UserAttributes.PRIVATE_KEY])
        else:
            return jsonify(status="error",errorMessage="Password Incorrect!")
    else:
        return jsonify(status="error", errorMessage="User doesn't exist!")


@app.route('/voucherApp/createVoucher',methods=['POST'])
def createVoucher():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME, required=True, type=str)
    parser.add_argument('value', required=True, type=str)
    parser.add_argument('voucher_name', required=True, type=str)


    voucherName = request.args.get('voucher_name')
    username = request.args.get(UserAttributes.USERNAME)
    value = request.args.get('value')

    if(not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    else:
        voucherPayload = {}
        voucherPayload["name"] = voucherName
        voucherPayload["value"] = value
        user_pub_key = getTupleFromDB(TableNames.USER,username)[UserAttributes.PUBLIC_KEY]
        tx = b.create_transaction(b.me, user_pub_key, None, Operations.CREATE, payload=voucherPayload)
        tx_signed = b.sign_transaction(tx, b.me_private)
        b.write_transaction(tx_signed)
        time.sleep(5)
        return jsonify(status="success",message="Voucher Created Successfully")


@app.route('/voucherApp/getOwnedIDs',methods=['GET'])
def getOwnedIDs():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME, required=True, type=str)

    username = request.args.get(UserAttributes.USERNAME)
    if (not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    else:
        user_pub_key = getTupleFromDB(TableNames.USER, username)[UserAttributes.PUBLIC_KEY]
        return b.get_owned_ids(user_pub_key)


@app.route('/voucherApp/transferVoucher',methods=['POST'])
def transferVoucher():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.TARGET_USERNAME, required=True, type=str)
    parser.add_argument(UserAttributes.SOURCE_USERNAME, required=True, type=str)
    parser.add_argument(UserAttributes.PRIVATE_KEY, required=True, type=str)
    parser.add_argument('asset_id', required=True, type=str)


    source_username = request.args.get(UserAttributes.SOURCE_USERNAME)
    target_username = request.args.get(UserAttributes.TARGET_USERNAME)
    sourceuser_priv_key = request.args.get(UserAttributes.PRIVATE_KEY)
    asset_id = request.args.get('asset_id')
    if (not checkIfTheUserExists(target_username)):
        return jsonify(status="error", errorMessage="Target User doesn't exist!")
    elif(not checkIfTheUserExists(source_username)):
        return jsonify(status="error", errorMessage="Source User doesn't exist!")
    else:
        target_user_pub_key = getTupleFromDB(TableNames.USER, target_username)[UserAttributes.PUBLIC_KEY]
        source_user_pub_key = getTupleFromDB(TableNames.USER, source_username)[UserAttributes.PUBLIC_KEY]
        tx_transfer = b.create_transaction(source_user_pub_key, target_user_pub_key, asset_id, Operations.TRANSFER)
        tx_transfer_signed = b.sign_transaction(tx_transfer, sourceuser_priv_key)
        b.write_transaction(tx_transfer_signed)
        time.sleep(5)
        return jsonify(status="success", errorMessage="Voucher Successfully Trasferred")


# Following are the utility methods

def checkIfTheUserExists(userName):
    return_data = r.db(TableNames.BIGCHAIN).table(TableNames.USER).get(userName).count().run(conn)
    if(return_data >0):
        return True
    else:
        return False


def constructUserTuple(username, password, type, public_key,private_key):
    data = {}
    data[UserAttributes.USERNAME] = username
    data[UserAttributes.PASSWORD] = password
    data[UserAttributes.TYPE] = type
    data[UserAttributes.PUBLIC_KEY] = public_key
    data[UserAttributes.PRIVATE_KEY] = private_key
    return data

def getTupleFromDB(tableName,primary_key):
    return r.db(TableNames.BIGCHAIN).table(tableName).get(primary_key)

def insertData(tableName,data):
    r.db(TableNames.BIGCHAIN).table(tableName).insert(data).run(conn)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)



