from tkinter import filedialog


def ask_open_csv(parent):
    return filedialog.askopenfilename(
        parent=parent,
        title="Select a .csv file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
