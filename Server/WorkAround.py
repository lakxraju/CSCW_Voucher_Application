import json
import rethinkdb as r
from bigchaindb import Bigchain

conn = r.connect("localhost", 28015)

def query_reql_response(response, query):
    result = list(response)

    if result and len(result):
        content = result[0]["transaction"]["data"]["payload"]["content"]
        if content:
            if (not query) or (query and query in content):
                return result
    return None


def process_response(response, query):
    result = list(response)

    if result and len(result):
        content = result[0]["transaction"]["data"]["payload"]["content"]
        if content:
            if (not query) or (query and query in content):
                return result
    return None




def get_owned_assets_backup(bigchain, vk, query=None, table='bigchain'):

    assets = []
    asset_ids = bigchain.get_owned_ids(vk)

    if table == 'backlog':
        reql_query = \
            r.table(table) \
            .filter(lambda tx: tx['transaction']['conditions']
                    .contains(lambda c: c['new_owners']
                              .contains(vk)))
        response = query_reql_response(reql_query.run(bigchain.conn), query)
        if response:
            assets += response

    elif table == 'bigchain':
        for asset_id in asset_ids:
            txid = asset_id['txid'] if isinstance(asset_id, dict) else asset_id

            reql_query = r.table(table)\
                .concat_map(lambda doc: doc['block']['transactions']) \
                .filter(lambda transaction: transaction['id'] == txid)
            response = query_reql_response(reql_query.run(bigchain.conn), query)
            if response:
                assets += response

    return assets


def get_owned_assets(bigchain, vk, query=None, table='bigchain'):

    assets = []
    tempresponse = r.db("bigchain").table(table).run(bigchain.conn)
    public_key ="cscw_donor"
   # response = list(tempresponse)
    allPayloads = []
    for temprow in tempresponse:
        txns = temprow["block"]["transactions"]
        for txn in txns:
            temp = txn["transaction"]["data"]["payload"]
            temp['txid'] = txn['id']
            if 'from' in temp and 'to' in temp and (temp['from'] == public_key or temp['to'] == public_key):

                if temp['from'] == public_key and temp['to'] == public_key:
                    temp['type'] = 'CREATE'
                elif temp['from'] == public_key:
                    temp['type'] = 'SENT'
                elif temp['to'] == public_key:
                    temp['type'] = 'RECEIVED'

                allPayloads.append(temp)
    print("Final Output:")
    print(allPayloads)


    assets = []
    return assets

b = Bigchain()
assets = get_owned_assets(b,vk="DgnY3aPBQ1ptw65C6GNWmxyPqFBSHUBRH61Wxy6KvTqz")
print(assets)



'''
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
data = {}
data["userName"]="lrajendran"
data["password"] = "12345678"
data["type"]="2"
data["public_key"]="sdfansan123214klddadnasnOjdfsjMsdafbsdfngddf"
data["private_key"]="Hasdbnasdnas2343534dfsdfnsdf2342adsd324dr32"


json_data = json.dumps(data)
print(json_data)
r.db("bigchain").table("user_table").insert(data).run(conn)


return_data = r.db("bigchain").table("user_table").get("lrajendran").count().run(conn)
print(return_data)
print(return_data>0)
if(return_data>0):
    print("Hello")
#print(return_data["password"])
#print(return_data["private_key"])

'''
