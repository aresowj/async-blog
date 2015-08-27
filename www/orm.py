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

def log(sql, args=()):
    logging.info('SQL: %s' % sql)

def create_args_string(length):
	L = []
	for n in range(length):
		L.append('?')
		
	return ', '.join(L)

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
		password = kw['password'],
		db = kw['db'],
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

#The instance of Model will be substantiated with the __new__ method in metaclass ModelMetaClass
class ModelMetaClass(type):
	def __new__(cls, name, bases, attrs):
		#Excluding the Model class itself
		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)
		#Get name of table
		tableName = attrs.get('__table__', None) or name
		logging.info('Found model: %s (table: %s)' % (name, tableName))
		#Get all the Field and Primary Keys
		mappings = dict()
		fields = []
		primaryKey = None
		for k, v in attrs.items():
			if isinstance(v, Field):
				logging.info('	Found mapping: %s => %s' % (k, v))
				mappings[k] = v		#Store the mapping if v is a Field instance
				if v.primary_key:
					#Primary Key found
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.append(k)	#Append elements not primary key into the fields list
		if not primaryKey:		#Must get a primary key
			raise RuntimeError('Primary key not found.')
		for k in mappings.keys():
			attrs.pop(k)	#Remove all the elements processed.
		escaped_fields = list(map(lambda f: '`%s`' % f, fields))	#Generate a list of attributes transferred to str for SQL
		
		#Re-define the attrs for passing to the new class
		attrs['__mappings__'] = mappings
		attrs['__table__'] = tableName
		attrs['__primary_key__'] = primaryKey
		attrs['__fields__'] = fields
		#Constructing default syntax for select, insert, update and delete
		attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
		
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
			tableName, 		#First parameter
			', '.join(escaped_fields), 		#List of columns
			primaryKey, 	#Put primary key at last
			create_args_string(len(escaped_fields)+1)
			)
		
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
		return type.__new__(cls, name, bases, attrs)	#Pass the new attrs to the subclass

#Create a class using metaclass ModelMetaClass		
class Model(dict, metaclass=ModelMetaClass):
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)	#Using init() in ModelMetaClass
		
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
				value = field.default() if callable(field.default) else field.default
				logging.debug('Using default value for %s: %s' % (key, str(value)))
				setattr(self, key, value)
		return value
		
	@classmethod
	def findAll(cls, where=None, args=None, **kw):
		'''
		Find objects by where clause.'
		'''
		sql = [cls.__select__]
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:
			args = []
		orderBy = kw.get('orderBy', None)
		if orderBy:
			sql.append('order by')
			sql.append(orderBy)
		limit = kw.get('limit', None)
		if limit is not None:
			sql.append('limit')
			if isinstance(limit, int):
				sql.append('?')
				args.append(limit)
			elif isinstance(limit, tuple) and len(limit) == 2:
				sql.append('?, ?')
				args.extend(limit)
			else:
				raise ValueError('Invalid limit value: %s' % str(limit))
		rs = yield from select(' '.join(sql), args)
		return [cls(**r) for r in rs]
		
	@asyncio.coroutine
	def find(cls, pk):
		'''Find object by primary key.'''
		rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
		if len(rs) == 0:
			return None
		return cls(**rs[0])
		
	@asyncio.coroutine
	def save(self):
		args = list(map(self.getValueOrDefault, self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = yield from execute(self.__insert__, args)
		if rows != 1:
			logging.warn('Failed to insert record: affected rows: %s' % rows)
	
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
		
class BooleanField(Field):
	def __init__(self, name=None, default=False):
		super().__init__(name, 'boolean', False, default)
		
class FloatField(Field):
	def __init__(self, name=None, primary_key=False, default=0.0):
		super().__init__(name, 'real', primary_key, default)
	
class IntegerField(Field):
	def __init__(self, name=None, primary_key=False, default=0):
		super().__init__(name, 'bigint', primary_key, default)
		
class TextField(Field):
	def __init__(self, name=None, default=None):
		super().__init__(name, 'text', False, default)
		