
from django.core.cache import cache
import random

def random_number():
    while True:
        code = random.randint(10000, 99999)
        if not cache.get(f"verify:{code}"):
            return code
VERIFY_TTL = 120  # 2 minut

def set_verify_code(code, email):
    cache.set(
        f"verify:{code}",
        {"email": email},
        timeout=VERIFY_TTL
    )

def get_verify_email_by_code(code):
    # print(cache.get(f"verify:{code}"))
    return cache.get(f"verify:{code}")

def delete_verify_code(code):
    cache.delete(f"verify:{code}")
