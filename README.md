# 🐳 Container Health Monitor

A lightweight, real-time dashboard for monitoring Docker and Podman containers' health, resource usage, and system metrics. Built with Flask, Socket.IO, and designed to run on both Linux and Windows.

## Features

- **Container Engine Support**: Works with both Docker and Podman
- **Real-time Monitoring**: Live updates every 5 seconds
- **Container Metrics**: CPU, memory, network I/O for all containers
- **Host System Stats**: CPU, memory, disk usage of the host machine
- **Cross-Platform**: Compatible with Linux and Windows
- **Responsive UI**: Works on desktop and mobile devices
- **Health Checks**: Built-in health endpoint for monitoring
- **Lightweight**: Minimal resource footprint
- **Auto-Detection**: Automatically detects available container engine

## Quick Start

### Docker

```bash
# Clone and run with Docker
git clone https://github.com/m3hr4nn/BonfireWatch.git && cd container-health-monitor && docker-compose up -d

# Or build and run directly
docker build -t container-health-monitor . && docker run -d -p 8443:8443 -v /var/run/docker.sock:/var/run/docker.sock:ro container-health-monitor
```

### Podman

```bash
# Make sure Podman socket is enabled
systemctl --user enable --now podman.socket

# Clone and run with Podman
git clone https://github.com/m3hr4nn/BonfireWatch.git && cd container-health-monitor && podman-compose up -d

# Or build and run directly
podman build -t container-health-monitor . && podman run -d -p 8443:8443 -v /run/podman/podman.sock:/var/run/docker.sock:ro container-health-monitor
```

### Windows Setup

```powershell
# Windows with Docker Desktop
docker build -t container-health-monitor .
docker run -d -p 8443:8443 -v //var/run/docker.sock:/var/run/docker.sock:ro container-health-monitor

# Windows with Podman
podman build -t container-health-monitor .
podman run -d -p 8443:8443 -v //run/podman/podman.sock:/var/run/docker.sock:ro container-health-monitor
```

## Access Dashboard

Open your browser and go to: **http://localhost:8443**

## API Endpoints

- `GET /` - Main dashboard
- `GET /health` - Health check endpoint
- `GET /api/containers` - JSON API for container information
- `GET /api/system` - JSON API for system information

## Container Engine Detection

The application automatically detects which container engine is available:

1. **Podman Detection**: Checks for `podman` command and socket
2. **Docker Detection**: Falls back to Docker if Podman is not available
3. **API Compatibility**: Uses Docker API with both engines

### Podman Setup Requirements

For Podman, ensure the socket is enabled:

```bash
# Enable Podman socket (rootless)
systemctl --user enable --now podman.socket

# Or for system-wide (rootful)
sudo systemctl enable --now podman.socket

# Verify socket is running
systemctl --user status podman.socket
```

### Docker vs Podman Socket Locations

- **Docker**: `/var/run/docker.sock`
- **Podman (rootless)**: `/run/user/$UID/podman/podman.sock`
- **Podman (rootful)**: `/run/podman/podman.sock`

## Requirements

- Docker OR Podman installed and running
- Container socket access (Docker or Podman socket)
- Port 8443 available

## Architecture

```
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # One-command deployment
├── requirements.txt        # Python dependencies
├── app.py                  # Main Flask application
└── templates/
    └── index.html          # Dashboard frontend
```

## Features in Detail

### Container Monitoring
- Container status (running, stopped, paused)
- Real-time CPU and memory usage
- Network I/O statistics
- Container metadata (image, ID, ports)

### Host System Monitoring  
- CPU usage percentage
- Memory usage and availability
- Disk usage statistics
- Network statistics

### Real-time Updates
- WebSocket connection for live updates
- Connection status indicator
- Automatic reconnection on disconnect

## Security

- Runs as non-root user inside container
- Read-only access to Docker socket
- No external dependencies beyond Python packages
- Health checks for container monitoring

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Create templates directory
mkdir -p templates

# Run locally (requires Docker daemon)
python app.py
```

### Environment Variables
- `FLASK_ENV`: Set to 'development' for debug mode
- `PYTHONUNBUFFERED`: Set to 1 for real-time logging

## Troubleshooting

### Common Issues

1. **Docker socket permission denied**
   ```bash
   # Linux: Add user to docker group
   sudo usermod -aG docker $USER
   ```

2. **Port 8443 already in use**
   ```bash
   # Change port in docker-compose.yml or use different port
   docker run -p 8080:8443 ...
   ```

3. **Container not showing stats**
   - Ensure container engine daemon is running
   - Check container socket permissions
   - For Podman: Enable socket with `systemctl --user enable --now podman.socket`
   - Verify container has access to the appropriate socket

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Verify Docker daemon is running and accessible
