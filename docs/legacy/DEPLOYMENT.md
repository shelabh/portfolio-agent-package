# Deployment Guide

This guide covers deployment options for the Portfolio Agent, including Docker, Kubernetes, and cloud platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 4GB+ RAM recommended
- **Storage**: 10GB+ available disk space
- **Network**: Internet access for API calls and model downloads

### Software Requirements

- Docker 20.10+ or Kubernetes 1.20+
- Python 3.12+ (for local development)
- PostgreSQL 13+ with pgvector extension
- Redis 6+ (optional, for caching)

## Docker Deployment

### Quick Start

```bash
# Clone the repository
git clone https://github.com/shelabhtyagi/portfolio-agent-package.git
cd portfolio-agent-package

# Start all services with Docker Compose
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f portfolio-agent
```

### Production Docker Deployment

```bash
# Build production image
docker build -t portfolio-agent:latest .

# Run with environment variables
docker run -d \
  --name portfolio-agent \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379 \
  portfolio-agent:latest
```

### Docker Compose Services

The `docker-compose.yml` includes:

- **portfolio-agent**: Main application
- **postgres**: PostgreSQL with pgvector
- **redis**: Redis for caching
- **nginx**: Reverse proxy
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboard

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3+ (optional)

### Basic Kubernetes Deployment

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: portfolio-agent

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: portfolio-agent-config
  namespace: portfolio-agent
data:
  LOCAL_ONLY: "false"
  LOG_LEVEL: "INFO"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: portfolio-agent-secrets
  namespace: portfolio-agent
type: Opaque
data:
  OPENAI_API_KEY: <base64-encoded-key>
  DATABASE_URL: <base64-encoded-url>

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portfolio-agent
  namespace: portfolio-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: portfolio-agent
  template:
    metadata:
      labels:
        app: portfolio-agent
    spec:
      containers:
      - name: portfolio-agent
        image: ghcr.io/shelabhtyagi/portfolio-agent-package:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: portfolio-agent-secrets
              key: OPENAI_API_KEY
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: portfolio-agent-secrets
              key: DATABASE_URL
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: portfolio-agent-service
  namespace: portfolio-agent
spec:
  selector:
    app: portfolio-agent
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: portfolio-agent-ingress
  namespace: portfolio-agent
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - portfolio-agent.example.com
    secretName: portfolio-agent-tls
  rules:
  - host: portfolio-agent.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: portfolio-agent-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n portfolio-agent

# Check service
kubectl get svc -n portfolio-agent

# View logs
kubectl logs -f deployment/portfolio-agent -n portfolio-agent
```

### Helm Chart (Optional)

```bash
# Create Helm chart
helm create portfolio-agent-chart

# Install with Helm
helm install portfolio-agent ./portfolio-agent-chart \
  --namespace portfolio-agent \
  --create-namespace \
  --set image.tag=latest \
  --set replicaCount=3
```

## Cloud Deployment

### AWS EKS

```bash
# Create EKS cluster
eksctl create cluster --name portfolio-agent-cluster --region us-west-2

# Deploy application
kubectl apply -f k8s/

# Create load balancer
kubectl expose deployment portfolio-agent --type=LoadBalancer
```

### Google GKE

```bash
# Create GKE cluster
gcloud container clusters create portfolio-agent-cluster \
  --zone us-central1-a \
  --num-nodes 3

# Deploy application
kubectl apply -f k8s/
```

### Azure AKS

```bash
# Create AKS cluster
az aks create --resource-group myResourceGroup \
  --name portfolio-agent-cluster \
  --node-count 3

# Deploy application
kubectl apply -f k8s/
```

## Environment Configuration

### Required Environment Variables

```bash
# API Keys
OPENAI_API_KEY=sk-...
HUGGINGFACE_API_KEY=hf_...

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis (optional)
REDIS_URL=redis://host:6379

# Security
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# Application
LOCAL_ONLY=false
LOG_LEVEL=INFO
DEBUG=false
```

### Optional Environment Variables

```bash
# Vector Store
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...

# Monitoring
PROMETHEUS_ENDPOINT=http://prometheus:9090
GRAFANA_ENDPOINT=http://grafana:3000

# Features
ENABLE_ANALYTICS=true
ENABLE_MONITORING=true
ENABLE_SECURITY_SCANNING=true
```

## Monitoring & Observability

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Metrics endpoint
curl http://localhost:8000/metrics
```

### Prometheus Metrics

The application exposes metrics at `/metrics`:

- `portfolio_agent_requests_total`: Total HTTP requests
- `portfolio_agent_request_duration_seconds`: Request duration
- `portfolio_agent_active_connections`: Active connections
- `portfolio_agent_vector_operations_total`: Vector operations

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (admin/admin):

- **Application Dashboard**: Request rates, response times, error rates
- **Infrastructure Dashboard**: CPU, memory, disk usage
- **Security Dashboard**: Authentication, authorization events

### Logging

```bash
# View application logs
docker-compose logs -f portfolio-agent

# View all service logs
docker-compose logs -f

# Kubernetes logs
kubectl logs -f deployment/portfolio-agent -n portfolio-agent
```

## Security Considerations

### Network Security

- Use TLS/SSL for all external communications
- Implement network policies in Kubernetes
- Use private networks for internal communication

### Data Security

- Encrypt data at rest and in transit
- Use secure secret management (Kubernetes secrets, AWS Secrets Manager)
- Implement proper access controls

### Application Security

- Enable security scanning in CI/CD
- Use non-root containers
- Implement rate limiting
- Enable audit logging

### Example Security Configuration

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: portfolio-agent-network-policy
  namespace: portfolio-agent
spec:
  podSelector:
    matchLabels:
      app: portfolio-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
```

## Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check logs
docker-compose logs portfolio-agent

# Check environment variables
docker-compose exec portfolio-agent env

# Check database connectivity
docker-compose exec portfolio-agent python -c "import psycopg2; print('DB OK')"
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Check database exists
docker-compose exec postgres psql -U portfolio -d portfolio_db -c "\l"

# Check pgvector extension
docker-compose exec postgres psql -U portfolio -d portfolio_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Check application metrics
curl http://localhost:8000/metrics

# Check database performance
docker-compose exec postgres psql -U portfolio -d portfolio_db -c "SELECT * FROM pg_stat_activity;"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Run with debug mode
docker-compose up portfolio-agent
```

### Backup and Recovery

```bash
# Backup database
docker-compose exec postgres pg_dump -U portfolio portfolio_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U portfolio portfolio_db < backup.sql

# Backup application data
docker-compose exec portfolio-agent tar -czf /tmp/data-backup.tar.gz /app/data
```

## Support

For deployment issues:

1. Check the logs: `docker-compose logs -f`
2. Review the troubleshooting section
3. Check GitHub issues: https://github.com/shelabhtyagi/portfolio-agent-package/issues
4. Create a new issue with deployment details

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
