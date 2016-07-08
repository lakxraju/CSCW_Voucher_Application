from flask import Flask, render_template, send_from_directory
from flask import request
from flask import jsonify
from flask import json
from bigchaindb import Bigchain
from bigchaindb import crypto
from flask_restful import reqparse
import rethinkdb as r
from flask.ext.cors import CORS
import time
import os
import datetime
from enum import Enum

from werkzeug.debug import DebuggedApplication

app = Flask(__name__)
CORS(app)


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
# Adding the user database and table if it does't exist
if not r.db_list().contains(DatabaseNames.CUSTOM_DB.value).run(conn):
    r.db_create(DatabaseNames.CUSTOM_DB.value).run(conn)
if not r.db(DatabaseNames.CUSTOM_DB.value).table_list().contains(TableNames.USER.value).run(conn):
    r.db(DatabaseNames.CUSTOM_DB.value).table_create(TableNames.USER.value, primary_key='username').run(conn)


@app.route('/voucherApp/createUser', methods=['POST'])
def createUser():
    """
    :arg username: Desired Username of the user to be created
    :arg password: Intended password
    :arg type: Type of the user: This can be one of the following strings: 1.CUSTOMER 2. DONOR 3. COMPANY
    :return: status of the operation and the keypairs when the user creation is success! If there is some error, it sends the errorMessage as well.

    """
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)
    parser.add_argument(UserAttributes.PASSWORD.value, required=True, type=str)
    parser.add_argument(UserAttributes.TYPE.value, required=True, type=str)

    username = request.get_json(force=False)[UserAttributes.USERNAME.value]
    password = request.get_json(force=False)[UserAttributes.PASSWORD.value]
    type = request.get_json(force=False)[UserAttributes.TYPE.value]

    if (not checkIfTheUserExists(username)):
        user_priv, user_pub = crypto.generate_key_pair()
        userTuple = constructUserTuple(username, password, type, user_pub, user_priv)
        insertData(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, userTuple)
        return jsonify(status="success", publicKey=user_pub, privateKey=user_priv)
    else:
        return jsonify(status="error", errorMessage="Username Already Exists!")


@app.route('/voucherApp/signIn', methods=['POST'])
def signIn():
    """
    :arg username: Username of the user to log in
    :arg password: password of the username provided
    :return: Returns the error message if the username or password is incorrect. Else, it returns public, private keypairs and the type of the user.

    """
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)
    parser.add_argument(UserAttributes.PASSWORD.value, required=True, type=str)

    username = request.get_json(force=False)[UserAttributes.USERNAME.value]
    password = request.get_json(force=False)[UserAttributes.PASSWORD.value]

    if (checkIfTheUserExists(username)):
        tupleData = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, username)
        if (tupleData[UserAttributes.PASSWORD.value] == password):
            return jsonify(status="success", publicKey=tupleData[UserAttributes.PUBLIC_KEY.value],
                           privateKey=tupleData[UserAttributes.PRIVATE_KEY.value])
        else:
            return jsonify(status="error", errorMessage="Password Incorrect!")
    else:
        return jsonify(status="error", errorMessage="User doesn't exist!")


@app.route('/voucherApp/createVoucher', methods=['POST'])
def createVoucher():
    """
    :arg username: Username of the current user
    :arg voucher_name: name of the voucher to be created. This name should be same as an existing company name
    :arg value: value of the voucher. For now, it is just a string and doesn't play a key role
    :return: Returns the error message if the username or password is incorrect. Else, it returns public, private keypairs and the type of the user.

    """
    #Specifying Mandatory Arguments
    print('in create voucher')
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)
    parser.add_argument('value', required=True, type=str)
    parser.add_argument('voucher_name', required=True, type=str)

    voucherName = request.get_json(force=False)['voucher_name']
    username = request.get_json(force=False)[UserAttributes.USERNAME.value]
    value = request.get_json(force=False)['value']

    if (not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    elif (not UserType.DONOR.value == getUserType(username)):
        return jsonify(status="error", errorMessage="Invalid Operation for the current User!")
    elif (not checkIfTheUserExists(voucherName)):
        return jsonify(status="error", errorMessage="Company doesn't exist! Please check the name of the voucher!")
    elif (not UserType.COMPANY.value == getUserType(voucherName)):
        return jsonify(status="error", errorMessage="Voucher name is not valid! Hint: Voucher name should match a company")
    else:
        print('creating voucher payload')
        voucherPayload = {}
        voucherPayload["name"] = voucherName # its also the company name
        voucherPayload["value"] = value
        voucherPayload["from"] = username
        voucherPayload["to"] = username
        voucherPayload["donor_name"] = username
        user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, username)[
            UserAttributes.PUBLIC_KEY.value]
        tx = b.create_transaction(b.me, user_pub_key, None, Operations.CREATE.value, payload=voucherPayload)
        tx_signed = b.sign_transaction(tx, b.me_private)
        userData = {}

        if b.is_valid_transaction(tx_signed):
            print('writing transaction')
            b.write_transaction(tx_signed)
            # b.validate_transaction(tx_signed)
            time.sleep(10)
            ownedIDs = b.get_owned_ids(user_pub_key)
            for k in ownedIDs:
                txn = b.get_transaction(k["txid"])
                k["name"] = txn["transaction"]["data"]["payload"]["name"]
                k["value"] = txn["transaction"]["data"]["payload"]["value"]
                k["from"] = txn["transaction"]["data"]["payload"]["from"]
                k["to"] = txn["transaction"]["data"]["payload"]["to"]
            userData["txnDetails"] = ownedIDs
            userData["username"] = username
            userData["usertype"] = getUserType(username)
        else:
            print("Transaction no valid!")
            return jsonify(status="error", errorMessage="Transaction not valid!")
        print('In Create Voucher: Voucher created: Details Below')
        print(userData)
        return json.dumps(userData)

@app.route('/voucherApp/createAndTransferVoucher', methods=['POST'])
def createAndTransferVoucher():
    """
    :arg source_username: Username of the current user
    :arg voucher_name: name of the voucher to be created. This name should be same as an existing company name
    :arg value: value of the voucher. For now, it is just a string and doesn't play a key role
    :return: Returns the error message if the source_username or password is incorrect. Else, it returns public, private keypairs and the type of the user.

    """
    #Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.SOURCE_USERNAME.value, required=True, type=str)
    parser.add_argument('value', required=True, type=str)
    parser.add_argument('voucher_name', required=True, type=str)

    voucherName = request.get_json(force=False)['voucher_name']
    source_username = request.get_json(force=False)[UserAttributes.SOURCE_USERNAME.value]
    value = request.get_json(force=False)['value']
    data = r.db(DatabaseNames.CUSTOM_DB.value).table(TableNames.USER.value).filter({'type': UserType.CONSUMER.value}).pluck('source_username').run(conn)
    customerList = list(data)
    non_transferred_assets = []

    if (not checkIfTheUserExists(source_username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    elif (not UserType.DONOR.value == getUserType(source_username)):
        return jsonify(status="error", errorMessage="Invalid Operation for the current User!")
    if (not checkIfTheUserExists(voucherName)):
        return jsonify(status="error", errorMessage="Company doesn't exist! Please check the name of the voucher!")
    elif (not UserType.COMPANY.value == getUserType(voucherName)):
        return jsonify(status="error", errorMessage="Voucher name is not valid! Hint: Voucher name should match a company")

    for idx,currentCustomer in enumerate(customerList):
        voucherPayload = {}
        voucherPayload["name"] = voucherName # its also the company name
        voucherPayload["value"] = value
        voucherPayload["from"] = source_username
        voucherPayload["to"] = currentCustomer
        voucherPayload["donor_name"] = source_username
        voucherPayload["combo"] = source_username
        user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, currentCustomer)[
            UserAttributes.PUBLIC_KEY.value]
        tx = b.create_transaction(b.me, user_pub_key, None, Operations.CREATE.value, payload=voucherPayload)
        tx_signed = b.sign_transaction(tx, b.me_private)
        if b.is_valid_transaction(tx_signed):
            b.write_transaction(tx_signed)
        else:
            temp = {"status":"error", "errorMessage":"Transaction not valid!", "toUser":currentCustomer}
            non_transferred_assets.append(temp)

    time.sleep(10)
    if(len(non_transferred_assets) > 0):
        return jsonify(status = "error", errorMessage = "Not transferred to all. Error Occurred", non_transferred_companies=non_transferred_assets)
    else:
        return jsonify(status = "success", message = "Transferred to all")


@app.route('/Client/', methods=['GET', 'POST'])
def testConnection():
    """
    :return: Returns the index page of the voucher application

    """
    return render_template("index.html")


@app.route('/Client/<path:path>', methods=['GET'])
def sendStaticFile(path):
    """
    :return: Returns the static javascript/CSS files as requested

    """
    print("/Client/" + path)
    return send_from_directory(os.path.dirname(os.getcwd()) + "/Client/", path)


@app.route('/templates/<path:path>', methods=['GET'])
def sendStaticFile1(path):
    """
    :return: Returns the static javascript/CSS files as requested

    """
    print("/Client/" + path)
    return send_from_directory(os.path.dirname(os.getcwd()) + "/Client/templates/", path)


@app.route('/partials/<path:path>', methods=['GET'])
def sendStaticFile2(path):
    """
    :return: Returns the static javascript/CSS files as requested

    """
    print("/Client/" + path)
    return send_from_directory(os.path.dirname(os.getcwd()) + "/Client/partials/", path)

@app.route('/voucherApp/getBlockContents', methods=['GET'])
def getBlockDetails():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument("blockNumber", required=True, type=int)
    blockNumber = request.args.get("blockNumber")

    if(r.db(DatabaseNames.BIGCHAIN.value).table(TableNames.BIGCHAIN.value).filter({"block_number":int(blockNumber)}).count().run(conn) > 0):
        return jsonify(blockContents = r.db(DatabaseNames.BIGCHAIN.value).table(TableNames.BIGCHAIN.value).filter({"block_number":int(blockNumber)}).run(conn))
    else:
        return jsonify(errorMessage = "Queried Block Number doesn't exist!")

@app.route('/voucherApp/getOwnedIDs', methods=['GET'])
def getOwnedIDs():
    # Specifying Mandatory Arguments
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)

    username = request.args.get(UserAttributes.USERNAME.value)
    if (not checkIfTheUserExists(username)):
        return jsonify(status="error", errorMessage="User doesn't exist!")
    else:
        user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, username)[
            UserAttributes.PUBLIC_KEY.value]
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
        #userData = [userData]

        return json.dumps(userData)


@app.route('/voucherApp/transferVoucher', methods=['POST'])
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
    asset = b.get_transaction(asset_id)

    if (not checkIfTheUserExists(target_username)):
        return jsonify(status="error", errorMessage="Target User doesn't exist!")
    elif (not checkIfTheUserExists(source_username)):
        return jsonify(status="error", errorMessage="Source User doesn't exist!")
    elif (not isTransferValid(source_username, target_username, asset)):
        return jsonify(status="error", errorMessage="Transaction is not valid between the intended Users!")
    else:
        target_user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, target_username)[
            UserAttributes.PUBLIC_KEY.value]
        source_user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, source_username)[
            UserAttributes.PUBLIC_KEY.value]
        print(sourceuser_priv_key)
        tx = {}
        tx["txid"] = asset_id
        tx["cid"] = cid
        # asset = b.get_transaction(asset_id)

        newPayload = asset["transaction"]["data"]["payload"]
        newPayload["from"] = source_username
        newPayload["to"] = target_username
        tx_transfer = b.create_transaction(source_user_pub_key, target_user_pub_key, tx, Operations.TRANSFER.value,
                                           payload=newPayload)
        tx_transfer_signed = b.sign_transaction(tx_transfer, sourceuser_priv_key)

        if b.is_valid_transaction(tx_transfer_signed):
            b.write_transaction(tx_transfer_signed)
            # b.validate_transaction(tx_transfer_signed)
            time.sleep(10)
            return jsonify(status="success", message="Voucher Successfully Trasferred")
        else:
            print("Error While transferring an asset: Not a valid Transaction!")
            print("Source Username:" + source_username + "   --Source Pub Key:" + source_user_pub_key)
            print("Target Username:" + target_username + "   --Target Pub Key:" + target_user_pub_key)
            return jsonify(status="error", errorMessage="Transaction is not valid")



@app.route('/voucherApp/transferMultipleVouchers', methods=['POST'])
def transferMultipleVouchers():
    source_username = request.get_json(force=False)[UserAttributes.SOURCE_USERNAME.value]
    target_username = request.get_json(force=False)[UserAttributes.TARGET_USERNAME.value]
    sourceuser_priv_key = request.get_json(force=False)[UserAttributes.PRIVATE_KEY.value]
    cids = request.form.getlist("cids")
    asset_ids = request.form.getlist("asset_ids")
    non_transferred_assets = []

    for idx, value in enumerate(asset_ids):
        current_cid = cids[idx]
        current_asset = b.get_transaction(value)
        if (not checkIfTheUserExists(target_username)):
            return jsonify(status="error", errorMessage="Target User doesn't exist!")
        elif (not checkIfTheUserExists(source_username)):
            return jsonify(status="error", errorMessage="Source User doesn't exist!")
        elif (not isTransferValid(source_username, target_username, current_asset)):
            temp = {'asset_id': value, 'message': "Transaction not valid between intended users!"}
            non_transferred_assets.append(temp)
        else:
            target_user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, target_username)[
                UserAttributes.PUBLIC_KEY.value]
            source_user_pub_key = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, source_username)[
                UserAttributes.PUBLIC_KEY.value]
            print(sourceuser_priv_key)
            tx = {}
            tx["txid"] = value
            tx["cid"] = current_cid
            # asset = b.get_transaction(asset_id)

            newPayload = current_asset["transaction"]["data"]["payload"]
            newPayload["from"] = source_username
            newPayload["to"] = target_username
            tx_transfer = b.create_transaction(source_user_pub_key, target_user_pub_key, tx, Operations.TRANSFER.value,
                                               payload=newPayload)
            tx_transfer_signed = b.sign_transaction(tx_transfer, sourceuser_priv_key)

            if b.is_valid_transaction(tx_transfer_signed):
                b.write_transaction(tx_transfer_signed)
            else:
                print("Error While transferring an asset: Not a valid Transaction!")
                print("Source Username:" + source_username + "   --Source Pub Key:" + source_user_pub_key)
                print("Target Username:" + target_username + "   --Target Pub Key:" + target_user_pub_key)
                temp = {'asset_id': value, 'message': "Error While transferring an asset: Not a valid Transaction!"}
                non_transferred_assets.append(temp)

    time.sleep(10)
    if(len(non_transferred_assets)>0):
        return jsonify(status="error", details = non_transferred_assets)
    else:
        return jsonify(status="success")


@app.route('/voucherApp/companys', methods=['GET'])
def getCompanyList():
    data = r.db(DatabaseNames.CUSTOM_DB.value).table(TableNames.USER.value).filter({'type': UserType.COMPANY.value}).pluck('username').run(conn)
    dataList = list(data)
    return json.dumps(dataList)

@app.route('/voucherApp/donors', methods=['GET'])
def getDonorList():
    data = r.db(DatabaseNames.CUSTOM_DB.value).table(TableNames.USER.value).filter({'type': UserType.DONOR.value}).pluck('username').run(conn)
    dataList = list(data)
    return json.dumps(dataList)

@app.route('/voucherApp/customers', methods=['GET'])
def getCustomerList():
    data = r.db(DatabaseNames.CUSTOM_DB.value).table(TableNames.USER.value).filter({'type': UserType.CONSUMER.value}).pluck('username').run(conn)
    dataList = list(data)
    return json.dumps(dataList)

@app.route('/voucherApp/getHistory', methods=['GET'])
def get_owned_assets():
    parser = reqparse.RequestParser()
    parser.add_argument(UserAttributes.USERNAME.value, required=True, type=str)

    public_key = request.args.get(UserAttributes.USERNAME.value)
    tempresponse = r.db(DatabaseNames.BIGCHAIN.value).table(TableNames.BIGCHAIN.value).run(conn)
   # response = list(tempresponse)
    allPayloads = []
    for temprow in tempresponse:
        block_number = temprow["block_number"]
        txns = temprow["block"]["transactions"]
        temp_timestamp = float(temprow["block"]["timestamp"])
        block_timestamp = datetime.datetime.fromtimestamp(temp_timestamp).strftime('%d %b %Y %H:%M:%S')

        for txn in txns:
            temp = txn["transaction"]["data"]["payload"]
            temp['txid'] = txn['id']
            temp['datetime'] = block_timestamp
            temp['timestamp'] = temp_timestamp
            temp['blockNumber'] = block_number
            if 'from' in temp and 'to' in temp and (temp['from'] == public_key or temp['to'] == public_key):

                if temp['from'] == public_key and temp['to'] == public_key:
                    temp['type'] = 'CREATE'
                elif temp['from'] == public_key:
                    temp['type'] = 'SENT'
                    if 'combo' in temp:
                        temp1 = txn["transaction"]["data"]["payload"]
                        temp1['txid'] = txn['id']
                        temp1['datetime'] = block_timestamp
                        temp1['timestamp'] = temp_timestamp
                        temp1['type'] = "CREATE"
                        temp1['blockNumber'] = block_number
                        allPayloads.append(temp1)
                elif temp['to'] == public_key:
                    temp['type'] = 'RECEIVED'

                allPayloads.append(temp)
    return jsonify(history = allPayloads)

# Following are the utility methods

def checkIfTheUserExists(userName):
    return_data = r.db(DatabaseNames.CUSTOM_DB.value).table(TableNames.USER.value).get(userName).count().default(0).run(
        conn)
    if (return_data > 0):
        return True
    else:
        return False


def constructUserTuple(username, password, type, public_key, private_key):
    data = {}
    data[UserAttributes.USERNAME.value] = username
    data[UserAttributes.PASSWORD.value] = password
    data[UserAttributes.TYPE.value] = type
    data[UserAttributes.PUBLIC_KEY.value] = public_key
    data[UserAttributes.PRIVATE_KEY.value] = private_key
    return data


def getUserType(username):
    userTuple = getTupleFromDB(DatabaseNames.CUSTOM_DB.value, TableNames.USER.value, username)
    if (userTuple[UserAttributes.TYPE.value] == "1"):
        return UserType.DONOR.value
    elif (userTuple[UserAttributes.TYPE.value] == "2"):
        return UserType.CONSUMER.value
    elif (userTuple[UserAttributes.TYPE.value] == "3"):
        return UserType.COMPANY.value

def isTransferValid(username1, username2, voucher):
    userType1 = getUserType(username1)
    userType2 = getUserType(username2)
    if (userType1 == UserType.DONOR.value and userType2 == UserType.CONSUMER.value):
        return True
    elif (userType1 == UserType.CONSUMER.value and userType2 == UserType.COMPANY.value):
        if (voucher['transaction']['data']['payload']['name'] != username2):
            return False
        else:
            return True
    elif (userType1 == UserType.COMPANY.value and userType2 == UserType.DONOR.value):
        if (voucher['transaction']['data']['payload']['donor_name'] != username2):
            return False
        else:
            return True
    else:
        return False


def getTupleFromDB(dbName, tableName, primary_key):
    return r.db(dbName).table(tableName).get(primary_key).run(conn)


def insertData(dbName, tableName, data):
    r.db(dbName).table(tableName).insert(data).run(conn)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
