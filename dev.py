#!/usr/bin/env python3
"""
Django Missive - Development Tool
Cross-platform script for building, testing, and managing the project.

Usage:
    python dev.py <command>
    ./dev.py <command>  (on Linux/macOS with chmod +x)
    
Examples:
    python dev.py install-dev
    python dev.py test
    python dev.py build
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Colors for terminal output
BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
NC = '\033[0m'  # No Color

# Disable colors on Windows if not supported
if platform.system() == 'Windows' and not os.environ.get('ANSICON'):
    BLUE = GREEN = RED = YELLOW = NC = ''

# Project paths
PROJECT_ROOT = Path(__file__).parent
VENV_DIR = PROJECT_ROOT / 'venv'
VENV_BIN = VENV_DIR / ('Scripts' if platform.system() == 'Windows' else 'bin')
PYTHON = VENV_BIN / ('python.exe' if platform.system() == 'Windows' else 'python')
PIP = VENV_BIN / ('pip.exe' if platform.system() == 'Windows' else 'pip')


def print_info(message):
    """Print info message in blue"""
    print(f"{BLUE}{message}{NC}")


def print_success(message):
    """Print success message in green"""
    print(f"{GREEN}{message}{NC}")


def print_error(message):
    """Print error message in red"""
    print(f"{RED}{message}{NC}", file=sys.stderr)


def print_warning(message):
    """Print warning message in yellow"""
    print(f"{YELLOW}{message}{NC}")


def run_command(cmd, check=True, **kwargs):
    """Run a command and handle errors"""
    print_info(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(cmd, check=check, **kwargs)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd}")
        return False


def venv_exists():
    """Check if virtual environment exists"""
    return VENV_DIR.exists() and PYTHON.exists()


def task_help():
    """Show available commands"""
    print(f"{BLUE}Django Missive - Available Commands{NC}\n")
    
    print(f"{GREEN}Development:{NC}")
    print("  venv              Create virtual environment")
    print("  install           Install package in production mode")
    print("  install-dev       Install package in development mode")
    print("")
    
    print(f"{GREEN}Django Dev Server:{NC}")
    print("  migrate           Run Django migrations")
    print("  makemigrations    Create new Django migrations")
    print("  runserver         Start Django development server (admin:admin)")
    print("  shell             Open Django shell")
    print("  createsuperuser   Create Django superuser")
    print("")
    
    print(f"{GREEN}Testing:{NC}")
    print("  test              Run tests with pytest")
    print("  test-verbose      Run tests with verbose output")
    print("  coverage          Run tests with coverage report")
    print("")
    
    print(f"{GREEN}Code Quality:{NC}")
    print("  lint              Run flake8 and mypy linters")
    print("  format            Format code with black and isort")
    print("  check             Run all checks (lint + format check)")
    print("  cleanup           Detect unused code, imports, and redundancies")
    print("  fix-imports       Auto-remove unused imports with autoflake")
    print("  complexity        Analyze code complexity with radon")
    print("")
    
    print(f"{GREEN}Security:{NC}")
    print("  security          Run security audit (bandit, safety, pip-audit)")
    print("")
    
    print(f"{GREEN}Building:{NC}")
    print("  clean             Remove all build, test, and Python artifacts")
    print("  clean-build       Remove build artifacts")
    print("  clean-pyc         Remove Python file artifacts")
    print("  clean-test        Remove test artifacts")
    print("  build             Build source and wheel distributions")
    print("  dist              Alias for build")
    print("")
    
    print(f"{GREEN}Publishing:{NC}")
    print("  upload-test       Upload package to TestPyPI")
    print("  upload            Upload package to PyPI")
    print("  release           Clean, build, and upload to PyPI")
    print("")
    
    print(f"{GREEN}Utilities:{NC}")
    print("  show-version      Show current package version")
    print("  requirements      Generate requirements.txt")
    print("  venv-clean        Remove and recreate virtual environment")
    print("")
    
    print(f"Usage: python dev.py <command>")


def task_venv():
    """Create virtual environment"""
    if venv_exists():
        print_warning("Virtual environment already exists")
        return True
    
    print_info("Creating virtual environment...")
    # Use python3 directly instead of sys.executable (which may be Cursor)
    python_cmd = 'python3' if platform.system() != 'Windows' else 'python'
    if not run_command([python_cmd, '-m', 'venv', str(VENV_DIR)]):
        return False
    
    print_success(f"Virtual environment created at {VENV_DIR}")
    if platform.system() == 'Windows':
        print_info(f"Activate it with: {VENV_DIR}\\Scripts\\activate")
    else:
        print_info(f"Activate it with: source {VENV_DIR}/bin/activate")
    return True


def task_install():
    """Install package in production mode"""
    if not venv_exists() and not task_venv():
        return False
    
    print_info("Installing package...")
    commands = [
        [str(PIP), 'install', '--upgrade', 'pip', 'setuptools', 'wheel'],
        [str(PIP), 'install', '.']
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            return False
    
    print_success("Installation complete!")
    return True


def task_install_dev():
    """Install package in development mode"""
    if not venv_exists() and not task_venv():
        return False
    
    print_info("Installing package in development mode...")
    commands = [
        [str(PIP), 'install', '--upgrade', 'pip', 'setuptools', 'wheel'],
        [str(PIP), 'install', '-e', '.[dev]']
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            return False
    
    print_success("Development installation complete!")
    return True


def task_clean_build():
    """Remove build artifacts"""
    print_info("Cleaning build artifacts...")
    dirs_to_remove = ['build', 'dist', '.eggs']
    
    for dir_name in dirs_to_remove:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed {dir_name}/")
    
    # Remove *.egg-info directories
    for egg_info in PROJECT_ROOT.glob('**/*.egg-info'):
        shutil.rmtree(egg_info)
        print(f"  Removed {egg_info.name}")
    
    # Remove *.egg files
    for egg in PROJECT_ROOT.glob('**/*.egg'):
        egg.unlink()
        print(f"  Removed {egg.name}")
    
    return True


def task_clean_pyc():
    """Remove Python file artifacts"""
    print_info("Cleaning Python file artifacts...")
    
    # Remove __pycache__ directories
    for pycache in PROJECT_ROOT.glob('**/__pycache__'):
        shutil.rmtree(pycache)
        print(f"  Removed {pycache}")
    
    # Remove .pyc, .pyo files
    for pattern in ['**/*.pyc', '**/*.pyo', '**/*~']:
        for file in PROJECT_ROOT.glob(pattern):
            file.unlink()
            print(f"  Removed {file}")
    
    return True


def task_clean_test():
    """Remove test artifacts"""
    print_info("Cleaning test artifacts...")
    artifacts = ['.pytest_cache', '.coverage', 'htmlcov', '.mypy_cache', '.tox', 'coverage.xml']
    
    removed_count = 0
    for artifact in artifacts:
        artifact_path = PROJECT_ROOT / artifact
        if artifact_path.exists():
            if artifact_path.is_dir():
                shutil.rmtree(artifact_path)
            else:
                artifact_path.unlink()
            print(f"  ✓ Removed {artifact}")
            removed_count += 1
    
    if removed_count == 0:
        print("  Nothing to clean")
    else:
        print_success(f"Cleaned {removed_count} artifact(s)")
    
    return True


def task_clean():
    """Remove all build, test, and Python artifacts"""
    task_clean_build()
    task_clean_pyc()
    task_clean_test()
    print_success("All clean!")
    return True


def task_test():
    """Run tests with pytest"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Running tests...")
    pytest = VENV_BIN / ('pytest.exe' if platform.system() == 'Windows' else 'pytest')
    
    if run_command([str(pytest)]):
        print_success("Tests complete!")
        return True
    return False


def task_test_verbose():
    """Run tests with verbose output"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Running tests (verbose)...")
    pytest = VENV_BIN / ('pytest.exe' if platform.system() == 'Windows' else 'pytest')
    
    if run_command([str(pytest), '-vv']):
        print_success("Tests complete!")
        return True
    return False


def task_coverage():
    """Run tests with coverage report"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Running tests with coverage...")
    pytest = VENV_BIN / ('pytest.exe' if platform.system() == 'Windows' else 'pytest')
    
    if run_command([str(pytest), '--cov=missive', '--cov-report=html', '--cov-report=term']):
        print_success("Coverage report generated in htmlcov/index.html")
        return True
    return False


def task_lint():
    """Run linters"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Running linters...")
    flake8 = VENV_BIN / ('flake8.exe' if platform.system() == 'Windows' else 'flake8')
    mypy = VENV_BIN / ('mypy.exe' if platform.system() == 'Windows' else 'mypy')
    
    success = True
    if not run_command([str(flake8), 'missive', 'tests']):
        success = False
    
    if not run_command([str(mypy), 'missive']):
        success = False
    
    if success:
        print_success("Linting complete!")
    return success


def task_format():
    """Format code with black and isort"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Formatting code...")
    black = VENV_BIN / ('black.exe' if platform.system() == 'Windows' else 'black')
    isort = VENV_BIN / ('isort.exe' if platform.system() == 'Windows' else 'isort')
    
    success = True
    if not run_command([str(black), 'missive', 'tests']):
        success = False
    
    if not run_command([str(isort), 'missive', 'tests']):
        success = False
    
    if success:
        print_success("Code formatted!")
    return success


def task_check():
    """Run all checks"""
    if not task_lint():
        return False
    
    print_info("Checking code format...")
    black = VENV_BIN / ('black.exe' if platform.system() == 'Windows' else 'black')
    isort = VENV_BIN / ('isort.exe' if platform.system() == 'Windows' else 'isort')
    
    success = True
    if not run_command([str(black), '--check', 'missive', 'tests']):
        success = False
    
    if not run_command([str(isort), '--check-only', 'missive', 'tests']):
        success = False
    
    if success:
        print_success("All checks passed!")
    return success


def task_cleanup():
    """Detect unused code, imports, and redundancies"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("=" * 70)
    print_info("CODE CLEANUP ANALYSIS - Django Missive")
    print_info("=" * 70)
    
    vulture = VENV_BIN / ('vulture.exe' if platform.system() == 'Windows' else 'vulture')
    autoflake = VENV_BIN / ('autoflake.exe' if platform.system() == 'Windows' else 'autoflake')
    pylint = VENV_BIN / ('pylint.exe' if platform.system() == 'Windows' else 'pylint')
    
    results = {
        'vulture': False,
        'autoflake': False,
        'pylint': False,
    }
    
    # 1. Vulture - Dead code detection
    print("\n" + "=" * 70)
    print_info("1/3 - Running Vulture (Dead Code Detection)")
    print_info("=" * 70)
    
    # Vulture retourne 0 si pas de dead code, 1 sinon
    result = run_command([str(vulture), 'missive/', '--min-confidence', '80'], check=False)
    if result:
        print_success("✓ Vulture: No dead code found")
        results['vulture'] = True
    else:
        print_warning("⚠ Vulture: Potential dead code detected (review above)")
    
    # 2. Autoflake - Unused imports check
    print("\n" + "=" * 70)
    print_info("2/3 - Running Autoflake (Unused Imports Check)")
    print_info("=" * 70)
    
    # Check mode only (no modifications)
    if run_command([str(autoflake), '--check', '--recursive', 
                   '--remove-all-unused-imports', 
                   '--remove-unused-variables', 
                   'missive/'], check=False):
        print_success("✓ Autoflake: No unused imports or variables")
        results['autoflake'] = True
    else:
        print_warning("⚠ Autoflake: Unused imports/variables found (run 'fix-imports' to fix)")
    
    # 3. Pylint - Code quality and redundancies
    print("\n" + "=" * 70)
    print_info("3/3 - Running Pylint (Code Quality & Redundancies)")
    print_info("=" * 70)
    
    # Pylint avec score minimum de 8/10
    if run_command([str(pylint), 'missive/', '--fail-under=8.0', 
                   '--disable=C0111,C0103,R0903'], check=False):
        print_success("✓ Pylint: Code quality score >= 8.0/10")
        results['pylint'] = True
    else:
        print_warning("⚠ Pylint: Code quality issues found (review above)")
    
    # Summary
    print("\n" + "=" * 70)
    print_info("CODE CLEANUP SUMMARY")
    print_info("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for tool, success in results.items():
        status = f"{GREEN}✓ PASS{NC}" if success else f"{RED}✗ FAIL{NC}"
        print(f"  {tool.upper():15} {status}")
    
    print("\n" + "-" * 70)
    score = int((passed / total) * 100)
    
    if score == 100:
        print_success(f"CLEANUP SCORE: {score}/100 - EXCELLENT!")
    elif score >= 66:
        print_warning(f"CLEANUP SCORE: {score}/100 - GOOD")
    else:
        print_error(f"CLEANUP SCORE: {score}/100 - NEEDS ATTENTION")
    
    print("-" * 70)
    
    return score == 100


def task_fix_imports():
    """Auto-remove unused imports and variables with autoflake"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Fixing unused imports and variables...")
    autoflake = VENV_BIN / ('autoflake.exe' if platform.system() == 'Windows' else 'autoflake')
    
    # Apply fixes in-place
    if run_command([
        str(autoflake),
        '--in-place',
        '--recursive',
        '--remove-all-unused-imports',
        '--remove-unused-variables',
        '--remove-duplicate-keys',
        'missive/',
        'tests/'
    ]):
        print_success("✓ Unused imports and variables removed!")
        return True
    else:
        print_error("✗ Failed to fix imports")
        return False


def task_complexity():
    """Analyze code complexity with radon"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("=" * 70)
    print_info("CODE COMPLEXITY ANALYSIS - Django Missive")
    print_info("=" * 70)
    
    radon = VENV_BIN / ('radon.exe' if platform.system() == 'Windows' else 'radon')
    
    # Cyclomatic Complexity
    print("\n" + "=" * 70)
    print_info("Cyclomatic Complexity (CC)")
    print_info("=" * 70)
    print_info("A = simple (1-5), B = moderate (6-10), C = complex (11-20)")
    print_info("D = very complex (21-50), E/F = extremely complex (>50)")
    print("")
    
    run_command([str(radon), 'cc', 'missive/', '-s', '-a'], check=False)
    
    # Maintainability Index
    print("\n" + "=" * 70)
    print_info("Maintainability Index (MI)")
    print_info("=" * 70)
    print_info("A = highly maintainable, B = good, C = moderate, D/F = hard to maintain")
    print("")
    
    run_command([str(radon), 'mi', 'missive/', '-s'], check=False)
    
    # Raw metrics
    print("\n" + "=" * 70)
    print_info("Raw Metrics (LOC, LLOC, Comments)")
    print_info("=" * 70)
    
    run_command([str(radon), 'raw', 'missive/', '-s'], check=False)
    
    print("\n" + "=" * 70)
    print_success("Complexity analysis complete!")
    print_info("Tip: Focus on reducing functions with CC > 10 (C or higher)")
    print_info("=" * 70)
    
    return True


def task_security():
    """Run security audit with multiple tools"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("=" * 70)
    print_info("SECURITY AUDIT - Django Missive")
    print_info("=" * 70)
    
    bandit = VENV_BIN / ('bandit.exe' if platform.system() == 'Windows' else 'bandit')
    safety = VENV_BIN / ('safety.exe' if platform.system() == 'Windows' else 'safety')
    pip_audit = VENV_BIN / ('pip-audit.exe' if platform.system() == 'Windows' else 'pip-audit')
    
    results = {
        'bandit': False,
        'safety': False,
        'pip_audit': False,
    }
    
    # 1. Bandit - Static code analysis
    print("\n" + "=" * 70)
    print_info("1/3 - Running Bandit (Static Code Analysis)")
    print_info("=" * 70)
    
    if run_command([str(bandit), '-r', 'missive/', '-ll', '-f', 'screen'], check=False):
        print_success("✓ Bandit: No high/medium issues found")
        results['bandit'] = True
    else:
        print_warning("⚠ Bandit: Issues found (review above)")
    
    # 2. Safety - Dependency vulnerability check
    print("\n" + "=" * 70)
    print_info("2/3 - Running Safety (Dependency Vulnerabilities)")
    print_info("=" * 70)
    
    if run_command([str(safety), 'check', '--json'], check=False):
        print_success("✓ Safety: No known vulnerabilities in dependencies")
        results['safety'] = True
    else:
        print_warning("⚠ Safety: Vulnerabilities found (review above)")
    
    # 3. Pip-Audit - PyPI vulnerability audit
    print("\n" + "=" * 70)
    print_info("3/3 - Running Pip-Audit (PyPI Vulnerabilities)")
    print_info("=" * 70)
    
    if run_command([str(pip_audit)], check=False):
        print_success("✓ Pip-Audit: No vulnerabilities found")
        results['pip_audit'] = True
    else:
        print_warning("⚠ Pip-Audit: Vulnerabilities found (review above)")
    
    # Summary
    print("\n" + "=" * 70)
    print_info("SECURITY AUDIT SUMMARY")
    print_info("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for tool, success in results.items():
        status = f"{GREEN}✓ PASS{NC}" if success else f"{RED}✗ FAIL{NC}"
        print(f"  {tool.upper():15} {status}")
    
    print("\n" + "-" * 70)
    score = int((passed / total) * 100)
    
    if score == 100:
        print_success(f"SECURITY SCORE: {score}/100 - EXCELLENT!")
    elif score >= 66:
        print_warning(f"SECURITY SCORE: {score}/100 - GOOD")
    else:
        print_error(f"SECURITY SCORE: {score}/100 - NEEDS ATTENTION")
    
    print("-" * 70)
    
    # Additional tools info
    print("\n" + BLUE + "Additional Security Tools (manual setup):" + NC)
    print("  • SonarQube: https://sonarcloud.io/ (requires account)")
    print("  • Snyk: https://snyk.io/ (requires account)")
    print("  • OWASP Dependency-Check: https://owasp.org/www-project-dependency-check/")
    
    return score == 100


def task_build():
    """Build package"""
    if not venv_exists() and not task_venv():
        return False
    
    task_clean()
    
    print_info("Building package...")
    
    # Install build
    if not run_command([str(PIP), 'install', '--upgrade', 'build']):
        return False
    
    # Build
    python_build = VENV_BIN / ('python.exe' if platform.system() == 'Windows' else 'python')
    if not run_command([str(python_build), '-m', 'build']):
        return False
    
    print_success("Build complete! Files in dist/")
    
    # List files in dist
    dist_dir = PROJECT_ROOT / 'dist'
    if dist_dir.exists():
        for file in dist_dir.iterdir():
            print(f"  {file.name} ({file.stat().st_size / 1024:.1f} KB)")
    
    return True


def task_dist():
    """Alias for build"""
    return task_build()


def task_upload_test():
    """Upload to TestPyPI"""
    if not task_build():
        return False
    
    print_info("Uploading to TestPyPI...")
    
    if not run_command([str(PIP), 'install', '--upgrade', 'twine']):
        return False
    
    twine = VENV_BIN / ('twine.exe' if platform.system() == 'Windows' else 'twine')
    if not run_command([str(twine), 'upload', '--repository', 'testpypi', 'dist/*']):
        return False
    
    print_success("Upload complete!")
    print_info("Install with: pip install --index-url https://test.pypi.org/simple/ django-missive")
    return True


def task_upload():
    """Upload to PyPI"""
    if not task_build():
        return False
    
    print_warning("WARNING: This will upload to PyPI!")
    response = input("Press Enter to continue, or Ctrl+C to cancel... ")
    
    print_info("Uploading to PyPI...")
    
    if not run_command([str(PIP), 'install', '--upgrade', 'twine']):
        return False
    
    twine = VENV_BIN / ('twine.exe' if platform.system() == 'Windows' else 'twine')
    if not run_command([str(twine), 'upload', 'dist/*']):
        return False
    
    print_success("Upload complete!")
    print_info("Install with: pip install django-missive")
    return True


def task_release():
    """Full release workflow"""
    if not task_check():
        return False
    
    if not task_test():
        return False
    
    if not task_upload():
        return False
    
    print_success("Release complete!")
    return True


def task_show_version():
    """Show current package version"""
    print_info("Current version:")
    pyproject = PROJECT_ROOT / 'pyproject.toml'
    
    with open(pyproject, 'r') as f:
        for line in f:
            if line.startswith('version'):
                version = line.split('"')[1]
                print(f"  {version}")
                return True
    
    print_error("Version not found in pyproject.toml")
    return False


def task_requirements():
    """Generate requirements.txt"""
    print_info("Generating requirements.txt...")
    
    requirements_file = PROJECT_ROOT / 'requirements.txt'
    with open(requirements_file, 'w') as f:
        f.write("# Production dependencies for django-missive\n")
        f.write("# Auto-generated from pyproject.toml\n")
        f.write("# Install with: pip install -r requirements.txt\n\n")
        f.write("Django>=3.2\n")
    
    print_success("requirements.txt generated!")
    return True


def task_venv_clean():
    """Remove and recreate virtual environment"""
    if venv_exists():
        print_info("Removing existing virtual environment...")
        shutil.rmtree(VENV_DIR)
        print_success("Virtual environment removed")
    
    return task_venv()


def task_migrate():
    """Run Django migrations"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Running Django migrations...")
    manage_py = PROJECT_ROOT / 'manage.py'
    
    if run_command([str(PYTHON), str(manage_py), 'migrate']):
        print_success("Migrations complete!")
        print_info("Access admin at: http://127.0.0.1:8000/admin/")
        print_info("Login: admin / admin")
        return True
    return False


def task_makemigrations():
    """Create new Django migrations"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Creating Django migrations...")
    manage_py = PROJECT_ROOT / 'manage.py'
    
    if run_command([str(PYTHON), str(manage_py), 'makemigrations']):
        print_success("Migrations created!")
        return True
    return False


def task_runserver():
    """Start Django development server
    
    Configuration via variables d'environnement :
        DJANGO_PORT : Port d'écoute (défaut: 8000)
        DJANGO_HOST : Adresse d'écoute (défaut: 127.0.0.1)
    
    Exemples :
        python dev.py runserver
        DJANGO_PORT=30080 python dev.py runserver
        DJANGO_HOST=0.0.0.0 DJANGO_PORT=30080 python dev.py runserver
    """
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    # Check if migrations exist
    db_path = PROJECT_ROOT / 'db.sqlite3'
    if not db_path.exists():
        print_warning("Database not found. Running migrations first...")
        if not task_migrate():
            return False
    
    # Récupérer le port et l'hôte depuis les variables d'environnement
    port = os.environ.get('DJANGO_PORT', '8000')
    host = os.environ.get('DJANGO_HOST', '127.0.0.1')
    bind_address = f"{host}:{port}"
    
    print_success("Starting Django development server...")
    print_info(f"Access server at: http://{host}:{port}/")
    print_info(f"Access admin at: http://{host}:{port}/admin/")
    print_info("Login: admin / admin")
    print_warning("Press Ctrl+C to stop the server")
    
    manage_py = PROJECT_ROOT / 'manage.py'
    run_command([str(PYTHON), str(manage_py), 'runserver', bind_address], check=False)
    return True


def task_shell():
    """Open Django shell"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Opening Django shell...")
    manage_py = PROJECT_ROOT / 'manage.py'
    
    run_command([str(PYTHON), str(manage_py), 'shell'], check=False)
    return True


def task_createsuperuser():
    """Create Django superuser"""
    if not venv_exists():
        print_error("Virtual environment not found. Run: python dev.py install-dev")
        return False
    
    print_info("Creating Django superuser...")
    manage_py = PROJECT_ROOT / 'manage.py'
    
    run_command([str(PYTHON), str(manage_py), 'createsuperuser'], check=False)
    return True


# Command mapping
COMMANDS = {
    'help': task_help,
    'venv': task_venv,
    'install': task_install,
    'install-dev': task_install_dev,
    # Django commands
    'migrate': task_migrate,
    'makemigrations': task_makemigrations,
    'runserver': task_runserver,
    'shell': task_shell,
    'createsuperuser': task_createsuperuser,
    # Testing
    'clean': task_clean,
    'clean-build': task_clean_build,
    'clean-pyc': task_clean_pyc,
    'clean-test': task_clean_test,
    'test': task_test,
    'test-verbose': task_test_verbose,
    'coverage': task_coverage,
    # Code quality
    'lint': task_lint,
    'format': task_format,
    'check': task_check,
    'cleanup': task_cleanup,
    'fix-imports': task_fix_imports,
    'complexity': task_complexity,
    # Security
    'security': task_security,
    # Building
    'build': task_build,
    'dist': task_dist,
    # Publishing
    'upload-test': task_upload_test,
    'upload': task_upload,
    'release': task_release,
    # Utilities
    'show-version': task_show_version,
    'requirements': task_requirements,
    'venv-clean': task_venv_clean,
}


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        task_help()
        return 0
    
    command = sys.argv[1]
    
    if command not in COMMANDS:
        print_error(f"Unknown command: {command}")
        print_info("Run 'python dev.py help' to see available commands")
        return 1
    
    try:
        success = COMMANDS[command]()
        return 0 if success else 1
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

