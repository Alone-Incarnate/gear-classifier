import os
import platform
import sys
from mvIMPACT import acquire
from mvIMPACT.Common import exampleHelper
from PIL import Image
import numpy as np

def capture_and_save_images(output_dir="captured_images"):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize device manager
    devMgr = acquire.DeviceManager()
    pDev = exampleHelper.getDeviceFromUserInput(devMgr)
    if pDev is None:
        exampleHelper.requestENTERFromUser()
        sys.exit(-1)
    pDev.open()

    # Get number of frames to capture
    print("Please enter the number of buffers to capture followed by [ENTER]: ", end='')
    framesToCapture = exampleHelper.getNumberFromUser()
    if framesToCapture < 1:
        print("Invalid input! Please capture at least one image")
        sys.exit(-1)

    # Check if mvDisplay is available (Windows-only)
    isDisplayModuleAvailable = platform.system() == "Windows"
    if isDisplayModuleAvailable:
        display = acquire.ImageDisplayWindow("A window created from Python")
    else:
        print("The display library is not available on this('" + platform.system() + "') system. Saving images instead.")

    # Initialize function interface and statistics
    fi = acquire.FunctionInterface(pDev)
    statistics = acquire.Statistics(pDev)

    # Queue initial image requests
    while fi.imageRequestSingle() == acquire.DMR_NO_ERROR:
        print("Buffer queued")

    pPreviousRequest = None
    exampleHelper.manuallyStartAcquisitionIfNeeded(pDev, fi)

    try:
        for i in range(framesToCapture):
            requestNr = fi.imageRequestWaitFor(10000)
            if fi.isRequestNrValid(requestNr):
                pRequest = fi.getRequest(requestNr)
                if pRequest.isOK:
                    # Print statistics every 100 frames
                    if i % 100 == 0:
                        print("Info from " + pDev.serial.read() +
                              ": " + statistics.framesPerSecond.name() + ": " + statistics.framesPerSecond.readS() +
                              ", " + statistics.errorCount.name() + ": " + statistics.errorCount.readS() +
                              ", " + statistics.captureTime_s.name() + ": " + statistics.captureTime_s.readS())

                    # Display image if available
                    if isDisplayModuleAvailable:
                        display.GetImageDisplay().SetImage(pRequest)
                        display.GetImageDisplay().Update()

                    # Save image using PIL and numpy
                    try:
                        # Get image properties
                        image_buffer = pRequest.imageData  # Direct property access
                        width = pRequest.imageWidth
                        height = pRequest.imageHeight
                        channel_count = pRequest.imageChannelCount
                        channel_bit_depth = pRequest.imageChannelBitDepth
                        pixel_format = pRequest.imagePixelFormat

                        # Determine data type based on bit depth
                        channel_type = np.uint16 if channel_bit_depth > 8 else np.uint8

                        # Convert buffer to numpy array
                        if channel_count == 1:
                            arr = np.frombuffer(image_buffer, dtype=channel_type).reshape(height, width)
                        else:
                            arr = np.frombuffer(image_buffer, dtype=channel_type).reshape(height, width, channel_count)

                        # Create PIL image
                        if channel_count == 1:
                            img = Image.fromarray(arr, mode='L')  # Grayscale
                        else:
                            mode = 'RGB' if channel_count == 3 else 'RGBA'
                            img = Image.fromarray(arr, mode=mode)

                        # Save image
                        output_path = os.path.join(output_dir, f"image_{i:04d}.png")
                        img.save(output_path)
                        print(f"Saved image {i} to {output_path}")

                    except Exception as e:
                        print(f"Error processing image {i}: {e}")

                    # Unlock previous request and queue new one
                    if pPreviousRequest is not None:
                        pPreviousRequest.unlock()
                    pPreviousRequest = pRequest
                    fi.imageRequestSingle()
                else:
                    print(f"Request {requestNr} failed")
            else:
                print("imageRequestWaitFor failed (" + str(requestNr) + ", " +
                      acquire.ImpactAcquireException.getErrorCodeAsString(requestNr) + ")")

    finally:
        # Stop acquisition and clean up
        exampleHelper.manuallyStopAcquisitionIfNeeded(pDev, fi)
        if pPreviousRequest is not None:
            pPreviousRequest.unlock()
        exampleHelper.requestENTERFromUser()

if __name__ == "__main__":
    capture_and_save_images()
