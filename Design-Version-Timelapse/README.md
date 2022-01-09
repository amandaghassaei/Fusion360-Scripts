# Design-Version-Timelapse
A script to turn your Fusion360 version history (i.e. all your previous saves) into a timelapse animation.

![Animation Example](docs/animation.gif)

This script can be configured to save at any image resolution and has a few other configurable controls including spin and other camera stabilization settings.  See [Use](#Use) for more details.  

**WARNING - USE AT YOUR OWN RISK.**  This script is opens old versions of your design and takes screenshots.  It should not do any saving operations or promote old versions.  However, things in Fusion's API could change at any point without warning and you never know what repercussions that might have.  So please test this out on something you don't care much about first.  I use this on my own files and have had no issues, but if you have a very important document you want to run this on, you might want to at least save a copy of it before proceeding.


## Installation

See instructions in the [parent README](https://github.com/amandaghassaei/Fusion360-Scripts#installation).


## Use

Unfortunately, I could not create an interactive panel for this script because it was causing Fusion to crash when it goes to open older versions of the design.  So for now you're going to have to open up the script and edit the parameters by hand.  Luckily, you only need to install once, and any saved changes will be updated when you run the script from Fusion.

To modify the script parameters, look for a comment `# Set initial values.` in [Design-version-Timelapse.py](Design-Version-Timelapse/Design-Version-Timelapse.py).

```py
# Set initial values.
self._outputPath = os.path.expanduser("~/Desktop/")
self._width = 2000 # Output image width, in px.
self._height = 2000 # Output image height, in px.
self._start = 1 # Starting version number.
self._end = int(dataFile.versionId.split('version=')[1]) # Ending version number (defaults to current opened version).
self._fixCamera = True # Use a consistent camera zoom/offset across versions (if False, will adjust camera to fit model boundaries for each version, I think it looks better set to True)
self._turnOffSectionAnalysis = True # Turning off section analysis gives better quality animations.
self._rotate = True # Add model rotation to exported frames.
self._framesPerRotation = 250 # Number of frames for one complete rotation of model.
self._finalFrames = 0 # Number of frames of the final version to add to end of sequence.
# Save current camera target (or override), this only matters if using fixCamera = True.
camera = app.activeViewport.camera
self._cameraTarget = camera.target.copy() # adsk.core.Point3D.create(0, 0, 0)
self._cameraOffset = self._cameraTarget.vectorTo(camera.eye) # adsk.core.Vector3D.create(1, 1, 1)
self._cameraExtents = camera.viewExtents # Radius of bounding sphere to fit camera view to.
```

Some notes:

- Test this on something small and unimportant to make sure it's working as expected.
- This script usually takes a few (2-3) hrs to run for complex designs with several hundred versions.  The script starts by doing a sort of the versions based on their version number so that they are saved in the same order.  This may take some time (30 mins) to complete for designs with >200 versions, so be patient.  As long as you see the cursor spinning in Fusion, you're good.  Once it starts saving files you will see your old versions pop up on the screen.
- By default, the animation frames will be saved in a folder with the same name as your design file on your Desktop.


## Creating an Animation Video/GIF

See instructions in the [parent README](https://github.com/amandaghassaei/Fusion360-Scripts#creating-an-animation-video).


## Development

Pull requests welcome!  This is a quick script I wrote for myself and I'm sure there are additional features that could be added to make it even better!
