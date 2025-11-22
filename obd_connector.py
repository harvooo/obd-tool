# obd_connector.py with logging and fake data capability
import obd
import logging
import random
import time

# Get a logger instance (it will inherit handlers from the root logger configured in main.py)
logger = logging.getLogger(__name__) # Use module-specific logger is good practice

# ---- Fake OBD Data Simulation Classes ----

class FakeQuantity:
    """A fake pint.Quantity-like object to simulate OBD response values."""
    def __init__(self, magnitude, units=None):
        self.magnitude = magnitude
        self.units = units

class FakeOBDResponse:
    """A fake obd.OBDResponse to simulate responses from the OBD device."""
    def __init__(self, value, unit=None):
        if value is None:
            self.value = None
        elif isinstance(value, bytes):  # For VIN, which is bytes
            self.value = value
        else:
            self.value = FakeQuantity(value, unit)

    def is_null(self):
        return self.value is None

class FakeOBDConnection:
    """A fake obd.Async connection that simulates a real OBD-II adapter for testing."""
    def __init__(self, *args, **kwargs):
        self._is_connected = False
        self.vin_callback = None
        # Simulate supported_commands as a dictionary-like object
        class SupportedCommands:
            def get(self, key, default=None):
                if hasattr(key, 'name') and key.name == "VIN":
                    return True
                return default
        self.supported_commands = SupportedCommands()

    def watch(self, command, callback):
        """Mocks watching for a command, specifically VIN."""
        if command.name == "VIN":
            self.vin_callback = callback

    def start(self):
        """Starts the fake connection and simulates receiving a VIN."""
        self._is_connected = True
        logger.info("Fake OBD connection started.")
        if self.vin_callback:
            # Simulate VIN callback after a short delay
            time.sleep(0.2)
            fake_vin_response = FakeOBDResponse("FAKEVIN1234567890".encode('latin-1'))
            self.vin_callback(fake_vin_response)
            logger.info("Fake VIN sent to callback.")


    def is_connected(self):
        """Returns the connection status."""
        return self._is_connected

    def query(self, command):
        """Mocks querying a command and returns simulated data."""
        if not self.is_connected():
            return FakeOBDResponse(None)

        if command.name == "RPM":
            return FakeOBDResponse(random.uniform(800, 3500), "rpm")
        elif command.name == "SPEED":
            return FakeOBDResponse(random.uniform(0, 120), "kph")
        return FakeOBDResponse(None) # Return a null response for other commands

    def stop(self):
        """Stops the fake connection."""
        self._is_connected = False
        logger.info("Fake OBD connection stopped.")

    def close(self):
        """Closes the fake connection."""
        self._is_connected = False
        logger.info("Fake OBD connection closed.")


class OBDConnector:
    def __init__(self):
        self.connection = None
        self.rpm = 0.0
        self.speed = 0.0
        self.vin = "N/A" # Initialize VIN attribute

    def connect(self, port=None, use_fake_data=False):
        """ Establishes a connection to the OBD interface (real or fake). """
        if use_fake_data:
            logger.info("Using fake OBD data source.")
            self.connection = FakeOBDConnection()
        else:
            logger.info(f"Attempting to connect to real OBD interface on port: {port}")
            try:
                self.connection = obd.Async(portstr=port, fast=False, timeout=30)
            except Exception as e:
                logger.error(f"Failed to initialize obd.Async: {e}", exc_info=True)
                self.connection = None
                return False

        try:
            self.connection.watch(obd.commands.VIN, callback=self.set_vin)
            self.connection.start() 

            # Give a brief moment for initial connection status
            # time.sleep(0.5) # Optional short delay

            if not self.connection.is_connected() and not use_fake_data:
                 logger.warning("Connection not established immediately. Async process running. Check logs.")
                 
            logger.info("OBD Async connection process started. Watching for VIN...")
            return True # Indicate attempt started

        except Exception as e:
            logger.error(f"Connection error during setup: {e}", exc_info=True) # Log exception info
            if self.connection and not use_fake_data:
                self.connection.stop()
                self.connection.close()
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
            self.rpm = 0.0
            self.speed = 0.0

    def close(self):
        """ Stops the asynchronous connection and closes the serial port. """
        if self.connection:
            logger.info("Closing OBD connection...")
            self.connection.stop() 
            self.connection.close()
            self.connection = None
            logger.info("OBD connection closed.")
