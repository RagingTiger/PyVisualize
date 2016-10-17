# NOTE: this command is specific to my Python environment (i.e. adapt to yours)
dmgbuild:
	deactivate
	dmgbuild -s settings.py -D app=`pwd`/dist/PyVisualize.app "PyVisualize" PyVisualize_MacOSX_10.11.6.dmg
	cd .

pyinstall:
	pyinstaller -w PyVisualize.spec

clean: 
	rm -rf build dist
