# PromptStack Auth Service

Standalone authentication and identity management microservice for the PromptStack platform.

## Overview

This service handles all authentication, user management, team memberships, and domain assignments for the PromptStack ecosystem. It's designed to be deployed independently and consumed by other microservices via REST API.

## Features

- **User Authentication**: Login, registration, JWT token generation
- **Token Validation**: Service-to-service token validation endpoint
- **Identity Management**: Users, teams, domains, and memberships
- **Multiple Auth Modes**: 
  - Development headers (X-User-Email, X-User-Name)
  - JWT tokens with configurable secret
  - OIDC integration (Cognito, Auth0, etc.)

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Auth Service (Port 8001)              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐         ┌─────────────────┐  │
│  │   REST API   │         │  Authentication │  │
│  │  (FastAPI)   │────────▶│     Logic       │  │
│  └──────────────┘         └─────────────────┘  │
│         │                          │            │
│         │                          │            │
│         ▼                          ▼            │
│  ┌──────────────┐         ┌─────────────────┐  │
│  │   Prisma     │────────▶│   PostgreSQL    │  │
│  │     ORM      │         │    Database     │  │
│  └──────────────┘         └─────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Database Tables

This service owns the following tables:

- **users**: User accounts (id, email, name, password_hash, avatar_url, created_at)
- **teams**: Organizational teams (id, name, external_ref, is_active)
- **team_memberships**: User-team relationships (id, user_id, team_id, role)
- **domains**: Business domains (id, key, name, parent_domain_id, is_active)
- **user_domains**: User-domain assignments (id, user_id, domain_id)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL (or use Docker Compose)

### Option 1: Docker Compose (Recommended)

```bash
# Start the service with database
docker compose up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f auth

# Stop services
docker compose down
```

The service will be available at:
- API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Database: localhost:5433

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://promptstack:promptstack@localhost:5432/promptstack"
export AUTH_ALLOW_DEV_HEADERS=true
export AUTH_JWT_SECRET_KEY="your-secret-key"

# Generate Prisma client
prisma generate

# Run database migrations (if using Prisma migrate)
# prisma migrate dev

# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```env
# Database
DATABASE_URL=postgresql://promptstack:promptstack@db:5432/promptstack

# JWT Configuration
AUTH_JWT_SECRET_KEY=your-secret-key-change-in-production
AUTH_JWT_ALGORITHM=HS256
AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Origins (comma-separated)
AUTH_API_CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8000

# Development Settings
AUTH_ALLOW_DEV_HEADERS=true

# Optional: OIDC for Production
# AUTH_OIDC_ISSUER=https://cognito-idp.region.amazonaws.com/poolid
# AUTH_OIDC_AUDIENCE=client-id
# AUTH_OIDC_JWKS_URL=https://cognito-idp.region.amazonaws.com/poolid/.well-known/jwks.json
```

See `.env.example` for a complete template.

## API Endpoints

### Health Check

```bash
GET /health
```

Returns service health status.

### Authentication

#### Register User
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "teams": [...],
    "domains": [...]
  }
}
```

#### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Returns same response as register.

#### Validate Token (Service-to-Service)
```bash
POST /auth/validate
Content-Type: application/json

{
  "token": "eyJhbGc..."
}
```

Response:
```json
{
  "valid": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "teams": [...],
    "domains": [...]
  },
  "error": null
}
```

#### Get Current User
```bash
GET /auth/me
Authorization: Bearer <token>
# OR (dev mode)
X-User-Email: user@example.com
X-User-Name: User Name
```

Returns full user context with teams and domains.

### Teams

#### Get User's Teams
```bash
GET /teams
Authorization: Bearer <token>
```

#### Get All Teams
```bash
GET /teams/all
Authorization: Bearer <token>
```

### Domains

#### Get User's Domains
```bash
GET /domains
Authorization: Bearer <token>
```

#### Get All Domains
```bash
GET /domains/all
Authorization: Bearer <token>
```

## Authentication Modes

### Development Mode (Headers)

For local development and testing:

```bash
curl http://localhost:8001/auth/me \
  -H "X-User-Email: user@example.com" \
  -H "X-User-Name: Test User"
```

Set `AUTH_ALLOW_DEV_HEADERS=true` to enable.

### Production Mode (JWT)

1. User logs in and receives JWT token
2. Client includes token in Authorization header
3. Service validates token signature and expiration

```bash
curl http://localhost:8001/auth/me \
  -H "Authorization: Bearer eyJhbGc..."
```

### OIDC Mode (Enterprise)

Configure external identity provider:

```env
AUTH_OIDC_ISSUER=https://cognito-idp.region.amazonaws.com/poolid
AUTH_OIDC_AUDIENCE=client-id
AUTH_OIDC_JWKS_URL=https://cognito-idp.region.amazonaws.com/poolid/.well-known/jwks.json
```

Service will validate tokens from the IdP using JWKS.

## Integration with Other Services

Other microservices should call the `/auth/validate` endpoint to validate user tokens:

```python
import requests

def validate_user_token(token: str):
    response = requests.post(
        "http://auth-service:8001/auth/validate",
        json={"token": token},
        timeout=5
    )
    data = response.json()
    
    if data["valid"]:
        return data["user"]  # Contains id, email, name, teams, domains
    else:
        raise AuthenticationError(data["error"])
```

## Database Setup

### Using Docker Compose

The included `docker-compose.yml` sets up PostgreSQL automatically.

### Using External Database

1. Create a PostgreSQL database
2. Set `DATABASE_URL` environment variable
3. Run Prisma migrations:

```bash
prisma migrate deploy
```

### Seed Data

The service automatically seeds default teams and domains on startup:

**Teams:**
- General
- Engineering
- Product
- Design

**Domains:**
- engineering
- product
- design
- marketing
- sales

Modify `app/seed.py` to customize seed data.

## Development

### Project Structure

```
promptstack-poc-auth/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── auth.py              # Authentication logic
│   ├── schemas.py           # Pydantic models
│   ├── prisma_client.py     # Database client
│   ├── seed.py              # Seed data
│   └── routers/
│       ├── __init__.py
│       ├── health.py        # Health check
│       ├── auth.py          # Auth endpoints
│       ├── teams.py         # Team management
│       └── domains.py       # Domain management
├── prisma/
│   └── schema.prisma        # Database schema
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Adding New Features

1. Update Prisma schema in `prisma/schema.prisma`
2. Generate client: `prisma generate`
3. Add route in `app/routers/`
4. Include router in `app/main.py`
5. Update tests

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Deployment

### Docker

Build and run the Docker image:

```bash
# Build
docker build -t promptstack-auth:latest .

# Run
docker run -p 8001:8001 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e AUTH_JWT_SECRET_KEY="secret" \
  promptstack-auth:latest
```

### AWS ECS Fargate

1. Build and push Docker image to ECR
2. Create ECS task definition with environment variables
3. Create ECS service with Application Load Balancer
4. Configure RDS PostgreSQL instance
5. Set up CloudWatch logging

Example task definition:
```json
{
  "containerDefinitions": [{
    "name": "auth",
    "image": "123456789.dkr.ecr.region.amazonaws.com/promptstack-auth:latest",
    "portMappings": [{"containerPort": 8001}],
    "environment": [
      {"name": "DATABASE_URL", "value": "postgresql://..."},
      {"name": "AUTH_JWT_SECRET_KEY", "value": "..."},
      {"name": "AUTH_ALLOW_DEV_HEADERS", "value": "false"}
    ]
  }]
}
```

### Kubernetes

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: auth
        image: promptstack-auth:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: AUTH_JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: auth-secrets
              key: jwt-secret
```

## Security

### Production Checklist

- [ ] Change `AUTH_JWT_SECRET_KEY` to secure random value (at least 32 characters)
- [ ] Set `AUTH_ALLOW_DEV_HEADERS=false`
- [ ] Use HTTPS/TLS for all connections
- [ ] Configure CORS origins to include only production domains
- [ ] Use managed database service (RDS, Cloud SQL, etc.)
- [ ] Enable database connection encryption
- [ ] Set up monitoring and alerting
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Use secrets manager for sensitive configuration
- [ ] Implement token refresh mechanism
- [ ] Set up automated backups

### Password Security

- Passwords hashed using bcrypt with salt
- Minimum password length enforced (in schemas)
- Password complexity rules (implement as needed)

### JWT Security

- Tokens expire after configured time (default 30 minutes)
- Include user email in `sub` claim
- Validate issuer and audience for OIDC tokens
- Use strong signing algorithm (HS256 or RS256)

## Monitoring

### Health Checks

```bash
# Service health
curl http://localhost:8001/health

# Database connectivity
docker compose exec auth prisma db pull
```

### Logs

```bash
# Docker Compose
docker compose logs -f auth

# Docker
docker logs -f <container-id>

# Kubernetes
kubectl logs -f deployment/auth-service
```

### Metrics

Consider adding:
- Prometheus metrics endpoint
- Request/response times
- Authentication success/failure rates
- Token validation latency
- Database query performance

## Troubleshooting

### Service won't start

```bash
# Check logs
docker compose logs auth

# Verify database connection
docker compose exec auth prisma db pull

# Restart service
docker compose restart auth
```

### Database connection errors

- Verify `DATABASE_URL` is correct
- Check database is running: `docker compose ps db`
- Ensure network connectivity
- Check database credentials

### Authentication failures

- Verify `AUTH_JWT_SECRET_KEY` matches across services
- Check token hasn't expired
- Validate OIDC configuration if using external IdP
- Review CORS settings

### Port conflicts

If port 8001 is in use:

```bash
# Change in docker-compose.yml
ports:
  - "8002:8001"  # Host:Container
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit pull request

## License

Internal use only.

## Support

For questions or issues:
- Check the documentation
- Review logs for error messages
- Contact the platform team

---

**Service Version**: 1.0.0  
**Last Updated**: 2025-11-04

