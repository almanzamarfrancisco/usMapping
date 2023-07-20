from tkinter import messagebox
from tkinter import ttk
from tkinter import *
import json
import makeDiagrams


class windowLayout:
    def __init__(self) -> None:
        root = Tk()
        root.title("User Stories Mapping")

        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        ttk.Label(mainframe, text="Processes: ").grid(
            column=0, row=0, sticky=W)
        self.inputBox = Text(mainframe, height=30, width=75,
                             bg="gray", padx=2, pady=2)
        self.inputBox.grid(column=0, row=3, columnspan=5)
        self.inputBox.insert(
            END, f"{json.dumps(makeDiagrams.process1_names, indent='   ', ensure_ascii=False)}")
        self.inputBox.insert(
            END, f"{json.dumps(makeDiagrams.process2_names, indent='   ', ensure_ascii=False)}")
        self.inputBox.insert(
            END, f"{json.dumps(makeDiagrams.process3_names, indent='   ', ensure_ascii=False)}")
        self.inputBox.insert(
            END, f"{json.dumps(makeDiagrams.process4_names, indent='   ', ensure_ascii=False)}")

        ttk.Button(mainframe, text="Load diagrams",
                   command=makeDiagrams.init).grid(column=0, row=7, sticky=W)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        root.mainloop()


if __name__ == '__main__':
    windowLayout()
