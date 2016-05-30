from flask import Flask
from flask import request
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

def checkIfTheUserExists(userName):

    return False

@app.route('/voucherApp/createUser', methods=['GET'])
def createUser():
    username = request.args.get('username')
    password = request.args.get('password')
    type = request.args.get('type')
    return username+password+type



@app.route('/')
def hello_world():


    # Create a test user
    testuser1_priv, testuser1_pub = crypto.generate_key_pair()
    testuser2_priv, testuser2_pub = crypto.generate_key_pair()

    # Define a digital asset data payload
    digital_asset_payload = {'msg': 'Hello BigchainDB!'}

    # A create transaction uses the operation `CREATE` and has no inputs
    tx = b.create_transaction(b.me, testuser1_pub, None, 'CREATE', payload=digital_asset_payload)

    # All transactions need to be signed by the user creating the transaction
    tx_signed = b.sign_transaction(tx, b.me_private)

    # Write the transaction to the bigchain.
    # The transaction will be stored in a backlog where it will be validated,
    # included in a block, and written to the bigchain
    b.write_transaction(tx_signed)

    time.sleep(10)

    # Retrieve the transaction with condition id
    tx_retrieved_id = b.get_owned_ids(testuser1_pub).pop()

    # touhid_pub = "4pP1W1hRXGfTFmRotmyrdmx8HSYGqK7MJ7PwdLS5CLTf"
    # Create a transfer transaction
    tx_transfer = b.create_transaction(testuser1_pub, testuser2_pub, tx_retrieved_id, 'TRANSFER')

    # Sign the transaction
    tx_transfer_signed = b.sign_transaction(tx_transfer, testuser1_priv)

    # Write the transaction
    b.write_transaction(tx_transfer_signed)

    time.sleep(10)

    # Check if the transaction is already in the bigchain
    tx_transfer_retrieved = b.get_transaction(tx_transfer_signed['id'])
    print(tx_transfer_retrieved)
    print("Transferred Successfully")

    return testuser2_pub


@app.route('/rethinkdb')
def hello_world1():
    r.db("bigchain").table("user_table").insert([
        {"name": "William Adama", "tv_show": "Battlestar Galactica",
         "posts": [
             {"title": "Decommissioning speech", "content": "The Cylon War is long over..."},
             {"title": "We are at war", "content": "Moments ago, this ship received..."},
             {"title": "The new Earth", "content": "The discoveries of the past few days..."}
         ]
         },
        {"name": "Laura Roslin", "tv_show": "Battlestar Galactica",
         "posts": [
             {"title": "The oath of office", "content": "I, Laura Roslin, ..."},
             {"title": "They look like us", "content": "The Cylons have the ability..."}
         ]
         },
        {"name": "Jean-Luc Picard", "tv_show": "Star Trek TNG",
         "posts": [
             {"title": "Civil rights", "content": "There are some words I've known since..."}
         ]
         }
    ]).run(conn)
    return "Done"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)



