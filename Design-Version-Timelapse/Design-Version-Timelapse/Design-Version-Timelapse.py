#Author-Amanda Ghassaei
#Description-Turn your Fusion360 version history into a timelapse animation

import adsk.core, traceback, os, math, json
import neu_server 
import neu_modeling 

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
        self._turnOffSectionAnalysis = True # Turning off section analysis gives better quality animations.
        self._rotate = True # Add model rotation to exported frames.
        self._rotationDirection = 1 # Use -1 to reverse rotation direction.
        self._framesPerRotation = 250 # Number of frames for one complete rotation of model.
        self._finalFrames = 0 # Number of frames of the final version to add to end of sequence.
        # Save current camera target (or override), this only matters if using fixCamera = True.
        camera = app.activeViewport.camera
        self._cameraTarget = camera.target.copy() # adsk.core.Point3D.create(0, 0, 0)
        self._cameraOffset = self._cameraTarget.vectorTo(camera.eye) # adsk.core.Vector3D.create(1, 1, 1)
        self._cameraExtents = camera.viewExtents # Radius of bounding sphere to fit camera view to.

    def collectFrames(self):
        versions = self._versions
        start = self._start - 1 # Zero index the start value
        end = self._end
        width = self._width
        height = self._height
        filename = self._filename
        outputPath = self._outputPath
        fixCamera = self._fixCamera
        turnOffSectionAnalysis = self._turnOffSectionAnalysis
        framesPerRotation = self._framesPerRotation if self._rotate else 0
        rotationDirection = self._rotationDirection
        finalFrames = self._finalFrames

        documents = app.documents

        for i in range(start, end):
            # Close active document.
            app.activeDocument.close(False)

            # Open older version.
            version = versions[i]
            document = documents.open(version, True)

            if turnOffSectionAnalysis:
                # This is not officially supported.
                # https://forums.autodesk.com/t5/fusion-360-api-and-scripts/access-section-analysis/m-p/9693712
                # For some reason turning off all analyses and turning off each individual analysis is required.
                analyses = neu_server.get_entity_id("VisualAnalyses")
                neu_server.set_entity_properties(analyses, {'isVisible': False})
                # Dump all properties
                # ui.messageBox(json.dumps(neu_server.get_entity_properties(analyses)))
                for j in range(neu_modeling.get_child_count(analyses)):
                    analysis = neu_modeling.get_child(analyses, j) 
                    # Dump all properties
                    # ui.messageBox(json.dumps(neu_server.get_entity_properties(analysis)))
                    neu_server.set_entity_properties(analysis, {'isVisible': False})

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
                angle = rotationDirection * math.pi * 2.0 * i / framesPerRotation
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
WARNING: I recommend testing this on a design you don't care about to be sure that it works as expected and doesn't harm your file.  You can quit Fusion now to stop the script if you are unsure about continuing.\n
This script is slow and may take 2-3 hrs for designs with hundreds of previous versions.  Output images will land on your Desktop as they are saved, but it may take 30min or more for the first image to appear.\n
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
