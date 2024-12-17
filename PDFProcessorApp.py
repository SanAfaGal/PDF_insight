import tkinter as tk
from tkinter import filedialog, messagebox
import os

# Importar tus funciones existentes
from main import rename_pdfs_with_prefix, split_pdfs, process_pdfs, combine_and_rename_pdfs, EPS_CONFIG


class PDFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Processor")

        # Variables para las acciones seleccionadas
        self.rename_var = tk.BooleanVar(value=False)
        self.split_var = tk.BooleanVar(value=False)
        self.ocr_var = tk.BooleanVar(value=False)
        self.combine_var = tk.BooleanVar(value=False)

        # Configuración de EPS
        self.eps_name_var = tk.StringVar(value="NUEVA EPS")

        # Ruta de entrada
        self.input_path = ""

        # Interfaz gráfica
        self.create_widgets()

    def create_widgets(self):
        # Sección para elegir la ruta de entrada
        tk.Label(self.root, text="Select Input Folder/File:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Button(self.root, text="Browse", command=self.select_input_path).grid(row=0, column=1, padx=10, pady=5)
        self.path_label = tk.Label(self.root, text="No path selected", fg="gray")
        self.path_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10)

        # EPS Selection
        tk.Label(self.root, text="Select EPS:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        eps_options = list(EPS_CONFIG.keys())
        tk.OptionMenu(self.root, self.eps_name_var, *eps_options).grid(row=2, column=1, padx=10, pady=5)

        # Acciones (Checkbuttons)
        tk.Label(self.root, text="Select Actions:").grid(row=3, column=0, sticky="w", padx=10, pady=5)

        tk.Checkbutton(self.root, text="Rename PDFs with Prefix", variable=self.rename_var).grid(row=4, column=0,
                                                                                                 sticky="w", padx=20)
        tk.Checkbutton(self.root, text="Split PDFs into Pages", variable=self.split_var).grid(row=5, column=0,
                                                                                              sticky="w", padx=20)
        tk.Checkbutton(self.root, text="Extract Text or Apply OCR", variable=self.ocr_var).grid(row=6, column=0,
                                                                                                sticky="w", padx=20)
        tk.Checkbutton(self.root, text="Combine and Rename PDFs", variable=self.combine_var).grid(row=7, column=0,
                                                                                                  sticky="w", padx=20)

        # Botón para ejecutar las acciones seleccionadas
        tk.Button(self.root, text="Run Selected Actions", command=self.run_selected_actions).grid(row=8, column=0,
                                                                                                  columnspan=2, pady=10)

        # Salida de logs
        self.log_text = tk.Text(self.root, height=10, width=60, state=tk.DISABLED)
        self.log_text.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

    def select_input_path(self):
        """Permite al usuario seleccionar una carpeta o archivo."""
        self.input_path = filedialog.askdirectory()  # Puedes usar askopenfilename para archivos
        if self.input_path:
            self.path_label.config(text=self.input_path, fg="black")
        else:
            self.path_label.config(text="No path selected", fg="gray")

    def log_message(self, message):
        """Muestra mensajes en el área de logs."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def run_selected_actions(self):
        """Ejecuta las acciones seleccionadas por el usuario."""
        if not self.input_path:
            messagebox.showerror("Error", "Please select an input folder or file.")
            return

        eps_name = self.eps_name_var.get()
        eps_config = EPS_CONFIG.get(eps_name)

        if not eps_config:
            messagebox.showerror("Error", f"Invalid EPS configuration: {eps_name}")
            return

        try:
            # Ejecutar las acciones en orden
            if self.rename_var.get():
                self.log_message("Renaming PDFs with prefix...")
                rename_pdfs_with_prefix(self.input_path)

            if self.split_var.get():
                self.log_message("Splitting PDFs into pages...")
                split_pdfs(self.input_path)

            if self.ocr_var.get():
                self.log_message("Extracting text or applying OCR...")
                process_pdfs(self.input_path, eps_config)

            if self.combine_var.get():
                self.log_message("Combining and renaming PDFs...")
                combine_and_rename_pdfs(self.input_path, eps_config)

            self.log_message("All selected actions completed successfully.")
            messagebox.showinfo("Success", "Selected actions completed successfully!")

        except Exception as e:
            self.log_message(f"Error: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()
