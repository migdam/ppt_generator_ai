# Production Deployment Guide

This guide covers deploying the PPT Generator AI in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required
- Python 3.9+
- Google Gemini API key
- Minimum 2GB RAM
- 1GB free disk space

### Optional
- Docker 20.10+
- Docker Compose 1.29+
- Kubernetes 1.20+ (for K8s deployment)

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd ppt_generator_ai
```

### 2. Set Environment Variables

Create a `.env` file:

```bash
# Required
export GEMINI_API_KEY="your-api-key-here"

# Optional Configuration
export QUALITY_THRESHOLD=45
export MAX_RETRIES=4
export MAX_QUALITY_ATTEMPTS=5
export REQUEST_TIMEOUT=30
export OUTPUT_DIR="Output"
export LOG_DIR="logs"
export RATE_LIMIT_ENABLED=true
export CACHE_ENABLED=true
```

### 3. Install Dependencies

#### Using Conda (Recommended)

```bash
conda env create -f environment.yml
conda activate ppt_generator
```

#### Using pip

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Docker Deployment

### Build Image

```bash
docker build -t ppt-generator-ai:latest .
```

### Run Container

**Basic Usage:**

```bash
docker run --rm \
  -e GEMINI_API_KEY="your-api-key" \
  -v $(pwd)/Input:/app/Input:ro \
  -v $(pwd)/Output:/app/Output \
  ppt-generator-ai:latest \
  --url https://example.com/article
```

**With Local HTML File:**

```bash
docker run --rm \
  -e GEMINI_API_KEY="your-api-key" \
  -v $(pwd)/Input:/app/Input:ro \
  -v $(pwd)/Output:/app/Output \
  ppt-generator-ai:latest \
  --html sample.html --slides 10 --style detailed
```

### Using Docker Compose

**1. Create .env file:**

```bash
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

**2. Run with docker-compose:**

```bash
# Edit docker-compose.yml to set your desired URL/options
docker-compose up
```

**3. For development:**

```bash
docker-compose --profile dev up ppt-generator-dev
```

## Kubernetes Deployment

### 1. Create Secret for API Key

```bash
kubectl create secret generic ppt-generator-secrets \
  --from-literal=gemini-api-key='your-api-key-here'
```

### 2. Create ConfigMap

Save as `k8s-configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ppt-generator-config
data:
  QUALITY_THRESHOLD: "45"
  MAX_RETRIES: "4"
  OUTPUT_DIR: "/app/Output"
  LOG_DIR: "/app/logs"
```

```bash
kubectl apply -f k8s-configmap.yaml
```

### 3. Create Job

Save as `k8s-job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ppt-generator-job
spec:
  template:
    spec:
      containers:
      - name: ppt-generator
        image: ppt-generator-ai:latest
        args:
          - "--url"
          - "https://example.com/article"
          - "--slides"
          - "auto"
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ppt-generator-secrets
              key: gemini-api-key
        envFrom:
        - configMapRef:
            name: ppt-generator-config
        volumeMounts:
        - name: output
          mountPath: /app/Output
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: output
        persistentVolumeClaim:
          claimName: ppt-output-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: ppt-logs-pvc
      restartPolicy: Never
  backoffLimit: 3
```

```bash
kubectl apply -f k8s-job.yaml
```

## Configuration

### Configuration File

Create `config.json` in the project root:

```json
{
  "gemini_model": "gemini-1.5-flash",
  "quality_threshold": 45,
  "max_quality_attempts": 5,
  "max_retries": 4,
  "request_timeout": 30,
  "output_dir": "Output",
  "log_dir": "logs",
  "default_style": "general",
  "rate_limit_enabled": true,
  "cache_enabled": true
}
```

Use with:

```bash
python main.py --config config.json --url https://example.com
```

### Environment Variables

All configuration can be set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | Required | Google Gemini API key |
| `GEMINI_MODEL` | gemini-1.5-flash | AI model to use |
| `QUALITY_THRESHOLD` | 45 | Minimum quality score |
| `MAX_QUALITY_ATTEMPTS` | 5 | Max feedback loop attempts |
| `MAX_RETRIES` | 4 | Max network retry attempts |
| `REQUEST_TIMEOUT` | 30 | HTTP request timeout (seconds) |
| `OUTPUT_DIR` | Output | Output directory path |
| `INPUT_DIR` | Input | Input directory path |
| `LOG_DIR` | logs | Logs directory path |
| `RATE_LIMIT_ENABLED` | true | Enable API rate limiting |
| `CACHE_ENABLED` | true | Enable response caching |

## Monitoring

### Logs

Logs are stored in the `logs/` directory:

```bash
# View today's logs
tail -f logs/ppt_generator_$(date +%Y%m%d).log

# Search for errors
grep "ERROR" logs/*.log

# Watch real-time
tail -f logs/*.log | grep -E "ERROR|WARNING"
```

### Metrics

Metrics are stored in `metrics/` directory as JSON Lines:

```bash
# View today's metrics
cat metrics/metrics_$(date +%Y%m%d).jsonl | jq '.'

# Get summary stats
python -c "
from modules.metrics import get_metrics_collector
collector = get_metrics_collector()
stats = collector.get_summary_stats(days=7)
print(f'Success rate: {stats[\"successful_sessions\"] / stats[\"total_sessions\"] * 100:.1f}%')
print(f'Avg time: {stats[\"avg_generation_time\"]:.1f}s')
"
```

### Health Checks

**Docker:**

```bash
docker inspect --format='{{json .State.Health}}' ppt-generator | jq '.'
```

**Application:**

```bash
# Check if application starts
python main.py --help

# Validate configuration
python -c "from modules.config import get_config; print(get_config())"
```

## Security

### Best Practices

1. **Never commit API keys** - Use environment variables or secrets management
2. **Use non-root user** - Docker image uses non-root user `pptgen`
3. **Limit file access** - Input validation prevents path traversal
4. **Enable HTTPS only** - Default URL validation allows only http/https
5. **Rate limiting** - Built-in rate limiting prevents API abuse

### Secret Management

**Using Docker Secrets:**

```bash
echo "your-api-key" | docker secret create gemini_api_key -

docker service create \
  --name ppt-generator \
  --secret gemini_api_key \
  ppt-generator-ai:latest
```

**Using Kubernetes Secrets:**

```bash
kubectl create secret generic ppt-generator-secrets \
  --from-literal=gemini-api-key='your-api-key'
```

### Network Security

- Firewall rules: Allow outbound HTTPS (443) for API calls
- Restrict inbound access to management interfaces only
- Use VPC/private networks when possible

## Troubleshooting

### Common Issues

**1. API Key Not Found**

```
Error: GEMINI_API_KEY not found or invalid
```

Solution:
```bash
export GEMINI_API_KEY="your-key"
# Or add to ~/.zshrc or ~/.bashrc
```

**2. Permission Denied (Docker)**

```
Permission denied: '/app/Output'
```

Solution:
```bash
chmod -R 777 Output logs metrics
# Or run container as current user
docker run --user $(id -u):$(id -g) ...
```

**3. Module Not Found**

```
ModuleNotFoundError: No module named 'xyz'
```

Solution:
```bash
pip install -r requirements.txt
# Or rebuild Docker image
docker build --no-cache -t ppt-generator-ai:latest .
```

**4. Network Timeout**

```
Request timed out after 30 seconds
```

Solution:
```bash
# Increase timeout
export REQUEST_TIMEOUT=60
# Or use environment variable
python main.py --url https://slow-site.com
```

**5. Quality Score Never Meets Threshold**

```
Max attempts reached. Using best plan (score: 42/50)
```

Solution:
```bash
# Lower threshold
export QUALITY_THRESHOLD=40
# Or use different style
python main.py --url https://example.com --style detailed
```

### Debugging

**Enable verbose logging:**

```bash
python main.py --verbose --url https://example.com
```

**Check logs:**

```bash
tail -f logs/ppt_generator_*.log
```

**Test individual components:**

```bash
# Test validators
python -m pytest tests/test_validators.py -v

# Test configuration
python -c "from modules.config import get_config; print(get_config())"

# Test extraction
python -c "
from modules.content_extractor import ContentExtractor
ext = ContentExtractor()
content, images, title = ext.extract_from_url('https://example.com')
print(f'Words: {len(content.split())}, Images: {len(images)}')
"
```

## Performance Optimization

### Caching

Enable caching to speed up repeated requests:

```bash
export CACHE_ENABLED=true
export CACHE_TTL=3600  # 1 hour
```

### Parallel Processing

Enable parallel image downloads:

```bash
export PARALLEL_IMAGE_DOWNLOADS=true
export MAX_CONCURRENT_DOWNLOADS=5
```

### Resource Limits

**Docker:**

```bash
docker run --memory=2g --cpus=1.0 ppt-generator-ai:latest
```

**Kubernetes:**

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## Scaling

### Horizontal Scaling

Run multiple instances for parallel processing:

```bash
# Process multiple URLs in parallel
for url in url1 url2 url3; do
  docker run --rm -d \
    -e GEMINI_API_KEY="$GEMINI_API_KEY" \
    -v $(pwd)/Output:/app/Output \
    ppt-generator-ai:latest \
    --url "$url" &
done
```

### Queue-Based Processing

Integrate with message queues (RabbitMQ, SQS, etc.) for asynchronous processing.

## Backup and Recovery

### Backup

```bash
# Backup outputs
tar -czf outputs-backup-$(date +%Y%m%d).tar.gz Output/

# Backup metrics
tar -czf metrics-backup-$(date +%Y%m%d).tar.gz metrics/

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### Recovery

```bash
# Restore from backup
tar -xzf outputs-backup-20231118.tar.gz
tar -xzf metrics-backup-20231118.tar.gz
```

## Support

For issues and questions:
- Check logs in `logs/` directory
- Review metrics in `metrics/` directory
- Run tests: `pytest tests/ -v`
- Enable verbose mode: `--verbose`

## License

See [LICENSE](LICENSE) file for details.
