import os

def create_url_shortcut():
    try:
        # Standard way to get Desktop path in Windows
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, "AI Stock Market.url")
        
        # .url File Format (INI style)
        # IconIndex 14 in shell32.dll is usually a Globe/Network icon
        content = """[InternetShortcut]
URL=http://127.0.0.1:5001
IconIndex=14
IconFile=C:\\Windows\\System32\\shell32.dll
"""
        
        with open(path, 'w') as f:
            f.write(content)
        
        print(f"Successfully created shortcut at: {path}")
        print("Icon set to System Globe (Index 14)")
        
    except Exception as e:
        print(f"Error creating shortcut: {e}")

if __name__ == "__main__":
    create_url_shortcut()
