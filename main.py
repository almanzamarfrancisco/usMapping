from functools import partial
import tkinter as tk
import makeDiagrams
import json

process1_names = [  # Prospect registration
    "Catálogo y matriz de configuración",
    "Alta de prospecto",
    "Selección de tipo de contrato",
    "Registro de segmentos",
    "Admin de servicios de internet ",
    "Documentación de alta de prospecto",
    "Validación de PLD",
]
process2_names = [  # Information validation
    "Recepción de prospecto",
    "Validación de prospecto",
    "Asignación de tarjeta de internet",
    "Validación de PLD",
    "Validación de prospecto",
    "Alta de contrato",
    "Envío de Contrato para Firma",
]
process3_names = [  # Signature, activation and digitalizace
    "Recepción de Contrato Firmado",
    "Gestión de contrato",
    "Digitalización de documentos",
]
process4_names = [  # Contract modification
    "Tipo de Modificación",
    "Modificación de cliente/contrato",
    "Digitalización de documentos",
]

predefined_processes = [
    {'label': 'Alta de prospecto', 'list': process1_names},
    # {'label': 'Validación de información', 'list': process2_names},
    # {'label': 'Firma, activación y digitalización', 'list': process3_names},
    # {'label': 'Modificación de contrato', 'list': process4_names},
]


class window():
    def add_list(self):
        self.input_text = self.text_area.get("1.0", tk.END).strip()
        if self.input_text:
            # Split the input text by lines and add the list to the main list
            self.new_list = [{'label': self.process_label_entry.get(
            ), 'list': [item.strip() for item in self.input_text.split("\n")]}]
            self.main_list.append(self.new_list)
            self.listbox.configure(state='normal')
            self.listbox.insert(tk.END, json.dumps(
                self.new_list, indent='  ', ensure_ascii=False)+'\n')
            self.listbox.configure(state='disabled')
            # Clear the text area after adding the list
            self.text_area.delete("1.0", tk.END)
            self.process_label.set("")
        else:
            # If there was no input, show an error message
            self.error_label.config(
                text="Please enter a list of strings in the text area.")

    def __init__(self):
        # Create the main Tkinter window
        root = tk.Tk()
        root.title("List of Lists (Multiline)")
        # Main list to store the lists of strings
        self.main_list = []
        self.process_label = tk.StringVar()
        self.process_label_entry = tk.Entry(
            root, width=20, textvariable=self.process_label)
        self.process_label_entry.pack(pady=10)
        # Text area for inputting a list
        self.text_area = tk.Text(root, width=100, height=6)
        self.text_area.pack(pady=10)
        # "Add List" button
        add_button = tk.Button(root, text="Add List", command=self.add_list)
        add_button.pack()
        # Listbox to display the added lists
        self.listbox = tk.Text(root, width=100)
        self.listbox.pack(pady=10)
        self.listbox.insert(tk.END, json.dumps(
            predefined_processes, indent=4, ensure_ascii=False)+'\n')
        self.listbox.configure(state='disabled')
        # Error label to show any input validation errors
        self.error_label = tk.Label(root, fg="red")
        self.error_label.pack()
        # Rendering button
        render_button = tk.Button(root, text="Render", command=partial(
            makeDiagrams.render, predefined_processes))
        render_button.pack()
        # Start the Tkinter event loop
        root.mainloop()


if __name__ == '__main__':
    window()
