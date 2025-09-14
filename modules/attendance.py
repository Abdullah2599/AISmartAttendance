from datetime import datetime
import streamlit as st

class AttendanceManager:
    def __init__(self):
        self.current_session_attendance = {}
        self.session_detected_students = {}
    
    def clear_session_data(self):
        self.current_session_attendance = {}
        self.session_detected_students = {}
    
    def reset_session_detection(self, class_name):
        current_date = datetime.now().strftime('%Y-%m-%d')
        session_key = f"{class_name}_{current_date}"
        if session_key in self.session_detected_students:
            self.session_detected_students[session_key] = set()
            return True
        return False
    
    def mark_attendance(self, class_name, recognized_students, all_class_students, db_manager):
        try:
            
            current_time = datetime.now()
            attendance_data = {class_name: {}}
            already_marked_count = 0
            present_count = 0
            late_count = 0
            
            session_key = f"{class_name}_{current_time.strftime('%Y-%m-%d')}"
            if session_key not in self.session_detected_students:
                self.session_detected_students[session_key] = set()
            
            recognized_ids = {student['student_id'] for student in recognized_students if student.get('student_id')}
            
            for student in all_class_students:
                student_id = student.get('id')
                if not student_id:
                    continue
                
                already_marked = db_manager.check_student_already_marked(class_name, student_id)
                
                already_detected_in_session = student_id in self.session_detected_students[session_key]
                
                if student_id in recognized_ids:
                    if already_marked:
                        already_marked_count += 1
                        st.info(f"ℹ️ {student.get('name', 'Student')} already marked for {class_name} today")
                        continue
                    elif already_detected_in_session:
                        st.info(f"🔄 {student.get('name', 'Student')} already detected in this session")
                        continue
                    else:
                        self.session_detected_students[session_key].add(student_id)
                        status = db_manager.get_attendance_status_by_time(class_name, current_time)
                        
                        attendance_data[class_name][student_id] = {
                            'status': status,
                            'in_time': current_time.strftime("%H:%M:%S"),
                            'out_time': '',
                            'date': current_time.strftime("%Y-%m-%d"),
                            'marked_by': 'face_recognition',
                            'confidence': next((s['confidence'] for s in recognized_students if s.get('student_id') == student_id), 0)
                        }
                        
                        if status == 'present':
                            present_count += 1
                        elif status == 'late':
                            late_count += 1
                else:
                    if not already_marked:
                        attendance_data[class_name][student_id] = {
                            'status': 'absent',
                            'in_time': '',
                            'out_time': '',
                            'date': current_time.strftime("%Y-%m-%d"),
                            'marked_by': 'auto_absent',
                            'confidence': 0
                        }
            
            if already_marked_count > 0:
                st.warning(f"⚠️ {already_marked_count} students already marked today")
            if present_count > 0:
                st.success(f"✅ {present_count} students marked Present (on time)")
            if late_count > 0:
                st.warning(f"🕐 {late_count} students marked Late")
            
            self.current_session_attendance.update(attendance_data)
            return attendance_data
            
        except Exception as e:
            st.error(f"Error marking attendance: {e}")
            return None
    
    def update_out_time(self, class_name, student_id):
        try:
            current_time = datetime.now()
            return {
                'out_time': current_time.strftime("%H:%M:%S"),
                'updated_at': current_time.isoformat()
            }
        except Exception as e:
            print(f"Error updating out time: {e}")
            return None
    
    def calculate_duration(self, in_time, out_time):
        try:
            if in_time and out_time:
                in_dt = datetime.strptime(in_time, "%H:%M:%S")
                out_dt = datetime.strptime(out_time, "%H:%M:%S")
                duration = out_dt - in_dt
                return str(duration)
            return "Not calculated"
        except Exception as e:
            print(f"Error calculating duration: {e}")
            return "Error"
    
    def check_class_schedule_and_mark_attendance(self, db_manager, face_recognizer):
        try:
            active_classes = db_manager.get_classes_for_current_time()
            
            if not active_classes:
                return None, "No classes are currently scheduled"
            
            results = []
            for cls in active_classes:
                class_name = cls.get('name')
                schedule = cls.get('schedule', {})
                
                results.append({
                    'class_name': class_name,
                    'schedule': schedule,
                    'students_count': len(db_manager.get_students_by_class(class_name))
                })
            
            return results, f"Found {len(active_classes)} active classes"
            
        except Exception as e:
            return None, f"Error checking schedule: {e}"
    
    def get_daily_summary(self, attendance_data, class_name):
        try:
            if class_name not in attendance_data:
                return {"total": 0, "present": 0, "absent": 0, "percentage": 0}
            
            class_attendance = attendance_data[class_name]
            total = len(class_attendance)
            present = sum(1 for record in class_attendance.values() if record.get('status') == 'present')
            absent = total - present
            percentage = (present / total * 100) if total > 0 else 0
            
            return {
                "total": total,
                "present": present,
                "absent": absent,
                "percentage": round(percentage, 2)
            }
            
        except Exception as e:
            print(f"Error getting summary: {e}")
            return {"total": 0, "present": 0, "absent": 0, "percentage": 0}
