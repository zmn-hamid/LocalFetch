# LocalFetch

A simple system to easily transfer text between your devices using local network.

[demo](https://github.com/user-attachments/assets/987b48b1-8cbb-40ca-9752-fb162d3d9456)

# How To Use

Download the files needed as described bellow

1. Open port 8000 in your firewall so other devices in your local network can connect to it.
    For windows you can use `open_port_8000.bat` (Run as administrator), for linux it's `open_port_8000.sh`
2. Run the server in a Windows OS (the left window in the demo is the server)
3. Run the Android/Windwos/Linux app in another device (right side of the demo)
4. Copy the address from server to ther first field of the app. You can get the ip:port from
    the qrcode on the top-right. It should in this format: `192.168.1.x:8000` (in the demo i use the `Copy Addr` button to get this)
5. Either receive the text from the server or send a new one, as shown in the demo.

This way you can send and receive text between your devices. Note that all of these devices
should be connected to the same network for this to work. It doesn't use any website, it just require network
so you can send data locally within that network, the same way apps like Shareit work.

# State Of The Project

This project is technically working correctly, but a some change need to be made:

1. More beautiful visuals, icons, etc.
2. Official exports for all devices. Currently it's more of a debug build, specially for android.
3. Server exports for other devices, specially linux
4. Support for files as well

I'll work on these in my free time but I'm not sure how long it'd take. Any contribution is appreciated tho.

Note: In case you encounter weird codes, it's because I used AI for this project.

# Licence

This project is licensed under the GNU General Public License (GPL) v3. See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) for full terms.
