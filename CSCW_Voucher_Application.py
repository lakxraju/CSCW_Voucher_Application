from flask import Flask
from flask import request
from flask import jsonify
from flask import json
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
    DONOR = "1"
    CONSUMER = "2"
    COMPANY = "3"

class Operations(Enum):
    CREATE = "CREATE"
    TRANSFER = "TRANSFER"

class TableNames(Enum):
    USER = "user_table"
    BIGCHAIN = "bigchain"

class DatabaseNames(Enum):
    CUSTOM_DB = "custom_db"
    BIGCHAIN = "bigchain"

b = Bigchain()
conn = r.connect("localhost", 28015)
#Adding the userdatabase and table if it does't exist
if not r.dbList().contains(DatabaseNames.CUSTOM_DB.value).run(conn):
    r.dbCreate(DatabaseNames.CUSTOM_DB.value).run(conn)
if not r.db(DatabaseNames.CUSTOM_DB.value).tableList().contains(TableNames.USER.value).run(conn):
    r.db(DatabaseNames.CUSTOM_DB.value).tableCreate(TableNames.USER.value,{'primary_key':'username'}).run(conn)

@app.route('/voucherApp/createUser', methods=['POST'])
def createUser():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value,required=True, type=str)
    parser.add_argument(UserAttributes.PASSWORD.value, required=True, type=str)
    parser.add_argument(UserAttributes.TYPE.value, required=True, type=str)

    username = request.get_json(force=False)[UserAttributes.USERNAME.value]
    password = request.get_json(force=False)[UserAttributes.PASSWORD.value]
    type = request.get_json(force=False)[UserAttributes.TYPE.value]


    if(not checkIfTheUserExists(username)):
        user_priv, user_pub = crypto.generate_key_pair()
        userTuple = constructUserTuple(username,password,type,user_pub,user_priv)
        insertData(DatabaseNames.CUSTOM_DB.value,TableNames.USER.value,userTuple)
        return jsonify(status="success",publicKey=user_pub,privateKey=user_priv)
    else:
        return jsonify(status="error", errorMessage="Username Already Exists!")


@app.route('/voucherApp/signIn',methods=['POST'])
def signIn():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)
    parser.add_argument(UserAttributes.PASSWORD.value, required=True, type=str)

    username = request.get_json(force=False)[UserAttributes.USERNAME.value]
    password = request.get_json(force=False)[UserAttributes.PASSWORD.value]

    if(checkIfTheUserExists(username)):
        tupleData = getTupleFromDB(DatabaseNames.CUSTOM_DB.value,TableNames.USER.value,username)
        if(tupleData[UserAttributes.PASSWORD.value] == password):
            return jsonify(status="success",publicKey=tupleData[UserAttributes.PUBLIC_KEY.value],privateKey=tupleData[UserAttributes.PRIVATE_KEY.value])
        else:
            return jsonify(status="error",errorMessage="Password Incorrect!")
    else:
        return jsonify(status="error", errorMessage="User doesn't exist!")


@app.route('/voucherApp/createVoucher',methods=['POST'])
def createVoucher():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)
    parser.add_argument('value', required=True, type=str)
    parser.add_argument('voucher_name', required=True, type=str)


    voucherName = request.get_json(force=False)['voucher_name']
    username = request.get_json(force=False)[UserAttributes.USERNAME.value]
    value = request.get_json(force=False)['value']

    if(not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    elif(not UserType.DONOR.value == getUserType(username)):
        return jsonify(status="error", errorMessage="Invalid Operation for the current User!")
    else:
        voucherPayload = {}
        voucherPayload["name"] = voucherName
        voucherPayload["value"] = value
        user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value,TableNames.USER.value,username)[UserAttributes.PUBLIC_KEY.value]
        tx = b.create_transaction(b.me, user_pub_key, None, Operations.CREATE.value, payload=voucherPayload)
        tx_signed = b.sign_transaction(tx, b.me_private)
        userData = {}

        if b.is_valid_transaction(tx_signed):
            b.write_transaction(tx_signed)
            #b.validate_transaction(tx_signed)
            time.sleep(10)
            ownedIDs = b.get_owned_ids(user_pub_key)
            for k in ownedIDs:
                txn = b.get_transaction(k["txid"])
                k["name"] = txn["transaction"]["data"]["payload"]["name"]
                k["value"] = txn["transaction"]["data"]["payload"]["value"]
            userData["txnDetails"] = ownedIDs
            userData["username"] = username
            userData["usertype"] = getUserType(username)
        else:
            return jsonify(status="error", errorMessage="Transaction not valid!")

        return json.dumps(userData)


@app.route('/',methods=['GET','POST'])
def testConnection():
    return jsonify(status="success", errorMessage="Server Available!")




@app.route('/voucherApp/getOwnedIDs',methods=['GET'])
def getOwnedIDs():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)

    username = request.args.get(UserAttributes.USERNAME.value)
    if (not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    else:
        user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value,TableNames.USER.value, username)[UserAttributes.PUBLIC_KEY.value]
        ownedIDs = b.get_owned_ids(user_pub_key)
        for k in ownedIDs:
            txn = b.get_transaction(k["txid"])
            print(txn)
            k["name"] = txn["transaction"]["data"]["payload"]["name"]
            k["value"] = txn["transaction"]["data"]["payload"]["value"]

        userData = {}
        userData["txnDetails"] = ownedIDs
        userData["username"] = username
        userData["usertype"] = getUserType(username)

        return json.dumps(userData)


@app.route('/voucherApp/transferVoucher',methods=['POST'])
def transferVoucher():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.TARGET_USERNAME.value, required=True, type=str)
    parser.add_argument(UserAttributes.SOURCE_USERNAME.value, required=True, type=str)
    parser.add_argument(UserAttributes.PRIVATE_KEY.value, required=True, type=str)
    parser.add_argument('asset_id', required=True, type=str)
    parser.add_argument('cid', required=True, type=str)


    source_username = request.get_json(force=False)[UserAttributes.SOURCE_USERNAME.value]
    target_username = request.get_json(force=False)[UserAttributes.TARGET_USERNAME.value]
    sourceuser_priv_key = request.get_json(force=False)[UserAttributes.PRIVATE_KEY.value]
    asset_id = request.get_json(force=False)['asset_id']
    cid = request.get_json(force=False)['cid']

    if (not checkIfTheUserExists(target_username)):
        return jsonify(status="error", errorMessage="Target User doesn't exist!")
    elif(not checkIfTheUserExists(source_username)):
        return jsonify(status="error", errorMessage="Source User doesn't exist!")
    elif(not isTransferValid(source_username,target_username)):
        return jsonify(status="error", errorMessage="Transaction is not valid between the intended Users!")
    else:
        target_user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value,TableNames.USER.value, target_username)[UserAttributes.PUBLIC_KEY.value]
        source_user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value,TableNames.USER.value, source_username)[UserAttributes.PUBLIC_KEY.value]
        print(sourceuser_priv_key)
        tx = {}
        tx["txid"] = asset_id
        tx["cid"] = cid
        asset = b.get_transaction(asset_id)
        tx_transfer = b.create_transaction(source_user_pub_key, target_user_pub_key, tx, Operations.TRANSFER.value,payload=asset["transaction"]["data"]["payload"])
        tx_transfer_signed = b.sign_transaction(tx_transfer, sourceuser_priv_key)

        if b.is_valid_transaction(tx_transfer_signed):
            b.write_transaction(tx_transfer_signed)
            #b.validate_transaction(tx_transfer_signed)
            time.sleep(10)
            return jsonify(status="success", message="Voucher Successfully Trasferred")
        else:
            print("Error While transferring an asset: Not a valid Transaction!")
            print("Source Username:"+ source_username + "   --Source Pub Key:"+ source_user_pub_key)
            print("Target Username:"+ target_username + "   --Target Pub Key:"+ target_user_pub_key)
            return jsonify(status="error", errorMessage="Transaction is not valid")


# Following are the utility methods

def checkIfTheUserExists(userName):
    return_data = r.db("bigchain").table(TableNames.USER.value).get(userName).count().default(0).run(conn)
    if(return_data >0):
        return True
    else:
        return False


def constructUserTuple(username, password, type, public_key,private_key):
    data = {}
    data[UserAttributes.USERNAME.value] = username
    data[UserAttributes.PASSWORD.value] = password
    data[UserAttributes.TYPE.value] = type
    data[UserAttributes.PUBLIC_KEY.value] = public_key
    data[UserAttributes.PRIVATE_KEY.value] = private_key
    return data

def getUserType(username):
    userTuple = getTupleFromDB(DatabaseNames.CUSTOM_DB.value,TableNames.USER.value,username)
    if(userTuple[UserAttributes.TYPE.value]=="1"):
        return UserType.DONOR.value
    elif(userTuple[UserAttributes.TYPE.value]=="2"):
        return UserType.CONSUMER.value
    elif(userTuple[UserAttributes.TYPE.value]=="3"):
        return UserType.COMPANY.value

def isTransferValid(username1,username2):
    userType1 = getUserType(username1)
    userType2 = getUserType(username2)
    if(userType1==UserType.DONOR.value and userType2==UserType.CONSUMER.value):
        return True
    elif(userType1==UserType.CONSUMER.value and userType2==UserType.COMPANY.value):
        return True
    elif(userType1==UserType.COMPANY.value and userType2==UserType.DONOR.value):
        return True
    else:
        return False

def getTupleFromDB(dbName,tableName,primary_key):
    return r.db(dbName).table(tableName).get(primary_key).run(conn)

def insertData(dbName,tableName,data):
    r.db(dbName).table(tableName).insert(data).run(conn)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)



