import os
import sys
from mvIMPACT import acquire
from mvIMPACT.Common import exampleHelper

# Try importing PIL and numpy for image display
try:
    import ctypes
    import numpy
    from PIL import Image
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install Pillow and numpy using:")
    print("  pip install Pillow numpy")
    sys.exit(-1)

# Initialize Device Manager
devMgr = acquire.DeviceManager()
pDev = exampleHelper.getDeviceFromUserInput(devMgr)

if pDev is None:
    print("No device selected.")
    exampleHelper.requestENTERFromUser()
    sys.exit(-1)

try:
    # Open the device
    pDev.open()
except acquire.ImpactAcquireException as e:
    print(f"Failed to open device: {e}")
    exampleHelper.requestENTERFromUser()
    sys.exit(-1)

# Get number of frames to capture
print("Please enter the number of buffers to capture followed by [ENTER]: ", end='')
framesToCapture = exampleHelper.getNumberFromUser()
if framesToCapture < 1:
    print("Invalid input! Please capture at least one image.")
    pDev.close()
    sys.exit(-1)

# Initialize Function Interface and Statistics
fi = acquire.FunctionInterface(pDev)
statistics = acquire.Statistics(pDev)

# Queue initial requests (limit to avoid overflow)
maxRequests = min(framesToCapture, 10)  # Arbitrary limit to prevent over-queuing
for _ in range(maxRequests):
    if fi.imageRequestSingle() != acquire.DMR_NO_ERROR:
        print("Failed to queue buffer.")
        break
    print("Buffer queued")

pPreviousRequest = None
exampleHelper.manuallyStartAcquisitionIfNeeded(pDev, fi)

# Capture loop
for i in range(framesToCapture):
    requestNr = fi.imageRequestWaitFor(10000)  # 10-second timeout
    if fi.isRequestNrValid(requestNr):
        pRequest = fi.getRequest(requestNr)
        if pRequest.isOK:
            if i % 100 == 0:
                print(f"Info from {pDev.serial.read()}: "
                      f"{statistics.framesPerSecond.name()}: {str(statistics.framesPerSecond.read())} "
                      f"{statistics.errorCount.name()}: {str(statistics.errorCount.read())} "
                      f"{statistics.captureTime_s.name()}: {str(statistics.captureTime_s.read())}")

            # Convert image data to numpy array for display
            try:
                cbuf = (ctypes.c_char * pRequest.imageSize.read()).from_address(int(pRequest.imageData.read()))
                channelType = numpy.uint16 if pRequest.imageChannelBitDepth.read() > 8 else numpy.uint8
                arr = numpy.frombuffer(cbuf, dtype=channelType)
                arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read(), pRequest.imageChannelCount.read())
                
                if pRequest.imageChannelCount.read() == 1:
                    img = Image.fromarray(arr, mode='L')  # Grayscale
                else:
                    img = Image.fromarray(arr, mode='RGB')  # RGB
                img.show()  # Display image (may open default viewer)
                # Optionally save image: img.save(f"capture_{i}.png")
            except Exception as e:
                print(f"Failed to display image: {e}")

            # Unlock previous request
            if pPreviousRequest is not None:
                pPreviousRequest.unlock()
            pPreviousRequest = pRequest

            # Queue next request
            fi.imageRequestSingle()
        else:
            print(f"Request {requestNr} is not OK.")
            pRequest.unlock()
    else:
        print(f"imageRequestWaitFor failed ({requestNr}, {acquire.ImpactAcquireException.getErrorCodeAsString(requestNr)})")
        print("Possible reasons: Timeout, slow system, or device not triggered. Consider increasing timeout or checking trigger settings.")

# Stop acquisition and clean up
exampleHelper.manuallyStopAcquisitionIfNeeded(pDev, fi)
if pPreviousRequest is not None:
    pPreviousRequest.unlock()
pDev.close()

# Wait for user input before exiting
exampleHelper.requestENTERFromUser()
