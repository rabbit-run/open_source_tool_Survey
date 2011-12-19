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

#class UserInfo(db.Model):
#  name = db.StringProperty()
#  email = db.StringProperty()
#  uid = db.StringProperty()
#  last_action = db.DateTimeProperty()
#  

class Survey(db.Model):
    user = db.UserProperty()
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

def print_err(err_msg):
    value = {}
    value['err'] = err_msg
    return template.render('html/error.html', value)

def most_recent_survey():
    query = db.Query(Survey)
    surveys = query.order('-create_time')[:5]
    dic = {}
    for s in surveys:
        if s != None:
            key = '%s:%s' % (s.user.nickname(), s.title)
            print key
            dic[key] = s.title
    return dic


def view_all_survey():
    query = Survey.all()
    surveys = query.order('create_time')
    value ={}
    dic = {}
    for s in surveys:
        if s != None:
            key = '%s:%s' % (s.user.nickname(), s.title)
            print key
            dic[key] = s.title
    if dic != {}:
        value['dic'] = dic
    return template.render('html/view_all.html', value)
    
    
    
def cgi_home():
    user = users.get_current_user()
    value = {}
    query = db.Query(Survey)
    surveys = query.order('create_time')
    keys = []
    
    dic = most_recent_survey()
    
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
    value = {}
    survey = Survey.get_by_key_name(survey_key)
    question_result = {}
    title = survey_key.split(':')[1]
    value['title'] = title
    
    for q in survey.questions:
        ques_lit = q.ques
        choices = q.choices
        answers = q.answers
        results = []
        for c in choices:
            ans = answers.count(c)
            entry = (c, ans)
            results.append(entry)
        question_result[ques_lit] = results
        
        value['results'] = question_result
        
    return template.render('html/result.html', value)

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
        user = users.get_current_user()
        args = {}
        params = self.request.params
        
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
                '%s:%s' % (user.nickname(), survey_title),
                user = user, title = survey_title,)
            _survey.create_time = datetime.datetime.now()
            
            question = Question(
                       survey = _survey,
                       ques =  _ques,
                       choices = _choices,
                       users = [],
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
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        query = db.Query(Survey)
        query.filter('user =', user)
        surveys = {}
        value = {}
        
        for q in query:
            title = q.title
            key =  '%s:%s' % (user.nickname(), title)
            surveys[key] = title
        
        value['surveys'] = surveys
        response = template.render('html/manager.html', value)
        self.response.out.write(response)
        
    def post(self):
        user = users.get_current_user()
        params = self.request.params
        if not params.has_key('key'):
            err_msg = 'Sorry, must specify a survey.'
            response = print_err(err_msg)
            self.response.out.write(response)
        else:    
            _key = params['key']
            if not user:
                self.redirect(users.create_login_url(self.request.uri))
            
            if params['submit'] == 'show result':
                self.redirect('/results?key='+_key)
            elif params['submit'] == 'delete':
                survey = Survey.get_by_key_name(_key)
                survey.delete()
                self.redirect('/index.html')
        
    
class VoteHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))      
        
        params = self.request.params
        _key = self.request.get('key')
        survey = Survey.get_by_key_name(_key)
        
        if user.nickname() in survey.users:
            if user == survey.user:
                self.redirect('/manage_sy')
            else:
                err_msg = 'Sorry, you cannot vote the same survey multiple times.'
                response = print_err(err_msg)
                self.redirect('/results?key='+_key) 
        else :
            survey.users.append(user.nickname())
            survey.put()
       
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
            if params.has_key(q.ques):
                q.answers.append(params[q.ques])
                q.put()
        self.redirect('/results?key='+_key) 
    
        
class ShowResult(webapp.RequestHandler):
    def get(self):
        params = self.request.params
        key = params['key']
        response =  cgi_results(key)
        self.response.out.write(response) 
        
class ViewAll(webapp.RequestHandler):
    def post(self):
        response =  view_all_survey()
        self.response.out.write(response)
        
        
######################## Main ####################################

def main():
	app = webapp.WSGIApplication([
		
		(r'/create_sy', CreateSyHandler),
		(r'/manage_sy', Manager),
		(r'/view_all', ViewAll),
		(r'/vote_sy.*', VoteHandler),
		(r'/results.*', ShowResult),
#		(r'/edit_sy', EditHandler),
        (r'.*',MainPage),
		], debug = True);
          
	run_wsgi_app(app)

if __name__ == "__main__":
	main()			
