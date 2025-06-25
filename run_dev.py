#!/usr/bin/env python3
"""
Gotcha Guardian Payment Server Development Runner

This script provides various development utilities for running and managing
the payment server during development.
"""

import os
import sys
import subprocess
import signal
import time
import threading
from pathlib import Path
from typing import Optional, List


class DevServer:
    """Development server manager."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        
    def run_server(self, 
                   host: str = '127.0.0.1', 
                   port: int = 5000, 
                   debug: bool = True,
                   reload: bool = True,
                   threaded: bool = True) -> None:
        """Run the development server."""
        print(f"🚀 Starting Gotcha Guardian Payment Server")
        print(f"📍 URL: http://{host}:{port}")
        print(f"🔧 Debug: {debug}, Reload: {reload}, Threaded: {threaded}")
        print("=" * 60)
        
        # Set environment variables
        env = os.environ.copy()
        env.update({
            'FLASK_ENV': 'development' if debug else 'production',
            'FLASK_DEBUG': str(debug).lower(),
            'FLASK_RUN_HOST': host,
            'FLASK_RUN_PORT': str(port)
        })
        
        # Add src to Python path
        src_path = str(self.project_root / 'src')
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = src_path
        
        try:
            # Run the server
            cmd = [sys.executable, 'payment_server.py']
            
            if reload:
                cmd.extend(['--reload'])
            if threaded:
                cmd.extend(['--threaded'])
                
            self.process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.running = True
            
            # Start output monitoring thread
            output_thread = threading.Thread(target=self._monitor_output)
            output_thread.daemon = True
            output_thread.start()
            
            # Wait for process
            self.process.wait()
            
        except KeyboardInterrupt:
            print("\n⚠️  Shutting down server...")
            self.stop_server()
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            
    def _monitor_output(self) -> None:
        """Monitor server output."""
        if not self.process or not self.process.stdout:
            return
            
        for line in iter(self.process.stdout.readline, ''):
            if line:
                print(line.rstrip())
            if not self.running:
                break
                
    def stop_server(self) -> None:
        """Stop the development server."""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            print("✅ Server stopped")
            
    def run_tests(self, 
                  test_path: Optional[str] = None,
                  coverage: bool = False,
                  verbose: bool = False) -> bool:
        """Run tests."""
        print("🧪 Running tests...")
        
        cmd = [sys.executable, '-m', 'pytest']
        
        if test_path:
            cmd.append(test_path)
        else:
            cmd.append('tests/')
            
        if verbose:
            cmd.append('-v')
            
        if coverage:
            cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
            
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
            
    def lint_code(self) -> bool:
        """Run code linting."""
        print("🔍 Running code linting...")
        
        success = True
        
        # Run flake8
        try:
            print("\n📋 Running flake8...")
            result = subprocess.run(
                [sys.executable, '-m', 'flake8', 'src/', 'tests/'],
                cwd=self.project_root
            )
            if result.returncode != 0:
                success = False
        except FileNotFoundError:
            print("⚠️  flake8 not installed")
            
        # Run black (check only)
        try:
            print("\n🎨 Running black (check)...")
            result = subprocess.run(
                [sys.executable, '-m', 'black', '--check', 'src/', 'tests/'],
                cwd=self.project_root
            )
            if result.returncode != 0:
                success = False
        except FileNotFoundError:
            print("⚠️  black not installed")
            
        # Run isort (check only)
        try:
            print("\n📦 Running isort (check)...")
            result = subprocess.run(
                [sys.executable, '-m', 'isort', '--check-only', 'src/', 'tests/'],
                cwd=self.project_root
            )
            if result.returncode != 0:
                success = False
        except FileNotFoundError:
            print("⚠️  isort not installed")
            
        return success
        
    def format_code(self) -> None:
        """Format code using black and isort."""
        print("🎨 Formatting code...")
        
        # Run black
        try:
            print("\n🎨 Running black...")
            subprocess.run(
                [sys.executable, '-m', 'black', 'src/', 'tests/'],
                cwd=self.project_root
            )
        except FileNotFoundError:
            print("⚠️  black not installed")
            
        # Run isort
        try:
            print("\n📦 Running isort...")
            subprocess.run(
                [sys.executable, '-m', 'isort', 'src/', 'tests/'],
                cwd=self.project_root
            )
        except FileNotFoundError:
            print("⚠️  isort not installed")
            
    def check_dependencies(self) -> bool:
        """Check if all dependencies are installed."""
        print("📦 Checking dependencies...")
        
        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            return False
            
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'check'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ All dependencies are satisfied")
                return True
            else:
                print(f"❌ Dependency issues found:\n{result.stdout}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to check dependencies: {e}")
            return False
            
    def install_dev_dependencies(self) -> bool:
        """Install development dependencies."""
        print("📦 Installing development dependencies...")
        
        dev_packages = [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'flake8>=5.0.0',
            'black>=22.0.0',
            'isort>=5.10.0',
            'mypy>=0.991'
        ]
        
        try:
            for package in dev_packages:
                print(f"  Installing {package}...")
                subprocess.check_call(
                    [sys.executable, '-m', 'pip', 'install', package],
                    stdout=subprocess.DEVNULL
                )
            print("✅ Development dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install development dependencies: {e}")
            return False
            
    def create_migration(self, message: str) -> None:
        """Create a database migration."""
        print(f"🗄️  Creating migration: {message}")
        
        # This would integrate with your migration system
        # For now, just create a timestamp-based migration file
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        migration_name = f"{timestamp}_{message.lower().replace(' ', '_')}"
        
        migrations_dir = self.project_root / 'migrations'
        migrations_dir.mkdir(exist_ok=True)
        
        migration_file = migrations_dir / f"{migration_name}.py"
        
        migration_template = f'''"""
Migration: {message}
Created: {datetime.datetime.now().isoformat()}
"""

def upgrade():
    """Apply migration."""
    pass

def downgrade():
    """Rollback migration."""
    pass
'''
        
        with open(migration_file, 'w') as f:
            f.write(migration_template)
            
        print(f"✅ Migration created: {migration_file}")
        
    def backup_database(self) -> None:
        """Create a database backup."""
        print("💾 Creating database backup...")
        
        import datetime
        import shutil
        
        db_path = self.project_root / 'data' / 'payment_server.db'
        if not db_path.exists():
            print("⚠️  Database file not found")
            return
            
        backup_dir = self.project_root / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"payment_server_backup_{timestamp}.db"
        
        try:
            shutil.copy2(db_path, backup_file)
            print(f"✅ Database backed up to: {backup_file}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            
    def show_logs(self, log_type: str = 'app', lines: int = 50) -> None:
        """Show recent log entries."""
        log_files = {
            'app': 'logs/app.log',
            'error': 'logs/error.log',
            'security': 'logs/security.log',
            'payment': 'logs/payment.log'
        }
        
        if log_type not in log_files:
            print(f"❌ Unknown log type: {log_type}")
            print(f"Available types: {', '.join(log_files.keys())}")
            return
            
        log_file = self.project_root / log_files[log_type]
        if not log_file.exists():
            print(f"⚠️  Log file not found: {log_file}")
            return
            
        print(f"📋 Last {lines} lines from {log_type} log:")
        print("=" * 60)
        
        try:
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
                for line in log_lines[-lines:]:
                    print(line.rstrip())
        except Exception as e:
            print(f"❌ Failed to read log file: {e}")


def main():
    """Main development runner function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gotcha Guardian Payment Server Development Tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Run development server')
    server_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    server_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    server_parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    server_parser.add_argument('--no-reload', action='store_true', help='Disable auto-reload')
    server_parser.add_argument('--no-threaded', action='store_true', help='Disable threading')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('path', nargs='?', help='Specific test path')
    test_parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    test_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # Lint command
    lint_parser = subparsers.add_parser('lint', help='Run code linting')
    
    # Format command
    format_parser = subparsers.add_parser('format', help='Format code')
    
    # Dependencies command
    deps_parser = subparsers.add_parser('deps', help='Dependency management')
    deps_parser.add_argument('action', choices=['check', 'install-dev'], help='Dependency action')
    
    # Migration command
    migration_parser = subparsers.add_parser('migration', help='Create database migration')
    migration_parser.add_argument('message', help='Migration message')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup database')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show logs')
    logs_parser.add_argument('type', nargs='?', default='app', 
                           choices=['app', 'error', 'security', 'payment'],
                           help='Log type to show')
    logs_parser.add_argument('--lines', type=int, default=50, help='Number of lines to show')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    dev_server = DevServer()
    
    try:
        if args.command == 'server':
            dev_server.run_server(
                host=args.host,
                port=args.port,
                debug=not args.no_debug,
                reload=not args.no_reload,
                threaded=not args.no_threaded
            )
        elif args.command == 'test':
            success = dev_server.run_tests(
                test_path=args.path,
                coverage=args.coverage,
                verbose=args.verbose
            )
            sys.exit(0 if success else 1)
        elif args.command == 'lint':
            success = dev_server.lint_code()
            sys.exit(0 if success else 1)
        elif args.command == 'format':
            dev_server.format_code()
        elif args.command == 'deps':
            if args.action == 'check':
                success = dev_server.check_dependencies()
                sys.exit(0 if success else 1)
            elif args.action == 'install-dev':
                success = dev_server.install_dev_dependencies()
                sys.exit(0 if success else 1)
        elif args.command == 'migration':
            dev_server.create_migration(args.message)
        elif args.command == 'backup':
            dev_server.backup_database()
        elif args.command == 'logs':
            dev_server.show_logs(args.type, args.lines)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()