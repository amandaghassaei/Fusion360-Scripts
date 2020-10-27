# Fusion360-Design-History-Animation
A script to turn your Fusion360 design history into an animation.  When run, this script rolls your Design history timeline back to the beginning and saves out screnshots as it steps through each operation in your design.  For many operations (e.g. Extrudes, Revolves), it create a smooth animation by interpolating the operation across a range of values.  You can optionally add spin to the animation and change various other parameters via a small panel:



WARNING - THIS SCRIPT WILL MAKE CHANGES TO YOUR DESIGN FILE.  I recommended running this script on the copy of your design so that you don't accidently modify your file.  At the very least, do not save the changes to your file - they involve unlinking references to external components and are purely for better control over the animation transitions - you probably do not want these changes.

## Installation

## Development

Pull resquests welcome!  This is a quick script I wrote for myself, and while it does a decent job at animating the most common Fusion360 operations, there is room for improvement.  Some of this is due to time constraints on my end, others may be limitations of the Fusion API.  Some examples of features I'd like to add:

- **Animating Extrude with Extent "To Object" or "All"**: Since I'm not able to get a distance parameter from this operation, it is difficult to animate.  For now, if the extrude operation creates a new body or component, I have it set to fade that component in.
- **Move**: This operation is throwing an error in the current implementation and is ignored completly.  See TODO comment in code for more details.
- **FilletFeature / ChamferFeature / OffsetFacesFeature**: I'm unable to figure out how to extract the extent parameter for these operations.
- **More robust handling of Joints** Currently this code assumes that when users add a new component to an assembly, they immediately add a joint to it and move into into the correct position.  Because of this, the code ignores "Occurrence" operations - where the part is initially placed in the assembly, and instead fades in the object at occurenceOne of the following Joint operation.  This is typically how I set up my files, but I'm sure a more robust approach could be established.  One case where I'm still having trouble is when the Joint's occcurrenceOne is not the top-level component of the the new added assembly - see TODO note in Joint handler for more details.
