@echo off
chcp 65001 > nul
cd /d "change_this_to_folder_name" example: "C:\Users\poyra\OneDrive\Masaüstü\x"
start /b pythonw.exe bot.py
start /b pythonw.exe client.py
