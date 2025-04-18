# Example application for mvIMPACT Acquire in Python
# Copyright (C) 2005 - 2024 Balluff GmbH
# Authors: APIs and drivers development team at Balluff GmbH
# Initial date: 2005-05-04
# License: MIT License (see original C++ code for details)

import sys
import cv2
import numpy as np
from mvIMPACT import acquire

def get_device_from_user_input(dev_mgr):
    """Prompt user to select a device from the device manager."""
    if dev_mgr.deviceCount() == 0:
        print("No devices found!")
        return None
    print("Available devices:")
    for i in range(dev_mgr.deviceCount()):
        dev = dev_mgr.getDevice(i)
        print(f"{i}: {dev.serial}, {dev.product}")
    try:
        idx = int(input("Select device index: "))
        if 0 <= idx < dev_mgr.deviceCount():
            return dev_mgr.getDevice(idx)
        else:
            print("Invalid index!")
            return None
    except ValueError:
        print("Invalid input!")
        return None

def main():
    # Initialize DeviceManager
    dev_mgr = acquire.DeviceManager()
    
    # Get device from user input
    p_dev = get_device_from_user_input(dev_mgr)
    if not p_dev:
        print("Unable to continue! Press Enter to exit.")
        input()
        return 1

    try:
        # Open the device
        p_dev.open()
    except acquire.ImpactAcquireException as e:
        print(f"An error occurred while opening the device (error code: {e.getErrorCode()}).")
        print("Press Enter to exit.")
        input()
        return 1

    # Create FunctionInterface
    fi = acquire.FunctionInterface(p_dev)

    # Send a single image request
    fi.imageRequestSingle()

    # Start acquisition if needed (simplified, assuming device is ready)
    # Note: Manually starting/stopping acquisition may depend on device settings
    fi.imageRequestWaitFor(10000)  # Wait for request to be processed

    # Wait for the image (timeout: 10 seconds)
    request_nr = fi.imageRequestWaitFor(10000)

    # Check if the request is valid
    if not fi.isRequestNrValid(request_nr):
        print("imageRequestWaitFor failed, maybe the timeout value is too small?")
        return 1

    # Get the request object
    p_request = fi.getRequest(request_nr)
    
    if p_request.isOK():
        # Get image buffer
        payload_type = p_request.payloadType.read()
        if payload_type == acquire.pt2DImage:
            image_buffer = p_request.getImageBufferDesc().getBuffer()
            # Convert to numpy array for OpenCV
            img_data = np.frombuffer(image_buffer.vpData, dtype=np.uint8)
            img_data = img_data.reshape(image_buffer.iHeight, image_buffer.iWidth, -1)

            # Display or log the image
            print(f"Image captured ({p_request.imagePixelFormat.readS()}, {image_buffer.iWidth}x{image_buffer.iHeight})")
            
            # Display using OpenCV
            cv2.imshow("mvIMPACT_acquire sample", img_data)
            cv2.waitKey(0)  # Wait for key press
            cv2.destroyAllWindows()
        else:
            print(f"Unsupported payload type: {payload_type}")
    else:
        print(f"Error: {p_request.requestResult.readS()}")
        return 1

    # Unlock the request
    fi.imageRequestUnlock(request_nr)

    print("Press Enter to exit.")
    input()
    return 0

if __name__ == "__main__":
    sys.exit(main())
