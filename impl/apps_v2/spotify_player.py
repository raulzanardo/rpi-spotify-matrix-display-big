import numpy as np
import requests
import math
import time
import threading
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO


class SpotifyScreen:
    def __init__(self, config, modules, fullscreen, canvas_width=192, canvas_height=128):
        self.modules = modules

        # fonts (small bitmap font included) — scale sizes for larger panel
        self.title_font = ImageFont.truetype("fonts/tiny.otf", 14)
        self.artist_font = ImageFont.truetype("fonts/tiny.otf", 12)

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.title_color = (255, 255, 255)
        self.artist_color = (200, 200, 200)
        self.play_color = (102, 240, 110)

        # album art area: 128x128 on the right, info panel on the left
        self.art_width = 128
        self.art_height = 128
        self.info_x = 0
        self.info_width = self.canvas_width - self.art_width
        self.art_x = self.canvas_width - self.art_width

        self.full_screen_always = fullscreen

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

    def getCurrentPlaybackAsync(self):
        # delay spotify fetches
        time.sleep(3)
        while True:
            self.response = self.spotify_module.getCurrentPlayback()
            time.sleep(1)

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
                if self.current_art_url != art_url:
                    self.current_art_url = art_url
                    response = requests.get(self.current_art_url)
                    img = Image.open(BytesIO(response.content))
                    self.current_art_img = self._fit_image(
                        img, self.canvas_width, self.canvas_height)

                frame = Image.new(
                    "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
                frame.paste(self.current_art_img, (0, 0))
                return (frame, self.is_playing)
            else:
                if not self.is_playing:
                    if not self.paused:
                        self.paused_time = math.floor(time.time())
                        self.paused = True
                else:
                    if self.paused and self.current_art_img and self.current_art_img.size == (self.canvas_width, self.canvas_height):
                        self.title_animation_cnt = 0
                        self.artist_animation_cnt = 0
                        self.last_title_reset = math.floor(time.time())
                        self.last_artist_reset = math.floor(time.time())
                    self.paused_time = math.floor(time.time())
                    self.paused = False

                if (self.current_title != title or self.current_artist != artist):
                    self.current_artist = artist
                    self.current_title = title
                    self.title_animation_cnt = 0
                    self.artist_animation_cnt = 0
                    self.last_title_reset = math.floor(time.time())
                    self.last_artist_reset = math.floor(time.time())

                current_time = math.floor(time.time())
                show_fullscreen = current_time - self.paused_time >= self.paused_delay

                # ensure current art image is sized for the art panel
                if self.current_art_url != art_url or self.current_art_img is None:
                    self.current_art_url = art_url
                    response = requests.get(self.current_art_url)
                    img = Image.open(BytesIO(response.content))
                    self.current_art_img = self._fit_image(
                        img, self.art_width, self.art_height)

                frame = Image.new(
                    "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))

                # paste album art on the right
                if self.current_art_img is not None:
                    frame.paste(self.current_art_img, (self.art_x, 0))
                draw = ImageDraw.Draw(frame)

                # draw title and artist in the right info panel
                pad_x = 6
                title_x = self.info_x + pad_x
                title_y = 20
                artist_x = title_x
                artist_y = title_y + 36

                spacer = "     "

                # Title (scroll if too long)
                title_len = self.title_font.getlength(self.current_title)
                avail_width = self.info_width - pad_x * 2
                if title_len > avail_width:
                    draw.text((title_x - self.title_animation_cnt, title_y), self.current_title +
                              spacer + self.current_title, self.title_color, font=self.title_font)
                    if current_time - self.last_title_reset >= self.scroll_delay:
                        self.title_animation_cnt += 1
                    if self.title_animation_cnt >= self.title_font.getlength(self.current_title + spacer):
                        self.title_animation_cnt = 0
                        self.last_title_reset = math.floor(time.time())
                else:
                    draw.text((title_x, title_y), self.current_title,
                              self.title_color, font=self.title_font)

                # Artist (scroll if too long)
                artist_len = self.artist_font.getlength(self.current_artist)
                if artist_len > avail_width:
                    draw.text((artist_x - self.artist_animation_cnt, artist_y), self.current_artist +
                              spacer + self.current_artist, self.artist_color, font=self.artist_font)
                    if current_time - self.last_artist_reset >= self.scroll_delay:
                        self.artist_animation_cnt += 1
                    if self.artist_animation_cnt >= self.artist_font.getlength(self.current_artist + spacer):
                        self.artist_animation_cnt = 0
                        self.last_artist_reset = math.floor(time.time())
                else:
                    draw.text((artist_x, artist_y), self.current_artist,
                              self.artist_color, font=self.artist_font)

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

                # play/pause icon near the top of left info panel
                drawPlayPause(draw, self.is_playing,
                              self.play_color, offset_x=self.info_x + 4, offset_y=4)

                return (frame, self.is_playing)
        else:
            # not active
            frame = Image.new(
                "RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
            draw = ImageDraw.Draw(frame)

            self.current_art_url = ''
            self.is_playing = False
            self.title_animation_cnt = 0
            self.artist_animation_cnt = 0
            self.last_title_reset = math.floor(time.time())
            self.last_artist_reset = math.floor(time.time())
            self.paused = True
            self.paused_time = math.floor(time.time())

            return (None, self.is_playing)


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
