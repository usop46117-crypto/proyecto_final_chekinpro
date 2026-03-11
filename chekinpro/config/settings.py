"""
Django settings for config project.
"""

from pathlib import Path
import os

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-osldmz$r6z)7ou$(igl1kiu)7zbjj8e2lrfzc1(p!o18-z)9=88'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# 👇 AGREGADAS TODAS LAS IPS POSIBLES
ALLOWED_HOSTS = [
    '10.3.141.47',
    'localhost',
    '127.0.0.1',
    '10.3.140.22',
    '192.168.101.5',
    '0.0.0.0',
    '*'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Social Auth
    'social_django',

    # Tus apps
    'usuarios',
    'hotel',
    'habitaciones',
    'huespedes',
    'reservas',
    'notificaciones',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Social Auth
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'notificaciones.context_processors.notificaciones',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'CheKinPro',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'panel'
LOGOUT_REDIRECT_URL = 'login'
AUTH_USER_MODEL = 'usuarios.Usuario'

# Social Auth Backends
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

# Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''  # Client ID
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''  #  Client Secret

# Facebook OAuth2
SOCIAL_AUTH_FACEBOOK_KEY = ''  # App ID
SOCIAL_AUTH_FACEBOOK_SECRET = ''  # App Secret
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, email'
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'chekinpro2027@gmail.com'
EMAIL_HOST_PASSWORD = 'btcjavlutdwjrtev'

SITE_URL = 'http://10.3.141.47:8000' # IP