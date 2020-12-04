#Author-Amanda Ghassaei
#Description-Turn your Fusion360 version history into a timelapse animation

import adsk.core, traceback, os, math

app = adsk.core.Application.get()
ui  = app.userInterface

class VersionTimelapse:
    def __init__(self):
        dataFile = app.activeDocument.dataFile

        # Some old code for grabbing all versions of all files in the current folder so they can be saved in chronological order.
        # This ended up looking a bit too erratic imo, but you can try it if you like.
        # # Get all files in the same folder.
        # allDataFiles = dataFile.parentFolder.dataFiles
        # self._filename = dataFile.parentFolder.name
        # # Parse previous versions of allDataFiles.
        # names = [_dataFile.name for _dataFile in allDataFiles]
        # versions = [_dataFile.versions.item(i) for _dataFile in allDataFiles for i in range(_dataFile.versions.count)]

        self._filename = dataFile.name
        # Parse previous versions of active document.
        versions = [dataFile.versions.item(i) for i in range(dataFile.versions.count)]

        # Sort versions.
        # Turns out dataCreated is not a good metric for parsing the lineage.  Use version number instead.
        # versions.sort(key=lambda version: version.dateCreated)
        versions.sort(key=lambda version: int(version.versionId.split('version=')[1]))
        self._versions = versions
        
        # Set initial values.
        # TODO: edit these.
        self._outputPath = os.path.expanduser("~/Desktop/")
        self._width = 2000 # Output image width, in px.
        self._height = 2000 # Output image height, in px.
        self._start = 1 # Starting version number.
        self._end = int(dataFile.versionId.split('version=')[1]) # Ending version number (defaults to current opened version).
        self._fixCamera = True # Use a consistent camera zoom/offset across versions (if False, will adjust camera to fit model boundaries for each version, I think it looks better set to True)
        self._rotate = True # Add model rotation to exported frames.
        self._framesPerRotation = 250 # Number of frames for one complete rotation of model.
        self._finalFrames = 250 # Number of frames of the final version to add to end of sequence.
        # Save current camera target (or override), this only matters if using fixCamera = True.
        camera = app.activeViewport.camera
        self._cameraTarget = camera.target.copy() # adsk.core.Point3D.create(0, 0, 0)
        self._cameraOffset = self._cameraTarget.vectorTo(camera.eye) # adsk.core.Vector3D.create(1, 1, 1)
        self._cameraExtents = camera.viewExtents # Radius of bounding sphere to fit camera view to.

    # Properties
    @property
    def filename(self):
        return self._filename
    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def outputPath(self):
        return self._outputPath
    @outputPath.setter
    def outputPath(self, value):
        self._outputPath = value
    
    @property
    def versions(self):
        return self._versions

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, value):
        self._height = value

    @property
    def start(self):
        return self._start
    @start.setter
    def start(self, value):
        self._start = value

    @property
    def end(self):
        return self._end
    @end.setter
    def end(self, value):
        self._end = value

    @property
    def fixCamera(self):
        return self._fixCamera
    @fixCamera.setter
    def fixCamera(self, value):
        self._fixCamera = value

    @property
    def rotate(self):
        return self._rotate
    @rotate.setter
    def rotate(self, value):
        self._rotate = value

    @property
    def framesPerRotation(self):
        return self._framesPerRotation
    @framesPerRotation.setter
    def framesPerRotation(self, value):
        self._framesPerRotation = value

    @property
    def finalFrames(self):
        return self._finalFrames
    @finalFrames.setter
    def finalFrames(self, value):
        self._finalFrames = value

    def collectFrames(self):
        versions = self.versions
        start = self.start - 1 # Zero index the start value
        end = self.end
        width = self.width
        height = self.height
        filename = self.filename
        outputPath = self.outputPath
        fixCamera = self.fixCamera
        framesPerRotation = self.framesPerRotation if self.rotate else 0
        finalFrames = self.finalFrames

        documents = app.documents

        for i in range(start, end):
            # Close active document.
            app.activeDocument.close(False)

            # Open older version.
            version = versions[i]
            document = documents.open(version, True)

            # Set viewport and rotation.
            shouldUpdateViewport = False
            viewport = app.activeViewport
            camera = viewport.camera
            if fixCamera:
                camera.isFitView = False
                camera.target = self._cameraTarget
                offset = camera.target.copy()
                offset.translateBy(self._cameraOffset)
                camera.eye = offset
                camera.viewExtents = self._cameraExtents
                shouldUpdateViewport = True
            if framesPerRotation > 0:
                angle = math.pi * 2.0 * i / framesPerRotation
                eye = camera.eye
                cos = math.cos(angle)
                sin = math.sin(angle)
                camera.eye = adsk.core.Point3D.create(eye.x * cos + eye.z * sin, eye.y, - eye.x * sin + eye.z * cos)
                shouldUpdateViewport = True
            if shouldUpdateViewport:
                # camera.isSmoothTransition = False # This could speed things up, but it prevents you from seeing what you're going to get in the animation.
                # Set camera property to trigger update.
                viewport.camera = camera

            # Save image.
            success = viewport.saveAsImageFile(outputPath + 'Version_Timelapse_' + filename + '/' + filename + '_' + str(i + 1) + '.png', width, height)
            if not success:
                ui.messageBox('Failed saving image for ' + version.name + ' version ' + version.versionId.split('version=')[1])

        # Add final padding frames.
        for j in range(finalFrames):
            if framesPerRotation > 0:
                angleDelta = math.pi * 2.0 / framesPerRotation
                eye = camera.eye
                cos = math.cos(angleDelta)
                sin = math.sin(angleDelta)
                camera.eye = adsk.core.Point3D.create(eye.x * cos + eye.z * sin, eye.y, - eye.x * sin + eye.z * cos)
                shouldUpdateViewport = True
                # Set camera property to trigger update.
                viewport.camera = camera

            # Save image.
            success = app.activeViewport.saveAsImageFile(outputPath + 'Version_Timelapse_' + filename + '/' + filename + '_' + str(i + j + 2) + '.png', width, height)
            if not success:
                ui.messageBox('Failed saving image for ' + version.name + ' version ' + version.versionId.split('version=')[1])


        # # Close active document.
        # app.activeDocument.close(False)

def run(context):
    try:
        ui.messageBox("""
WARNING: I recommend testing this on a design you don't care about to be sure that it works as expected and doesn't harm your file.  
You can quit Fusion now to stop the script if you are unsure about continuing.\n\n
This script is slow and may take 2-3 hrs for designs with hundreds of previous versions.  
Output images will land on your Desktop as they are saved, but it may take 30min or more for the first image to appear.\n\n
To change animation parameters, you will need to modify the code directly - see github.com/amandaghassaei/Fusion360-Design-Version-Timelapse for more details.
            """)
        timelapse = VersionTimelapse()
        timelapse.collectFrames()
        # When the command is done, terminate the script.
        # This will release all globals which will remove all event handlers.
        adsk.terminate()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
