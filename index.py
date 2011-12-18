#!/usr/bin/env python
from google.appengine.api import users
from google.appengine.ext import webapp
import wsgiref.handlers
from google.appengine.ext import db
from google.appengine.ext.webapp \
	import template
from google.appengine.ext.webapp.util import run_wsgi_app
import datetime

from google.appengine.dist import use_library
use_library('django', '1.2')

######################## Models ####################################

class UserInfo(db.Model):
  name = db.StringProperty()
  email = db.StringProperty()
  uid = db.StringProperty()
  last_action = db.DateTimeProperty()
  
class Survey(db.Model):
    uid = db.StringProperty()
    title = db.StringProperty()
    # There is an implicitly created property called 'questions'
    users = db.StringListProperty()
    create_time = db.DateTimeProperty()
    
class Question(db.Model):
    survey = db.ReferenceProperty(Survey,
                collection_name = 'questions')
    ques = db.StringProperty()
    choices = db.StringListProperty()
    answers = db.StringListProperty()

#class Answer(db.Model):
#    question = db.ReferenceProperty(Question,
#                collection_name = 'answers')
#    choice = db.StringProperty()
#    uid = db.StringProperty()
#    
    
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
    query = db.Query(Survey)
    surveys = query.order('create_time')
    keys = []
    dic = {}
    for s in surveys:
        key = '%s:%s' % (s.uid, s.title)
        dic[key] = s.title
    
    if user:
        value['name'] = user.nickname()
        value['logout'] = users.create_logout_url("/index.html")
    else:
        value['login'] = users.create_login_url("/index.html")
    
    if dic != {}:
        value['dic'] = dic
    return template.render('html/index.html', value)


def cgi_create_sy():
    return template.render('html/create_sy.html', {})

def cgi_add_ques(title):
    value = {'title':title}
    return template.render('html/addq.html', value)
    

def cgi_results(survey_key):
    
    
    
    
    

######################## Handlers ####################################

class MainPage(webapp.RequestHandler):
    def get(self):
        self.post()
        
    def post(self):
        query = db.Query(Survey)
        titles = query.order('title')
        
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
            _ques = params['question']
            tmp_choices = params['choices'].split('\n')
            _choices = []
            for c in tmp_choices:
                if c.strip() != '':
                    _choices.append(c.strip())
            
            
            _survey = Survey.get_or_insert(
                '%s:%s' % (user.uid, survey_title),
                uid = user.uid, title = survey_title,)
            _survey.create_time = datetime.datetime.now()
            
            question = Question(
                       survey = _survey,
                       ques =  _ques,
                       choices = _choices
                       )
            question.put()
            _survey.put()
            
            if params['submit'] == 'Add another question':
                response = cgi_add_ques(survey_title);
                self.response.out.write(response)
            else:
                self.redirect('/index.html')

class Manager(webapp.RequestHandler):
    def get(self):
        user = get_user_info()
        query = db.Query(Survey)
        query.filter('uid =', user.uid)
        titles = []
        for q in query:
            titles.append(q.title)
        value = {'titles':titles}
        response = template.render('html/manager.html', value)
        self.response.out.write(response)
    
class VoteHandler(webapp.RequestHandler):
    def get(self):
        cu = users.get_current_user()
        if cu:
            user = get_user_info()
        else:
            self.redirect(users.create_login_url(self.request.uri))

        params = self.request.params
        _key = self.request.get('key')
        uid = user.uid
        survey = Survey.get_by_key_name(_key)
        
        if uid in survey.users:
            slf.redirect('/index.html')
        
        value = {}
        _ques = {}
        for q in survey.questions:
             _ques[q.ques] = q.choices 
        value['ques'] = _ques
        value['title'] = survey.title
        value['survey_key'] = _key
        response = template.render('html/vote.html', value)
        self.response.out.write(response)
    
    def post(self):
        params = self.request.params
        _key = params['key']
        survey = Survey.get_by_key_name(_key)
        
        for q in survey.questions:
            q.answers.append(params[q.ques])
            q.put()
        response = cgi_results(_key)
        self.response.out.write(response)
        
        
        
######################## Main ####################################

def main():
	app = webapp.WSGIApplication([
		(r'.*/index\.html$',MainPage),
		(r'/create_sy', CreateSyHandler),
		(r'/manage_sy', Manager),
#		(r'/view_sy', ViewSyHandler),
		(r'/vote_sy.*', VoteHandler),
#		(r'/edit', EditHandler),
		], debug = True);
          
	run_wsgi_app(app)

if __name__ == "__main__":
	main()			
