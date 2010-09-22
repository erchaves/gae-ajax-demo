
function sendit(){
    $.ajax({
        type: "POST",
        url: "/rpc",
        data: "name=John&location=Boston",
        success: function(msg){
            alert( "Data Saved: " + msg);
        }
    });   
}








class Magician(webapp.RequestHandler):
    def get(self):
        messages = self.get_messages()
        values = {"messages": messages}
        path = os.path.join(os.path.dirname(__file__), "magic.html")
        self.response.out.write(template.render(path, values))

    def get_messages(self):
        from random import choice
        from random import shuffle
        from random import random
        colors = ["#7E949E", "#AEC2AB","#EBCEA0", "#FC7765", "#FF335F", "#E0DC8B", "#F6AA3D", "#ED4C57", "#574435", "#6CC4B9", "#540633",
        "#009050","#261826", "#800F25", "#F02311", "#5F7F96", "#AA2F48", "#C0ADDB", "#7078E6"]

        messages = ""
        keys = []
        query = db.GqlQuery("SELECT __key__ FROM Crap ORDER BY date DESC")
        results = query.fetch(1000)
        for result in results:
            keys.append(result)

        shuffle(keys)
        num = 0

        if len(keys) > 400:
            num = 400
        else:
            num = len(keys)

        for i in range(num):
            if db.get(keys[i]):
                result = db.get(keys[i])

                if result.content != "":
                    x = round(random()*400)
                    y = round(random()*50)
                    color = choice(colors)
                    content = cgi.escape(result.content)#.replace(""", "'") #comment is just to help my text editor formater
                    messages += content + "-" + cgi.escape(result.credit) + "-"+color+"-"+str(x)+"px-"+str(y)+"px|"

        return messages

    def post(self):
        first = self.request.get("first")
        credit = self.request.get("credit")
        message = first
        query = db.GqlQuery ("SELECT * FROM Crap WHERE content=:1", message)
        done = False
        results = query.fetch(1)
        for result in results:
        done = True
        if done ==  True:
        text = "sorry"
        else:
        crap = Crap()
        crap.content = message
        crap.credit = credit
        crap.put()
        text = self.get_messages()
        self.response.out.write(text)

        Calling self.response.out.write will give our page the "responseText" that it requires. Now we just finish up:
        application = webapp.WSGIApplication([('/i-stat', Magician)])
    