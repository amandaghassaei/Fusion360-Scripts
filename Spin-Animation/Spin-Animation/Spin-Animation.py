#Author-Amanda Ghassaei
#Description-Spinning animation of design

import adsk.core, adsk.fusion, traceback, math, os

app = adsk.core.Application.get()
if app:
    ui  = app.userInterface

# Global set of event handlers to keep them referenced for the duration of the command
handlers = []

# Keep the frameRecorder object in global namespace.
frameRecorder = None

# Event handler for the inputChanged event.
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        
        # Check the value of the input.
        input = eventArgs.input
        if input.id == 'centerX':
            frameRecorder.centerX = input.value
        elif input.id == 'centerY':
            frameRecorder.centerY = input.value
        elif input.id == 'centerZ':
            frameRecorder.centerZ = input.value

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs

            for input in inputs:
                if input.id == 'filename':
                    frameRecorder.filename = input.value
                elif input.id == 'outputPath':
                    frameRecorder.outputPath = input.value
                elif input.id == 'width':
                    frameRecorder.width = input.value
                elif input.id == 'height':
                    frameRecorder.height = input.value
                elif input.id == 'framesPerRotation':
                    frameRecorder.framesPerRotation = input.value
                elif input.id == 'numRotations':
                    frameRecorder.numRotations = input.value
                elif input.id == 'centerX':
                    frameRecorder.centerX = input.value
                elif input.id == 'centerY':
                    frameRecorder.centerY = input.value
                elif input.id == 'centerZ':
                    frameRecorder.centerZ = input.value

            frameRecorder.collectFrames()

            args.isValidResult = True
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # When the command is done, terminate the script.
            # This will release all globals which will remove all event handlers.
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)

            onInputChanged = CommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)

            onDestroy = CommandDestroyHandler()
            cmd.destroy.add(onDestroy)

            # Keep the handler referenced beyond this function.
            handlers.append(onExecute)
            handlers.append(onInputChanged)
            handlers.append(onDestroy)

            pos_infinity = float('inf')
            neg_infinity = float('-inf')
            max_int = 2147483647
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            units = design.unitsManager.defaultLengthUnits

            # Define the inputs.
            inputs = cmd.commandInputs
            # File params.
            inputs.addStringValueInput('filename', 'Filename', frameRecorder.filename)
            inputs.addStringValueInput('outputPath', 'Output Path', frameRecorder.outputPath)
            inputs.addIntegerSpinnerCommandInput('width', 'Image Width (px)', 1, max_int, 1, frameRecorder.width)
            inputs.addIntegerSpinnerCommandInput('height', 'Image Height (px)', 1, max_int, 1, frameRecorder.height)
            # Animation params.
            inputs.addIntegerSpinnerCommandInput('framesPerRotation', 'Frames per Rotation', 1, max_int, 1, frameRecorder.framesPerRotation)
            inputs.addIntegerSpinnerCommandInput('numRotations', 'Num Rotations', 1, max_int, 1, frameRecorder.numRotations)
            # Camera params.
            inputs.addFloatSpinnerCommandInput('centerX', 'Center X', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerX)
            inputs.addFloatSpinnerCommandInput('centerY', 'Center Y', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerY)
            inputs.addFloatSpinnerCommandInput('centerZ', 'Center Z', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerZ)


        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class FrameRecorder:
    def __init__(self):
        dataFile = app.activeDocument.dataFile

        # Set initial values.
        self._filename = dataFile.name
        self._outputPath = os.path.expanduser("~/Desktop/")
        self._width = 2000
        self._height = 2000
        self._framesPerRotation = 25
        self._numRotations = 1

        viewport = app.activeViewport
        camera = viewport.camera
        self._centerX = camera.target.x
        self._centerY = camera.target.y
        self._centerZ = camera.target.z
        self._cameraTarget = adsk.core.Point3D.create(self._centerX, self._centerY, self._centerZ)
        self._cameraOffset = self._cameraTarget.vectorTo(camera.eye)
        self._cameraExtents = camera.viewExtents # Radius of bounding sphere to fit camera view to.

    # Properties.
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
    def centerX(self):
        return self._centerX
    @centerX.setter
    def centerX(self, value):
        self._centerX = value
        self.updateCamera()
    @property
    def centerY(self):
        return self._centerY
    @centerY.setter
    def centerY(self, value):
        self._centerY = value
        self.updateCamera()
    @property
    def centerZ(self):
        return self._centerZ
    @centerZ.setter
    def centerZ(self, value):
        self._centerZ = value
        self.updateCamera()

    @property
    def framesPerRotation(self):
        return self._framesPerRotation
    @framesPerRotation.setter
    def framesPerRotation(self, value):
        self._framesPerRotation = value

    @property
    def numRotations(self):
        return self._numRotations
    @numRotations.setter
    def numRotations(self, value):
        if value < 1:
            value = 1
        self._numRotations = value

    def updateCamera(self):
        viewport = app.activeViewport
        camera = viewport.camera
        self._cameraTarget = adsk.core.Point3D.create(self._centerX, self._centerY, self._centerZ)
        self._cameraOffset = self._cameraTarget.vectorTo(camera.eye)
        self._cameraExtents = camera.viewExtents # Radius of bounding sphere to fit camera view to.
        camera.target = self._cameraTarget
        offset = camera.target.copy()
        offset.translateBy(self._cameraOffset)
        camera.eye = offset
        camera.viewExtents = self._cameraExtents
        # Set camera property to trigger update.
        camera.upVector = adsk.core.Vector3D.create(0, 1, 0)
        viewport.camera = camera

    def collectFrames(self):
        width = self.width
        height = self.height
        filename = self.filename
        outputPath = self.outputPath
        framesPerRotation = self.framesPerRotation
        numRotations = self.numRotations

        viewport = app.activeViewport

        for i in range(0, framesPerRotation * numRotations):
            camera = viewport.camera
            camera.target = self._cameraTarget
            offset = camera.target.copy()
            offset.translateBy(self._cameraOffset)
            camera.eye = offset
            camera.viewExtents = self._cameraExtents
            # Rotate camera around y axis.
            angle = math.pi * 2.0 * i / framesPerRotation
            eye = camera.eye
            cos = math.cos(angle)
            sin = math.sin(angle)
            camera.eye = adsk.core.Point3D.create(eye.x * cos + eye.z * sin, eye.y, - eye.x * sin + eye.z * cos)
            # Set camera property to trigger update.
            camera.upVector = adsk.core.Vector3D.create(0, 1, 0)
            viewport.camera = camera

            # Save image.
            success = app.activeViewport.saveAsImageFile(outputPath + 'Spin_Animation_' + filename + '/' + filename + '_' + str(i) + '.png', width, height)
            if not success:
                ui.messageBox('Failed saving viewport image.')



def run(context):
    global frameRecorder
    try:
        # Init a frameRecorder object.
        if frameRecorder == None:
            frameRecorder = FrameRecorder()

        commandDefinitions = ui.commandDefinitions
        # Check the command exists or not.
        cmdDef = commandDefinitions.itemById('spinanimation')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('spinanimation',
                    'Spin Animation',
                    'Create animation frames of your design spinning')

        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # Keep the handler referenced beyond this function.
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
