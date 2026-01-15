import numpy as np
import requests
import math
import time
import threading
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO


class SpotifyScreen:
    def __init__(self, config, modules, fullscreen, canvas_width=192, canvas_height=128, show_clock=False):
        self.modules = modules

        # very small fonts for 64px width panel
        self.title_font = ImageFont.truetype("fonts/tiny.otf", 5)
        self.artist_font = ImageFont.truetype("fonts/tiny.otf", 5)

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.title_color = (255, 255, 255)
        self.artist_color = (200, 200, 200)
        self.play_color = (102, 240, 110)

        # album art area: 128x128 on the right starting at x=64, info panel on the left 64x128 starting at x=0
        self.art_width = 128
        self.art_height = 128
        self.art_x = 64  # album art starts at x=64
        self.info_x = 0  # info panel starts at x=0
        self.info_width = 64  # info panel width

        self.full_screen_always = fullscreen
        self.show_clock = show_clock

        self.current_art_url = ''
        self.current_art_img = None
        self.current_title = ''
        self.current_artist = ''

        self.title_animation_cnt = 0
        self.artist_animation_cnt = 0
        self.last_title_reset = math.floor(time.time())
        self.last_artist_reset = math.floor(time.time())
        self.scroll_delay = 4

        self.paused = True
        self.paused_time = math.floor(time.time())
        self.paused_delay = 5

        self.is_playing = False

        self.last_fetch_time = math.floor(time.time())
        self.fetch_interval = 1
        self.spotify_module = self.modules['spotify']

        self.response = None
        self.thread = threading.Thread(target=self.getCurrentPlaybackAsync)
        self.thread.start()

    def _fit_image(self, img, target_w, target_h, fill_color=(0, 0, 0)):
        # Preserve aspect ratio, fit within target and center on background
        img = img.convert('RGB')
        iw, ih = img.size
        if iw == 0 or ih == 0:
            return Image.new('RGB', (target_w, target_h), fill_color)
        scale = min(target_w / iw, target_h / ih)
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))
        resized = img.resize((new_w, new_h), resample=Image.LANCZOS)
        canvas = Image.new('RGB', (target_w, target_h), fill_color)
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        canvas.paste(resized, (x, y))
        return canvas

    def _cover_image(self, img, target_w, target_h):
        # Resize and crop to completely fill target (no stretching)
        img = img.convert('RGB')
        iw, ih = img.size
        if iw == 0 or ih == 0:
            return Image.new('RGB', (target_w, target_h), (0, 0, 0))
        scale = max(target_w / iw, target_h / ih)
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))
        resized = img.resize((new_w, new_h), resample=Image.LANCZOS)
        # crop center
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    def getCurrentPlaybackAsync(self):
        # delay spotify fetches
        time.sleep(3)
        while True:
            self.response = self.spotify_module.getCurrentPlayback()
            time.sleep(1)

    def _get_clock_digit_color(self, hour, minute):
        # Ported from getClockDigitColor in spotify_clock_wf2 (color_tools.h)
        # Defaults for configuration (can be exposed later via config)
        CONFIG_NIGHT_START_HOUR = 22
        CONFIG_NIGHT_END_HOUR = 6
        NIGHT_TEMP = 1500.0
        MIN_TEMP = 2000.0
        MAX_TEMP = 6500.0
        CONFIG_NIGHT_DIM_FACTOR = 0.3

        timeOfDay = hour + minute / 60.0

        if timeOfDay < CONFIG_NIGHT_END_HOUR or timeOfDay >= CONFIG_NIGHT_START_HOUR:
            temp = NIGHT_TEMP
        elif timeOfDay < 12:
            temp = MIN_TEMP + (MAX_TEMP - MIN_TEMP) * ((timeOfDay - 6) / 6.0)
        elif timeOfDay < 18:
            temp = MAX_TEMP - (MAX_TEMP - MIN_TEMP) * ((timeOfDay - 12) / 6.0)
        else:
            temp = MIN_TEMP - (MIN_TEMP - NIGHT_TEMP) * \
                ((timeOfDay - 18) / 4.0)

        # Convert temperature to RGB (approximation)
        t = temp / 100.0
        if t <= 66:
            red = 255.0
            green = 99.4708025861 * math.log(t) - 161.1195681661
            if t <= 19:
                blue = 0.0
            else:
                blue = 138.5177312231 * math.log(t - 10) - 305.0447927307
        else:
            red = 329.698727446 * math.pow(t - 60, -0.1332047592)
            green = 288.1221695283 * math.pow(t - 60, -0.0755148492)
            blue = 255.0

        # Clamp
        red = max(0.0, min(255.0, red))
        green = max(0.0, min(255.0, green))
        blue = max(0.0, min(255.0, blue))

        # Dim at night
        if timeOfDay < CONFIG_NIGHT_END_HOUR or timeOfDay >= CONFIG_NIGHT_START_HOUR:
            dim = CONFIG_NIGHT_DIM_FACTOR
            red *= dim
            green *= dim
            blue *= dim

        return (int(red), int(green), int(blue))

    def _get_top_two_colors(self, img, sample=50):
        """Return the two most prevalent RGB colors from `img` as (primary, secondary).
        Falls back to white/gray on error."""
        try:
            small = img.convert('RGB').resize((sample, sample))
            colors = small.getcolors(sample * sample)
            if colors:
                # colors is list of (count, (r,g,b))
                colors.sort(reverse=True, key=lambda x: x[0])
                top = [c[1] for c in colors[:2]]
                if len(top) == 1:
                    top.append(top[0])
                return (top[0], top[1])

            # fallback: use adaptive palette
            pal = small.convert('P', palette=Image.ADAPTIVE, colors=5)
            palette = pal.getpalette()
            counts = pal.getcolors()
            counts.sort(reverse=True, key=lambda x: x[0])
            res = []
            for cnt, idx in counts[:2]:
                r = palette[idx * 3]
                g = palette[idx * 3 + 1]
                b = palette[idx * 3 + 2]
                res.append((r, g, b))
            if len(res) == 1:
                res.append(res[0])
            if res:
                return (res[0], res[1])
        except Exception:
            pass
        return ((255, 255, 255), (200, 200, 200))

    def generate(self):
        if not self.spotify_module.queue.empty():
            self.response = self.spotify_module.queue.get()
            self.spotify_module.queue.queue.clear()
        return self.generateFrame(self.response)

    def generateFrame(self, response):
        if response is not None:
            (artist, title, art_url, self.is_playing,
             progress_ms, duration_ms) = response

            if self.full_screen_always:
                # if not playing, show only the centered clock (no album art)
                if not self.is_playing:
                    from datetime import datetime
                    now = datetime.now()
                    frame = Image.new(
                        "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
                    draw = ImageDraw.Draw(frame)
                    current_time_str = now.strftime("%H:%M")
                    try:
                        time_font = ImageFont.truetype(
                            "fonts/Montserrat-Regular.otf", 50)
                    except Exception:
                        time_font = ImageFont.load_default()
                    color = self._get_clock_digit_color(now.hour, now.minute)
                    cx = self.canvas_width // 2
                    cy = self.canvas_height // 2
                    draw.text((cx, cy), current_time_str,
                              font=time_font, fill=color, anchor='mm')
                    return (frame, self.is_playing)

                # playing: show album art fullscreen
                if self.current_art_url != art_url:
                    self.current_art_url = art_url
                    response = requests.get(self.current_art_url)
                    img = Image.open(BytesIO(response.content))
                    # fullscreen: cover the screen to avoid letterbox but no stretching
                    self.current_art_img = self._cover_image(
                        img, self.canvas_width, self.canvas_height)

                frame = Image.new(
                    "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
                frame.paste(self.current_art_img, (0, 0))

                # optionally overlay a small clock on top of the cover (only in fullscreen and when playing)
                if self.show_clock:
                    from datetime import datetime
                    now = datetime.now()
                    # prefer using the two most prevalent colors from the album cover
                    if self.current_art_img is not None:
                        body_rgb, border_rgb = self._get_top_two_colors(
                            self.current_art_img)
                    else:
                        body_rgb = self._get_clock_digit_color(
                            now.hour, now.minute)
                        border_rgb = tuple(max(0, c - 60) for c in body_rgb)

                    # overlay with alpha for subtle background
                    overlay = Image.new(
                        'RGBA', (self.canvas_width, self.canvas_height), (0, 0, 0, 0))
                    odraw = ImageDraw.Draw(overlay)

                    # center the clock overlay (match the not-playing centered clock)
                    time_str = now.strftime("%H:%M")
                    try:
                        time_font = ImageFont.truetype(
                            "fonts/Montserrat-Regular.otf", 50)
                    except Exception:
                        time_font = ImageFont.load_default()

                    # center coordinates
                    cx = self.canvas_width // 2
                    cy = self.canvas_height // 2

                    # draw outlined time string using cover colors (border then body)
                    border_fill = (
                        border_rgb[0], border_rgb[1], border_rgb[2], 255)
                    body_fill = (body_rgb[0], body_rgb[1], body_rgb[2], 255)
                    # draw border by painting text in surrounding pixels
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                        odraw.text((cx + dx, cy + dy), time_str,
                                   font=time_font, fill=border_fill, anchor='mm')
                    # draw main body
                    odraw.text((cx, cy), time_str, font=time_font,
                               fill=body_fill, anchor='mm')

                    # composite overlay onto frame
                    frame = frame.convert('RGBA')
                    frame = Image.alpha_composite(
                        frame, overlay).convert('RGB')

                return (frame, self.is_playing)
            else:
                # if playback is paused (music not playing), show clock instead of album art
                if not self.is_playing:
                    from datetime import datetime
                    frame = Image.new(
                        "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
                    draw = ImageDraw.Draw(frame)
                    current_time_str = datetime.now().strftime("%H:%M")
                    time_font = ImageFont.truetype(
                        "fonts/Montserrat-Regular.otf", 50)
                    time_bbox = draw.textbbox(
                        (0, 0), current_time_str, font=time_font)
                    # center using midpoint anchor 'mm'
                    cx = self.canvas_width // 2
                    cy = self.canvas_height // 2
                    now = datetime.now()
                    color = self._get_clock_digit_color(now.hour, now.minute)
                    draw.text((cx, cy), current_time_str,
                              font=time_font, fill=color, anchor='mm')
                    return (frame, self.is_playing)

                if (self.current_title != title or self.current_artist != artist):
                    self.current_artist = artist
                    self.current_title = title
                    self.title_animation_cnt = 0
                    self.artist_animation_cnt = 0
                    self.last_title_reset = math.floor(time.time())
                    self.last_artist_reset = math.floor(time.time())

                current_time = math.floor(time.time())
                show_fullscreen = current_time - self.paused_time >= self.paused_delay

                # ensure current art image is sized for the art panel (128x128)
                if self.current_art_url != art_url or self.current_art_img is None:
                    self.current_art_url = art_url
                    response = requests.get(self.current_art_url)
                    img = Image.open(BytesIO(response.content))
                    # panel art: crop to fill exactly 128x128
                    self.current_art_img = self._cover_image(img, 128, 128)

                frame = Image.new(
                    "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
                draw = ImageDraw.Draw(frame)

                # paste album art on the right at x=64, size 128x128
                if self.current_art_img is not None:
                    # Ensure it's exactly 128x128
                    if self.current_art_img.size != (128, 128):
                        self.current_art_img = self._cover_image(
                            self.current_art_img, 128, 128)
                    frame.paste(self.current_art_img, (64, 0))

                # draw title and artist in the left info panel
                pad_x = 2
                title_x = self.info_x + pad_x
                title_y = 20
                artist_x = title_x
                artist_y = title_y + 36

                # Title and Artist: wrap to multiple lines if needed
                avail_width = self.info_width - pad_x * 2

                def wrap_text(text, font, max_w):
                    # returns list of lines that fit within max_w
                    words = text.split()
                    lines = []
                    current_line = ""

                    for word in words:
                        test_line = current_line + \
                            (" " if current_line else "") + word
                        if font.getlength(test_line) <= max_w:
                            current_line = test_line
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word

                    if current_line:
                        lines.append(current_line)

                    return lines if lines else [text[:1]]  # at least one char

                title_lines = wrap_text(
                    self.current_title, self.title_font, avail_width)
                artist_lines = wrap_text(
                    self.current_artist, self.artist_font, avail_width)

                # Draw title lines
                y_pos = title_y
                line_height = 6
                for line in title_lines:
                    draw.text((title_x, y_pos), line,
                              self.title_color, font=self.title_font)
                    y_pos += line_height

                # Draw artist lines
                y_pos = artist_y
                for line in artist_lines:
                    draw.text((artist_x, y_pos), line,
                              self.artist_color, font=self.artist_font)
                    y_pos += line_height

                # progress bar in the left info panel (near bottom)
                bar_pad = 8
                bar_x0 = self.info_x + bar_pad
                bar_x1 = self.info_x + self.info_width - bar_pad
                bar_h = 10
                bar_y1 = self.canvas_height - 6
                bar_y0 = bar_y1 - bar_h
                draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1),
                               fill=(40, 40, 40))
                try:
                    frac = 0.0 if duration_ms == 0 else max(
                        0.0, min(1.0, progress_ms / duration_ms))
                except Exception:
                    frac = 0.0
                fill_x = bar_x0 + int(frac * (bar_x1 - bar_x0))
                draw.rectangle((bar_x0, bar_y0, fill_x, bar_y1),
                               fill=self.play_color)

                return (frame, self.is_playing)
        else:
            # not active - show current time
            from datetime import datetime

            frame = Image.new(
                "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
            draw = ImageDraw.Draw(frame)

            # Display current time centered on screen
            current_time_str = datetime.now().strftime("%H:%M")
            time_font = ImageFont.truetype("fonts/Montserrat-Regular.otf", 50)
            time_bbox = draw.textbbox((0, 0), current_time_str, font=time_font)
            # center using midpoint anchor 'mm'
            cx = self.canvas_width // 2
            cy = self.canvas_height // 2
            now = datetime.now()
            color = self._get_clock_digit_color(now.hour, now.minute)
            draw.text((cx, cy), current_time_str,
                      font=time_font, fill=color, anchor='mm')

            self.current_art_url = ''
            self.is_playing = False
            self.title_animation_cnt = 0
            self.artist_animation_cnt = 0
            self.last_title_reset = math.floor(time.time())
            self.last_artist_reset = math.floor(time.time())
            self.paused = True
            self.paused_time = math.floor(time.time())

            return (frame, self.is_playing)


def drawPlayPause(draw, is_playing, color, offset_x=0, offset_y=0):
    x = offset_x + 8
    y = offset_y + 8
    if not is_playing:
        draw.line((x+18, y+8, x+18, y+14), fill=color)
        draw.line((x+19, y+9, x+19, y+13), fill=color)
        draw.line((x+22, y+9, x+22, y+13), fill=color)
        draw.line((x+23, y+10, x+23, y+12), fill=color)
    else:
        draw.polygon([(x+18, y+8), (x+18, y+14), (x+24, y+11)], fill=color)
