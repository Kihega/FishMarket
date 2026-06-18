# Database Notes

## Local Development (no Docker)
- Engine : MySQL 8.x installed locally
- DB name: fishmarket_dev
- Run    : `php artisan migrate --seed`

## Production
- Provider: PlanetScale (free Hobby plan)
- URL     : https://planetscale.com
- Steps:
    1. Create account + DB named `fishmarket_prod`
    2. Create a branch `main`
    3. Copy connection string to Render env vars
    4. Push schema: `pscale deploy-request create fishmarket_prod main`

## Alternatives (all free tier)
- Aiven for MySQL   : https://aiven.io  (1 GB, 1 service)
- Railway           : https://railway.app ($5 free credit/month)
- TiDB Serverless   : https://tidbcloud.com (MySQL-compatible, 5 GB)
