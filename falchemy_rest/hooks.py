

import falcon 
import datetime

def validate_serializer_data(req,resp,resource,params, serializer_class):

    data = req.media
  
    try:
        req.context['data'] = serializer_class(data).data
    except KeyError as ex:
        raise falcon.HTTPBadRequest(title = "Invalid Data" , description = "%s field value needed"%( str(ex) ))
        
