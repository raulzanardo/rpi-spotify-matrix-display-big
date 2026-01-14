# rpi-spotify-matrix-display

A Spotify display for 64x64 RGB LED matrices (raspberry pi project v2)

## Hardware

[Here is the list](https://www.reddit.com/r/raspberry_pi/comments/ombwwg/my_64x64_rgb_led_matrix_album_art_display_pi_3b/) of hardware I used. You can ignore the software details as they are irrelevant for v2.

## Spotify Pre-Setup

1. Go to https://developer.spotify.com/dashboard
2. Create an account and/or login
3. Select "Create app" (name/description does not matter)
4. Add http://127.0.0.1:8080/callback under Redirect URIs
5. Save, then tap "Settings" in the upper right
6. Copy the generated Client ID and Secret ID for later

## Pi Setup

> [!IMPORTANT]
> Please see the [pi setup wiki page](https://github.com/kylejohnsonkj/rpi-spotify-matrix-display/wiki/raspberry-pi-full-setup-guide) for a full installation guide!

https://github.com/user-attachments/assets/9bf163f9-8e0f-47cc-b2d2-a62b3a975471

<sup>The above video is from [my reddit post here.](https://www.reddit.com/r/raspberry_pi/comments/ziz4hk/my_64x64_rgb_led_matrix_album_art_display_pi_3b/)</sup>

## Quick Run (on a Pi)

1. Clone and enter the repo
   - `git clone --recurse-submodules https://github.com/kylejohnsonkj/rpi-spotify-matrix-display`
   - `cd rpi-spotify-matrix-display/`
2. **Set your Client ID and Secret ID in the config.ini**
3. Create and activate a python [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
4. Install dependencies
   - `python3 -m pip install -r requirements.txt`
5. Run the controller from the `impl/` directory
   - `cd impl/`
   - `python3 controller_v3.py`

## Arguments

| Argument              | Default | Description                                     |
| :-------------------- | :------ | :---------------------------------------------- |
| `-f` , `--fullscreen` | false   | Always display album art in full screen (64x64) |
| `-h` , `--help`       | false   | Display help messages for arguments             |

## Configuration

Configuration is handled in the config.ini. I have included my own as a sample.

For Matrix configuration, see https://github.com/hzeller/rpi-rgb-led-matrix#changing-parameters-via-command-line-flags. More extensive customization can be done in `impl/controller_v3.py` directly.

Note: The `shutdown_delay` value (in seconds) controls automatic screen shutdown when music is inactive — set `shutdown_delay = 0` to disable automatic shutdown and keep the display on.

For Spotify configuration, set the `client_id` and `client_secret` to your own. You may leave `redirect_uri` alone. I have also included a `device_whitelist` which is disabled by default.

## Acknowledgements

Thanks to allenslab for providing the original codebase for this project, [matrix-dashboard](https://github.com/allenslab/matrix-dashboard). You can find his original reddit post [here](https://www.reddit.com/r/3Dprinting/comments/ujyy4g/i_designed_and_3d_printed_a_led_matrix_dashboard/). This project is an adaption of his Spotify app for 64x64 matrices, while also packing some other improvements.

Thanks to ty-porter for [his fork](https://github.com/ty-porter/matrix-dashboard) of matrix-dashboard from which my development branched from. His work on RGBMatrixEmulator was helpful during development.

And finally, thanks to hzeller for his work on [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix).
