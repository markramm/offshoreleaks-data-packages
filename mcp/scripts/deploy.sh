#!/bin/bash

# Offshore Leaks MCP Server Deployment Script
# This script automates the deployment process for production environments

set -e  # Exit on any error

# Configuration
APP_USER="offshore-leaks"
APP_HOME="/home/$APP_USER"
APP_DIR="$APP_HOME/offshoreleaks-data-packages/mcp"
CONFIG_DIR="/etc/offshore-leaks-mcp"
LOG_DIR="/var/log/offshore-leaks-mcp"
DATA_DIR="/var/lib/offshore-leaks-mcp"
VENV_NAME="venv-prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a regular user with sudo privileges."
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."

    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        error "Cannot determine OS version"
    fi

    # Check Python version
    if ! python3.11 --version >/dev/null 2>&1; then
        if ! python3.10 --version >/dev/null 2>&1; then
            error "Python 3.10+ is required. Please install Python 3.10 or newer."
        else
            PYTHON_CMD="python3.10"
        fi
    else
        PYTHON_CMD="python3.11"
    fi

    success "System requirements check passed"
}

# Create application user
create_user() {
    log "Creating application user..."

    if id "$APP_USER" >/dev/null 2>&1; then
        warning "User $APP_USER already exists"
    else
        sudo useradd -m -s /bin/bash "$APP_USER"
        success "Created user $APP_USER"
    fi
}

# Setup directories
setup_directories() {
    log "Setting up directories..."

    # Create system directories
    sudo mkdir -p "$CONFIG_DIR" "$LOG_DIR" "$DATA_DIR/exports"

    # Set ownership
    sudo chown -R "$APP_USER:$APP_USER" "$LOG_DIR" "$DATA_DIR"
    sudo chown "$APP_USER:$APP_USER" "$CONFIG_DIR"

    # Set permissions
    sudo chmod 750 "$LOG_DIR" "$DATA_DIR"
    sudo chmod 755 "$CONFIG_DIR"

    success "Directories created and configured"
}

# Install application
install_application() {
    log "Installing application..."

    # Switch to app user for installation
    sudo -u "$APP_USER" bash << EOF
set -e

# Clone or update repository
if [ -d "$APP_DIR" ]; then
    echo "Updating existing installation..."
    cd "$APP_DIR"
    git pull
else
    echo "Cloning repository..."
    cd "$APP_HOME"
    git clone https://github.com/markramm/offshoreleaks-data-packages.git
fi

cd "$APP_DIR"

# Create virtual environment
if [ ! -d "$VENV_NAME" ]; then
    $PYTHON_CMD -m venv "$VENV_NAME"
fi

# Activate and install
source "$VENV_NAME/bin/activate"
pip install --upgrade pip
pip install -e ".[mcp]"

# Verify installation
python -c "from offshore_leaks_mcp.mcp_server import MCPOffshoreLeaksServer; print('Installation verified')"
EOF

    success "Application installed successfully"
}

# Generate configuration
generate_config() {
    log "Generating configuration files..."

    # Generate environment file template
    sudo tee "$CONFIG_DIR/.env.template" > /dev/null << EOF
# Offshore Leaks MCP Server Environment Configuration
# Copy this file to .env and update with your values

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password-here
NEO4J_DATABASE=offshoreleaks

# Security Configuration
DEBUG=false
ENVIRONMENT=production
API_KEY=your-secure-api-key-here

# Optional: Encryption key for sensitive data
# ENCRYPTION_KEY=your-encryption-key-here
EOF

    # Generate main configuration
    sudo tee "$CONFIG_DIR/production.yaml" > /dev/null << EOF
# Offshore Leaks MCP Server Production Configuration

server:
  version: "0.1.0"
  environment: "production"
  log_level: "INFO"
  query_timeout: 30.0
  max_concurrent_queries: 10

neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "\${NEO4J_PASSWORD}"
  database: "offshoreleaks"
  connection_timeout: 10.0
  max_connection_pool_size: 20
  max_connection_lifetime: 3600

resilience:
  retry_attempts: 5
  circuit_breaker_threshold: 3
  health_check_interval: 30

logging:
  level: "INFO"
  format: "json"
  file: "$LOG_DIR/server.log"
  max_size: "100MB"
  backup_count: 10
EOF

    # Set permissions
    sudo chown "$APP_USER:$APP_USER" "$CONFIG_DIR/production.yaml"
    sudo chown "$APP_USER:$APP_USER" "$CONFIG_DIR/.env.template"
    sudo chmod 644 "$CONFIG_DIR/production.yaml"
    sudo chmod 600 "$CONFIG_DIR/.env.template"

    success "Configuration files generated"
    warning "Please copy $CONFIG_DIR/.env.template to $CONFIG_DIR/.env and update with your values"
}

# Create systemd service
create_service() {
    log "Creating systemd service..."

    sudo tee /etc/systemd/system/offshore-leaks-mcp.service > /dev/null << EOF
[Unit]
Description=Offshore Leaks MCP Server
After=network.target neo4j.service
Wants=neo4j.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/$VENV_NAME/bin
EnvironmentFile=$CONFIG_DIR/.env
ExecStart=$APP_DIR/$VENV_NAME/bin/python -m offshore_leaks_mcp.mcp_server
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
ReadWritePaths=$LOG_DIR $DATA_DIR

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable offshore-leaks-mcp

    success "Systemd service created and enabled"
}

# Setup logrotate
setup_logrotate() {
    log "Setting up log rotation..."

    sudo tee /etc/logrotate.d/offshore-leaks-mcp > /dev/null << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su $APP_USER $APP_USER
}
EOF

    success "Log rotation configured"
}

# Create monitoring scripts
create_monitoring() {
    log "Creating monitoring scripts..."

    # Health check script
    sudo -u "$APP_USER" tee "$APP_HOME/health-check.sh" > /dev/null << EOF
#!/bin/bash

# Health check script for Offshore Leaks MCP Server
LOG_FILE="$LOG_DIR/health-check.log"
TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')

# Function to log messages
log_message() {
    echo "[\$TIMESTAMP] \$1" >> "\$LOG_FILE"
}

# Check if service is running
if systemctl is-active --quiet offshore-leaks-mcp; then
    log_message "INFO: Service is running"

    # Test if process exists
    if pgrep -f "offshore_leaks_mcp.mcp_server" > /dev/null; then
        log_message "INFO: MCP server process is healthy"
        exit 0
    else
        log_message "ERROR: MCP server process not found"
        exit 1
    fi
else
    log_message "ERROR: Service is not running"
    exit 1
fi
EOF

    # Performance monitoring script
    sudo -u "$APP_USER" tee "$APP_HOME/monitor-performance.sh" > /dev/null << EOF
#!/bin/bash

# Performance monitoring for Offshore Leaks MCP Server
LOGFILE="$LOG_DIR/performance.log"
TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')

# Get process info
PID=\$(pgrep -f "offshore_leaks_mcp.mcp_server")

if [ -n "\$PID" ]; then
    # CPU and Memory usage
    PS_OUTPUT=\$(ps -p \$PID -o pid,pcpu,pmem,vsz,rss --no-headers)

    # Database connections (if netstat available)
    DB_CONNECTIONS=\$(ss -an 2>/dev/null | grep ":7687" | grep ESTAB | wc -l)

    echo "[\$TIMESTAMP] PID:\$PID CPU:\$(echo \$PS_OUTPUT | awk '{print \$2}')% MEM:\$(echo \$PS_OUTPUT | awk '{print \$3}')% VSZ:\$(echo \$PS_OUTPUT | awk '{print \$4}') RSS:\$(echo \$PS_OUTPUT | awk '{print \$5}') DB_CONN:\$DB_CONNECTIONS" >> "\$LOGFILE"
else
    echo "[\$TIMESTAMP] ERROR: Process not found" >> "\$LOGFILE"
fi
EOF

    # Make scripts executable
    sudo chmod +x "$APP_HOME/health-check.sh"
    sudo chmod +x "$APP_HOME/monitor-performance.sh"

    success "Monitoring scripts created"
}

# Create backup scripts
create_backup() {
    log "Creating backup scripts..."

    sudo -u "$APP_USER" tee "$APP_HOME/backup-config.sh" > /dev/null << EOF
#!/bin/bash

BACKUP_DIR="/var/backups/offshore-leaks-mcp"
TIMESTAMP=\$(date '+%Y%m%d_%H%M%S')

# Create backup directory
sudo mkdir -p "\$BACKUP_DIR"

# Backup configuration files
sudo tar -czf "\$BACKUP_DIR/config_backup_\$TIMESTAMP.tar.gz" \\
    "$CONFIG_DIR/" \\
    "$APP_DIR/pyproject.toml" \\
    /etc/systemd/system/offshore-leaks-mcp.service

# Keep only last 30 days of backups
sudo find "\$BACKUP_DIR" -name "config_backup_*.tar.gz" -mtime +30 -delete

echo "Configuration backup completed: config_backup_\$TIMESTAMP.tar.gz"
EOF

    sudo chmod +x "$APP_HOME/backup-config.sh"

    success "Backup scripts created"
}

# Main deployment function
main() {
    log "Starting Offshore Leaks MCP Server deployment..."

    check_root
    check_requirements
    create_user
    setup_directories
    install_application
    generate_config
    create_service
    setup_logrotate
    create_monitoring
    create_backup

    success "Deployment completed successfully!"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}🎉 Offshore Leaks MCP Server Deployment Complete!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Configure your environment variables:"
    echo "   sudo cp $CONFIG_DIR/.env.template $CONFIG_DIR/.env"
    echo "   sudo nano $CONFIG_DIR/.env"
    echo ""
    echo "2. Update production configuration if needed:"
    echo "   sudo nano $CONFIG_DIR/production.yaml"
    echo ""
    echo "3. Start the service:"
    echo "   sudo systemctl start offshore-leaks-mcp"
    echo ""
    echo "4. Check service status:"
    echo "   sudo systemctl status offshore-leaks-mcp"
    echo ""
    echo "5. View logs:"
    echo "   sudo journalctl -u offshore-leaks-mcp -f"
    echo ""
    echo -e "${BLUE}Configuration files location:${NC} $CONFIG_DIR"
    echo -e "${BLUE}Log files location:${NC} $LOG_DIR"
    echo -e "${BLUE}Application location:${NC} $APP_DIR"
    echo ""
    echo -e "${GREEN}For more details, see: docs/PRODUCTION_DEPLOYMENT.md${NC}"
    echo ""
}

# Run deployment
main "$@"
