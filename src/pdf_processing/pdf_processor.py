"""
PDF Processor class for extracting content from PDF files using PyMuPDF.
"""

import fitz  # PyMuPDF
from typing import Optional, List, Dict, Any
import os


class PDFProcessor:
    """
    A class to extract content from PDF files using PyMuPDF.
    
    This class provides methods to extract text, images, metadata, and other
    content from PDF documents.
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF processor with a PDF file path.
        
        Args:
            pdf_path (str): Path to the PDF file to process
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError(f"File must be a PDF: {pdf_path}")
        
        self.pdf_path = pdf_path
        self._document = None
    
    def _open_document(self) -> fitz.Document:
        """
        Open the PDF document if not already open.
        
        Returns:
            fitz.Document: The opened PDF document
        """
        if self._document is None:
            self._document = fitz.open(self.pdf_path)
        return self._document
    
    def close(self):
        """Close the PDF document to free resources."""
        if self._document is not None:
            self._document.close()
            self._document = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_page_count(self) -> int:
        """
        Get the total number of pages in the PDF.
        
        Returns:
            int: Number of pages in the PDF
        """
        doc = self._open_document()
        return doc.page_count
    
    def extract_text(self, page_range: Optional[tuple] = None) -> str:
        """
        Extract text content from the PDF.
        
        Args:
            page_range (tuple, optional): Tuple of (start_page, end_page) indices.
                                        If None, extracts from all pages.
        
        Returns:
            str: Extracted text content
        """
        doc = self._open_document()
        
        if page_range is None:
            start_page, end_page = 0, doc.page_count
        else:
            start_page, end_page = page_range
            start_page = max(0, start_page)
            end_page = min(doc.page_count, end_page)
        
        text_content = []
        for page_num in range(start_page, end_page):
            page = doc[page_num]
            text_content.append(page.get_text())
        
        return '\n'.join(text_content)
    
    def extract_text_by_page(self, page_number: int) -> str:
        """
        Extract text content from a specific page.
        
        Args:
            page_number (int): Page number (0-indexed)
        
        Returns:
            str: Text content from the specified page
            
        Raises:
            IndexError: If page number is out of range
        """
        doc = self._open_document()
        
        if page_number < 0 or page_number >= doc.page_count:
            raise IndexError(f"Page number {page_number} is out of range. "
                           f"PDF has {doc.page_count} pages.")
        
        page = doc[page_number]
        return page.get_text()
    
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract metadata from the PDF.
        
        Returns:
            Dict[str, Any]: PDF metadata including title, author, subject, etc.
        """
        doc = self._open_document()
        return doc.metadata
    
    def extract_images(self, page_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extract images from the PDF.
        
        Args:
            page_number (int, optional): Specific page to extract images from.
                                      If None, extracts from all pages.
        
        Returns:
            List[Dict[str, Any]]: List of image information dictionaries
        """
        doc = self._open_document()
        images = []
        
        if page_number is not None:
            pages_to_process = [page_number]
        else:
            pages_to_process = range(doc.page_count)
        
        for page_num in pages_to_process:
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n > 4 or pix.alpha:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                image_info = {
                    'page_number': page_num,
                    'image_index': img_index,
                    'xref': xref,
                    'width': pix.width,
                    'height': pix.height,
                    'colorspace': pix.colorspace.name if pix.colorspace else None,
                    'n': pix.n,
                    'alpha': pix.alpha,
                    'image_bytes': pix.tobytes("png"),
                }
                images.append(image_info)
                pix = None  # Free memory
        
        return images
    
    def get_page_dimensions(self, page_number: int) -> Dict[str, float]:
        """
        Get the dimensions of a specific page.
        
        Args:
            page_number (int): Page number (0-indexed)
        
        Returns:
            Dict[str, float]: Page dimensions with 'width' and 'height' keys
        """
        doc = self._open_document()
        
        if page_number < 0 or page_number >= doc.page_count:
            raise IndexError(f"Page number {page_number} is out of range. "
                           f"PDF has {doc.page_count} pages.")
        
        page = doc[page_number]
        rect = page.rect
        
        return {
            'width': rect.width,
            'height': rect.height
        }
    
    def search_text(self, search_term: str, page_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for text within the PDF.
        
        Args:
            search_term (str): Text to search for
            page_number (int, optional): Specific page to search in.
                                       If None, searches all pages.
        
        Returns:
            List[Dict[str, Any]]: List of search results with page and position info
        """
        doc = self._open_document()
        results = []
        
        if page_number is not None:
            pages_to_search = [page_number]
        else:
            pages_to_search = range(doc.page_count)
        
        for page_num in pages_to_search:
            page = doc[page_num]
            text_instances = page.search_for(search_term)
            
            for instance in text_instances:
                result = {
                    'page_number': page_num,
                    'bbox': instance,  # Bounding box coordinates
                    'text': search_term
                }
                results.append(result)
        
        return results
