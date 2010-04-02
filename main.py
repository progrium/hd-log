import logging

from google.appengine.ext import webapp, db
from google.appengine.api import urlfetch, memcache, users
from google.appengine.ext.webapp import util, template
from google.appengine.api.labs import taskqueue
from django.utils import simplejson

# Parsing the username ourselfs because the nickname on GAE does funky stuff with non @gmail account
def username(user):
    return user.nickname().split('@')[0] if user else None

# Hacker Dojo Domain API helper with caching
def dojo(path, cache_ttl=3600):
    base_url = 'http://domain.hackerdojo.com'
    resp = memcache.get(path)
    if not resp:
        resp = urlfetch.fetch(base_url + path, deadline=10)
        try:
            resp = simplejson.loads(resp.content)
        except Exception, e:
            resp = []
            cache_ttl = 10
        memcache.set(path, resp, cache_ttl)
    return resp

# Return the name of a user from the memcache. If it was not set we set it and queue a query to the domain api
def fullname(username):
    fullname = memcache.get('/users/%s:fullname' % username)
    if not fullname:
        taskqueue.add(url='/worker/user', params={'username': username})
        memcache.set('/users/%s:fullname' % username, username, 10)
        return username
    else:
        return fullname

# Worket to handle the fullname queue request.
class UserWorker(webapp.RequestHandler):
    def post(self):
        username = self.request.get('username')
        month_ttl = 3600*24*28
        user = dojo('/users/%s' % username, month_ttl)
        memcache.set('/users/%s:fullname' % username, "%s %s" % (user['first_name'], user['last_name']), month_ttl)

#Data Models:
class Update(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    body = db.StringProperty(required=True, multiline=True)
    created = db.DateTimeProperty(auto_now_add=True)
    
    def user_fullname(self):
      return fullname(username(self.user))

class Comment(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    body = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    update = db.ReferenceProperty(Update)

    def user_fullname(self):
      return fullname(username(self.user))


# Handlers:
class CommentHandler(webapp.RequestHandler):
    def post(self, update_id):
        update = Update.get_by_id(int(update_id))
        if update:
            comment = Comment(
                body=self.request.get('body'),
                update=update)
            comment.put()
        self.redirect('/')

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            logout_url = users.create_logout_url('/')
        else:
            login_url = users.create_login_url('/')
        updates = Update.all().order('-created')
        self.response.out.write(template.render('templates/main.html', locals()))
    
    def post(self):
        update = Update(body=self.request.get('body'))
        update.put()
        self.redirect('/')

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/comment/(.+)', CommentHandler),
        ('/worker/user', UserWorker),
      ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
