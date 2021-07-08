# Spin-Animation
A script to spin your design and generate still for an animation.

![Animation Example](docs/animation.gif)

This script can be configured to save at any image resolution!  You can specify other parameters via a small panel:

![Plugin Panel](docs/panel.png)


## Installation

See instructions in the [parent README](https://github.com/amandaghassaei/Fusion360-Scripts#installation).

## Use

A few notes on use:

- Rotation is about the y-axis (this is "up" by Fusion's convention) and the zoom level is set by the current zoom of the camera.
- The script uses the current position of the camera for the starting frame.
- *Center X/Y/Z* sets the position of the center point for the spin animation, the camera will center itself around this pivot point, so it will appear in the center of the frame.

I'm hoping the rest of the parameters in the panel are self-explanatory.

## Creating an Animation Video

After all the still frames (with the name FILENAME_###.png) are generated, I use [ffmpeg](https://ffmpeg.org/) to compile the stills into an animation.  From the terminal run:

```ffmpeg -r 30 -i PATH_TO_FRAMES/FILENAME_%d.png -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -an OUTPUT_DIRECTORY/animation.mp4```

`-r 30` sets the framerate to 30 fps  
`-c:v libx264 -preset slow -crf 22` encodes as h.264 with better compression settings  
`-pix_fmt yuv420p` makes it compatible with the web browser  
`-an` creates a video with no audio  
You can optionally specify `-s 640x640` to control the output size of the video  
If your filename has spaces in it, you can escape them with `-i PATH_TO_FRAMES/filename\ with\ spaces_%d.png`  


## Creating an Animated GIF

I upload the resulting video or raw frames to [ezgif](https://ezgif.com/) to create an animated gif.  I'm sure many other solutions exist (e.g. Photoshop, Premiere, GIMP).


## Development

Pull requests welcome!  Some examples of features I'd like to add:

- **Select axis of rotation from edge**: Currently this is set to rotate around the Y axis, but it would be nice to generalize this.