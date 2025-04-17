import dearpygui.dearpygui as g
import random
import time
from collections import deque
import obd # Import obd library
from obd_connector import OBDConnector # Import the connector class
import logging # Import logging

# --- Logging Setup ---
# Create a custom handler to store logs
class ListHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_records = deque(maxlen=200) # Store last 200 records

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_records.append(msg)
        except Exception:
            self.handleError(record)

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
list_handler = ListHandler()
list_handler.setFormatter(log_formatter)

# Get the root logger and add the custom handler
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO) # Set the desired level
root_logger.addHandler(list_handler)

# Also add a console handler for debugging if needed
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(log_formatter)
# root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__) # Logger for this main module
# --- End Logging Setup ---

# --- Global Variables ---
obd_connector = None
selected_port = None
# --- End Global Variables ---


def startConnection():
    global obd_connector, selected_port # Use global variables
# --- OBD Connection Setup ---
    obd_connector = OBDConnector() # Modify the global instance
    ports = obd.scan_serial()
    logger.info(f"Available serial ports: {ports}") # Use logger
    selected_port = ports[0] if ports else None # Modify the global variable
    if selected_port:
        logger.info(f"Attempting to connect to: {selected_port}") # Use logger
        obd_connector.connect(selected_port)
    else:
        logger.warning("No OBD adapter found. Please ensure it's connected.") # Use logger

startConnection() # Attempt initial connection

# --- End OBD Connection Setup ---

def closeConnection():
    global obd_connector # Use global variable
    if obd_connector:
        obd_connector.close()
        logger.info("OBD connection closed.")
    else:
        logger.warning("Attempted to close connection, but no connector object exists.")


g.create_context()
g.create_viewport(title='OBD Tool', width=1280, height=720) # Changed title

# Hardcoded info (VIN removed, others remain for now)
infoManu = "Audi"
infoModel = "A4"
infoAge = 2008
infoEngine = "BRD"
infoBody = "Estate"
infoMiles = 192834 # Mileage might require a specific OBD command (PID 01A6 or manufacturer specific)

# Window visibility state (used for checkboxes)
window_visibility = {
    "Trouble Codes": False,
    "ECU Information": False,
    "Graphs": False,
    "Logger": False
}

def toggle_window(sender, app_data, user_data):
    """Callback to toggle window visibility based on menu checkbox"""
    window_label = user_data
    is_visible = g.get_value(sender) # Checkbox state
    window_visibility[window_label] = is_visible

    window_tag = f"window_{window_label.replace(' ', '_')}" # Consistent tag generation

    if g.does_item_exist(window_tag):
        if is_visible:
            g.show_item(window_tag)
            # Bring to front? Might not be strictly necessary if just shown
            # g.focus_item(window_tag) # Doesn't work directly on windows
        else:
            g.hide_item(window_tag)
    elif is_visible:
        # If window doesn't exist and we want to show it, call the creation function
        if window_label == "Trouble Codes":
            viewTroubleCodesWindow()
        elif window_label == "ECU Information":
            viewECUInformationWindow()
        elif window_label == "Graphs":
            viewGraphsWindow()
        elif window_label == "Logger":
             viewLoggerWindow()
        # Ensure the newly created window's visibility matches the checkbox
        #if g.does_item_exist(window_tag):
        #    g.set_item_callback(window_tag, lambda s, a, u: on_window_close(u, window_label)) # Set close callback
        #    g.set_item_user_data(window_tag, window_tag) # Set user data for close callback


def on_window_close(sender, app_data, user_data):
    """Callback when a window is closed via the 'X' button"""
    window_label = user_data # Get the label passed from toggle_window
    window_visibility[window_label] = False
    # Update the corresponding menu checkbox
    menu_item_tag = f"menu_{window_label.replace(' ', '_')}"
    if g.does_item_exist(menu_item_tag):
        g.set_value(menu_item_tag, False)


def viewTroubleCodesWindow():
    window_label = "Trouble Codes"
    window_tag = f"window_{window_label.replace(' ', '_')}"
    if g.does_item_exist(window_tag):
        if not g.is_item_visible(window_tag):
             g.show_item(window_tag)
        # g.focus_item(window_tag) # Bring to front?
        return

    # TODO: Implement actual DTC fetching using obd_connector
    with g.window(label=window_label, width=600, height=300, tag=window_tag,
                  on_close=lambda s, a, u: on_window_close(s, a, window_label)): # Pass label to close callback
        g.set_item_user_data(window_tag, window_label) # Needed?
        with g.table(header_row=True, row_background=True, borders_innerH=True, borders_outerH=True, borders_outerV=True):
            g.add_table_column(label="Code")
            g.add_table_column(label="Status")
            g.add_table_column(label="Description")

            # --- Placeholder Data ---
            with g.table_row():
                g.add_text("P0101")
                g.add_text("Active")
                g.add_text("Mass Airflow Circuit Range/Performance Problem")
            with g.table_row():
                g.add_text("P0171")
                g.add_text("Inactive")
                g.add_text("System Too Lean (Bank 1)")
            with g.table_row():
                g.add_text("P0300")
                g.add_text("Active")
                g.add_text("Random/Multiple Cylinder Misfire Detected")
            # --- End Placeholder ---

def viewECUInformationWindow():
    global obd_connector, selected_port # Need access to globals
    window_label = "ECU Information"
    window_tag = f"window_{window_label.replace(' ', '_')}"
    if g.does_item_exist(window_tag):
        if not g.is_item_visible(window_tag):
             g.show_item(window_tag)
        # Update dynamic data when shown
        if obd_connector: # Check if connector exists
            if g.does_item_exist("vin_display"):
                 g.set_value("vin_display", obd_connector.get_vin())
            if g.does_item_exist("connection_status_display"):
                 status = "Connected" if obd_connector.connection and obd_connector.connection.is_connected() else "Disconnected"
                 g.set_value("connection_status_display", status)
            if g.does_item_exist("port_display"): # Add tag for port display
                 g.set_value("port_display", selected_port if selected_port else "N/A")
        # g.focus_item(window_tag)
        return

    current_vin = obd_connector.get_vin() if obd_connector else "N/A"
    current_status = "Connected" if obd_connector and obd_connector.connection and obd_connector.connection.is_connected() else "Disconnected"
    current_port = selected_port if selected_port else "N/A"

    with g.window(label=window_label, width=500, height=400, tag=window_tag,
                  on_close=lambda s, a, u: on_window_close(s, a, window_label)):
        g.set_item_user_data(window_tag, window_label)
        with g.table(header_row=False, borders_innerV=True, borders_outerH=True, borders_innerH=True):
            g.add_table_column(label="Name", width_fixed=True)
            g.add_table_column(label="Information", width_stretch=True)

            with g.table_row(): g.add_text("Manufacturer"); g.add_text(infoManu)
            with g.table_row(): g.add_text("Model"); g.add_text(infoModel)
            with g.table_row():
                g.add_text("VIN")
                g.add_input_text(default_value=current_vin, readonly=True, width=-1, tag="vin_display")
            with g.table_row(): g.add_text("Production Date"); g.add_text(f'{infoAge}')
            with g.table_row(): g.add_text("Body type"); g.add_text(infoBody)
            with g.table_row(): g.add_text("Engine type"); g.add_text(infoEngine)
            with g.table_row(): g.add_text("Odometer (mls)"); g.add_text(f"{infoMiles:,}")
            with g.table_row():
                g.add_text("OBD Connection")
                g.add_text(current_status, tag="connection_status_display")
            with g.table_row():
                g.add_text("OBD Port")
                g.add_text(current_port, tag="port_display") # Tag added

# --- Data for Graphs (Example) ---
max_data_points = 100
rpm_data = deque([0.0] * max_data_points, maxlen=max_data_points)
time_data = deque([0.0] * max_data_points, maxlen=max_data_points) # Store relative time
start_time = time.time()
last_graph_update_time = 0
graph_update_interval = 0.2 # Update graph data every 0.2 seconds

def update_graph_data():
    """ Call this periodically to update graph data sources """
    global last_graph_update_time, obd_connector # Need global connector
    current_time_abs = time.time()

    # Limit update frequency
    if current_time_abs - last_graph_update_time < graph_update_interval:
        return

    last_graph_update_time = current_time_abs
    current_time_rel = current_time_abs - start_time # Time since start

    if obd_connector and obd_connector.connection and obd_connector.connection.is_connected():
        current_rpm = obd_connector.rpm # Get latest RPM (updated in main loop)
        rpm_data.append(current_rpm)
        time_data.append(current_time_rel)

        # Update the series data only if the plot exists and is visible
        if g.does_item_exist("engine_rpm_plot") and g.is_item_visible("engine_rpm_plot"):
             if g.does_item_exist("rpm_series"):
                 g.set_value("rpm_series", [list(time_data), list(rpm_data)])
                 # Adjust axes limits dynamically but avoid jittering
                 try: # Add try-except for safety if time_data becomes empty
                     g.set_axis_limits("rpm_time_axis", time_data[0], time_data[-1])
                 except IndexError:
                     pass # Don't update limits if data is empty
                 min_rpm = min(rpm_data) if rpm_data else 0
                 max_rpm = max(rpm_data) if rpm_data else 0
                 y_min_limit = min_rpm - 500 if min_rpm > 500 else 0
                 y_max_limit = max_rpm + 500 if max_rpm > 100 else 8000 # Default max if idle
                 # Only update if limits significantly change? Or just set them.
                 g.set_axis_limits("rpm_y_axis", y_min_limit, y_max_limit)

    else:
        # Append 0 or placeholder if not connected
        rpm_data.append(0.0)
        time_data.append(current_time_rel)
        # Update graph to show disconnected state if visible
        if g.does_item_exist("engine_rpm_plot") and g.is_item_visible("engine_rpm_plot"):
             if g.does_item_exist("rpm_series"):
                try: # Add try-except for safety
                     g.set_value("rpm_series", [list(time_data), list(rpm_data)])
                     # g.set_axis_limits_auto("rpm_time_axis") # Auto time when disconnected? Maybe keep last range?
                     g.set_axis_limits("rpm_time_axis", time_data[0], time_data[-1]) # Keep time range
                     g.set_axis_limits("rpm_y_axis", 0, 8000) # Reset to default range
                except IndexError:
                    pass # Don't update if data is empty

def ViewEngineRPMGraph():
    window_label = "Engine RPM Graph" # Give graph its own window
    window_tag = f"window_{window_label.replace(' ', '_')}"

    if g.does_item_exist(window_tag):
        if not g.is_item_visible(window_tag):
            g.show_item(window_tag)
        # g.focus_item(window_tag)
        return

    # Ensure data deques are initialized correctly before plotting
    initial_time = list(time_data) if time_data else [0.0]
    initial_rpm = list(rpm_data) if rpm_data else [0.0]

    with g.window(label=window_label, width=700, height=500, tag=window_tag,
                  on_close=lambda s,a,u: g.hide_item(window_tag)): # Just hide on close? Or manage via menu?

        with g.plot(label="Engine RPM Over Time", height=-1, width=-1, tag="engine_rpm_plot"):
            g.add_plot_legend()
            g.add_plot_axis(g.mvXAxis, label="Time (s)", tag="rpm_time_axis")
            g.add_plot_axis(g.mvYAxis, label="RPM", tag="rpm_y_axis")
            # Ensure parent axis exists before adding series
            g.add_line_series(initial_time, initial_rpm, label="RPM", parent="rpm_y_axis", tag="rpm_series")
            g.set_axis_limits_auto("rpm_time_axis")
            g.set_axis_limits("rpm_y_axis", 0, 8000) # Initial limits

# --- Placeholder functions for other graphs ---
def wheelSpeed():
    logger.info("Wheel Speed graph not implemented yet.") # Use logger
    with g.window(label="Wheel Speed", width=600, height=400, show=True): # Show immediately
         g.add_text("Wheel Speed Data Unavailable")

def coolantTemp():
    logger.info("Coolant Temp graph not implemented yet.") # Use logger
    with g.window(label="Coolant Temp", width=600, height=400, show=True):
         g.add_text("Coolant Temp Data Unavailable")

def oilTemp():
     logger.info("Oil Temp graph not implemented yet.") # Use logger
     with g.window(label="Oil Temp", width=600, height=400, show=True):
         g.add_text("Oil Temp Data Unavailable")
# --- End Placeholder functions ---

def viewGraphsWindow():
    window_label = "Graphs"
    window_tag = f"window_{window_label.replace(' ', '_')}"
    if g.does_item_exist(window_tag):
        if not g.is_item_visible(window_tag):
            g.show_item(window_tag)
        # g.focus_item(window_tag)
        return

    with g.window(label=window_label, width=500, height=150, tag=window_tag,
                   on_close=lambda s, a, u: on_window_close(s, a, window_label)):
        g.set_item_user_data(window_tag, window_label)
        # Simple layout for buttons to *open* graph windows
        with g.group(horizontal=True):
            g.add_button(label="Engine RPM", callback=ViewEngineRPMGraph, width=100, height=60)
            g.add_button(label="Wheel Speed", callback=wheelSpeed, width=100, height=60)
        with g.group(horizontal=True):
            g.add_button(label="Coolant temp", callback=coolantTemp, width=100, height=60)
            g.add_button(label="Oil temp", callback=oilTemp, width=100, height=60)


def update_logger_window_content():
    """Updates the content of the logger window if it's visible and logs changed."""
    global last_log_count
    window_tag = "window_Logger"
    output_tag = "logger_output"

    if g.does_item_exist(window_tag) and g.is_item_visible(window_tag):
        if g.does_item_exist(output_tag):
            current_log_count = len(list_handler.log_records)
            # Only update if the number of logs has changed
            if current_log_count != last_log_count:
                log_text = "
".join(list(list_handler.log_records))
                g.set_value(output_tag, log_text)
                # Auto-scroll? DPG doesn't have easy auto-scroll for input_text.
                # A child window with auto-scroll might be better if needed.
                last_log_count = current_log_count

# --- Logger Window ---
last_log_count = 0

def viewLoggerWindow():
    global last_log_count
    window_label = "Logger"
    window_tag = f"window_{window_label.replace(' ', '_')}"

    if g.does_item_exist(window_tag):
        if not g.is_item_visible(window_tag):
            g.show_item(window_tag)
            # Force update content when shown
            last_log_count = -1 # Ensure update happens
            update_logger_window_content()
        # g.focus_item(window_tag)
        return

    # Create the window
    with g.window(label=window_label, width=800, height=400, tag=window_tag,
                  on_close=lambda s, a, u: on_window_close(s, a, window_label)):
        g.set_item_user_data(window_tag, window_label)
        g.add_button(label="Retry Connection", callback=startConnection, width=150, height=25)
        g.add_same_line()
        g.add_button(label="Close Connection", callback=closeConnection, width=150, height=25)
        # Read-only text area to display logs
        g.add_input_text(tag="logger_output", multiline=True, readonly=True, width=-1, height=-1, default_value="")
        # Initialize content
        last_log_count = -1
        update_logger_window_content()

# Open logger window upon startup
viewLoggerWindow()

def print_me():
    pass


# --- Menu Bar ---
with g.viewport_menu_bar():
    with g.menu(label="File"):
        g.add_menu_item(label="Save a report", callback=print_me) # Placeholder
        g.add_menu_item(label="Settings", callback=print_me) # Placeholder
        g.add_separator()
        g.add_menu_item(label="Exit", callback=lambda: g.stop_dearpygui())

    with g.menu(label="View"):
        # Use checkboxes linked to the toggle_window callback
        g.add_menu_item(label="Trouble Codes", check=True, default_value=window_visibility["Trouble Codes"],
                        callback=toggle_window, user_data="Trouble Codes", tag="menu_Trouble_Codes")
        g.add_menu_item(label="ECU Information", check=True, default_value=window_visibility["ECU Information"],
                        callback=toggle_window, user_data="ECU Information", tag="menu_ECU_Information")
        g.add_menu_item(label="Graphs", check=True, default_value=window_visibility["Graphs"],
                        callback=toggle_window, user_data="Graphs", tag="menu_Graphs")
        g.add_menu_item(label="Logger", check=True, default_value=window_visibility["Logger"],
                        callback=toggle_window, user_data="Logger", tag="menu_Logger") # Add logger toggle

    g.add_menu_item(label="Help", callback=print_me) # Placeholder


# --- Dear PyGui Setup and Main Loop ---
g.setup_dearpygui()
g.show_viewport()

# Set theme (optional)
# ... (theme code remains the same) ...
try:
    with g.theme() as global_theme:
        with g.theme_component(g.mvAll):
            g.add_theme_style(g.mvStyleVar_WindowPadding, 8, 8, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_FramePadding, 4, 3, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_ItemSpacing, 8, 4, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_CellPadding, 4, 2, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_GrabMinSize, 10, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_WindowBorderSize, 1, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_ChildBorderSize, 1, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_PopupBorderSize, 1, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_FrameBorderSize, 0, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_TabBorderSize, 0, category=g.mvThemeCat_Core)
            g.add_theme_style(g.mvStyleVar_WindowRounding, 4, category=g.mvThemeCat_Core)
            # ... add more styling ...
    g.bind_theme(global_theme)
except Exception as e:
    logger.error(f"Could not apply theme: {e}") # Use logger


# Main loop
data_update_interval = 0.5 # How often to query OBD data (seconds)
last_data_update = 0

logger.info("Starting Dear PyGui main loop...") # Use logger
while g.is_dearpygui_running():
    current_time = time.time()

    # Call OBD update functions periodically
    if current_time - last_data_update > data_update_interval:
        if obd_connector: # Check if connector exists before using it
            obd_connector.update_data() # Update RPM/Speed
        last_data_update = current_time

        # Update dynamic UI elements if they exist and are visible
        if obd_connector and window_visibility["ECU Information"] and g.does_item_exist("window_ECU_Information") and g.is_item_visible("window_ECU_Information"):
            if g.does_item_exist("vin_display"):
                g.set_value("vin_display", obd_connector.get_vin())
            if g.does_item_exist("connection_status_display"):
                status = "Connected" if obd_connector.connection and obd_connector.connection.is_connected() else "Disconnected"
                g.set_value("connection_status_display", status)
            if g.does_item_exist("port_display"): # Update port display too
                 g.set_value("port_display", selected_port if selected_port else "N/A")

    # Update graph data (handles its own timing)
    update_graph_data()

    # Update logger window content (handles its own logic)
    update_logger_window_content()


    # Render the frame
    g.render_dearpygui_frame()

# --- Cleanup ---
logger.info("Shutting down...") # Use logger
closeConnection() # Call the modified close function
g.destroy_context()
logger.info("Application closed.") # Use logger
