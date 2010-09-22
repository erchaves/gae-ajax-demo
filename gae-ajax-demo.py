# A google apps project demo to test ajax

__author__ = "ericchaves"
__date__ = "$Sep 16, 2010 2:40:49 PM$"

import cgi
import datetime
from django.utils import simplejson
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import logging
import os
import wsgiref.handlers


#sample user type db Model
class TestSubject(db.Model):
    user = db.UserProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    sampleParam = db.FloatProperty(default=0.0)
#question? Is it better to actually subclass the User class?


# A Model for a ChatMessage
class ChatMessage(db.Model):
    user = db.UserProperty()
    text = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)


#----------------
#global functions
#----------------

def verify_test_subject(currentUser=None):
    """ Find the current testSubject or init a new one """
    if not currentUser:
        currentUser = users.get_current_user()

    if not currentUser:
        return False

    thisTestSubject = TestSubject.gql("WHERE user = :1", currentUser).get()
    if not thisTestSubject:
        thisTestSubject = TestSubject(user=currentUser, sampleParam=0.0)
        thisTestSubject.put()
    return thisTestSubject

# doRender: A helper to consolodate rendering functions

#defaults for doRender:
baseHtml = 'base.html'
templatesPath = 'templates/'
loginTemplate = 'login.html'

def doRender(handler, templatePage=baseHtml, values={}):
    """
    Check for user logged in, then setup the functions for rendering a template page.
    Add re-used values to the 'values' dict that is passed to the template -
    things like the logout url that we use every time
    """
    currentUser = users.get_current_user()

    if currentUser:
        # Make a copy of the 'values' dictionary and augment it
        valuesPlus = dict(values)
        #add default values that we want everytime page is rendered
        valuesPlus['thisUserName'] = currentUser.nickname()
        valuesPlus['logUrl'] = users.create_logout_url(handler.request.uri)
        valuesPlus['logUrl_linktext'] = 'Logout'

    else:
        #overwrite the passed in templatePage and redirect to login page
        templatePage = loginTemplate
        
        valuesPlus = {} #clear any values passed in - we don't need or want them
        valuesPlus['logUrl'] = users.create_login_url(handler.request.uri)
        valuesPlus['logUrl_linktext'] = 'Login'


    filePath = os.path.join(
                            os.path.dirname(__file__),
                            templatesPath + templatePage)

    if not os.path.isfile(filePath):
        return False

    valuesPlus['path'] = handler.request.path #are we using this?
    
    outstr = template.render(filePath, valuesPlus)
    handler.response.out.write(outstr)


#----------------
#request handlers
#----------------

class MainHandler(webapp.RequestHandler):
    """ Handler for the main page"""
    def get(self):

        #sample - function to verify that the user is logged in and possibly other qualifications
        thisTestSubject = verify_test_subject()

        if not thisTestSubject:
            doRender(handler=self, values={}) #let the doRender default to the log in page
            return

        templatePath = 'messageboard.html'

        values = {
            'sampleParam': thisTestSubject.sampleParam + 1 #arbitrary param test
        }

        doRender(self, templatePath, values)


#The RPC handler modified from http://code.google.com/appengine/articles/rpc.html
#my notes: Really, there isn't a way to wrap all the functions in a secure closure?
#We have to try to allow functions by checking the function name?
#Anyway, couldn't a hacker just rewrite the function name and pass in malicious code?
#I don't get it...  trying to think of a better solution....
class RPCHandler(webapp.RequestHandler):
    """ Allows the functions defined in the RPCMethods class to be RPCed."""

    def __init__(self):
        webapp.RequestHandler.__init__(self)
        self.methods = RPCMethods()

    def get(self):
        func = None

        action = self.request.get('action')
        if action:
            if action[0] == '_':
                self.error(403) # access denied
                return
            else:
                func = getattr(self.methods, action, None)

        if not func:
            self.error(404) # file not found
            return

        args = ()
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args += (simplejson.loads(val),)
            else:
                break
        result = func(*args)
        self.response.out.write(simplejson.dumps(result))


#The RPC handler modified from http://code.google.com/appengine/articles/rpc.html
#see note above for RPCHandler
class RPCMethods:
    """ Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    """
    # The JSON encoding may have encoded integers as strings.
    # Be sure to convert args to any mandatory type(s).

    def Sample1(self, * args):
        ints = [int(arg) for arg in args]
        return sum(ints)

    def Sample2(self, * args):
        ints = 1
        for arg in args:
            ints *= int(arg)
        return ints

    
class ChatHandler(webapp.RequestHandler):
    def get(self):
        doRender(self, 'messageboard.html')
        
    def post(self):
        thisTestSubject = verify_test_subject()

        if not thisTestSubject:
            doRender(handler=self, values={}) #let the doRender default to the log in page
            return

        msg = self.request.get('message')
        if msg == '':
            doRender(
                     self,
                     'messageboard.html',
                     {'error': 'Blank message ignored'}
                     )
            return
        
        newchat = ChatMessage(user=thisTestSubject.user, text=msg)
        newchat.put();

        values = {
            'sampleParam': thisTestSubject.sampleParam - 3 #arbitrary param test
        }

        doRender(self, 'messageboard.html', values)

class MessagesHandler(webapp.RequestHandler):
    def get(self):
        chatQ = db.Query(ChatMessage).order('-created')
        chats = chatQ.fetch(limit=100)
        doRender(self, 'chatlist.html', {'chats': chats})

class ClearChat(webapp.RequestHandler):
    def post(self):
        chatQ = db.Query(ChatMessage).order('-created')
        if chatQ:
            for chat in chatQ:
                chat.delete()
        self.redirect('/')

application = webapp.WSGIApplication([
                                     ('/rpc', RPCHandler),
                                     ('/messages', MessagesHandler),
                                     ('/chat', ChatHandler),
                                     ('/clearChat', ClearChat),
                                     ('/', MainHandler)

                                     ], debug=True
                                     )

def main():
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()