# HTTPServer
Written for UW Networks & Distributed Computing class that serves up files on your hard drive.

**WARNING: DO NOT USE IN PRODUCTION!** Clients can request arbitrary files from your hard drive regardless of where they are located.

# Requirements
HTTPServer is intended for Python 3.10.9 on Arch Linux.

# Instructions
1. Eric, if you're actually reading this readme, could you leave a comment on Canvas or something? I'd feel kind of silly if I'm writing all this stuff for no reason.
2. (optional) Change the hostname and/or port. To do this, dind and change the line `HOST, PORT = "localhost", 80`. By default, the server runs on localhost on port 80.
3. Run `python3 HTTPServer.py`