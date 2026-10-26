#Author-Amanda Ghassaei
#Description-Turn your Fusion360 design history timeline into an animation
#Modified by-Colin Holloway
#Modification date-2026-10-26
#Changes-XYZ rotation selection, conditional frame validation, Windows paths, unique axis-labelled output folders, original camera view restoration, and automatic timeline-group expansion/restoration.

import adsk.core, adsk.fusion, traceback, math, os

app = adsk.core.Application.get()
if app:
    ui  = app.userInterface

# Global set of event handlers to keep them referenced for the duration of the command
handlers = []

# Keep the timelapse object in global namespace.
timelapse = None

# Colin Holloway | 2026-10-26: Remember only groups this run expands.
# Restoring these on command destruction also handles the Cancel button.
expandedTimelineGroups = []


def expandTimelineGroups(timeline):
    # Colin Holloway | 2026-10-26: Expand groups BEFORE the dialog
    # calculates its timeline range; collapsed groups count as one timeline step.
    global expandedTimelineGroups
    expandedTimelineGroups = []
    groups = timeline.timelineGroups
    try:
        for index in range(groups.count):
            group = groups.item(index)
            if group.isCollapsed:
                group.isCollapsed = False
                expandedTimelineGroups.append(group)
    except:
        restoreTimelineGroups()
        raise


def restoreTimelineGroups():
    # Colin Holloway | 2026-10-26: Re-collapse only originally
    # collapsed groups; leave groups originally expanded untouched.
    global expandedTimelineGroups
    try:
        for group in reversed(expandedTimelineGroups):
            if group.isValid:
                group.isCollapsed = True
    finally:
        expandedTimelineGroups = []

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            for input in inputs:
                if input.id == 'filename':
                    timelapse.filename = input.value
                elif input.id == 'outputPath':
                    timelapse.outputPath = input.value
                elif input.id == 'saveObj':
                    timelapse.saveObj = input.value
                elif input.id == 'width':
                    timelapse.width = input.value
                elif input.id == 'height':
                    timelapse.height = input.value
                elif input.id == 'range':
                    timelapse.start = input.valueOne
                    timelapse.end = input.valueTwo
                elif input.id == 'interpolationFrames':
                    timelapse.interpolationFrames = input.value
                elif input.id == 'rotate':
                    timelapse.rotate = input.value
                # Colin Holloway | 2026-10-26: Read the selected X/Y/Z rotation axis from the dialog.
                elif input.id == 'rotationAxis':
                    timelapse.rotationAxis = input.selectedItem.name
                elif input.id == 'framesPerRotation':
                    timelapse.framesPerRotation = input.value
                elif input.id == 'finalFrames':
                    timelapse.finalFrames = input.value

            timelapse.collectFrames()

            args.isValidResult = True
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Colin Holloway | 2026-10-26: Restore original timeline
            # group visibility on completion, cancellation, or execution failure.
            restoreTimelineGroups()
            # When the command is done, terminate the script.
            # This will release all globals which will remove all event handlers.
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Colin Holloway | 2026-10-26: Allow zero rotation frames only when rotation is disabled.
class CommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        inputs = args.firingEvent.sender.commandInputs
        rotate = inputs.itemById('rotate').value
        frames = inputs.itemById('framesPerRotation').value
        # Zero is valid when rotation is disabled, but not when enabled.
        args.areInputsValid = (not rotate) or (frames >= 1)


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            # Colin Holloway | 2026-10-26: Register rotation-dependent input validation.
            onValidate = CommandValidateInputsHandler()
            cmd.validateInputs.add(onValidate)
            onDestroy = CommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # Keep the handler referenced beyond this function.
            handlers.append(onExecute)
            handlers.append(onValidate)
            handlers.append(onDestroy)

            max_int = 2147483647

            # Define the inputs.
            inputs = cmd.commandInputs
            # File params.
            inputs.addStringValueInput('filename', 'Filename', timelapse.filename)
            inputs.addStringValueInput('outputPath', 'Output Path', timelapse.outputPath)
            inputs.addBoolValueInput('saveObj', 'Save .obj Files', True, '', timelapse.saveObj)
            inputs.addIntegerSpinnerCommandInput('width', 'Image Width (px)', 1, max_int, 1, timelapse.width)
            inputs.addIntegerSpinnerCommandInput('height', 'Image Height (px)', 1, max_int, 1, timelapse.height)
            # Animation params.
            inputs.addIntegerSliderCommandInput('range', 'Timeline Range', 1, timelapse.timeline.count, True)
            inputs.itemById('range').valueOne = timelapse.start
            inputs.itemById('range').valueTwo = timelapse.end
            inputs.addIntegerSpinnerCommandInput('interpolationFrames', 'Frames per Operation', 1, max_int, 1, timelapse.interpolationFrames)
            inputs.addBoolValueInput('rotate', 'Should Rotate Design', True, '', timelapse.rotate)
            # Colin Holloway | 2026-10-26: Add mutually exclusive X/Y/Z rotation-axis radio buttons.
            axisInput = inputs.addRadioButtonGroupCommandInput('rotationAxis', 'Axis of Rotation')
            for axis in ('X', 'Y', 'Z'):
                axisInput.listItems.add(axis, axis == timelapse.rotationAxis)
            # Colin Holloway | 2026-10-26: Permit zero in spinner; validator enforces positive frames when rotating.
            inputs.addIntegerSpinnerCommandInput('framesPerRotation', 'Frames per Rotation', 0, max_int, 1, timelapse.framesPerRotation)
            inputs.addIntegerSpinnerCommandInput('finalFrames', 'Num Final Frames', 0, max_int, 1, timelapse.finalFrames)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class HistoryTimelapse:
    def __init__(self, design):
        dataFile = app.activeDocument.dataFile

        # Set initial values.
        self._filename = dataFile.name
        # Colin Holloway | 2026-10-26: Normalize the default Desktop path for Windows.
        self._outputPath = os.path.normpath(os.path.join(os.path.expanduser("~"), "Desktop"))
        self._saveObj = False
        self._timeline = design.timeline
        self._width = 2000
        self._height = 2000
        self._start = 1
        self._end = self._timeline.markerPosition
        self._interpolationFrames = 5
        self._rotate = True
        # Colin Holloway | 2026-10-26: Default to the original Y-axis rotation behaviour.
        self._rotationAxis = 'Y'
        self._framesPerRotation = 500
        self._finalFrames = 0
        self._design = design

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
    def saveObj(self):
        return self._saveObj
    @saveObj.setter
    def saveObj(self, value):
        self._saveObj = value
    
    @property
    def timeline(self):
        return self._timeline

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
    def interpolationFrames(self):
        return self._interpolationFrames
    @interpolationFrames.setter
    def interpolationFrames(self, value):
        self._interpolationFrames = value

    @property
    def rotate(self):
        return self._rotate
    @rotate.setter
    def rotate(self, value):
        self._rotate = value

    @property
    # Colin Holloway | 2026-10-26: Expose and validate the selected rotation axis.
    def rotationAxis(self):
        return self._rotationAxis
    @rotationAxis.setter
    def rotationAxis(self, value):
        if value not in ('X', 'Y', 'Z'):
            raise ValueError('Invalid rotation axis: ' + str(value))
        self._rotationAxis = value

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
        if value < 0:
            value = 0
        self._finalFrames = value

    @property
    def design(self):
        return self._design

    def isNumericExtent(self, extent):
        classname = type(extent).__name__
        # ui.messageBox(classname)
        if classname == 'DistanceExtentDefinition':
            return True
        if classname == 'SymmetricExtentDefinition':
            return True
        if classname == 'AngleExtentDefinition':
            return True
        return False

    def collectFrames(self):
        start = self.start - 1 # Zero index the start value.
        end = self.end
        width = self.width
        height = self.height
        filename = self.filename
        outputPath = self.outputPath
        # Colin Holloway | 2026-10-26: Create axis-labelled output folders with automatic run numbering.
        # Include the selected axis and avoid overwriting previous runs.
        axisLabel = self.rotationAxis if self.rotate else 'No_Rotation'
        folderName = 'History_Animation_{}_{}'.format(filename, axisLabel)
        outputFolder = os.path.join(outputPath, folderName)
        runNumber = 2
        while os.path.exists(outputFolder):
            outputFolder = os.path.join(outputPath, '{}_Run_{:02d}'.format(folderName, runNumber))
            runNumber += 1
        os.makedirs(outputFolder)
        saveObj = self.saveObj
        timeline = self.timeline
        documents = app.documents
        interpolationFrames = self.interpolationFrames
        framesPerRotation = self.framesPerRotation if self.rotate else 0
        finalFrames = self.finalFrames

        viewport = app.activeViewport
        # Colin Holloway | 2026-10-26: Snapshot supported camera properties for exact view restoration.
        # Save independent values: Fusion Camera does not implement copy().
        initialCamera = viewport.camera
        initialEye = (initialCamera.eye.x, initialCamera.eye.y, initialCamera.eye.z)
        initialTarget = (initialCamera.target.x, initialCamera.target.y, initialCamera.target.z)
        initialUp = (initialCamera.upVector.x, initialCamera.upVector.y, initialCamera.upVector.z)
        initialExtents = initialCamera.viewExtents
        initialCameraType = initialCamera.cameraType
        try:
            viewport.fit()
            camera = viewport.camera

            num = 0
            startingAngle = None

            for i in range(start, end):
                try:
                    # Get feature at current timeline index.
                    item = timeline.item(i)

                    # If item is suppressed, ignore.
                    if item.isSuppressed:
                        continue
                    # If item is group, ignore.
                    if item.isGroup:
                        continue
                    # # If item has an error, ignore.
                    # TODO: Move is throwing error here.
                    # if item.healthState == 2: # ErrorFeatureHealthState
                    #     continue

                    entity = item.entity
                    # TODO: Move TimelineObject is not working properly here.
                    if not entity:
                        continue
                    classname = type(entity).__name__

                    # Some operations should be ignored as they can't be easily animated.
                    # TODO: feature handling list is not exhaustive, just what I frequently use.
                    if classname == 'Occurrence':
                        continue
                        # # We only allow a fade in for Occurrence if this is the first item inserted into the design.
                        # if i > 0:
                        #     continue
                        # # And if insert operation not immediately folled by a joint.
                        # nextItem = type(timeline.item(i + 1).entity).__name__
                        # if nextItem == 'Joint':
                        #     continue
                    # If item is sketch, ignore.
                    if classname == 'Sketch':
                        continue
                    if classname == 'ConstructionPlane':
                        continue
                    if classname == 'ConstructionAxis':
                        continue
                    if classname == 'ConstructionPoint':
                        continue
                    if classname == 'ThreadFeature':
                        continue
                    if classname == 'Combine':
                        continue
                    # ui.messageBox(classname)
                except:
                    continue

                # Set marker position.
                timeline.markerPosition = i + 1

                # Get parameters to interpolate.
                interpolatedParameters = []
                stepSizes = []
                stepOffsets = []
                alphaComponents = []
                if classname == 'ExtrudeFeature':
                    if self.isNumericExtent(entity.extentOne):
                        param = entity.extentOne.distance
                        interpolatedParameters.append(param)
                        stepSizes.append(param.value / interpolationFrames)
                        stepOffsets.append(0)
                    # At the very least we can fade it in if it's a new body/component.
                    elif entity.operation == 3 or entity.operation == 4: # NewBodyFeatureOperation or NewComponentFeatureOperation.
                        bodies = entity.bodies
                        for body in bodies:
                            alphaComponents.append(body)
                    if entity.hasTwoExtents:
                        # Handle side 2.
                        if self.isNumericExtent(entity.extentTwo):
                            param = entity.extentTwo.distance
                            interpolatedParameters.append(param)
                            stepSizes.append(param.value / interpolationFrames)
                            stepOffsets.append(0)
                        # At the very least we can fade it in if it's a new body/component.
                        elif entity.operation == 3 or entity.operation == 4: # NewBodyFeatureOperation or NewComponentFeatureOperation.
                            bodies = entity.bodies
                            for body in bodies:
                                alphaComponents.append(body)
                # if classname == 'OffsetFacesFeature': # TODO: unable to get extent parameter from this operation.
                if classname == 'Move':
                    # TODO: implement this.
                    continue
                if classname == 'RevolveFeature':
                    if self.isNumericExtent(entity.extentDefinition):
                        param = entity.extentDefinition.angle
                        interpolatedParameters.append(param)
                        stepSizes.append(param.value / interpolationFrames)
                        # ui.messageBox(str(param.value / interpolationFrames))
                        stepOffsets.append(0)
                # if classname == 'FilletFeature' or classname == 'ChamferFeature': # TODO: unable to get extent parameter from this operation.
                if classname == 'Joint':
                    # This usually happens after occurrence, fade in the component.
                    # Need to break link first so that opacity changes aren't
                    # applied to all linked components - this is irreversible.
                    # TODO: If the occurrence is not the top level component of the linked component, this may throw an error.
                    if entity.occurrenceOne:
                        try:
                            if entity.occurrenceOne.isReferencedComponent:
                                entity.occurrenceOne.breakLink()
                        except:
                            pass
                        alphaComponents.append(entity.occurrenceOne.component)
                if classname == 'Occurrence':
                    try:
                        if entity.isReferencedComponent:
                            entity.breakLink()
                    except:
                        pass
                    alphaComponents.append(entity.component)
                if classname == 'RectangularPatternFeature':
                    if entity.quantityOne:
                        param = entity.quantityOne
                        if param.value != 1:
                            interpolatedParameters.append(param)
                            stepSize = int(param.value / interpolationFrames)
                            if stepSize < 1:
                                stepSize = 1
                            stepSizes.append(stepSize)
                            stepOffsets.append(0)
                            if entity.distanceOne:
                                dist = entity.distanceOne
                                interpolatedParameters.append(dist)
                                distStepSize = dist.value / (param.value - 1)
                                # ui.messageBox(str(distStepSize))
                                stepSizes.append(distStepSize * stepSize)
                                stepOffsets.append(-distStepSize)
                    if entity.quantityTwo:
                        param = entity.quantityTwo
                        if param.value != 1:
                            interpolatedParameters.append(param)
                            stepSize = int(param.value / interpolationFrames)
                            stepSizes.append(stepSize)
                            stepOffsets.append(0)
                            if entity.distanceTwo:
                                dist = entity.distanceTwo
                                interpolatedParameters.append(dist)
                                distStepSize = dist.value / (param.value - 1)
                                stepSizes.append(distStepSize * stepSize)
                                stepOffsets.append(-distStepSize)
                # Save original values and expressions.
                originalValues = [param.value for param in interpolatedParameters]
                originalExpressions = [param.expression for param in interpolatedParameters]
                originalAlphas = [comp.opacity for comp in alphaComponents]
                # Calc number of interpolation frames for this feature.
                _interpolationFrames = interpolationFrames if (i < end - 1) else (interpolationFrames + finalFrames)
                for j in range(_interpolationFrames):
                    # Interpolate parameters.
                    for k in range(len(interpolatedParameters)):
                        value = stepSizes[k] * (j + 1) + stepOffsets[k]
                        if abs(value) > abs(originalValues[k]):
                            value = originalValues[k]
                        # ui.messageBox(str(value))
                        interpolatedParameters[k].value = value
                        # Force a recompute (needed for symmetric Revolves for some reason?).
                        if classname == 'RevolveFeature':
                            entity.extentDefinition.isSymmetric = entity.extentDefinition.isSymmetric
                    for k in range(len(alphaComponents)):
                        value = originalAlphas[k] * (j + 1) / interpolationFrames
                        if abs(value) > abs(originalAlphas[k]):
                            value = originalAlphas[k]
                        # ui.messageBox(str(value))
                        alphaComponents[k].opacity = value

                    # Colin Holloway | 2026-10-26: Orbit around selected global axis and camera target.
                    # Orbit the camera around the selected global axis, through
                    # the camera target. Rotate the up vector as well so the
                    # camera orientation remains valid for X, Y and Z orbits.
                    if framesPerRotation > 0:
                        angle = 2.0 * math.pi / framesPerRotation
                        camera = viewport.camera
                        target = camera.target
                        eye = camera.eye
                        up = camera.upVector
                        axis = self.rotationAxis
                        c = math.cos(angle)
                        s = math.sin(angle)

                        def rotateVector(x, y, z):
                            # Rodrigues' formula for a principal Cartesian axis.
                            if axis == 'X':
                                return (x, y * c - z * s, y * s + z * c)
                            if axis == 'Y':
                                return (x * c + z * s, y, -x * s + z * c)
                            return (x * c - y * s, x * s + y * c, z)

                        dx, dy, dz = rotateVector(
                            eye.x - target.x, eye.y - target.y, eye.z - target.z)
                        ux, uy, uz = rotateVector(up.x, up.y, up.z)
                        camera.eye = adsk.core.Point3D.create(
                            target.x + dx, target.y + dy, target.z + dz)
                        camera.upVector = adsk.core.Vector3D.create(ux, uy, uz)
                        viewport.camera = camera

                    # Save image.
                    # Colin Holloway | 2026-10-26: Join image/OBJ paths safely without requiring a trailing slash.
                    outputFilename = os.path.join(outputFolder, filename + '_' + str(num))
                    success = app.activeViewport.saveAsImageFile(outputFilename + '.png', width, height)
                    if not success:
                        ui.messageBox('Failed saving viewport image.')
                
                    # Save obj file if requested
                    if saveObj:
                        success = self.saveObjFile(outputFilename + '.obj')
                        if not success:
                            ui.messageBox('Failed saving obj file.')

                    num += 1

                # Reset parameters.
                for k in range(len(interpolatedParameters)):
                    interpolatedParameters[k].value = originalValues[k]
                    interpolatedParameters[k].expression = originalExpressions[k]
                for k in range(len(alphaComponents)):
                    alphaComponents[k].opacity = originalAlphas[k]
        finally:
            # Colin Holloway | 2026-10-26: Restore original camera even if rendering fails.
            # Always restore the user's exact initial view, including when
            # rendering fails or the selected frame count is not a full orbit.
            restoredCamera = viewport.camera
            restoredCamera.eye = adsk.core.Point3D.create(*initialEye)
            restoredCamera.target = adsk.core.Point3D.create(*initialTarget)
            restoredCamera.upVector = adsk.core.Vector3D.create(*initialUp)
            restoredCamera.viewExtents = initialExtents
            restoredCamera.cameraType = initialCameraType
            viewport.camera = restoredCamera

    def saveObjFile(self, file):
        '''Export an .obj file from the root component'''
        try:
            adsk.doEvents()
            bodies = []
            comp = self.design.rootComponent
            for body in comp.bRepBodies:
                bodies.append(body)
            for occurrence in comp.allOccurrences:
                for body in occurrence.bRepBodies:
                    bodies.append(body)

            meshes = []
            for body in bodies:
                mesher = body.meshManager.createMeshCalculator()
                mesher.setQuality(
                    adsk.fusion.TriangleMeshQualityOptions.NormalQualityTriangleMesh
                )
                mesh = mesher.calculate()
                meshes.append(mesh)

            triangle_count = 0
            vert_count = 0
            for mesh in meshes:
                triangle_count += mesh.triangleCount
                vert_count += mesh.nodeCount

            # Write the mesh to OBJ
            with open(file, 'w') as fh:
                fh.write('# WaveFront *.obj file\n')
                fh.write(f'# Vertices: {vert_count}\n')
                fh.write(f'# Triangles : {triangle_count}\n\n')

                for mesh in meshes:
                    verts = mesh.nodeCoordinates
                    for pt in verts:
                        fh.write(f'v {pt.x} {pt.y} {pt.z}\n')
                for mesh in meshes:
                    for vec in mesh.normalVectors:
                        fh.write(f'vn {vec.x} {vec.y} {vec.z}\n')

                index_offset = 0
                for mesh in meshes:
                    mesh_tri_count = mesh.triangleCount
                    indices = mesh.nodeIndices
                    for t in range(mesh_tri_count):
                        i0 = indices[t * 3] + 1 + index_offset
                        i1 = indices[t * 3 + 1] + 1 + index_offset
                        i2 = indices[t * 3 + 2] + 1 + index_offset
                        fh.write(f'f {i0}//{i0} {i1}//{i1} {i2}//{i2}\n')
                    index_offset += mesh.nodeCount

                fh.write(f'\n# End of file')
                return True

        except Exception as ex:
            return False

def run(context):
    global timelapse
    try:
        ui.messageBox('WARNING: This script will make changes to your file (e.g. break links to referenced components).  You may want to run this on a copy of your design.  You can quit Fusion now to stop the script if you are unsure about continuing.')
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('Script is not supported in current workspace, please change to MODEL workspace and try again.')
            return
        # Colin Holloway | 2026-10-26: Expand collapsed timeline
        # groups before initializing the dialog so every feature gets a step.
        expandTimelineGroups(design.timeline)
        # Init a timelapse object.
        if timelapse == None:
            timelapse = HistoryTimelapse(design)

        commandDefinitions = ui.commandDefinitions
        # Check the command exists or not.
        cmdDef = commandDefinitions.itemById('designhistoryanimation')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('designhistoryanimation',
                    'Design History Animation',
                    'Turn your Fusion360 design history into an animation')

        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # Keep the handler referenced beyond this function.
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
        adsk.autoTerminate(False)

    except:
        # Colin Holloway | 2026-10-26: Undo group expansion if
        # command setup fails before the destroy event can restore the groups.
        try:
            restoreTimelineGroups()
        except:
            pass
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
