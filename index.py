#!/usr/bin/env python
from google.appengine.api import users
from google.appengine.ext import webapp
import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.ext.webapp \
	import template
from google.appengine.ext.webapp.util import run_wsgi_app
import datetime


######################## Models ####################################

class UserInfo(db.Model):
  name = db.StringProperty()
  email = db.StringProperty()
  sid = db.StringProperty()
  last_action = db.DateTimeProperty()
  
class Survey(db.Model):
    sid = db.StringProperty()
    title = db.StringProperty()
    # There is an implicitly created property called 'questions'
    create_time = db.DateTimeProperty()
    
class Question(db.Model):
    survey = db.ReferenceProperty(Survey,
                collection_name = 'questions')
    ques = db.StringProperty()
    #implicitly created property called 'answers'
    choices = db.StringListProperty()

class Answer(db.Model):
    question = db.ReferenceProperty(Question,
                collection_name = 'answers')
    choice = db.StringProperty()
    sid = db.StringProperty()
    
    
######################## Methods ####################################
def get_user_info():
  cu = users.get_current_user()
  s = UserInfo.get_or_insert(cu.user_id(),
                             email=cu.email(), name=cu.nickname()) 
  s.last_action = datetime.datetime.now()
  s.put()
  return s


def cgi_home():
    user = users.get_current_user()
    value = {}
    if user:
        value['name'] = user.nickname()
        value['logout'] = users.create_logout_url("/index.html")
    else:
        value['login'] = users.create_login_url("/index.html")
    return template.render('html/index.html', value)

def cgi_create_sy():
    return template.render('html/create_sy.html', {})

def cgi_add_ques(title):
    value = {'title':title}
    return template.render('html/addq.html', value)
    
    
    
def cgi_login( sid = None):
    s = get_user_info()
    sid = s.sid
    if not sid:
        return cgi_register()
    else:
        return cgi_home()


######################## Handlers ####################################

class MainPage(webapp.RequestHandler):
    def get(self):
        self.post()
        
    def post(self):
        response = cgi_home()
        self.response.out.write(response)

class CreateSyHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            response = cgi_create_sy()
            self.response.out.write(response)
        else:
            self.redirect(users.create_login_url(self.request.uri))
            
    def post(self):
        args = {}
        params = self.request.params
        user = get_user_info()
        
        isValid = True
        for v in params:
            if self.request.params[v] == '':
                isValid = False
            
        if not isValid:
            self.redirect('/index.html')
        else:
            survey_title = params['title']
            survey = Survey.get_or_insert(
                '%s:%s' % (user.sid, survey_title),
                sid = user.sid, title = survey_title,)
            survey.create_time = datetime.datetime.now()
            survey.put()
            
            if params['submit'] == 'Add another question':
                response = cgi_add_ques(survey_title);
                self.response.out.write(response)
            else:
                self.response.out.write('hello')

######################## Main ####################################

def main():
	app = webapp.WSGIApplication([
		(r'.*/index\.html$',MainPage),
		(r'/create_sy', CreateSyHandler),
#		('/view_sy', ViewSyHandler),
#		('/vote', VoteHandler),
#		('/edit', EditHandler),
		], debug = True);
          
	run_wsgi_app(app)

if __name__ == "__main__":
	main()			
