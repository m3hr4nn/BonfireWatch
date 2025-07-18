#!/usr/bin/env python3

import os
import time
import json
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import docker
import psutil
import platform
import subprocess
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'container-health-monitor-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
docker_client = None
container_engine = None
is_monitoring = True

def detect_container_engine():
    """Detect available container engine (Docker or Podman)"""
    # Check for Podman first
    try:
        result = subprocess.run(['podman', 'version', '--format', 'json'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return 'podman'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Check for Docker
    try:
        result = subprocess.run(['docker', 'version', '--format', 'json'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return 'docker'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None

def init_container_client():
    """Initialize container client with Docker/Podman compatibility"""
    global docker_client, container_engine
    
    # First detect which engine is available
    container_engine = detect_container_engine()
    
    if container_engine == 'docker':
        try:
            docker_client = docker.from_env()
            docker_client.ping()
            print("✓ Docker client initialized successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize Docker client: {e}")
    
    elif container_engine == 'podman':
        try:
            # Try to connect to Podman socket
            docker_client = docker.DockerClient(base_url='unix://run/podman/podman.sock')
            docker_client.ping()
            print("✓ Podman client initialized successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Podman socket, trying Docker API compatibility: {e}")
            try:
                # Fallback to Docker API compatibility
                docker_client = docker.from_env()
                docker_client.ping()
                print("✓ Podman (Docker API compatibility) initialized successfully")
                return True
            except Exception as e2:
                print(f"✗ Failed to initialize Podman client: {e2}")
    
    print("✗ No compatible container engine found (Docker or Podman)")
    docker_client = None
    container_engine = None
    return False

def get_system_info():
    """Get basic system information"""
    engine_info = "None"
    if container_engine:
        engine_info = container_engine.capitalize()
        if docker_client:
            try:
                version_info = docker_client.version()
                engine_version = version_info.get('Version', 'Unknown')
                engine_info = f"{engine_info} {engine_version}"
            except:
                pass
    
    return {
        'os': platform.system(),
        'os_version': platform.release(),
        'architecture': platform.machine(),
        'python_version': platform.python_version(),
        'hostname': platform.node(),
        'container_engine': engine_info,
        'timestamp': datetime.now().isoformat()
    }

def get_container_stats(container):
    """Get container statistics"""
    try:
        stats = container.stats(stream=False)
        
        # Calculate CPU usage
        cpu_stats = stats['cpu_stats']
        precpu_stats = stats['precpu_stats']
        
        cpu_usage = 0
        if 'cpu_usage' in cpu_stats and 'cpu_usage' in precpu_stats:
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            
            if system_delta > 0:
                cpu_usage = (cpu_delta / system_delta) * len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', [1])) * 100
        
        # Calculate memory usage
        memory_stats = stats['memory_stats']
        memory_usage = memory_stats.get('usage', 0)
        memory_limit = memory_stats.get('limit', 0)
        memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
        
        # Network I/O
        networks = stats.get('networks', {})
        rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values())
        tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values())
        
        return {
            'cpu_percent': round(cpu_usage, 2),
            'memory_usage': memory_usage,
            'memory_limit': memory_limit,
            'memory_percent': round(memory_percent, 2),
            'network_rx': rx_bytes,
            'network_tx': tx_bytes
        }
    except Exception as e:
        print(f"Error getting container stats: {e}")
        return None

def get_containers_info():
    """Get information about all containers"""
    if not docker_client:
        return []
    
    containers_info = []
    
    try:
        containers = docker_client.containers.list(all=True)
        
        for container in containers:
            container_info = {
                'id': container.short_id,
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created'],
                'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {}),
                'stats': None
            }
            
            # Get stats only for running containers
            if container.status == 'running':
                container_info['stats'] = get_container_stats(container)
            
            containers_info.append(container_info)
    
    except Exception as e:
        print(f"Error getting containers info: {e}")
    
    return containers_info

def get_host_stats():
    """Get host system statistics"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict(),
            'network': psutil.net_io_counters()._asdict(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error getting host stats: {e}")
        return None

def monitoring_loop():
    """Background monitoring loop"""
    while is_monitoring:
        try:
            data = {
                'containers': get_containers_info(),
                'host_stats': get_host_stats(),
                'timestamp': datetime.now().isoformat()
            }
            socketio.emit('update', data)
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(10)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'container_engine': container_engine,
        'client_connected': docker_client is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/containers')
def api_containers():
    """API endpoint for container information"""
    return jsonify(get_containers_info())

@app.route('/api/system')
def api_system():
    """API endpoint for system information"""
    return jsonify(get_system_info())

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('system_info', get_system_info())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("🐳 Container Health Monitor starting...")
    
    # Initialize container client
    if not init_container_client():
        print("⚠️  No container engine available - some features will be limited")
    else:
        print(f"✓ Using {container_engine} as container engine")
    
    # Start monitoring thread
    monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()
    
    print("🚀 Starting web server on port 8443...")
    socketio.run(app, host='0.0.0.0', port=8443, debug=False)