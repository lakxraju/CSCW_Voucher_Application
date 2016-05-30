import json
import rethinkdb as r

conn = r.connect("localhost", 28015)

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
'''
return_data = r.db("bigchain").table("user_table").get("lrajendran").run(conn)
print(return_data)
print(return_data["password"])
print(return_data["private_key"])


