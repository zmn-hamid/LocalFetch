extends Node

@onready var ipport_input: LineEdit = %IPPort
@onready var text_to_send_input: TextEdit = %TextInput
@onready var send_button: Button = %SendButton
@onready var receive_button: Button = %ReceiveButton
@onready var text_output: TextEdit = %TextOutput
@onready var status_output: TextEdit = %TextStatus
@onready var http_request_node: HTTPRequest = %HTTPRequest

var server_base_url: String = ""
var _last_initiated_method: int # Will store HTTPClient.METHOD_GET or HTTPClient.METHOD_POST

func _ready():
    send_button.pressed.connect(_on_send_button_pressed)
    receive_button.pressed.connect(_on_receive_button_pressed)
    http_request_node.request_completed.connect(_on_request_completed)

    if OS.has_feature("debug"): # set ip port for faster debug
        ipport_input.text = "192.168.1.186:8000"
    
    _log_status("Client initialized. Enter Server IP:Port and send/receive text.")


func _log_status(message: String):
    var timestamp = Time.get_time_string_from_system() # Gets time like HH:MM:SS
    var new_log_entry = "[%s] %s" % [timestamp, message]
    
    if status_output.text.is_empty():
        status_output.text = new_log_entry
    else:
        status_output.text += "\n" + new_log_entry
    
    # Scroll to the bottom after the text has been updated
    # Using call_deferred to ensure UI update has happened before trying to scroll
    # status_output.call_deferred("_scroll_to_bottom")
    _scroll_to_bottom.call_deferred()

func _scroll_to_bottom():
    # Ensures the TextEdit scrolls to the latest message
    status_output.scroll_vertical = status_output.get_v_scroll_bar().max_value


func _update_server_url() -> bool:
    var ip_port_text = ipport_input.text.strip_edges()
    if ip_port_text.is_empty():
        _log_status("Error: Server IP:Port cannot be empty.")
        return false
    if not ip_port_text.begins_with("http://") and not ip_port_text.begins_with("https://"):
        server_base_url = "http://" + ip_port_text
    else:
        server_base_url = ip_port_text
    
    # Check if a port is present after the scheme (if any)
    var domain_part = server_base_url
    var scheme_end_idx = server_base_url.find("://")
    if scheme_end_idx != -1:
        domain_part = server_base_url.substr(scheme_end_idx + 3)
        
    if not ":" in domain_part or domain_part.rfind(":") <= domain_part.find("/"): # Ensure ':' is for port, not elsewhere in path
        _log_status("Error: Invalid IP:Port format. Ensure it includes a port (e.g., 127.0.0.1:8000 or http://127.0.0.1:8000).")
        return false
        
    return true


func _on_send_button_pressed():
    if not _update_server_url():
        return

    var url = server_base_url + "/text"
    var text_to_send = text_to_send_input.text

    if text_to_send.is_empty():
        _log_status("Error: Text to send is empty. Action aborted.")
        return

    var headers = ["Content-Type: text/plain; charset=utf-8"]
    
    _last_initiated_method = HTTPClient.METHOD_POST # Store the method
    var error = http_request_node.request(url, headers, HTTPClient.METHOD_POST, text_to_send)
    
    if error == OK:
        _log_status("Status: Sending text to %s..." % url)
    else:
        _last_initiated_method = -1 # Reset if request failed to start
        _log_status("Error: Failed to start send request. Code: %s" % error)
        push_error("HTTPRequest (POST) error: " + str(error))


func _on_receive_button_pressed():
    if not _update_server_url():
        return

    var url = server_base_url + "/text"
    
    _last_initiated_method = HTTPClient.METHOD_GET # Store the method
    var error = http_request_node.request(url, [], HTTPClient.METHOD_GET, "")
    
    if error == OK:
        _log_status("Status: Requesting text from %s..." % url)
    else:
        _last_initiated_method = -1 # Reset if request failed to start
        _log_status("Error: Failed to start receive request. Code: %s" % error)
        push_error("HTTPRequest (GET) error: " + str(error))


func _on_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray):
    if _result != HTTPRequest.RESULT_SUCCESS:
        _log_status("Connection Error: Request failed. Result code: %s. Check server address and network." % _result)
        push_error("HTTPRequest failed! Result: " + str(_result))
        _last_initiated_method = -1 # Reset on failure
        return

    var response_body_text = body.get_string_from_utf8()
    
    if response_code == 200: # HTTP OK
        if _last_initiated_method == HTTPClient.METHOD_GET:
            text_output.text = response_body_text # Update the separate output field
            _log_status("Status: Text received successfully from server.")
        elif _last_initiated_method == HTTPClient.METHOD_POST:
            _log_status("Status: Text sent. Server confirmation: \"%s\"" % response_body_text)
        else:
            _log_status("Status: Request successful (Code %s), unknown method. Server response: \"%s\"" % [response_code, response_body_text])
    
    elif response_code == 0: # This often indicates connection refused or host not found at TCP level
        _log_status("Connection Error: No response from server (Code 0). Is it running at the correct IP:Port, or is a firewall blocking?")
        push_error("Server error 0: No response or connection refused. Body (if any): %s" % response_body_text)

    else: # Other HTTP error codes from the server
        _log_status("Server Error (Code %s): %s" % [response_code, response_body_text])
        push_error("Server error %s: %s" % [response_code, response_body_text])
    
    _last_initiated_method = -1 # Reset after handling


func _unhandled_input(event: InputEvent):
    if ipport_input.has_focus() and event.is_action_pressed("ui_accept"):
        _on_receive_button_pressed() # Trigger receive on Enter in IP field
        get_viewport().set_input_as_handled()
    elif text_to_send_input.has_focus() and event.is_action_pressed("ui_accept") and event.is_command_or_control_pressed():
        _on_send_button_pressed() # Trigger send on Ctrl/Cmd+Enter in text input field
        get_viewport().set_input_as_handled()
