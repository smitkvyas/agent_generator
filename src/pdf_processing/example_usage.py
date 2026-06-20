"""
Example usage of the PDFProcessor class.
"""

import os
from pdf_processor import PDFProcessor


def main():
    """Example usage of PDFProcessor."""
    
    # Example PDF path - replace with your actual PDF file
    pdf_path = "../../media/mva case with image in pdf.pdf"
    
    # Check if the example PDF exists
    if not os.path.exists(pdf_path):
        print(f"Please provide a PDF file named '{pdf_path}' or update the pdf_path variable")
        print("You can use any PDF file you have available.")
        return
    
    try:
        # Using context manager (recommended)
        with PDFProcessor(pdf_path) as processor:
            # Get basic information
            print(f"PDF has {processor.get_page_count()} pages")
            
            # Extract metadata
            metadata = processor.extract_metadata()
            print(f"Title: {metadata.get('title', 'N/A')}")
            print(f"Author: {metadata.get('author', 'N/A')}")
            
            # Extract text from all pages
            full_text = processor.extract_text()
            print(f"Extracted text length: {len(full_text)} characters")
            
            # Extract text from first page only
            first_page_text = processor.extract_text_by_page(0)
            print(f"First page text length: {len(first_page_text)} characters")
            
            # Search for specific text
            search_results = processor.search_text("example")
            print(f"Found 'example' {len(search_results)} times")
            
            # Get page dimensions
            dimensions = processor.get_page_dimensions(0)
            print(f"First page dimensions: {dimensions['width']} x {dimensions['height']}")
            
            # Extract images
            images = processor.extract_images()
            print(f"Found {len(images)} images in the PDF")
    
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
