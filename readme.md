# GoodTime Python Visualisation
Created by Clément Raphin on 29 Nov. 2024 from an existing script by tmazzoni (SYRTE).

## How to use
Run the two commands:
D:\PythonProjects\_venvs\goodtimevis\Scripts\activate.bat
python D:\PythonProjects\goodTime_pyvis\goodTime_pyvis.py

### Explanation
This script needs to run in a virtual environment (see "requirements.txt").
On Sarocema Detection computer, this virtual environment is called "goodtimevis", and is located in
D:\PythonProjects\_venvs.
First command is to activate the virtual environment, second command runs the script.

## Principle
Each time a GoodTime sequence is executed, it will write analog & digital values to a set of buffers that are passed on to the NI cards.
Additionally, those buffers are written in the "goodTime_exchange" folder (on GoodTime PC: C:\homes\goodTime_exchange). This folder is accessible over a local network with the Detection computer.
This script then translates this data into user-readable values. It also includes a thread that updates data in real time whenever an update is detected.

Warning: In order for this to work, the "commondef" (file that contains correspondence between channel numbers and their name in goodtime) has to correspond to the one of the experiment. Please keep this in mind whenever changing channel numbering or naming in the commondef.