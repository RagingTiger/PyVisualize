# NOTE: this command is specific to my Python environment (i.e. adapt to yours)
dmgbuild:
	dmgbuild -s settings.py -D app=`pwd`/dist/PyVisualize.app "PyVisualize" PyVisualize_MacOSX_10.11.6.dmg

pyinstall:
	pyinstaller -w pyvisualize.spec

clean: 
	rm -rf build dist
