# ------------------------------------------------------------------------
#    Schedule timer by Jani Kahrama
#  TODO:
#  * up next -event
#  * add/remove events in GUI
# ------------------------------------------------------------------------

import tkinter as tk
import math
import time


class Clock_GUI(object):
    def __init__(self, width, height):
        self.window_width = width
        self.window_height = height
        self.clock_width = round(width * 2 / 3)
        self.clock_height = height
        self.clock_digital = None
        self.clock_arm = None
        self.clock_arm_length = round(self.clock_height / 2)
        self.refresh_ms = 100
        self.event_overlay = False

        self.max_overlap = 0

        self.black = '#000000'
        self.white = '#ffffff'
        self.orange = '#ffaa00'
        self.purple = '#aa00ff'
        self.cyan = '#0033aa'
        self.darkgray = '#444444'
        self.lightgreen = '#77ff77'
        self.yellow = '#ffff00'
        self.bg_gray = '#282828'
        self.bg_dgray = '#202020'

        self.mode = 1  # 0 == 24h clock face, 1 == 12h clock face

        self.events = {
            0:  {'name': 'Meeting',    'time_hour': 18, 'time_minute': 00,  'duration': 30, 'color': self.purple},
            1:  {'name': 'Late thing', 'time_hour': 22, 'time_minute': 30,  'duration': 45, 'color': self.cyan},
            2:  {'name': 'Lunch',      'time_hour': 12, 'time_minute': 00,  'duration': 60, 'color': self.lightgreen},
            3:  {'name': 'Early thing','time_hour': 7,  'time_minute': 30,  'duration': 30, 'color': self.yellow},
            4:  {'name': 'Meeting 2',  'time_hour': 13, 'time_minute': 20,  'duration': 20, 'color': self.white},
            5:  {'name': 'Nightly',    'time_hour': 23, 'time_minute': 20,  'duration': 95, 'color': self.black},
            6:  {'name': 'Nightly2',   'time_hour': 17, 'time_minute': 20,  'duration': 95, 'color': self.black},
            7:  {'name': 'Nightly3',   'time_hour': 23, 'time_minute': 20,  'duration': 95, 'color': self.cyan},
            8:  {'name': 'Nightly4',   'time_hour': 17, 'time_minute': 20,  'duration': 95, 'color': self.cyan},
            9:  {'name': 'Nightly5',   'time_hour': 23, 'time_minute': 20,  'duration': 95, 'color': self.yellow},
            10: {'name': 'Nightly6',   'time_hour': 17, 'time_minute': 20,  'duration': 95, 'color': self.yellow}
        }

        self.event_bricks = []

        self.window = tk.Tk()
        self.window.title('Schedule Timer')
        self.window.geometry(f'{width}x{height}')
        self.window.configure(bg=self.black)

        self.canvas = tk.Canvas(self.window, width=width, height=height)
        self.canvas.configure(bd=0, bg=self.bg_dgray, highlightthickness=0, highlightbackground=self.black)
        self.canvas.pack(fill='both', expand=True)

        self.overlay = None
        self.overlay_close_button = None
        self.overlay_width = 0
        self.overlay_height = 0

        self.draw_clock()


    def toggle_event_overlay(self):
        self.event_overlay = not self.event_overlay


    # conversion logic
    def event_to_arc(self, hours, minutes, seconds, duration):
        mode_dict = {0:86400, 1:43200}

        start = (hours * 60 * 60 + minutes * 60 + seconds) / mode_dict[self.mode] * 360
        extent = ((duration * 60) / mode_dict[self.mode]) * 360

        return start % 360, extent


    def parse_time(self, hours, minutes, seconds):
        unit_strings = ['', '', '']
        times = [hours, minutes, seconds]
        for i, unit in enumerate(times):
            if unit < 10:
                unit_strings[i] = '0'+str(unit)
            else:
                unit_strings[i] = str(unit)

        return unit_strings[0], unit_strings[1], unit_strings[2]


    def rgb_to_hsl(in_rgba):
        R = in_rgba[0]
        G = in_rgba[1]
        B = in_rgba[2]
        Cmax = max(R, G, B)
        Cmin = min(R, G, B)

        H = 0.0
        S = 0.0
        L = (Cmax+Cmin)/2.0

        if L == 1.0:
            S = 0.0
        elif 0.0 < L < 0.5:
            S = (Cmax-Cmin)/(Cmax+Cmin)
        elif L >= 0.5:
            S = (Cmax-Cmin)/(2.0-Cmax-Cmin)

        if S > 0.0:
            if R == Cmax:
                H = ((G-B)/(Cmax-Cmin))*60.0
            elif G == Cmax:
                H = ((B-R)/(Cmax-Cmin)+2.0)*60.0
            elif B == Cmax:
                H = ((R-G)/(Cmax-Cmin)+4.0)*60.0

        return [H/360.0, S, L]


    def hsl_to_rgb(in_value):
        H, S, L = in_value

        v1 = 0.0
        v2 = 0.0

        rgb = [0.0, 0.0, 0.0]

        if S == 0.0:
            rgb = [L, L, L]
        else:
            if L < 0.5:
                v1 = L*(S+1.0)
            elif L >= 0.5:
                v1 = L+S-L*S

            v2 = 2.0*L-v1

            # H = H/360.0

            tR = H + 0.333333
            tG = H
            tB = H - 0.333333

            tList = [tR, tG, tB]

            for i, t in enumerate(tList):
                if t < 0.0:
                    t += 1.0
                elif t > 1.0:
                    t -= 1.0

                if t*6.0 < 1.0:
                    rgb[i] = v2+(v1-v2)*6.0*t
                elif t*2.0 < 1.0:
                    rgb[i] = v1
                elif t*3.0 < 2.0:
                    rgb[i] = v2+(v1-v2)*(0.666666 - t)*6.0
                else:
                    rgb[i] = v2

        return rgb


    # sort events
    # divide clock face to 5-min slots
    def sort_events(self):
        mode_dict = {0:24, 1:12}
        timeslot_list = [0] * 12 * mode_dict[self.mode]
        event_list = []
        for key, value in self.events.items():
            h, m, _ = self.parse_time(value['time_hour'], value['time_minute'], 0)
            self.events[key]['timecode'] = h+m
            event_list.append(value)

            # reserve 5-min slots according to duration
            slot_start = abs(value['time_hour'] - mode_dict[self.mode]) * 12 + math.floor(value['time_minute'] / 5)
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

            self.events[key]['overlap'] = overlap
            if overlap > self.max_overlap:
                self.max_overlap = overlap

        event_list_clock = sorted(event_list, key=lambda k: k['overlap'])
        event_list_stack = sorted(event_list, key=lambda k: k['timecode'])

        return event_list_clock, event_list_stack


    def draw_clock(self):
        def coord(value):
            return value, value, self.clock_width-value, self.clock_height-value

        mode_dict = {0:24, 1:12}
        center_radius = 50
        center = self.clock_width * 0.5 - center_radius, self.clock_height * 0.5 - center_radius, self.clock_width * 0.5 + center_radius, self.clock_height * 0.5 + center_radius
        event_list_clock, event_list_stack = self.sort_events()

        # clear background
        self.canvas.delete("all")

        # draw bg hour arcs
        for i in range(mode_dict[self.mode]):
            x = i*(360/mode_dict[self.mode])
            y = 360/mode_dict[self.mode]
            if i % 2 == 0:
                fillcolor = self.bg_gray
            else:
                fillcolor = self.darkgray

            self.canvas.create_arc(coord(50), start=90-x, extent=-y, fill=fillcolor, outline='', width=0)

        # draw clock background
        self.canvas.create_oval(coord(60), fill=self.darkgray, outline=self.bg_gray, width=0)

        # draw events
        now = time.localtime()
        arm_angle, _ = self.event_to_arc(now.tm_hour, now.tm_min, now.tm_sec, 0)
        # arm_angle, _ = event_to_arc(now.tm_min, now.tm_sec, 0, 0)  # quick test mode

        # draw events on clock face
        for i, event in enumerate(event_list_clock):
            x, y = self.event_to_arc(event['time_hour'], event['time_minute'], 0, event['duration'])

            # highlight active events
            # if (x <= arm_angle <= x+y) and (event.time_hour == now.tm_hour):
            if (x <= arm_angle <= x+y):
                self.canvas.create_arc(coord(60 + event['overlap'] * (self.clock_width * 0.5 / (self.max_overlap + 1) - center_radius)), start=90-x, extent=-y, fill=event['color'], outline='', width=0)
            else:
                self.canvas.create_arc(coord(60 + event['overlap'] * (self.clock_width * 0.5 / (self.max_overlap + 1) - center_radius)), start=90-x, extent=-y, fill=event['color'], outline='', width=0, stipple='gray25')
            self.canvas.create_arc(coord(60 + (event['overlap'] + 1) * (self.clock_width * 0.5 / (self.max_overlap + 1) - center_radius)), start=90-x+10, extent=-y-10, fill=self.darkgray, outline='', width=0)

        # draw event stack
        for i, event in enumerate(event_list_stack):
            if i % 2 == 0:
                fillcolor = self.bg_dgray
            else:
                fillcolor = self.bg_gray

            # highlight active events
            # if (x <= arm_angle <= x+y) and (event.time_hour == now.tm_hour):
            if (x <= arm_angle <= x+y):
                self.canvas.create_rectangle(self.clock_width, i*100, self.window_width, i*100+100, fill=fillcolor, outline='', width=0)
                self.canvas.create_rectangle(self.clock_width+10, i*100+20, self.window_width, i*100+85, fill=event['color'], outline='', width=0)
                # draw NOW with a black outline
                self.canvas.create_text(self.clock_width+44, i*100+56, text=f'NOW', fill=self.black, font=('Helvetica 15 bold'))
                self.canvas.create_text(self.clock_width+46, i*100+54, text=f'NOW', fill=self.black, font=('Helvetica 15 bold'))
                self.canvas.create_text(self.clock_width+45, i*100+55, text=f'NOW', fill=self.white, font=('Helvetica 15 bold'))
            else:
                self.canvas.create_rectangle(self.clock_width, i*100, self.window_width, i*100+100, fill=fillcolor, outline='', width=0)
                self.canvas.create_rectangle(self.clock_width+10, i*100+20, self.window_width, i*100+85, fill=event['color'], outline='', width=0, stipple='gray25')
            self.canvas.create_rectangle(self.clock_width+80, i*100+20, self.window_width, i*100+80, fill=fillcolor, outline='', width=0)
            self.canvas.create_text(self.clock_width - 20 + ((self.window_width-self.clock_width)*0.5), i*100+55, text=event['name'], fill=self.white, font=('Helvetica 20 bold'))

            h, m, _ = self.parse_time(event['time_hour'], event['time_minute'], 0)
            self.canvas.create_text(self.window_width-75, i*100+55, text=f'{h}:{m}', fill=self.white, font=('Helvetica 20 bold'))

        # draw clock arm
        self.canvas.create_oval(center, fill=self.orange, outline=self.orange, width=2)
        x2 = self.clock_arm_length * math.cos(math.radians(arm_angle) - math.radians(90)) + self.clock_width * 0.5
        y2 = self.clock_arm_length * math.sin(math.radians(arm_angle) - math.radians(90)) + self.clock_height * 0.5
        self.clock_arm = self.canvas.create_line(self.clock_width*0.5, self.clock_height*0.5, x2, y2, width=5, fill=self.orange)

        # draw digital clock
        h, m, s = self.parse_time(now.tm_hour, now.tm_min, now.tm_sec)
        self.clock_digital = self.canvas.create_text(self.clock_width*0.5, self.clock_height*0.5, text=f'{h}:{m}:{s}', fill=self.black, font=('Helvetica 15 bold'))

        # draw add button
        add_event_button = tk.Button(self.window, cursor='hand2', text='+', width=3, height=1, bd='0', bg=self.black, fg=self.white, font=('Helvetica 35 bold'), command=self.toggle_event_overlay)
        add_event_button.place(x=20, y=20)

        # initialize event adding window
        self.overlay_width = int(self.canvas.winfo_reqwidth())
        self.overlay_height = int(self.canvas.winfo_reqheight())
        self.overlay = self.canvas.create_rectangle(0, self.overlay_height / 2, self.overlay_width, self.overlay_height, fill=self.black, outline='', width=0)
        # clock_canvas.create_text(clock_width - 20 + ((window_width-clock_width)*0.5), i*100+55, text=event['name'], fill=white, font=('Helvetica 20 bold'))

        # draw close button
        self.close_overlay_button = tk.Button(self.window, cursor='hand2', text='+', width=3, height=1, bd='0', bg=self.black, fg=self.white, font=('Helvetica 35 bold'), command=self.toggle_event_overlay)
        self.close_overlay_button.place(x=20, y=self.overlay_height-80)


    def update_clock(self):
        now = time.localtime()
        h, m, s = self.parse_time(now.tm_hour, now.tm_min, now.tm_sec)
        arm_angle, _ = self.event_to_arc(now.tm_hour, now.tm_min, now.tm_sec, 0)

        for brick in enumerate(self.event_bricks):
            x = 90 - brick.start
            y = -brick.extent

            # highlight active events
            # if (x <= arm_angle <= x+y) and (event.time_hour == now.tm_hour):
            if (x <= arm_angle <= x+y):
                self.canvas.itemconfigure(brick, stipple='')
            else:
                self.canvas.itemconfigure(brick, stipple='gray25')

        self.canvas.itemconfigure(self.clock_digital, text=f'{h}:{m}:{s}')

        arm_angle, _ = self.event_to_arc(now.tm_hour, now.tm_min, now.tm_sec, 0)
        x2 = self.clock_arm_length * math.cos(math.radians(arm_angle) - math.radians(90)) + self.clock_width * 0.5
        y2 = self.clock_arm_length * math.sin(math.radians(arm_angle) - math.radians(90)) + self.clock_height * 0.5
        self.canvas.coords(self.clock_arm, self.clock_width*0.5, self.clock_height*0.5, x2, y2)

        if self.event_overlay:
            self.canvas.coords(self.overlay, 0, self.overlay_height / 2, self.overlay_width, self.overlay_height)
        else:
            self.canvas.coords(self.overlay, 0, self.overlay_height, self.overlay_width, self.overlay_height + self.overlay_height / 2)

        self.window.after(self.refresh_ms, self.update_clock)


    def run(self):
        self.update_clock()
        self.window.mainloop()


clock = Clock_GUI(1200, 800)
clock.run()
