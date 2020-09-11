from __future__ import absolute_import

from . import messages
from . import packet_dumper

import logging
import os

def get_from_environment(variable, default):
    if variable in os.environ:
        v = os.environ.get(variable)
        logging.info("Using environment variable %s=%s" % (variable, default))
    else:
        v = default
        logging.warning("Using default variable %s=%s" % (variable, default))
    return v


arrow_up = """
      _
     / \\
    /   \\
   /     \\
  /       \\
 /__     __\\   
    |   |              _ _       _      
    |   |             | (_)     | |         
    |   |  _   _ _ __ | |_ _ __ | | __        
    |   | | | | | '_ \| | | '_ \\| |/ /      
    |   | | |_| | |_) | | | | | |   <
    |   |  \__,_| .__/|_|_|_| |_|_|\_\\              
    |   |       | |           
    |   |       |_|                  
    !___!   
   \\  O  / 
    \\/|\/ 
      | 
     / \\
   _/   \\ _

"""

arrow_down = """
    ___       
   |   |       
   |   |       _                     _ _       _    
   |   |      | |                   | (_)     | |   
   |   |    __| | _____      ___ __ | |_ _ __ | | __
   |   |   / _` |/ _ \\ \\ /\\ / / '_ \\| | | '_ '\\| |/ /
   |   |  | (_| | (_) \\ V  V /| | | | | | | | |   < 
   |   |   \\__,_|\\___/ \\_/\\_/ |_| |_|_|_|_| |_|_|\_\\
   |   | 
 __!   !__,
 \\       / \O
  \\     / \/|
   \\   /    |
    \\ /    / \\
     Y   _/  _\\
"""

ioppytest_banner="""
  _                              _              _                                     _   
 (_)  ___   _ __   _ __   _   _ | |_  ___  ___ | |_         __ _   __ _   ___  _ __  | |_ 
 | | / _ \\ | '_ \\ | '_ \\ | | | || __|/ _ \\/ __|| __|_____  / _` | / _` | / _ \\| '_ \\ | __|
 | || (_) || |_) || |_) || |_| || |_|  __/\\__ \\| |_|_____|| (_| || (_| ||  __/| | | || |_ 
 |_| \\___/ | .__/ | .__/  \\__, | \\__|\\___||___/ \\__|       \\__,_| \\__, | \\___||_| |_| \\__|
           |_|    |_|     |___/                                   |___/
                      
"""

