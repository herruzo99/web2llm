"""A scraper for extracting text content from PDF files."""

import io
import os
from datetime import datetime, timezone

import pdfplumber
import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..utils import fetch_html

class PDFScraper(BaseScraper):
    """
    Scrapes a PDF file. It intelligently attempts to find the associated
    HTML landing page to extract high-quality metadata before processing the PDF.
    """

    def _get_metadata_from_landing_page(self) -> dict:
        """
        Attempts to find and scrape the HTML landing page for a PDF to get
        reliable metadata.

        Returns:
            A dictionary containing 'title' and 'description'.
        """
        metadata = {'title': '', 'description': ''}
        
        # Heuristic for arXiv URLs
        if 'arxiv.org/pdf/' in self.url:
            landing_page_url = self.url.replace('/pdf/', '/abs/')
            try:
                html = fetch_html(landing_page_url)
                soup = BeautifulSoup(html, 'lxml')
                
                title_tag = soup.select_one('h1.title')
                if title_tag:
                    title_text = title_tag.get_text(strip=True).replace("Title:", "").strip()
                    metadata['title'] = title_text

                desc_tag = soup.select_one('blockquote.abstract')
                if desc_tag:
                    desc_text = desc_tag.get_text(strip=True).replace("Abstract:", "").strip()
                    metadata['description'] = desc_text
                
            except Exception as e:
                print(f"Warning: Could not fetch or parse landing page: {e}")
        
        return metadata

    def scrape(self) -> tuple[str, dict]:
        """Downloads a PDF and extracts its text content and metadata."""
        
        metadata = self._get_metadata_from_landing_page()
        title = metadata.get('title', '')
        description = metadata.get('description', 'No description found.')

        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise IOError(f"Failed to download PDF: {e}")

        pdf_content = ""
        with io.BytesIO(response.content) as pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                # As a fallback, check PDF properties if landing page failed
                if not title and pdf.metadata and 'Title' in pdf.metadata:
                    title = pdf.metadata['Title']
                
                # As a final fallback, use the filename
                if not title:
                    title = os.path.basename(self.url)

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text(keep_blank_chars=True, x_tolerance=2)
                    if text:
                        pdf_content += f"\n\n--- Page {i+1} ---\n\n{text}"
        
        scraped_at = datetime.now(timezone.utc).isoformat()
        front_matter = (
            "---\n"
            f'title: "{title}"\n'
            f'source_url: "{self.url}"\n'
            f'description: "{description}"\n'
            f'scraped_at: "{scraped_at}"\n'
            "---\n"
        )
        
        final_markdown = front_matter + pdf_content
        context_data = {
            "source_url": self.url,
            "page_title": title,
            "description": description,
            "scraped_at": scraped_at
        }
        
        return final_markdown, context_data