import cv2
import numpy as np
import os
from PIL import Image
import pickle
from datetime import datetime

class FaceRecognizer:
    def __init__(self):
        # Face detection using Haar Cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Face recognition using LBPH (requires opencv-contrib-python)
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            print("✅ LBPH Face Recognizer initialized successfully")
        except AttributeError:
            print("❌ cv2.face module not found. Installing opencv-contrib-python...")
            print("Run: pip install opencv-contrib-python")
            # Fallback to basic recognition without LBPH
            self.recognizer = None
        
        self.known_faces = {}
        self.known_names = {}
        
    def detect_faces(self, image):
        """Detect faces in image using OpenCV Haar Cascade"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=4,
            minSize=(30, 30)
        )
        return faces, gray
    
    def process_student_images(self, student_id, student_name, image_file, roll_number=None):
        """Process student image and generate exactly 100 grayscale variations"""
        try:
            # Use provided roll number or fallback to student_id
            if not roll_number:
                roll_number = student_id[:8]  # Use first 8 chars of ID as roll number fallback
            
            # Face similarity check is now done in main.py before calling this function
            # This prevents partial registration
            
            # Create student directory
            student_dir = f"data/students/{roll_number}_{student_name.replace(' ', '_')}"
            os.makedirs(student_dir, exist_ok=True)
            
            image_paths = []
            total_variations_needed = 100
            
            # Read image from Streamlit uploaded file
            if hasattr(image_file, 'read'):
                # Reset file pointer to beginning
                image_file.seek(0)
                image_bytes = image_file.read()
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = cv2.imread(str(image_file))
            
            if image is None:
                print("Error: Could not read image")
                return False
            
            # Detect face in original image
            faces, gray = self.detect_faces(image)
            
            if len(faces) == 0:
                print("Error: No face detected in image")
                return False
            
            # Take the largest face
            largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = largest_face
            
            # Extract face region
            face_gray = gray[y:y+h, x:x+w]
            
            # Generate 100 variations
            for i in range(total_variations_needed):
                if i == 0:
                    # Original grayscale
                    processed_face = face_gray.copy()
                else:
                    # Create variations
                    processed_face = self.create_face_variation(face_gray, i)
                
                # Resize to standard size (100x100)
                processed_face = cv2.resize(processed_face, (100, 100))
                
                # Save image
                image_path = os.path.join(student_dir, f"face_{i:03d}.jpg")
                cv2.imwrite(image_path, processed_face)
                image_paths.append(image_path)
            
            # Update student data with image paths
            self.update_student_image_paths(student_id, image_paths)
            
            print(f"Generated {len(image_paths)} grayscale face images for {student_name}")
            return True
            
        except Exception as e:
            print(f"Error processing images: {e}")
            return False
    
    def update_student_image_paths(self, student_id, image_paths):
        """Update student record with image paths"""
        try:
            # This would need to be implemented with database manager
            # For now, we'll handle this in the main registration flow
            pass
        except Exception as e:
            print(f"Error updating student image paths: {e}")
    
    def check_face_similarity(self, new_image_file):
        """Check if the new face is similar to any existing registered faces - comprehensive check"""
        try:
            # Read the new image
            if hasattr(new_image_file, 'read'):
                new_image_file.seek(0)
                image_bytes = new_image_file.read()
                nparr = np.frombuffer(image_bytes, np.uint8)
                new_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                new_image = cv2.imread(str(new_image_file))
            
            if new_image is None:
                print("❌ Could not read uploaded image")
                return False
            
            # Detect face in new image
            new_faces, new_gray = self.detect_faces(new_image)
            if len(new_faces) == 0:
                print("❌ No face detected in uploaded image")
                return False
            
            # Get the largest face from new image
            largest_new_face = max(new_faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = largest_new_face
            new_face_region = new_gray[y:y+h, x:x+w]
            new_face_resized = cv2.resize(new_face_region, (100, 100))
            
            # Check against existing student images
            students_dir = "data/students"
            if not os.path.exists(students_dir):
                return False
            
            # Balanced threshold for accurate detection
            similarity_threshold = 0.65  # Balanced detection - not too sensitive
            max_similarity = 0.0
            matched_student = ""
            
            print(f"🔍 Checking face against existing students...")
            
            for student_folder in os.listdir(students_dir):
                student_path = os.path.join(students_dir, student_folder)
                if os.path.isdir(student_path):
                    print(f"   Checking against: {student_folder}")
                    
                    # Check MORE images from each student for thorough comparison
                    for i in range(min(20, 100)):  # Check first 20 images instead of 5
                        image_path = os.path.join(student_path, f"face_{i:03d}.jpg")
                        if os.path.exists(image_path):
                            existing_face = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                            if existing_face is not None:
                                # Resize existing face to match new face size
                                existing_face_resized = cv2.resize(existing_face, (100, 100))
                                
                                # Multiple comparison methods for better accuracy
                                
                                # Method 1: Template Matching
                                result = cv2.matchTemplate(new_face_resized, existing_face_resized, cv2.TM_CCOEFF_NORMED)
                                template_similarity = cv2.minMaxLoc(result)[1]
                                
                                # Method 2: Histogram Comparison
                                hist1 = cv2.calcHist([new_face_resized], [0], None, [256], [0, 256])
                                hist2 = cv2.calcHist([existing_face_resized], [0], None, [256], [0, 256])
                                hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                                
                                # Method 3: Structural Similarity (SSIM approximation)
                                # Convert to float for calculation
                                img1_float = new_face_resized.astype(np.float64)
                                img2_float = existing_face_resized.astype(np.float64)
                                
                                # Calculate mean squared error
                                mse = np.mean((img1_float - img2_float) ** 2)
                                if mse == 0:
                                    structural_similarity = 1.0
                                else:
                                    structural_similarity = 1.0 / (1.0 + mse / 10000.0)
                                
                                # Combined similarity score (weighted average)
                                combined_similarity = (
                                    template_similarity * 0.5 + 
                                    hist_similarity * 0.3 + 
                                    structural_similarity * 0.2
                                )
                                
                                if combined_similarity > max_similarity:
                                    max_similarity = combined_similarity
                                    matched_student = student_folder
                                
                                # Check if any method shows high similarity
                                if (template_similarity > similarity_threshold or 
                                    hist_similarity > similarity_threshold or 
                                    structural_similarity > similarity_threshold or
                                    combined_similarity > similarity_threshold):
                                    
                                    print(f"🚨 FACE MATCH DETECTED!")
                                    print(f"   Student: {student_folder}")
                                    print(f"   Template: {template_similarity:.3f}")
                                    print(f"   Histogram: {hist_similarity:.3f}")
                                    print(f"   Structural: {structural_similarity:.3f}")
                                    print(f"   Combined: {combined_similarity:.3f}")
                                    return True
                                
                                # Also check individual scores for debugging
                                if i < 3:  # Only show first 3 images for cleaner output
                                    print(f"     Image {i}: T={template_similarity:.3f}, H={hist_similarity:.3f}, S={structural_similarity:.3f}, C={combined_similarity:.3f}")
            
            print(f"🔍 Final Check - Max similarity: {max_similarity:.3f} with {matched_student}")
            
            # Final threshold check - if max similarity is above 0.55, block registration
            if max_similarity > 0.55:
                print(f"🚨 BLOCKING REGISTRATION - Similarity {max_similarity:.3f} too high!")
                print(f"   Matched with: {matched_student}")
                return True
            
            print(f"✅ No matching face found. Registration allowed.")
            return False
            
        except Exception as e:
            print(f"Error checking face similarity: {e}")
            return False
    
    def create_face_variation(self, face_gray, variation_num):
        """Create variations of face image for better training"""
        try:
            # More variation types for better diversity
            variation_type = variation_num % 10
            
            if variation_type == 0:
                # Brightness adjustment
                brightness = np.random.randint(-40, 40)
                brightness_matrix = np.ones(face_gray.shape, dtype=np.int16) * brightness
                face_variation = np.clip(face_gray.astype(np.int16) + brightness_matrix, 0, 255).astype(np.uint8)
            
            elif variation_type == 1:
                # Gaussian noise
                noise = np.random.normal(0, 15, face_gray.shape).astype(np.int16)
                face_variation = np.clip(face_gray.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            elif variation_type == 2:
                # Slight rotation
                angle = np.random.uniform(-15, 15)
                rows, cols = face_gray.shape
                M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
                face_variation = cv2.warpAffine(face_gray, M, (cols, rows))
            
            elif variation_type == 3:
                # Histogram equalization
                face_variation = cv2.equalizeHist(face_gray)
            
            elif variation_type == 4:
                # Gaussian blur
                kernel_size = np.random.choice([3, 5])
                face_variation = cv2.GaussianBlur(face_gray, (kernel_size, kernel_size), 0)
            
            elif variation_type == 5:
                # Contrast adjustment
                alpha = np.random.uniform(0.8, 1.5)
                beta = np.random.randint(-20, 20)
                face_variation = cv2.convertScaleAbs(face_gray, alpha=alpha, beta=beta)
            
            elif variation_type == 6:
                # Salt and pepper noise
                noise = np.random.random(face_gray.shape)
                face_variation = face_gray.copy()
                face_variation[noise < 0.05] = 0
                face_variation[noise > 0.95] = 255
            
            elif variation_type == 7:
                # Horizontal flip
                face_variation = cv2.flip(face_gray, 1)
            
            elif variation_type == 8:
                # Slight scaling
                scale = np.random.uniform(0.9, 1.1)
                rows, cols = face_gray.shape
                M = cv2.getRotationMatrix2D((cols/2, rows/2), 0, scale)
                face_variation = cv2.warpAffine(face_gray, M, (cols, rows))
            
            else:
                # Morphological operations
                kernel = np.ones((3,3), np.uint8)
                if np.random.random() > 0.5:
                    face_variation = cv2.morphologyEx(face_gray, cv2.MORPH_OPEN, kernel)
                else:
                    face_variation = cv2.morphologyEx(face_gray, cv2.MORPH_CLOSE, kernel)
            
            return face_variation
            
        except Exception as e:
            print(f"Error creating variation: {e}")
            return face_gray
    
    def load_known_faces(self, students):
        """Load known faces for recognition"""
        if self.recognizer is None:
            print("❌ Face recognizer not available. Please install opencv-contrib-python")
            return False
            
        try:
            faces = []
            labels = []
            label_names = {}
            
            current_label = 0
            
            for student in students:
                student_name = student.get('name', 'Unknown')
                image_paths = student.get('image_paths', [])
                
                # Load first 20 images for training (better accuracy)
                loaded_count = 0
                for image_path in image_paths:
                    if loaded_count >= 20:  # Limit to 20 images per student
                        break
                        
                    if os.path.exists(image_path):
                        face_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                        if face_image is not None:
                            faces.append(face_image)
                            labels.append(current_label)
                            loaded_count += 1
                
                if loaded_count > 0:  # Only assign label if student has images
                    label_names[current_label] = student_name
                    self.known_names[current_label] = student
                    current_label += 1
            
            if faces and labels:
                # Train the recognizer
                self.recognizer.train(faces, np.array(labels))
                print(f"✅ Trained recognizer with {len(faces)} face images for {len(label_names)} students")
                return True
            else:
                print("❌ No faces found for training")
                return False
                
        except Exception as e:
            print(f"Error loading known faces: {e}")
            return False
    
    def recognize_faces_from_image(self, image_file):
        """Recognize faces from uploaded image"""
        if self.recognizer is None:
            print("❌ Face recognizer not available")
            return []
            
        try:
            # Read image
            if hasattr(image_file, 'read'):
                image_bytes = image_file.read()
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = cv2.imread(image_file)
            
            if image is None:
                return []
            
            # Detect faces
            faces, gray = self.detect_faces(image)
            recognized_students = []
            
            for (x, y, w, h) in faces:
                # Extract face region
                face_gray = gray[y:y+h, x:x+w]
                face_resized = cv2.resize(face_gray, (100, 100))
                
                # Predict using trained recognizer
                label, confidence = self.recognizer.predict(face_resized)
                
                # Lower confidence value means better match (LBPH threshold: 0-120)
                if confidence < 80:  # Threshold for recognition
                    student_info = self.known_names.get(label)
                    if student_info:
                        # Convert confidence to percentage (0-100%)
                        confidence_percentage = max(0, (80 - confidence) / 80)
                        
                        recognized_students.append({
                            'name': student_info.get('name', 'Unknown'),
                            'student_id': student_info.get('id'),
                            'roll_number': student_info.get('roll_number'),
                            'confidence': confidence_percentage,
                            'face_location': (x, y, w, h)
                        })
            
            return recognized_students
            
        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return []
    
    def save_model(self, model_path="data/face_recognizer_model.yml"):
        """Save trained model"""
        if self.recognizer is None:
            return False
            
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.recognizer.save(model_path)
            
            # Save names mapping
            names_path = model_path.replace('.yml', '_names.pkl')
            with open(names_path, 'wb') as f:
                pickle.dump(self.known_names, f)
            
            print(f"✅ Model saved: {model_path}")
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self, model_path="data/face_recognizer_model.yml"):
        """Load trained model"""
        if self.recognizer is None:
            return False
            
        try:
            if os.path.exists(model_path):
                self.recognizer.read(model_path)
                
                # Load names mapping
                names_path = model_path.replace('.yml', '_names.pkl')
                if os.path.exists(names_path):
                    with open(names_path, 'rb') as f:
                        self.known_names = pickle.load(f)
                
                print(f"✅ Model loaded: {model_path}")
                return True
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
