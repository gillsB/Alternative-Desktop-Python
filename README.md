# Alternative-Desktop

Alternative Desktop

So far, a basic barebones example of how to create and build then distribute a python program

### Base Requirements: 
Python  
pip (https://pip.pypa.io/en/stable/installation/)  
pyinstaller (pip install pyinstaller)  
Inno setup compiler (https://jrsoftware.org/isdl.php)  

**Just for the example Requirements:**  
pyautogui (pip install pyautogui)  
requests (pip install requests) (github API for checking new releases)

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

###Install: 
run **Alternative Desktop Installer.exe** (or whatever you rename it)

###Uninstall: 
Uninstall through Platform default or by launching unins000.exe wherever you installed it  
(default directory: C:\Program Files (x86)\Alternative Desktop))


