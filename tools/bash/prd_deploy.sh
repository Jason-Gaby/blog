#!/bin/bash

VENV_FILE="$1"
PROJECT_ROOT="$2"
CONTENT_ROOT="$3"

echo "=========================================="
echo "Processing with arguments:"
echo "  Source File: $VENV_FILE"
echo "  Project Root: $PROJECT_ROOT"
echo "=========================================="

echo "=========================================="
echo "Moving uploaded files from /tmp/upload to $PROJECT_ROOT:"
cp -r -f /tmp/uploads/. "$PROJECT_ROOT/"
echo "Complete."
echo "=========================================="



echo "=========================================="
echo "Activating virtual environment:"
source "$VENV_FILE"
export DJANGO_SETTINGS_MODULE=mysite.settings.production
echo "Complete."
echo "=========================================="


echo "=========================================="
echo "Pull git for both projects and update for any requirements."
echo "Also install blog content package."
cd "$CONTENT_ROOT"
git pull

cd "$PROJECT_ROOT"
git pull

pip install -r requirements.txt
pip install -e "$CONTENT_ROOT"
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
