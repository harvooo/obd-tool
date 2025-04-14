import dearpygui.dearpygui as g
import random
import time
from collections import deque
import obd # Import obd library
from obd_connector import OBDConnector # Import the connector class

# --- OBD Connection Setup ---
obd_connector = OBDConnector()
ports = obd.scan_serial()
print(f"Available serial ports: {ports}")
selected_port = ports[0] if ports else None # Use the first found port

if selected_port:
    print(f"Attempting to connect to: {selected_port}")
    obd_connector.connect(selected_port)
else:
    print("No OBD adapter found. Please ensure it's connected.")
# --- End OBD Connection Setup ---


def print_me(sender):
    print(f"Menu Item: {sender}")

g.create_context()
g.create_viewport(title='OBD Tool', width=1280, height=720) # Changed title

# Hardcoded info (VIN removed, others remain for now)
# These could be replaced later by VIN decoding or other OBD commands
infoManu = "Audi" 
infoModel = "A4"
# infoVin = "WAUZZ00FH329JSA93JBN" # Removed hardcoded VIN
infoAge = 2008
infoEngine = "BRD"
infoBody = "Estate"
infoMiles = 192834 # Mileage might require a specific OBD command (PID 01A6 or manufacturer specific)

def viewTroubleCodesWindow():
    # TODO: Implement actual DTC fetching using obd_connector
    with g.window(label="Trouble Codes", width=600, height=300):
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
    # Fetch dynamic data from the connector
    # obd_connector.update_data() # Update RPM/Speed (VIN is async) - Moved to main loop
    current_vin = obd_connector.get_vin()

    with g.window(label="ECU Information", width=500, height=400):
        with g.table(header_row=False, borders_innerV=True, borders_outerH=True, borders_innerH=True):
            g.add_table_column(label="Name", width_fixed=True)
            g.add_table_column(label="Information", width_stretch=True)

            with g.table_row():
                g.add_text("Manufacturer")
                g.add_text(infoManu) # Keep placeholder for now
            with g.table_row():
                g.add_text("Model")
                g.add_text(infoModel) # Keep placeholder for now
            with g.table_row():
                g.add_text("VIN")
                # Use a text input to allow copying, make read-only if needed
                g.add_input_text(default_value=current_vin, readonly=True, width=-1, tag="vin_display") 
            with g.table_row():
                g.add_text("Production Date")
                g.add_text(f'{infoAge}') # Keep placeholder for now
            with g.table_row():
                g.add_text("Body type")
                g.add_text(infoBody) # Keep placeholder for now
            with g.table_row():
                g.add_text("Engine type")
                g.add_text(infoEngine) # Keep placeholder for now
            with g.table_row():
                g.add_text("Odometer (mls)")
                g.add_text(f"{infoMiles:,}") # Keep placeholder for now, format number
            with g.table_row():
                g.add_text("OBD Connection")
                status = "Connected" if obd_connector.connection and obd_connector.connection.is_connected() else "Disconnected"
                g.add_text(status, tag="connection_status_display")
            with g.table_row():
                g.add_text("OBD Port")
                g.add_text(selected_port if selected_port else "N/A")


# --- Data for Graphs (Example) ---
max_data_points = 100
rpm_data = deque([0.0] * max_data_points, maxlen=max_data_points)
time_data = deque([0.0] * max_data_points, maxlen=max_data_points) # Store relative time
start_time = time.time()

def update_graph_data():
    """ Call this periodically to update graph data sources """
    current_time = time.time() - start_time # Time since start
    
    if obd_connector.connection and obd_connector.connection.is_connected():
        # Get latest RPM from connector (already updated in main loop)
        current_rpm = obd_connector.rpm 
        rpm_data.append(current_rpm)
        time_data.append(current_time)
        
        # Update the series data if plot exists and is visible
        if g.does_item_exist("rpm_series") and g.is_item_visible("engine_rpm_plot"):
             g.set_value("rpm_series", [list(time_data), list(rpm_data)])
             # Adjust axes limits 
             g.set_axis_limits("rpm_time_axis", time_data[0], time_data[-1])
             min_rpm = min(rpm_data)
             max_rpm = max(rpm_data) 
             # Set practical limits, avoid clamping near zero unless data is truly zero
             y_min_limit = min_rpm - 500 if min_rpm > 500 else 0
             y_max_limit = max_rpm + 500 if max_rpm > 100 else 8000 # Default max if idle
             g.set_axis_limits("rpm_y_axis", y_min_limit, y_max_limit)
        
    else:
        # Append 0 or placeholder if not connected
        rpm_data.append(0.0) 
        time_data.append(current_time)
        # Optionally update graph to show disconnected state
        if g.does_item_exist("rpm_series") and g.is_item_visible("engine_rpm_plot"):
             g.set_value("rpm_series", [list(time_data), list(rpm_data)])
             g.set_axis_limits_auto("rpm_time_axis")
             g.set_axis_limits("rpm_y_axis", 0, 8000) # Reset to default range when disconnected


def ViewEngineRPMGraph():
    global rpm_data, time_data # Access global deques
    
    # Ensure data deques are initialized correctly before plotting
    if not list(time_data):
        initial_time = [0.0]
        initial_rpm = [0.0]
    else:
        initial_time = list(time_data)
        initial_rpm = list(rpm_data)
        
    with g.window(label="Engine RPM", width=700, height=500):
        # Check if plot exists, create if not
        if not g.does_item_exist("engine_rpm_plot"):
             with g.plot(label="Engine RPM Over Time", height=-1, width=-1, tag="engine_rpm_plot"): 
                g.add_plot_legend()
                g.add_plot_axis(g.mvXAxis, label="Time (s)", tag="rpm_time_axis")
                g.add_plot_axis(g.mvYAxis, label="RPM", tag="rpm_y_axis")
                g.add_line_series(initial_time, initial_rpm, label="RPM", parent="rpm_y_axis", tag="rpm_series")
                g.set_axis_limits_auto("rpm_time_axis")
                g.set_axis_limits("rpm_y_axis", 0, 8000) # Initial limits
        else:
            # If plot exists, ensure it's shown or handle appropriately
            # This part might be redundant if window creation implies showing
            pass 

# --- Placeholder functions for other graphs ---
def wheelSpeed():
     # TODO: Implement using obd_connector.speed
    print("Wheel Speed graph not implemented yet.")
    with g.window(label="Wheel Speed", width=600, height=400):
         g.add_text("Wheel Speed Data Unavailable")

def coolantTemp():
    # TODO: Implement using obd.commands.COOLANT_TEMP
    print("Coolant Temp graph not implemented yet.")
    with g.window(label="Coolant Temp", width=600, height=400):
         g.add_text("Coolant Temp Data Unavailable")

def oilTemp():
     # TODO: Implement using obd.commands.OIL_TEMP (if supported)
    print("Oil Temp graph not implemented yet.")
    with g.window(label="Oil Temp", width=600, height=400):
         g.add_text("Oil Temp Data Unavailable")
# --- End Placeholder functions ---


def viewGraphsWindow():
    with g.window(label="Live Data Graphs", width=500, height=150): # Adjusted size
        # Simple layout for buttons
        with g.group(horizontal=True):
            g.add_button(label="Engine RPM", callback=ViewEngineRPMGraph, width=100, height=60)
            g.add_button(label="Wheel Speed", callback=wheelSpeed, width=100, height=60)
        with g.group(horizontal=True):
            g.add_button(label="Coolant temp", callback=coolantTemp, width=100, height=60)
            g.add_button(label="Oil temp", callback=oilTemp, width=100, height=60)


# --- Menu Bar ---
with g.viewport_menu_bar():
    with g.menu(label="File"):
        g.add_menu_item(label="Save a report", callback=print_me) # Placeholder
        g.add_menu_item(label="Settings", callback=print_me) # Placeholder
        g.add_separator()
        g.add_menu_item(label="Exit", callback=lambda: g.stop_dearpygui())

    with g.menu(label="View"):
        # Using check boxes to toggle window visibility might be better
        # Or use menu items that create/focus the window
        g.add_menu_item(label="Trouble codes", callback=viewTroubleCodesWindow)
        g.add_menu_item(label="ECU Information", callback=viewECUInformationWindow)
        g.add_menu_item(label="Graphs", callback=viewGraphsWindow)

    g.add_menu_item(label="Help", callback=print_me) # Placeholder


# --- Dear PyGui Setup and Main Loop ---
g.setup_dearpygui()
g.show_viewport()

# Set theme (optional)
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
    print(f"Could not apply theme: {e}")

# Main loop
while g.is_dearpygui_running():
    # Call OBD update functions periodically
    obd_connector.update_data() # Update RPM/Speed 
    update_graph_data() # Update data for graphs

    # Update dynamic UI elements if they exist
    if g.does_item_exist("vin_display") and g.is_item_visible("vin_display"):
        g.set_value("vin_display", obd_connector.get_vin())
    if g.does_item_exist("connection_status_display") and g.is_item_visible("connection_status_display"):
        status = "Connected" if obd_connector.connection and obd_connector.connection.is_connected() else "Disconnected"
        g.set_value("connection_status_display", status)

    # Render the frame
    g.render_dearpygui_frame()

# --- Cleanup ---
print("Shutting down...")
obd_connector.close() # Close OBD connection gracefully
g.destroy_context()
print("Application closed.")
