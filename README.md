# LocalFetch

A simple system to easily transfer text between your devices using local network.

[![demo]]([https://youtu.be/vt5fpE0bzSY](https://github.com/user-attachments/assets/987b48b1-8cbb-40ca-9752-fb162d3d9456))

# How To Use

1. Run the server in a Windows OS (left side of the demo)
2. Run the Android/Windwos/Linux app in another device (right side of the demo)
3. Copy the address from server to ther first field of the app. You can get the ip:port from
    the qrcode on the top-right. It should in this format: `192.168.1.x:8000`
4. Either receive the text from the server or send a new one, as shown in the demo.

This way you can send and receive between your devices. Note that all of these devices
should be connected to the same network for this to work. It doesn't use any internet, It just requires
one so you can send data locally, the same way apps like Shareit work

# State Of The Project

The project is technically working correctly, but a few change need to be made:

1. More beautiful visuals, icons, etc.
2. Official exports for all devices. Currently it's more of a debug build, specially for android.

I'll work on these in my free time but I'm not sure how long it'd take. Any contribution is appreciated tho.

Note: In case you encounter weird codes, it's because I used AI for this project.

# Licence

This project is licensed under the GNU General Public License (GPL) v3. See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) for full terms.
