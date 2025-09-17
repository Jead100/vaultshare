set -o errexit

pip install -r requirements.txt

# Build Tailwind CSS
python manage.py tailwind build

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
