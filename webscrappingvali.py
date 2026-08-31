""")

# Main input area
urls_to_scrape = []
scrape_button = False

if input_mode == "Single URL":
col1, col2 = st.columns([3, 1])
with col1:
    url_input = st.text_input(
        "Enter website URL:",
        placeholder="python.org or https://python.org",
        help="Enter the website you want to analyze"
    )
with col2:
    st.write("")
    st.write("")
    scrape_button = st.button("🔍 Start Analysis", type="primary", use_container_width=True)

if url_input:
    urls_to_scrape = [url_input]
    
else:  # Multiple URLs
urls_text = st.text_area(
    "Enter URLs (one per line):",
    height=200,
    placeholder="python.org\napache.org\ngnu.org\neff.org",
    help="Enter each URL on a new line"
)

scrape_button = st.button("🔍 Start Analysis", type="primary", use_container_width=True)

if urls_text:
    urls_to_scrape = [url.strip() for url in urls_text.split('\n') if url.strip()]

# Show URLs count
if urls_to_scrape:
st.info(f"📋 **{len(urls_to_scrape)}** URL(s) ready to analyze")

# Initialize session state
if 'results' not in st.session_state:
st.session_state.results = None

# Process URLs
if scrape_button and urls_to_scrape:
st.markdown("---")
st.info(f"🔍 Analyzing {len(urls_to_scrape)} website(s)...")

progress_bar = st.progress(0)
status_text = st.empty()

scraper = WebsiteScraper()
results = []

for i, url in enumerate(urls_to_scrape):
    status_text.text(f"Scraping {i+1}/{len(urls_to_scrape)}: {url}")
    result = scraper.scrape_single_website(url, max_pages)
    results.append(result)
    progress_bar.progress((i + 1) / len(urls_to_scrape))

progress_bar.empty()
status_text.empty()

st.session_state.results = results

# Show summary
total_emails = sum(len(r['emails']) for r in results)
total_socials = sum(len(r['social_media']) for r in results)
successful = sum(1 for r in results if r['status'] == 'success')

st.success(f"✅ **Analysis Complete!** Found {total_emails} emails and {total_socials} social media accounts from {successful}/{len(results)} websites.")

# Display results
if st.session_state.results:
st.markdown("---")

# Summary table
st.subheader("📊 Results Summary")
summary_data = []
for result in st.session_state.results:
    summary_data.append({
        'Website': result['url'],
        'Status': result['status'].upper(),
        'Emails': len(result['emails']),
        'Social Media': len(result['social_media']),
        'Pages': result['pages_scraped']
    })

df_summary = pd.DataFrame(summary_data)
st.dataframe(df_summary, use_container_width=True, hide_index=True)

# Emails section
st.markdown("---")
st.subheader("📧 Emails Found")

all_emails_with_source = []
for result in st.session_state.results:
    if result['emails']:
        for email in result['emails']:
            all_emails_with_source.append({
                'Email': email,
                'Source': result['url'],
                'Validation': perform_full_email_validation(email)['status']
            })

if all_emails_with_source:
    df_emails = pd.DataFrame(all_emails_with_source)
    
    # Add filter
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect(
            "Filter by validation status:",
            options=['Valid', 'Invalid', 'Potentially Undeliverable'],
            default=['Valid', 'Potentially Undeliverable']
        )
    
    if status_filter:
        df_emails = df_emails[df_emails['Validation'].isin(status_filter)]
    
    st.dataframe(df_emails, use_container_width=True, hide_index=True)
else:
    st.info("No emails found.")

# Social media section
st.markdown("---")
st.subheader("🌐 Social Media Accounts")

all_socials = []
for result in st.session_state.results:
    if result['social_media']:
        for platform, url in result['social_media'].items():
            all_socials.append({
                'Platform': platform,
                'URL': url,
                'Source': result['url']
            })

if all_socials:
    df_socials = pd.DataFrame(all_socials)
    st.dataframe(df_socials, use_container_width=True, hide_index=True)
else:
    st.info("No social media accounts found.")

# Export options
st.markdown("---")
st.subheader("📥 Export Results")

col1, col2 = st.columns(2)

with col1:
    if all_emails_with_source:
        df_export = pd.DataFrame(all_emails_with_source)
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Emails (CSV)",
            data=csv_data,
            file_name=f"emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

with col2:
    if all_socials:
        df_social_export = pd.DataFrame(all_socials)
        social_csv = df_social_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Social Media (CSV)",
            data=social_csv,
            file_name=f"social_media_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

if __name__ == "__main__":
main()