#coding = utf-8
__author__ = 'aresowj'

'''
app.py
Base frame of the web app.
Using asyncio and aiohttp to contruct the basement.
'''

import logging
logging.basicConfig(level=logging.INFO)	#Reporting events occur during normal opeartion.

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

def index(request):
	'''
	Response function for index requests.
	'''
	return web.Response(body=b'<h1>Welcome to AresOu.net</h1>')

@asyncio.coroutine
def init(loop):
	'''
	Initiation function for the whole app.
	Using Coroutine at this point.
	'''
	app = web.Application(loop=loop)	#Passing the main loop to app.
	app.router.add_route('GET', '/', index)		#When being requested the root folder by GET method, call index()
	srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 80)
	logging.info('Server started at http://127.0.0.1:80...')
	return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
