import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import queue
import time
import qrcode
from PIL import Image, ImageTk
import io
import os
import sys
import subprocess

# --- Configuration ---
DEFAULT_HOST_NAME = "0.0.0.0"
DEFAULT_PORT_NUMBER = 8000
# ---------------------

app_instance_ref = None


# =============================================================================
# UI Configuration and Theme Management
# =============================================================================
class Config:
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_SMALL = 9
    FONT_SIZE_HEADER = 14
    PAD_X = 10
    PAD_Y = 5


class Theme:
    """
    Manages color themes for the application.
    Now loads and saves the selected theme from/to a configuration file.
    """

    CONFIG_FILE = "theme.cfg"  # The file to store the theme setting

    def __init__(self):
        self.themes = self.themes = {
            "LocalFetch Dark": {
                "BG": "#2B2623",
                "FG": "#D4C9B5",
                "FRAME_BG": "#3C362D",
                "INPUT_BG": "#3D322B",
                "ACCENT": "#7F6636",
                "ACCENT_FG": "#2A211C",
                "SUCCESS": "#879A39",
                "ERROR": "#D75F5F",
                "DISABLED_FG": "#85786B",
            },
            "Darcula": {
                "BG": "#282A36",
                "FG": "#E3E7EE",
                "FRAME_BG": "#44475A",
                "INPUT_BG": "#313335",
                "ACCENT": "#6272A4",
                "ACCENT_FG": "#F8F8F2",
                "SUCCESS": "#FF79C6",
                "ERROR": "#FF5555",
                "DISABLED_FG": "#808080",
            },
            "Monokai": {
                "BG": "#272822",
                "FG": "#F8F8F2",
                "FRAME_BG": "#272822",
                "INPUT_BG": "#3E3D32",
                "ACCENT": "#FF6188",
                "ACCENT_FG": "#272822",
                "SUCCESS": "#A9DC76",
                "ERROR": "#F92672",
                "DISABLED_FG": "#75715E",
            },
            "Solarized Dark": {
                "BG": "#002b36",
                "FG": "#93a1a1",
                "FRAME_BG": "#073642",
                "INPUT_BG": "#586e75",
                "ACCENT": "#d3  3682",
                "ACCENT_FG": "#fdf6e3",
                "SUCCESS": "#859900",
                "ERROR": "#dc322f",
                "DISABLED_FG": "#586e75",
            },
            "Solarized Light": {
                "BG": "#fdf6e3",
                "FG": "#073642",
                "FRAME_BG": "#eee8d5",
                "INPUT_BG": "#eee8d5",
                "ACCENT": "#268bd2",
                "ACCENT_FG": "#fdf6e3",
                "SUCCESS": "#859900",
                "ERROR": "#dc322f",
                "DISABLED_FG": "#93a1a1",
            },
            "GitHub Light": {
                "BG": "#FFFFFF",
                "FG": "#24292E",
                "FRAME_BG": "#F6F8FA",
                "INPUT_BG": "#FAFBFC",
                "ACCENT": "#0366D6",
                "ACCENT_FG": "#FFFFFF",
                "SUCCESS": "#28A745",
                "ERROR": "#D73A49",
                "DISABLED_FG": "#586069",
            },
            "Default Light": {
                "BG": "#F0F0F0",
                "FG": "#000000",
                "FRAME_BG": "#FFFFFF",
                "INPUT_BG": "#EAEAEA",
                "ACCENT": "#0078D7",
                "ACCENT_FG": "#FFFFFF",
                "SUCCESS": "#107C10",
                "ERROR": "#D32F2F",
                "DISABLED_FG": "#666666",
            },
            "Oceanic": {
                "BG": "#F2F9FF",
                "FG": "#003B5C",
                "FRAME_BG": "#E0F2FF",
                "INPUT_BG": "#FFFFFF",
                "ACCENT": "#008CBA",
                "ACCENT_FG": "#FFFFFF",
                "SUCCESS": "#4CAF50",
                "ERROR": "#F44336",
                "DISABLED_FG": "#547B94",
            },
        }
        self.current_theme_name = self._load_theme_from_file()
        self.current = self.themes[self.current_theme_name]

    def _load_theme_from_file(self):
        """Tries to read the theme name from the config file."""
        try:
            with open(self.CONFIG_FILE, "r") as f:
                theme_name = f.read().strip()
            if theme_name in self.themes:
                print(f"Theme loaded from file: {theme_name}")
                return theme_name
        except FileNotFoundError:
            print("Theme file not found, using default.")
        except Exception as e:
            print(f"Warning: Could not read theme file '{self.CONFIG_FILE}': {e}")

        return "LocalFetch Dark"  # Default theme

    def save_theme_to_file(self, theme_name):
        """Saves the selected theme name to the config file."""
        try:
            with open(self.CONFIG_FILE, "w") as f:
                f.write(theme_name)
            print(f"Theme '{theme_name}' saved to file.")
        except Exception as e:
            messagebox.showerror(
                "Theme Save Error",
                f"Could not save theme to '{self.CONFIG_FILE}':\n{e}",
            )


# =============================================================================
# Server Handler
# =============================================================================
class LocalFetchHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers", "X-Requested-With, Content-Type"
        )

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        global app_instance_ref
        if not app_instance_ref:
            body_bytes = b"Server app not initialized"
            self.send_response(503)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)
            return

        if self.path == "/text":
            current_text = app_instance_ref.get_shared_text()
            encoded_body = current_text.encode("utf-8")

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded_body)))
            self.end_headers()
            self.wfile.write(encoded_body)
            app_instance_ref.log_to_gui(
                f"GET /text from {self.client_address[0]}: Sent '{current_text}' (Length: {len(encoded_body)})"
            )
        else:
            error_message_bytes = b"Not Found"
            self.send_response(404)
            self._send_cors_headers()
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(error_message_bytes)))
            self.end_headers()
            self.wfile.write(error_message_bytes)
            app_instance_ref.log_to_gui(
                f"GET {self.path} from {self.client_address[0]}: Sent 404 (Length: {len(error_message_bytes)})"
            )

    def do_POST(self):
        global app_instance_ref
        if not app_instance_ref:
            body_bytes = b"Server app not initialized"
            self.send_response(503)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)
            return

        if self.path == "/text":
            try:
                content_length = int(self.headers["Content-Length"])
                if content_length > 1024 * 1024:  # Limit POST size to 1MB
                    raise ValueError("Content too large")
                post_data = self.rfile.read(content_length)
                received_text = post_data.decode("utf-8")
                app_instance_ref.update_shared_text(received_text, from_client=True)

                success_message_bytes = b"Text received successfully!"
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(success_message_bytes)))
                self.end_headers()
                self.wfile.write(success_message_bytes)
            except Exception as e:
                app_instance_ref.log_to_gui(f"Error processing POST: {e}")
                error_response_bytes = b"Error processing request"
                self.send_response(400)
                self._send_cors_headers()
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(error_response_bytes)))
                self.end_headers()
                self.wfile.write(error_response_bytes)
        else:
            error_message_bytes = b"Not Found"
            self.send_response(404)
            self._send_cors_headers()
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(error_message_bytes)))
            self.end_headers()
            self.wfile.write(error_message_bytes)
            app_instance_ref.log_to_gui(
                f"POST {self.path} from {self.client_address[0]}: Sent 404 (Length: {len(error_message_bytes)})"
            )


# =============================================================================
# Main Application Class
# =============================================================================
class LocalFetchServerApp:
    def __init__(self, root_window: tk.Tk):
        # --- Core App State ---
        self.root: tk.Tk = root_window
        self.shared_text_data = "Hello from the Python server GUI!"
        self.server_thread = None
        self.httpd = None
        self.running_port = DEFAULT_PORT_NUMBER
        self.preferred_ip = "N/A"
        self.all_ips = []
        self.gui_queue = queue.Queue()
        self.qr_image_tk = None

        # --- UI Styling ---
        self.config = Config()
        self.theme = Theme()

        # --- Setup ---
        self._configure_root_window()
        self._apply_theme()
        self._setup_gui()
        self.update_shared_text_display()

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._process_gui_queue()
        self._update_ip_info()
        self.start_server()

    def _configure_root_window(self):
        self.root.title("Local Fetch Server")
        self.root.geometry("800x650")
        self.root.minsize(750, 600)
        self.root.iconphoto(
            True,
            tk.PhotoImage(file=os.path.abspath(".").join(("Logo1.png",))),
        )
        self.root.configure(bg=self.theme.current["BG"])

        # Configure grid layout
        self.root.grid_rowconfigure(1, weight=1)  # Main content area row
        self.root.grid_rowconfigure(2, weight=1)  # Log area row
        self.root.grid_columnconfigure(0, weight=3)  # Left column (main content)
        self.root.grid_columnconfigure(1, weight=2)  # Right column (server info)

    def _apply_theme(self):
        """Configures ttk styles based on the selected theme."""
        style = ttk.Style()
        style.theme_use("clam")  # A good base theme to build on

        theme = self.theme.current
        font_normal = (self.config.FONT_FAMILY, self.config.FONT_SIZE_NORMAL)
        font_small = (self.config.FONT_FAMILY, self.config.FONT_SIZE_SMALL)

        # General widget styling
        style.configure(
            ".", background=theme["BG"], foreground=theme["FG"], font=font_normal
        )
        style.configure("TFrame", background=theme["BG"])
        style.configure("TLabel", background=theme["BG"], foreground=theme["FG"])
        style.configure(
            "TEntry",
            fieldbackground=theme["INPUT_BG"],
            foreground=theme["FG"],
            insertcolor=theme["FG"],
        )
        style.configure(
            "TCombobox", fieldbackground=theme["INPUT_BG"], foreground=theme["FG"]
        )

        # Button styling
        style.configure(
            "TButton",
            background=theme["FRAME_BG"],
            foreground=theme["FG"],
            font=font_normal,
        )
        style.map("TButton", background=[("active", theme["ACCENT"])])

        # Accent button style (for primary actions)
        style.configure(
            "Accent.TButton",
            background=theme["ACCENT"],
            foreground=theme["ACCENT_FG"],
            font=font_normal,
        )
        style.map(
            "Accent.TButton",
            background=[("active", theme["BG"]), ("pressed", theme["ACCENT"])],
        )

        # LabelFrame styling
        style.configure(
            "TLabelframe", background=theme["BG"], bordercolor=theme["DISABLED_FG"]
        )
        style.configure(
            "TLabelframe.Label", background=theme["BG"], foreground=theme["FG"]
        )

    def _setup_gui(self):
        """Creates and places all GUI elements using a grid layout."""
        self._create_header_frame()
        self._create_shared_text_frame()
        self._create_log_frame()
        self._create_server_info_frame()

    def _create_header_frame(self):
        header_frame = ttk.Frame(self.root, padding=self.config.PAD_X)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        title_label = ttk.Label(
            header_frame,
            text="Local Fetch Server",
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE_HEADER, "bold"),
        )
        title_label.pack(side=tk.LEFT)

        # --- Theme Switcher ---
        theme_frame = ttk.Frame(header_frame)
        theme_frame.pack(side=tk.RIGHT)

        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT, padx=(0, 5))
        self.theme_selector = ttk.Combobox(
            theme_frame,
            values=list(self.theme.themes.keys()),
            width=20,
            state="readonly",
            background=self.theme.current["BG"],
            foreground=self.theme.current["FG"],
        )
        self.theme_selector.set(self.theme.current_theme_name)
        self.theme_selector.bind("<<ComboboxSelected>>", self._change_theme)
        self.theme_selector.pack(side=tk.LEFT)

    def _create_shared_text_frame(self):
        shared_text_frame = ttk.LabelFrame(
            self.root,
            text="Shared Text",
            padding=(self.config.PAD_X, self.config.PAD_Y),
        )
        shared_text_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=self.config.PAD_X,
            pady=self.config.PAD_Y,
        )
        shared_text_frame.grid_rowconfigure(0, weight=1)
        shared_text_frame.grid_columnconfigure(0, weight=1)

        self.shared_text_display = scrolledtext.ScrolledText(
            shared_text_frame,
            height=5,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.theme.current["INPUT_BG"],
            fg=self.theme.current["FG"],
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE_NORMAL),
            relief=tk.FLAT,
            borderwidth=2,
        )
        self.shared_text_display.grid(
            row=0, column=0, columnspan=2, sticky="nsew", pady=(0, self.config.PAD_Y)
        )

        self.gui_text_input = ttk.Entry(
            shared_text_frame,
            width=50,
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE_NORMAL),
        )
        self.gui_text_input.grid(
            row=1, column=0, sticky="ew", padx=(0, self.config.PAD_X)
        )

        self.update_text_button = ttk.Button(
            shared_text_frame,
            text="Update from GUI",
            command=self.update_shared_text_from_gui,
            style="Accent.TButton",
        )
        self.update_text_button.grid(row=1, column=1, sticky="e")

    def _create_log_frame(self):
        log_frame = ttk.LabelFrame(
            self.root, text="Server Log", padding=(self.config.PAD_X, self.config.PAD_Y)
        )
        log_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=self.config.PAD_X,
            pady=(0, self.config.PAD_Y),
        )
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.theme.current["FRAME_BG"],
            fg=self.theme.current["DISABLED_FG"],
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE_SMALL),
            relief=tk.FLAT,
            borderwidth=2,
        )
        self.log_area.grid(row=0, column=0, sticky="nsew")

    def _create_server_info_frame(self):
        info_frame = ttk.LabelFrame(
            self.root,
            text="Server Information",
            padding=(self.config.PAD_X, self.config.PAD_Y),
        )
        info_frame.grid(
            row=1,
            column=1,
            rowspan=1,
            sticky="nsew",
            padx=(0, self.config.PAD_X),
            pady=self.config.PAD_Y,
        )
        info_frame.grid_columnconfigure(1, weight=1)

        # Status Label
        self.status_label = ttk.Label(
            info_frame,
            text="Initializing...",
            font=(self.config.FONT_FAMILY, 12, "bold"),
        )
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # IP/Port Display
        ttk.Label(info_frame, text="Address:").grid(row=1, column=0, sticky="w")
        self.ip_display_var = tk.StringVar(value="N/A")
        self.ip_display_entry = ttk.Entry(
            info_frame, textvariable=self.ip_display_var, state="readonly", width=20
        )
        self.ip_display_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        ttk.Label(info_frame, text="Port:").grid(
            row=2, column=0, sticky="w", pady=(self.config.PAD_Y, 0)
        )
        self.port_display_var = tk.StringVar(value=str(DEFAULT_PORT_NUMBER))
        self.port_entry = ttk.Entry(
            info_frame, textvariable=self.port_display_var, state="readonly", width=20
        )
        self.port_entry.grid(
            row=2, column=1, sticky="ew", padx=(5, 0), pady=(self.config.PAD_Y, 0)
        )

        # Action Buttons
        button_frame = ttk.Frame(info_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 15))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.copy_ip_button = ttk.Button(
            button_frame, text="Copy Address", command=self._copy_ip
        )
        self.copy_ip_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.refresh_ip_button = ttk.Button(
            button_frame, text="Refresh IPs", command=self._update_ip_info
        )
        self.refresh_ip_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Other IPs
        self.all_ips_label = ttk.Label(
            info_frame,
            text="Other IPs: (loading...)",
            wraplength=250,
            justify=tk.LEFT,
            foreground=self.theme.current["DISABLED_FG"],
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE_SMALL),
        )
        self.all_ips_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # QR Code
        self.qr_label = ttk.Label(
            info_frame,
            text="QR will appear here",
            relief=tk.SOLID,
            anchor=tk.CENTER,
            borderwidth=1,
            background=self.theme.current["FRAME_BG"],
        )
        self.qr_label.grid(row=5, column=0, columnspan=2, sticky="nsew", ipady=10)
        info_frame.grid_rowconfigure(5, weight=1)

    # --- THEME MANAGEMENT ---
    def _change_theme(self, event=None):
        """
        Handles theme selection. Saves the new theme and prompts the user to restart.
        """
        selected_theme = self.theme_selector.get()
        if selected_theme == self.theme.current_theme_name:
            return  # Do nothing if the theme hasn't changed

        # Save the new theme choice to the configuration file.
        self.theme.save_theme_to_file(selected_theme)

        # Inform the user that a restart is required.
        messagebox.showinfo(
            "Restart Required",
            f"Theme has been set to '{selected_theme}'.\nPlease restart the application for the changes to take effect.",
        )

        # Gracefully shut down the server and close the application.
        self.stop_server()
        self.root.destroy()

    # --- BACKEND LOGIC ---
    def _get_local_ips(self):
        ips = []
        preferred = None
        try:
            hostname = socket.gethostname()
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
            for item in addr_info:
                ip = item[4][0]
                if not ip.startswith("127."):
                    ips.append(ip)
                    if ip.startswith("192.168."):
                        preferred = ip

            if not ips:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(("10.255.255.255", 1))
                    fallback_ip = s.getsockname()[0]
                    if fallback_ip and not fallback_ip.startswith("127."):
                        ips.append(fallback_ip)
                except Exception:
                    pass
                finally:
                    s.close()

            if not preferred and ips:
                preferred = ips[0]
            elif not preferred and not ips:
                preferred = "127.0.0.1"
                ips.append("127.0.0.1")

        except socket.gaierror:
            preferred = "127.0.0.1"
            ips = ["127.0.0.1"]
        return preferred, sorted(list(set(ips)))

    def _update_ip_info(self):
        self.preferred_ip, self.all_ips = self._get_local_ips()

        status_update = {
            "ip": self.preferred_ip,
            "all_ips": self.all_ips,
        }
        self.gui_queue.put({"type": "ip_update", "content": status_update})

        if self.httpd:
            self._generate_and_display_qr_code()

    def _copy_ip(self):
        if self.preferred_ip and self.preferred_ip != "N/A" and self.httpd:
            full_address = f"{self.preferred_ip}:{self.running_port}"
            self.root.clipboard_clear()
            self.root.clipboard_append(full_address)
            self.log_to_gui(f"Copied '{full_address}' to clipboard.")
        else:
            self.log_to_gui(
                "Cannot copy address: Server is not running or IP is invalid."
            )

    def _generate_and_display_qr_code(self):
        if self.preferred_ip != "N/A" and self.httpd:
            server_address_for_qr = f"{self.preferred_ip}:{self.running_port}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=6,
                border=2,
            )
            qr.add_data(server_address_for_qr)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            pil_image = Image.open(img_byte_arr)

            # Resize image to fit the label if it's too big
            label_width = self.qr_label.winfo_width()
            if label_width > 10 and pil_image.width > label_width:
                wpercent = label_width / float(pil_image.size[0])
                hsize = int((float(pil_image.size[1]) * float(wpercent)))
                pil_image = pil_image.resize(
                    (label_width, hsize), Image.Resampling.LANCZOS
                )

            self.qr_image_tk = ImageTk.PhotoImage(pil_image)
            self.qr_label.config(image=self.qr_image_tk)
            self.qr_label.image = self.qr_image_tk
            self.log_to_gui(f"QR code updated for: {server_address_for_qr}")
        else:
            self.qr_label.config(image="", text="Server Offline")
            self.qr_label.image = None

    def log_to_gui(self, message):
        self.gui_queue.put({"type": "log", "content": message})

    def get_shared_text(self):
        return self.shared_text_data

    def update_shared_text(self, new_text, from_client=False):
        self.shared_text_data = new_text
        source = "Client" if from_client else "GUI"
        log_msg = (
            f"{source} updated text to: '{new_text[:50]}...'"
            if len(new_text) > 50
            else f"{source} updated text to: '{new_text}'"
        )
        self.gui_queue.put({"type": "shared_text_update", "content": log_msg})

    def update_shared_text_from_gui(self):
        new_text = self.gui_text_input.get()
        if new_text:  # Only update if there is text
            self.gui_text_input.delete(0, tk.END)
            self.update_shared_text(new_text, from_client=False)

    def update_shared_text_display(self):
        self.shared_text_display.config(state=tk.NORMAL)
        self.shared_text_display.delete(1.0, tk.END)
        self.shared_text_display.insert(tk.END, self.shared_text_data)
        self.shared_text_display.config(state=tk.DISABLED)

    def _process_gui_queue(self):
        try:
            while True:
                item = self.gui_queue.get_nowait()
                msg_type, content = item.get("type"), item.get("content")

                if msg_type == "log":
                    self._append_to_log_area(content)
                elif msg_type == "shared_text_update":
                    self.update_shared_text_display()
                    self._append_to_log_area(content)
                elif msg_type == "server_status":
                    self.status_label.config(
                        text=content.get("text"), foreground=content.get("color")
                    )
                elif msg_type == "ip_update":
                    self.preferred_ip = content.get("ip", "N/A")
                    self.all_ips = content.get("all_ips", [])
                    self.ip_display_var.set(f"{self.preferred_ip}")

                    other_ips = [ip for ip in self.all_ips if ip != self.preferred_ip]
                    self.all_ips_label.config(
                        text=f"Other IPs: {', '.join(other_ips) if other_ips else 'None found'}"
                    )

        except queue.Empty:
            pass
        self.root.after(100, self._process_gui_queue)

    def _append_to_log_area(self, message):
        self.log_area.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def start_server(self):
        self.running_port = DEFAULT_PORT_NUMBER
        self.port_display_var.set(str(self.running_port))

        try:
            global app_instance_ref
            app_instance_ref = self
            self.httpd = HTTPServer(
                (DEFAULT_HOST_NAME, self.running_port), LocalFetchHandler
            )
        except OSError as e:
            messagebox.showerror(
                "Server Error",
                f"Failed to start server on port {self.running_port}: {e}",
            )
            self.log_to_gui(
                f"FATAL: Server failed to start. Port {self.running_port} likely in use."
            )
            status_update = {
                "text": f"Server Failed on Port {self.running_port}",
                "color": self.theme.current["ERROR"],
            }
            self.gui_queue.put({"type": "server_status", "content": status_update})
            self.httpd = None
            return

        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()

        self._update_ip_info()  # Fetch and display IPs
        status_update = {
            "text": f"Server Running",
            "color": self.theme.current["SUCCESS"],
        }
        self.gui_queue.put({"type": "server_status", "content": status_update})
        self.log_to_gui(
            f"Server started on {DEFAULT_HOST_NAME}:{self.running_port}. Access via LAN IPs."
        )

    def stop_server(self):
        if self.httpd:
            self.log_to_gui("Attempting to shut down server...")
            threading.Thread(target=self.httpd.shutdown, daemon=True).start()
            self.httpd.server_close()
            self.log_to_gui("Server shut down.")

        self.httpd = None
        self.server_thread = None
        global app_instance_ref
        app_instance_ref = None

        status_update = {"text": "Server Offline", "color": self.theme.current["ERROR"]}
        self.gui_queue.put({"type": "server_status", "content": status_update})
        self._generate_and_display_qr_code()  # Clear the QR code

    def _on_closing(self):
        if self.httpd:
            if messagebox.askokcancel(
                "Quit", "Server is running. Stop server and quit?"
            ):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LocalFetchServerApp(root)
    root.mainloop()
