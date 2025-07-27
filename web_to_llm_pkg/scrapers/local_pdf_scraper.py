"""A scraper for processing a local PDF file."""

import os
from datetime import datetime, timezone
import pdfplumber

from .pdf_scraper import PDFScraper

class LocalPDFScraper(PDFScraper):
    """
    Scrapes text content from a local PDF file.

    This class reuses the PDF processing and title-finding heuristics from the
    main PDFScraper but operates on a local file path.
    """

    def scrape(self) -> tuple[str, dict]:
        """
        Reads the local PDF and returns its structured content.
        """
        file_path = self.url
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The provided file was not found: {file_path}")

        pdf_content = ""
        title = ""
        print(f"Processing local PDF file: {file_path}")
        
        with pdfplumber.open(file_path) as pdf:
            # First, try to get the title from the PDF's internal metadata
            if pdf.metadata and 'Title' in pdf.metadata and pdf.metadata['Title']:
                title = pdf.metadata['Title']
            
            # If no metadata title, use our heuristic on the first page
            if not title and len(pdf.pages) > 0:
                title = self._find_title_heuristic(pdf.pages[0])

            # As a final fallback, use the filename
            if not title:
                title = os.path.basename(file_path)

            for i, page in enumerate(pdf.pages):
                text = page.extract_text(keep_blank_chars=True, x_tolerance=2)
                if text:
                    pdf_content += f"\n\n--- Page {i+1} ---\n\n{text}"
        
        scraped_at = datetime.now(timezone.utc).isoformat()
        front_matter = (
            "---\n"
            f'title: "{title}"\n'
            f'source_path: "{file_path}"\n'
            f'scraped_at: "{scraped_at}"\n'
            "---\n"
        )
        
        final_markdown = front_matter + pdf_content
        context_data = { "source_path": file_path, "page_title": title, "scraped_at": scraped_at }
        
        return final_markdown, context_data