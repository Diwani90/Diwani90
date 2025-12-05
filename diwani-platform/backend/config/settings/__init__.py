# ===================================
# منصة ديواني - Settings Module
# ===================================

import os

environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
else:
    from .development import *
