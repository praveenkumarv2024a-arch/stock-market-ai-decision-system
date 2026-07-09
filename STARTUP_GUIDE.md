# How to Auto-Start the Stock Dashboard

To make the dashboard open automatically when you log in to Windows, follow these steps:

## 1. Test the Script
1. Go to your project folder: `c:\stock market`
2. Double-click **`start_dashboard.bat`**.
3. A black window (CMD) should appear, and you should see "Running on http://127.0.0.1:5004".
4. Open your browser to http://127.0.0.1:5004 to verify it's working.

## 2. Add to Windows Startup (Hidden Mode)
To ensure the black window doesn't bother you:
1. **Right-click** on **`start_dashboard_hidden.vbs`** (not the .bat file) and select **Create shortcut**.
2. Press `Win + R` on your keyboard to open the Run dialog.
3. Type **`shell:startup`** and press Enter.
4. **Drag and drop** the shortcut you created into this Startup folder.

## Stopping the Server
Since the window is hidden, if you need to stop the server:
- Double-click **`stop_dashboard.bat`** in the project folder.
