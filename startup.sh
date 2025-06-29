#!/bin/bash
pip install -r requirements.txt
gunicorn expensetracker.wsgi:application --bind=0.0.0.0:8000
