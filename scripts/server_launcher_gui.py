#!/usr/bin/env python3
"""
GUI launcher for the simple HTTP server.

Usage:
  # Run from VSCoding root directory
  python scripts/server_launcher_gui.py
  
  # Or from scripts directory
  cd scripts
  python server_launcher_gui.py

The GUI will launch the simple_http_server.py with default settings:
  --port 8000 --directory . (serves from VSCoding root)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import sys

class ServerLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Server Launcher")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        self.server_process = None
        self.server_running = False
        
        # Main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Simple HTTP Server Launcher", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Server Status: Stopped", 
                                     foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Start/Stop button
        self.toggle_button = ttk.Button(main_frame, text="Start Server", 
                                       command=self.toggle_server)
        self.toggle_button.grid(row=2, column=0, pady=10, padx=(0, 10))
        
        # Exit button
        exit_button = ttk.Button(main_frame, text="Exit", command=self.on_exit)
        exit_button.grid(row=2, column=1, pady=10)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Handle window close
        root.protocol("WM_DELETE_WINDOW", self.on_exit)
    
    def toggle_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()
    
    def start_server(self):
        try:
            # Get the directory of this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            server_script = os.path.join(script_dir, "simple_http_server.py")
            
            # Determine the VSCoding root directory (parent of scripts)
            vscoding_root = os.path.dirname(script_dir)
            
            if not os.path.exists(server_script):
                messagebox.showerror("Error", "simple_http_server.py not found!")
                return
            
            # Start server in a separate thread
            def run_server():
                try:
                    # Run the equivalent of: python scripts/simple_http_server.py --port 8000 --directory .
                    self.server_process = subprocess.Popen([
                        sys.executable, server_script, 
                        "--port", "8000", 
                        "--directory", vscoding_root
                    ], cwd=vscoding_root)
                    self.server_process.wait()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to start server: {str(e)}")
                    self.server_running = False
                    self.update_ui()
            
            threading.Thread(target=run_server, daemon=True).start()
            
            self.server_running = True
            self.update_ui()
            messagebox.showinfo("Success", 
                              "Server started on port 8000!\n\n"
                              "Visit: http://localhost:8000/concert/webcode/homepage.html")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
    
    def stop_server(self):
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process = None
                self.server_running = False
                self.update_ui()
                messagebox.showinfo("Success", "Server stopped successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop server: {str(e)}")
    
    def update_ui(self):
        if self.server_running:
            self.status_label.config(text="Server Status: Running on port 8000", foreground="green")
            self.toggle_button.config(text="Stop Server")
        else:
            self.status_label.config(text="Server Status: Stopped", foreground="red")
            self.toggle_button.config(text="Start Server")
    
    def on_exit(self):
        if self.server_running:
            self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerLauncherGUI(root)
    root.mainloop()