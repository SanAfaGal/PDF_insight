# PDF Processor for EPS Files

A Python-based application designed to process and rename PDF files based on EPS-specific configurations. The tool leverages exact and fuzzy matching techniques to identify file types, apply OCR for text extraction, and supports splitting and combining PDFs.

## Features 🚀
- **Automatic PDF Renaming**: Renames files using EPS-specific naming conventions.
- **Text Extraction**: Extracts text from PDFs using PyPDF2 and OCR.
- **File Type Identification**: Uses exact and fuzzy matching for robust keyword detection.
- **PDF Splitting and Combining**: Handles multi-page PDFs by splitting and recombining files as needed.

## Technologies 🛠️
- **Python 3.x**
- **PyPDF2**: For PDF text extraction and manipulation.
- **ocrmypdf**: Adds OCR to non-searchable PDFs.
- **rapidfuzz**: Implements fuzzy matching for text processing.
- **logging**: For structured application logging.

## Prerequisites 🔧

### 1. Install Tesseract
Download and install Tesseract OCR from [UB-Mannheim's Tesseract repository](https://github.com/UB-Mannheim/tesseract/wiki).  
After installation, add the following to your system's **Environment Variables** (PATH):
```
C:\Program Files\Tesseract-OCR
```

### 2. Install Ghostscript
Download and install Ghostscript from the [official Ghostscript website](https://ghostscript.com/releases/gsdnld.html).  
After installation, add the `bin` directory to your system's **Environment Variables** (PATH):
```
C:\Program Files\gs\gs10.04.0\bin
```

### 3. Verify Installations
Run the following commands in a terminal to verify installations:
```bash
tesseract --version
gswin64c --version
```

## Installation 📦

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. **Set up a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage 📋

### CLI Arguments
- `eps_name`: The EPS name to process the files for (e.g., "NUEVA EPS").
- `input_path`: Path to the folder or file to process.

### Example Command
```bash
python main.py "NUEVA EPS" "/path/to/input/folder"
```

## EPS Configuration 🏥
The application supports multiple EPS configurations, such as:
- **NUEVA EPS**
- **SALUD TOTAL**

Each configuration includes:
- Keywords for file type identification.
- Customizable naming conventions.

## Logging 📄
Logs are generated in the following files:
- `info.log`: General process information.
- `error.log`: Errors encountered during processing.
