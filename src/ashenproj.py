# A google apps project for Andrew Shen

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

class TestSubject(db.Model):
    user = db.UserProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    scoreTotal = db.FloatProperty(default=0.0)

class Session(db.Model):
    testSubject = db.ReferenceProperty(TestSubject)
    sessionType = db.StringProperty(default="A")
    index = db.IntegerProperty()
    status = db.IntegerProperty() # 0: null, 1: pending, 2: active, 3: complete
    trueAnswer = db.StringProperty() #'real', 'fake', or 'na'
    score = db.FloatProperty(default=0.0)
    date = db.DateTimeProperty(auto_now_add=True)
    startTime = db.DateTimeProperty()

class Question(db.Model):
    session = db.ReferenceProperty(Session)
    index = db.IntegerProperty(default=0)
    answer = db.StringProperty() #'real', 'fake', or 'na'

# A Model for a ChatMessage
class ChatMessage(db.Model):
    user = db.UserProperty()
    text = db.StringProperty()
    created = db.DateTimeProperty(auto_now=True)


#class BaseHandler(webapp.RequestHandler):

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
        thisTestSubject = TestSubject(user=currentUser, scoreTotal=0.0)
        thisTestSubject.put()
    return thisTestSubject

def get_session(type):
    return {
    "A": "A",
    "B": "B",
    "C": "C"
    }.get(type, "A") #default to "A"


def verify_session(thisTestSubject):
    """ Find the current session, or init a new one """

    lastSession = Session.all().filter("testSubject =", thisTestSubject).filter("status =", 3).order('-index').get() #status 3: complete
    thisSession = Session.all().filter("testSubject =", thisTestSubject).filter("status <", 3).get() #status < 3: null, pending, or active.  Should be only 1 item for get() to get

    if not thisSession:
        if not lastSession:
            sessionIndex = 0
        else:
            sessionIndex = lastSession.index + 1

        thisSession = Session(
                              testSubject=thisTestSubject,
                              sessionType=get_session("A"),
                              index=sessionIndex,
                              status=1,
                              trueAnswer="real",
                              score=0.0
                              )
    else:
        #questions
        pass

    thisSession.put()
    return thisSession


def verify_last_question_index(thisSession):
    lastQuestion = Question.all().filter("session =", thisSession).order('-index').get()
    if lastQuestion:
        return lastQuestion.index
    else:
        return 0

def getStatusText(status):
    return {
        0: "null",
        1: "pending",
        2: "active",
        3: "complete"
    }.get(status)


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
    def get(self):

        thisTestSubject = verify_test_subject()

        if not thisTestSubject:
            doRender(handler=self, values={}) #let the doRender default to the log in page
            return

        thisSession = verify_session(thisTestSubject)

        lastQuestionIndex = verify_last_question_index(thisSession)

        templatePath = 'messageboard.html'

        username = thisTestSubject.user.nickname() #todofix this
        values = {
            'thisUserName': username,
            'thisTestSubject': thisTestSubject,
            'scoreTotal': thisTestSubject.scoreTotal,
            'thisSession': thisSession,
            'currentSessionStatusText': getStatusText(thisSession.status),
            'scoreThisSession': thisSession.score,
            'thisQuestionIndex': lastQuestionIndex + 1,
            'lastQuestionIndex': lastQuestionIndex,
        }

        doRender(self, templatePath, values)


class AnswerHandler(webapp.RequestHandler):
    """ Must be called from a current session with status active... """
    def post(self):

        thisTestSubject = verify_test_subject()

        #status < 3: null, pending, or active.  Should only be one item for get() to get, but sort anyways just in case.
        #must sort by order first then date.
        thisSession = Session.all().filter("testSubject =", thisTestSubject).filter("status <", 3).order("status").order("-date").get()

        lastQuestion = Question.all().filter("session =", thisSession).order('-index').get()

        if not lastQuestion:
            index = 0
        else:
            index = lastQuestion.index + 1

        answer = cgi.escape(self.request.get('real')) or cgi.escape(self.request.get('fake')) or 'na'

        thisQuestion = Question(
                                session=thisSession,
                                answer=answer,
                                index=index
                                )
        thisQuestion.put()

        if answer == thisSession.trueAnswer:
            thisSession.score += 3
        elif answer == "na":
            thisSession.score -= .5
        else:
            thisSession.score -= 5

        thisSession.put()
        self.redirect('/')
   
class FinishHandler(webapp.RequestHandler):
    def post(self):

        def total_score(testSubject):
            totalScore = 0.0

            #status 3: complete.  Order doesn't really matter..
            sessions = Session.all().filter("testSubject =", testSubject).filter("status =", 3).order('index')
            for session in sessions:
                logging.info(session.score)
                totalScore += session.score
            return totalScore
        

        thisTestSubject = verify_test_subject()

        #status < 3: null, pending, or active.  Should only be one item for get() to get, but sort anyways just in case.
        #must sort by order first then date.
        thisSession = Session.all().filter("testSubject =", thisTestSubject).filter("status <", 3).order("status").order("-date").get()

        thisSession.status = 3 #status 3 : complete
        #thisSession.score = float(cgi.escape(self.request.get('score')) or 0.0)
        thisSession.put()
        thisTestSubject.scoreTotal = total_score(thisTestSubject) #consider making it a proper method, how?
        thisTestSubject.put()

        self.redirect('/')

#The RPC handler from http://code.google.com/appengine/articles/rpc.html
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
                args += (simplejson.loads(val), )
            else:
                break
        result = func(*args)
        self.response.out.write(simplejson.dumps(result))

#The RPC methods - code from http://code.google.com/appengine/articles/rpc.html
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
        
        newchat = ChatMessage(user = thisTestSubject.user, text=msg)
        newchat.put();
        doRender(self, 'messageboard.html')

class MessagesHandler(webapp.RequestHandler):
    def get(self):
        chatQ = db.Query(ChatMessage).order('-created')
        chats = chatQ.fetch(limit=100)
        doRender(self, 'chatlist.html', {'chats': chats})

application = webapp.WSGIApplication([
                                     ('/finish', FinishHandler),
                                     ('/answer', AnswerHandler),
                                     ('/rpc', RPCHandler),
                                     ('/messages', MessagesHandler),
                                     ('/chat', ChatHandler),
                                     ('/.*', MainHandler)
                                     ], debug=True
                                     )

def main():
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
    