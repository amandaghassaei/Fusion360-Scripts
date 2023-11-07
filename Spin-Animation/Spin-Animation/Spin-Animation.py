#Author-Amanda Ghassaei
#Description-Spinning animation of design
from enum import StrEnum

import adsk.core, adsk.fusion, traceback, math, os

app = adsk.core.Application.get()
if app:
    ui  = app.userInterface

# Global set of event handlers to keep them referenced for the duration of the command
handlers = []

centerEndInputs = []
zoomEndInputs = []

# Keep the frameRecorder object in global namespace.
frameRecorder = None

class RotationAxis(StrEnum):
    X = "X"
    Y = "Y"
    Z = "Z"

# Event handler for the inputChanged event.
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        
        # Check the value of the input.
        input = eventArgs.input
        if input.id == 'centerStartX':
            centerStart = frameRecorder.centerStart
            frameRecorder.centerStart = (input.value, centerStart[1], centerStart[2])
        elif input.id == 'centerStartY':
            centerStart = frameRecorder.centerStart
            frameRecorder.centerStart = (centerStart[0], input.value, centerStart[2])
        elif input.id == 'centerStartZ':
            centerStart = frameRecorder.centerStart
            frameRecorder.centerStart = (centerStart[0], centerStart[1], input.value)
        elif input.id == 'centerEndX':
            centerEnd = frameRecorder.centerEnd
            frameRecorder.centerEnd = (input.value, centerEnd[1], centerEnd[2])
        elif input.id == 'centerEndY':
            centerEnd = frameRecorder.centerEnd
            frameRecorder.centerEnd = (centerEnd[0], input.value, centerEnd[2])
        elif input.id == 'centerEndZ':
            centerEnd = frameRecorder.centerEnd
            frameRecorder.centerEnd = (centerEnd[0], centerEnd[1], input.value)
        elif input.id == 'animateCenter':
            frameRecorder.animateCenter = input.value
        elif input.id == 'zoomStart':
            frameRecorder.zoomStart = input.value
        elif input.id == 'zoomEnd':
            frameRecorder.zoomEnd = input.value
        elif input.id == 'animateZoom':
            frameRecorder.animateZoom = input.value
        elif input.id == 'upAxis':
            if input.selectedItem.name == 'Y':
                frameRecorder.upAxis = RotationAxis.Y
            elif input.selectedItem.name == 'Z':
                frameRecorder.upAxis = RotationAxis.Z
            else:
                raise Exception("Invalid up axis selected")


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
                elif input.id == 'upAxis':
                    if not input:
                        raise Exception("No up axis selected")
                    elif input.selectedItem.name == 'Y':
                        frameRecorder.upAxis = RotationAxis.Y
                    elif input.selectedItem.name == 'Z':
                        frameRecorder.upAxis = RotationAxis.Z
                    else:
                        raise Exception("Invalid up axis selected")
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
            inputs.addFloatSpinnerCommandInput('numRotations', 'Num Rotations', '', neg_infinity, pos_infinity, 0.1, frameRecorder.numRotations)
            # Camera params.
            dropdown = inputs.addDropDownCommandInput('upAxis', 'Up Vector', adsk.core.DropDownStyles.TextListDropDownStyle)
            dropdownItems = dropdown.listItems
            dropdownItems.add('Y', True)  # Default to Y Up
            dropdownItems.add('Z', False)

            inputs.addFloatSpinnerCommandInput('centerStartX', 'Center X', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerStart[0])
            inputs.addFloatSpinnerCommandInput('centerStartY', 'Center Y', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerStart[1])
            inputs.addFloatSpinnerCommandInput('centerStartZ', 'Center Z', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerStart[2])
            inputs.addFloatSpinnerCommandInput('zoomStart', 'Zoom Radius', units, 0, pos_infinity, 0.1, frameRecorder.zoomStart)
            inputs.addBoolValueInput('animateCenter', 'Animate Center Position', True, '', frameRecorder.animateCenter)
            centerEndInputs.append(inputs.addFloatSpinnerCommandInput('centerEndX', 'Center X End', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerEnd[0]))
            centerEndInputs.append(inputs.addFloatSpinnerCommandInput('centerEndY', 'Center Y End', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerEnd[1]))
            centerEndInputs.append(inputs.addFloatSpinnerCommandInput('centerEndZ', 'Center Z End', units, neg_infinity, pos_infinity, 0.1, frameRecorder.centerEnd[2]))
            inputs.addBoolValueInput('animateZoom', 'Animate Zoom', True, '', frameRecorder.animateZoom)
            zoomEndInputs.append(inputs.addFloatSpinnerCommandInput('zoomEnd', 'Zoom Radius End', units, 0, pos_infinity, 0.1, frameRecorder.zoomEnd))

            # Trigger refresh of ui visibility
            frameRecorder.animateCenter = frameRecorder.animateCenter
            frameRecorder.animateZoom = frameRecorder.animateZoom


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
        self._upAxis = RotationAxis.Y

        viewport = app.activeViewport
        camera = viewport.camera
        self._centerStart = [camera.target.x, camera.target.y, camera.target.z]
        self._centerEnd = [camera.target.x, camera.target.y, camera.target.z]
        self._animateCenter = False
        self._cameraTarget = adsk.core.Point3D.create(self._centerStart[0], self._centerStart[1], self._centerStart[2])
        self._cameraOffset = self._cameraTarget.vectorTo(camera.eye)

        self._zoomStart = camera.viewExtents / 2.54 # Radius of bounding sphere to fit camera view to.
        self._zoomEnd = self._zoomStart
        self._animateZoom = False
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
    def centerStart(self):
        return self._centerStart
    @centerStart.setter
    def centerStart(self, center):
        x, y, z = center
        self._centerStart = [x, y, z]
        self.updateCameraTarget(x, y, z)
    @property
    def centerEnd(self):
        return self._centerEnd
    @centerEnd.setter
    def centerEnd(self, center):
        x, y, z = center
        self._centerEnd = [x, y, z]
        self.updateCameraTarget(x, y, z)

    @property
    def animateCenter(self):
        return self._animateCenter
    @animateCenter.setter
    def animateCenter(self, value):
        self._animateCenter = value
        if not value:
            # centerEnd = centerStart
            self.centerEnd = (self.centerStart[0], self.centerStart[1], self.centerStart[2])
        # Show/hide inputs.
        for input in centerEndInputs:
            input.isVisible = self._animateCenter

    @property
    def animateZoom(self):
        return self._animateZoom
    @animateZoom.setter
    def animateZoom(self, value):
        self._animateZoom = value
        if not value:
            # zoomEnd = zoomStart
            self.zoomEnd = self.zoomStart
        # Show/hide inputs.
        for input in zoomEndInputs:
            input.isVisible = self._animateZoom

    @property
    def zoomStart(self):
        return self._zoomStart
    @zoomStart.setter
    def zoomStart(self, value):
        self._zoomStart = value
        self.updateCamera(value)
    @property
    def zoomEnd(self):
        return self._zoomEnd
    @zoomEnd.setter
    def zoomEnd(self, value):
        self._zoomEnd = value
        self.updateCamera(value)

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
        self._numRotations = value

    @property
    def upAxis(self):
        return self._upAxis
    @upAxis.setter
    def upAxis(self, value):
        self._upAxis = value
        self.updateCamera()

    @property
    def upVector(self):
        if self._upAxis == RotationAxis.X:
            return adsk.core.Vector3D.create(1, 0, 0)
        elif self._upAxis == RotationAxis.Y:
            return adsk.core.Vector3D.create(0, 1, 0)
        elif self._upAxis == RotationAxis.Z:
            return adsk.core.Vector3D.create(0, 0, 1)
        else:
            raise Exception("Invalid up axis")

    def updateCameraTarget(self, x, y, z):
        viewport = app.activeViewport
        camera = viewport.camera
        self._cameraOffset = self._cameraTarget.vectorTo(camera.eye)
        self._cameraTarget = adsk.core.Point3D.create(x, y, z)
        self.updateCamera()

    def updateCamera(self, extents=None):
        viewport = app.activeViewport
        camera = viewport.camera
        cameraExtents = camera.viewExtents # Radius of bounding sphere to fit camera view to.
        if extents != None:
            cameraExtents = extents
        camera.target = self._cameraTarget
        offset = camera.target.copy()
        offset.translateBy(self._cameraOffset)
        camera.eye = offset
        camera.viewExtents = cameraExtents
        # Set camera property to trigger update.
        camera.upVector = self.upVector
        viewport.camera = camera

    def _rotateAroundAxis(self, camera, angle):
        eye = camera.eye
        cos = math.cos(angle)
        sin = math.sin(angle)

        if self.upAxis == RotationAxis.X:
            raise NotImplementedError("X axis rotation not yet implemented")
        elif self.upAxis == RotationAxis.Y:
            camera.eye = adsk.core.Point3D.create(eye.x * cos - eye.z * sin, eye.y, eye.x * sin + eye.z * cos)
        elif self.upAxis == RotationAxis.Z:
            camera.eye = adsk.core.Point3D.create(eye.x * cos - eye.y * sin, eye.x * sin + eye.y * cos, eye.z)
        # Set camera property to trigger update.
        camera.upVector = self.upVector
        return camera

    def collectFrames(self):
        width = self.width
        height = self.height
        filename = self.filename
        outputPath = self.outputPath
        framesPerRotation = self.framesPerRotation
        numRotations = self.numRotations
        zoomStart = self.zoomStart
        zoomEnd = self.zoomEnd if self.animateZoom else zoomStart
        centerStart = self.centerStart
        centerEnd = self.centerEnd if self.animateCenter else centerStart

        viewport = app.activeViewport
        numFrames = int(abs(framesPerRotation * numRotations))

        for i in range(0, numFrames):
            t = float(i) / float(numFrames)
            camera = viewport.camera
            x = centerEnd[0] * t + centerStart[0] * (1 - t)
            y = centerEnd[1] * t + centerStart[1] * (1 - t)
            z = centerEnd[2] * t + centerStart[2] * (1 - t)
            camera.target = adsk.core.Point3D.create(x, y, z)
            offset = camera.target.copy()
            offset.translateBy(self._cameraOffset)
            camera.eye = offset
            camera.viewExtents = zoomEnd * t + zoomStart * (1 - t)
            # Rotate camera around axis.
            angle = math.pi * 2.0 * i / framesPerRotation
            if numRotations < 0:
                angle = angle * -1.0
            viewport.camera = self._rotateAroundAxis(camera, angle)

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
