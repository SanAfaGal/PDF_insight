import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import os
import threading  # Para no bloquear la interfaz mientras se procesan los archivos

# Importar las funciones principales del script
from config import EPS_CONFIG
from main import process_input


class PDFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Processor for EPS")
        self.root.geometry("600x400")
        self.create_widgets()

    def create_widgets(self):
        # Etiqueta y ComboBox para EPS
        tk.Label(self.root, text="Select EPS:", font=("Arial", 12)).pack(pady=10)
        self.eps_combo = ttk.Combobox(self.root, values=list(EPS_CONFIG.keys()), state="readonly", width=30)
        self.eps_combo.pack(pady=5)
        self.eps_combo.current(0)  # Seleccionar la primera opción por defecto

        # Botón para seleccionar carpeta
        tk.Label(self.root, text="Select Folder:", font=("Arial", 12)).pack(pady=10)
        self.folder_entry = tk.Entry(self.root, width=50)
        self.folder_entry.pack(pady=5)
        tk.Button(self.root, text="Browse", command=self.select_folder).pack(pady=5)

        # Botón de Procesar
        tk.Button(self.root, text="Process PDFs", command=self.run_processing, bg="green", fg="white").pack(pady=10)

        # Área de logs
        tk.Label(self.root, text="Logs:", font=("Arial", 12)).pack(pady=5)
        self.log_area = scrolledtext.ScrolledText(self.root, width=70, height=10)
        self.log_area.pack(pady=5)

    def select_folder(self):
        folder_selected = filedialog.askdirectory(title="Select Folder Containing PDFs")
        if folder_selected:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)

    def run_processing(self):
        # Recuperar valores seleccionados
        eps_name = self.eps_combo.get()
        input_path = self.folder_entry.get()

        if not input_path or not os.path.exists(input_path):
            self.log("Please select a valid folder path.")
            return

        self.log(f"Processing started for EPS: {eps_name}, Folder: {input_path}")

        # Ejecutar el proceso en un hilo separado para no congelar la interfaz
        threading.Thread(target=self.process_pdfs, args=(eps_name, input_path)).start()

    def process_pdfs(self, eps_name, input_path):
        try:
            process_input(input_path, eps_name)
            self.log("Processing completed successfully!")
        except Exception as e:
            self.log(f"Error: {e}")

    def log(self, message):
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()
