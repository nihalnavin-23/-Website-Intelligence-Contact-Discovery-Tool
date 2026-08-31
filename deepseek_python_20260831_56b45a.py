# webscrappingvali.py
import streamlit as st
import sys
import subprocess

# Try to install missing dependencies
def install_missing_dependencies():
    """Install missing dependencies"""
    required_packages = [
        'requests',
        'beautifulsoup4',
        'pandas',
        'openpyxl',
        'dnspython',
        'validators',
        'python-whois',
        'lxml'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        st.warning(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            st.success("Packages installed successfully! Please refresh the page.")
            st.stop()
        except Exception as e:
            st.error(f"Failed to install packages: {str(e)}")
            st.info("Please add a requirements.txt file to your repository with the following content:")
            st.code("""
streamlit==1.28.0
requests==2.31.0
beautifulsoup4==4.12.2
pandas==2.1.3
openpyxl==3.1.2
dnspython==2.4.2
validators==0.22.0
python-whois==0.8.0
lxml==4.9.3
            """)
            st.stop()

# Install dependencies
install_missing_dependencies()

# Now import required modules
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import urlparse, urljoin
import time
from datetime import datetime
import dns.resolver
import validators
import whois
from typing import Set, List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

# Rest of your code...