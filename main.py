import dearpygui.dearpygui as g

def print_me(sender):
    print(f"Menu Item: {sender}")

g.create_context()
g.create_viewport(title='Custom Title', width=600, height=200)

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
    pass

def viewGraphsWindow():
    pass

with g.viewport_menu_bar():
    with g.menu(label="File"):
        g.add_menu_item(label="Save", callback=print_me)
        g.add_menu_item(label="Save As", callback=print_me)

        with g.menu(label="Settings"):
            g.add_menu_item(label="Setting 1", callback=print_me, check=True)
            g.add_menu_item(label="Setting 2", callback=print_me)

    g.add_menu_item(label="Help", callback=print_me)

    with g.menu(label="Widget Items"):
        g.add_checkbox(label="Pick Me", callback=print_me)
        g.add_button(label="Press Me", callback=print_me)
        g.add_color_picker(label="Color Me", callback=print_me)

    with g.menu(label="View"):
        g.add_checkbox(label="Trouble codes", callback=viewTroubleCodesWindow)
        g.add_checkbox(label="ECU Information", callback=viewECUInformationWindow)
        g.add_checkbox(label="Graphs", callback=viewGraphsWindow)



    

g.setup_dearpygui()
g.show_viewport()
g.start_dearpygui()
g.destroy_context()