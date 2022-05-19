import dearpygui.dearpygui as dpg
import numpy as np
import astropy.constants as const
from collections import namedtuple

# region Global Definitions and Variables

Body = namedtuple('Body', ['id', 'name', 'position', 'velocity', 'mass', 'color'])
Vec2 = namedtuple('Vector2', ['x', 'y'])

default_graph_scale = 11.5
graph_scale = 11.5
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

bodies = {}
body_names = []

selected_body = Body(0, "", Vec2(0, 0), Vec2(0, 0), 0, [0, 0, 0, 0])

reset = True

# endregion


# region Physical Models and Calculations

def n_body_grav_accel(body, n_bodies):
    accel_sum_x = 0
    accel_sum_y = 0

    for n_body in n_bodies:
        r = np.sqrt((body.position.x - n_body.position.x) ** 2 + (body.position.y - n_body.position.y) ** 2)
        scaler = -(const.G.value * n_body.mass) / r ** 3

        accel_sum_x += (body.position.x - n_body.position.x) * scaler
        accel_sum_y += (body.position.y - n_body.position.y) * scaler

    return Vec2(accel_sum_x, accel_sum_y)


def current_body(body, position, velocity):
    return Body(body.id, body.name, position, velocity, body.mass, body.color)


def reset_trajectories():
    for body_key, body_value in bodies.items():
        if dpg.does_item_exist(f"line_{body_key}"):
            dpg.delete_item(f"line_{body_key}")

        if dpg.does_item_exist(f"line_theme_{body_key}"):
            dpg.delete_item(f"line_theme_{body_key}")

        dpg.set_value(body_key, body_value.position)

        with dpg.theme(tag=f"line_theme_{body_key}"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, body_value.color, category=dpg.mvThemeCat_Plots)

        dpg.add_line_series([], [], parent="y_axis", tag=f"line_{body_key}")

        dpg.bind_item_theme(f"line_{body_key}", f"line_theme_{body_key}")

    global reset
    reset = True


def calculate_trajectories():
    reset_trajectories()

    global reset
    reset = False

    h = dpg.get_value("step_size")
    sim_time = dpg.get_value("sim_time")
    update_freq = dpg.get_value("update_freq")

    body_positions = {}
    body_velocities = {}
    body_accelerations = {}

    for body_key, body_value in bodies.items():
        body_positions[body_key] = [Vec2(0, 0) for _ in range(0, sim_time)]

        body_positions[body_key][0] = body_value.position

        body_velocities[body_key] = [Vec2(0, 0) for _ in range(0, sim_time)]
        body_velocities[body_key][0] = body_value.velocity

        body_accelerations[body_key] = [Vec2(0, 0) for _ in range(0, sim_time)]
        n_bodies = [value for key, value in bodies.items() if key != body_key]

        body_accelerations[body_key][0] = n_body_grav_accel(body_value, n_bodies)

    for i in range(0, sim_time - 1):
        for body_key, body_value in bodies.items():
            body = current_body(body_value, body_positions[body_key][i], body_velocities[body_key][i])

            n_bodies = [current_body(value, body_positions[key][i], body_velocities[key][i]) for key, value in bodies.items() if key != body_key]

            accel = body_accelerations[body_key][i]

            x = body.position.x + body.velocity.x * h + accel.x * (h * h * 0.5)
            y = body.position.y + body.velocity.y * h + accel.y * (h * h * 0.5)
            new_position = Vec2(x, y)

            new_accel = n_body_grav_accel(body, n_bodies)

            vx = body.velocity.x + (accel.x + new_accel.x) * (h / 2)
            vy = body.velocity.y + (accel.y + new_accel.y) * (h / 2)
            new_velocity = Vec2(vx, vy)

            body_positions[body_key][i + 1] = new_position
            body_velocities[body_key][i + 1] = new_velocity
            body_accelerations[body_key][i + 1] = new_accel

            if i % update_freq == 0:
                x_pos = [r.x for r in body_positions[body_key]]
                y_pos = [r.y for r in body_positions[body_key]]

                dpg.set_value(f"line_{body_key}", [x_pos[0:i + 1], y_pos[0:i + 1]])
                dpg.set_value(body_key, [x_pos[i + 1], y_pos[i + 1]])

        dpg.set_value("sim_progress", i / (sim_time - 1))


# endregion


# region GUI Setup and Logic

dpg.create_context()
dpg.create_viewport(title='Gravity Tool', width=1280, height=720, resizable=False)
dpg.setup_dearpygui()


# region Item Update Wrapper Methods

def update_graph_position():
    dpg.set_axis_limits("x_axis", graph_center_x - graph_scale, graph_center_x + graph_scale)
    dpg.set_axis_limits("y_axis", graph_center_y - graph_scale, graph_center_y + graph_scale)


def update_graph_scale(_, value):
    global graph_scale
    graph_scale = 1 * 10 ** value
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
    dpg.add_combo(body_names, default_value=selected_body.name, tag="selected_body_combo", callback=select_body, parent="selected_body_group")

    dpg.delete_item("selected_body_circle")
    dpg.draw_circle((10, 9), 5, fill=selected_body.color, tag="selected_body_circle", parent="selected_body_drawlist")

    dpg.delete_item("selected_body_x_input")
    dpg.add_input_float(tag="selected_body_x_input", step=100, step_fast=1000, default_value=selected_body.position.x, width=217, parent="selected_body_x_group", callback=edit_body)

    dpg.delete_item("selected_body_y_input")
    dpg.add_input_float(tag="selected_body_y_input", step=100, step_fast=1000, default_value=selected_body.position.y, width=217, parent="selected_body_y_group", callback=edit_body)

    dpg.delete_item("selected_body_vx_input")
    dpg.add_input_float(tag="selected_body_vx_input", step=100, step_fast=1000, default_value=selected_body.velocity.x, width=217, parent="selected_body_vx_group", callback=edit_body)

    dpg.delete_item("selected_body_vy_input")
    dpg.add_input_float(tag="selected_body_vy_input", step=100, step_fast=1000, default_value=selected_body.velocity.y, width=217, parent="selected_body_vy_group", callback=edit_body)

    dpg.delete_item("selected_body_mass_input")
    dpg.add_input_float(tag="selected_body_mass_input", step=100, step_fast=1000, default_value=selected_body.mass, parent="selected_body_mass_group", callback=edit_body)

# endregion


# region Item Reset Wrapper Methods

def reset_slider_value(item_tag, value, slider_function):
    dpg.set_value(item_tag, value)
    slider_function(0, value)
    update_graph_position()


def reset_create_body_input():
    dpg.set_value("create_x_input", 0)
    dpg.set_value("create_y_input", 0)
    dpg.set_value("create_vx_input", 0)
    dpg.set_value("create_vy_input", 0)
    dpg.set_value("create_mass_input", 0)
    dpg.set_value("create_name_input", f"Body {body_count}")
    dpg.set_value("create_color_input", body_color)


def reset_selected_body():
    global selected_body
    selected_body = Body(0, "", Vec2(0, 0), Vec2(0, 0), 0, [0, 0, 0, 0])

# endregion


# region Item Callback Methods

def drag_body(body_id):
    if not reset:
        return

    body_x, body_y, z, w = dpg.get_value(body_id)
    body_position = Vec2(body_x, body_y)
    body = bodies[body_id]

    edited_body = Body(body.id, body.name, body_position, body.velocity, body.mass, body.color)
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
    body_x = dpg.get_value("selected_body_x_input")
    body_y = dpg.get_value("selected_body_y_input")
    body_vx = dpg.get_value("selected_body_vx_input")
    body_vy = dpg.get_value("selected_body_vy_input")
    body_mass = dpg.get_value("selected_body_mass_input")

    body_position = Vec2(body_x, body_y)
    body_velocity = Vec2(body_vx, body_vy)

    body = Body(selected_body.id, selected_body.name, body_position,body_velocity, body_mass, selected_body.color)

    bodies[selected_body.id] = body
    dpg.set_value(selected_body.id, [body_x, body_y, 0, 0])


def create_body_manual(name, position, velocity, mass, color):
    body_id = dpg.add_drag_point(label=name, parent="main_graph", default_value=position, color=color, callback=drag_body)

    body = Body(body_id, name, position, velocity, mass, color)

    global body_names
    body_names = list(np.append(body_names, name))

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


def create_body():
    body_name = dpg.get_value("create_name_input")
    body_x = dpg.get_value("create_x_input")
    body_y = dpg.get_value("create_y_input")
    body_vx = dpg.get_value("create_vx_input")
    body_vy = dpg.get_value("create_vy_input")
    body_mass = dpg.get_value("create_mass_input")
    color = dpg.get_value("create_color_input")

    body_position = Vec2(body_x, body_y)
    body_velocity = Vec2(body_vx, body_vy)

    create_body_manual(body_name, body_position, body_velocity, body_mass, color)


def delete_body():
    bodies.pop(selected_body.id)
    body_names.remove(selected_body.name)
    dpg.delete_item(selected_body.id)
    reset_selected_body()
    update_selected_body_group()

# endregion


# region DearPyGui Item Initiation

with dpg.window(label="Graph", width=681, height=681, no_resize=True, no_move=True, no_close=True, no_collapse=True):
    with dpg.plot(label="Top-Down View", height=-1, width=-1, tag="main_graph", anti_aliased=True):
        dpg.add_plot_axis(dpg.mvXAxis, label="x (m)", tag="x_axis")
        dpg.set_axis_limits(dpg.last_item(), graph_center_x - 10 ** default_graph_scale, graph_center_x + 10 ** default_graph_scale)

        dpg.add_plot_axis(dpg.mvYAxis, label="y (m)", tag="y_axis")
        dpg.set_axis_limits(dpg.last_item(), -graph_center_y - 10 ** default_graph_scale, graph_center_y + 10 ** default_graph_scale)

with dpg.window(label="Settings", width=583, height=681, pos=(681, 0), no_resize=True, no_move=True, no_close=True, no_collapse=True):

    # region Graph Position Child Window

    with dpg.child_window(menubar=True, height=100):
        with dpg.menu_bar():
            dpg.add_text("Graph Controls")

        # Graph Scale Settings
        with dpg.group(horizontal=True):
            dpg.add_text("Scale   ")
            dpg.add_slider_float(width=435, min_value=0, max_value=13, default_value=default_graph_scale, callback=update_graph_scale, tag="scale_slider")
            dpg.add_button(label="Reset", callback=lambda: reset_slider_value("scale_slider", default_graph_scale, update_graph_scale))

        with dpg.group(horizontal=True):
            dpg.add_text("X Center")
            dpg.add_slider_float(width=435, min_value=-3E11, max_value=3E11, default_value=0, callback=update_graph_center_x, tag="x_center_slider")
            dpg.add_button(label="Reset", callback=lambda: reset_slider_value("x_center_slider", 0, update_graph_center_x))

        with dpg.group(horizontal=True):
            dpg.add_text("Y Center")
            dpg.add_slider_float(width=435, min_value=-3E11, max_value=3E11, default_value=0, callback=update_graph_center_y, tag="y_center_slider")
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

        with dpg.group(horizontal=True):
            dpg.add_text("Position  ")

            dpg.add_text("X")
            dpg.add_input_float(tag="create_x_input", step=100, step_fast=1000, width=217)

            dpg.add_text("Y")
            dpg.add_input_float(tag="create_y_input", step=100, step_fast=1000, width=217)

        with dpg.group(horizontal=True):
            dpg.add_text("Velocity  ")

            dpg.add_text("X")
            dpg.add_input_float(tag="create_vx_input", step=100, step_fast=1000, width=217)

            dpg.add_text("Y")
            dpg.add_input_float(tag="create_vy_input", step=100, step_fast=1000, width=217)

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

    with dpg.child_window(menubar=True, height=147):
        with dpg.menu_bar():
            dpg.add_text("Edit Body")

        with dpg.group(horizontal=True, tag="selected_body_group"):
            with dpg.drawlist(width=20, height=20, tag="selected_body_drawlist"):
                dpg.draw_circle((10, 9), 5, fill=selected_body.color, tag="selected_body_circle")
            dpg.add_combo(body_names, default_value="Earth", tag="selected_body_combo", callback=select_body)

        with dpg.group(horizontal=True):
            dpg.add_text("Position  ")

            with dpg.group(horizontal=True, tag="selected_body_x_group"):
                dpg.add_text("X")
                dpg.add_input_float(tag="selected_body_x_input", step=100, step_fast=1000, width=217, default_value=selected_body.position.x, callback=edit_body)

            with dpg.group(horizontal=True, tag="selected_body_y_group"):
                dpg.add_text("Y")
                dpg.add_input_float(tag="selected_body_y_input", step=100, step_fast=1000, width=217, default_value=selected_body.position.y, callback=edit_body)

        with dpg.group(horizontal=True, tag="selected_body_velocity_group"):
            dpg.add_text("Velocity  ")

            with dpg.group(horizontal=True, tag="selected_body_vx_group"):
                dpg.add_text("X")
                dpg.add_input_float(tag="selected_body_vx_input", step=100, step_fast=1000, width=217, default_value=selected_body.velocity.x, callback=edit_body)

            with dpg.group(horizontal=True, tag="selected_body_vy_group"):
                dpg.add_text("Y")
                dpg.add_input_float(tag="selected_body_vy_input", step=100, step_fast=1000, width=217, default_value=selected_body.velocity.y, callback=edit_body)

        with dpg.group(horizontal=True, width=-1, tag="selected_body_mass_group"):
            dpg.add_text("Mass      ")
            dpg.add_input_float(tag="selected_body_mass_input", step=100, step_fast=1000, default_value=selected_body.mass, callback=edit_body)

        with dpg.group(horizontal=True, width=-1):
            dpg.add_button(label="Delete Body", callback=delete_body)

    # endregion

    dpg.add_spacer(height=64)

    with dpg.group():
        dpg.add_text("Simulation Progress")
        dpg.add_progress_bar(tag="sim_progress", width=-1)

    # region Simulation Control

    with dpg.group(horizontal=True):
        with dpg.group(width=183):
            dpg.add_text("Step Size (s)")
            dpg.add_input_int(tag="step_size", default_value=3600)

        with dpg.group(width=184):
            dpg.add_text("Sim Time (h)")
            dpg.add_input_int(tag="sim_time", default_value=8760)

        with dpg.group(width=183):
            dpg.add_text("Update Freq (h)")
            dpg.add_input_int(tag="update_freq", default_value=24)

    dpg.add_spacer()

    with dpg.group(horizontal=True, width=-1):
        dpg.add_button(label="Reset Trajectories", callback=reset_trajectories)

    with dpg.group(horizontal=True, width=-1):
        dpg.add_button(label="Calculate Trajectories", callback=calculate_trajectories)

    # endregion

# endregion

create_body_manual("Sun", Vec2(0, 0), Vec2(0, 0), 1988500E24, [249, 215, 28, 255])
create_body_manual("Mercury", Vec2(57.9E9, 0), Vec2(0, 47900), 0.330E24, [26, 26, 26, 255])
create_body_manual("Venus", Vec2(108.2E9, 0), Vec2(0, 35000), 4.87E24, [230, 230, 230, 255])
create_body_manual("Earth", Vec2(149.6E9, 0), Vec2(0, 29800), 5.97E24, [47, 106, 105, 255])
create_body_manual("Moon", Vec2(149.6E9 + 0.384E9, 0), Vec2(0, 29800 + 1000), 0.073E24, [254, 252, 215, 255])
create_body_manual("Mars", Vec2(228.0E9, 0), Vec2(0, 24000), 0.642E24, [153, 61, 0, 255])
create_body_manual("Jupiter", Vec2(778.5E9, 0), Vec2(0, 13100), 1898E24, [176, 127, 53, 255])
create_body_manual("Saturn", Vec2(1432.0E9, 0), Vec2(0, 9690), 568E24, [176, 143, 54, 255])
create_body_manual("Uranus", Vec2(2867.0E9, 0), Vec2(0, 6810), 86.8E24, [85, 128, 170, 255])
create_body_manual("Neptune", Vec2(4515.0E9, 0), Vec2(0, 5430), 102E24, [54, 104, 150, 255])

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

# endregion
