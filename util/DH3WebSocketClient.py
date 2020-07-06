import ssl
import websocket
import json
import datetime
import os
from sys import argv

args = argv[1:]
if len(args)==0:
	print("Usage:")
	print("\t%s <out-files ...>" % argv[0])
	sys.exit(0)

URL="wss://dh3-server1.diamondhunt.co/"
USER=os.getenv("DH3_USER")
PASS=os.getenv("DH3_PASS")
now=datetime.datetime.utcnow().isoformat()+'Z'
ws = websocket.create_connection(URL, sslopt={"cert_reqs": ssl.CERT_NONE})

# auth
message = "LOGIN=%s~%s" % (USER, PASS)
print("SEND: "+message)
ws.send(message)

tradables = None
market = None

while(True):
	message = ws.recv()
	if message is None:
		break
	#print("--DEBUG-- RECV: "+message)
	message = message.strip()
	
	if "LOGIN" in message:
		print("RECV: "+message)
		message = "LAST_TAB=right-market"
		print("SEND: "+message)
		ws.send(message)
		message = "REFRESH_TRADABLES"
		print("SEND: "+message)
		ws.send(message)
		
	if "Invalid" in message:
		print("RECV: "+message)
		ws.close()
		break
		
	if message.startswith("REFRESH_TRADABLES") and "~" in message:
		print("RECV: REFRESH_TRADABLES")
		print("RECV: "+message)
		tradables = message
		if tradables is not None and market is not None:
			ws.close()
			break
		
	if message.startswith("REFRESH_MARKET") or message.startswith("REFESH_MARKET"):
		print("RECV: REF[R]ESH_MARKET")
		print("RECV: "+message)
		market = message
		if tradables is not None and market is not None:
			ws.close()
			break
		
	
ws.close()

if market is not None and tradables is not None:
	
	if tradables.startswith("REFRESH_TRADABLES"):
		tradables = tradables[len("REFRESH_TRADABLES="):]
	elif tradables.startswith("REFESH_TRADABLES"):
		tradables = tradables[len("REFESH_TRADABLES="):]
	print("TRD:"+tradables)
	tradables = tradables.split("~")
	items = {}
	while len(tradables)>0:
		item = tradables[0]
		min = int(tradables[1])
		max = int(tradables[2])
		category = tradables[3]
		tradables = tradables[4:]
		items[item] = {
			"item": item,
			"hardMin": min,
			"hardMax": max,
			"category": category,
			"amount": 0,
			"min": -1,
			"max": -1,
			"average": 0
		}
	
	if market.startswith("REFRESH_MARKET"):
		market = market[len("REFRESH_MARKET="):]
	elif market.startswith("REFESH_MARKET"):
		market = market[len("REFESH_MARKET="):]
	market = market.split("~")
	while len(market)>0:
		item = market[2]
		amount = int(market[3])
		price = int(market[4])
		market = market[9:]
		if item not in items.keys():
			continue
		obj = items[item]
		if obj is not None:
			obj["amount"] += amount
			obj["average"] += price*amount
			if obj["min"] == -1 or price < obj["min"]:
				obj["min"] = price
			if obj["max"] == -1 or price > obj["max"]:
				obj["max"] = price
	for key, value in items.items():
		if value["amount"] != 0:
			value["average"] /= value["amount"]
	marketData = {
		"time": now,
		"items": items
	}
	for file in args:
		with open(file, "w") as f:
			f.write(json.dumps(marketData))
