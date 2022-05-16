import dearpygui.dearpygui as dpg
import numpy as np
import numpy.random as rand
from collections import namedtuple

dpg.create_context()
dpg.create_viewport(title='Gravity Tool', width=1280, height=720, resizable=False)
dpg.setup_dearpygui()


# region Global Variables

default_graph_scale = 50000
graph_scale = 50000
graph_center_x = 0
graph_center_y = 0

colors = [[68, 216, 0, 255],
          [255, 140, 0, 255],
          [127, 0, 255, 255],
          [255, 56, 0, 255],
          [167, 252, 0, 255],
          [175, 13, 211, 255],
          [255, 43, 103, 255],
          [255, 235, 0, 255],
          [0, 255, 206, 255],
          [255, 29, 206, 255]]

body_count = 1
body_color = colors[0]

Body = namedtuple('Body', 'id name x y mass color')
bodies = {}
body_names = []

selected_body = Body(0, "", 0, 0, 0, [0, 0, 0, 0])

# endregion


# region Item Update Wrapper Methods

def update_graph_position():
    dpg.set_axis_limits("x_axis", graph_center_x - graph_scale, graph_center_x + graph_scale)
    dpg.set_axis_limits("y_axis", graph_center_y - graph_scale, graph_center_y + graph_scale)


def update_graph_scale(_, value):
    global graph_scale
    graph_scale = value
    update_graph_position()


def update_graph_center_x(_, value):
    global graph_center_x
    graph_center_x = value
    update_graph_position()


def update_graph_center_y(_, value):
    global graph_center_y
    graph_center_y = value
    update_graph_position()


def update_selected_body_group():
    dpg.delete_item("selected_body_combo")
    dpg.add_combo(list(body_names), default_value=selected_body.name, tag="selected_body_combo", callback=select_body, parent="selected_body_group")

    dpg.delete_item("selected_body_circle")
    dpg.draw_circle((10, 9), 5, fill=selected_body.color, tag="selected_body_circle", parent="selected_body_drawlist")

    dpg.delete_item("selected_body_x_position_input")
    dpg.add_input_float(tag="selected_body_x_position_input", step=100, step_fast=1000, default_value=selected_body.x, parent="selected_body_x_group", callback=edit_body)

    dpg.delete_item("selected_body_y_position_input")
    dpg.add_input_float(tag="selected_body_y_position_input", step=100, step_fast=1000, default_value=selected_body.y, parent="selected_body_y_group", callback=edit_body)

    dpg.delete_item("selected_body_mass_input")
    dpg.add_input_float(tag="selected_body_mass_input", step=100, step_fast=1000, default_value=selected_body.mass, parent="selected_body_mass_group", callback=edit_body)

# endregion


# region Item Reset Wrapper Methods

def reset_slider_value(item_tag, value, slider_function):
    dpg.set_value(item_tag, value)
    slider_function(0, value)
    update_graph_position()


def reset_create_body_input():
    dpg.set_value("create_x_position_input", 0)
    dpg.set_value("create_y_position_input", 0)
    dpg.set_value("create_mass_input", 0)
    dpg.set_value("create_name_input", f"Body {body_count}")
    dpg.set_value("create_color_input", body_color)

# endregion


# region Item Callback Methods

def drag_body(body_id):
    body_x, body_y, z, w = dpg.get_value(body_id)
    body = bodies[body_id]
    edited_body = Body(body.id, body.name, body_x, body_y, body.mass, body.color)
    bodies[body_id] = edited_body

    global selected_body
    selected_body = edited_body

    update_selected_body_group()


def select_body(item_tag):
    body_name = dpg.get_value(item_tag)

    body_id = next(i for i in bodies if bodies[i].name == body_name)

    global selected_body
    selected_body = bodies[body_id]

    update_selected_body_group()


def edit_body():
    body_x = dpg.get_value("selected_body_x_position_input")
    body_y = dpg.get_value("selected_body_y_position_input")
    body_mass = dpg.get_value("selected_body_mass_input")

    body = Body(selected_body.id, selected_body.name, body_x, body_y, body_mass, selected_body.color)

    bodies[selected_body.id] = body
    dpg.set_value(selected_body.id, [body_x, body_y, 0, 0])


def create_body():
    body_name = dpg.get_value("create_name_input")
    body_x = dpg.get_value("create_x_position_input")
    body_y = dpg.get_value("create_y_position_input")
    body_mass = dpg.get_value("create_mass_input")
    color = dpg.get_value("create_color_input")

    body_id = dpg.add_drag_point(label=body_name, parent="main_graph", default_value=(body_x, body_y), color=color, callback=drag_body)

    body = Body(body_id, body_name, body_x, body_y, body_mass, color)

    global body_names
    body_names = np.append(body_names, body_name)

    global bodies
    bodies[body_id] = body

    print("Added body:", body)

    global body_count
    body_count += 1

    global body_color
    body_color = colors[(body_count - 1) % len(colors)]

    global selected_body
    selected_body = body

    reset_create_body_input()
    update_selected_body_group()

# endregion


# region DearPyGui Item Initiation

with dpg.window(label="Graph", width=681, height=681, no_resize=True, no_move=True, no_close=True, no_collapse=True):
    with dpg.plot(label="Top-Down View", height=-1, width=-1, tag="main_graph", callback=print):
        dpg.add_plot_axis(dpg.mvXAxis, label="x", tag="x_axis")
        dpg.set_axis_limits(dpg.last_item(), graph_center_x - default_graph_scale, graph_center_x + default_graph_scale)

        dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="y_axis")
        dpg.set_axis_limits(dpg.last_item(), -graph_center_y - default_graph_scale, graph_center_y + default_graph_scale)

with dpg.window(label="Settings", width=583, height=681, pos=(681, 0), no_resize=True, no_move=True, no_close=True, no_collapse=True):

    # region Graph Position Child Window

    with dpg.child_window(menubar=True, height=100):
        with dpg.menu_bar():
            dpg.add_text("Graph Controls")

        # Graph Scale Settings
        with dpg.group(horizontal=True):
            dpg.add_text("Scale   ")
            dpg.add_slider_float(width=435, min_value=0, max_value=100000, default_value=default_graph_scale, callback=update_graph_scale, tag="scale_slider")
            dpg.add_button(label="Reset", callback=lambda: reset_slider_value("scale_slider", default_graph_scale, update_graph_scale))

        with dpg.group(horizontal=True):
            dpg.add_text("X Center")
            dpg.add_slider_float(width=435, min_value=-100000, max_value=100000, default_value=0, callback=update_graph_center_x, tag="x_center_slider")
            dpg.add_button(label="Reset", callback=lambda: reset_slider_value("x_center_slider", 0, update_graph_center_x))

        with dpg.group(horizontal=True):
            dpg.add_text("Y Center")
            dpg.add_slider_float(width=435, min_value=-100000, max_value=100000, default_value=0, callback=update_graph_center_y, tag="y_center_slider")
            dpg.add_button(label="Reset", callback=lambda: reset_slider_value("y_center_slider", 0, update_graph_center_y))

    # endregion

    dpg.add_spacer()

    # region Create Body Child Window

    with dpg.child_window(menubar=True, height=173):
        with dpg.menu_bar():
            dpg.add_text("Create Body")

        with dpg.group(horizontal=True, width=-1):
            dpg.add_text("Name      ")
            dpg.add_input_text(tag="create_name_input", default_value=f"Body {body_count}")

        with dpg.group(horizontal=True, width=-1):
            dpg.add_text("X Position")
            dpg.add_input_float(tag="create_x_position_input", step=100, step_fast=1000)

        with dpg.group(horizontal=True, width=-1):
            dpg.add_text("Y Position")
            dpg.add_input_float(tag="create_y_position_input", step=100, step_fast=1000)

        with dpg.group(horizontal=True, width=-1):
            dpg.add_text("Mass      ")
            dpg.add_input_float(tag="create_mass_input", step=100, step_fast=1000)

        with dpg.group(horizontal=True, width=-1):
            dpg.add_text("Color     ")
            dpg.add_color_edit(tag="create_color_input", default_value=body_color)

        dpg.add_spacer()

        with dpg.group(horizontal=True):
            dpg.add_button(label="Create Body", width=367, callback=create_body)
            dpg.add_button(label="Reset", width=175, callback=reset_create_body_input)

    # endregion

    dpg.add_spacer()

    # region Edit Body Child Window

    with dpg.child_window(menubar=True, height=173):
        with dpg.menu_bar():
            dpg.add_text("Edit Body")

        with dpg.group(horizontal=True, tag="selected_body_group"):
            with dpg.drawlist(width=20, height=20, tag="selected_body_drawlist"):
                dpg.draw_circle((10, 9), 5, fill=selected_body.color, tag="selected_body_circle")
            dpg.add_combo(body_names, default_value="Select Body", tag="selected_body_combo", callback=select_body)

        with dpg.group(horizontal=True, width=-1, tag="selected_body_x_group"):
            dpg.add_text("X Position")
            dpg.add_input_float(tag="selected_body_x_position_input", step=100, step_fast=1000, default_value=selected_body.x, callback=edit_body)

        with dpg.group(horizontal=True, width=-1, tag="selected_body_y_group"):
            dpg.add_text("Y Position")
            dpg.add_input_float(tag="selected_body_y_position_input", step=100, step_fast=1000, default_value=selected_body.y, callback=edit_body)

        with dpg.group(horizontal=True, width=-1, tag="selected_body_mass_group"):
            dpg.add_text("Mass      ")
            dpg.add_input_float(tag="selected_body_mass_input", step=100, step_fast=1000, default_value=selected_body.mass, callback=edit_body)

    # endregion

# endregion


dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
