from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template

class Update(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    body = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)



class MainHandler(webapp.RequestHandler):
    def get(self):
        your_name = "Jeff"
        self.response.out.write(template.render('templates/main.html', locals()))


def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler)], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
