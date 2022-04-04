#!/usr/bin/env python3
"""App configuration."""
#!/usr/bin/env python3

class Config:
    """Set Flask configuration vars from .env file."""
    RFM69 = 'RFMGate.home'
    RFM69_CONFIG = 'http://'+ RFM69 + ':8001/config'
    RFM69_CONTROL = 'http://'+ RFM69 + ':8001/setValue'
    RFM69_CACHE = url = 'http://' + RFM69 + ':8001/cached'
    RADIO_URL = 'http://PiRadio.home:8001/postjson'
    NODES = {"Pumpe":11,"Weather":12}
    NODE_CACHE = {}
    #create empty cache
    for node in NODES.values(): 
        NODE_CACHE[str(node)] = None

    


