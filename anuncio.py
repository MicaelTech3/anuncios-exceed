import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Menu
import os
import pygame
from pygame import mixer
import json
from datetime import datetime
import time
import shutil
from PIL import Image, ImageTk
import random
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

class PlayerInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Player de Áudio")
        self.root.geometry("1000x700")
        self.root.configure(bg='#222222')
        
        self.root.minsize(800, 600)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        try:
            mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except pygame.error as e:
            messagebox.showerror("Erro de Áudio", f"Não foi possível inicializar o áudio: {str(e)}")
            raise SystemExit
        
        self.playlist_file = "playlists.json"
        self.playlists = self.load_playlists()
        self.current_playlist = None
        self.current_media_index = None
        
        self.create_icons()
        self.create_widgets()
        self.check_schedules()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_icons(self):
        self.gear_icon = self.create_text_icon("⚙", '#FF9800')
        self.on_icon = self.create_text_icon("ON", '#4CAF50')
        self.off_icon = self.create_text_icon("OFF", '#F44336')

    def create_text_icon(self, text, bg_color):
        img = Image.new('RGB', (24, 24), bg_color)
        return ImageTk.PhotoImage(img)

    def load_playlists(self):
        if os.path.exists(self.playlist_file):
            try:
                with open(self.playlist_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_playlists(self):
        with open(self.playlist_file, 'w') as f:
            json.dump(self.playlists, f, indent=4)

    def get_spotify_session(self):
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name().lower() == "spotify.exe":
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    return volume
            return None
        except Exception as e:
            print(f"Erro ao acessar sessão do Spotify: {e}")
            return None

    def set_spotify_volume(self, volume_level):
        spotify_session = self.get_spotify_session()
        if spotify_session:
            try:
                spotify_session.SetMasterVolume(volume_level, None)
                return True
            except Exception as e:
                print(f"Erro ao ajustar volume do Spotify: {e}")
        return False

    def gradually_increase_spotify_volume(self, target_volume=0.8, steps=10, interval=0.5):
        spotify_session = self.get_spotify_session()
        if not spotify_session:
            return
        
        current_volume = 0.1
        step_size = (target_volume - current_volume) / steps
        
        for _ in range(steps):
            current_volume += step_size
            self.set_spotify_volume(current_volume)
            time.sleep(interval)

    def check_schedules(self):
        now = datetime.now().strftime("%H:%M")
        
        for playlist_name, playlist_data in self.playlists.items():
            if not playlist_data.get("active", True):
                continue
                
            if playlist_data["time"] == now:
                self.play_playlist(playlist_name)
            
            for media in playlist_data["files"]:
                if isinstance(media, dict) and media["time"] == now:
                    self.play_media(media["path"], media.get("repeats", 1))
        
        self.root.after(60000, self.check_schedules)

    def play_playlist(self, playlist_name):
        for media in self.playlists[playlist_name]["files"]:
            path = media["path"] if isinstance(media, dict) else media
            repeats = media.get("repeats", 1) if isinstance(media, dict) else 1
            self.play_media(path, repeats)

    def play_media(self, path, repeats=1):
        try:
            mixer.music.load(path)
            self.set_spotify_volume(0.1)
            
            for _ in range(repeats):
                mixer.music.play()
                while mixer.music.get_busy():
                    time.sleep(0.1)
            
            if not mixer.music.get_busy():
                self.gradually_increase_spotify_volume()
        except Exception as e:
            print(f"Erro ao reproduzir {path}: {e}")

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg='#222222')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = tk.Frame(main_frame, bg='#222222')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Load and display logo
        try:
            logo_img = Image.open("logo/logo.png")
            # Resize logo to fit header (adjust size as needed)
            logo_img = logo_img.resize((150, 50), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(header_frame, image=self.logo_photo, bg='#222222')
            logo_label.pack(side=tk.LEFT)
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            # Fallback to text if logo fails to load
            logo_label = tk.Label(header_frame, text="PLAYER DE ÁUDIO", 
                                font=('Arial', 20, 'bold'), fg='white', bg='#222222')
            logo_label.pack(side=tk.LEFT)
        
        self.menu_btn = tk.Button(header_frame, image=self.gear_icon, 
                                command=self.show_main_menu, bd=0, bg='#222222')
        self.menu_btn.pack(side=tk.RIGHT)
        
        content_frame = tk.Frame(main_frame, bg='#222222')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        playlist_frame = tk.Frame(content_frame, bg='#222222', width=250)
        playlist_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 10))
        playlist_frame.pack_propagate(False)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                      background="#333333", 
                      foreground="white", 
                      fieldbackground="#333333",
                      borderwidth=0)
        style.configure("Treeview.Heading", 
                      background="#444444", 
                      foreground="white",
                      borderwidth=0)
        style.map("Treeview", background=[('selected', '#4CAF50')])
        
        self.playlist_tree = ttk.Treeview(playlist_frame, columns=('status'), 
                                        show='tree headings', height=15)
        self.playlist_tree.heading('#0', text='Playlists')
        self.playlist_tree.heading('status', text='Status')
        self.playlist_tree.column('status', width=60, anchor='center')
        
        vsb = ttk.Scrollbar(playlist_frame, orient="vertical", command=self.playlist_tree.yview)
        hsb = ttk.Scrollbar(playlist_frame, orient="horizontal", command=self.playlist_tree.xview)
        self.playlist_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.playlist_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        playlist_frame.grid_rowconfigure(0, weight=1)
        playlist_frame.grid_columnconfigure(0, weight=1)
        
        self.playlist_tree.bind('<<TreeviewSelect>>', self.show_media)
        self.playlist_tree.bind("<MouseWheel>", self.on_mousewheel)
        
        self.update_playlist_display()
        
        self.media_frame = tk.Frame(content_frame, bg='#222222')
        self.media_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.media_canvas = tk.Canvas(self.media_frame, bg='#222222', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.media_frame, orient="vertical", command=self.media_canvas.yview)
        self.media_container = tk.Frame(self.media_canvas, bg='#222222')
        
        self.media_container.bind("<Configure>", lambda e: self.media_canvas.configure(
            scrollregion=self.media_canvas.bbox("all")))
        
        self.media_canvas.create_window((0, 0), window=self.media_container, anchor="nw")
        self.media_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.media_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.media_frame.grid_rowconfigure(0, weight=1)
        self.media_frame.grid_columnconfigure(0, weight=1)
        
        self.media_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.media_container.bind("<MouseWheel>", self.on_mousewheel)
        
        control_frame = tk.Frame(main_frame, bg='#222222')
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        btn_style = {
            'bg': '#333333',
            'fg': 'white',
            'activebackground': '#444444',
            'borderwidth': 0,
            'font': ('Arial', 10),
            'height': 2,
            'width': 15,
            'compound': tk.LEFT,
            'padx': 10
        }
        
        self.create_btn = tk.Button(control_frame, text="Criar Playlist", 
                                  command=self.create_playlist, **btn_style)
        self.create_btn.pack(side=tk.LEFT, padx=5)
        
        self.media_btn = tk.Button(control_frame, text="Adicionar Mídia", 
                                  command=self.add_media, **btn_style)
        self.media_btn.pack(side=tk.LEFT, padx=5)
        
        self.play_btn = tk.Button(control_frame, text="Tocar Agora", 
                                command=self.play_selected_media, **btn_style)
        self.play_btn.pack(side=tk.LEFT, padx=5)

    def show_main_menu(self):
        menu = Menu(self.root, tearoff=0, bg='#333333', fg='white')
        
        playlist_menu = Menu(menu, tearoff=0, bg='#333333', fg='white')
        playlist_menu.add_command(label="Nova Playlist", command=self.create_playlist)
        playlist_menu.add_command(label="Renomear Playlist", command=self.rename_current_playlist)
        playlist_menu.add_command(label="Excluir Playlist", command=self.delete_current_playlist)
        playlist_menu.add_command(label="Duplicar Playlist", command=self.duplicate_current_playlist)
        playlist_menu.add_separator()
        playlist_menu.add_command(label="Exportar Playlist", command=self.export_playlist)
        playlist_menu.add_command(label="Importar Playlist", command=self.import_playlist)
        
        config_menu = Menu(menu, tearoff=0, bg='#333333', fg='white')
        config_menu.add_command(label="Ligar/Desligar Playlist", command=self.toggle_current_playlist)
        
        menu.add_cascade(label="Playlist", menu=playlist_menu)
        menu.add_cascade(label="Configurações", menu=config_menu)
        menu.add_command(label="Salvar Tudo", command=self.save_playlists)
        
        try:
            menu.tk_popup(self.menu_btn.winfo_rootx(), 
                         self.menu_btn.winfo_rooty() + self.menu_btn.winfo_height())
        finally:
            menu.grab_release()

    def toggle_current_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Nenhuma playlist selecionada!")
            return
        self.toggle_playlist_status(self.current_playlist)

    def rename_current_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Nenhuma playlist selecionada!")
            return
        self.rename_playlist(self.current_playlist)

    def delete_current_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Nenhuma playlist selecionada!")
            return
        self.delete_playlist(self.current_playlist)

    def duplicate_current_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Nenhuma playlist selecionada!")
            return
        self.duplicate_playlist(self.current_playlist)

    def on_mousewheel(self, event):
        if event.widget == self.playlist_tree:
            self.playlist_tree.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            self.media_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def toggle_playlist_status(self, playlist_name):
        if playlist_name in self.playlists:
            self.playlists[playlist_name]["active"] = not self.playlists[playlist_name].get("active", True)
            self.update_playlist_display()
            self.save_playlists()

    def rename_playlist(self, old_name):
        new_name = simpledialog.askstring("Renomear Playlist", "Novo nome:", initialvalue=old_name)
        if new_name and new_name != old_name:
            self.playlists[new_name] = self.playlists.pop(old_name)
            self.current_playlist = new_name
            self.update_playlist_display()
            self.save_playlists()

    def delete_playlist(self, name):
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir a playlist '{name}'?"):
            del self.playlists[name]
            self.update_playlist_display()
            self.save_playlists()
            if self.current_playlist == name:
                self.current_playlist = None
                for widget in self.media_container.winfo_children():
                    widget.destroy()

    def duplicate_playlist(self, name):
        new_name = simpledialog.askstring("Duplicar Playlist", "Nome da nova playlist:", 
                                        initialvalue=f"{name}_copia")
        if new_name and new_name not in self.playlists:
            import copy
            self.playlists[new_name] = copy.deepcopy(self.playlists[name])
            self.update_playlist_display()
            self.save_playlists()

    def export_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Nenhuma playlist selecionada!")
            return
            
        folder_path = filedialog.askdirectory(title="Selecione a pasta para exportar")
        if not folder_path:
            return
            
        export_data = {
            "playlist": self.playlists[self.current_playlist],
            "metadata": {
                "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "playlist_name": self.current_playlist
            }
        }
        
        export_folder = os.path.join(folder_path, f"export_{self.current_playlist}")
        os.makedirs(export_folder, exist_ok=True)
        
        exported_files = []
        for media in export_data["playlist"]["files"]:
            if isinstance(media, dict):
                src_path = media["path"]
            else:
                src_path = media
                
            if not os.path.exists(src_path):
                continue
                
            filename = os.path.basename(src_path)
            dst_path = os.path.join(export_folder, filename)
            
            try:
                shutil.copy2(src_path, dst_path)
                exported_files.append({
                    "path": filename,
                    "time": media.get("time", "00:00") if isinstance(media, dict) else "00:00",
                    "repeats": media.get("repeats", 1) if isinstance(media, dict) else 1
                })
            except Exception as e:
                print(f"Erro ao copiar {src_path}: {e}")
        
        if not exported_files:
            messagebox.showwarning("Aviso", "Nenhum arquivo foi exportado!")
            shutil.rmtree(export_folder)
            return
            
        export_data["playlist"]["files"] = exported_files
        
        config_path = os.path.join(export_folder, "playlist_config.json")
        with open(config_path, 'w') as f:
            json.dump(export_data, f, indent=4)
        
        messagebox.showinfo("Sucesso", f"Playlist exportada para:\n{export_folder}")

    def import_playlist(self):
        folder_path = filedialog.askdirectory(title="Selecione a pasta com a playlist exportada")
        if not folder_path:
            return
            
        config_path = os.path.join(folder_path, "playlist_config.json")
        if not os.path.exists(config_path):
            messagebox.showerror("Erro", "Arquivo de configuração não encontrado!")
            return
            
        try:
            with open(config_path, 'r') as f:
                import_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo de configuração:\n{e}")
            return
            
        if "playlist" not in import_data or "files" not in import_data["playlist"]:
            messagebox.showerror("Erro", "Formato de arquivo inválido!")
            return
            
        playlist_name = import_data.get("metadata", {}).get("playlist_name", 
                  f"importada_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        base_name = playlist_name
        counter = 1
        while playlist_name in self.playlists:
            playlist_name = f"{base_name}_{counter}"
            counter += 1
            
        imported_files = []
        for media in import_data["playlist"]["files"]:
            if isinstance(media, dict):
                filename = media["path"]
                file_path = os.path.join(folder_path, filename)
                
                if os.path.exists(file_path):
                    imported_files.append({
                        "path": file_path,
                        "time": media.get("time", "00:00"),
                        "repeats": media.get("repeats", 1)
                    })
            else:
                file_path = os.path.join(folder_path, media)
                if os.path.exists(file_path):
                    imported_files.append(file_path)
        
        if not imported_files:
            messagebox.showwarning("Aviso", "Nenhum arquivo válido encontrado na importação!")
            return
            
        self.playlists[playlist_name] = {
            "files": imported_files,
            "time": import_data["playlist"].get("time", "00:00"),
            "repeats": import_data["playlist"].get("repeats", 1),
            "active": True
        }
        
        self.update_playlist_display()
        self.save_playlists()
        
        items = self.playlist_tree.get_children()
        for item in items:
            if self.playlist_tree.item(item, 'text') == playlist_name:
                self.playlist_tree.selection_set(item)
                self.playlist_tree.focus(item)
                self.show_media()
                break

    def show_media(self, event=None):
        for widget in self.media_container.winfo_children():
            widget.destroy()
        
        selection = self.playlist_tree.selection()
        if not selection:
            return
            
        playlist_name = self.playlist_tree.item(selection[0], 'text')
        self.current_playlist = playlist_name
        
        for idx, media in enumerate(self.playlists[playlist_name]["files"]):
            media_frame = tk.Frame(self.media_container, bg='#333333')
            media_frame.pack(fill=tk.X, pady=2, padx=2)
            
            if isinstance(media, dict):
                path = media["path"]
                media_time = media.get("time", "00:00")
                repeats = media.get("repeats", 1)
            else:
                path = media
                media_time = "00:00"
                repeats = 1
                
            file_name = os.path.basename(path)
            
            tk.Label(media_frame, text=file_name, bg='#333333', fg='white',
                    font=('Arial', 10), anchor='w', width=40).pack(side=tk.LEFT, padx=5)
            
            tk.Label(media_frame, text=f"{media_time} | Repetir: {repeats}", 
                    bg='#333333', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=5)
            
            tk.Button(media_frame, text="⚙", bg='#4CAF50', fg='white',
                    font=('Arial', 10), bd=0, width=2, height=1,
                    command=lambda i=idx: self.config_media(i)).pack(side=tk.RIGHT, padx=5)
            
            tk.Button(media_frame, text="►", bg='#2196F3', fg='white',
                    font=('Arial', 10), bd=0, width=2, height=1,
                    command=lambda i=idx: self.select_media(i)).pack(side=tk.RIGHT, padx=2)

    def select_media(self, media_index):
        self.current_media_index = media_index
        messagebox.showinfo("Mídia Selecionada", "Mídia selecionada para tocar agora!")

    def play_selected_media(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Selecione uma playlist primeiro!")
            return
            
        if self.current_media_index is None:
            messagebox.showwarning("Aviso", "Selecione uma mídia primeiro!")
            return
            
        repeats = simpledialog.askinteger("Repetições", "Quantas vezes deseja repetir?", 
                                        parent=self.root, minvalue=1, initialvalue=1)
        
        if repeats is None:
            return
            
        media = self.playlists[self.current_playlist]["files"][self.current_media_index]
        path = media["path"] if isinstance(media, dict) else media
        self.play_media(path, repeats)
        
        if isinstance(media, dict):
            self.playlists[self.current_playlist]["files"][self.current_media_index]["repeats"] = repeats
        else:
            self.playlists[self.current_playlist]["files"][self.current_media_index] = {
                "path": path,
                "time": "00:00",
                "repeats": repeats
            }
        
        self.show_media()
        self.save_playlists()

    def config_media(self, media_index):
        if not self.current_playlist:
            return
            
        media = self.playlists[self.current_playlist]["files"][media_index]
        is_dict = isinstance(media, dict)
        
        config_window = tk.Toplevel(self.root)
        config_window.title("Configurar Mídia")
        config_window.geometry("300x200")
        config_window.configure(bg='#222222')
        
        frame = tk.Frame(config_window, bg='#222222')
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Horário (HH:MM):", bg='#222222', fg='white').pack()
        time_entry = tk.Entry(frame, bg='#333333', fg='white', insertbackground='white')
        time_entry.pack(pady=5)
        if is_dict:
            time_entry.insert(0, media.get("time", "00:00"))
        else:
            time_entry.insert(0, "00:00")
        
        tk.Label(frame, text="Repetições:", bg='#222222', fg='white').pack()
        repeat_entry = tk.Entry(frame, bg='#333333', fg='white', insertbackground='white')
        repeat_entry.pack(pady=5)
        if is_dict:
            repeat_entry.insert(0, str(media.get("repeats", 1)))
        else:
            repeat_entry.insert(0, "1")
        
        def save_config():
            time_str = time_entry.get()
            repeats = repeat_entry.get()
            
            try:
                time.strptime(time_str, "%H:%M")
            except ValueError:
                messagebox.showerror("Erro", "Formato de horário inválido! Use HH:MM")
                return
                
            try:
                repeats = int(repeats)
                if repeats < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erro", "Repetições deve ser um número inteiro positivo!")
                return
                
            path = media["path"] if is_dict else media
            self.playlists[self.current_playlist]["files"][media_index] = {
                "path": path,
                "time": time_str,
                "repeats": repeats
            }
            
            self.show_media()
            self.save_playlists()
            config_window.destroy()
        
        tk.Button(frame, text="Salvar", command=save_config, 
                bg='#4CAF50', fg='white').pack(pady=10)

    def create_playlist(self):
        name = simpledialog.askstring("Nova Playlist", "Nome da playlist:")
        if name:
            self.playlists[name] = {"files": [], "time": "00:00", "repeats": 1, "active": True}
            self.update_playlist_display()
            self.save_playlists()

    def add_media(self):
        if not self.current_playlist:
            messagebox.showwarning("Aviso", "Selecione uma playlist primeiro!")
            return
            
        files = filedialog.askopenfilenames(
            title="Selecione arquivos de áudio",
            filetypes=[("Arquivos de Áudio", "*.mp3 *.wav *.ogg")]
        )
        
        if files:
            for file_path in files:
                self.playlists[self.current_playlist]["files"].append({
                    "path": file_path,
                    "time": "00:00",
                    "repeats": 1
                })
            
            self.show_media()
            self.save_playlists()

    def update_playlist_display(self):
        for item in self.playlist_tree.get_children():
            self.playlist_tree.delete(item)
        
        for name, data in self.playlists.items():
            status = "ON" if data.get("active", True) else "OFF"
            status_icon = self.on_icon if data.get("active", True) else self.off_icon
            
            item = self.playlist_tree.insert("", "end", text=name, values=(status), image=status_icon)
            
            self.playlist_tree.tag_bind(item, '<Button-1>', 
                                      lambda e, n=name: self.toggle_playlist_status(n) if self.playlist_tree.identify_column(e.x) == '#2' else None)

    def on_closing(self):
        self.save_playlists()
        self.set_spotify_volume(0.8)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PlayerInterface(root)
    root.mainloop()