set -o errexit

# Python deps
pip install -r requirements.txt

# Tailwind (django-tailwind handles Node deps for the 'theme' app)
python manage.py tailwind install
python manage.py tailwind build

# Django static & DB
python manage.py collectstatic --no-input
python manage.py migrate
