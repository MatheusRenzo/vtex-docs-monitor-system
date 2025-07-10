import requests
import pandas as pd
from datetime import datetime, time as dt_time
import os
import time
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from queue import Queue
import csv

# Configurações globais
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Documents")
LOG_FILE = os.path.join(OUTPUT_DIR, "api_logs.csv")

class APIClient:
    def __init__(self, app_key, app_token):
        HEADERS["X-VTEX-API-AppKey"] = app_key
        HEADERS["X-VTEX-API-AppToken"] = app_token
    
    def fetch_dock_data(self, stores, progress_queue, log_queue):
        all_records = []
        
        for i, store in enumerate(stores):
            try:
                url = f"https://{store}.vtexcommercestable.com.br/api/logistics/pvt/configuration/docks"
                response = requests.get(url, headers=HEADERS, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                for dock in data:
                    all_records.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'store_id': store,
                        'dock_id': dock.get('id', 'N/A'),
                        'dock_name': dock.get('name', 'N/A'),
                        'is_active': dock.get('isActive', 'N/A'),
                        'dock_time_fake': dock.get('dockTimeFake', 'N/A'),
                        'priority': dock.get('priority', 'N/A')
                    })
                
                log_queue.put((store, "SUCCESS", f"Found {len(data)} docks"))
                progress_queue.put((i + 1, len(stores), store))
                
            except Exception as e:
                log_queue.put((store, "ERROR", str(e)))
                progress_queue.put((i + 1, len(stores), f"Error: {str(e)}"))
            
            time.sleep(0.1)
        
        return all_records

class Logger:
    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("timestamp,store_id,status,details\n")
    
    def log(self, store_id, status, details):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp},{store_id},{status},\"{details}\"\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        
        return f"[{timestamp}] {store_id} - {status}: {details}"

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VTEX Dock Monitoring System")
        self.geometry("900x900")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.stores = []
        self.output_format = tk.StringVar(value="xlsx")
        self.app_key = tk.StringVar()
        self.app_token = tk.StringVar()
        self.logger = Logger()
        self.running = False
        self.worker_thread = None
        
        # Fila para comunicação entre threads
        self.log_queue = Queue()
        self.progress_queue = Queue()
        
        self.create_widgets()
        self.check_queues()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de credenciais
        cred_frame = ttk.LabelFrame(main_frame, text="VTEX Credentials", padding="10")
        cred_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cred_frame, text="App Key:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(cred_frame, textvariable=self.app_key, width=50).grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(cred_frame, text="App Token:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(cred_frame, textvariable=self.app_token, width=50, show="*").grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        # Frame de lojas
        store_frame = ttk.LabelFrame(main_frame, text="account list (em coluna, sem virgulas)", padding="10")
        store_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.store_text = scrolledtext.ScrolledText(
            store_frame, 
            height=10,
            wrap=tk.WORD
        )
        self.store_text.pack(fill=tk.BOTH, expand=True)
        
        # Frame de saída
        output_frame = ttk.LabelFrame(main_frame, text="Output Options", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Output Format:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(output_frame, text="Excel (XLSX)", variable=self.output_format, value="xlsx").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(output_frame, text="CSV", variable=self.output_format, value="csv").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side=tk.RIGHT, padx=5)
        
        # Frame de progresso
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        # Frame de logs
        log_frame = ttk.LabelFrame(main_frame, text="Execution Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Frame de botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(
            button_frame, 
            text="Start Collection", 
            command=self.start_collection
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Clear Logs", 
            command=self.clear_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Export Logs", 
            command=self.export_logs
        ).pack(side=tk.LEFT, padx=5)
    
    def browse_output(self):
        file_types = [
            ("Excel files", "*.xlsx"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=file_types,
            initialdir=OUTPUT_DIR
        )
        
        if file_path:
            self.output_file = file_path
    
    def start_collection(self):
        if self.running:
            messagebox.showwarning("Warning", "Operation already in progress")
            return
        
        # Validar credenciais
        if not self.app_key.get() or not self.app_token.get():
            messagebox.showerror("Error", "App Key and App Token are required")
            return
        
        # Obter lista de lojas
        store_list = self.store_text.get("1.0", tk.END).strip().splitlines()
        if not store_list:
            messagebox.showerror("Error", "Store list cannot be empty")
            return
        
        self.stores = [store.strip() for store in store_list if store.strip()]
        
        # Configurar arquivo de saída
        if not hasattr(self, 'output_file'):
            default_name = f"dock_times_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ext = self.output_format.get()
            self.output_file = os.path.join(OUTPUT_DIR, f"{default_name}.{ext}")
        
        # Iniciar thread de trabalho
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Starting collection...")
        
        self.worker_thread = threading.Thread(
            target=self.run_collection,
            args=(self.stores,),
            daemon=True
        )
        self.worker_thread.start()
    
    def run_collection(self, stores):
        client = APIClient(self.app_key.get(), self.app_token.get())
        
        try:
            records = client.fetch_dock_data(
                stores,
                self.progress_queue,
                self.log_queue
            )
            
            self.save_data(records)
            self.progress_queue.put((len(stores), len(stores), "Completed successfully"))
            
        except Exception as e:
            self.log_queue.put(("SYSTEM", "ERROR", f"Collection failed: {str(e)}"))
            self.progress_queue.put((len(stores), len(stores), f"Error: {str(e)}"))
        
        finally:
            self.running = False
            self.progress_queue.put("FINISHED")
    
    def save_data(self, records):
        try:
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            df = pd.DataFrame(records)
            
            if self.output_format.get() == "csv":
                df.to_csv(self.output_file, index=False)
            else:
                df.to_excel(self.output_file, index=False, engine='openpyxl')
            
            self.log_queue.put((
                "SYSTEM", 
                "SUCCESS", 
                f"Data saved to: {self.output_file}"
            ))
            
            return True
        
        except Exception as e:
            self.log_queue.put((
                "SYSTEM", 
                "ERROR", 
                f"Error saving data: {str(e)}"
            ))
            return False
    
    def check_queues(self):
        # Processar fila de progresso
        while not self.progress_queue.empty():
            item = self.progress_queue.get()
            
            if item == "FINISHED":
                self.start_btn.config(state=tk.NORMAL)
                self.status_label.config(text="Ready")
            else:
                current, total, *extra = item
                progress = (current / total) * 100
                self.progress_var.set(progress)
                
                if extra:
                    self.status_label.config(text=extra[0])
                else:
                    self.status_label.config(
                        text=f"Processing: {current}/{total} stores"
                    )
        
        # Processar fila de logs
        while not self.log_queue.empty():
            store, status, details = self.log_queue.get()
            log_line = self.logger.log(store, status, details)
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_line + "\n")
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
        
        # Agendar próxima verificação
        self.after(100, self.check_queues)
    
    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def export_logs(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialdir=OUTPUT_DIR
        )
        
        if file_path:
            try:
                # Copiar o arquivo de log existente
                import shutil
                shutil.copyfile(LOG_FILE, file_path)
                messagebox.showinfo("Success", f"Logs exported to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export logs: {str(e)}")
    
    def on_close(self):
        if self.running:
            if messagebox.askokcancel(
                "Quit", 
                "Collection is still running. Do you want to force quit?"
            ):
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    app = Application()
    app.mainloop()