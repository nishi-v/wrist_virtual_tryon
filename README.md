Wrist Virtual Try-On

Overview

The "Wrist Virtual Try-On" app allows users to see how different bracelets will look on their wrist. Users can capture an image of their wrist using a webcam, and the app will overlay the selected bracelet onto the wrist image. The bracelet is resized and rotated to match the wrist's dimensions and angle.

Features

- Select a Bracelet: Choose from a variety of bracelets.
- Capture Wrist Image: Use your webcam to take a photo of your wrist.
- Overlay Bracelet: The app resizes and rotates the bracelet to fit the wrist in the captured image.
- Visualize Results: View the bracelet overlay in the app.

Setup

To set up and run this app locally, follow these steps:

1. Clone the Repository

   git clone <your-repository-url>
   cd <repository-directory>

2. Create a Virtual Environment (Optional but recommended)

   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. Install Dependencies

   Install the required Python packages using `requirements.txt`.

   pip install -r requirements.txt

4. Run the App

   Start the Streamlit app.

   streamlit run app.py

   Replace `app.py` with the name of your Streamlit script if it differs.

Usage

1. Select a Bracelet:
   - The app will display images of available bracelets. Click the "Try On" button for the bracelet you want to see on your wrist.

2. Capture Wrist Image:
   - Use the "Capture an image of the wrist" button to take a photo of your wrist with the webcam.

3. View the Result:
   - The app will process the wrist image, overlay the selected bracelet, and display the result.

File Structure

- app.py: Main Streamlit application script.
- requirements.txt: Lists the Python packages required for the app.
- bracelets/: Directory containing images of bracelets to try on.

Dependencies

Ensure the following packages are included in your `requirements.txt` file:

- numpy
- opencv-python
- streamlit
- Pillow
- requests
