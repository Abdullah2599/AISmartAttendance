import qrcode
import cv2
from pyzbar import pyzbar
import json
import os
from PIL import Image
import numpy as np
import streamlit as st
from datetime import datetime

class QRHandler:
    def __init__(self):
        self.qr_dir = "data/qr_codes"
        os.makedirs(self.qr_dir, exist_ok=True)
    
    def generate_student_qr(self, student_id, student_name):
        """Generate QR code for student photo upload"""
        try:
            # QR data for student photo upload
            qr_data = {
                'type': 'student_upload',
                'student_id': student_id,
                'name': student_name,
                'generated_at': datetime.now().isoformat()
            }
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            qr_filename = f"student_{student_id}_qr.png"
            qr_path = os.path.join(self.qr_dir, qr_filename)
            qr_image.save(qr_path)
            
            return qr_path
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None
    
    def scan_qr_code(self, image_file):
        """Scan QR code from uploaded image"""
        try:
            # Read image
            if hasattr(image_file, 'read'):
                image_bytes = image_file.read()
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = cv2.imread(image_file)
            
            if image is None:
                return None
            
            # Convert to grayscale for better QR detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Decode QR codes
            decoded_objects = pyzbar.decode(gray)
            
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                try:
                    parsed_data = json.loads(qr_data)
                    return parsed_data
                except json.JSONDecodeError:
                    # If not JSON, return as plain text
                    return {'type': 'text', 'data': qr_data}
            
            return None
            
        except Exception as e:
            print(f"Error scanning QR code: {e}")
            return None
    
    def process_student_photo(self, student_id, photo_file):
        """Process photo uploaded via QR code"""
        try:
            # Create temp directory for processing
            temp_dir = "data/temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save uploaded photo temporarily
            temp_path = os.path.join(temp_dir, f"temp_{student_id}.jpg")
            
            if hasattr(photo_file, 'read'):
                with open(temp_path, 'wb') as f:
                    f.write(photo_file.read())
            else:
                # If it's already a file path
                temp_path = photo_file
            
            # Process image (convert to grayscale, resize, etc.)
            image = cv2.imread(temp_path)
            if image is None:
                return False
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Extract largest face
                largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                x, y, w, h = largest_face
                face_region = gray[y:y+h, x:x+w]
                
                # Resize and save
                face_resized = cv2.resize(face_region, (100, 100))
                
                # Save processed face
                student_dir = f"data/students/{student_id}"
                os.makedirs(student_dir, exist_ok=True)
                
                face_path = os.path.join(student_dir, f"qr_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                cv2.imwrite(face_path, face_resized)
                
                # Clean up temp file
                if os.path.exists(temp_path) and "temp" in temp_path:
                    os.remove(temp_path)
                
                return True
            else:
                st.warning("No face detected in uploaded image")
                return False
                
        except Exception as e:
            print(f"Error processing student photo: {e}")
            return False
    
    def generate_attendance_qr(self, class_name, date):
        """Generate QR code for attendance marking"""
        try:
            qr_data = {
                'type': 'attendance',
                'class': class_name,
                'date': date,
                'generated_at': datetime.now().isoformat()
            }
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            qr_filename = f"attendance_{class_name}_{date}_qr.png"
            qr_path = os.path.join(self.qr_dir, qr_filename)
            qr_image.save(qr_path)
            
            return qr_path
            
        except Exception as e:
            print(f"Error generating attendance QR: {e}")
            return None
