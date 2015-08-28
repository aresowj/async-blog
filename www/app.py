#coding = utf-8
__author__ = 'aresowj'

'''
app.py
Base frame of the web app.
Using asyncio and aiohttp to contruct the basement.
'''

import logging
logging.basicConfig(level=logging.INFO)    #Reporting events occur during normal opeartion.

import asyncio, os, json, time
from datetime import datetime

from aiohttp import web

from jinja2 import Environment, FileSystemLoader

from config import configs
import orm
from coroweb import add_routes, add_static

def init_jinja2(app, **kw):
    """
    Initialize jinja2 by creating an Environment.
    """
    logging.info('Initializing jinja2...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
        
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

    logging.info('Jinja2 template path set to: %s' % path)
    
    env = Environment(loader=FileSystemLoader(path), **options)
    
    filters = kw.get('filters', None)
    
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    
    app['__templating__'] = env        #Add jinja2 to the app for templating

def datetime_filter(t):
    """
    Datetime filter, transforming time to formatted strings.
    """
    #delta is in seconds
    delta = int(time.time() - t)     #Calculate the difference between t and the time when page loaded.
    
    #Because jinja2 is using Unicode, we should return unicode strings
    if delta < 60:
        return u'1m ago'
    if delta < 3600:
        return u'%sm ago' % (delta // 60)
    if delta < 86400:
        return u'%sh ago' % (delta // 3600)
    if delta < 604800:
        return u'%sd ago' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s/%s/%s' % (dt.month, dt.day, dt.year)

@asyncio.coroutine
def logger_factory(app, handler):
    """
    Middleware for logging.
    """
    
    @asyncio.coroutine
    def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        return (yield from handler(request))
    return logger

@asyncio.coroutine
def response_factory(app, handler):
    """
    Middleware for response.
    """
    @asyncio.coroutine
    def response(request):
        logging.info('Response handler...')
        r = yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and t >= 100 and t < 600:
            return web.Response(t)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        #default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    
    return response

@asyncio.coroutine
def init(loop):
    """
    Initiation function for the whole app.
    Using Coroutine at this point.
    """
    
    yield from orm.create_pool(loop=loop, **configs.db)
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
        ])    #Passing the main loop and middlewares to app.
    init_jinja2(app, filters=dict(datetime=datetime_filter))    #Initialize jinja2
    add_routes(app, 'handlers')        #When being requested the root folder by GET method, call index()
    add_static(app)
    srv = yield from loop.create_server(app.make_handler(), '0.0.0.0', 8080)
    logging.info('Server started at http://127.0.0.1:8080...')
    return srv

def application():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()

if __name__ == '__main__':
    application()