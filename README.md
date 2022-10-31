This is a port of my [raspberry pi thermostat](https://github.com/GM-Script-Writer-62850/Raspberry_Pi_Thermostat)

* This exist case lightening killed my pi zero and there is a silicon shortage making them unobtainable

The contents of the PICO folder goes on the pico W

* The `gps_cords.py` file contains the location used for calculating sun set/rise
* The `wifi_auth.py` file contains the wifi SSID and passphrase
* `lib/request.py` is a patched version of `urequests.py`
* `lib/uasync_requests.py` is a patched version of my `request.py` patched for `uasyncio` support
* `main_with_async_urequests.py` is `main.py` patched to use `uasync_requests`
  * Not sure if doing that is a good idea, but it is unlikely to matter for this application
* Edit `remote_ip` and `remote_url` in `main.py` as needed




The contents of server folder goes on your local server
You will need to have a data folder in it with read/write access from the page

* `mkdir data`
* `chown www-data:www-data ./data`

All the server does is deal with logging data, showing log data, restoring data to the pico after it boots

note that this server is also running a ntp server server
* `sudo apt-get install ntp`