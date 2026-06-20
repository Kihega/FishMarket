#!/bin/sh
set -e

cd /var/www

# ── TEMPORARY DIAGNOSTIC ────────────────────────────────────────────────
# Prints whether DATABASE_URL is visible to this process at runtime.
# Remove this block once the connection issue is confirmed fixed.
echo "=== SmartFish startup diagnostics ==="
if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL is EMPTY or NOT SET in this container."
else
    echo "DATABASE_URL is set. Length: ${#DATABASE_URL} chars."
    echo "Starts with: $(echo "$DATABASE_URL" | cut -c1-15)..."
fi
echo "MYSQL_ATTR_SSL_CA = $MYSQL_ATTR_SSL_CA"
echo "===================================="

# Generate APP_KEY only if not already set via Render env vars
if [ -z "$APP_KEY" ]; then
    php artisan key:generate --force
fi

# Apply database migrations on every deploy
php artisan migrate --force

# Cache config/routes for performance in production
php artisan config:cache
php artisan route:cache

# Link storage so uploaded images are served correctly
php artisan storage:link || true

exec supervisord -c /etc/supervisord.conf
