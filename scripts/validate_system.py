#!/usr/bin/env python3
"""
System Validation Script
Validates the complete traffic classifier system
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import get_config
from src.utils.logger import get_logger


class SystemValidator:
    """Validates system components and configuration"""
    
    def __init__(self):
        self.logger = get_logger('validator')
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("="*80)
        print("🔍 SYSTEM VALIDATION")
        print("="*80)
        print()
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("Configuration", self.check_configuration),
            ("Directory Structure", self.check_directories),
            ("Models", self.check_models),
            ("Ryu Controller", self.check_ryu),
            ("Mininet", self.check_mininet),
            ("Open vSwitch", self.check_ovs),
        ]
        
        for name, check_func in checks:
            print(f"Checking {name}...", end=" ")
            try:
                result = check_func()
                self.results[name] = result
                if result:
                    print("✅ PASS")
                else:
                    print("❌ FAIL")
            except Exception as e:
                self.results[name] = False
                self.errors.append(f"{name}: {str(e)}")
                print(f"❌ ERROR: {e}")
        
        print()
        print("="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("="*80)
        
        return all(self.results.values())
    
    def check_python_version(self) -> bool:
        """Check Python version"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True
        self.errors.append(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    def check_dependencies(self) -> bool:
        """Check required Python packages"""
        required = [
            'numpy',
            'sklearn',
            'yaml',
            'flask',
            'prettytable',
            'psutil'
        ]
        
        missing = []
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            self.errors.append(f"Missing packages: {', '.join(missing)}")
            return False
        
        return True
    
    def check_configuration(self) -> bool:
        """Check configuration files"""
        try:
            config = get_config()
            
            # Check required sections
            required_sections = ['system', 'controller', 'classification', 'qos', 'logging']
            for section in required_sections:
                if section not in config.config:
                    self.errors.append(f"Missing config section: {section}")
                    return False
            
            return True
        except Exception as e:
            self.errors.append(f"Configuration error: {e}")
            return False
    
    def check_directories(self) -> bool:
        """Check required directories exist"""
        base_dir = Path(__file__).parent.parent
        
        required_dirs = [
            'src',
            'src/utils',
            'src/ml',
            'src/controller',
            'config',
            'models',
            'datasets',
            'tests',
            'logs',
            'metrics',
            'flow_rules'
        ]
        
        missing = []
        for dir_path in required_dirs:
            full_path = base_dir / dir_path
            if not full_path.exists():
                missing.append(dir_path)
        
        if missing:
            self.errors.append(f"Missing directories: {', '.join(missing)}")
            return False
        
        return True
    
    def check_models(self) -> bool:
        """Check ML models exist"""
        base_dir = Path(__file__).parent.parent
        models_dir = base_dir / 'models'
        
        if not models_dir.exists():
            self.errors.append("Models directory not found")
            return False
        
        # Check for at least one model
        model_files = list(models_dir.glob('*.pkl'))
        
        if not model_files:
            self.errors.append("No model files found in models/")
            return False
        
        return True
    
    def check_ryu(self) -> bool:
        """Check Ryu controller availability"""
        try:
            result = subprocess.run(
                ['ryu-manager', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.errors.append("Ryu controller not found or not responding")
            return False
    
    def check_mininet(self) -> bool:
        """Check Mininet availability"""
        try:
            result = subprocess.run(
                ['mn', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.errors.append("Mininet not found")
            return False
    
    def check_ovs(self) -> bool:
        """Check Open vSwitch availability"""
        try:
            result = subprocess.run(
                ['ovs-vsctl', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.errors.append("Open vSwitch not found")
            return False


def main():
    """Main validation function"""
    validator = SystemValidator()
    success = validator.validate_all()
    
    if success:
        print("\n✅ System validation PASSED - Ready for deployment!")
        return 0
    else:
        print("\n❌ System validation FAILED - Please fix errors before deployment")
        return 1


if __name__ == '__main__':
    sys.exit(main())
