#coding = utf-8
__author__ = 'aresowj'

'''
orm.py
Database connection module for MySQL.
Using aoimysql to keep implementing async methods in all program layers.
'''

import logging

import asyncio, aiomysql
from coroweb import get, post

