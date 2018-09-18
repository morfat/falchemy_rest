
from jwcrypto import jwt, jwk,jwe
import datetime
import falcon

import json

def validate_access_token(access_token,secret_key):
    
    if not access_token:
        return None

    k = {"k": secret_key, "kty":"oct"}

    key = jwk.JWK(**k)

    try:
        ET = jwt.JWT(key = key, jwt = access_token)
      
        ST = jwt.JWT(key=key, jwt=ET.claims) # check_claims = required_token_claims)
        return json.loads(ST.claims)

    except jwt.JWTExpired:
        raise falcon.HTTPUnauthorized(description = 'Access Token Expired')
    
    except jwt.JWTInvalidClaimValue:
        raise falcon.HTTPUnauthorized(description = 'Invalid Token . Valid Token Claims are needed')
    except jwe.InvalidJWEData:
        raise falcon.HTTPUnauthorized(title = "Invalid Data" ,description = 'Data Badly Encrypted. Please check key used.')






 
