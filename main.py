from mvIMPACTAcquire import DeviceManager, FunctionInterface
from PIL import Image
import numpy as np

def capture_and_save_image(output_path="captured_image.png"):
    # Initialize device manager
    devMgr = DeviceManager()
    try:
        devMgr.updateDeviceList()
        if devMgr.deviceCount() == 0:
            print("No camera found")
            return False

        # Get the first device
        pDev = devMgr.getDevice(0)
        print(f"Using device: {pDev.serial}")

        # Initialize function interface
        fi = FunctionInterface(pDev)

        # Start acquisition
        fi.acquisitionStart()
        print("Acquisition started")

        # Request a single image
        requestNr = fi.imageRequestSingle()
        timeout_ms = 1000  # Wait up to 1 second
        fi.imageRequestWaitFor(requestNr, timeout_ms)

        # Check if the image was captured successfully
        pRequest = fi.getRequest(requestNr)
        if pRequest.isOK():
            # Get image data
            image_buffer = pRequest.imageData()
            width = pRequest.imageWidth()
            height = pRequest.imageHeight()
            pixel_format = pRequest.imagePixelFormat()

            # Convert to numpy array (assuming RGB or mono format)
            if pixel_format == "Mono8":
                image_array = np.frombuffer(image_buffer, dtype=np.uint8).reshape(height, width)
            elif pixel_format == "RGB8":
                image_array = np.frombuffer(image_buffer, dtype=np.uint8).reshape(height, width, 3)
            else:
                print(f"Unsupported pixel format: {pixel_format}")
                return False

            # Convert to PIL Image and save
            image = Image.fromarray(image_array)
            image.save(output_path)
            print(f"Image saved to {output_path}")
            return True
        else:
            print("Failed to capture image")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

    finally:
        # Stop acquisition and clean up
        fi.acquisitionStop()
        print("Acquisition stopped")

if __name__ == "__main__":
    capture_and_save_image("captured_image.png")
