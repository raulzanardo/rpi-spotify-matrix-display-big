# rpi-spotify-matrix-display

A Spotify display for led matrix forked from the [Kylejohnsonkj's](https://github.com/kylejohnsonkj) [rpi-spotify-matrix-display](https://github.com/kylejohnsonkj/rpi-spotify-matrix-display) modified to run in a 192x128 matrix setup.

## Hardware

TODO

## Spotify Pre-Setup

1. Go to https://developer.spotify.com/dashboard
2. Create an account and/or login
3. Select "Create app" (name/description does not matter)
4. Add http://127.0.0.1:8080/callback under Redirect URIs
5. Save, then tap "Settings" in the upper right
6. Copy the generated Client ID and Secret ID for later

## Quick Run (on a Pi)

1. Clone and enter the repo
   - `git clone --recurse-submodules https://github.com/raulzanardo/rpi-spotify-matrix-display`
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
   - or run script at the root of the repo:
   - `chmod +x start.sh`
   - `./start.sh`

## Arguments

| Argument              | Default | Description                                       |
| :-------------------- | :------ | :------------------------------------------------ |
| `-f` , `--fullscreen` | false   | Always display album art in full screen (192x128) |
| `-h` , `--help`       | false   | Display help messages for arguments               |

## Configuration

Configuration is handled in the config.ini. I have included my own as a sample.

For Matrix configuration, see https://github.com/hzeller/rpi-rgb-led-matrix#changing-parameters-via-command-line-flags. More extensive customization can be done in `impl/controller_v3.py` directly.

Note: The `shutdown_delay` value (in seconds) controls automatic screen shutdown when music is inactive — set `shutdown_delay = 0` to disable automatic shutdown and keep the display on.

For Spotify configuration, set the `client_id` and `client_secret` to your own. You may leave `redirect_uri` alone. I have also included a `device_whitelist` which is disabled by default.

## Acknowledgements

Thanks to allenslab and Kylejohnsonkj for providing the original codebase for this project, [rpi-spotify-matrix-display](https://github.com/kylejohnsonkj/rpi-spotify-matrix-display) and [matrix-dashboard](https://github.com/allenslab/matrix-dashboard). You can find his original reddit post [here](https://www.reddit.com/r/3Dprinting/comments/ujyy4g/i_designed_and_3d_printed_a_led_matrix_dashboard/). This project is an adaption of his Spotify app for 192x128 matrices, while also packing some other improvements.

Thanks to ty-porter for [his fork](https://github.com/ty-porter/matrix-dashboard) of matrix-dashboard from which my development branched from.

And finally, thanks to hzeller for his work on [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix).
