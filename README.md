# Proxy Herd Application
Application server herd "prototype" for [UCLA CS 131 (Programming Languages) course](http://web.cs.ucla.edu/classes/fall17/cs131/hw/pr.html)

## Instructions
To run *all servers* at once you can simply run:
`python3 main.py`

To run only *a particular server* you would run:
`python3 main.py Alford`

Where Alford would be any valid server name given in the Project spec

Please also note that we need to run **main.py** and *not* server.py like in the spec

The servers then will log all of its inputs and  outputs onto their corresponding <name>-log.txt starting from when their server is created.

The following servers are connected to these ports:
- Alford - 16540
- Ball - 16541
- Hamilton - 16542
- Holiday - 16543
- Welsh - 16544

The client messages also must have a newline at the end for it to be valid.
