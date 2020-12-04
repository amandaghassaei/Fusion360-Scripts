# Design-Version-Timelapse
A script to turn your Fusion360 version history (i.e. all your previous saves) into a timelapse animation.

![Animation Example](docs/animation.gif)

This script can be configured to save at any image resolution and has a few other configurable controls including spin and other camera stabilization settings.  See [Use](#Use) for more details.  

**WARNING - USE AT YOUR OWN RISK.**  This script is opens old versions of your design and takes screenshots without doing any saving operations or promoting the old version.  However, things in Fusion's API could change at any point without warning and you never know what repercussions that might have.  So please test this out on something you don't care much about first.  I use this on my own files and have had no issues, but if you have a very important document you want to run this on, you might want to at least save a copy of it before proceeding.

If you like this, you should also check out [Fusion360-Design-History-Animation](https://github.com/amandaghassaei/Fusion360-Design-History-Animation).

## Installation

See instructions in the parent README.

## Use

Unfortunately, I could not create an interactive panel for this script because it was causing Fusion to crash when it goes to open older versions of the design.  So for now you're going to have to open up the script and edit the parameters by hand.  Luckily, you only need to install once, and any saved changes will be updated when you run the script from Fusion.

To modify the script parameters, look for a comment `# Set initial values.` in [Design-version-Timelapse.py](Design-Version-Timelapse/Design-Version-Timelapse.py).

Some notes:

- Test this on something small and unimportant to make sure it's working as expected.
- This script usually takes a few (2-3) hrs to run for complex designs with several hundred versions.  The script starts by doing a sort of the versions based on their version number so that they are saved in the same order.  This may take some time (30 mins) to complete for designs with >200 versions, so be patient.  As long as you see the cursor spinning in Fusion, you're good.  Once it starts saving files you will see your old versions pop up on the screen.
- By default, the animation frames will be saved in a folder with the same name as your design file on your Desktop.


## Creating an Animation Video

After all the still frames (with the name FILENAME_###.png) are generated, I use [ffmpeg](https://ffmpeg.org/) to compile the stills into an animation.  From the terminal run:

```ffmpeg -r 15 -i PATH_TO_FRAMES/FILENAME_%d.png -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -an OUTPUT_DIRECTORY/animation.mp4```

`-r 15` sets the framerate to 15 fps
`-c:v libx264 -preset slow -crf 22` encodes as h.264 with better compression settings  
`-pix_fmt yuv420p` makes it compatible with the web browser
`-an` creates a video with no audio. 
You can optionally specify `-s 640x640` to control the output size of the video. 
If your filename has spaces in it, you can escape them with `-i PATH_TO_FRAMES/filename\ with\ spaces_%d.png`

In case you need to delete some of the frames from the sequence, I've included a script for renaming them back to a sequential order that ffmpeg expects:

`./renumber_files.sh DIRECTORY_TO_RENUMBER`


## Creating an Animated GIF

I upload the resulting video or raw frames to [ezgif](https://ezgif.com/) to create an animated gif.  I'm sure many other solutions exist (e.g. Photoshop, Premiere, GIMP).


## Development

Pull requests welcome!  This is a quick script I wrote for myself and I'm sure there are additional features that could be added to make it even better!  

One thing I'm looking at changing is an option to turn off Section Analysis in old versions for a smoother animation (or possibly have it always on and looking at the same section).  This is currently not supported through the API, see discussion [here](https://forums.autodesk.com/t5/fusion-360-api-and-scripts/access-section-analysis/m-p/9693712).
