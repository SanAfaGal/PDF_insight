import argparse
import logging
import os
import re

import ocrmypdf
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError
from rapidfuzz import fuzz
from unidecode import unidecode


# --- Logging Configuration ---
def setup_logging():
    """Sets up logging for the application."""
    logging.basicConfig(level=logging.INFO)
    info_logger = logging.getLogger("info_logger")
    error_logger = logging.getLogger("error_logger")

    # Handlers
    info_handler = logging.FileHandler("info.log")
    error_handler = logging.FileHandler("error.log")

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Assign levels
    info_handler.setLevel(logging.INFO)
    error_handler.setLevel(logging.ERROR)

    info_logger.addHandler(info_handler)
    error_logger.addHandler(error_handler)

    return info_logger, error_logger


info_logger, error_logger = setup_logging()

# --- Constants ---
DEFAULT_NIT = "890702241"
DEFAULT_PREFIX = "ELE"

EPS_CONFIG = {
    "NUEVA EPS": {
        "NIT": DEFAULT_NIT,
        "PREFIX": DEFAULT_PREFIX,
        "KEYWORDS": {
            "FVS": ["PERIODO FACTURADO", "FACTURA DE VENTA ELECTRONICA"],
            "EPI": ["HISTORIA ELECTRONICA", "REGISTRO PROFESIONAL", "NOTAS"],
            "OTR": ["CONSULTA DEL ESTADO DE AFILIACION",
                    "RESOLUCION NO",
                    "TRASLADO ASISTENCIAL",
                    "AUTORIZAR OTROS SERVICIOS",
                    "AUTORIZACION SERVICIOS",
                    "FORMATO DE BITACORA DE REMISIONES",
                    "CODIGO DESCRIPCION",
                    "SOLICITUD AUTORIZACION"],
            "OPF": ["ORDENACION DE PROCEDIMIENTOS", "ORDENES MEDICAS", "ORDEN MEDICA DE EGRESO"],
            "CRC": ["COMPROBANTE DE RECIBIDO DE SERVICIOS MEDICOS"],
            # "PDX": [""],
        },
        "FILENAME_FORMAT": "{file_type}_{NIT}_{PREFIX}{invoice}.pdf"
    },
    "SALUD TOTAL": {
        "NIT": DEFAULT_NIT,
        "PREFIX": DEFAULT_PREFIX,
        "SUFFIX": "1",
        "KEYWORDS": {
            1: ["PERIODO FACTURADO", "FACTURA DE VENTA ELECTRONICA"],
            5: ["HISTORIA ELECTRONICA"],
            14: ["FORMATO DE BITACORA DE REMISIONES"],
            15: ["COMPROBANTE DE RECIBIDO DE SERVICIOS MEDICOS"],
            17: ["ADRES"]
        },
        "FILENAME_FORMAT": "{NIT}_{PREFIX}_{invoice}_{file_type}_{SUFFIX}.pdf"
    }
}


# --- Utility Functions ---
def clean_path(path):
    """Removes enclosing single or double quotation marks from a file path."""
    return path.strip("'\"")


def extract_invoice_number(folder_name):
    """Extracts the first numeric value from the folder name."""
    match = re.search(r'\d+', folder_name)
    return match.group(0) if match else None


def clean_text(text):
    """Removes extra whitespace from text. Returns empty string if text is None."""
    return re.sub(r'\s{2,}', ' ', text) if text else ""


# --- PDF Processing ---
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF using PyPDF2."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            # writer = PdfWriter()
            # for page in reader.pages:
                # print("rotation:" + str(page.get('/Rotate')))
                # page.rotate(0)
                # writer.add_page(page)

            # with open(pdf_path, "wb") as corrected_file:
            #     writer.write(corrected_file)

            return "".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as e:
        error_logger.error(f"Error reading PDF {pdf_path}: {e}")
    except Exception as e:
        error_logger.error(f"Unexpected error extracting text from {pdf_path}: {e}")
    return None


def apply_ocr(pdf_path):
    """Applies OCR to a PDF and returns the path to the searchable PDF."""
    try:
        output_path = f"{os.path.splitext(pdf_path)[0]}_searchable.pdf"
        ocrmypdf.ocr(pdf_path, output_path, deskew=True)
        os.remove(pdf_path)
        return output_path
    except Exception as e:
        error_logger.error(f"Error applying OCR to {pdf_path}: {e}")
        return None


def split_pdf_by_page(pdf_path):
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


def combine_pdfs(pdf_paths, output_path):
    """Combines multiple PDFs into a single PDF file."""
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
        # Optionally, remove original files after combining
        for pdf_path in pdf_paths:
            os.remove(pdf_path)
    except Exception as e:
        error_logger.error(f"Error combining PDFs {pdf_paths}: {e}")


def determine_file_type(text, keywords, similarity_threshold=80):
    """Determines the file type based on keywords and fuzzy matching."""
    normalized_text = unidecode(text).lower()
    for file_type, keyword_list in keywords.items():
        for keyword in keyword_list:
            normalized_keyword = unidecode(keyword).lower()
            if normalized_keyword in normalized_text:
                return file_type
            if fuzz.partial_ratio(normalized_text, normalized_keyword) >= similarity_threshold:
                return file_type
    return None


# --- File Renaming ---
def generate_new_filename(invoice, file_type, eps_config):
    """Generates a new filename based on EPS configuration."""
    return eps_config["FILENAME_FORMAT"].format(
        file_type=file_type,
        NIT=eps_config["NIT"],
        PREFIX=eps_config["PREFIX"],
        invoice=invoice,
        SUFFIX=eps_config.get("SUFFIX", "")
    )


# --- Utility Functions ---
def extract_text_or_apply_ocr(pdf_path):
    """Tries to extract text from PDF, applies OCR if text is not found."""
    text = extract_text_from_pdf(pdf_path)
    if not text:
        ocr_pdf_path = apply_ocr(pdf_path)
        if ocr_pdf_path:
            pdf_path = ocr_pdf_path
            info_logger.info(f"OCR applied, new file is {pdf_path}")
            text = extract_text_from_pdf(pdf_path)
        else:
            error_logger.error(f"Failed to apply OCR to {pdf_path}. Skipping.")
            return None, None
    return text, pdf_path


def handle_pdf_splitting(pdf_path):
    """Splits the PDF into individual pages and removes the original if necessary."""
    page_paths = split_pdf_by_page(pdf_path)
    if not page_paths:
        error_logger.error(f"Failed to split {pdf_path}. Skipping.")
        return None
    if len(page_paths) > 1:
        try:
            os.remove(pdf_path)
            info_logger.info(f"Deleted original file after splitting: {pdf_path}")
        except Exception as e:
            error_logger.error(f"Error deleting original file {pdf_path}: {e}")
    return page_paths


def process_text_for_file_type(text, eps_config):
    """Cleans text and determines the file type based on keywords."""
    cleaned_text = clean_text(text)
    file_type = determine_file_type(cleaned_text, eps_config["KEYWORDS"])
    return file_type


def generate_new_file_path(pdf_path, file_type, invoice, eps_config):
    """Generates the new file path with the new filename."""
    new_filename = generate_new_filename(invoice, file_type, eps_config)
    new_pdf_path = os.path.join(os.path.dirname(pdf_path), new_filename)
    return new_pdf_path


# --- Main Processing ---
def process_input(input_path, eps_name):
    """Processes a folder or single PDF file and renames files based on EPS configuration."""
    eps_config = EPS_CONFIG.get(eps_name)
    if not eps_config:
        error_logger.error(f"Unsupported EPS: {eps_name}")
        return

    if os.path.isdir(input_path):
        # Add a prefix to all PDFs before processing
        rename_pdfs_with_prefix(input_path)

        # Split PDF files if necessary
        split_pdfs(input_path)

        # Extract text or apply OCR if text extraction fails
        process_pdfs(input_path, eps_config)

        # Combine PDFs by file type, rename, and handle the output
        combine_and_rename_pdfs(input_path, eps_config)

    else:
        error_logger.error(f"Invalid path: {input_path}")


def rename_pdfs_with_prefix(input_path):
    """Adds a temporary prefix to all PDFs in the directory."""
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                temp_pdf_path = os.path.join(root, f"original_{file}")
                try:
                    os.rename(pdf_path, temp_pdf_path)
                except Exception as e:
                    error_logger.error(f"Error adding temporary prefix to {pdf_path}: {e}")


def split_pdfs(input_path):
    """Splits multi-page PDFs into individual pages."""
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.startswith('original_') and file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                page_paths = handle_pdf_splitting(pdf_path)


def process_pdfs(input_path, eps_config):
    """Extracts text from PDFs or applies OCR if text extraction fails."""
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                text, pdf_path = extract_text_or_apply_ocr(pdf_path)


def combine_and_rename_pdfs(input_path, eps_config):
    """Combines PDFs by file type and renames the output file."""
    file_type_to_pages = {}
    for root, _, files in os.walk(input_path):
        for file in files:
            folder_name = os.path.basename(root)
            invoice = extract_invoice_number(folder_name)
            if not invoice:
                error_logger.error(f"No valid invoice number found in folder name {folder_name}. Skipping {file}.")
                continue

            pdf_path = os.path.join(root, file)
            text = extract_text_from_pdf(pdf_path)

            if not text:
                error_logger.error(f"Failed to extract text from {pdf_path}. Skipping.")
                continue

            file_type = process_text_for_file_type(text, eps_config)
            if not file_type:
                error_logger.error(f"No valid keyword found in {pdf_path}. Skipping.")
                continue

            file_type_to_pages.setdefault(file_type, []).append(pdf_path)

    for file_type, related_pages in file_type_to_pages.items():
        combined_path = os.path.join(os.path.dirname(pdf_path), f"combined_{file_type}.pdf")
        combine_pdfs(related_pages, combined_path)

        new_pdf_path = generate_new_file_path(pdf_path, file_type, invoice, eps_config)
        try:
            os.rename(combined_path, new_pdf_path)
            info_logger.info(f"Renamed {combined_path} to {new_pdf_path}")
        except Exception as e:
            error_logger.error(f"Error renaming {combined_path}: {e}")


# --- Entry Point ---
def main():
    """Main entry point of the script."""
    parser = argparse.ArgumentParser(description="Process and rename PDFs based on EPS configurations.")
    parser.add_argument("eps_name", help="EPS name", choices=EPS_CONFIG.keys())
    parser.add_argument("input_path", help="Path to a folder or a single file")
    args = parser.parse_args()

    input_path = clean_path(args.input_path)
    if not os.path.exists(input_path):
        print(f"The path '{input_path}' does not exist. Exiting.")
        return

    process_input(input_path, args.eps_name)


if __name__ == "__main__":
    import sys

    # Valores por defecto para pruebas
    if len(sys.argv) == 1:
        eps = "NUEVA EPS"
        file = r"D:\HOSPITAL\NUEVA EPS\SUBSIDIADO\ELE46339"
        sys.argv.extend([eps, file])

    main()
