# Fusion360-Design-History-Animation
A script to turn your Fusion360 design history timeline into an animation.  When run, this script rolls your design history timeline back to the beginning and saves out screenshots as it steps through each operation in your design.  For many operations (e.g. Extrudes, Revolves), it create a smooth animation by interpolating across a range of values.

![Animation Example](/docs/animation.gif)

This script can be configured to save at any image resolution!  You can optionally add spin to the animation and change various other parameters via a small panel:

![Plugin Panel](/docs/panel.png)

**WARNING - THIS SCRIPT WILL MAKE CHANGES TO YOUR DESIGN FILE.**  I recommended running this script on the copy of your design so that you don't accidentally modify your file.  At the very least, do not save the changes to your file - they involve unlinking references to external components for better control over the animation transitions - you probably do not want these changes.


## Installation

Download this repository as ZIP and unzip the folder (put this folder in a place where you won't delete it later):

![Download button](/docs/download.png)

In the *Design* workspace, go to the *Tools* tab and select *Add Ins > Scripts and Add-Ins...*:

![Tools Menu](/docs/tools.png)

Click the green plus sign next to My Scripts:

![Add Script](/docs/addscript.png)

Then Select the folder called `Design-History-Animation` inside `Fusion360-Design-History-Animation`:

![Select Folder](/docs/selectfolder.png)

You should now see it added to your scripts.  To Run the script, select it and press *Run*:

![Script Added](/docs/scriptadded.png)


## Use

A few notes on use:

- The script uses the current position of the camera in the design for the starting frame.  It will do a fitToView() call before it starts, but the angle does not change.
- The rotation is about the y-axis (this is "up" by Fusion's convention).
- *Timeline Range* sets the start and end position in the timeline that you would like to animate.  By default start is set to 1 and end is set to the current timeline position in the design.  Note that not all operations are animated (e.g. Sketch, Combine, ConstructionPlane).
- *Num Final Frames* adds several frames to the end of the animation, once the script has reached the end of the selected timeline range to animate.

I'm hoping the rest of the parameters in the panel are self-explanatory.


## Creating an Animation Video

After all the still frames (with the name FILENAME_###.png) are generated, I use [ffmpeg](https://ffmpeg.org/) to compile the stills into an animation.  From the terminal run:

```ffmpeg -r 30 -i PATH_TO_FRAMES/FILENAME_%d.png -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -an OUTPUT_DIRECTORY/animation.mp4```

`-r 30` sets the framerate to 30 fps
`-c:v libx264 -preset slow -crf 22` encodes as h.264 with better compression settings  
`-pix_fmt yuv420p` makes it compatible with the web browser
`-an` creates a video with no audio. 
You can optionally specify `-s 640x640` to control the output size of the video. 
If your filename has spaces in it, you can escape them with `-i PATH_TO_FRAMES/filename\ with\ spaces_%d.png`


## Creating an Animated GIF

I upload the resulting video or raw frames to [ezgif](https://ezgif.com/) to create an animated gif.  I'm sure many other solutions exist (e.g. Photoshop, Premiere, GIMP).


## Development

Pull requests welcome!  This is a quick script I wrote for myself, and while it does a decent job at animating the most common Fusion360 operations, there is room for improvement.  Some of this is due to time constraints on my end, others may be limitations of the Fusion API.  Some examples of features I'd like to add:

- **Animating Extrude with Extent "To Object" or "All"**: Since I'm not able to get a distance parameter from this operation, it is difficult to animate.  For now, if the extrude operation creates a new body or component, I have it set to fade that component in.
- **Move**: This operation is throwing an error in the current implementation and is ignored completely.  See TODO comment in code for more details.
- **[FilletFeature](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-9f6de809-6e53-4667-bedb-9e95600411e9) / [ChamferFeature](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7a005e53-0664-479c-9f6a-6146709ca1ef) / [OffsetFacesFeature](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-5FF19D49-8553-4F36-9C7F-8199B2A71933)**: I'm unable to figure out how to extract the extent parameter for these operations.  Bug report [here](https://forums.autodesk.com/t5/fusion-360-api-and-scripts/missing-extent-parameter-for-filletfeature-chamferfeature/td-p/9826317).
- **More robust handling of Joints**: Currently this code assumes that when users add a new component to an assembly, they immediately add a joint to it and move into into the correct position.  Because of this, the code ignores "Occurrence" operations - where the part is initially placed in the assembly, and instead fades in the object at occurrenceOne of the following Joint operation.  This is typically how I set up my files, but I'm sure a more robust approach could be established.  One case where I'm still having trouble is when the Joint's occurrenceOne is not the top-level component of the the new added assembly - see TODO note in Joint handler for more details.
- **Additional timeline operations**: This script does not handle all of the Operations that Fusion360's design history timeline may contain, just those that I frequently use. The quality of the resulting animations could be improved by adding additional handlers for more operations.
