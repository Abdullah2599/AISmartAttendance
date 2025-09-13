import json
import os
from datetime import datetime
import uuid
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

class DatabaseManager:
    def __init__(self):
        self.db = None
        self.initialize_firebase()
        
        # Fallback to local JSON storage if Firebase fails
        self.local_storage = True
        self.data_dir = "data"
        self.students_file = os.path.join(self.data_dir, "students.json")
        self.classes_file = os.path.join(self.data_dir, "classes.json")
        self.attendance_file = os.path.join(self.data_dir, "attendance.json")
        
        os.makedirs(self.data_dir, exist_ok=True)
    
    def initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            config_path = "config/firebase_config.json"
            if os.path.exists(config_path):
                if not firebase_admin._apps:
                    cred = credentials.Certificate(config_path)
                    firebase_admin.initialize_app(cred)
                
                self.db = firestore.client()
                self.local_storage = False
                st.success("Connected to Firebase!")
            else:
                st.warning("Firebase config not found, using local storage")
        except Exception as e:
            st.warning(f"Firebase connection failed: {e}. Using local storage.")
            self.local_storage = True
    
    def load_json_file(self, filepath):
        """Load data from JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
    
    def save_json_file(self, filepath, data):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False
    
    def add_student(self, student_data):
        """Add new student - prevent duplicate face registration"""
        try:
            # Check multiple criteria to prevent duplicate registration
            roll_number = student_data.get('roll_number')
            student_name = student_data.get('name', '').lower().strip()
            
            if roll_number or student_name:
                existing_students = self.get_all_students()
                for student in existing_students:
                    existing_roll = student.get('roll_number')
                    existing_name = student.get('name', '').lower().strip()
                    has_images = student.get('image_paths') and len(student.get('image_paths', [])) > 0
                    
                    # Block if same roll number OR same name (with face images)
                    if has_images and (
                        (roll_number and existing_roll == roll_number) or
                        (student_name and existing_name == student_name)
                    ):
                        print(f"❌ Student already registered: {student.get('name')} (Roll: {existing_roll})")
                        return "DUPLICATE_STUDENT"
            
            student_id = str(uuid.uuid4())
            student_data['id'] = student_id
            student_data['registration_date'] = datetime.now().isoformat()
            
            if self.local_storage:
                # Local storage
                students = self.load_json_file(self.students_file)
                students[student_id] = student_data
                if self.save_json_file(self.students_file, students):
                    return student_id
            else:
                # Firebase storage
                doc_ref = self.db.collection('students').document(student_id)
                doc_ref.set(student_data)
                return student_id
                
        except Exception as e:
            print(f"Error adding student: {e}")
            return None
    
    def get_all_students(self):
        """Get all students"""
        try:
            if self.local_storage:
                students_dict = self.load_json_file(self.students_file)
                return list(students_dict.values())
            else:
                students = []
                docs = self.db.collection('students').stream()
                for doc in docs:
                    student_data = doc.to_dict()
                    students.append(student_data)
                return students
        except Exception as e:
            print(f"Error getting students: {e}")
            return []
    
    def get_student_by_id(self, student_id):
        """Get student by ID"""
        try:
            if self.local_storage:
                students = self.load_json_file(self.students_file)
                return students.get(student_id)
            else:
                doc_ref = self.db.collection('students').document(student_id)
                doc = doc_ref.get()
                if doc.exists:
                    return doc.to_dict()
                return None
        except Exception as e:
            print(f"Error getting student: {e}")
            return None
    
    def get_students_by_class(self, class_name):
        """Get students by class name - supports multiple classes per student"""
        try:
            all_students = self.get_all_students()
            class_students = []
            
            for student in all_students:
                student_classes = student.get('classes', [])
                # Support both old single class format and new multiple classes format
                if isinstance(student_classes, str):
                    if student_classes == class_name:
                        class_students.append(student)
                elif isinstance(student_classes, list):
                    if class_name in student_classes:
                        class_students.append(student)
                # Fallback to old 'class' field
                elif student.get('class') == class_name:
                    class_students.append(student)
            
            return class_students
        except Exception as e:
            print(f"Error getting students by class: {e}")
            return []
    
    def check_student_already_exists(self, roll_number):
        """Check if student with roll number already exists"""
        try:
            all_students = self.get_all_students()
            for student in all_students:
                if student.get('roll_number') == roll_number:
                    return True, student.get('id')
            return False, None
        except Exception as e:
            print(f"Error checking student existence: {e}")
            return False, None
    
    def update_student(self, student_id, updated_data):
        """Update existing student data"""
        try:
            if self.local_storage:
                students = self.load_json_file(self.students_file)
                if student_id in students:
                    students[student_id].update(updated_data)
                    return self.save_json_file(self.students_file, students)
            else:
                doc_ref = self.db.collection('students').document(student_id)
                doc_ref.update(updated_data)
                return True
            return False
        except Exception as e:
            print(f"Error updating student: {e}")
            return False
    
    def add_class(self, class_data):
        """Add new class with schedule"""
        try:
            class_id = str(uuid.uuid4())
            class_data['id'] = class_id
            class_data['created_date'] = datetime.now().isoformat()
            
            # Ensure schedule fields exist
            if 'schedule' not in class_data:
                class_data['schedule'] = {
                    'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                    'start_time': '09:00',
                    'end_time': '10:00'
                }
            
            if self.local_storage:
                classes = self.load_json_file(self.classes_file)
                classes[class_id] = class_data
                if self.save_json_file(self.classes_file, classes):
                    return class_id
            else:
                doc_ref = self.db.collection('classes').document(class_id)
                doc_ref.set(class_data)
                return class_id
                
        except Exception as e:
            print(f"Error adding class: {e}")
            return None
    
    def get_all_classes(self):
        """Get all classes"""
        try:
            if self.local_storage:
                classes_dict = self.load_json_file(self.classes_file)
                return list(classes_dict.values())
            else:
                classes = []
                docs = self.db.collection('classes').stream()
                for doc in docs:
                    class_data = doc.to_dict()
                    classes.append(class_data)
                return classes
        except Exception as e:
            print(f"Error getting classes: {e}")
            return []
    
    def delete_class(self, class_id):
        """Delete class"""
        try:
            if self.local_storage:
                classes = self.load_json_file(self.classes_file)
                if class_id in classes:
                    del classes[class_id]
                    return self.save_json_file(self.classes_file, classes)
            else:
                self.db.collection('classes').document(class_id).delete()
                return True
        except Exception as e:
            print(f"Error deleting class: {e}")
            return False
    
    def save_attendance(self, attendance_data):
        """Save attendance data - prevents duplicate marking for same class on same day"""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            if self.local_storage:
                attendance = self.load_json_file(self.attendance_file)
                if date_str not in attendance:
                    attendance[date_str] = {}
                
                # Check for existing attendance and only update if not already marked
                for class_name, students in attendance_data.items():
                    if class_name not in attendance[date_str]:
                        attendance[date_str][class_name] = {}
                    
                    for student_id, record in students.items():
                        # Only mark if not already present for this class today
                        existing_record = attendance[date_str][class_name].get(student_id)
                        if not existing_record or existing_record.get('status') != 'present':
                            attendance[date_str][class_name][student_id] = record
                        elif existing_record.get('status') == 'present':
                            print(f"Student {student_id} already marked present for {class_name} today")
                
                return self.save_json_file(self.attendance_file, attendance)
            else:
                doc_ref = self.db.collection('attendance').document(date_str)
                doc_ref.set(attendance_data, merge=True)
                return True
                
        except Exception as e:
            print(f"Error saving attendance: {e}")
            return False
    
    def get_attendance_by_date(self, date_str):
        """Get attendance by date"""
        try:
            if self.local_storage:
                attendance = self.load_json_file(self.attendance_file)
                return attendance.get(date_str, {})
            else:
                doc_ref = self.db.collection('attendance').document(date_str)
                doc = doc_ref.get()
                if doc.exists:
                    return doc.to_dict()
                return {}
        except Exception as e:
            print(f"Error getting attendance: {e}")
            return {}
    
    def get_classes_for_current_time(self):
        """Get classes that should be active at current time"""
        try:
            current_time = datetime.now()
            current_day = current_time.strftime('%A')
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_total_minutes = current_hour * 60 + current_minute
            
            active_classes = []
            all_classes = self.get_all_classes()
            
            for cls in all_classes:
                schedule = cls.get('schedule', {})
                days = schedule.get('days', [])
                start_time = schedule.get('start_time', '09:00')
                end_time = schedule.get('end_time', '10:00')
                
                # Check if today is in the class schedule
                if current_day in days:
                    # Parse start and end times
                    start_parts = start_time.split(':')
                    end_parts = end_time.split(':')
                    
                    start_total_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                    end_total_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
                    
                    # Check if current time is within class time
                    if start_total_minutes <= current_total_minutes <= end_total_minutes:
                        active_classes.append(cls)
            
            return active_classes
        except Exception as e:
            print(f"Error getting active classes: {e}")
            return []
    
    def get_daily_class_attendance(self, class_name, date_str=None):
        """Get attendance for a specific class on a specific date"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            daily_attendance = self.get_attendance_by_date(date_str)
            class_attendance = daily_attendance.get(class_name, {})
            
            # Get detailed student info
            detailed_attendance = []
            for student_id, record in class_attendance.items():
                student_info = self.get_student_by_id(student_id)
                if student_info:
                    detailed_attendance.append({
                        'student_id': student_id,
                        'name': student_info.get('name', 'Unknown'),
                        'roll_number': student_info.get('roll_number', 'N/A'),
                        'status': record.get('status', 'absent'),
                        'in_time': record.get('in_time', ''),
                        'out_time': record.get('out_time', ''),
                        'confidence': record.get('confidence', 0),
                        'marked_by': record.get('marked_by', 'unknown')
                    })
            
            return detailed_attendance
        except Exception as e:
            print(f"Error getting daily class attendance: {e}")
            return []
    
    def get_attendance_status_by_time(self, class_name, current_time):
        """Determine attendance status based on class schedule and current time"""
        try:
            # Get class schedule
            classes = self.get_all_classes()
            target_class = None
            for cls in classes:
                if cls.get('name') == class_name:
                    target_class = cls
                    break
            
            if not target_class:
                return 'absent'  # Class not found
            
            schedule = target_class.get('schedule', {})
            start_time_str = schedule.get('start_time', '09:00')
            
            # Parse times
            from datetime import datetime, timedelta
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            current_time_obj = datetime.strptime(current_time.strftime('%H:%M'), '%H:%M').time()
            
            # Convert to datetime objects for comparison
            today = current_time.date()
            start_datetime = datetime.combine(today, start_time)
            current_datetime = datetime.combine(today, current_time_obj)
            
            # Calculate time differences
            time_diff = (current_datetime - start_datetime).total_seconds() / 60  # in minutes
            
            # Attendance rules:
            # 15 minutes before class start: Present
            # After class start to 1 hour: Late
            # After 1 hour: Absent
            
            if time_diff <= -15:  # More than 15 minutes before class
                return 'present'
            elif time_diff <= 0:  # Within 15 minutes before class start
                return 'present'
            elif time_diff <= 60:  # Within 1 hour after class start
                return 'late'
            else:  # More than 1 hour after class start
                return 'absent'
                
        except Exception as e:
            print(f"Error determining attendance status: {e}")
            return 'absent'
    
    def check_student_already_marked(self, class_name, student_id, date_str=None):
        """Check if student is already marked for this class today"""
        try:
            if date_str is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            daily_attendance = self.get_attendance_by_date(date_str)
            class_attendance = daily_attendance.get(class_name, {})
            student_record = class_attendance.get(student_id, {})
            
            # Return True if student has any status (present, late, or absent)
            return bool(student_record.get('status'))
        except Exception as e:
            print(f"Error checking student attendance: {e}")
            return False
    
    def get_classes_with_dates(self):
        """Get all classes with their attendance dates"""
        try:
            classes_with_dates = {}
            
            # Get all classes
            all_classes = self.get_all_classes()
            
            # Get all attendance data
            if self.local_storage:
                attendance_data = self.load_json_file(self.attendance_file)
            else:
                # For Firebase, we'd need to get all attendance documents
                attendance_data = {}
            
            # Build classes with their attendance dates
            for cls in all_classes:
                class_name = cls.get('name')
                classes_with_dates[class_name] = {
                    'class_info': cls,
                    'dates': []
                }
            
            # Add dates where attendance was recorded
            for date_str, daily_data in attendance_data.items():
                for class_name in daily_data.keys():
                    if class_name in classes_with_dates:
                        classes_with_dates[class_name]['dates'].append(date_str)
            
            # Sort dates for each class
            for class_name in classes_with_dates:
                classes_with_dates[class_name]['dates'].sort(reverse=True)  # Most recent first
            
            return classes_with_dates
            
        except Exception as e:
            print(f"Error getting classes with dates: {e}")
            return {}
    
    def get_attendance_report(self, start_date, end_date, class_filter=None):
        """Generate attendance report"""
        try:
            report_data = []
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                daily_attendance = self.get_attendance_by_date(date_str)
                
                for class_name, students in daily_attendance.items():
                    if class_filter and class_filter != "All Classes" and class_name != class_filter:
                        continue
                    
                    for student_id, record in students.items():
                        student_info = self.get_student_by_id(student_id)
                        report_data.append({
                            'date': date_str,
                            'class': class_name,
                            'student_id': student_id,
                            'student_name': student_info.get('name', 'Unknown') if student_info else 'Unknown',
                            'roll_number': student_info.get('roll_number', 'Unknown') if student_info else 'Unknown',
                            'status': record.get('status', 'absent'),
                            'in_time': record.get('in_time', ''),
                            'out_time': record.get('out_time', '')
                        })
                
                current_date += datetime.timedelta(days=1)
            
            return report_data
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return []
