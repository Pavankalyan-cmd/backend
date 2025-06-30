import os
from pathlib import Path
import environ
from mongoengine import connect
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / '.env')
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# MongoDB Connection (MongoEngine)
MONGO_URI = env('MONGO_URI')
connect('expensestracker', host=MONGO_URI)

# Dummy Django database (needed for Django's ORM checks)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': "memory",  # In-memory dummy DB
    }
}

# ALLOWED HOSTS (Allow Render backend, Vercel frontend, local dev)
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'expensewiseai-pro.onrender.com',  # Your backend (Render)
    'expense-wise-ai-ltgug9exr-pavankalyan-vandanapus-projects.vercel.app', 
    # Your frontend (Vercel)

    "*"
]

# Secret Key & Debug
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)  # Set False for production

# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'api',
    'rest_framework',
    'corsheaders',
    'django_extensions',
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "http://localhost:3000",
    "https://expense-wise-ai-ltgug9exr-pavankalyan-vandanapus-projects.vercel.app",
])

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOW_HEADERS = list(default_headers) + [
    'authorization',
]

# URL Configuration
ROOT_URLCONF = 'expensetracker.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI
WSGI_APPLICATION = 'expensetracker.wsgi.application'

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True



# Default Primary Key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API Base URL for internal use (adjustable via .env)
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/')

# Logging
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django_debug.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

# DRF Custom Exception Handler
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'api.custom_exception_handler.custom_exception_handler',
}
