#coding = utf-8
__author__ = 'aresowj'

'''
orm.py
Database connection module for MySQL.
Using aoimysql to keep using async methods in all program layers.
'''

import logging
logging.basicConfig(level=logging.INFO)		#Reporting events occur during normal opeartion.

import asyncio, aiomysql

#Create connection pool
@asyncio.coroutine
def create_pool(loop, **kw):
	'''
	Create a connection pool. loop: the main app loop; kw: a dict of arguments for the connection settings
	'''
	logging.info('Creating database connection pool...')
	global __pool	#The pool
	__pool = yield from aiomysql.create_pool(
		host = kw.get('host', 'localhost'),
		port = kw.get('port', 3306),
		user = kw['user'],	#Must be provided
		password = kw['db'],
		charset = kw.get('charset', 'utf8'),
		autocommit = kw.get('autocommit', True),
		maxsize = kw.get('maxsize', 10),
		minsize = kw.get('minsize', 1),
		loop = loop
	)
	
@asyncio.coroutine
def select(sql, args, size=None):
	'''
	Wrapped select method. Returns a list of tuples.
	'''
	log(sql, args)
	global __pool
	with (yield from __pool) as conn:
		cur = yield from conn.cursor(aiomysql.DictCursor)
		yield from cur.execute(sql.replace('?', '%s'), args or ())
		if size:
			rs = yield from cur.fetchmany(size)		#Fetch a size of data if this parameter is passed
		else:
			rs = yield from cur.fetchall()
		yield from cur.close()
		logging.info('Rows returned: %s' % len(rs))
		return rs
		
@asyncio.coroutine
def execute(sql, args):
	'''
	Wrapped function for insert, update and delete. Returns rows affected
	'''
	log(sql)
	with (yield from __pool) as conn:
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?', '%s'), args)
			affected = cur.rowcount
			yield from cur.close()
		except BaseException as e:
			raise
		return affected		#Return rows affected
		

	