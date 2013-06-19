test.py
=======
Wie testen:

1. in test.py die folgende Zeile anpassen und dort './meshnode.py' mit dem Pfad zur eigenen Implementation ersetzen

	implementations = [ './meshnode.py' ]

2. Test starten via

       python test.py

3. weitere Hilfe via

	python test.py --help
	usage: test.py [-h] [-v] [n_intermediates] [n_sources] [n_sinks] [n_messages]
	
	Mesh network test harness. Please edit the variable "implementations" at the
	top of this file to test with additional/alternative mesh implementations.
	
	positional arguments:
	  n_intermediates  connecting nodes
	  n_sources        source nodes
	  n_sinks          sink nodes
	  n_messages       # of messages to send
	
	optional arguments:
	  -h, --help       show this help message and exit
	  -v               be verbose

util.py
=======
Weitere Erklärungen sind mit `./util.py -h` verfügbar.

zwei lokale Nodes verbinden
---------------------------
Loggt sich im lokalen Node auf Port 3333 ein und sagt ihm er soll sich mit dem lokalen Node auf port 3334 verbinden.

	python util.py connect 3333 3334


mehrere lokale Nodes hintereinander hängen
------------------------------------------
Verbindet 6 Nodes beginnend ab Port 3333 seriel miteinander (3333 mit 3334, 3334 mit 3335, 3335 mit 3336, ...)

	python util.py connect_line 3333 6


ein Paket an Quelle oder an Ziel senden
---------------------------------------
Logt sich am Node auf Port 3333 und sendet ihm ein Paket mit id 14 welches an die Quelle (0) oder ans Ziel (1) und wartet auf eine Antwort (irgend eine Antwort)

	python util.py send_packet 3333 1  14


n Pakete senden
---------------
Gleich wie `send_packet` einfach mit zusätzlichem count Parameter

meshnode.py
===========

Benötigt [twisted](http://twistedmatrix.com/trac/ "twisted framework") um zu laufen. Unter Debian kann dieses installiert werden via:

	apt-get install python-twisted-bin

Danach Verwendung wie folgt:

	python meshnode.py -z 3333
