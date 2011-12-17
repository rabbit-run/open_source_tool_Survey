#!/usr/bin/env python

from google.appengine.ext import db
from google.appengine.ext import webapp
import wsgiref.handlers
from google.appengine.ext.webapp \
	import template

class Shout(db.Model):
	message = db.StringProperty(
			required=True)
	when = db.DateTimeProperty(
			auto_now_add=True)

class MyHandler(webapp.RequestHandler):
	def get(self):
		shouts = db.GqlQuery(
		  'SELECT * FROM Shout '
		  'ORDER BY when DESC')
		values = {
		  'shouts' : shouts
		}
		self.response.out.write(
			template.render('main.html', values))
			
	def post(self):
		shout = Shout(
			message=self.request.get(
			'message'))
		shout.put()
		self.redirect('/')
		
		

def main():
	app = webapp.WSGIApplication([
		(r'.*',MyHandler)], debug = True);
	wsgiref.handlers.CGIHandler().run(app);

if __name__ == "__main__":
	main()
	