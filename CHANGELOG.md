# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-04

### Added
- Initial release of PromptStack Auth Service
- User registration and login endpoints
- JWT token generation and validation
- Token validation endpoint for service-to-service authentication
- User context API with teams and domains
- Team management endpoints
- Domain management endpoints
- Support for development header authentication
- Support for OIDC integration
- Docker containerization
- Docker Compose setup with PostgreSQL
- Comprehensive documentation
- Health check endpoint
- Automatic seeding of default teams and domains

### Security
- Password hashing with bcrypt
- JWT token expiration
- CORS configuration
- Environment-based configuration
# Ignore Python cache and virtual environment
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Prisma
node_modules/
.prisma/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# Docker
*.tar

