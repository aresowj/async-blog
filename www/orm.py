#coding = utf-8
__author__ = 'aresowj'

'''
orm.py
Database connection module for MySQL.
Using aoimysql to keep implementing async methods in all program layers.
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

#The instance of Model will be substantiated with the __new__ method in metaclass ModelMetaclass
class ModelMetaclass(type):
	def __new__(cls, name, bases, attrs):
		#Excluding the Model class itself
		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)
		#Get name of table
		tableName = attrs.get('__table__', None) or name
		logging.info('Found model: %s (table: %s)' % (name, tableName))
		#Get all the Field and Primary Keys
		mappings = dict()
		fileds = []
		primaryKey = None
		for k, v in attrs.items():
			if isinstance(v, Field):
				logging.info('	Found mapping: %s => %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					#Primary Key found
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.append(k)
			if not primaryKey:
				raise RuntimeError('Primary key not found.')
			for k in mappings.keys():
				attrs.pop(k)
			escaped_fields = list(map(lambda f: '`%s`' % f, fields))
			attrs['__mappings__'] = mappings
			attrs['__table__'] = tableName
			attrs['__primary_key__'] = primaryKey
			attrs['__fields__'] = fields
			#Constructing default syntax for select, insert, update and delete
			attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
			attrs['__insert__'] = 'insert into `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
			attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
			return type.__new__(cls, name, bases, attrs)

#Create a class using metaclass ModelMetaclass		
class Model(dict, metaclass=ModelMetaclass):
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)	#Using init() in ModelMetaclass
		
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" % key)
			
	def __setattr__(self, key, value):
		self[key] = value
		
	def getValue(self, key):
		return getattr(self, key, None)
		
	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(filed.default) else field.default
				logging.debug('Using default value for %s: %s' & (key, str(value)))
				setattr(self, key, value)
		return value
	
class Field(object):
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default
		
	def __str__(self):
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)
		
class StringField(Field):
	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		super().__init__(name, ddl, primary_key, default)
		
