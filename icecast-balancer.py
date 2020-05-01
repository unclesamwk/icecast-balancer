#!/usr/bin/env python3
from flask import Flask, redirect, request, jsonify
import requests
import json
import os

# check if ICECAST_SERVERS env exists
if os.getenv("ICECAST_SERVERS") is None:
    print("Please give me icecastservers as ICECAST_SERVERS env!")
    print("ICECAST_SERVERS='server1.example.com,server2.example.com'")
    exit(1)

# split icecast server into an python list
ICECAST_SERVERS = os.environ['ICECAST_SERVERS'].split(",")
print("icecast-balancer starts with following server ...")
print(ICECAST_SERVERS)


def get_listeners_from_icecast_servers():

    server_listeners = {}

    for server in ICECAST_SERVERS:
        try:
            r = requests.get(
                "http://{server}/status-json.xsl".format(server=server))
            r.raise_for_status()
        except:
            # if icecastserver is not reachable continue with next icecastserver
            continue

        # iterate over json-status.xsl from icecastserver and sum listeners from all mountpoints
        data = json.loads(r.text)
        if "source" in data["icestats"]:
            listeners = data["icestats"]["source"]
            listeners_sum = []
            if isinstance(listeners, list):
                for source in listeners:
                    listeners_sum.append(source["listeners"])

            if isinstance(listeners, dict):
                listeners_sum.append(listeners["listeners"])

            server_listeners[server] = sum(listeners_sum)

    sorted_server_listeners = {k: v for k, v in sorted(
        server_listeners.items(), key=lambda item: item[1])}

    return sorted_server_listeners


# set flask app
app = Flask(__name__)

# balancer route
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def icecast_redirector(path):
    if not path:
        return jsonify({"message": "Please give me an stream path!"}), 400

    SECURE = "http"

    if 'HTTP_X_FORWARDED_PROTO' in request.environ:
        SECURE = request.environ["HTTP_X_FORWARDED_PROTO"]

    if request.is_secure:
        SECURE = "https"

    listeners = get_listeners_from_icecast_servers()

    if not listeners:
        return jsonify({"message": "No iceastrelay is reachable!"}), 400

    for server in listeners:
        return redirect("{secure}://{server}/{path}".format(secure=SECURE, server=server, path=path))

# status route
@app.route('/status')
def icecast_status():

    listeners = get_listeners_from_icecast_servers()

    if not listeners:
        return jsonify({"message": "No iceastrelay is reachable!"}), 400

    sorted_relays = {k: v for k, v in sorted(
        listeners.items(), key=lambda item: item[1])}

    return jsonify(sorted_relays)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
