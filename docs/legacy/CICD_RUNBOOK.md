# CI/CD Runbook

This runbook provides detailed information about the CI/CD pipeline, troubleshooting guides, and operational procedures for the Portfolio Agent project.

## Table of Contents

- [Pipeline Overview](#pipeline-overview)
- [Workflow Details](#workflow-details)
- [Quality Gates](#quality-gates)
- [Security Scanning](#security-scanning)
- [Deployment Procedures](#deployment-procedures)
- [Monitoring & Alerting](#monitoring--alerting)
- [Troubleshooting](#troubleshooting)
- [Emergency Procedures](#emergency-procedures)

## Pipeline Overview

The CI/CD pipeline consists of multiple workflows:

### 1. CI Pipeline (`ci.yaml`)
- **Trigger**: Push to main/develop, PRs, daily schedule
- **Jobs**: Lint, Test, Security Scan, Performance Test, Build
- **Duration**: ~15-20 minutes
- **Success Criteria**: All jobs must pass

### 2. Docker Pipeline (`docker.yml`)
- **Trigger**: Push to main/develop, PRs, tags
- **Jobs**: Build, Security Scan, Deploy
- **Duration**: ~10-15 minutes
- **Success Criteria**: Image builds and scans pass

### 3. Deployment Pipeline (`deploy.yml`)
- **Trigger**: Push to main, tags, manual dispatch
- **Jobs**: Deploy Staging, Deploy Production
- **Duration**: ~5-10 minutes
- **Success Criteria**: Deployment successful, smoke tests pass

## Workflow Details

### CI Pipeline Jobs

#### 1. Lint Job
```yaml
# Code Quality & Linting
- Black (Code Formatting)
- isort (Import Sorting)
- Flake8 (Linting)
- MyPy (Type Checking)
```

**Success Criteria:**
- All code formatting checks pass
- No linting errors
- Type checking passes (warnings allowed)

**Common Issues:**
- Code formatting violations → Run `black .` and `isort .`
- Import sorting issues → Run `isort .`
- Linting errors → Fix according to flake8 suggestions
- Type errors → Add type hints or ignore with `# type: ignore`

#### 2. Test Job
```yaml
# Matrix Testing
- Python 3.12, 3.13
- Test Groups: unit, integration, security
- Coverage reporting
- JUnit XML output
```

**Success Criteria:**
- All tests pass
- Coverage > 80%
- No test failures

**Common Issues:**
- Test failures → Check test logs, fix failing tests
- Coverage too low → Add more tests
- Timeout issues → Optimize slow tests

#### 3. Security Scan Job
```yaml
# Security Scanning
- Bandit (Security Linting)
- Safety (Dependency Vulnerabilities)
- Semgrep (SAST)
- Secret Scanning
```

**Success Criteria:**
- No high-severity security issues
- No exposed secrets
- Dependency vulnerabilities addressed

**Common Issues:**
- Security vulnerabilities → Update dependencies or fix code
- Exposed secrets → Remove or redact secrets
- False positives → Add exceptions to security configs

#### 4. Performance Test Job
```yaml
# Performance Testing
- Benchmark tests
- Load testing
- Memory usage tests
- Concurrent operation tests
```

**Success Criteria:**
- Performance benchmarks pass
- No memory leaks
- Concurrent operations work correctly

**Common Issues:**
- Performance regressions → Optimize code or adjust thresholds
- Memory leaks → Fix memory management issues
- Timeout issues → Optimize slow operations

#### 5. Build Job
```yaml
# Build & Package
- Package build
- Package validation
- Installation test
- Artifact upload
```

**Success Criteria:**
- Package builds successfully
- Package installs correctly
- All dependencies resolved

**Common Issues:**
- Build failures → Check dependencies and build configuration
- Installation issues → Verify package structure
- Dependency conflicts → Resolve version conflicts

### Docker Pipeline Jobs

#### 1. Build Job
```yaml
# Docker Build
- Multi-platform build (amd64, arm64)
- Metadata extraction
- Image tagging
- Registry push
```

**Success Criteria:**
- Image builds successfully
- Multi-platform support works
- Image pushes to registry

**Common Issues:**
- Build failures → Check Dockerfile and dependencies
- Platform issues → Verify multi-platform support
- Registry issues → Check authentication and permissions

#### 2. Security Scan Job
```yaml
# Container Security
- Trivy vulnerability scan
- SARIF report generation
- GitHub Security tab upload
```

**Success Criteria:**
- No critical vulnerabilities
- Security report generated
- Results uploaded to GitHub

**Common Issues:**
- Vulnerabilities → Update base image or dependencies
- Scan failures → Check Trivy configuration
- Upload issues → Verify GitHub permissions

### Deployment Pipeline Jobs

#### 1. Deploy Staging
```yaml
# Staging Deployment
- Image build and push
- Environment deployment
- Smoke tests
- Notification
```

**Success Criteria:**
- Deployment successful
- Smoke tests pass
- Service accessible

**Common Issues:**
- Deployment failures → Check environment configuration
- Test failures → Verify application functionality
- Access issues → Check networking and ingress

#### 2. Deploy Production
```yaml
# Production Deployment
- Image build and push
- Environment deployment
- Production tests
- Release creation
- Notification
```

**Success Criteria:**
- Deployment successful
- Production tests pass
- Release created
- Service accessible

**Common Issues:**
- Deployment failures → Check production environment
- Test failures → Verify production functionality
- Release issues → Check GitHub permissions

## Quality Gates

### Pre-Deployment Checks

1. **Code Quality**
   - All linting checks pass
   - Type checking passes
   - Code coverage > 80%

2. **Testing**
   - All unit tests pass
   - All integration tests pass
   - All security tests pass
   - Performance tests pass

3. **Security**
   - No high-severity vulnerabilities
   - No exposed secrets
   - Security scans pass

4. **Build**
   - Package builds successfully
   - Docker image builds successfully
   - All artifacts created

### Deployment Gates

1. **Staging**
   - All pre-deployment checks pass
   - Staging deployment successful
   - Smoke tests pass

2. **Production**
   - Staging deployment successful
   - Production deployment successful
   - Production tests pass
   - Monitoring shows healthy status

## Security Scanning

### Automated Scans

1. **Code Security (Bandit)**
   - Scans for common security issues
   - Generates JSON report
   - Fails on high-severity issues

2. **Dependency Security (Safety)**
   - Checks for known vulnerabilities
   - Generates JSON report
   - Fails on critical vulnerabilities

3. **Static Analysis (Semgrep)**
   - SAST scanning
   - OWASP Top 10 checks
   - Generates SARIF report

4. **Secret Scanning**
   - Scans for exposed secrets
   - Checks for API keys, tokens
   - Fails on any secrets found

5. **Container Security (Trivy)**
   - Scans Docker images
   - Checks for vulnerabilities
   - Generates SARIF report

### Security Reports

Reports are generated and uploaded to:
- **GitHub Security Tab**: SARIF reports
- **Artifacts**: JSON reports for detailed analysis
- **Logs**: Console output for immediate feedback

## Deployment Procedures

### Staging Deployment

1. **Automatic Trigger**
   - Push to `develop` branch
   - Manual workflow dispatch

2. **Deployment Steps**
   ```bash
   # 1. Build and push image
   docker build -t ghcr.io/shelabhtyagi/portfolio-agent-package:staging .
   docker push ghcr.io/shelabhtyagi/portfolio-agent-package:staging
   
   # 2. Deploy to staging
   kubectl set image deployment/portfolio-agent portfolio-agent=ghcr.io/shelabhtyagi/portfolio-agent-package:staging
   kubectl rollout status deployment/portfolio-agent
   
   # 3. Run smoke tests
   curl -f http://staging.portfolio-agent.com/health
   ```

3. **Verification**
   - Check deployment status
   - Run smoke tests
   - Verify service accessibility
   - Check monitoring dashboards

### Production Deployment

1. **Automatic Trigger**
   - Push tag (e.g., `v1.0.0`)
   - Manual workflow dispatch

2. **Deployment Steps**
   ```bash
   # 1. Build and push image
   docker build -t ghcr.io/shelabhtyagi/portfolio-agent-package:v1.0.0 .
   docker push ghcr.io/shelabhtyagi/portfolio-agent-package:v1.0.0
   
   # 2. Deploy to production
   kubectl set image deployment/portfolio-agent portfolio-agent=ghcr.io/shelabhtyagi/portfolio-agent-package:v1.0.0
   kubectl rollout status deployment/portfolio-agent
   
   # 3. Run production tests
   curl -f https://portfolio-agent.com/health
   ```

3. **Verification**
   - Check deployment status
   - Run production tests
   - Verify service accessibility
   - Check monitoring dashboards
   - Create GitHub release

### Rollback Procedures

#### Staging Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/portfolio-agent -n staging

# Check rollback status
kubectl rollout status deployment/portfolio-agent -n staging
```

#### Production Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/portfolio-agent -n production

# Check rollback status
kubectl rollout status deployment/portfolio-agent -n production

# Verify service
curl -f https://portfolio-agent.com/health
```

## Monitoring & Alerting

### Pipeline Monitoring

1. **GitHub Actions**
   - Workflow status
   - Job duration
   - Failure notifications

2. **External Monitoring**
   - Service health checks
   - Performance metrics
   - Error rates

### Alerting Rules

1. **Pipeline Failures**
   - Any job failure
   - Security scan failures
   - Deployment failures

2. **Service Health**
   - Service down
   - High error rates
   - Performance degradation

### Notification Channels

1. **Slack**
   - Pipeline status updates
   - Deployment notifications
   - Alert notifications

2. **Email**
   - Critical failures
   - Security issues
   - Production deployments

## Troubleshooting

### Common Pipeline Issues

#### 1. Lint Failures
```bash
# Fix formatting issues
black .
isort .

# Fix linting issues
flake8 . --max-line-length=88 --extend-ignore=E203,W503

# Fix type issues
mypy src/portfolio_agent --ignore-missing-imports
```

#### 2. Test Failures
```bash
# Run tests locally
pytest tests/ -v

# Run specific test group
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=src/portfolio_agent --cov-report=html
```

#### 3. Security Scan Failures
```bash
# Run security scans locally
bandit -r src/
safety check
semgrep --config=auto src/
```

#### 4. Build Failures
```bash
# Build package locally
poetry build

# Check package
poetry run twine check dist/*

# Build Docker image locally
docker build -t portfolio-agent:test .
```

#### 5. Deployment Failures
```bash
# Check deployment status
kubectl get pods -n portfolio-agent

# Check logs
kubectl logs -f deployment/portfolio-agent -n portfolio-agent

# Check service
kubectl get svc -n portfolio-agent
```

### Debugging Commands

#### Pipeline Debug
```bash
# Check workflow runs
gh run list

# View workflow logs
gh run view <run-id>

# Rerun failed workflow
gh run rerun <run-id>
```

#### Application Debug
```bash
# Check application health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:8000/metrics

# Check logs
docker-compose logs -f portfolio-agent
```

#### Infrastructure Debug
```bash
# Check Kubernetes resources
kubectl get all -n portfolio-agent

# Check ingress
kubectl get ingress -n portfolio-agent

# Check persistent volumes
kubectl get pv,pvc -n portfolio-agent
```

## Emergency Procedures

### Pipeline Emergency

1. **Stop All Pipelines**
   ```bash
   # Cancel running workflows
   gh run cancel <run-id>
   
   # Disable workflows (if needed)
   # Go to GitHub Actions settings and disable workflows
   ```

2. **Emergency Deployment**
   ```bash
   # Deploy previous known good version
   kubectl set image deployment/portfolio-agent portfolio-agent=ghcr.io/shelabhtyagi/portfolio-agent-package:v0.9.0
   kubectl rollout status deployment/portfolio-agent
   ```

### Service Emergency

1. **Service Down**
   ```bash
   # Check service status
   kubectl get pods -n portfolio-agent
   
   # Restart deployment
   kubectl rollout restart deployment/portfolio-agent
   
   # Scale up if needed
   kubectl scale deployment portfolio-agent --replicas=5
   ```

2. **Data Issues**
   ```bash
   # Check database connectivity
   kubectl exec -it deployment/portfolio-agent -- python -c "import psycopg2; print('DB OK')"
   
   # Check Redis connectivity
   kubectl exec -it deployment/portfolio-agent -- python -c "import redis; print('Redis OK')"
   ```

3. **Security Incident**
   ```bash
   # Check audit logs
   kubectl logs deployment/portfolio-agent | grep -i "security\|auth\|error"
   
   # Check for suspicious activity
   kubectl exec -it deployment/portfolio-agent -- python -c "from portfolio_agent.security.audit_logger import AuditLogger; print('Audit OK')"
   ```

### Communication Plan

1. **Internal Team**
   - Slack notification
   - Email alert
   - Phone call (critical issues)

2. **External Communication**
   - Status page update
   - User notification
   - Public communication (if needed)

### Recovery Procedures

1. **Data Recovery**
   ```bash
   # Backup current state
   kubectl exec deployment/postgres -- pg_dump -U portfolio portfolio_db > backup-$(date +%Y%m%d-%H%M%S).sql
   
   # Restore from backup
   kubectl exec -i deployment/postgres -- psql -U portfolio portfolio_db < backup-20240101-120000.sql
   ```

2. **Service Recovery**
   ```bash
   # Restart all services
   kubectl rollout restart deployment/portfolio-agent
   kubectl rollout restart deployment/postgres
   kubectl rollout restart deployment/redis
   
   # Verify recovery
   curl -f https://portfolio-agent.com/health
   ```

## Best Practices

### Development

1. **Code Quality**
   - Run linting before commits
   - Write comprehensive tests
   - Use type hints
   - Follow security best practices

2. **Testing**
   - Test locally before pushing
   - Write unit and integration tests
   - Test security features
   - Performance test critical paths

### Deployment

1. **Staging First**
   - Always deploy to staging first
   - Run smoke tests
   - Verify functionality
   - Check monitoring

2. **Production Deployment**
   - Use tags for releases
   - Monitor deployment closely
   - Have rollback plan ready
   - Communicate with team

### Monitoring

1. **Continuous Monitoring**
   - Monitor pipeline health
   - Monitor service health
   - Monitor security events
   - Monitor performance metrics

2. **Alerting**
   - Set up appropriate alerts
   - Test alerting systems
   - Respond to alerts quickly
   - Document alert procedures

## Support

For CI/CD issues:

1. **Check Documentation**
   - This runbook
   - GitHub Actions documentation
   - Kubernetes documentation

2. **Check Logs**
   - GitHub Actions logs
   - Application logs
   - Infrastructure logs

3. **Contact Support**
   - Create GitHub issue
   - Contact team via Slack
   - Escalate to on-call engineer

4. **Emergency Contact**
   - On-call engineer: [contact info]
   - Team lead: [contact info]
   - Security team: [contact info]
