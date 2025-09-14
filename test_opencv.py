import cv2
print(f"OpenCV version: {cv2.__version__}")

try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    print("✅ cv2.face module working!")
except AttributeError as e:
    print(f"❌ Error: {e}")
