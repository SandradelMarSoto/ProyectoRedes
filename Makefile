PYTHON = python3

.PHONY = help setup

FILES = input output

.DEFAULT_GOAL = help

help:
	@echo "Para configurar el proyecto escribe make setup"

setup:
	chmod +x install-deb.sh
	./install-deb.sh

runApp:
	chmod +x run-app.sh
	./run-app.sh

runServer:
	chmod +x run-server.sh
	./run-server.sh

genDoc:
	chmod +x gen-doc.sh
	./gen-doc.sh

clean:
	chmod +x clean.sh
	./clean.sh


