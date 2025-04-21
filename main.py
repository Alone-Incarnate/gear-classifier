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

            # Debug image properties
            width = pRequest.imageWidth.read()
            height = pRequest.imageHeight.read()
            channelCount = pRequest.imageChannelCount.read()
            bitDepth = pRequest.imageChannelBitDepth.read()
            imageSize = pRequest.imageSize.read()
            print(f"Image {i}: {width}x{height}, Channels: {channelCount}, Bit Depth: {bitDepth}, Size: {imageSize} bytes")

            # Convert image data to numpy array for display
            try:
                cbuf = (ctypes.c_char * imageSize).from_address(int(pRequest.imageData.read()))
                channelType = numpy.uint16 if bitDepth > 8 else numpy.uint8
                arr = numpy.frombuffer(cbuf, dtype=channelType)

                # Calculate expected shape
                if channelCount == 1:
                    # Grayscale
                    arr.shape = (height, width)
                    img = Image.fromarray(arr, mode='L')
                elif channelCount == 3:
                    # RGB
                    arr.shape = (height, width, 3)
                    img = Image.fromarray(arr, mode='RGB')
                else:
                    raise ValueError(f"Unsupported channel count: {channelCount}")

                img.show()  # Display image
                # Optionally save image: img.save(f"capture_{i}.png")
            except Exception as e:
                print(f"Failed to display image: {e}")
                print("Check camera format (e.g., Bayer, YUV) or bit depth settings.")

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
