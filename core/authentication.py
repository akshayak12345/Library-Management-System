import jwt
import datetime
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from django.conf import settings
from .models import User
import uuid

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                raise exceptions.AuthenticationFailed('Invalid token type')
        except ValueError:
            raise exceptions.AuthenticationFailed('Invalid token format')

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')

        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        return (user, token)

def create_access_token(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
         'jti': str(uuid.uuid4()),
         'token_type': 'access' 
    }, settings.SECRET_KEY, algorithm='HS256')

def decode_access_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed('Token has expired')
    except jwt.InvalidTokenError:
        raise exceptions.AuthenticationFailed('Invalid token')

def create_refresh_token(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow(),
        'jti': str(uuid.uuid4()),
        'token_type': 'refresh' 
    }, settings.SECRET_KEY, algorithm='HS256')

def decode_refresh_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed('Token has expired')
    except jwt.InvalidTokenError:
        raise exceptions.AuthenticationFailed('Invalid token')
