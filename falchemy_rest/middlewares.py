

from falchemy_rest import auth
from falchemy_rest import sql

class CoreMiddleWare:
    def __init__(self,db_engine):
        self.db_engine = db_engine

   
    def process_request(self,req,resp):
        conn = self.db_engine.connect()
        
        req.context['db'] = sql.Db(connection = conn)


    def process_resource(self,req,resp,resource,params):
        req.context['transaction'] = req.context['db']._connection.begin()


    def process_response(self,req,resp,resource,req_succeeded):
        try:
            if req_succeeded:
                req.context['transaction'].commit()
            else:
                req.context['transaction'].rollback()
        except:
            pass
        
        req.context['db']._connection.close()


class CORSMiddleWare:

    ALLOWED_ORIGINS=['*']


    def process_resource(self,req,resp,resource,params):
        origin=req.get_header('Origin')
        if origin:
            #if no origin then its not a valid CORS request
            acrm=req.get_header('Access-Control-Request-Method')
            acrh = req.get_header('Access-Control-Request-Headers')
            if req.method=='OPTIONS' and acrm and acrh:
                #this is preflight request
                

                # Set ACAH to echo ACRH
                resp.set_header('Access-Control-Allow-Headers', acrh)
                resp.set_header('Access-Control-Expose-Headers',acrh)
               
                # Optionally set ACMA
                # resp.set_header('Access-Control-Max-Age', '60')

                # Find implemented methods
                allowed_methods = []
                for method in HTTP_METHODS:
                    allowed_method = getattr(resource, 'on_' + method.lower(), None)
                    if allowed_method:
                        allowed_methods.append(method)
                

                # Fill ACAM
                resp.set_header('Access-Control-Allow-Methods', ','.join(sorted(allowed_methods)))


    def process_response(self,req,resp,resource,req_succeeded): #called immediately before the response is returned.
        origin = req.get_header('Origin')
        if origin:
            # If there is no Origin header, then it is not a valid CORS request
            if '*' in self.ALLOWED_ORIGINS:
                resp.set_header('Access-Control-Allow-Origin', '*')
            elif origin in self.ALLOWED_ORIGINS:
                resp.set_header('Access-Control-Allow-Origin', origin)



class AuthMiddleWare:

    def __init__(self, secret_key):
        self.secret_key = secret_key


        
    def process_resource(self,req,resp,resource,params):
        must_login = True
        auth_token_type = 'Bearer'

        try:
            must_login = resource.login_required #we expect login_required = False
        except AttributeError:
            pass
        
        try:
            auth_token_type = resource.auth_token_type #we expect login_required = False
        except AttributeError:
            pass
            

        if must_login:
            auth_data = None

            if auth_token_type == 'Bearer':
                auth_data = auth.validate_bearer_token( bearer_token = req.auth , secret_key = self.secret_key)
            
        
            if auth_data is None:
                raise falcon.HTTPUnauthorized(description = 'Login Required')
            
            req.context['auth'] = auth_data
            

       
    

