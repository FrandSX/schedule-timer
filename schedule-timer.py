# ------------------------------------------------------------------------
#    Schedule timer by Jani Kahrama
#  TODO:
#  * up next -event
#  * overlapping events as arcs of varying radii
#  * add/remove events in GUI
# ------------------------------------------------------------------------

import tkinter as tk
import math
import time
import signal


window_width = 1200
window_height = 800
clock_width = 800
clock_height = 800

black = '#000000'
white = '#ffffff'
orange = '#ffaa00'
purple = '#aa00ff'
cyan = '#0033aa'
darkgray = '#333333'
lightgreen = '#77ff77'
yellow = '#ffff00'

mode = 1  # 0 == 24h clock face, 1 == 12h clock face

events = {
    0:  {'name': 'Meeting',    'time_hour': 18, 'time_minute': 00,  'duration': 30, 'color': purple},
    1:  {'name': 'Late thing', 'time_hour': 22, 'time_minute': 30,  'duration': 45, 'color': cyan},
    2:  {'name': 'Lunch',      'time_hour': 12, 'time_minute': 00,  'duration': 60, 'color': lightgreen},
    3:  {'name': 'Early thing','time_hour': 7,  'time_minute': 30,  'duration': 30, 'color': yellow},
    4:  {'name': 'Meeting 2',  'time_hour': 13, 'time_minute': 20,  'duration': 20, 'color': white},
}


class ExitHandler:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)


    def exit_gracefully(self,signum, frame):
        self.kill_now = True


# Initialize tk window
def create_clock_window():
    window = tk.Tk()
    window.title('Schedule Timer')
    window.geometry(f'{window_width}x{window_height}')
    window.configure(bg=black)
    return window


# create canvas
def create_clock_canvas(window):
    canvas = tk.Canvas(window, width=window_width, height=window_height)
    canvas.configure(bd=0, bg=black, highlightthickness=0, highlightbackground=black)
    canvas.pack(fill='both', expand=True)
    return canvas
    

# conversion logic
def event_to_arc(hours, minutes, seconds, duration):
    mode_dict = {0:86400, 1:43200}

    start = (hours * 60 * 60 + minutes * 60 + seconds) / mode_dict[mode] * 360
    extent = ((duration * 60) / mode_dict[mode]) * 360

    return start % 360, extent


def parse_time(hours, minutes, seconds):
    unit_strings = ['', '', '']
    times = [hours, minutes, seconds]
    for i, unit in enumerate(times):
        if unit < 10:
            unit_strings[i] = '0'+str(unit)
        else:
            unit_strings[i] = str(unit)

    return unit_strings[0], unit_strings[1], unit_strings[2]


# animate clock
def draw_clock(clock_canvas):
    coord = 50, 50, clock_width-50, clock_height-50
    center_radius = 50
    center = clock_width * 0.5 - center_radius, clock_height * 0.5 - center_radius, clock_width * 0.5 + center_radius, clock_height * 0.5 + center_radius

    # draw clock face
    clock_canvas.create_rectangle(0, 0, window_width, window_height, fill=black)
    clock_canvas.create_oval(coord, fill=darkgray, outline=darkgray, width=0)

    # draw events
    now = time.localtime()
    arm_angle, _ = event_to_arc(now.tm_hour, now.tm_min, now.tm_sec, 0)
    # arm_angle, _ = event_to_arc(now.tm_min, now.tm_sec, 0, 0)  # quick test mode

    # sort events by start time
    event_list = []
    for key, value in events.items():
        h, m, _ = parse_time(value['time_hour'], value['time_minute'], 0)
        events[key]['timecode'] = h+m
        event_list.append(value)

    event_list = sorted(event_list, key=lambda k: k['timecode'])

    for i, event in enumerate(event_list):
        x, y = event_to_arc(event['time_hour'], event['time_minute'], 0, event['duration'])

        # highlight active events
        # if (x <= arm_angle <= x+y) and (event.time_hour == now.tm_hour):
        if (x <= arm_angle <= x+y):
            clock_canvas.create_arc(coord, start=90-x, extent=-y, fill=event['color'], outline='', width=0)
            clock_canvas.create_rectangle(clock_width+10, i*100+20, window_width, i*100+85, fill=event['color'])
            clock_canvas.create_text(clock_width+44, i*100+56, text=f'NOW', fill=black, font=('Helvetica 15 bold'))
            clock_canvas.create_text(clock_width+46, i*100+54, text=f'NOW', fill=black, font=('Helvetica 15 bold'))
            clock_canvas.create_text(clock_width+45, i*100+55, text=f'NOW', fill=white, font=('Helvetica 15 bold'))
        else:
            clock_canvas.create_arc(coord, start=90-x, extent=-y, fill=event['color'], outline='', width=0, stipple='gray25')
            clock_canvas.create_rectangle(clock_width+10, i*100+20, window_width, i*100+85, fill=event['color'], stipple='gray25')
        clock_canvas.create_rectangle(clock_width+80, i*100+20, window_width, i*100+80, fill=black)
        clock_canvas.create_text(clock_width - 20 + ((window_width-clock_width)*0.5), i*100+55, text=event['name'], fill=white, font=('Helvetica 20 bold'))
        h, m, _ = parse_time(event['time_hour'], event['time_minute'], 0)
        clock_canvas.create_text(window_width-50, i*100+55, text=f'{h}:{m}', fill=white, font=('Helvetica 20 bold'))


    # draw clock arm
    arm_length = 400
    clock_canvas.create_oval(center, fill=orange, outline=orange, width=2)
    x2 = arm_length * math.cos(math.radians(arm_angle) - math.radians(90)) + clock_width * 0.5
    y2 = arm_length * math.sin(math.radians(arm_angle) - math.radians(90)) + clock_height * 0.5
    clock_canvas.create_line(clock_width*0.5, clock_height*0.5, x2, y2, width=5, fill=orange)

    # draw digital clock
    h, m, s = parse_time(now.tm_hour, now.tm_min, now.tm_sec)
    clock_canvas.create_text(clock_width*0.5, clock_height*0.5, text=f'{h}:{m}:{s}', fill=black, font=('Helvetica 15 bold'))

    # canvas.after(100000, draw_clock(canvas))


exit_handler = ExitHandler()


if __name__ == '__main__':
    # Create window and canvas
    clock_window = create_clock_window()
    clock_canvas = create_clock_canvas(clock_window)

    while not exit_handler.kill_now:
        draw_clock(clock_canvas)
        clock_canvas.update()
        time.sleep(1.0)

    # clock_window.mainloop()
