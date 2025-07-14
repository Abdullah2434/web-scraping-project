#!/usr/bin/env python3
"""
Test script to verify deployment readiness
"""

import sys
import os

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing imports...")
    
    try:
        # Core Flask
        from flask import Flask
        print("✅ Flask import successful")
        
        # Data processing
        import pandas as pd
        print("✅ Pandas import successful")
        
        import requests
        print("✅ Requests import successful")
        
        # Our modules
        from config import DATA_PATHS, DEFAULT_KEYWORDS
        print("✅ Config import successful")
        
        from flask_app import app
        print("✅ Flask app import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_creation():
    """Test app creation"""
    print("\n🧪 Testing app creation...")
    
    try:
        from app import create_app
        app = create_app()
        print("✅ App creation successful")
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Deployment Readiness Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return False
    
    # Test app creation
    if not test_app_creation():
        print("\n❌ App creation tests failed!")
        return False
    
    print("\n🎉 All tests passed! Ready for deployment!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 