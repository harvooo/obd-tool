import dearpygui.dearpygui as g
import random
import time
from collections import deque
def print_me(sender):
    print(f"Menu Item: {sender}")

g.create_context()
g.create_viewport(title='Custom Title', width=1280, height=720)

infoManu = "Audi"
infoModel = "A4"
infoVin = "WAUZZ00FH329JSA93JBN"
infoAge = 2008
infoEngine = "BRD"
infoBody = "Estate"
infoMiles = 192834

def viewTroubleCodesWindow():
    with g.window(label="Trouble Codes"):
        with g.table(header_row=True, row_background=True, borders_innerH=True, borders_outerH=True, borders_outerV=True):
            g.add_table_column(label="Code")
            g.add_table_column(label="Status")
            g.add_table_column(label="Description")

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

def viewECUInformationWindow():
    with g.window(label="ECU Information"):
        with g.table():
            g.add_table_column(label="Name")
            g.add_table_column(label="Information")

            with g.table_row():
                g.add_text("Manufacturer")
                g.add_text(infoManu)
            with g.table_row():
                g.add_text("Model")
                g.add_text(infoModel)
            with g.table_row():
                g.add_text("VIN")
                g.add_text(infoVin)
            with g.table_row():
                g.add_text("Production Date")
                g.add_text(f'{infoAge}')
            with g.table_row():
                g.add_text("Body type")
                g.add_text(infoBody)
            with g.table_row():
                g.add_text("Engine type")
                g.add_text(infoEngine)
            with g.table_row():
                g.add_text("Odometer (mls)")
                g.add_text(infoMiles)
            

def ViewEngineRPMGraph():
    with g.window(label="Graph Window", width=600, height=400):
        # Create a plot
        with g.plot(label="Line Graph", height=300, width=500):
            # Add x and y axes
            g.add_plot_axis(g.mvXAxis, label="X Axis")
            g.add_plot_axis(g.mvYAxis, label="Y Axis", id="y_axis")

            # Generate some random data
            x_data = list(range(10))
            y_data = [random.randint(0, 100) for _ in range(10)]

            # Add a line series to the plot
            g.add_line_series(x_data, y_data, label="Random Data", parent="y_axis")

def wheelSpeed():
    pass
def coolantTemp():
    pass
def oilTemp():
    pass

def viewGraphsWindow():
    with g.window(label="Graphs", width=500, height=500):
        with g.table(header_row=False):
            g.add_table_column()
            g.add_table_column()
            g.add_table_column()
            g.add_table_column()


            with g.table_row():
                g.add_button(label="Engine RPM", callback=ViewEngineRPMGraph, width=90, height=60)
                g.add_button(label="Wheel Speed", callback=wheelSpeed, width=90, height=60)
                g.add_button(label="Coolant temp", callback=coolantTemp, width=90, height=60)
                g.add_button(label="Oil temp", callback=oilTemp, width=90, height=60)

    

with g.viewport_menu_bar():
    with g.menu(label="File"):
        g.add_menu_item(label="Save a report", callback=print_me)
        g.add_menu_item(label="Personalisation", callback=print_me)
        g.add_menu_item(label="Settings", callback=print_me)

    with g.menu(label="View"):
        g.add_checkbox(label="Trouble codes", callback=viewTroubleCodesWindow)
        g.add_checkbox(label="ECU Information", callback=viewECUInformationWindow)
        g.add_checkbox(label="Graphs", callback=viewGraphsWindow)

    g.add_menu_item(label="Help", callback=print_me)



    

g.setup_dearpygui()
g.show_viewport()
g.start_dearpygui()
g.destroy_context()