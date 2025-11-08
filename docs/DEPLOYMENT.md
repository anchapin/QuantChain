# Production Deployment Guide

This document outlines the production deployment process for QuantChain.

## Deployment Pipeline

### Automated Deployment

QuantChain uses GitHub Actions for automated CI/CD deployment. The deployment pipeline triggers on:

1. **Code pushes** to `main` branch - Runs CI tests only
2. **Pull requests** to `main` branch - Runs CI tests only  
3. **Release creation/publishing** - Runs full CI + CD pipeline

### Deployment Jobs

#### 1. Lint and Format
- Runs Black code formatting checks
- Runs Flake8 linting with project standards
- Runs MyPy type checking

#### 2. Unit Tests
- Matrix testing across Python 3.11, 3.12, 3.13
- Runs all unit tests with coverage reporting
- Uploads coverage to Codecov

#### 3. Integration Tests  
- Matrix testing across Python 3.12, 3.13
- Runs integration tests for end-to-end workflows
- Uploads coverage to Codecov

#### 4. Slow Tests
- Runs on main branch or with `run-slow-tests` label
- Tests full system with all optional dependencies
- Matrix testing across Python 3.12, 3.13

#### 5. Production Deploy (on Release)
- Builds Python package using `build`
- Publishes to PyPI using token authentication
- Builds and pushes Docker image to GitHub Container Registry
- Deploys with semantic versioning based on release tag

## Manual Deployment

### PyPI Publishing

1. **Create a release** on GitHub:
   - Create new release with semantic version (e.g., `v0.1.0`)
   - Write release notes
   - Publish release

2. **Set up PyPI token** (first time only):
   - Generate API token at https://pypi.org/manage/api/tokens
   - Add as repository secret: `PYPI_API_TOKEN`

3. **Deployment triggers automatically**:
   - Tests run and must pass
   - Package builds and uploads to PyPI
   - Docker image builds and pushes to GHCR

### Docker Deployment

1. **Pull the Docker image**:
   ```bash
   docker pull ghcr.io/username/quantchain:latest
   docker pull ghcr.io/username/quantchain:v0.1.0
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 ghcr.io/username/quantchain:latest
   ```

3. **With environment variables**:
   ```bash
   docker run -p 8000:8000 \
     -e OPENAI_API_KEY=your_key \
     -e DATABASE_URL=your_db_url \
     ghcr.io/username/quantchain:latest
   ```

## Environment Configuration

### Production Environment
- URL: https://quantchain.dev
- Type: Production
- Protection: Requires approval for deployments

### Required Secrets
- `PYPI_API_TOKEN`: PyPI upload token
- `GITHUB_TOKEN`: GitHub API token (automatically provided)

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for LLM providers
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string for caching
- `ALPACA_API_KEY`: Alpaca trading API key
- `ALPACA_SECRET_KEY`: Alpaca trading secret key

## Monitoring and Observability

### CI/CD Pipeline Monitoring
- GitHub Actions dashboard monitors pipeline runs
- Codecov dashboard tracks test coverage
- Docker Hub/GHCR monitors image builds

### Production Monitoring
- Application logs via structured logging
- Performance metrics via integrated monitoring
- Error tracking with alerting setup
- Health check endpoints for service monitoring

## Rollback Procedures

### Package Rollback
1. Create new release with previous version number
2. Tag and publish to trigger automated deployment

### Docker Rollback
1. Pull previous version:
   ```bash
   docker pull ghcr.io/username/quantchain:v0.0.9
   ```
2. Redeploy with previous version tag

### Database Rollback
- Database migrations are versioned
- Use `alembic downgrade <version>` to rollback schema changes

## Security Considerations

### Access Control
- Production deployments require approval
- API keys stored in GitHub Secrets
- Principle of least privilege applied

### Code Security
- All code passes linting and type checking
- Dependencies scanned for vulnerabilities
- Secret scanning enabled on repository

### Network Security
- HTTPS enforced for all endpoints
- API rate limiting implemented
- CORS policies configured appropriately

## Performance Considerations

### Build Optimization
- Docker images use multi-stage builds
- Python packages cached in CI/CD
- Parallel testing reduces pipeline duration

### Runtime Optimization
- Application runs on optimized Docker base
- Connection pooling for database access
- Redis caching for frequently accessed data

## Troubleshooting

### Common CI/CD Issues

1. **Test failures**:
   - Check logs in GitHub Actions
   - Run tests locally to reproduce
   - Update fixtures or test data as needed

2. **Build failures**:
   - Verify requirements.txt syntax
   - Check dependency versions compatibility
   - Update Dockerfile if necessary

3. **Deployment failures**:
   - Verify PyPI token validity
   - Check Docker build logs
   - Confirm GitHub secrets are configured

### Production Issues

1. **Service unavailable**:
   - Check deployment status in GitHub Actions
   - Verify environment variables are set
   - Check application logs

2. **Performance degradation**:
   - Monitor resource usage
   - Check database connection pool
   - Review recent code changes

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing in CI
- [ ] Documentation updated
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] Security scan completed

### Post-Deployment
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Load testing completed
- [ ] Documentation verified
- [ ] Backup procedures confirmed

## Support

For deployment issues:
1. Check this documentation first
2. Review GitHub Actions logs
3. Check existing GitHub Issues
4. Create new issue with deployment details
5. Contact dev team for urgent issues

---

*This deployment guide is part of QuantChain's documentation suite. For additional information, see the main README.md.*
