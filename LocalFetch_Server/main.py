import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import queue
import time
import qrcode  # For QR code generation
from PIL import Image, ImageTk  # For displaying QR code in Tkinter
import io  # For handling image data in memory

# --- Configuration ---
DEFAULT_HOST_NAME = "0.0.0.0"  # Listen on all available network interfaces
DEFAULT_PORT_NUMBER = 8000
# ---------------------

app_instance_ref = None


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


class LocalFetchServerApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Local Fetch Server")
        self.root.geometry("750x550")

        self.shared_text_data = "Hello from the Python server GUI!"
        self.server_thread = None
        self.httpd = None
        self.running_port = (
            DEFAULT_PORT_NUMBER  # Set default, confirmed by start_server
        )
        self.preferred_ip = "N/A"
        self.all_ips = []

        self.gui_queue = queue.Queue()
        self.qr_image_tk = None

        self._setup_gui()
        self.update_shared_text_display()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._process_gui_queue()
        self._update_ip_info()  # Initial IP fetch for display

        self.start_server()  # Start server automatically

    def _get_local_ips(self):
        """Gets all non-loopback IPv4 addresses and prioritizes 192.168.x.x."""
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
        self.ip_display_var.set(self.preferred_ip if self.preferred_ip else "N/A")

        if hasattr(self, "all_ips_label"):  # Check if GUI is setup
            other_ips_list = [ip for ip in self.all_ips if ip != self.preferred_ip]
            self.all_ips_label.config(
                text=(
                    f"Other IPs: {', '.join(other_ips_list)}"
                    if other_ips_list
                    else "Other IPs: None found"
                )
            )

        if self.httpd:  # Check if server is actually running
            self._generate_and_display_qr_code()

    def _copy_ip(self):
        ip_to_copy = self.ip_display_var.get()
        if ip_to_copy and ip_to_copy != "N/A":
            if self.httpd:  # Only copy if server is confirmed running
                full_address = f"{ip_to_copy}:{self.running_port}"
                self.root.clipboard_clear()
                self.root.clipboard_append(full_address)
                self.log_to_gui(f"Copied '{full_address}' to clipboard.")
            else:
                self.log_to_gui("Cannot copy address: Server is not running.")
        else:
            self.log_to_gui("No valid IP to copy.")

    def _generate_and_display_qr_code(self):
        if self.preferred_ip != "N/A" and self.httpd:
            server_address_for_qr = f"{self.preferred_ip}:{self.running_port}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            qr.add_data(server_address_for_qr)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)

            pil_image_for_tk = Image.open(img_byte_arr)
            self.qr_image_tk = ImageTk.PhotoImage(pil_image_for_tk)

            self.qr_label.config(
                image=self.qr_image_tk,
                width=pil_image_for_tk.width,
                height=pil_image_for_tk.height,
            )
            self.qr_label.image = self.qr_image_tk
            self.log_to_gui(f"QR code updated for: {server_address_for_qr}")
        else:
            if hasattr(self, "qr_label") and self.qr_label:
                self.qr_label.config(image="")
                self.qr_label.image = None
            # self.log_to_gui("QR code cleared (server not running or no IP).") # Can be noisy

    def _setup_gui(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        controls_frame = tk.Frame(top_frame)
        controls_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        server_control_frame = tk.Frame(controls_frame, pady=5)
        server_control_frame.pack(fill=tk.X)
        tk.Label(server_control_frame, text="Port:").pack(side=tk.LEFT, padx=(0, 5))

        self.port_display_var = tk.StringVar(value=str(DEFAULT_PORT_NUMBER))
        self.port_entry = tk.Entry(
            server_control_frame,
            textvariable=self.port_display_var,
            width=6,
            state="readonly",
        )
        self.port_entry.pack(side=tk.LEFT, padx=5)

        ip_frame = tk.Frame(controls_frame, pady=5)
        ip_frame.pack(fill=tk.X)
        tk.Label(ip_frame, text="Server IP:").pack(side=tk.LEFT, padx=(0, 5))
        self.ip_display_var = tk.StringVar(value="N/A")
        self.ip_display_entry = tk.Entry(
            ip_frame, textvariable=self.ip_display_var, state="readonly", width=15
        )
        self.ip_display_entry.pack(side=tk.LEFT, padx=5)
        self.copy_ip_button = tk.Button(  # Renamed button
            ip_frame, text="Copy Addr", command=self._copy_ip, width=10
        )
        self.copy_ip_button.pack(side=tk.LEFT, padx=5)
        self.refresh_ip_button = tk.Button(
            ip_frame, text="Refresh IPs", command=self._update_ip_info, width=10
        )
        self.refresh_ip_button.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            controls_frame,
            text="Initializing Server...",
            fg="orange",
            pady=2,
            anchor="w",
        )
        self.status_label.pack(fill=tk.X)
        self.all_ips_label = tk.Label(
            controls_frame,
            text="Other available IPs will be listed here.",
            fg="gray",
            pady=2,
            anchor="w",
            wraplength=450,
            justify=tk.LEFT,
        )
        self.all_ips_label.pack(fill=tk.X)

        self.qr_label = tk.Label(
            top_frame,
            text="QR will appear here\nwhen server starts",
            relief=tk.SUNKEN,
            width=18,
            height=9,
        )
        self.qr_label.pack(side=tk.RIGHT, padx=(10, 0))

        shared_text_frame = tk.LabelFrame(
            self.root, text="Current Shared Text", padx=10, pady=10
        )
        shared_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.shared_text_display = scrolledtext.ScrolledText(
            shared_text_frame, height=5, wrap=tk.WORD, state=tk.DISABLED
        )
        self.shared_text_display.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        update_text_subframe = tk.Frame(shared_text_frame)
        update_text_subframe.pack(fill=tk.X)
        self.gui_text_input = tk.Entry(update_text_subframe, width=50)
        self.gui_text_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.update_text_button = tk.Button(
            update_text_subframe,
            text="Update Text (from GUI)",
            command=self.update_shared_text_from_gui,
        )
        self.update_text_button.pack(side=tk.LEFT)

        log_frame = tk.LabelFrame(self.root, text="Server Log", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_area = scrolledtext.ScrolledText(
            log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def log_to_gui(self, message):
        self.gui_queue.put({"type": "log", "content": message})

    def get_shared_text(self):
        return self.shared_text_data

    def update_shared_text(self, new_text, from_client=False):
        self.shared_text_data = new_text
        source = "Client" if from_client else "GUI Admin"
        log_msg = f"{source} updated shared text: '{new_text}'"
        self.gui_queue.put({"type": "shared_text_update", "content": log_msg})

    def update_shared_text_from_gui(self):
        new_text = self.gui_text_input.get()
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
                message_item = self.gui_queue.get_nowait()
                msg_type = message_item.get("type")
                content = message_item.get("content")

                if msg_type == "log":
                    self._append_to_log_area(content)
                elif msg_type == "shared_text_update":
                    self.update_shared_text_display()
                    self._append_to_log_area(content)
                elif msg_type == "server_status":
                    self.status_label.config(
                        text=content.get("text"), fg=content.get("color")
                    )
                    if "ip" in content:
                        self.ip_display_var.set(
                            content["ip"] if content["ip"] else "N/A"
                        )

                    if (
                        "all_ips" in content and "ip" in content
                    ):  # Ensure primary IP is also there for comparison
                        other_ips_list = [
                            ip for ip in content["all_ips"] if ip != content.get("ip")
                        ]
                        self.all_ips_label.config(
                            text=(
                                f"Other IPs: {', '.join(other_ips_list)}"
                                if other_ips_list
                                else "Other IPs: None found"
                            )
                        )
                    elif (
                        "all_ips" in content
                    ):  # Fallback if primary IP not in content but all_ips is
                        self.all_ips_label.config(
                            text=f"Other IPs: {', '.join(content['all_ips'])}"
                        )

                    if self.httpd:
                        self._generate_and_display_qr_code()
                    else:
                        if hasattr(self, "qr_label") and self.qr_label:
                            self.qr_label.config(image="")
                            self.qr_label.image = None
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
        self.port_display_var.set(str(self.running_port))  # Ensure display is correct

        server_address = (DEFAULT_HOST_NAME, self.running_port)
        try:
            global app_instance_ref
            app_instance_ref = self
            self.httpd = HTTPServer(server_address, LocalFetchHandler)
        except OSError as e:
            messagebox.showerror(
                "Server Error",
                f"Failed to start server on port {self.running_port}: {e}\n(Port might be in use or IP binding issue)",
            )
            self.gui_queue.put(
                {
                    "type": "log",
                    "content": f"Failed to start server on port {self.running_port}: {e}",
                }
            )
            # Update status to reflect failure
            current_pref_ip, current_all_ips = (
                self._get_local_ips()
            )  # Get current IPs for status
            status_update_fail = {
                "text": f"Server Failed on Port {self.running_port}",
                "color": "red",
                "ip": current_pref_ip,
                "all_ips": current_all_ips,
            }
            self.gui_queue.put({"type": "server_status", "content": status_update_fail})
            app_instance_ref = None
            self.httpd = None  # Ensure httpd is None on failure
            return

        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()

        pref_ip, all_other_ips = self._get_local_ips()
        self.preferred_ip = pref_ip
        self.all_ips = all_other_ips
        self.ip_display_var.set(self.preferred_ip if self.preferred_ip else "N/A")

        status_update = {
            "text": f"Server Running on {self.preferred_ip}:{self.running_port}",
            "color": "green",
            "ip": self.preferred_ip,
            "port": self.running_port,
            "all_ips": self.all_ips,
        }
        self.gui_queue.put({"type": "server_status", "content": status_update})

        self.log_to_gui(
            f"Server started. Listening on {DEFAULT_HOST_NAME}:{self.running_port}"
        )
        self.log_to_gui(f"Access via: {self.preferred_ip}:{self.running_port}")
        if self.all_ips:
            self.log_to_gui(f"All detected non-loopback IPs: {', '.join(self.all_ips)}")

    def stop_server(self):
        if self.httpd:
            self.log_to_gui("Attempting to shut down server...")
            shutdown_thread = threading.Thread(target=self.httpd.shutdown)
            shutdown_thread.daemon = True
            shutdown_thread.start()
            shutdown_thread.join(timeout=5)
            self.httpd.server_close()
            self.log_to_gui("Server socket closed.")

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)
            if self.server_thread.is_alive():
                self.log_to_gui("Warning: Server thread did not exit cleanly.")

        self.httpd = None
        self.server_thread = None
        global app_instance_ref
        app_instance_ref = None

        current_pref_ip, current_all_ips = (
            self._get_local_ips()
        )  # Get current IPs for status
        status_update = {
            "text": "Server Offline",
            "color": "red",
            "ip": current_pref_ip,  # Show current IP even if server is offline
            "all_ips": current_all_ips,
        }
        self.gui_queue.put({"type": "server_status", "content": status_update})
        self.log_to_gui("Server stopped.")

    def _on_closing(self):
        if self.httpd and self.server_thread and self.server_thread.is_alive():
            if messagebox.askokcancel(
                "Quit", "Server is running. Stop server and quit?"
            ):
                self.stop_server()
                self.root.destroy()
        else:
            # Call stop_server even if httpd is None to ensure consistent state update (e.g. status label)
            self.stop_server()
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LocalFetchServerApp(root)
    root.mainloop()
