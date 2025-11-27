#!/bin/bash

VENV_FILE="$1"
PROJECT_ROOT="$2"

echo "=========================================="
echo "Processing with arguments:"
echo "  Source File: $VENV_FILE"
echo "  Project Root: $PROJECT_ROOT"
echo "=========================================="

echo "=========================================="
echo "Moving uploaded files from /tmp/upload to $PROJECT_ROOT:"
cp -r -f /tmp/upload/* "$PROJECT_ROOT/"
echo "Complete."
echo "=========================================="



echo "=========================================="
echo "Activating virtual environment:"
source "$VENV_FILE"
export DJANGO_SETTINGS_MODULE=mysite.settings.production
cd "$PROJECT_ROOT"
echo "Complete."
echo "=========================================="


echo "=========================================="
echo "Pull git and update for any requirements:"
git pull
pip install -r requirements.txt
echo "Complete."
echo "=========================================="


echo "=========================================="
echo "Update Django migrations and static files:"
python manage.py migrate
python manage.py collectstatic --noinput
echo "Complete."
echo "=========================================="


echo "=========================================="
echo "Restart server:"
sudo systemctl restart gunicorn.service
sleep 1
sudo systemctl status gunicorn.service
echo "=========================================="


echo "✓ Production changes complete!"
