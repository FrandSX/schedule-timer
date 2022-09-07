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
clock_digital = None
clock_arm = None
clock_arm_length = 400

max_overlap = 0

black = '#000000'
white = '#ffffff'
orange = '#ffaa00'
purple = '#aa00ff'
cyan = '#0033aa'
darkgray = '#444444'
lightgreen = '#77ff77'
yellow = '#ffff00'
bg_gray = '#282828'
bg_dgray = '#202020'

mode = 1  # 0 == 24h clock face, 1 == 12h clock face

events = {
    0:  {'name': 'Meeting',    'time_hour': 18, 'time_minute': 00,  'duration': 30, 'color': purple},
    1:  {'name': 'Late thing', 'time_hour': 22, 'time_minute': 30,  'duration': 45, 'color': cyan},
    2:  {'name': 'Lunch',      'time_hour': 12, 'time_minute': 00,  'duration': 60, 'color': lightgreen},
    3:  {'name': 'Early thing','time_hour': 7,  'time_minute': 30,  'duration': 30, 'color': yellow},
    4:  {'name': 'Meeting 2',  'time_hour': 13, 'time_minute': 20,  'duration': 20, 'color': white},
    5:  {'name': 'Nightly',    'time_hour': 23, 'time_minute': 20,  'duration': 95, 'color': black},
    6:  {'name': 'Nightly2',   'time_hour': 17, 'time_minute': 20,  'duration': 95, 'color': black},
    7:  {'name': 'Nightly3',   'time_hour': 23, 'time_minute': 20,  'duration': 95, 'color': cyan},
    8:  {'name': 'Nightly4',   'time_hour': 17, 'time_minute': 20,  'duration': 95, 'color': cyan},
    9:  {'name': 'Nightly5',   'time_hour': 23, 'time_minute': 20,  'duration': 95, 'color': yellow},
    10: {'name': 'Nightly6',   'time_hour': 17, 'time_minute': 20,  'duration': 95, 'color': yellow}
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
    canvas.configure(bd=0, bg=bg_dgray, highlightthickness=0, highlightbackground=black)
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


# sort events
# divide clock face to 5-min slots
def sort_events():
    global max_overlap
    mode_dict = {0:24, 1:12}
    timeslot_list = [0] * 12 * mode_dict[mode]
    event_list = []
    for key, value in events.items():
        h, m, _ = parse_time(value['time_hour'], value['time_minute'], 0)
        events[key]['timecode'] = h+m
        event_list.append(value)

        # reserve 5-min slots according to duration
        slot_start = abs(value['time_hour'] - mode_dict[mode]) * 12 + math.floor(value['time_minute'] / 5)
        slot_duration = math.ceil(value['duration'] / 5)

        # also handle events that cross midnight
        slot_chunks = [None, None]
        if slot_start + slot_duration > len(timeslot_list):
            slot_chunks[0] = timeslot_list[slot_start::]
            slot_chunks[1] = timeslot_list[0:slot_start+slot_duration-len(timeslot_list)]
        else:
            slot_chunks[0] = timeslot_list[slot_start:slot_start+slot_duration]

        overlap = 0
        for i, chunk in enumerate(slot_chunks):
            if chunk is not None:
                if max(chunk) > overlap:
                    overlap = max(chunk)
                slot_chunks[i] = [overlap + 1] * len(chunk)
        if slot_chunks[1] is not None:
            timeslot_list[slot_start::] = slot_chunks[0]
            timeslot_list[0:len(slot_chunks[1])] = slot_chunks[1]
        else: 
            timeslot_list[slot_start:slot_start+slot_duration:1] = slot_chunks[0]

        events[key]['overlap'] = overlap
        if overlap > max_overlap:
            max_overlap = overlap

    event_list_clock = sorted(event_list, key=lambda k: k['overlap'])
    event_list_stack = sorted(event_list, key=lambda k: k['timecode'])

    return event_list_clock, event_list_stack


def draw_clock(clock_canvas):
    def coord(value):
        return value, value, clock_width-value, clock_height-value

    global clock_digital, clock_arm
    mode_dict = {0:24, 1:12}
    center_radius = 50
    center = clock_width * 0.5 - center_radius, clock_height * 0.5 - center_radius, clock_width * 0.5 + center_radius, clock_height * 0.5 + center_radius
    event_list_clock, event_list_stack = sort_events()

    # clear background
    clock_canvas.delete("all")

    # draw bg hour arcs
    for i in range(mode_dict[mode]):
        x = i*(360/mode_dict[mode])
        y = 360/mode_dict[mode]
        if i % 2 == 0:
            fillcolor = bg_gray
        else:
            fillcolor = darkgray

        clock_canvas.create_arc(coord(50), start=90-x, extent=-y, fill=fillcolor, outline='', width=0)

    # draw clock background
    clock_canvas.create_oval(coord(60), fill=darkgray, outline=bg_gray, width=0)

    # draw events
    now = time.localtime()
    arm_angle, _ = event_to_arc(now.tm_hour, now.tm_min, now.tm_sec, 0)
    # arm_angle, _ = event_to_arc(now.tm_min, now.tm_sec, 0, 0)  # quick test mode

    # draw events on clock face
    for i, event in enumerate(event_list_clock):
        x, y = event_to_arc(event['time_hour'], event['time_minute'], 0, event['duration'])

        # highlight active events
        # if (x <= arm_angle <= x+y) and (event.time_hour == now.tm_hour):
        if (x <= arm_angle <= x+y):
            clock_canvas.create_arc(coord(60 + event['overlap'] * (clock_width * 0.5 / (max_overlap + 1) - center_radius)), start=90-x, extent=-y, fill=event['color'], outline='', width=0)
            clock_canvas.create_arc(coord(60 + (event['overlap'] + 1) * (clock_width * 0.5 / (max_overlap + 1) - center_radius)), start=90-x+10, extent=-y-10, fill=darkgray, outline='', width=0)
        else:
            clock_canvas.create_arc(coord(60 + event['overlap'] * (clock_width * 0.5 / (max_overlap + 1) - center_radius)), start=90-x, extent=-y, fill=event['color'], outline='', width=0, stipple='gray25')
            clock_canvas.create_arc(coord(60 + (event['overlap'] + 1) * (clock_width * 0.5 / (max_overlap + 1) - center_radius)), start=90-x+10, extent=-y-10, fill=darkgray, outline='', width=0)

    # draw event stack
    for i, event in enumerate(event_list_stack):
        if i % 2 == 0:
            fillcolor = bg_dgray
        else:
            fillcolor = bg_gray

        # highlight active events
        # if (x <= arm_angle <= x+y) and (event.time_hour == now.tm_hour):
        if (x <= arm_angle <= x+y):
            clock_canvas.create_rectangle(clock_width, i*100, window_width, i*100+100, fill=fillcolor, outline='', width=0)
            clock_canvas.create_rectangle(clock_width+10, i*100+20, window_width, i*100+85, fill=event['color'], outline='', width=0)
            # draw NOW with a black outline
            clock_canvas.create_text(clock_width+44, i*100+56, text=f'NOW', fill=black, font=('Helvetica 15 bold'))
            clock_canvas.create_text(clock_width+46, i*100+54, text=f'NOW', fill=black, font=('Helvetica 15 bold'))
            clock_canvas.create_text(clock_width+45, i*100+55, text=f'NOW', fill=white, font=('Helvetica 15 bold'))
        else:
            clock_canvas.create_rectangle(clock_width, i*100, window_width, i*100+100, fill=fillcolor, outline='', width=0)
            clock_canvas.create_rectangle(clock_width+10, i*100+20, window_width, i*100+85, fill=event['color'], outline='', width=0, stipple='gray25')
        clock_canvas.create_rectangle(clock_width+80, i*100+20, window_width, i*100+80, fill=fillcolor, outline='', width=0)
        clock_canvas.create_text(clock_width - 20 + ((window_width-clock_width)*0.5), i*100+55, text=event['name'], fill=white, font=('Helvetica 20 bold'))

        h, m, _ = parse_time(event['time_hour'], event['time_minute'], 0)
        clock_canvas.create_text(window_width-75, i*100+55, text=f'{h}:{m}', fill=white, font=('Helvetica 20 bold'))

    # draw clock arm
    clock_canvas.create_oval(center, fill=orange, outline=orange, width=2)
    x2 = clock_arm_length * math.cos(math.radians(arm_angle) - math.radians(90)) + clock_width * 0.5
    y2 = clock_arm_length * math.sin(math.radians(arm_angle) - math.radians(90)) + clock_height * 0.5
    clock_arm = clock_canvas.create_line(clock_width*0.5, clock_height*0.5, x2, y2, width=5, fill=orange)

    # draw digital clock
    h, m, s = parse_time(now.tm_hour, now.tm_min, now.tm_sec)
    clock_digital = clock_canvas.create_text(clock_width*0.5, clock_height*0.5, text=f'{h}:{m}:{s}', fill=black, font=('Helvetica 15 bold'))


# animate clock
def update_clock_face(clock_canvas):
    now = time.localtime()
    h, m, s = parse_time(now.tm_hour, now.tm_min, now.tm_sec)
    clock_canvas.itemconfigure(clock_digital, text=f'{h}:{m}:{s}')

    arm_angle, _ = event_to_arc(now.tm_hour, now.tm_min, now.tm_sec, 0)
    x2 = clock_arm_length * math.cos(math.radians(arm_angle) - math.radians(90)) + clock_width * 0.5
    y2 = clock_arm_length * math.sin(math.radians(arm_angle) - math.radians(90)) + clock_height * 0.5
    clock_canvas.coords(clock_arm, clock_width*0.5, clock_height*0.5, x2, y2)


exit_handler = ExitHandler()


if __name__ == '__main__':
    # Create window and canvas
    clock_window = create_clock_window()
    clock_canvas = create_clock_canvas(clock_window)

    # draw clock bg and static elements
    draw_clock(clock_canvas)

    # update dynamic elements in a loop
    while not exit_handler.kill_now:
        clock_canvas.update()
        time.sleep(1.0)
        update_clock_face(clock_canvas)
