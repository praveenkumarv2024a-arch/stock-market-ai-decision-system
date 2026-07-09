import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.web.app import update_data_loop
# We will just start it and let it run, we can look at the console output
update_data_loop()
