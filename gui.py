import os
from pathlib import Path
from ftplib import FTP
import datetime
from tkinter import ttk, messagebox
import tkinter as tk
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\GIGABYTE\Desktop\New folder (4)\build\build\assets\frame0")

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

window = Tk()
window.title("FTP client By uki")
window.geometry("1280x720")
window.configure(bg="#2B2B2B")

ftp = None
current_ftp_path = "/"
current_local_path = "D:/"

# ================== Local File System Functions ==================
def list_local_files(path=None):
    global current_local_path
    if path:
        current_local_path = path
    
    # Clear the Treeview
    for row in local_tree.get_children():
        local_tree.delete(row)
    
    try:
        # Add ".." for parent directory (except root)
        if current_local_path != "D:/":
            local_tree.insert("", "end", values=("..", "DIR", ""), tags=("dir",))
        
        # List directory contents
        for item in os.listdir(current_local_path):
            full_path = os.path.join(current_local_path, item)
            is_dir = os.path.isdir(full_path)
            size = os.path.getsize(full_path) if not is_dir else 0
            mtime = os.path.getmtime(full_path)
            date = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            if is_dir:
                local_tree.insert("", "end", values=(item, "DIR", date), tags=("dir",))
            else:
                size_str = f"{size/1024:.2f} KB" if size > 0 else "0 KB"
                local_tree.insert("", "end", values=(item, size_str, date), tags=("file",))

    except PermissionError:
        messagebox.showerror("Permission Denied", f"Cannot access {current_local_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error listing directory: {str(e)}")

# ================== Local File System Functions ==================
def on_local_tree_double_click(event):
    item = local_tree.selection()[0]
    name = local_tree.item(item, "values")[0]
    full_path = os.path.normpath(os.path.join(current_local_path, name))
    
    if name == "..":
        new_path = os.path.dirname(current_local_path)
        list_local_files(new_path)
    elif os.path.isdir(full_path):
        list_local_files(full_path)

def local_go_back():
    if current_local_path != "D:/":
        new_path = os.path.dirname(current_local_path)
        list_local_files(new_path)

# ================== FTP Functions (Existing) ==================
def connect_to_ftp():
    global ftp, current_ftp_path
    host = entry_3.get().strip()
    username = entry_2.get().strip()
    password = entry_1.get().strip()

    try:
        ftp = FTP()
        ftp.connect(host, timeout=10)
        ftp.login(username, password)
        entry_4.insert(tk.END, "✅ Connected successfully!\n")
        list_ftp_files()
    except Exception as e:
        messagebox.showerror("Connection Error", f"Error: {str(e)}")

def list_ftp_files(path=None):
    global current_ftp_path
    for row in ftp_tree.get_children():
        ftp_tree.delete(row)
    
    try:
        if path:
            ftp.cwd(path)
            current_ftp_path = ftp.pwd()
        
# ================== Host file navigation  ==================
        if current_ftp_path != "/":
            ftp_tree.insert("", "end", values=("..", "DIR", ""), tags=("dir",))
        
        files = []
        ftp.dir(files.append)
        
        for file in files:
            parts = file.split()
            name = " ".join(parts[8:])
            ftype = "DIR" if parts[0].startswith("d") else "FILE"
            size = parts[4] if ftype == "FILE" else "0"
            date = " ".join(parts[5:8])
            ftp_tree.insert("", "end", values=(name, ftype, date))

    except Exception as e:
        messagebox.showerror("Error", f"FTP Error: {str(e)}")

# ================== Host file navigation  ==================
def on_ftp_tree_double_click(event):
    item = ftp_tree.selection()[0]
    name = ftp_tree.item(item, "values")[0]
    
    if name == "..":
        list_ftp_files("..")
    else:
        try:
            ftp.cwd(name)
            list_ftp_files()
        except:
            pass  
#========================== Download file from Host  ==================
def download_file():
    if ftp is None:
        messagebox.showerror("Error", "Not connected to FTP.")
        return
    selected = ftp_tree.selection()
    if not selected:
        messagebox.showerror("Error", "No file selected on the host.")
        return
    item = selected[0]
    name, ftype, _ = ftp_tree.item(item, 'values')
    if ftype == 'DIR':
        messagebox.showerror("Error", "Cannot download a directory.")
        return
    try:
        local_path = os.path.join(current_local_path, name)
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f'RETR {name}', f.write)

#========================== Download Path  ==================
        entry_4.insert(tk.END, f"Downloaded {name} to {current_local_path}\n")
        list_local_files()  
    except Exception as e:
        messagebox.showerror("Download Error", str(e))

#========================== Uploading file to Host  ==================
def upload_file():
    if ftp is None:
        messagebox.showerror("Error", "Not connected to FTP.")#Error Hadling
        return
    selected = local_tree.selection()
    if not selected:
        messagebox.showerror("Error", "No file selected locally.")#Error Hadling
        return
    item = selected[0]
    name = local_tree.item(item, 'values')[0]
    local_full_path = os.path.join(current_local_path, name)
    if os.path.isdir(local_full_path):
        messagebox.showerror("Error", "Cannot upload a directory.")#Error Hadling
        return
    try:
        with open(local_full_path, 'rb') as f:
            ftp.storbinary(f'STOR {name}', f)
#========================== Uploding Path  ==================
        entry_4.insert(tk.END, f"Uploaded {name} to {current_ftp_path}\n")
        list_ftp_files()  # Refresh FTP file list
    except Exception as e:
        messagebox.showerror("Upload Error", str(e))

#========================== Deleting file from the host  ==================
def delete_file():
    if ftp is None:
        messagebox.showerror("Error", "Not connected to FTP.")
        return
    selected = ftp_tree.selection()
    if not selected:#host file selaction checking
        messagebox.showerror("Error", "No file selected on the host.")
        return
    item = selected[0]
    name, ftype, _ = ftp_tree.item(item, 'values')
    if ftype == 'DIR':
        messagebox.showerror("Error", "Cannot delete a directory.")#Error Hadling
        return
    confirm = messagebox.askyesno("Confirm Delete", f"Delete {name} from host?")#Confarmtion 
    if confirm:
        try:
            ftp.delete(name)
            entry_4.insert(tk.END, f"Deleted {name} from host.\n")
            list_ftp_files()  # Refresh FTP file list
        except Exception as e:
            messagebox.showerror("Delete Error", str(e))

#========================== Main GUI part(This is made by using custom tinker)  ==================
canvas = Canvas(
    window,
    bg = "#2B2B2B",
    height = 720,
    width = 1280,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)
image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    104.0,
    102.0,
    image=image_image_1
)

canvas.create_text(
    250.0,
    19.0,
    anchor="nw",
    text="Host: ",
    fill="#FFFFFF",
    font=("JetBrainsMono ExtraBold", 20 * -1)
)

canvas.create_text(
    74.0,
    205.0,
    anchor="nw",
    text="User files",
    fill="#FFFFFF",
    font=("JetBrainsMono ExtraBold", 20 * -1)
)

canvas.create_text(
    58.0,
    569.0,
    anchor="nw",
    text="Logs",
    fill="#FFFFFF",
    font=("JetBrainsMono ExtraBold", 20 * -1)
)

canvas.create_text(
    1106.0,
    205.0,
    anchor="nw",
    text="Host files",
    fill="#FFFFFF",
    font=("JetBrainsMono ExtraBold", 20 * -1)
)

canvas.create_text(
    728.0,
    13.0,
    anchor="nw",
    text="Password: ",
    fill="#FFFFFF",
    font=("JetBrainsMono ExtraBold", 20 * -1)
)

canvas.create_text(
    479.0,
    19.0,
    anchor="nw",
    text="Username:",
    fill="#FFFFFF",
    font=("JetBrainsMono ExtraBold", 20 * -1)
)

entry_image_1 = PhotoImage(
    file=relative_to_assets("entry_1.png"))
entry_bg_1 = canvas.create_image(
    819.5,
    68.0,
    image=entry_image_1
)
entry_1 = Entry(
    bd=0,
    bg="#D9D9D9",
    fg="#000716",
    highlightthickness=0
)
entry_1.place(
    x=745.0,
    y=51.0,
    width=149.0,
    height=32.0
)

entry_image_2 = PhotoImage(
    file=relative_to_assets("entry_2.png"))
entry_bg_2 = canvas.create_image(
    570.5,
    68.0,
    image=entry_image_2
)
entry_2 = Entry(
    bd=0,
    bg="#D9D9D9",
    fg="#000716",
    highlightthickness=0
)
entry_2.place(
    x=496.0,
    y=51.0,
    width=149.0,
    height=32.0
)

entry_image_3 = PhotoImage(
    file=relative_to_assets("entry_3.png"))
entry_bg_3 = canvas.create_image(
    327.5,
    68.0,
    image=entry_image_3
)
entry_3 = Entry(
    bd=0,
    bg="#D9D9D9",
    fg="#000716",
    highlightthickness=0
)
entry_3.place(
    x=253.0,
    y=51.0,
    width=149.0,
    height=32.0
)

#========================== Downloading Button  ==================
button_image_1 = PhotoImage(
    file=relative_to_assets("button_1.png"))
button_1 = Button(
    image=button_image_1,
    borderwidth=0,
    highlightthickness=0,
    command=download_file,
    relief="flat"
)
button_1.place(
    x=533.0,
    y=288.0,
    width=182.0,
    height=45.0
)

#========================== Uplaoding Button  ==================
button_image_2 = PhotoImage(
    file=relative_to_assets("button_2.png"))
button_2 = Button(
    image=button_image_2,
    borderwidth=0,
    highlightthickness=0,
    command=upload_file,
    relief="flat"
)
button_2.place(
    x=533.0,
    y=353.0,
    width=182.0,
    height=45.0
)

#========================== Delete Button  ==================
button_image_3 = PhotoImage(
    file=relative_to_assets("button_3.png"))
button_3 = Button(
    image=button_image_3,
    borderwidth=0,
    highlightthickness=0,
    command=delete_file,  
    relief="flat"
)
button_3.place(
    x=533.0,
    y=418.0,
    width=182.0,
    height=45.0
)

entry_image_4 = PhotoImage(
    file=relative_to_assets("entry_4.png"))
entry_bg_4 = canvas.create_image(
    630.0,
    645.5,
    image=entry_image_4
)
entry_4 = Text(
    bd=0,
    bg="#6C6C6C",
    fg="#F5F5F7",
    highlightthickness=0
)
entry_4.place(
    x=68.0,
    y=595.0,
    width=1150.0,
    height=99.0
)

entry_image_5 = PhotoImage(
    file=relative_to_assets("entry_5.png"))
entry_bg_5 = canvas.create_image(
    279.5,
    397.5,
    image=entry_image_5
)

#========================== Making Host and user File structher  ==================

local_tree = ttk.Treeview(window, columns=("Name", "Size", "Date"), show="headings")
local_tree.heading("Name", text="Name")
local_tree.heading("Size", text="Size")
local_tree.heading("Date", text="Modified Date")
local_tree.column("Name", width=200)
local_tree.column("Size", width=100)
local_tree.column("Date", width=150)
local_tree.place(x=73, y=246, width=413, height=301)
local_tree.bind("<Double-1>", on_local_tree_double_click)

# Local back button
local_back_btn = Button(
    window,
    text="← Back",
    command=local_go_back,
    bg="#4A4A4A",
    fg="white"
)
local_back_btn.place(x=400, y=560, width=80, height=30)

# FTP Treeview (right side)
ftp_tree = ttk.Treeview(window, columns=("Name", "Type", "Date"), show="headings")
ftp_tree.heading("Name", text="Name")
ftp_tree.heading("Type", text="Type")
ftp_tree.heading("Date", text="Date")
ftp_tree.column("Name", width=200)
ftp_tree.column("Type", width=100)
ftp_tree.column("Date", width=150)
ftp_tree.place(x=775, y=240, width=436, height=307)
ftp_tree.bind("<Double-1>", on_ftp_tree_double_click)


# Loading local files on startup
list_local_files("D:/")

#========================== Connecting Button  ==================

button_image_4 = PhotoImage(
    file=relative_to_assets("button_4.png"))
button_4 = Button(
    image=button_image_4,
    borderwidth=0,
    highlightthickness=0,
    command=connect_to_ftp,
    relief="flat"
)
button_4.place(
    x=998.0,
    y=41.0,
    width=182.0,
    height=45.0
)
window.resizable(False, False)
window.mainloop()
