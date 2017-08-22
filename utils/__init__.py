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


finterop_banner = \
    """
      ______    _____       _                       
     |  ____|  |_   _|     | |                      
     | |__ ______| |  _ __ | |_ ___ _ __ ___  _ __  
     |  __|______| | | '_ \\| __/ _ \\ '__/ _ \\| '_ \\ 
     | |        _| |_| | | | ||  __/ | | (_) | |_) |
     |_|       |_____|_| |_|\\__\\___|_|  \\___/| .__/ 
                                             | |    
                                             |_|    
    """