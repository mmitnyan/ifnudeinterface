import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, UnidentifiedImageError
from ifnude import detect

def list_images(directory, progress_var):
    image_files = []
    error_files = []
    total_files = sum([len(files) for r, d, files in os.walk(directory)])
    progress_var.set(0)
    step = 100 / total_files  # Calcule la valeur de l'étape de progression

    for root, dirs, files in os.walk(directory):
        for file in files:
            progress_var.set(progress_var.get() + step)
            progress_bar.update()
            print (progress_var.get() + step)
            #if (progress_var.get() + step  >= 100 ):
            # progress_label = ttk.Label(frame, text="allo toi")
            #    progress_var.set(0)
            #    progress_bar.update()            
            #    print ("allo toi")
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                file_path = os.path.join(root, file)
                try:
                    detections = detect(file_path, 'fast', 0.3)  # Utiliser `detect` pour filtrer les images
                    if detections:
                        for detection in detections:
                            normalized_path = os.path.normpath(file_path)
                            image_files.append((normalized_path, detection['score'], detection['label']))
                except (OSError, UnidentifiedImageError) as e:
                    print(f"Erreur lors du traitement de {file_path}: {e}")
                    normalized_path = os.path.normpath(file_path)
                    error_files.append(normalized_path)

    progress_var.set(0)  # Assurer que la barre de progression atteint 0%
    progress_bar.update()
    
    return image_files, error_files

def show_images(root, frame, image_files, error_files):
    # Treeview pour les images réussies
    columns = ('image', 'file_path', 'score', 'reason')
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    tree.heading('image', text='Image')
    tree.heading('file_path', text='File Path', command=lambda: sort_treeview_column(tree, 'file_path', False))
    tree.heading('score', text='Score', command=lambda: sort_treeview_column(tree, 'score', False))
    tree.heading('reason', text='Reason', command=lambda: sort_treeview_column(tree, 'reason', False))

    tree.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))  # Image reussi definit les collones

    scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar_y.grid(row=2, column=4, sticky=(tk.N, tk.S))
    tree['yscrollcommand'] = scrollbar_y.set

    scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
    scrollbar_x.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E))
    tree['xscrollcommand'] = scrollbar_x.set

    #preview_label = ttk.Label(frame)
    #preview_label.grid(row=2, column=5, padx=10, pady=10, sticky=(tk.S, tk.E))

    go_to_dir_btn = ttk.Button(frame, text="Go to Directory", state=tk.DISABLED)
    go_to_dir_btn.grid(row=2, column=5, padx=10, pady=50, sticky=(tk.S, tk.E))

    # Treeview pour les fichiers en erreur
    error_columns = ('file_path',)
    error_tree = ttk.Treeview(frame, columns=error_columns, show='headings')
    error_tree.heading('file_path', text='Error File Path')
    error_tree.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

    error_scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=error_tree.yview)
    error_scrollbar_y.grid(row=4, column=4, sticky=(tk.N, tk.S))
    error_tree['yscrollcommand'] = error_scrollbar_y.set

    delete_selected_btn = ttk.Button(frame, text="Delete Selected", state=tk.DISABLED, command=lambda: delete_selected_files(error_tree))
    delete_selected_btn.grid(row=4, column=5, padx=10, pady=50, sticky=(tk.S, tk.E))

    # Footer
    file_count_label = ttk.Label(frame, text=f"Number of files found: {len(image_files)}")
    file_count_label.grid(row=5, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.S))

    error_file_count_label = ttk.Label(frame, text=f"Number of error files: {len(error_files)}")
    error_file_count_label.grid(row=6, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.S))

    image_previews = {}
    for file_path, score, reason in image_files:
        try:
            file_name = os.path.basename(file_path)  # Extraire le nom du fichier
            tree.insert('', tk.END, values=(file_name, file_path, score, reason))
        except (OSError, UnidentifiedImageError) as e:
            print(f"Erreur lors du traitement de l'image {file_path}: {e}")
            continue  # Passer au fichier suivant en cas d'erreur

    for error_file in error_files:
        error_tree.insert('', tk.END, values=(error_file,))

    def on_select(event):
        selected_item = tree.selection()[0]
        selected_image = tree.item(selected_item, 'values')[1]  # Utiliser l'index correct pour file_path
        image = Image.open(selected_image)
        image.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(image)
        preview_label.config(image=photo)
        preview_label.image = ''
        preview_label.image = photo
        normalized_path = os.path.normpath(os.path.dirname(selected_image))
        go_to_dir_btn.config(command=lambda: open_directory(normalized_path))
        go_to_dir_btn.config(state=tk.NORMAL)

    def on_error_select(event):
        selected_item = error_tree.selection()[0]
        selected_error_file = error_tree.item(selected_item, 'values')[0]
        normalized_path = os.path.normpath(os.path.dirname(selected_error_file))
        error_go_to_dir_btn.config(command=lambda: open_directory(normalized_path))
        error_go_to_dir_btn.config(state=tk.NORMAL)
        delete_selected_btn.config(state=tk.NORMAL)

    def delete_selected_files(tree):
        selected_items = tree.selection()
        for selected_item in selected_items:
            selected_file = tree.item(selected_item, 'values')[0]
            try:
                os.remove(selected_file)
                tree.delete(selected_item)
            except OSError as e:
                messagebox.showerror("Error", f"Unable to delete {selected_file}: {e}")
        delete_selected_btn.config(state=tk.DISABLED)

    def sort_treeview_column(treeview, col, reverse):
        data = [(treeview.set(k, col), k) for k in treeview.get_children('')]
        data.sort(reverse=reverse)

        for index, (val, k) in enumerate(data):
            treeview.move(k, '', index)

        treeview.heading(col, command=lambda: sort_treeview_column(treeview, col, not reverse))

    tree.bind('<<TreeviewSelect>>', on_select)
    error_tree.bind('<<TreeviewSelect>>', on_error_select)

def open_directory(directory):
    os.startfile(directory)

def select_directory():
    directory = filedialog.askdirectory(title="Sélectionner un répertoire")
    if directory:
        #root.title("Scanning Progress")
        preview_label.image = ''
        #progress_label = ttk.Label(frame, text="Please wait")
        progress_var.set(0)
        progress_bar.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))
        #progress_label.grid(row=0, column=1, padx=10, sticky=(tk.W, tk.E))
        root.update_idletasks()
        image_files, error_files = list_images(directory, progress_var)
        show_images(root, frame, image_files, error_files)

if __name__ == "__main__":



    root = tk.Tk()
    root.title("Image Viewer")
    original_width = 800
    original_height = 400
    root.geometry(f"{original_width * 2}x{original_height * 2}")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
    progress_bar.grid(row=0, column=0, padx=10, pady=10, sticky=(tk.W, tk.E))

    #progress_label = ttk.Label(frame, text="")
    #progress_label.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))

    select_dir_btn = ttk.Button(frame, text="Select Directory", command=select_directory)
    select_dir_btn.grid(row=0, column=5, padx=10, pady=10, sticky=(tk.W, tk.E))
    
    #delete_selected_btn = ttk.Button(frame, text="Delete Selected", state=tk.DISABLED, command=lambda: delete_selected_files(error_tree))
    #delete_selected_btn.grid(row=4, column=5, padx=10, pady=50, sticky=(tk.S, tk.E))

    error_go_to_dir_btn = ttk.Button(frame, text="Go to Error Directory", state=tk.DISABLED)
    error_go_to_dir_btn.grid(row=4, column=5, padx=10, pady=75, sticky=(tk.S, tk.E))




    preview_label = ttk.Label(frame)
    preview_label.grid(row=2, column=5, padx=10, pady=80, sticky=(tk.S, tk.E))

    show_images(root, frame, '', '')

    root.mainloop()
