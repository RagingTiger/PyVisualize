run:
	pyinstaller -w PyVisualize.spec

clean: 
	rm -rf build dist
