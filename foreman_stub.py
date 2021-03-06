#!/usr/bin/env python

"""Foreman API v2 stub server."""

import glob
import json
import os

from collections import defaultdict
from urllib.parse import urlparse

from flask import Flask, jsonify, request


DEBUG = os.getenv('DEBUG', 'false').lower() not in ('false', '0', '', 'off')

if DEBUG:
    import pip
    pip.main(['install', 'q', 'epdb'])

app = Flask(__name__)

PAGECACHE = defaultdict(dict)


@app.before_first_request
def build_pagecache():
    """Read JSON fixtures into in-memory cache."""
    jfiles = glob.glob('fixtures/*.json')
    for jfile in jfiles:
        with open(jfile, 'r') as f:
            jdata = json.load(f)
        key = urlparse(jdata['url']).path[7:]
        subkey = jdata['page']
        PAGECACHE[key][subkey] = jdata['data']


def get_page_num():
    """Return page number if present."""
    pagenum = request.args.get('page')
    if pagenum:
        pagenum = int(pagenum)
    return pagenum


@app.route('/api/v2/hosts')
@app.route('/api/v2/hosts/<hostid>')
@app.route('/api/v2/hosts/<hostid>/facts')
def get_hosts(hostid=None):
    """Render fixture contents from cache."""
    pagenum = get_page_num()

    cache_key = '/hosts'
    if hostid is not None:
        cache_key = f'{cache_key}/{hostid}'

    resp = PAGECACHE[cache_key]
    try:
        if not request.path.endswith('/facts'):
            resp = resp[pagenum]
    except KeyError:
        if DEBUG:
            import q; q/cache_key; q/pagenum; q/hostid
            import epdb; epdb.st()
    else:
        return jsonify(resp)


@app.route('/ping')
@app.route('/heartbeat')
def ping_heartbeat():
    return jsonify({"status": "ok", "response": "pong"})


__name__ == '__main__' and app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), threaded=True, debug=DEBUG)
