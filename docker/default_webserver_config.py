"""Default configuration for the Airflow webserver"""
import os

from flask_appbuilder.security.manager import AUTH_DB

# Oather options
# from flask_appbuilder.security.manager import AUTH_LDAP
# from flask_appbuilder.security.manager import AUTH_OAUTH
# from flask_appbuilder.security.manager import AUTH_OID
# from flask_appbuilder.security.manager import AUTH_REMOTE_USER


basedir = os.path.abspath(os.path.dirname(__file__))

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
AUTH_TYPE = AUTH_DB
AUTH_ROLE_ADMIN = 'Admin'
AUTH_ROLE_PUBLIC = 'Admin'
AUTH_USER_REGISTRATION = False