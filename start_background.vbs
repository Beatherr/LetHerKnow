Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "change_this_to_file_location"  example: "C:\Users\poyra\OneDrive\Masaüstü\x"
WshShell.Run "pythonw.exe bot.py", 0, False
WshShell.Run "pythonw.exe client.py", 0, False
