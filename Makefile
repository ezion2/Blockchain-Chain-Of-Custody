
all:
	pip install pyinstaller					# found online as a solution to creating a python executable https://datatofish.com/executable-pyinstaller/
	pip install -r requirements.txt
	pyinstaller boot_info.py --onefile
	mv -f dist/* .							# automatically puts executable in dist directory, this moves all items into working directory
	chmod +x boot_info						# escalate permissions
