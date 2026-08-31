# 🔍 Website Intelligence & Contact Discovery Tool

A powerful web scraping and contact discovery tool built with Python and Streamlit that extracts email addresses, validates them, and identifies social media accounts from websites. Perfect for lead generation, market research, and business intelligence.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

## ✨ Features

### 🔍 Web Scraping
- **Multi-URL Support**: Scrape multiple websites simultaneously
- **Smart Page Discovery**: Automatically finds contact and about pages
- **Email Extraction**: Extracts emails from text, mailto links, and scripts
- **Social Media Detection**: Identifies 10+ social media platforms
- **Concurrent Processing**: Fast scraping with thread pooling
- **Polite Scraping**: Rate limiting and respectful crawling

### 📧 Email Validation
- **Syntax Validation**: Checks email format correctness
- **Domain Validation**: Verifies MX records for email domains
- **Disposable Email Detection**: Identifies temporary email providers
- **Status Classification**: Categorizes as Valid, Invalid, or Potentially Undeliverable
- **Detailed Reporting**: Provides validation details for each email

### 🌐 Social Media Discovery
- **Multiple Platforms**: LinkedIn, Instagram, Facebook, Twitter/X, YouTube, GitHub
- **Automatic Detection**: Finds social media links in webpage content
- **URL Extraction**: Captures complete profile URLs
- **Platform Icons**: Visual indicators for easy identification

### 📊 Dashboard Features
- **Interactive UI**: Clean Streamlit interface
- **Real-time Progress**: Live scraping progress indicators
- **Tabbed Results**: Organized overview, email, and social media sections
- **Filterable Data**: Search and filter email results
- **Summary Statistics**: Key metrics at a glance
- **Per-Website Analysis**: Detailed breakdown for each URL

### 📥 Export Options
- **CSV Export**: Download emails and social media separately
- **Excel Report**: Complete report with multiple sheets
- **Combined Export**: All data in one file
- **Timestamped Files**: Organized file naming

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/website-intelligence-tool.git
cd website-intelligence-tool
