# LocalFetch

A simple system to easily transfer text between your devices using local network.

https://github.com/user-attachments/assets/527864ea-8d57-4d77-8443-0a9f07db13e7

# How To Use

Download the files needed as described bellow, from the "Releases" section.

1. Open port 8000 in your firewall so other devices in your local network can connect to it.
    For windows you can use `open_port_8000.bat` (Run as administrator), for linux it's `open_port_8000.sh`
2. Run the server (LocalFetchServer) in a Windows OS (the left side in the demo is the server)
3. Run the Android/Windwos/Linux app in another device (right side of the demo)
4. Copy the address from server to ther first field of the app. You can get the ip:port from
    the qrcode as well. It should be in this format: `192.168.1.x:8000`
5. Either receive the text from the server or send a new one, as shown in the demo.

This way you can send and receive text between your devices within a local network (The same way apps like Shareit work).

# State Of The Project

This project is technically working correctly, but a some change need to be made:

1. Official exports for all devices. Currently it's more of a debug build, specially for android.
2. Server exports for other devices, specially linux
3. Support for files as well
4. QR Code Scanner (This is pretty hard to do with Godot)

I'll work on these in my free time but I'm not sure how long it'd take. Any contribution is appreciated tho.
Python 3.13 + Godot 4.4 is used

Note: In case you encounter weird codes, it's because I used AI for this project.

# Licence

This project is licensed under the MIT License.
