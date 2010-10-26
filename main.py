#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# # # # # # # # # # # # 
# todo: 
#   1. implement user system for: flag as inappropriate; add entry etc. 
#   2. an favicon and a title for the app. for better integration with iPhone.


from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import random
from appengine_utilities import sessions

######## db ########
class Entry(db.Model):
    situations = db.ListProperty(basestring)
    comment = db.TextProperty()
    flag = db.IntegerProperty(default = 0)
    muser = db.StringProperty()
    
class MUser(db.Model):
    username = db.StringProperty()
    password = db.StringProperty()
    email = db.StringProperty()
    
# controllers:

class MainHandler(webapp.RequestHandler):
    def get(self):
        s = sessions.Session()
        if not s.has_key("muser"):
            muser = None
        else:
            muser = s["muser"]
        self.response.out.write(template.render("templates/index.html", {'muser':muser}))

class SearchHandler(webapp.RequestHandler):
    def post(self):
        s = sessions.Session()
        if not s.has_key("muser"):
            muser = None
        else:
            muser = s["muser"]
        
        situations = self.request.get("situations")
        situations = situations.split(".")
        situations = [situation.lower().strip() for situation in situations if situation.strip() != ""]
        
        # form query:
        query = "where "
        for i in range(len(situations)):
            query += "situations = \'" + situations[i] + "\' "
            if i < len(situations) - 1:
                query += "and "
        
        entities = Entry.gql(query)
        # return a random comment:
        if entities.count() > 0:
            return_entity = entities[random.randint(0, entities.count() - 1)]
        else:
            return_entity = None
        
        self.response.out.write(template.render("templates/search_result.html", {"situations":situations, "result":return_entity, "muser": muser}))
        
class AddEntryHandler(webapp.RequestHandler):
    def get(self):
        situations = self.request.get("situations", None)
        self.response.out.write(template.render("templates/add_entry.html", {"situations":situations}))
    def post(self):
        s = sessions.Session()
        try:
            muser = s["muser"]
        except:
            self.redirect("/signin")
            return
            
        situations = self.request.get("situations")
        situations = situations.split(".")
        situations = [situation.lower().strip() for situation in situations]
        comment = self.request.get("comment")
        
        entry = Entry()
        entry.situations = situations
        entry.comment = comment
        entry.muser = str(muser.key())
        entry.put()
        self.redirect("/")
        
class AboutHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render("templates/about.html", {}))

class SigninHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render("templates/signin.html", {}))
    def post(self):
        email = self.request.get("email").lower()
        password = self.request.get("password")
        
        # try to signin:
        query = MUser.all().filter("email =", email).filter("password =", password)
        if not query.count() == 1:
            self.response.out.write(template.render("templates/signin.html", {"error": "no such user or password incorrect. "}))
            return
        else:
            s = sessions.Session()
            s["muser"] = query[0]
            self.redirect("/")
        
class RegisterHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render('templates/register.html', {}))
    def post(self):
        username = self.request.get("username").lower()
        password_1 = self.request.get("password_1")
        password_2 = self.request.get("password_2")
        email = self.request.get("email")
        filled = {'username': username, "email": email}
        
        if not password_1 == password_2:
            filled["error"] = "Two passwords didn't match."
            self.response.out.write(template.render('templates/register.html', {"filled": filled}))
            return
        
        # see if email exists
        query = MUser.all().filter("email =", email)
        if not query.count() == 0:
            filled["email"] = ""
            filled["error"] = "This email has already been used. "
            self.response.out.write(template.render('templates/register.html', {"filled": filled}))
            return
        
        # put new user in datastore
        muser = MUser()
        muser.email = email
        muser.username = username
        muser.password = password_1
        muser.put()
        
        # set session up
        s = sessions.Session()
        s['muser'] = muser
        
        # redirect
        self.redirect('/')

class FlagHandler(webapp.RequestHandler):
    '''
    flag an entity as inappropriate
    '''
    def get(self):
        s = sessions.Session()
        if not s.has_key('muser'):
            self.redirect("/sign_in")
            return
        
        entry_key = self.request.get("entry")
        try:
            entry = db.get(entry_key)
            if not entry.flag:
                entry.flag = 1
            else:
                entry.flag = entry.flag + 1
            entry.put()
        except:
            self.redirect("/")
            return
        self.redirect("/")
        

def main():
    application = webapp.WSGIApplication([
                                        ('/search_result', SearchHandler),
                                        ('/add_entry', AddEntryHandler),
                                        ('/what_is_this', AboutHandler),
                                        ('/sign_in', SigninHandler),
                                        ('/register', RegisterHandler),
                                        ('/flag', FlagHandler),
                                        ('/', MainHandler)
                                        
                                        ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
