import numpy as np
import cv2
import streamlit as st
import requests
from PIL import Image
import json
from typing import List

st.title('Wrist Virtual Try On')

# Initialize session state if not already done
if "bracelet_selected" not in st.session_state:
    st.session_state.bracelet_selected = False

bracelets = {
    "Bracelet 1": "bracelets/BFCL013D2C.png",
    "Bracelet 2": "bracelets/BFSV014D2C.png",
    "Bracelet 3": "bracelets/BFSV015D2C.png",
    "Bracelet 4": "bracelets/HalfProduct.png"
}

if not st.session_state.bracelet_selected:
    # Display bracelet images with "Try On" buttons
    for name, image_path in bracelets.items():
        object = Image.open(image_path).convert("RGBA")
        st.image(object, caption=name, width = 200)
        
        if st.button(f"Try On {name}"):
            st.session_state.bracelet_selected = True
            st.session_state.selected_bracelet = name
            st.session_state.object = object
            break  # Exit the loop after a bracelet is selected

else:
    # Capture Wrist Image and Overlay Selected Bracelet
    object = st.session_state.object
    
    # Display selected bracelet
    st.image(object, caption = "Selected Bracelet", width = 200)

    # Streamlit widget to capture an image using the webcam
    camera_image = st.camera_input("Capture an image of the wrist")

    if camera_image is not None:
        with open("temp_image_cam.jpg", "wb") as f:
            f.write(camera_image.getbuffer())

        import requests

        url = "https://fsvirtualnode.clouddeploy.in/coordinates"

        payload = {}
        files=[
            ('image',('temp_image_cam.jpg',open('temp_image_cam.jpg','rb'),'image/jpeg'))
        ]
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload, files=files)


        results = response.text

        # Load and display the uploaded image
        img = cv2.imdecode(np.frombuffer(camera_image.getbuffer(), np.uint8), cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        my_img = img.copy()

        # Print the response for debugging
        print("API Response:", results)

        # Attempt to parse the JSON response
        try:
            data = json.loads(results)
            # Check if 'results' key exists
            if 'results' not in data:
                st.error("API response does not contain 'results' key.")
            else:
                wrist_data = data["results"]["wrist"]
                # Further processing...
        except json.JSONDecodeError:
            st.error("Failed to decode JSON from the API response.")
            
        # Load and display the captured image
        st.image(img, width=200)

        data = json.loads(results)

        wrist_data = data["results"]["wrist"]

        # Separating out the coordinates
        left_coords: List[float] = wrist_data["left"]
        right_coords: List[float] = wrist_data["right"]
        center_coords: List[float] = wrist_data["center"]
        rotation_angle: float = wrist_data["rotation_angle"]
        polygon_coords: List[List[float]] = wrist_data["polygon"]

        # # Print the separated coordinates
        # st.write("Left coordinates:", left_coords)
        # st.write("Right coordinates:", right_coords)
        # st.write("Center coordinates:", center_coords)
        # st.write("Rotation Angle:", rotation_angle)
        # st.write("Polygon coordinates:", polygon_coords)

        # Calculating ceneter coordinate using left and right coordinates
        center_coords_rev: List[float] = [(left_coords[0] + right_coords[0]) / 2, (left_coords[1] + right_coords[1]) / 2]

        # st.write('Revised Center Coordinates:', center_coords_rev)

        img_height, img_width = img.shape[:2]
        left_pixel = (int(left_coords[0] * img_width), int(left_coords[1] * img_height))
        right_pixel = (int(right_coords[0] * img_width), int(right_coords[1] * img_height))
        center_pixel = (int(center_coords_rev[0] * img_width), int(center_coords_rev[1] * img_height))
        angle = int(rotation_angle)

        # Draw circles at the coordinates
        cv2.circle(img, left_pixel, 5, (0, 0, 255), -1)  
        cv2.circle(img, center_pixel, 5, (0, 0, 255), -1)
        cv2.circle(img, right_pixel, 5, (0, 0, 255), -1)  

        # # Display the image in Streamlit
        # st.image(img, caption = 'Wrist with Coordinates', use_column_width = True)

        polygon_pixels = [(int(coord[0] * img_width / 100), int(coord[1] * img_height / 100)) for coord in polygon_coords]

        cv2.polylines(img, [np.array(polygon_pixels)], isClosed = True, color=(0, 255, 0), thickness = 2)


        st.image(img, caption = 'Wrist with coordinates and polygon', use_column_width = True)

        # Calculate wrist length in pixels
        wrist_length = np.sqrt((right_pixel[0] - left_pixel[0])**2 + (right_pixel[1] - left_pixel[1])**2)

        # Resize the bracelet image to match wrist length
        object_np = np.array(object)

        bracelet_width = object_np.shape[1]
        resize_factor = wrist_length / bracelet_width
        new_width = int(bracelet_width * resize_factor)
        new_height = int(object_np.shape[0] * resize_factor)
        object_resized = cv2.resize(object_np, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

        # Rotate the resized bracelet to align with wrist angle
        st.write('Wrist rotation angle:', rotation_angle)
        if 0 <= rotation_angle < 60:
            angle = 90 - rotation_angle
        elif 60 <= rotation_angle < 120:
            angle = 180 - rotation_angle
        elif 120 <= rotation_angle <= 180:
            angle = 270 - rotation_angle
        st.write('Rotation matrix angle:', angle)
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
