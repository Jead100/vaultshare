set -o errexit

# Python deps
pip install -r requirements.txt

# Django static & DB
python manage.py collectstatic --no-input
python manage.py migrate
