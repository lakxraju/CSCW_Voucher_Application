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

conn = r.connect("192.168.0.38", 28015)

class TableNames(Enum):
    USER = "user_table"
    BIGCHAIN = "bigchain"


class DatabaseNames(Enum):
    CUSTOM_DB = "custom_db"
    BIGCHAIN = "bigchain"

def getBlockDetails():
    # Specifying Mandatory Arguments
    #parser = reqparse.RequestParser()
    #parser.add_argument("blockNumber", required=True, type=int)
    #username = request.args.get("blockNumber")

    if(r.db(DatabaseNames.BIGCHAIN.value).table(TableNames.BIGCHAIN.value).filter({"block_number":1}).count().run(conn) > 0):
        print(r.db(DatabaseNames.BIGCHAIN.value).table(TableNames.BIGCHAIN.value).filter({"block_number":1}).run(conn))
    else:
        return jsonify(errorMessage = "Queried Block Number doesn't exist!")

getBlockDetails()