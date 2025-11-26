from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def key_func():
    from flask import request
    return request.cookies.get("client_id") or get_remote_address()

limiter = Limiter(
    key_func=key_func,
    default_limits=[]
)
