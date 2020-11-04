Send NMEA0183 as AIS report
===========================

To be able to display some item that we receive NMEA data from on a navigation program this small ptyhon project uses the position information from some NMEA0183 sentences and sends them out as AIS type 1 and type 5 messages via udp.
Some of the parameters for the AIS message you can provide at the command line.

Installation
------------
You need python 2.x. Clone this repo.
Additionaly you need to install the following python packages:

* bitstring
* serial
* pynmea2

Eiher install them using pip or your package manager.

Usage
-----
    nmea-ais.py -r ser:/dev/ttyUSB0:9600 udp:localhost:34667 mmsi=277799911 shiptype=sail
or
    
    nmea-ais.py -r tcp:localhost:34567 udp:localhost:34667 mmsi=277799911 shiptype=sail    

With the first call the program receices NMEA data from /dev/ttyUSB0 and sends out the AIS messages to localhost, port 34667.
With the second call it receives data via tcp from localhost, port 34567.
The AIS messages will be sent out whenever a valid NMEA position report is received.

The following flags are supported:
* -r - retry forever (e.g. when the port cannot be opened on start)
* -d - output debug messages

Supported AIS parameters
------------------------
The following AIS parameters are supported:
* mmsi
* shipname
* callsign
* destination
* shiptype - refer to [the source](nmea-ais.py) for a list of supported types

If the destination is not set on the commandline a string containing the current altitude will be used.

Systemd unit file
-----------------
To support automated startup you can copy the file nmeaais.service to /etc/systemd/system and adapt it to your path and port parameters.
Afterwards run the following commands:
    
    sudo systemctl daemon-reload
    sudo systemctl enable nmeaais
    sudo systemctl start nmeaais





