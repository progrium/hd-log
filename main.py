from google.appengine.ext import webapp, db
from google.appengine.api import urlfetch, memcache, users
from google.appengine.ext.webapp import util, template

class Update(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    body = db.StringProperty(required=True, multiline=True)
    created = db.DateTimeProperty(auto_now_add=True)

class Comment(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    body = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    update = db.ReferenceProperty(Update)

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
        ('/comment/(.+)', CommentHandler)], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
