# ── PRODUCTION ONLY ───────────────────────────────────────────────────────
# This image is built by Render on every push to main.
# Local dev never uses Docker — see project_sprints.txt for the dev workflow.
# ───────────────────────────────────────────────────────────────────────────
FROM php:8.2-fpm-alpine

RUN apk add --no-cache \
    nginx \
    supervisor \
    libpng-dev libjpeg-turbo-dev libwebp-dev freetype-dev \
    zip unzip git curl \
    && docker-php-ext-configure gd --with-jpeg --with-webp --with-freetype \
    && docker-php-ext-install pdo pdo_mysql gd

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www

COPY . .

# NOTE: backend/docker/aiven-ca.pem must exist in the repo before building.
# It's copied here as part of "COPY . ." above, and Laravel reads it via
# MYSQL_ATTR_SSL_CA=/var/www/docker/aiven-ca.pem (see .env.example).

# Laravel's Dotenv bootstrapper needs an actual .env file to exist on disk
# to populate $_ENV correctly — without one, env() calls in config files
# can return null even though the real value IS set as a process env var
# (e.g. DATABASE_URL injected by Render). This creates an EMPTY .env so
# Dotenv has something to load; real values still come from Render's
# environment variables, which Dotenv does not override (immutable mode).
RUN touch .env

RUN composer install --no-dev --optimize-autoloader --no-interaction --no-progress

RUN mkdir -p storage/framework/{cache,sessions,testing,views} storage/logs bootstrap/cache \
    && chmod -R 775 storage bootstrap/cache

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisord.conf
COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 80

CMD ["/usr/local/bin/start.sh"]
