"""Native desktop UI; calls the local library in-process, without an HTTP server."""
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk
from app import app, DATA


def library_request(path, **kwargs):
    with app.test_client() as client:
        response = client.open(path, **kwargs)
        result = response.get_json()
        if response.status_code >= 400:
            raise ValueError((result or {}).get('error', 'Library operation failed'))
        return result


def import_files(paths, mode='Balanced'):
    results = []
    for path in paths:
        try:
            with open(path, 'rb') as source:
                results.extend(library_request('/api/upload', method='POST',
                    data={'images': (source, Path(path).name), 'mode': mode}))
        except Exception as error:
            results.append({'name': Path(path).name, 'ok': False, 'error': str(error)})
    return results


class FaceLibrary(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Face Library')
        self.geometry('1080x780')
        self.minsize(760, 580)
        self.photos = []
        self.visible = []
        self.images = []
        self.jobs = queue.Queue()
        self.busy = False
        self.selected_id = None
        top = ttk.Frame(self, padding=16)
        top.pack(fill='x')
        ttk.Label(top, text='Face Library', font=('Segoe UI', 24, 'bold')).pack(anchor='w')
        ttk.Label(top, text='Detect faces and add person tags manually. Photos stay on this computer.').pack(anchor='w', pady=(4, 12))
        self.import_button = ttk.Button(top, text='Import photos…', command=self.choose_files)
        self.import_button.pack(side='left')
        ttk.Label(top, text='   Show: ').pack(side='left')
        self.filter = ttk.Combobox(top, state='readonly', width=28)
        self.filter.pack(side='left')
        self.filter.bind('<<ComboboxSelected>>', lambda event: self.render_list())
        settings = ttk.Frame(self, padding=(16, 0, 16, 10))
        settings.pack(fill='x')
        ttk.Label(settings, text='Detection for new imports: ').pack(side='left')
        self.mode = ttk.Combobox(settings, state='readonly', values=['Strict', 'Balanced', 'Sensitive'], width=12)
        self.mode.set('Balanced')
        self.mode.pack(side='left')
        ttk.Label(settings, text='  Strict: fewer false faces · Sensitive: more faces, more false detections').pack(side='left')
        split = ttk.Panedwindow(self, orient='horizontal')
        split.pack(fill='both', expand=True, padx=16)
        left = ttk.Frame(split)
        self.listbox = tk.Listbox(left, width=32, exportselection=False)
        scrollbar = ttk.Scrollbar(left, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.listbox.pack(fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.select_photo)
        split.add(left, weight=1)
        right = ttk.Frame(split)
        self.canvas = tk.Canvas(right, highlightthickness=0)
        scroll = ttk.Scrollbar(right, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.detail = ttk.Frame(self.canvas, padding=16)
        window = self.canvas.create_window((0, 0), window=self.detail, anchor='nw')
        self.detail.bind('<Configure>', lambda event: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda event: self.canvas.itemconfigure(window, width=event.width))
        split.add(right, weight=3)
        self.status = tk.StringVar(value='Import photos to begin. No browser or server is needed.')
        ttk.Label(self, textvariable=self.status, padding=16, wraplength=1000).pack(fill='x')
        self.refresh()
        self.after(100, self.poll_jobs)
        self.protocol('WM_DELETE_WINDOW', self.close)

    def refresh(self):
        self.photos = library_request('/api/photos')
        tags = sorted({face['tag'] for p in self.photos for face in p['faces'] if face['tag']})
        previous = self.filter.get()
        choices = ['All photos', 'Photos with untagged faces'] + ['Tag: ' + tag for tag in tags]
        self.filter['values'] = choices
        self.filter.set(previous if previous in choices else choices[0])
        self.render_list()

    def render_list(self):
        choice = self.filter.get()
        self.visible = [p for p in self.photos if choice == 'All photos' or any(
            not f['tag'] if choice == 'Photos with untagged faces' else f['tag'] == choice[5:]
            for f in p['faces'])]
        self.listbox.delete(0, 'end')
        for photo in self.visible:
            self.listbox.insert('end', photo['name'])
        selected = next((i for i, p in enumerate(self.visible) if p['id'] == self.selected_id), 0)
        if self.visible:
            self.listbox.selection_set(selected)
            self.select_photo()
        else:
            self.selected_id = None
            self.clear_detail()
            ttk.Label(self.detail, text='No photos in this view. Import photos or change the filter.').pack(anchor='w')

    def clear_detail(self):
        for child in self.detail.winfo_children():
            child.destroy()
        self.images = []

    def image_label(self, parent, item_id, size):
        with Image.open(DATA / (item_id + '.jpg')) as original:
            image = original.copy()
        image.thumbnail(size)
        rendered = ImageTk.PhotoImage(image)
        self.images.append(rendered)
        ttk.Label(parent, image=rendered).pack(anchor='w', pady=8)

    def select_photo(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        photo = self.visible[selection[0]]
        self.selected_id = photo['id']
        self.clear_detail()
        self.canvas.yview_moveto(0)
        ttk.Label(self.detail, text=photo['name'], wraplength=540, font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        try:
            self.image_label(self.detail, photo['id'], (560, 340))
            ttk.Label(self.detail, text=f"{len(photo['faces'])} detected faces · review and tag below").pack(anchor='w')
            if not photo['faces']:
                ttk.Label(self.detail, text='No faces detected. Small or angled faces may be missed.').pack(anchor='w', pady=12)
            for face in photo['faces']:
                row = ttk.Frame(self.detail, padding=(0, 10))
                row.pack(fill='x')
                self.image_label(row, face['id'], (130, 130))
                value = tk.StringVar(value=face['tag'])
                ttk.Entry(row, textvariable=value, width=30).pack(side='left')
                ttk.Button(row, text='Save tag', command=lambda f=face['id'], v=value: self.save_tag(f, v.get())).pack(side='left', padx=8)
                ttk.Button(row, text='Not a face', command=lambda f=face['id']: self.remove_face(f)).pack(side='left')
        except OSError as error:
            self.status.set('Could not load stored image: ' + str(error))

    def save_tag(self, face_id, value):
        try:
            library_request('/api/faces/' + face_id + '/tag', method='POST', json={'tag': value})
            self.refresh()
            self.status.set('Tag saved.' if value.strip() else 'Tag removed.')
        except Exception as error:
            messagebox.showerror('Could not save tag', str(error), parent=self)

    def choose_files(self):
        paths = filedialog.askopenfilenames(parent=self, title='Import photos',
            filetypes=[('Photos', '*.jpg *.jpeg *.png *.webp'), ('All files', '*.*')])
        if not paths:
            return
        self.busy = True
        self.import_button.state(['disabled'])
        self.status.set(f'Importing {len(paths)} photos and detecting faces…')
        mode = self.mode.get()
        def work():
            try:
                self.jobs.put(('done', import_files(paths, mode)))
            except Exception as error:
                self.jobs.put(('error', str(error)))
        threading.Thread(target=work, daemon=True).start()

    def remove_face(self, face_id):
        if not messagebox.askyesno('Remove detection', 'Remove this face thumbnail and its tag? The original stored photo will remain.', parent=self):
            return
        try:
            library_request('/api/faces/' + face_id, method='DELETE')
            self.refresh()
            self.status.set('False detection removed. This does not retrain the detector.')
        except Exception as error:
            messagebox.showerror('Could not remove detection', str(error), parent=self)

    def poll_jobs(self):
        try:
            kind, result = self.jobs.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.import_button.state(['!disabled'])
            if kind == 'error':
                self.status.set('Import failed: ' + result)
            else:
                self.refresh()
                passed = sum(bool(r['ok']) for r in result)
                self.status.set(f'Imported {passed}/{len(result)} photos. Review faces and save your tags.')
                errors = [r['name'] + ': ' + r['error'] for r in result if not r['ok']]
                if errors:
                    messagebox.showwarning('Some photos were not imported', '\n'.join(errors), parent=self)
        self.after(100, self.poll_jobs)

    def close(self):
        if self.busy:
            messagebox.showinfo('Import in progress', 'Please wait for the import to finish before closing.', parent=self)
            return
        self.destroy()


if __name__ == '__main__':
    FaceLibrary().mainloop()
