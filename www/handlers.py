#coding = utf-8
__author__ = 'aresowj'

'''
URL handlers, to be filled.
'''

import re, time, json, logging, hashlib, base64, asyncio
from coroweb import get, post
from models import User, Comment, Blog, next_id

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@get('/')
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_time=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_time=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_time=time.time()-7200)
    ]
    users = yield from User.findAll()
    return {
        '__template__': 'test.html',
        'blogs': blogs,
        'users': users,
    }
    
@get('/api/users')
def api_get_users(*, page='1'):
    '''page_index = get_page_index(page)
    num = yield from User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())'''
    users = yield from User.findAll(orderBy='created_time desc')    #, limit=(p.offset, p.limit)
    for u in users:
        u.password = '******'

    return dict(users=users)    #page=p,

@post('/api/users')
def api_register_user(*, email, name, password):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_SHA1.match(password):
        raise APIValueError('password')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('Register failed, the email address is already in use.')
    uid = next_id()
    sha1_password = '%s:%s' % (uid, password)
    user = User(id=uid, name=name.strip(), email=email, password=hashlib.sha1(sha1_password.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    yield from user.save()
    #Make session cookie
    '''r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r'''

@get('/register')
def register_user(request):
    return {
        '__template__' : 'register.html',
    }
