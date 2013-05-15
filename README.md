util.py
=======
Weitere erklährungen sind mit `./util.py -h` verfügbar.

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
