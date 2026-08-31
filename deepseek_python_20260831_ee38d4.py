# webscrappingvali.py
import streamlit as st
import sys
import subprocess

# Function to check and install dependencies
@st.cache_resource
def check_dependencies():
    """Check and install required dependencies"""
    required_packages = {
        'requests': 'requests',
        'bs4': 'beautifulsoup4',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'dns': 'dnspython',
        'validators': 'validators',
        'whois': 'python-whois',
        'lxml': 'lxml'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        st.warning("Installing required packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])
            st.success("Packages installed! Please refresh the page.")
            st.stop()
        except Exception as e:
            st.error(f"Error installing packages: {e}")
            st.stop()
    
    return True

# Run dependency check
check_dependencies()

# Now import all required modules
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

# Set page config
st.set_page_config(
    page_title="Website Intelligence Tool",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Website Intelligence & Contact Discovery")
st.markdown("---")

# Email validation function
def validate_email_syntax(email: str) -> bool:
    """Check if email has valid syntax"""
    try:
        return validators.email(email)
    except:
        # Simple regex fallback
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

def check_email_domain(email: str) -> Tuple[bool, str]:
    """Check if email domain has valid MX records"""
    try:
        domain = email.split('@')[1]
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        mx_records = resolver.resolve(domain, 'MX')
        if mx_records:
            return True, "Domain has valid MX records"
        return False, "Domain has no MX records"
    except:
        # Skip DNS check if it fails
        return True, "DNS check skipped"

def check_disposable_email(email: str) -> bool:
    """Check if email is from a disposable email provider"""
    disposable_domains = {
        'tempmail.com', 'throwaway.com', 'mailinator.com', 'guerrillamail.com',
        'sharklasers.com', '10minutemail.com', 'yopmail.com', 'temp-mail.org',
        'fakeinbox.com', 'trashmail.com', 'getnada.com', 'dispostable.com'
    }
    try:
        domain = email.split('@')[1].lower()
        return domain in disposable_domains
    except:
        return False

def perform_full_email_validation(email: str) -> Dict:
    """Perform comprehensive email validation"""
    result = {
        'email': email,
        'syntax_valid': False,
        'domain_valid': False,
        'disposable': False,
        'status': 'Invalid',
        'details': []
    }
    
    # Check syntax
    if validate_email_syntax(email):
        result['syntax_valid'] = True
        result['details'].append("Syntax valid")
    else:
        result['details'].append("Invalid syntax")
        return result
    
    # Check disposable
    if check_disposable_email(email):
        result['disposable'] = True
        result['details'].append("Disposable email provider")
        result['status'] = 'Potentially Undeliverable'
        return result
    
    # Check domain (skip for speed)
    domain_valid, domain_msg = check_email_domain(email)
    result['domain_valid'] = domain_valid
    result['details'].append(domain_msg)
    
    # Final status
    if result['syntax_valid']:
        result['status'] = 'Valid'
    
    return result

# Web scraper class
class WebsiteScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL with protocol"""
        url = url.strip()
        if not url:
            return url
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def fetch_page(self, url: str):
        """Fetch page and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser'), response.url
        except:
            return None, url
    
    def extract_emails(self, soup) -> Set[str]:
        """Extract email addresses from page content"""
        if not soup:
            return set()
            
        emails = set()
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Get text and find emails
        text = soup.get_text()
        text_emails = re.findall(email_pattern, text)
        emails.update(text_emails)
        
        # Look for mailto links
        mailto_links = soup.find_all('a', href=True)
        for link in mailto_links:
            href = link['href']
            if 'mailto:' in href:
                email = href.replace('mailto:', '').split('?')[0]
                if re.match(email_pattern, email):
                    emails.add(email)
        
        # Filter emails
        filtered_emails = set()
        for email in emails:
            email_lower = email.lower()
            if '@' in email_lower and '.' in email_lower.split('@')[1]:
                if not any(x in email_lower for x in ['.png', '.jpg', '.gif', '.css', '.js']):
                    if len(email) < 100:
                        filtered_emails.add(email_lower)
        
        return filtered_emails
    
    def extract_social_media(self, soup) -> Dict[str, str]:
        """Extract social media links"""
        if not soup:
            return {}
            
        social_platforms = {
            'LinkedIn': ['linkedin.com'],
            'Instagram': ['instagram.com'],
            'Facebook': ['facebook.com', 'fb.com'],
            'Twitter/X': ['twitter.com', 'x.com'],
            'YouTube': ['youtube.com', 'youtu.be'],
            'GitHub': ['github.com'],
        }
        
        found_socials = {}
        all_links = soup.find_all('a', href=True)
        
        for link in all_links[:50]:
            href = link.get('href', '').lower()
            for platform, domains in social_platforms.items():
                if any(domain in href for domain in domains):
                    if platform not in found_socials:
                        found_socials[platform] = href
                    break
        
        return found_socials
    
    def scrape_single_website(self, url: str, max_pages: int = 3) -> Dict:
        """Scrape a single website quickly"""
        url = self.normalize_url(url)
        
        try:
            pages_to_try = [url]
            
            # Add contact page
            if '/contact' not in url:
                pages_to_try.append(url.rstrip('/') + '/contact')
            if '/about' not in url:
                pages_to_try.append(url.rstrip('/') + '/about')
            
            all_emails = set()
            all_socials = {}
            pages_scraped = 0
            
            for page_url in pages_to_try[:max_pages]:
                try:
                    soup, final_url = self.fetch_page(page_url)
                    if soup:
                        pages_scraped += 1
                        emails = self.extract_emails(soup)
                        all_emails.update(emails)
                        socials = self.extract_social_media(soup)
                        all_socials.update(socials)
                except:
                    continue
            
            return {
                'url': url,
                'emails': list(all_emails),
                'social_media': all_socials,
                'pages_scraped': pages_scraped,
                'status': 'success' if all_emails else 'partial',
                'error': None
            }
            
        except Exception as e:
            return {
                'url': url,
                'emails': [],
                'social_media': {},
                'pages_scraped': 0,
                'status': 'error',
                'error': str(e)
            }

# Main app
def main():
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        max_pages = st.slider("Max pages per website", 1, 5, 2)
        
        st.markdown("---")
        st.header("📝 Input Options")
        input_mode = st.radio(
            "Choose input method",
            ["Single URL", "Multiple URLs"]
        )
        
        st.info("""
        **Quick Test URLs:**