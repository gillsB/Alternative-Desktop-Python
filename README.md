# Alternative-Desktop

Alternative Desktop

# All current development is based on desktop_grid.py

I am making sure desktop_grid.py is good before adding it to the base application (AlternativeDesktop.py)
To run this file:   
```py desktop_grid.py```

Will probably not do a new release until desktop_grid.py is added to the base application.

previews so far: 

Adding a new icon: Left click any + on the screen, and you can drag and drop any file or manually enter the fields.
If it is an .lnk (shortcut file) or a .exe it will auto generate an image so long as you leave the icon path empty
![adding a new icon](readme/new_icon.gif)


To edit an icon you can right click an existing icon
![editng an icon](readme/edit.gif)


icon row, column, name, icon_path, and executable_path are all saved at:   
```C:/Users/UserName/AppData/Roaming/AlternativeDesktop/config/desktop.json```   
I am still working on a lot of error catching and implementation so if the program fails to start check here first.   

auto generated icons are stored at:   
```C:/Users/UserName/AppData/Roaming/AlternativeDesktop/data```   

### Base Requirements: 
Python  
pip (https://pip.pypa.io/en/stable/installation/)  
pyinstaller (pip install pyinstaller)  
Inno setup compiler (https://jrsoftware.org/isdl.php)  
requests   	(pulling updates from github, pip install requests)
Pyside6 	(Qt for Python, pip install PySide6)   
pylnk3		(for getting icons from .lnk files, pip install pylnk3)   
PIL 		(Python Imaging Library, pip install pillow)   
icoextract  (Extracting icons from .exe, pip install icoextract)

### Step 1: Building .exe
open command prompt

cd to file location i.e. C:\...\github\Alternative-Desktop

pyinstaller --onefile --noconsole AlternativeDesktop.py

Should create the folders: build, dist, and AlternativeDesktop.spec the important one being the .exe in /dist/

### Step 2: Inno setup

Install Inno Setup and open AlternativeDesktopInstaller_Example.iss in Inno Setup Compiler.

Generate a new GUID through Tools -> Generate GUID

Replace **GUID** in the Example file with the generated GUID

### Step 3: To make this into installer
Click Build -> compile, To get the Installer exe

### Install: 
run **Alternative Desktop Installer.exe** (or whatever you rename it)

### Uninstall: 
Uninstall through Platform default or by launching unins000.exe wherever you installed it  
(default directory: C:\Program Files (x86)\Alternative Desktop))


