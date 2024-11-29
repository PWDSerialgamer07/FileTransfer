from tkinter import filedialog
import os

file = filedialog.askopenfilename()
name = file.split("/").pop()
size = os.stat(file).st_size
print(file, size, name)