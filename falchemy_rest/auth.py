
from jwcrypto import jwt, jwk,jwe
import datetime
import falcon

import json

def validate_bearer_token(bearer_token,secret_key):
   

    #print (bearer_token, secret_key)

    if not bearer_token:
        return None

    k = {"k": secret_key, "kty":"oct"}

    key = jwk.JWK(**k)

    try:
        bearer_token_l = bearer_token.split('Bearer')
        bearer_token = bearer_token_l[1].strip()


        ET = jwt.JWT(key = key, jwt = bearer_token)
      
        ST = jwt.JWT(key=key, jwt=ET.claims) # check_claims = required_token_claims)
        return json.loads(ST.claims)
   
    except jwt.JWTExpired:
        raise falcon.HTTPUnauthorized(description = 'Access Token Expired')
    
    except jwt.JWTInvalidClaimValue:
        raise falcon.HTTPUnauthorized(description = 'Invalid Token . Valid Token Claims are needed')
    except jwe.InvalidJWEData:
        raise falcon.HTTPUnauthorized(title = "Invalid Data" ,description = 'Data Badly Encrypted. Please check key used.')



