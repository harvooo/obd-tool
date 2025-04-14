# obd_connector.py with logging
import obd
import logging

# Get a logger instance (it will inherit handlers from the root logger configured in main.py)
logger = logging.getLogger(__name__) # Use module-specific logger is good practice

class OBDConnector:
    def __init__(self):
        self.connection = None
        self.rpm = 0.0
        self.speed = 0.0
        self.vin = "N/A" # Initialize VIN attribute

    def connect(self, port=None):
        """ Establishes an asynchronous connection to the OBD interface and watches for VIN. """
        logger.info(f"Attempting to connect to OBD interface on port: {port}")
        try:
            self.connection = obd.Async(portstr=port, fast=False, timeout=30) 
            self.connection.watch(obd.commands.VIN, callback=self.set_vin)
            self.connection.start() 

            # Give a brief moment for initial connection status
            # time.sleep(0.5) # Optional short delay

            if not self.connection.is_connected():
                 logger.warning("Connection not established immediately. Async process running. Check logs.")
                 
            logger.info("OBD Async connection process started. Watching for VIN...")
            return True # Indicate attempt started

        except Exception as e:
            logger.error(f"Connection error during setup: {e}", exc_info=True) # Log exception info
            self.connection = None 
            return False

    def set_vin(self, r):
        """ Callback function to update the VIN when received. """
        if not r.is_null() and r.value:
            try:
                decoded_vin = r.value.decode('latin-1', errors='ignore') 
                if self.vin != decoded_vin: # Log only if VIN changes
                     self.vin = decoded_vin
                     logger.info(f"VIN Received/Updated: {self.vin}")
            except AttributeError:
                 vin_str = str(r.value)
                 if self.vin != vin_str:
                     self.vin = vin_str
                     logger.info(f"VIN Received/Updated (as string): {self.vin}")
            except Exception as e:
                logger.error(f"Error decoding VIN: {e}")
                self.vin = "Error Decoding"
        else:
            # Log only if status changes from a valid VIN to unavailable
            if self.vin not in ["N/A", "Not Available", "Error Decoding"]:
                 logger.warning("VIN became unavailable.")
            self.vin = "Not Available"
        

    def get_vin(self):
        """ Returns the currently stored VIN. """
        if not self.connection:
             return "Not Connected"
        # Async connection might take time, status reflects this
        if not self.connection.is_connected():
             # Check support status if connection exists but isn't 'connected'
             vin_support = self.connection.supported_commands.get(obd.commands.VIN)
             if vin_support is False: # Explicitly False means ECU reported unsupported
                 self.vin = "Unsupported by ECU"
                 return self.vin
             else: # Still trying or unknown
                  return "Connecting..." 
        
        # If connected but VIN is still initial value, might be waiting for callback
        if self.vin == "N/A": 
            return "Waiting for VIN..."
            
        return self.vin

    def update_data(self):
        """ Fetches latest RPM and Speed. VIN is updated by the watcher. """
        if self.connection and self.connection.is_connected():
            try:
                response_rpm = self.connection.query(obd.commands.RPM) 
                self.rpm = response_rpm.value.magnitude if not response_rpm.is_null() else 0.0

                response_speed = self.connection.query(obd.commands.SPEED)
                self.speed = response_speed.value.magnitude if not response_speed.is_null() else 0.0
            except Exception as e:
                 # Log errors less frequently or only if they persist?
                 logger.error(f"Error querying RPM/Speed: {e}", exc_info=False) # exc_info=False to reduce noise
        else:
            # Don't log repeatedly if just disconnected
            pass

    def close(self):
        """ Stops the asynchronous connection and closes the serial port. """
        if self.connection:
            logger.info("Closing OBD connection...")
            self.connection.stop() 
            self.connection.close()
            self.connection = None
            logger.info("OBD connection closed.")
