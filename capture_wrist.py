import numpy as np
import cv2
import streamlit as st
import requests
from PIL import Image
import json
from typing import List
import time
from dotenv import load_dotenv
import os
from pathlib import Path

# Get the current working directory
dir = Path(os.getcwd())

# Load environment variables from .env file
ENV_PATH = dir / '.env'
load_dotenv(ENV_PATH)

# Get API URL from environment variables
API_URL = os.environ["API_URL"]
BEARER_TOKEN = os.environ["BEARER_TOKEN"]

st.title('Wrist Virtual Try-On')

# Initialize session state if not already done
if "bracelet_selected" not in st.session_state:
    st.session_state.bracelet_selected = False

# Bracelet options
bracelets = {
    "Bracelet 1": "bracelets/BFCL013D2C.png",
    "Bracelet 2": "bracelets/BFSV014D2C.png",
    "Bracelet 3": "bracelets/BFSV015D2C.png",
    "Bracelet 4": "bracelets/HalfProduct.png",
    "Watch 1": "bracelets/watch1.png",
    "Watch 2": "bracelets/WFA015G1F.png",
    "Watch 3": "bracelets/WMA005S1F.png",
    "Watch 4": "bracelets/WMA006S1F.png"
}

if not st.session_state.bracelet_selected:
    # Display bracelet images with "Try On" buttons
    for name, image_path in bracelets.items():
        object_img = Image.open(image_path).convert("RGBA")
        st.image(object_img, caption=name, width=200)
        
        if st.button(f"Try On {name}"):
            st.session_state.bracelet_selected = True
            st.session_state.selected_bracelet = name
            st.session_state.object = object_img
            break  # Exit the loop after a bracelet is selected
else:
    # Display selected bracelet
    object_img = st.session_state.object
    st.image(object_img, caption="Selected Bracelet", width=200)

    # Provide options to either upload or capture an image
    option = st.radio("Choose Image Source", ("Capture Image", "Upload Image"))

    if option == "Capture Image":
        # Streamlit widget to capture an image using the webcam
        camera_image = st.camera_input("Capture an image of the wrist")
        if camera_image is not None:
            with open(dir / "temp_image_cam.jpg", "wb") as f:
                f.write(camera_image.getbuffer())
            img_path = str(dir / 'temp_image_cam.jpg')

    elif option == "Upload Image":
        # Streamlit widget to upload an image
        uploaded_image = st.file_uploader("Upload an image of the wrist", type=["jpg", "jpeg", "png"])
        if uploaded_image is not None:
            with open(dir / "temp_image.jpg", "wb") as f:
                f.write(uploaded_image.getbuffer())
            img_path = str(dir / 'temp_image.jpg')

    # Proceed if either a camera or uploaded image is available
    if (option == "Capture Image" and camera_image) or (option == "Upload Image" and uploaded_image):
        start = time.time()

        # API call to analyze the wrist image
        payload = {}
        files = [('image', (img_path, open(img_path, 'rb'), 'image/jpeg'))]
        headers = {
            'Authorization': f"Bearer {BEARER_TOKEN}"
        }

        response = requests.request("POST", API_URL, headers=headers, data=payload, files=files, verify=False)
        end = time.time() - start
        st.write(f"Time taken for API call: {end} seconds")

        # Parse API response
        results = response.text
        try:
            data = json.loads(results)  # Attempt to parse JSON
            wrist_data = data["results"]["wrist"]  # Assuming wrist data is in 'results'
        except json.JSONDecodeError:
            st.write("Error decoding JSON. Here's the response text:")
            st.write(results)  # Display raw response text
            st.error("Failed to decode JSON from the API response.")
            st.stop()
        except KeyError:
            st.write("Error: Expected data format is not present in the response.")
            st.write("Here's the response text:")
            st.write(results)  # Display raw response text
            st.error("Failed to find expected 'wrist' data in the API response.")
            st.stop()

        # Load and display the wrist image
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        my_img = img.copy()

        # Extract and process the wrist coordinates
        left_coords = wrist_data["left"]
        right_coords = wrist_data["right"]
        center_coords = wrist_data["center"]
        rotation_angle = wrist_data["rotation_angle"]
        polygon_coords = wrist_data["polygon"]

        # Calculate the center coordinate using left and right wrist points
        center_coords_rev = [(left_coords[0] + right_coords[0]) / 2, (left_coords[1] + right_coords[1]) / 2]

        # Convert wrist coordinates from percentage to pixel values
        img_height, img_width = img.shape[:2]
        left_pixel = (int(left_coords[0] * img_width), int(left_coords[1] * img_height))
        right_pixel = (int(right_coords[0] * img_width), int(right_coords[1] * img_height))
        center_pixel = (int(center_coords_rev[0] * img_width), int(center_coords_rev[1] * img_height))

        # Draw circles at the coordinates
        cv2.circle(img, left_pixel, 5, (0, 0, 255), -1)
        cv2.circle(img, center_pixel, 5, (0, 0, 255), -1)
        cv2.circle(img, right_pixel, 5, (0, 0, 255), -1)

        # Draw the wrist polygon
        polygon_pixels = [(int(coord[0] * img_width / 100), int(coord[1] * img_height / 100)) for coord in polygon_coords]
        cv2.polylines(img, [np.array(polygon_pixels)], isClosed=True, color=(0, 255, 0), thickness=2)

        # Display the image with coordinates and polygon
        st.image(img, caption='Wrist with coordinates and polygon', use_column_width=True)

        # Calculate wrist length in pixels
        wrist_length = np.sqrt((right_pixel[0] - left_pixel[0])**2 + (right_pixel[1] - left_pixel[1])**2)

        # Resize the bracelet image to match the wrist length
        object_np = np.array(object_img)
        bracelet_width = object_np.shape[1]
        resize_factor = wrist_length / bracelet_width
        new_width = int(bracelet_width * resize_factor)
        new_height = int(object_np.shape[0] * resize_factor)
        object_resized = cv2.resize(object_np, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

        # Rotate the resized bracelet to align with wrist angle
        st.write('Wrist rotation angle:', rotation_angle)
        angle = 270 - rotation_angle if 0 <= rotation_angle <= 90 else 90 - rotation_angle
        rotation_matrix = cv2.getRotationMatrix2D((new_width // 2, new_height // 2), angle, 1.0)
        object_rotated = cv2.warpAffine(object_resized, rotation_matrix, (new_width, new_height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

        # Convert the rotated bracelet back to PIL image for overlay
        object_rotated_pil = Image.fromarray(object_rotated, "RGBA")

        # Calculate the position to place the bracelet
        center_x = (left_pixel[0] + right_pixel[0]) // 2
        center_y = (left_pixel[1] + right_pixel[1]) // 2
        top_left_x = int(center_x - new_width // 2)
        top_left_y = int(center_y - new_height // 2)

        # Ensure the bracelet fits within the image bounds
        top_left_x = max(0, top_left_x)
        top_left_y = max(0, top_left_y)

        # Overlay the rotated bracelet on the wrist image
        object_rotated_cv = np.array(object_rotated_pil)
        result_img = img.copy()
        for i in range(new_height):
            for j in range(new_width):
                if object_rotated_cv[i, j][3] > 0:  # Check alpha channel
                    x = top_left_x + j
                    y = top_left_y + i
                    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
                        result_img[y, x] = object_rotated_cv[i, j][:3]  # Use RGB channels

        st.image(result_img, caption='Wrist with Bracelet Overlay', use_column_width=True)

        # Bracelet on wrist without polygon and coordinates
        my_result_img = my_img.copy()
        for i in range(new_height):
            for j in range(new_width):
                if object_rotated_cv[i, j][3] > 0:  # Check alpha channel
                    x = top_left_x + j
                    y = top_left_y + i
                    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
                        my_result_img[y, x] = object_rotated_cv[i, j][:3]  # Use RGB channels

        st.image(my_result_img, caption='Wrist with Bracelet Overlay without coordinates', use_column_width=True)
