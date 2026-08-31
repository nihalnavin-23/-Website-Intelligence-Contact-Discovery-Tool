# requirements.txt
"""
streamlit==1.28.0
requests==2.31.0
beautifulsoup4==4.12.2
pandas==2.1.3
openpyxl==3.1.2
dnspython==2.4.2
validators==0.22.0
python-whois==0.8.0
lxml==4.9.3
"""

# main.py
import streamlit as st
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
import json
from collections import defaultdict
import warnings
import concurrent.futures
from threading import Lock
import base64
from io import BytesIO
warnings.filterwarnings('ignore')

# Email validation function
def validate_email_syntax(email: str) -> bool:
    """Check if email has valid syntax"""
    return validators.email(email)

def check_email_domain(email: str) -> Tuple[bool, str]:
    """Check if email domain has valid MX records"""
    try:
        domain = email.split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        if mx_records:
            return True, "Domain has valid MX records"
        return False, "Domain has no MX records"
    except Exception as e:
        return False, f"Domain check failed: {str(e)[:50]}"

def check_disposable_email(email: str) -> bool:
    """Check if email is from a disposable email provider"""
    disposable_domains = {
        'tempmail.com', 'throwaway.com', 'mailinator.com', 'guerrillamail.com',
        'sharklasers.com', '10minutemail.com', 'yopmail.com', 'temp-mail.org',
        'fakeinbox.com', 'trashmail.com', 'getnada.com', 'dispostable.com'
    }
    domain = email.split('@')[1].lower()
    return domain in disposable_domains

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
    
    # Check domain
    domain_valid, domain_msg = check_email_domain(email)
    result['domain_valid'] = domain_valid
    result['details'].append(domain_msg)
    
    # Final status
    if result['syntax_valid'] and result['domain_valid'] and not result['disposable']:
        result['status'] = 'Valid'
    elif result['syntax_valid'] and not result['domain_valid']:
        result['status'] = 'Potentially Undeliverable'
    
    return result

# Web scraper class
class WebsiteScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.lock = Lock()
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL with protocol"""
        url = url.strip()
        if not url:
            return url
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def fetch_page(self, url: str) -> Tuple[BeautifulSoup, str]:
        """Fetch page and return BeautifulSoup object"""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml'), response.url
    
    def extract_emails(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract email addresses from page content"""
        emails = set()
        
        # Get all text from the page
        text = soup.get_text()
        
        # Look for emails in text
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        text_emails = re.findall(email_pattern, text)
        emails.update(text_emails)
        
        # Look for emails in mailto links
        mailto_links = soup.find_all('a', href=True)
        for link in mailto_links:
            href = link['href']
            if 'mailto:' in href:
                email = href.replace('mailto:', '').split('?')[0]
                if re.match(email_pattern, email):
                    emails.add(email)
        
        # Look for emails in scripts
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_emails = re.findall(email_pattern, script.string)
                emails.update(script_emails)
        
        # Filter out common false positives
        filtered_emails = set()
        false_positive_patterns = [
            '.png', '.jpg', '.gif', '.css', '.js', '.woff', '.svg', '.webp',
            '.ico', '.pdf', '.zip', '.tar', '.gz', '.mp4', '.mp3',
            'example.com', 'domain.com', 'email.com', 'test.com',
            'sentry.io', 'wixpress.com', 'sentry-next.wixpress.com'
        ]
        
        for email in emails:
            email_lower = email.lower()
            if not any(pattern in email_lower for pattern in false_positive_patterns):
                if len(email) < 100 and '@' in email:
                    filtered_emails.add(email_lower)
        
        return filtered_emails
    
    def extract_social_media(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Extract social media links"""
        social_platforms = {
            'LinkedIn': ['linkedin.com', 'linkedin.com/company'],
            'Instagram': ['instagram.com'],
            'Facebook': ['facebook.com', 'fb.com'],
            'Twitter/X': ['twitter.com', 'x.com'],
            'YouTube': ['youtube.com', 'youtu.be'],
            'GitHub': ['github.com'],
            'TikTok': ['tiktok.com'],
            'Pinterest': ['pinterest.com'],
            'Reddit': ['reddit.com'],
            'Discord': ['discord.gg', 'discord.com/invite']
        }
        
        found_socials = {}
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link['href'].lower()
            for platform, domains in social_platforms.items():
                if any(domain in href for domain in domains):
                    if platform not in found_socials:
                        found_socials[platform] = href
                    break
        
        return found_socials
    
    def scrape_single_website(self, url: str, max_pages: int = 5) -> Dict:
        """Scrape a single website"""
        try:
            url = self.normalize_url(url)
            all_emails = set()
            all_socials = {}
            visited_urls = set()
            pages_to_visit = [url]
            
            # Add common contact pages
            base_domain = urlparse(url).netloc
            common_paths = ['/contact', '/contact-us', '/about', '/about-us', '/team']
            for path in common_paths:
                pages_to_visit.append(urljoin(url, path))
            
            for i in range(min(max_pages, len(pages_to_visit) + 5)):
                if not pages_to_visit:
                    break
                    
                current_url = pages_to_visit.pop(0)
                if current_url in visited_urls:
                    continue
                
                try:
                    soup, final_url = self.fetch_page(current_url)
                    visited_urls.add(current_url)
                    
                    # Extract emails
                    emails = self.extract_emails(soup, final_url)
                    all_emails.update(emails)
                    
                    # Extract social media
                    socials = self.extract_social_media(soup, final_url)
                    all_socials.update(socials)
                    
                    # Find internal links for further scraping
                    if len(visited_urls) < max_pages:
                        links = soup.find_all('a', href=True)
                        for link in links[:20]:
                            href = link['href']
                            if href.startswith('/'):
                                absolute_url = urljoin(final_url, href)
                                if base_domain in absolute_url and absolute_url not in visited_urls:
                                    pages_to_visit.append(absolute_url)
                    
                    time.sleep(0.3)  # Be polite to the server
                    
                except Exception as e:
                    continue
            
            return {
                'url': url,
                'emails': list(all_emails),
                'social_media': all_socials,
                'pages_scraped': len(visited_urls),
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
    
    def scrape_multiple_websites(self, urls: List[str], max_pages: int = 5) -> List[Dict]:
        """Scrape multiple websites concurrently"""
        results = []
        
        # Use ThreadPoolExecutor for concurrent scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(self.scrape_single_website, url, max_pages): url 
                           for url in urls if url.strip()}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'url': url,
                        'emails': [],
                        'social_media': {},
                        'pages_scraped': 0,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return results

# Streamlit app
def main():
    st.set_page_config(
        page_title="Website Intelligence Tool - Multi-URL",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Website Intelligence & Contact Discovery")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        max_pages = st.slider("Max pages per website", 1, 20, 5)
        max_workers = st.slider("Concurrent requests", 1, 5, 3)
        
        st.markdown("---")
        st.header("📝 Input Options")
        input_mode = st.radio(
            "Choose input method",
            ["Single URL", "Multiple URLs", "Upload File"]
        )
        
        st.info("""
        **How it works:**
        1. Enter website URLs
        2. Tool scrapes the sites
        3. Extracts emails & social media
        4. Validates email addresses
        5. Export results
        """)
    
    # Main input area
    urls_to_scrape = []
    
    if input_mode == "Single URL":
        col1, col2 = st.columns([3, 1])
        with col1:
            url_input = st.text_input(
                "Enter website URL or name:",
                placeholder="example.com or https://example.com",
                help="Enter the website you want to analyze"
            )
        with col2:
            st.write("")
            st.write("")
            scrape_button = st.button("🔍 Start Analysis", type="primary", use_container_width=True)
        
        if url_input:
            urls_to_scrape = [url_input]
            
    elif input_mode == "Multiple URLs":
        st.markdown("### Enter Multiple URLs (one per line)")
        urls_text = st.text_area(
            "Enter URLs (one per line):",
            height=150,
            placeholder="python.org\napache.org\ngnu.org",
            help="Enter each URL on a new line"
        )
        
        scrape_button = st.button("🔍 Start Analysis", type="primary", use_container_width=True)
        
        if urls_text:
            urls_to_scrape = [url.strip() for url in urls_text.split('\n') if url.strip()]
            
    else:  # Upload File
        st.markdown("### Upload CSV/Text File with URLs")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'txt'],
            help="Upload a file with URLs (one per line for txt, or CSV with 'url' column)"
        )
        
        scrape_button = st.button("🔍 Start Analysis", type="primary", use_container_width=True)
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    if 'url' in df.columns:
                        urls_to_scrape = df['url'].dropna().tolist()
                    else:
                        st.error("CSV file must have a 'url' column")
                else:  # txt file
                    content = uploaded_file.getvalue().decode('utf-8')
                    urls_to_scrape = [url.strip() for url in content.split('\n') if url.strip()]
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    # Show URLs to be scraped
    if urls_to_scrape:
        st.markdown(f"**📋 URLs to analyze:** {len(urls_to_scrape)}")
        with st.expander("View URLs"):
            for i, url in enumerate(urls_to_scrape, 1):
                st.write(f"{i}. {url}")
    
    # Initialize session state
    if 'scraping_results' not in st.session_state:
        st.session_state.scraping_results = None
    if 'email_validation_results' not in st.session_state:
        st.session_state.email_validation_results = None
    
    if scrape_button and urls_to_scrape:
        with st.spinner(f"Scraping {len(urls_to_scrape)} website(s)..."):
            scraper = WebsiteScraper()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Scrape websites
            results = []
            total_urls = len(urls_to_scrape)
            
            for i, url in enumerate(urls_to_scrape):
                status_text.text(f"Scraping: {url} ({i+1}/{total_urls})")
                result = scraper.scrape_single_website(url, max_pages)
                results.append(result)
                progress_bar.progress((i + 1) / total_urls)
            
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.scraping_results = results
            
            # Validate all emails
            all_emails = []
            for result in results:
                for email in result['emails']:
                    if email not in [e['email'] for e in all_emails]:
                        validation = perform_full_email_validation(email)
                        validation['source_url'] = result['url']
                        all_emails.append(validation)
            
            st.session_state.email_validation_results = all_emails
            
            # Summary
            total_emails = len(all_emails)
            total_socials = sum(len(r['social_media']) for r in results)
            successful_scrapes = sum(1 for r in results if r['status'] == 'success')
            
            st.success(f"✅ Analysis complete! Scraped {successful_scrapes}/{total_urls} websites, found {total_emails} emails and {total_socials} social media accounts.")
    
    # Display results
    if st.session_state.scraping_results:
        st.markdown("---")
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📧 Email Analysis", "🌐 Social Media", "📋 Raw Results"])
        
        with tab1:
            st.subheader("Scraping Overview")
            
            # Summary metrics
            results = st.session_state.scraping_results
            total_emails = len(st.session_state.email_validation_results) if st.session_state.email_validation_results else 0
            total_socials = sum(len(r['social_media']) for r in results)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Websites Scraped", len(results))
            with col2:
                st.metric("Total Emails Found", total_emails)
            with col3:
                st.metric("Social Media Accounts", total_socials)
            with col4:
                success_rate = sum(1 for r in results if r['status'] == 'success') / len(results) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            # Per-website summary
            st.subheader("Per-Website Summary")
            summary_data = []
            for result in results:
                summary_data.append({
                    'Website': result['url'],
                    'Status': result['status'].upper(),
                    'Emails Found': len(result['emails']),
                    'Social Media': len(result['social_media']),
                    'Pages Scraped': result['pages_scraped']
                })
            
            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
        with tab2:
            if st.session_state.email_validation_results:
                st.subheader("Email Address Analysis")
                
                # Create DataFrame for display
                df_emails = pd.DataFrame(st.session_state.email_validation_results)
                df_emails['details'] = df_emails['details'].apply(lambda x: '; '.join(x))
                
                # Add status indicators
                df_emails['Status Icon'] = df_emails['status'].map({
                    'Valid': '✅',
                    'Invalid': '❌',
                    'Potentially Undeliverable': '⚠️'
                })
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.multiselect(
                        "Filter by status:",
                        options=['Valid', 'Invalid', 'Potentially Undeliverable'],
                        default=['Valid', 'Invalid', 'Potentially Undeliverable']
                    )
                with col2:
                    search_email = st.text_input("Search email:", "")
                
                # Apply filters
                if status_filter:
                    df_emails = df_emails[df_emails['status'].isin(status_filter)]
                if search_email:
                    df_emails = df_emails[df_emails['email'].str.contains(search_email, case=False)]
                
                # Reorder columns
                columns_order = ['Status Icon', 'email', 'status', 'source_url', 'syntax_valid', 'domain_valid', 'disposable', 'details']
                df_display = df_emails[columns_order]
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Status Icon": st.column_config.TextColumn("Status", width="small"),
                        "email": st.column_config.TextColumn("Email Address", width="medium"),
                        "status": st.column_config.TextColumn("Validation Status", width="medium"),
                        "source_url": st.column_config.TextColumn("Source URL", width="medium"),
                        "syntax_valid": st.column_config.CheckboxColumn("Syntax", width="small"),
                        "domain_valid": st.column_config.CheckboxColumn("Domain", width="small"),
                        "disposable": st.column_config.CheckboxColumn("Disposable", width="small"),
                        "details": st.column_config.TextColumn("Details", width="large"),
                    }
                )
            else:
                st.info("No emails to analyze.")
        
        with tab3:
            st.subheader("Social Media Accounts")
            
            all_socials = []
            for result in st.session_state.scraping_results:
                for platform, url in result['social_media'].items():
                    icon = {
                        'LinkedIn': '💼',
                        'Instagram': '📸',
                        'Facebook': '👥',
                        'Twitter/X': '🐦',
                        'YouTube': '▶️',
                        'GitHub': '💻',
                        'TikTok': '🎵',
                        'Pinterest': '📌',
                        'Reddit': '👽',
                        'Discord': '💬'
                    }.get(platform, '🔗')
                    
                    all_socials.append({
                        'Icon': icon,
                        'Platform': platform,
                        'URL': url,
                        'Source Website': result['url']
                    })
            
            if all_socials:
                df_socials = pd.DataFrame(all_socials)
                st.dataframe(
                    df_socials,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Icon": st.column_config.TextColumn("Icon", width="small"),
                        "Platform": st.column_config.TextColumn("Platform", width="medium"),
                        "URL": st.column_config.LinkColumn("Profile URL", width="large"),
                        "Source Website": st.column_config.TextColumn("Source", width="medium"),
                    }
                )
            else:
                st.info("No social media accounts found.")
        
        with tab4:
            st.subheader("Raw Scraping Results")
            
            for result in st.session_state.scraping_results:
                with st.expander(f"📄 {result['url']} - {result['status'].upper()}"):
                    st.write(f"**Pages Scraped:** {result['pages_scraped']}")
                    if result['error']:
                        st.error(f"**Error:** {result['error']}")
                    st.write(f"**Emails Found:** {len(result['emails'])}")
                    if result['emails']:
                        st.code('\n'.join(result['emails'][:10]))
                    st.write(f"**Social Media:** {len(result['social_media'])}")
                    if result['social_media']:
                        st.json(result['social_media'])
        
        # Export options
        st.markdown("---")
        st.subheader("📥 Export Results")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.session_state.email_validation_results:
                df_export = pd.DataFrame(st.session_state.email_validation_results)
                df_export['details'] = df_export['details'].apply(lambda x: '; '.join(x))
                
                csv_data = df_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download All Emails (CSV)",
                    data=csv_data,
                    file_name=f"emails_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            # Social media export
            all_socials = []
            for result in st.session_state.scraping_results:
                for platform, url in result['social_media'].items():
                    all_socials.append({
                        'Platform': platform,
                        'URL': url,
                        'Source Website': result['url']
                    })
            
            if all_socials:
                social_df = pd.DataFrame(all_socials)
                social_csv = social_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download Social Media (CSV)",
                    data=social_csv,
                    file_name=f"social_media_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col3:
            # Complete Excel report
            if st.session_state.email_validation_results:
                with pd.ExcelWriter('website_intel_complete.xlsx', engine='openpyxl') as writer:
                    # Emails sheet
                    df_emails = pd.DataFrame(st.session_state.email_validation_results)
                    df_emails['details'] = df_emails['details'].apply(lambda x: '; '.join(x))
                    df_emails.to_excel(writer, sheet_name='Emails', index=False)
                    
                    # Social media sheet
                    all_socials = []
                    for result in st.session_state.scraping_results:
                        for platform, url in result['social_media'].items():
                            all_socials.append({
                                'Platform': platform,
                                'URL': url,
                                'Source Website': result['url']
                            })
                    df_socials = pd.DataFrame(all_socials)
                    df_socials.to_excel(writer, sheet_name='Social Media', index=False)
                    
                    # Summary sheet
                    summary_data = []
                    for result in st.session_state.scraping_results:
                        summary_data.append({
                            'Website': result['url'],
                            'Status': result['status'],
                            'Emails Found': len(result['emails']),
                            'Social Media': len(result['social_media']),
                            'Pages Scraped': result['pages_scraped']
                        })
                    df_summary = pd.DataFrame(summary_data)
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                with open('website_intel_complete.xlsx', 'rb') as f:
                    excel_data = f.read()
                
                st.download_button(
                    label="📊 Download Complete Report (Excel)",
                    data=excel_data,
                    file_name=f"website_intel_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()