import sys
import os
import threading

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web.app import app, update_data_loop

# Start Background Loop (triggers locally and in production)
t = threading.Thread(target=update_data_loop, daemon=True)
t.start()

if __name__ == "__main__":
    # Auto-open browser
    import webbrowser
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5004")
    threading.Timer(1.5, open_browser).start()
    
    print("Registered Routes:")
    print(app.url_map)
    
    app.run(debug=True, port=5004, threaded=True, use_reloader=False)
