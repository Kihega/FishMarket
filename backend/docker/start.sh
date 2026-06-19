#!/bin/sh
set -e

cd /var/www

# Generate APP_KEY only if not already set via Render env vars
if [ -z "$APP_KEY" ]; then
    php artisan key:generate --force
fi

# Apply database migrations (PlanetScale) on every deploy
php artisan migrate --force

# Cache config/routes for performance in production
php artisan config:cache
php artisan route:cache

# Link storage so uploaded images are served correctly
php artisan storage:link || true

exec supervisord -c /etc/supervisord.conf
