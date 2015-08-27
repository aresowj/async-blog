#coding = utf-8
__author__ = 'aresowj'

'''
handlers, to be filled.
'''

import re, time, json, logging, hashlib, base64, asyncio
from coroweb import get, post

@get('/')
def index(request):
	users = yield from User.findAll()
	return {
		'__template__' : 'test.html',
		'users' : users
	}