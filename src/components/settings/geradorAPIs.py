import jwt
from datetime import datetime, timedelta


SECRET_KEY = "07091bca253ed2a404b8d242ee048fb51704f7f9e023425cfeb82051f3187edb"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60


def generate_token(audience: str):
    now = datetime.now()
    expire = now + timedelta(minutes=EXPIRE_MINUTES)
    payload = {
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


if __name__ == "__main__":
    audience = "ken01.utad.pt:8080"
    token = generate_token(audience)
    print(f"\nJWT Token for audience '{audience}':\n")
    print(token)
