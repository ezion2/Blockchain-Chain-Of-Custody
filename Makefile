all:
	pip install pyinstaller					# found online as a solution to creating a python executable https://datatofish.com/executable-pyinstaller/
	pip install -r requirements.txt
	pyinstaller cli.py --onefile --name bchoc
	mv -f dist/* .							# automatically puts executable in dist directory, this moves all items into working directory
	chmod +x bchoc						# escalate permissions
