import json
from falcon.media import JSONHandler
from datetime import date,datetime,time ,timedelta
import decimal 

class CustomJSONHandler(JSONHandler):
    #custom seriaze json returned to users

    def serialize(self, media):
        #here we can customize to hwo we need our formats to be.
        #print ("Serilize")
      
        return json.dumps(media, default=self.json_serial,ensure_ascii=False).encode('utf-8')

    def json_serial(self,obj):
        if isinstance(obj,(datetime,date,time)):
            return obj.isoformat()
        
        if isinstance(obj,(timedelta,decimal.Decimal)):
            return str(obj)

        if isinstance(obj,bytes):
            return obj.decode('UTF-8')


        raise TypeError("Type %s is not serializable"%(type(obj)))




