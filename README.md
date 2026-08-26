# FastAPI + MySQL + Docker Compose

A minimal, production-style FastAPI project with a MySQL backend, fully containerized
with Docker and Docker Compose. Database tables are created automatically on
application startup if they don't already exist (`Base.metadata.create_all`), with
retry logic so the app waits gracefully for MySQL to become ready.

## Project structure

```
.
├── app/
│   ├── main.py            # FastAPI app, startup DB init, health routes
│   ├── database.py        # SQLAlchemy engine/session config (env-driven)
│   ├── models.py          # ORM models (Item)
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py             # DB access functions
│   └── routers/
│       └── items.py       # /items CRUD endpoints
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .env                    # already filled with default local dev values
```

## Quick start

1. (Optional) Adjust credentials in `.env` — defaults work out of the box for local dev.
2. Build and run everything:

   ```bash
   docker compose up --build
   ```

3. The API will be available at:
   - App: http://localhost:8000
   - Interactive docs (Swagger): http://localhost:8000/docs
   - Health check: http://localhost:8000/health

On startup, the app connects to MySQL (retrying up to ~45s if MySQL is still
initializing) and runs `Base.metadata.create_all(bind=engine)`, which creates
the `items` table only if it does not already exist — safe to restart repeatedly
without wiping data.

## Stopping / cleaning up

```bash
docker compose down          # stop containers, keep DB volume (data persists)
docker compose down -v       # stop containers AND remove the MySQL data volume
```

## API endpoints

| Method | Path          | Description       |
|--------|---------------|--------------------|
| GET    | `/`           | Root/status check  |
| GET    | `/health`     | Health check       |
| POST   | `/items/`     | Create an item     |
| GET    | `/items/`     | List items         |
| GET    | `/items/{id}` | Get a single item  |
| PUT    | `/items/{id}` | Update an item     |
| DELETE | `/items/{id}` | Delete an item     |

Example:

```bash
curl -X POST http://localhost:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Keyboard", "description": "Mechanical", "price": 49.99}'
```

## Configuration (environment variables)

Set in `.env` (used by both the `db` and `app` services via docker-compose):

| Variable              | Default        | Description                  |
|-----------------------|----------------|-------------------------------|
| `MYSQL_ROOT_PASSWORD` | root_password  | MySQL root password           |
| `MYSQL_DATABASE`      | app_db         | Database name                 |
| `MYSQL_USER`          | app_user       | App DB user                   |
| `MYSQL_PASSWORD`      | app_password   | App DB user password          |

The app additionally reads `MYSQL_HOST` (`db`, the compose service name) and
`MYSQL_PORT` (`3306`), which are set directly in `docker-compose.yml`.

## Notes for production / DevOps use

- **Migrations**: `create_all` is convenient for bootstrapping, but for schema
  changes over time you should adopt [Alembic](https://alembic.sqlalchemy.org/)
  migrations instead of relying solely on `create_all`.
- **Secrets**: don't commit real credentials — use Docker secrets, a vault, or
  your CI/CD platform's secret store instead of a plain `.env` file in production.
- **Healthchecks**: both services define Docker healthchecks; `app` won't start
  until `db`'s healthcheck passes (`depends_on: condition: service_healthy`).
- **Non-root container**: the app image runs as an unprivileged `appuser`.
- **Persistence**: MySQL data is stored in the named volume `mysql_data`, so it
  survives `docker compose down` (but not `down -v`).
- **Scaling**: to run multiple app replicas behind a reverse proxy, put nginx/
  traefik in front and scale with `docker compose up --scale app=3` (drop the
  fixed host port mapping for `app` first, or manage it via the proxy).
