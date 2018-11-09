from jwcrypto import jwk
import json

def generate_signing_secret():
    key = jwk.JWK.generate(kty = 'oct',size = 256)
    return json.loads(key.export()).get("k")

