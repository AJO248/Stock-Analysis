#!/usr/bin/env python3
"""
System validation script for Stock Analysis Platform.
Run this before starting the app to check if everything is configured correctly.
"""

import sys
import os
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_header(text):
    """Print colored header."""
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{NC}")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{NC}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{NC}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{NC}")


def check_python_version():
    """Check if Python version is sufficient."""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version_str} (>= 3.8 required)")
        return True
    else:
        print_error(f"Python {version_str} - Need Python 3.8 or higher")
        return False


def check_dependencies():
    """Check if all required packages are installed."""
    print_header("Checking Dependencies")
    
    required_packages = [
        'yfinance',
        'beautifulsoup4',
        'requests',
        'openai',
        'langchain',
        'langchain_openai',
        'langchain_community',
        'faiss',
        'streamlit',
        'pandas',
        'dotenv',
    ]
    
    missing = []
    installed = []
    
    for package in required_packages:
        package_name = package if package != 'dotenv' else 'python-dotenv'
        package_name = package_name if package != 'faiss' else 'faiss-cpu'
        
        try:
            if package == 'dotenv':
                import dotenv
            elif package == 'faiss':
                import faiss
            else:
                __import__(package)
            installed.append(package)
            print_success(f"{package_name}")
        except ImportError:
            missing.append(package_name)
            print_error(f"{package_name} - Not installed")
    
    if missing:
        print(f"\n{YELLOW}Install missing packages with:{NC}")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def check_environment_file():
    """Check if .env file exists and has API key."""
    print_header("Checking Environment Configuration")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print_error(".env file not found")
        print(f"{YELLOW}Create it with:{NC} cp .env.template .env")
        return False
    
    print_success(".env file exists")
    
    # Check if API key is configured
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY', '')
        
        if not api_key or api_key == 'your_openai_api_key_here':
            print_warning("OPENAI_API_KEY not configured in .env")
            print(f"  {YELLOW}Add your API key to .env file{NC}")
            return False
        
        # Check if key format looks valid
        if api_key.startswith('sk-'):
            print_success("OPENAI_API_KEY configured")
            return True
        else:
            print_warning("OPENAI_API_KEY format looks incorrect (should start with 'sk-')")
            return False
    
    except Exception as e:
        print_error(f"Error reading .env: {e}")
        return False


def check_directories():
    """Check if required directories exist or can be created."""
    print_header("Checking Directory Structure")
    
    required_dirs = ['data', 'logs']
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        
        if dir_path.exists():
            print_success(f"{dir_name}/ directory exists")
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print_success(f"{dir_name}/ directory created")
            except Exception as e:
                print_error(f"Cannot create {dir_name}/ directory: {e}")
                return False
    
    return True


def check_project_files():
    """Check if all core project files exist."""
    print_header("Checking Project Files")
    
    required_files = [
        'config.py',
        'database.py',
        'stock_tracker.py',
        'news_scraper.py',
        'summarizer.py',
        'rag_engine.py',
        'main_pipeline.py',
        'app.py',
        'utils.py',
        'logger.py',
        'exceptions.py',
        'requirements.txt',
    ]
    
    missing = []
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            print_success(file_name)
        else:
            print_error(f"{file_name} - Missing")
            missing.append(file_name)
    
    if missing:
        print_error(f"{len(missing)} core files missing!")
        return False
    
    return True


def check_config_import():
    """Try to import config module."""
    print_header("Checking Configuration Import")
    
    try:
        import config
        print_success("config.py imports successfully")
        
        # Check critical config values
        if hasattr(config, 'OPENAI_API_KEY'):
            if config.OPENAI_API_KEY and config.OPENAI_API_KEY != 'your_openai_api_key_here':
                print_success("OpenAI API key configured in config")
            else:
                print_warning("OpenAI API key not configured")
        
        return True
    
    except Exception as e:
        print_error(f"Cannot import config: {e}")
        return False


def run_validation():
    """Run all validation checks."""
    print(f"\n{BLUE}╔═══════════════════════════════════════════════════════════╗")
    print(f"║  Stock Analysis Platform - System Validation             ║")
    print(f"╚═══════════════════════════════════════════════════════════╝{NC}\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_environment_file),
        ("Directories", check_directories),
        ("Project Files", check_project_files),
        ("Configuration", check_config_import),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Check failed with exception: {e}")
            results[name] = False
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{GREEN}PASS{NC}" if result else f"{RED}FAIL{NC}"
        print(f"  {name:.<40} {status}")
    
    print(f"\n{BLUE}Results: {passed}/{total} checks passed{NC}")
    
    if passed == total:
        print(f"\n{GREEN}╔═══════════════════════════════════════════════════════════╗")
        print(f"║  ✓ All checks passed! System is ready.                   ║")
        print(f"╚═══════════════════════════════════════════════════════════╝{NC}")
        print(f"\n{GREEN}You can now start the application:{NC}")
        print(f"  streamlit run app.py\n")
        return True
    else:
        print(f"\n{YELLOW}╔═══════════════════════════════════════════════════════════╗")
        print(f"║  ⚠ Some checks failed. Please fix the issues above.      ║")
        print(f"╚═══════════════════════════════════════════════════════════╝{NC}")
        print(f"\n{YELLOW}Common fixes:{NC}")
        print(f"  1. Install dependencies: pip install -r requirements.txt")
        print(f"  2. Configure API key: edit .env file")
        print(f"  3. Check file permissions\n")
        return False


if __name__ == "__main__":
    try:
        success = run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Validation interrupted by user{NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{NC}")
        sys.exit(1)
