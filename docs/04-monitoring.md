# Monitoring with Kanchi

## What is Kanchi

[Kanchi](https://kanchi.io/) is an open-source (MIT) real-time monitoring tool for Celery tasks. It connects directly to the broker (Redis/RabbitMQ) without requiring application code changes or SDK installation.

### Features

| Feature | Description |
|---------|-------------|
| **Live Tasks** | Real-time task tracking via WebSocket |
| **Search & Filters** | Filter by status, task name, worker, queue, and time range |
| **Orphan Detection** | Automatic detection of lost tasks with batch retry |
| **Worker Health** | Heartbeat, load, and utilization per worker |
| **Analytics** | Daily statistics, trends, and task history |
| **Workflows** | Event-driven actions, webhooks, and automatic retries |

### Ports

| Port | Service |
|------|---------|
| `3000` | Dashboard (frontend) |
| `8765` | API (backend) |

---

## Docker Compose Configuration

Kanchi is already configured in the project's `docker-compose.yml`. It starts automatically with `make up` and connects to the shared Redis instance.

```yaml
kanchi:
  image: getkanchi/kanchi:1.3
  ports:
    - "3000:3000"
    - "8765:8765"
  environment:
    CELERY_BROKER_URL: redis://redis:6379/0
    DATABASE_URL: sqlite:////data/kanchi.db
```

Access the dashboard at http://localhost:3000.

---

## Authentication (Basic Auth)

By default, Kanchi does not require authentication. To protect dashboard access, Basic Auth is enabled via environment variables in the compose file.

### 1. Generate credentials

Use the script included in the project:

```bash
python docs/generate_kanchi_password.py
```

The script prompts for a password (not stored in shell history) and generates three values:

```
KANCHI_AUTH_PASSWORD_HASH=pbkdf2_sha256$260000$salt$hash
KANCHI_SESSION_SECRET=<hex 64 chars>
KANCHI_TOKEN_SECRET=<hex 64 chars>
```

### 2. Configure `.env`

Paste the generated values into your `.env`:

```bash
# Kanchi Monitoring Auth
KANCHI_AUTH_USERNAME=admin
KANCHI_AUTH_PASSWORD_HASH=pbkdf2_sha256$260000$salt$hash
KANCHI_SESSION_SECRET=<generated value>
KANCHI_TOKEN_SECRET=<generated value>
```

### 3. Start the service

```bash
docker compose up -d kanchi
```

When accessing http://localhost:3000, Kanchi will display a login screen. Use the configured username and password.

### Authentication variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KANCHI_AUTH_USERNAME` | Login username | `admin` |
| `KANCHI_AUTH_PASSWORD_HASH` | PBKDF2 password hash | (required) |
| `KANCHI_SESSION_SECRET` | Session signing key | (required) |
| `KANCHI_TOKEN_SECRET` | JWT token signing key | (required) |

---

## Verifying it works

### Health check

```bash
curl http://localhost:8765/api/health
```

### Logs

```bash
docker compose logs -f kanchi
```

### Checklist

1. Dashboard accessible at http://localhost:3000
2. Login screen appears (if auth is configured)
3. Workers show up in the "Workers" tab
4. When submitting a job (`POST /jobs/example`), the task appears in real time on the dashboard
