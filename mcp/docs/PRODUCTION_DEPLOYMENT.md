# Production Deployment Guide

This guide covers deploying the Offshore Leaks MCP Server in production environments with proper security, monitoring, and resilience.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+) or macOS 10.15+
- **Python**: 3.10+ (Python 3.11+ recommended for optimal performance)
- **Memory**: 2GB RAM (4GB+ recommended for large datasets)
- **Storage**: 10GB free space (more if storing exports)
- **Network**: Stable connection to Neo4j database

**Recommended Production Specs:**
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ SSD
- **Network**: Gigabit connection with low latency to database

### Dependencies

**Required Services:**
- Neo4j database (4.x or 5.x) with offshore leaks data
- Python 3.10+ with pip
- Virtual environment manager (venv, conda, or pyenv)

**Optional but Recommended:**
- Reverse proxy (nginx, Apache, or Traefik)
- Process manager (systemd, supervisord, or PM2)
- Log aggregation (ELK stack, Fluentd, or similar)
- Monitoring (Prometheus + Grafana)

## Installation

### 1. System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# sudo yum update -y                    # RHEL/CentOS

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential

# Create dedicated user (recommended)
sudo useradd -m -s /bin/bash offshore-leaks
sudo usermod -aG sudo offshore-leaks  # If admin access needed
```

### 2. Application Setup

```bash
# Switch to application user
sudo -u offshore-leaks -i

# Clone repository
git clone https://github.com/markramm/offshoreleaks-data-packages.git
cd offshoreleaks-data-packages/mcp

# Create production virtual environment
python3.11 -m venv venv-prod
source venv-prod/bin/activate

# Install with production dependencies
pip install --upgrade pip
pip install -e ".[mcp]"

# Verify installation
python -c "from offshore_leaks_mcp.mcp_server import MCPOffshoreLeaksServer; print('✅ Installation successful')"
```

### 3. Configuration

Create production configuration file:

```bash
# Create configuration directory
mkdir -p /etc/offshore-leaks-mcp
sudo chown offshore-leaks:offshore-leaks /etc/offshore-leaks-mcp

# Create production config
cat > /etc/offshore-leaks-mcp/production.yaml << EOF
server:
  version: "0.1.0"
  environment: "production"
  log_level: "INFO"
  query_timeout: 30.0
  max_concurrent_queries: 10

neo4j:
  uri: "bolt://your-neo4j-server:7687"
  user: "neo4j"
  password: "your-secure-password"
  database: "offshoreleaks"
  connection_timeout: 10.0
  max_connection_pool_size: 20
  max_connection_lifetime: 3600

resilience:
  retry_attempts: 5
  circuit_breaker_threshold: 3
  health_check_interval: 30

security:
  enable_auth: true
  api_key_required: true
  rate_limiting: true
  max_requests_per_minute: 100

logging:
  level: "INFO"
  format: "json"
  file: "/var/log/offshore-leaks-mcp/server.log"
  max_size: "100MB"
  backup_count: 10
EOF
```

### 4. Environment Variables

Create secure environment file:

```bash
# Create environment file
sudo touch /etc/offshore-leaks-mcp/.env
sudo chown offshore-leaks:offshore-leaks /etc/offshore-leaks-mcp/.env
sudo chmod 600 /etc/offshore-leaks-mcp/.env

# Add sensitive configuration
cat > /etc/offshore-leaks-mcp/.env << EOF
NEO4J_PASSWORD=your-very-secure-password
API_KEY=your-secure-api-key-here
ENCRYPTION_KEY=your-encryption-key-for-sensitive-data
DEBUG=false
ENVIRONMENT=production
EOF
```

## Security Configuration

### 1. Database Security

```bash
# Neo4j security configuration
# Edit neo4j.conf:
dbms.security.auth_enabled=true
dbms.connectors.default_listen_address=127.0.0.1  # Local only
dbms.connector.bolt.tls_level=REQUIRED            # Require TLS
dbms.ssl.policy.bolt.enabled=true
```

### 2. Application Security

```bash
# Create secure directories
sudo mkdir -p /var/log/offshore-leaks-mcp
sudo mkdir -p /var/lib/offshore-leaks-mcp/exports
sudo chown -R offshore-leaks:offshore-leaks /var/log/offshore-leaks-mcp
sudo chown -R offshore-leaks:offshore-leaks /var/lib/offshore-leaks-mcp
sudo chmod 750 /var/log/offshore-leaks-mcp
sudo chmod 750 /var/lib/offshore-leaks-mcp

# Set file permissions
find /home/offshore-leaks/offshoreleaks-data-packages/mcp -name "*.py" -exec chmod 644 {} \;
chmod 600 /etc/offshore-leaks-mcp/.env
chmod 644 /etc/offshore-leaks-mcp/production.yaml
```

### 3. Firewall Configuration

```bash
# Configure UFW (Ubuntu) or firewalld (RHEL)
sudo ufw allow ssh
sudo ufw allow from trusted-ip-range to any port 8000  # MCP server port
sudo ufw enable

# For more restrictive access:
# sudo ufw allow from 10.0.0.0/8 to any port 8000  # Internal network only
```

## Process Management

### 1. Systemd Service

Create systemd service file:

```bash
sudo cat > /etc/systemd/system/offshore-leaks-mcp.service << EOF
[Unit]
Description=Offshore Leaks MCP Server
After=network.target neo4j.service
Wants=neo4j.service

[Service]
Type=simple
User=offshore-leaks
Group=offshore-leaks
WorkingDirectory=/home/offshore-leaks/offshoreleaks-data-packages/mcp
Environment=PATH=/home/offshore-leaks/offshoreleaks-data-packages/mcp/venv-prod/bin
EnvironmentFile=/etc/offshore-leaks-mcp/.env
ExecStart=/home/offshore-leaks/offshoreleaks-data-packages/mcp/venv-prod/bin/python -m offshore_leaks_mcp.mcp_server
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=offshore-leaks-mcp

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/offshore-leaks-mcp /var/lib/offshore-leaks-mcp

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable offshore-leaks-mcp
sudo systemctl start offshore-leaks-mcp

# Check status
sudo systemctl status offshore-leaks-mcp
```

### 2. Health Monitoring Script

Create health monitoring script:

```bash
cat > /home/offshore-leaks/health-check.sh << 'EOF'
#!/bin/bash

# Health check script for Offshore Leaks MCP Server
LOG_FILE="/var/log/offshore-leaks-mcp/health-check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Function to log messages
log_message() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

# Check if service is running
if systemctl is-active --quiet offshore-leaks-mcp; then
    log_message "INFO: Service is running"

    # Test MCP server health (you can implement actual health check endpoint)
    # For now, just check if process exists
    if pgrep -f "offshore_leaks_mcp.mcp_server" > /dev/null; then
        log_message "INFO: MCP server process is healthy"
        exit 0
    else
        log_message "ERROR: MCP server process not found"
        # Attempt restart
        sudo systemctl restart offshore-leaks-mcp
        log_message "INFO: Attempted service restart"
        exit 1
    fi
else
    log_message "ERROR: Service is not running"
    # Attempt restart
    sudo systemctl restart offshore-leaks-mcp
    log_message "INFO: Attempted service restart"
    exit 1
fi
EOF

chmod +x /home/offshore-leaks/health-check.sh

# Add to crontab for regular health checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/offshore-leaks/health-check.sh") | crontab -
```

## Monitoring and Logging

### 1. Log Management

```bash
# Configure logrotate for application logs
sudo cat > /etc/logrotate.d/offshore-leaks-mcp << EOF
/var/log/offshore-leaks-mcp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su offshore-leaks offshore-leaks
}
EOF
```

### 2. Monitoring with Prometheus (Optional)

```bash
# Create monitoring endpoints configuration
cat > /etc/offshore-leaks-mcp/monitoring.yaml << EOF
monitoring:
  enabled: true
  prometheus:
    enabled: true
    port: 9090
    metrics_path: "/metrics"
  health_check:
    enabled: true
    endpoint: "/health"
    interval: 30
EOF
```

### 3. Performance Monitoring

```bash
# Create performance monitoring script
cat > /home/offshore-leaks/monitor-performance.sh << 'EOF'
#!/bin/bash

# Performance monitoring for Offshore Leaks MCP Server
LOGFILE="/var/log/offshore-leaks-mcp/performance.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Get process info
PID=$(pgrep -f "offshore_leaks_mcp.mcp_server")

if [ -n "$PID" ]; then
    # CPU and Memory usage
    PS_OUTPUT=$(ps -p $PID -o pid,pcpu,pmem,vsz,rss --no-headers)

    # Database connections (if netstat available)
    DB_CONNECTIONS=$(netstat -an 2>/dev/null | grep ":7687" | grep ESTABLISHED | wc -l)

    echo "[$TIMESTAMP] PID:$PID CPU:$(echo $PS_OUTPUT | awk '{print $2}')% MEM:$(echo $PS_OUTPUT | awk '{print $3}')% VSZ:$(echo $PS_OUTPUT | awk '{print $4}') RSS:$(echo $PS_OUTPUT | awk '{print $5}') DB_CONN:$DB_CONNECTIONS" >> "$LOGFILE"
else
    echo "[$TIMESTAMP] ERROR: Process not found" >> "$LOGFILE"
fi
EOF

chmod +x /home/offshore-leaks/monitor-performance.sh

# Add to crontab for regular performance monitoring
(crontab -l 2>/dev/null; echo "*/10 * * * * /home/offshore-leaks/monitor-performance.sh") | crontab -
```

## Backup and Recovery

### 1. Configuration Backup

```bash
# Create backup script
cat > /home/offshore-leaks/backup-config.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/offshore-leaks-mcp"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration files
tar -czf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" \
    /etc/offshore-leaks-mcp/ \
    /home/offshore-leaks/offshoreleaks-data-packages/mcp/pyproject.toml \
    /etc/systemd/system/offshore-leaks-mcp.service

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "config_backup_*.tar.gz" -mtime +30 -delete

echo "Configuration backup completed: config_backup_$TIMESTAMP.tar.gz"
EOF

chmod +x /home/offshore-leaks/backup-config.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/offshore-leaks/backup-config.sh") | crontab -
```

### 2. Disaster Recovery

```bash
# Create disaster recovery script
cat > /home/offshore-leaks/disaster-recovery.sh << 'EOF'
#!/bin/bash

# Disaster recovery script for Offshore Leaks MCP Server
echo "Starting disaster recovery process..."

# Stop service
sudo systemctl stop offshore-leaks-mcp

# Backup current installation
BACKUP_DIR="/var/backups/offshore-leaks-mcp/disaster-recovery-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r /home/offshore-leaks/offshoreleaks-data-packages "$BACKUP_DIR/"

# Restore from latest config backup
LATEST_BACKUP=$(ls -t /var/backups/offshore-leaks-mcp/config_backup_*.tar.gz 2>/dev/null | head -n1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "Restoring from: $LATEST_BACKUP"
    tar -xzf "$LATEST_BACKUP" -C /
fi

# Restart service
sudo systemctl start offshore-leaks-mcp

echo "Disaster recovery completed. Check service status with: sudo systemctl status offshore-leaks-mcp"
EOF

chmod +x /home/offshore-leaks/disaster-recovery.sh
```

## Performance Optimization

### 1. Database Optimization

```bash
# Neo4j performance tuning recommendations
cat > /etc/offshore-leaks-mcp/neo4j-tuning.md << EOF
# Neo4j Performance Tuning for Offshore Leaks

## Memory Configuration
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=4g

## Connection Pool
dbms.connector.bolt.thread_pool_min_size=5
dbms.connector.bolt.thread_pool_max_size=20

## Query Performance
cypher.min_replan_interval=10s
cypher.statistics_divergence_threshold=0.5

## Indexing
# Ensure indexes exist on frequently queried fields:
# CREATE INDEX FOR (e:Entity) ON (e.name)
# CREATE INDEX FOR (e:Entity) ON (e.jurisdiction)
# CREATE INDEX FOR (o:Officer) ON (o.name)
EOF
```

### 2. Application Tuning

```bash
# Update production configuration for performance
cat >> /etc/offshore-leaks-mcp/production.yaml << EOF

performance:
  max_concurrent_queries: 20
  query_cache_size: 1000
  connection_pool_size: 10
  worker_threads: 4

  # Resilience tuning
  retry_delays: [1, 2, 4, 8, 16]  # seconds
  circuit_breaker_timeout: 60     # seconds
  health_check_timeout: 10        # seconds
EOF
```

## Deployment Checklist

### Pre-Deployment

- [ ] Neo4j database is running and accessible
- [ ] Database contains offshore leaks data
- [ ] System requirements are met
- [ ] Security configurations are in place
- [ ] Backup strategy is implemented

### Deployment

- [ ] Application installed in production environment
- [ ] Configuration files created and secured
- [ ] Environment variables set
- [ ] Service files created and enabled
- [ ] Monitoring scripts deployed
- [ ] Health checks configured

### Post-Deployment

- [ ] Service starts successfully
- [ ] Database connectivity verified
- [ ] MCP server responds to requests
- [ ] Logs are being written
- [ ] Monitoring is active
- [ ] Backup scripts are scheduled
- [ ] Performance metrics collected

### Testing

- [ ] Basic health check passes
- [ ] Search queries work correctly
- [ ] Export functionality works
- [ ] Error recovery mechanisms tested
- [ ] Circuit breakers function properly
- [ ] Load testing completed (if applicable)

## Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check logs
sudo journalctl -u offshore-leaks-mcp -f

# Check configuration
python -c "from offshore_leaks_mcp.config import load_config; print(load_config())"

# Test database connection
python -c "from offshore_leaks_mcp.database import Neo4jDatabase; from offshore_leaks_mcp.config import load_config; import asyncio; asyncio.run(Neo4jDatabase(load_config().neo4j).connect())"
```

**Database Connection Issues:**
```bash
# Test Neo4j connectivity
cypher-shell -a bolt://your-server:7687 -u neo4j -p your-password

# Check firewall
sudo ufw status
sudo netstat -tlnp | grep 7687
```

**Performance Issues:**
```bash
# Monitor resource usage
top -p $(pgrep -f offshore_leaks_mcp)
iostat -x 1

# Check database performance
# Monitor slow queries in Neo4j logs
```

**Memory Issues:**
```bash
# Increase memory limits in systemd service
echo "MemoryMax=4G" | sudo tee -a /etc/systemd/system/offshore-leaks-mcp.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart offshore-leaks-mcp
```

### Log Analysis

```bash
# View recent logs
sudo journalctl -u offshore-leaks-mcp --since "1 hour ago"

# Search for errors
sudo grep -i error /var/log/offshore-leaks-mcp/*.log

# Monitor real-time logs
sudo tail -f /var/log/offshore-leaks-mcp/server.log
```

## Maintenance

### Regular Tasks

**Daily:**
- Check service status
- Review error logs
- Monitor resource usage

**Weekly:**
- Review performance metrics
- Check backup integrity
- Update security patches

**Monthly:**
- Update dependencies
- Review and rotate logs
- Performance optimization review

### Update Procedure

```bash
# 1. Backup current installation
/home/offshore-leaks/backup-config.sh

# 2. Stop service
sudo systemctl stop offshore-leaks-mcp

# 3. Update code
cd /home/offshore-leaks/offshoreleaks-data-packages
git pull
cd mcp

# 4. Update dependencies
source venv-prod/bin/activate
pip install --upgrade -e ".[mcp]"

# 5. Test configuration
python -c "from offshore_leaks_mcp.mcp_server import MCPOffshoreLeaksServer; print('✅ Update successful')"

# 6. Start service
sudo systemctl start offshore-leaks-mcp

# 7. Verify health
sudo systemctl status offshore-leaks-mcp
```

## Security Considerations

### Access Control
- Use dedicated user account
- Implement API key authentication
- Restrict network access
- Regular security audits

### Data Protection
- Encrypt sensitive configuration
- Secure backup storage
- Monitor access patterns
- Implement audit logging

### Compliance
- Document data handling procedures
- Implement data retention policies
- Regular security assessments
- Compliance reporting

This deployment guide ensures a robust, secure, and maintainable production installation of the Offshore Leaks MCP Server with comprehensive monitoring, backup, and recovery capabilities.
