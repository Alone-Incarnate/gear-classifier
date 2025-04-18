import os
from mvIMPACT import acquire
from PIL import Image
import numpy as np

def capture_single_image(output_path="captured_image.png"):
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize device manager
    dev_mgr = acquire.DeviceManager()
    dev_mgr.updateDeviceList()

    # Check for available devices
    if dev_mgr.deviceCount() == 0:
        print("No camera found")
        return False

    # Open the first device
    dev = dev_mgr.getDevice(0)
    try:
        dev.open()
        print(f"Using device: {dev.serial.read()}")

        # Initialize function interface
        fi = acquire.FunctionInterface(dev)

        # Start acquisition
        fi.acquisitionStart()
        print("Acquisition started")

        # Request a single image
        request_nr = fi.imageRequestSingle()
        if request_nr != acquire.DMR_NO_ERROR:
            print("Failed to queue image request")
            return False

        # Wait for the image (timeout: 10 seconds)
        request_nr = fi.imageRequestWaitFor(10000)
        if fi.isRequestNrValid(request_nr):
            request = fi.getRequest(request_nr)
            if request.isOK:
                try:
                    # Get image properties
                    image_buffer = request.imageData  # Property, not method
                    width = request.imageWidth
                    height = request.imageHeight
                    channel_count = request.imageChannelCount.read()  # Use .read() for PropertyI
                    channel_bit_depth = request.imageChannelBitDepth.read()  # Use .read() for PropertyI
                    pixel_format = request.imagePixelFormat

                    # Debug: Print property types and pixel format
                    print(f"Pixel format: {pixel_format}")
                    print(f"Channel count: {channel_count}, type: {type(channel_count)}")
                    print(f"Channel bit depth: {channel_bit_depth}, type: {type(channel_bit_depth)}")

                    # Determine data type
                    channel_type = np.uint16 if channel_bit_depth > 8 else np.uint8

                    # Convert buffer to numpy array
                    if channel_count == 1:
                        arr = np.frombuffer(image_buffer, dtype=channel_type).reshape(height, width)
                        mode = 'L'  # Grayscale
                    else:
                        arr = np.frombuffer(image_buffer, dtype=channel_type).reshape(height, width, channel_count)
                        mode = 'RGB' if channel_count == 3 else 'RGBA'

                    # Create and save PIL image
                    img = Image.fromarray(arr, mode=mode)
                    img.save(output_path)
                    print(f"Image saved to {output_path}")

                    # Unlock request
                    request.unlock()
                    return True
                except Exception as e:
                    print(f"Error processing image: {e}")
                    return False
            else:
                print("Image capture failed")
                return False
        else:
            print(f"imageRequestWaitFor failed: {request_nr}, {acquire.ImpactAcquireException.getErrorCodeAsString(request_nr)}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

    finally:
        # Stop acquisition and close device
        fi.acquisitionStop()
        print("Acquisition stopped")
        dev.close()

if __name__ == "__main__":
    capture_single_image("captured_image.png")
