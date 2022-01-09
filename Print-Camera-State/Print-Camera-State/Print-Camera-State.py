#Author-Amanda Ghassaei
#Description-Turn your Fusion360 version history into a timelapse animation

import adsk.core, traceback, json

app = adsk.core.Application.get()
ui  = app.userInterface
product = app.activeProduct
design = adsk.fusion.Design.cast(product)
units = design.unitsManager.defaultLengthUnits

def format(num):
    # Fusion default units are cm.
    if units == 'in':
        num /= 2.54
    if units == 'mm':
        num *= 10
    if units == 'm':
        num /= 100
    return str(round(num, 2))

def run(context):
    try:
        viewport = app.activeViewport
        camera = viewport.camera
        _units = 'cm'
        if units == 'in' or units == 'mm' or units == 'm':
            _units = units
        ln1 = "eye (" + _units + "):\t\t" + ", ".join(format(el) for el in [camera.eye.x, camera.eye.y, camera.eye.z]) + "\n"
        ln2 = "target (" + _units + "):\t\t" + ", ".join(format(el) for el in [camera.target.x, camera.target.y, camera.target.z]) + "\n"
        ln3 = "upVector (" + _units + "):\t\t" + ", ".join(format(el) for el in [camera.upVector.x, camera.upVector.y, camera.upVector.z]) + "\n"
        ln4 = "viewExtents (" + _units + "):\t" + format(camera.viewExtents)
        ui.messageBox(ln1 + ln2 + ln3 + ln4)

        # When the command is done, terminate the script.
        # This will release all globals which will remove all event handlers.
        adsk.terminate()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
