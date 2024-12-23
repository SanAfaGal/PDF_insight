"""
Module for processing and managing PDF files.

This module provides functions for extracting text, applying OCR, splitting, combining,
and renaming PDF files based on their content and configuration mappings.

Usage:
- The primary functions handle PDF files in batches, using directories to manage input and output.
- Configuration dictionaries (`eps_config` and `hospital_config`) are used to customize processing,
including file type mappings and filename formats.

Dependencies:
- PyPDF2: For PDF reading and writing.
- ocrmypdf: For Optical Character Recognition (OCR) processing.
- rapidfuzz: For string similarity matching.
- unidecode: For normalizing text.
- utils.log_utils: For setting up logging.

"""

import os
import re
from typing import Dict, List, Optional

import ocrmypdf
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError
from rapidfuzz import fuzz
from unidecode import unidecode

from utils.log_utils import setup_logging

info_logger, error_logger = setup_logging()


def clean_path(path: str) -> str:
    """
    Removes enclosing single or double quotation marks from a file path.

    Args:
        path (str): The file path to clean.

    Returns:
        str: The cleaned file path.
    """
    return path.strip("'\"")


def extract_invoice_number(folder_name: str) -> Optional[str]:
    """
    Extracts the first numeric value from the folder name.

    Args:
        folder_name (str): The name of the folder to extract the invoice number from.

    Returns:
        Optional[str]: The extracted numeric invoice number or None if not found.
    """
    match = re.search(r'\d+', folder_name)
    return match.group(0) if match else None


def clean_text(text: Optional[str]) -> str:
    """
    Removes extra whitespace from text. Returns empty string if text is None.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    return re.sub(r'\s{2,}', ' ', text) if text else ""


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extracts text from a PDF using PyPDF2.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        Optional[str]: Extracted text from the PDF or None if extraction fails.
    """
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            return "".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as e:
        error_logger.error(f"Error reading PDF {pdf_path}: {e}")
    except Exception as e:
        error_logger.error(f"Unexpected error extracting text from {pdf_path}: {e}")
    return None


def extract_patient_id(text: str) -> Optional[str]:
    """
    Extracts the patient ID from the text using a regex pattern.

    Args:
        text (str): The text to search for the patient ID.

    Returns:
        Optional[str]: The extracted patient ID, or None if not found.
    """
    text = re.sub(r"\s+", "", text)
    id_pattern = r"(TI|CC|RC)-(\d{5,15})"
    match = re.search(id_pattern, text)
    if match:
        return match.group(2)
    return None


def apply_ocr(pdf_path: str) -> None:
    """
    Applies OCR to a PDF and returns the path to the searchable PDF.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        None
    """
    try:
        output_path = f"{os.path.splitext(pdf_path)[0]}_searchable.pdf"
        ocrmypdf.ocr(pdf_path, output_path, deskew=True)
        os.remove(pdf_path)
    except Exception as e:
        error_logger.error(f"Error applying OCR to {pdf_path}: {e}")


def split_pdf_by_page(pdf_path: str) -> List[str]:
    """
    Splits a PDF into individual pages and saves each page as a separate PDF.

    Args:
        pdf_path (str): Path to the original PDF file.

    Returns:
        list: A list of paths to the individual page PDFs, or the original file if it's a single-page PDF.
    """
    page_paths = []
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)

            # If the PDF has only one page, return an empty list (indicating no splitting needed)
            if len(reader.pages) == 1:
                info_logger.info(f"Skipping splitting for single-page PDF: {pdf_path}")
                return [pdf_path]  # Return the original file in the list without splitting

            # If the PDF has more than one page, proceed to split
            for i, page in enumerate(reader.pages):
                page_pdf_path = f"{os.path.splitext(pdf_path)[0]}_page_{i + 1}.pdf"
                writer = PdfWriter()
                writer.add_page(page)
                with open(page_pdf_path, "wb") as output_file:
                    writer.write(output_file)
                page_paths.append(page_pdf_path)
        return page_paths
    except Exception as e:
        error_logger.error(f"Error splitting PDF {pdf_path} into pages: {e}")
        return []  # Return an empty list if there is an error


def combine_pdfs(pdf_paths: List[str], output_path: str) -> None:
    """
    Combines multiple PDFs into a single PDF file.

    Args:
        pdf_paths (List[str]): List of paths to PDF files.
        output_path (str): Path to the output combined PDF file.

    Returns:
        None
    """
    try:
        writer = PdfWriter()
        for pdf_path in pdf_paths:
            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    writer.add_page(page)
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        info_logger.info(f"Combined PDFs into {output_path}")

        # Remove original files after combining
        for pdf_path in pdf_paths:
            os.remove(pdf_path)

    except Exception as e:
        error_logger.error(f"Error combining PDFs {pdf_paths}: {e}")


def determine_file_type(text: str, keywords: Dict[str, List[str]], similarity_threshold: int = 80) -> Optional[str]:
    """
    Determines the file type based on keywords and fuzzy matching, selecting the most relevant one.

    Args:
        text (str): The text to analyze for file type determination.
        keywords (Dict[str, List[str]]): Dictionary mapping file types to associated keywords.
        similarity_threshold (int): The threshold for similarity between text and keywords.

    Returns:
        Optional[str]: The determined file type or None if no match is found.
    """

    normalized_text = unidecode(text).lower()
    best_match_file_type = None
    highest_similarity = 0  # Almacenará la mejor coincidencia encontrada

    for file_type, keyword_list in keywords.items():
        for keyword in keyword_list:
            normalized_keyword = unidecode(keyword).lower()

            # Comprueba si el keyword está en el texto
            if normalized_keyword in normalized_text:
                return file_type  # Si la palabra clave exacta se encuentra, se retorna inmediatamente

            # Compara la similitud con el umbral
            similarity = fuzz.partial_ratio(normalized_text, normalized_keyword)
            if similarity >= similarity_threshold and similarity > highest_similarity:
                best_match_file_type = file_type
                highest_similarity = similarity

    return best_match_file_type


def generate_new_filename(invoice: str, file_type: str, eps_config: Dict, hospital_config: Dict) -> str:
    """
    Generates a new filename based on EPS configuration.

    Args:
        invoice (str): Invoice number.
        file_type (str): The type of file.
        eps_config (Dict): Configuration dictionary for file naming.
        hospital_config (Dict): Hospital configuration with NIT and optional prefix.

    Returns:
        str: The newly generated filename.
    """
    return eps_config["FILENAME_FORMAT"].format(
        file_type=file_type,
        NIT=hospital_config["NIT"],
        PREFIX=hospital_config.get("PREFIX", ""),
        invoice=invoice
    )


def extract_text_or_apply_ocr(pdf_path: str) -> None:
    """
    Tries to extract text from PDF, applies OCR if text is not found.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        None
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        apply_ocr(pdf_path)
        info_logger.info(f"OCR applied")


def handle_pdf_splitting(pdf_path: str) -> None:
    """
    Splits the PDF into individual pages and removes the original if necessary.

    Args:
        pdf_path (str): Path to the original PDF file.

    Returns:
        None
    """
    page_paths = split_pdf_by_page(pdf_path)

    if not page_paths:
        error_logger.error(f"Failed to split {pdf_path}. Skipping.")
        return

    if len(page_paths) > 1:
        try:
            os.remove(pdf_path)
            info_logger.info(f"Deleted original file after splitting: {pdf_path}")
        except Exception as e:
            error_logger.error(f"Error deleting original file {pdf_path}: {e}")
    return


def process_text_for_file_type(text: str, eps_config: Dict) -> Optional[str]:
    """
    Cleans text and determines the file type based on keywords.

    Args:
        text (str): The text to analyze.
        eps_config (Dict): Configuration dictionary containing file type mappings.

    Returns:
        Optional[str]: The determined file type, or None if no match is found.
    """
    cleaned_text = clean_text(text)
    file_type = determine_file_type(cleaned_text, eps_config["TYPES"])
    return file_type


def generate_new_file_path(pdf_path: str, file_type: str, invoice: str, eps_config: Dict, hospital_config: Dict) -> str:
    """
    Generates the new file path with the new filename.

    Args:
        pdf_path (str): Path to the original PDF file.
        file_type (str): Type of the file.
        invoice (str): Invoice number.
        eps_config (Dict): Configuration dictionary containing file type mappings.
        hospital_config (Dict): Hospital-specific configuration.

    Returns:
        str: The new file path.
    """
    new_filename = generate_new_filename(invoice, file_type, eps_config, hospital_config)
    new_pdf_path = os.path.join(os.path.dirname(pdf_path), new_filename)
    return new_pdf_path


def rename_pdfs_with_prefix(input_path: str) -> None:
    """
    Adds a temporary prefix to all PDFs in the directory.

    Args:
        input_path (str): Path to the directory containing PDFs.

    Returns:
        None
    """
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                temp_pdf_path = os.path.join(root, f"original_{file}")
                try:
                    os.rename(pdf_path, temp_pdf_path)
                except Exception as e:
                    error_logger.error(f"Error adding temporary prefix to {pdf_path}: {e}")


def split_pdfs(input_path: str) -> None:
    """
    Splits multipage PDFs into individual pages.

    Args:
        input_path (str): Path to the directory containing PDFs.

    Returns:
        None
    """
    for root, _, files in os.walk(input_path):
        for file in files:
            pdf_path = os.path.join(root, file)
            handle_pdf_splitting(pdf_path)


def process_pdfs(input_path: str) -> None:
    """
    Extracts text from PDFs or applies OCR if text extraction fails.

    Args:
        input_path (str): Path to the directory containing PDFs.

    Returns:
        None
    """
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                extract_text_or_apply_ocr(pdf_path)


def process_pdf_file(pdf_path: str, eps_config: Dict) -> Optional[Dict]:
    """
    Processes a PDF file to extract relevant information like file type, invoice number, and patient ID.

    Args:
        pdf_path (str): Path to the PDF file.
        eps_config (Dict): Configuration dictionary for file type mappings.

    Returns:
        Optional[Dict]: Dictionary with 'file_type', 'invoice', and 'patient_id', or None if errors occur.
    """
    try:
        folder_name = os.path.basename(os.path.dirname(pdf_path))
        invoice = extract_invoice_number(folder_name)

        if not invoice:
            error_logger.error(f"No valid invoice number found in folder name {folder_name}. Skipping {pdf_path}.")

        text = extract_text_from_pdf(pdf_path)

        if not text:
            error_logger.error(f"Failed to extract text from {pdf_path}. Skipping.")

        file_type = process_text_for_file_type(text, eps_config)

        if not file_type:
            error_logger.error(f"No valid keyword found in {pdf_path}. Skipping.")

        patient_id = extract_patient_id(text)

        if not patient_id:
            info_logger.warning(f"No Patient ID found in text for file type {file_type}")

        return {'file_type': file_type, 'invoice': invoice, 'patient_id': patient_id}

    except Exception as e:
        error_logger.error(f"Error processing {pdf_path}: {e}")


def combine_pdfs_by_type(file_type_to_pages: Dict[str, List[str]], eps_config: Dict, hospital_config: Dict) -> None:
    """
    Combines PDF by type and renames the combined files.

    Args:
        file_type_to_pages (Dict): Dictionary associating file types to their pages.
        eps_config (Dict): Configuration dictionary for file type mappings.
        hospital_config (Dict): Hospital-specific configuration.

    Returns:
        None
    """
    for file_type, related_pages in file_type_to_pages.items():
        combined_path = os.path.join(os.path.dirname(related_pages[0]), f"combined_{file_type}.pdf")
        combine_pdfs(related_pages, combined_path)

        invoice = extract_invoice_number(os.path.basename(os.path.dirname(related_pages[0])))
        new_pdf_path = generate_new_file_path(related_pages[0], file_type, invoice, eps_config, hospital_config)

        try:
            os.rename(combined_path, new_pdf_path)
            info_logger.info(f"Renamed {combined_path} to {new_pdf_path}")
        except Exception as e:
            error_logger.error(f"Error renaming {combined_path}: {e}")


def combine_and_rename_pdfs(input_path: str, eps_config: Dict, hospital_config: Dict) -> None:
    """
    Combines PDFs by type and renames the combined files.

    Args:
        input_path (str): Path to the input directory or file.
        eps_config (Dict): Configuration dictionary containing file type mappings.
        hospital_config (Dict): Hospital-specific configuration.

    Returns:
        None
    """
    try:
        for root, _, files in os.walk(input_path):
            file_type_to_pages = {}
            for file in files:
                pdf_path = os.path.join(root, file)
                result = process_pdf_file(pdf_path, eps_config)

                if result:
                    file_type_to_pages.setdefault(result['file_type'], []).append(pdf_path)

            if file_type_to_pages:
                combine_pdfs_by_type(file_type_to_pages, eps_config, hospital_config)

    except Exception as e:
        error_logger.error(f"Unexpected error: {e}")
