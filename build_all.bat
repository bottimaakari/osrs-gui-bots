echo START BUILD

@REM RUN BUILD PROCESSES

@REM RMDIR /S /Q .\build
RMDIR /S /Q .\dist

START /WAIT "NIGHTMARE" "%APPDATA%\Python\Python39\Scripts\pyinstaller.exe" --onefile .\nightmare\nightmare_clicker.py

START /WAIT "HUMIDIFY" "%APPDATA%\Python\Python39\Scripts\pyinstaller.exe" --onefile .\humidify\humidify_clicker.py

START /WAIT "WINE" "%APPDATA%\Python\Python39\Scripts\pyinstaller.exe" --onefile .\wine\wine_clicker.py

START /WAIT "SUPERGLASS" "%APPDATA%\Python\Python39\Scripts\pyinstaller.exe" --onefile .\superglass\superglass_clicker.py

START /WAIT "HIGH ALCHEMY" "%APPDATA%\Python\Python39\Scripts\pyinstaller.exe" --onefile .\high_alchemy\alchemy_clicker.py

@REM COPY DIST BINARIES WITH ASSETS TO CORRESPONDING DIRS

MKDIR .\dist\nightmare\
XCOPY /Y .\dist\nightmare_clicker.exe .\dist\nightmare\
XCOPY /Y .\nightmare\items-example.txt .\dist\nightmare\
XCOPY /Y .\nightmare\settings-example.txt .\dist\nightmare\

MKDIR .\dist\humidify\
XCOPY /Y .\dist\humidify_clicker.exe .\dist\humidify\
XCOPY /Y .\humidify\settings-example.txt .\dist\humidify\

MKDIR .\dist\wine\
XCOPY /Y .\dist\wine_clicker.exe .\dist\wine\
XCOPY /Y .\wine\settings-example.txt .\dist\wine\

MKDIR .\dist\superglass\
XCOPY /Y .\dist\superglass_clicker.exe .\dist\superglass\
XCOPY /Y .\humidify\settings-example.txt .\dist\superglass\

MKDIR .\dist\high_alchemy\
XCOPY /Y .\dist\alchemy_clicker.exe .\dist\high_alchemy\
XCOPY /Y .\high_alchemy\items-example.txt .\dist\high_alchemy\
XCOPY /Y .\high_alchemy\settings-example.txt .\dist\high_alchemy\

echo FINISHED BUILD
