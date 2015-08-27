#coding = utf-8
__author__ = 'aresowj'

'''
models.py
Set up basic models.
'''

import time, uuid
from orm import Model, StringField, BooleanField, FloatField, TextField

def next_id():
	#Generate random ID with time (15 digits) and uuid4 (random hex)
	return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
	__table__ = 'users'
	
	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')	#Passing next_id for future initiation.
	email = StringField(ddl='varchar(50)')
	password = StringField(ddl='varchar(50)')
	admin = BooleanField()
	name = StringField(ddl='varchar(50)')
	image = StringField(ddl='varchar(500)')
	created_time = FloatField(default=time.time)
	
class Blog(Model):
	__table__ = 'blogs'
	
	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
	user_id = StringField(ddl='varchar(50)')
	user_name = StringField(ddl='varchar(50)')
	user_image = StringField(ddl='varchar(500)')
	title = StringField(ddl='varchar(50)')
	summary = StringField(ddl='varchar(200)')
	context = TextField()
	created_time = FloatField(default=time.time)
	
class Comment(Model):
	__table__ = 'comments'
	
	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
	blog_id = StringField(ddl='varchar(50)')
	user_id = StringField(ddl='varchar(50)')
	user_name = StringField(ddl='varchar(50)')
	user_image = StringField(ddl='varchar(500)')
	context = TextField()
	created_time = FloatField(default=time.time)