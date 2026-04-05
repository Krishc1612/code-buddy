import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

load_dotenv()

EXPIRE_MINUTES = int(os.getenv("EXPIRE_MINUTES", 40))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "try-guess-it")
ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(
    schemes = ["bcrypt"],
    deprecated = "auto"
)
# above is some required initialization used for using bcrypt algorithm
# we can change the hashing algo by simply changing "schemes"

def hash_password(password : str) -> str: # this is just a wrapper function created for convenience
    return pwd_context.hash(password) # .hash() performs the algorithm specified in pwd_context on the password to hash it and generate a hashed password.

def verify_password(password : str, hashed_password : str) -> bool:
    return pwd_context.verify(password, hashed_password) # verifies whether password matches hashed_password.  

# hashed_password = hash_password("hellothere")
# print(verify_password("hellothere", hashed_password))
# print(verify_password("hello123", hashed_password))

def create_access_token(data : dict) -> str:
    to_encode = data.copy() # simply copying dictionary
    expire = datetime.utcnow() + timedelta(minutes = EXPIRE_MINUTES)
    # after expire_minutes from now the access token will expire
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm = ALGORITHM)
    # the above is the final jsonwebtoken that we would use to identify our user.
    # also called ACCESS_TOKEN which would expire at "expire" time.
    return encoded_jwt

# Note : A jsonwebtoken has three parts
#       1. Header -----> Describes which algorithm is used for encoding 
#       2. Payload ----> Is the encoded payload (data i.e, {user_id : "..."})
#       3. Signature --> ensures token is not modified.

# Why exactly we are creating this? 
# When user enters his details we create a sole truth of his identity called user_id.
# Giving it directly to the browser might too harmful as attacks then will be able to directly access it
# Hence we encode it with a specific random algorithm so as to keep the identity hidden and protected with user. Note that somehow the identity should be with user else we would not be able to identify the user (we identify a user by decoding the token hence getting the user_id).

# token = create_access_token({"user_id": "krish"})
# print(token) observe that token has three parts according to the explanation.

def decode_access_token(token : str) -> dict:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms = [ALGORITHM])
    return payload # simply decoding the token. It would raise an error (InvalidTokenError) if token is not valid or didn't matched the signature.