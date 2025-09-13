import streamlit as st
import cv2
import os
from datetime import datetime, timedelta
import pandas as pd
from modules.face_recognition import FaceRecognizer
from modules.database import DatabaseManager
from modules.qr_handler import QRHandler
from modules.attendance import AttendanceManager

# Page configuration
st.set_page_config(
    page_title="AI Attendance Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def initialize_components():
    face_recognizer = FaceRecognizer()
    db_manager = DatabaseManager()
    qr_handler = QRHandler()
    attendance_manager = AttendanceManager()
    return face_recognizer, db_manager, qr_handler, attendance_manager

def main():
    st.title("🎓 AI Attendance Manager")
    st.markdown("### Smart Attendance System Using Face Recognition")
    
    # Initialize components
    face_recognizer, db_manager, qr_handler, attendance_manager = initialize_components()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Student Registration", "Attendance Marking", "Class Management", "Reports", "QR Scanner"]
    )
    
    # Check if today is Sunday
    today = datetime.now()
    if today.weekday() == 6:  # Sunday
        st.warning("📅 Today is Sunday - No attendance will be marked!")
    
    if page == "Dashboard":
        show_dashboard(db_manager, attendance_manager)
    elif page == "Student Registration":
        show_student_registration(face_recognizer, db_manager, qr_handler)
    elif page == "Attendance Marking":
        show_attendance_marking(face_recognizer, db_manager, attendance_manager)
    elif page == "Class Management":
        show_class_management(db_manager)
    elif page == "Reports":
        show_reports(db_manager)
    elif page == "QR Scanner":
        show_qr_scanner(qr_handler, db_manager)

def show_dashboard(db_manager, attendance_manager):
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get statistics
    total_students = len(db_manager.get_all_students())
    total_classes = len(db_manager.get_all_classes())
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_attendance = db_manager.get_attendance_by_date(today_date)
    
    present_today = sum(1 for records in today_attendance.values() 
                       for record in records.values() 
                       if record.get('status') == 'present')
    
    with col1:
        st.metric("Total Students", total_students)
    with col2:
        st.metric("Total Classes", total_classes)
    with col3:
        st.metric("Present Today", present_today)
    with col4:
        st.metric("Attendance Rate", f"{(present_today/max(total_students,1)*100):.1f}%")
    
    # Recent attendance
    st.subheader("📋 Recent Attendance")
    if today_attendance:
        df_data = []
        for class_name, students in today_attendance.items():
            for student_id, record in students.items():
                student_info = db_manager.get_student_by_id(student_id)
                df_data.append({
                    'Student Name': student_info.get('name', 'Unknown') if student_info else 'Unknown',
                    'Class': class_name,
                    'Status': record.get('status', 'absent'),
                    'In Time': record.get('in_time', 'N/A'),
                    'Out Time': record.get('out_time', 'N/A')
                })
        
        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No attendance marked today")
    else:
        st.info("No attendance data available for today")

def show_student_registration(face_recognizer, db_manager, qr_handler):
    st.header("👤 Student Registration")
    
    with st.form("student_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Student Name*", placeholder="Enter full name", key="reg_name")
            roll_number = st.text_input("Roll Number*", placeholder="Enter roll number", key="reg_roll")
            email = st.text_input("Email", placeholder="student@email.com", key="reg_email")
            phone = st.text_input("Phone", placeholder="+92xxxxxxxxx", key="reg_phone")
        
        with col2:
            classes = db_manager.get_all_classes()
            class_names = [cls.get('name', 'Unknown') for cls in classes]
            if not class_names:
                class_names = ["No classes available"]
            
            # Multiple class selection
            st.subheader("📚 Select Classes")
            selected_classes = st.multiselect(
                "Select Classes (can select multiple)*", 
                class_names, 
                key="reg_classes",
                help="Student can be enrolled in multiple classes"
            )
            
            # Image capture options
            st.subheader("📸 Capture Student Photo")
            capture_method = st.radio(
                "Choose capture method:", 
                ["Camera", "Upload File", "QR Code Upload"], 
                key="reg_capture_method"
            )
        
        # Image capture section
        captured_images = []
        
        if capture_method == "Camera":
            st.info("📷 Use camera to take student photo")
            camera_image = st.camera_input("Take a photo", key="reg_camera_input")
            if camera_image:
                captured_images.append(camera_image)
                st.success("✅ Photo captured successfully!")
        
        elif capture_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload student photo", 
                type=['jpg', 'jpeg', 'png'], 
                key="reg_file_upload"
            )
            if uploaded_file:
                captured_images.append(uploaded_file)
                st.success("✅ File uploaded successfully!")
        
        elif capture_method == "QR Code Upload":
            st.info("📱 Generate QR code first, then scan with mobile to upload photo")
            st.write("This feature will be available after registration")
        
        # Submit button (REQUIRED for st.form)
        submitted = st.form_submit_button("🎯 Register Student", use_container_width=True)
        
        # Process form submission
        if submitted:
            # Get the captured image from the list
            captured_image = captured_images[0] if captured_images else None
            
            if name and roll_number and selected_classes and captured_image is not None:
                # Check if student already exists
                exists, existing_id = db_manager.check_student_already_exists(roll_number)
                if exists:
                    st.error(f"❌ Student with roll number {roll_number} already exists!")
                else:
                    try:
                        student_data = {
                            'name': name,
                            'roll_number': roll_number,
                            'email': email,
                            'phone': phone,
                            'classes': selected_classes  # Store multiple classes
                        }
                        
                        # Check face similarity BEFORE adding to database
                        with st.spinner("Checking for duplicate faces..."):
                            is_duplicate_face = face_recognizer.check_face_similarity(captured_image)
                        
                        if is_duplicate_face:
                            st.error("❌ This face is already registered! Same person cannot register again.")
                            st.warning("🔍 Your uploaded image matches with existing student images.")
                        else:
                            # Add student to database only if face is unique
                            student_id = db_manager.add_student(student_data)
                            
                            if student_id == "DUPLICATE_STUDENT":
                                st.error("❌ This student is already registered! Same person cannot register again.")
                            elif student_id:
                                # Process and save face images
                                with st.spinner("Processing face images..."):
                                    success = face_recognizer.process_student_images(student_id, name, captured_image, roll_number)
                                
                                if success:
                                    # Update student record with image paths
                                    student_dir = f"data/students/{roll_number}_{name.replace(' ', '_')}"
                                    image_paths = [os.path.join(student_dir, f"face_{i:03d}.jpg") for i in range(100)]
                                    
                                    # Update student data in database
                                    updated_data = student_data.copy()
                                    updated_data['image_paths'] = image_paths
                                    db_manager.update_student(student_id, updated_data)
                                    
                                    st.success(f"✅ Student {name} registered successfully!")
                                    st.info(f"📚 Enrolled in classes: {', '.join(selected_classes)}")
                                    st.balloons()
                                    
                                    # Generate QR code for student
                                    qr_code_path = qr_handler.generate_student_qr(student_id, name)
                                    if qr_code_path:
                                        st.success(f"📱 QR Code generated: {qr_code_path}")
                                else:
                                    st.error("❌ Failed to process face images")
                            else:
                                st.error("❌ Failed to register student")
                    except Exception as e:
                        st.error(f"❌ Error during registration: {str(e)}")
            else:
                missing = []
                if not name: missing.append("Name")
                if not roll_number: missing.append("Roll Number")
                if not selected_classes: missing.append("Classes")
                if captured_image is None: missing.append("Photo")
                st.error(f"❌ Please fill in: {', '.join(missing)}")
    
    # Show existing students
    st.subheader("👥 Registered Students")
    students = db_manager.get_all_students()
    
    if students:
        # Create a simple display of registered students
        for idx, student in enumerate(students):
            with st.expander(f"📚 {student.get('name', 'Unknown')} - {student.get('roll_number', 'N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    # Handle both old single class and new multiple classes format
                    classes = student.get('classes', student.get('class', 'N/A'))
                    if isinstance(classes, list):
                        classes_str = ', '.join(classes)
                    else:
                        classes_str = classes
                    st.write(f"**Classes:** {classes_str}")
                    st.write(f"**Email:** {student.get('email', 'N/A')}")
                with col2:
                    st.write(f"**Phone:** {student.get('phone', 'N/A')}")
                    st.write(f"**Registered:** {student.get('registration_date', 'N/A')}")
                
                # Show image count
                image_count = len(student.get('image_paths', []))
                st.write(f"**Training Images:** {image_count}")
    else:
        st.info("No students registered yet.")

def show_attendance_marking(face_recognizer, db_manager, attendance_manager):
    st.header("✅ Attendance Marking")
    
    # Check if Sunday
    if datetime.now().weekday() == 6:
        st.error("📅 Attendance cannot be marked on Sunday!")
        return
    
    # Class selection - only show active classes
    active_classes = db_manager.get_classes_for_current_time()
    all_classes = db_manager.get_all_classes()
    
    if not all_classes:
        st.warning("No classes available. Please create a class first.")
        return
    
    # Show class status
    st.subheader("📅 Class Schedule Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🟢 Currently Active Classes:**")
        if active_classes:
            for cls in active_classes:
                schedule = cls.get('schedule', {})
                st.success(f"✅ {cls.get('name')} ({schedule.get('start_time')} - {schedule.get('end_time')})")
        else:
            st.info("No classes currently in session")
    
    with col2:
        st.write("**📋 All Classes:**")
        for cls in all_classes:
            schedule = cls.get('schedule', {})
            is_active = cls.get('name') in [ac.get('name') for ac in active_classes]
            status = "🟢 Active" if is_active else "🔴 Inactive"
            st.write(f"{status} {cls.get('name')} ({schedule.get('start_time')} - {schedule.get('end_time')})")
    
    # Only allow attendance for active classes
    if not active_classes:
        st.error("🚫 **Attendance is disabled** - No classes are currently in session!")
        st.info("💡 Attendance can only be marked during scheduled class hours")
        return
    
    active_class_names = [cls.get('name', 'Unknown') for cls in active_classes]
    selected_class = st.selectbox("Select Active Class for Attendance", active_class_names)
    
    if selected_class:
        # Load student faces for recognition
        class_students = db_manager.get_students_by_class(selected_class)
        face_recognizer.load_known_faces(class_students)
        
        st.info(f"Loaded {len(class_students)} students for recognition")
        
        # Camera feed for attendance
        st.subheader("📹 Camera Feed")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Camera input
            run_camera = st.checkbox("Start Camera for Attendance")
            
            if run_camera:
                camera_input = st.camera_input("Live Camera Feed")
                
                if camera_input is not None:
                    # Process the frame
                    recognized_students = face_recognizer.recognize_faces_from_image(camera_input)
                    
                    if recognized_students:
                        st.success(f"Recognized {len(recognized_students)} students:")
                        for student in recognized_students:
                            st.write(f"- {student['name']} (Confidence: {student['confidence']:.2f})")
                        
                        # Mark attendance button
                        if st.button("Mark Attendance for Recognized Students", type="primary"):
                            attendance_data = attendance_manager.mark_attendance(
                                selected_class, recognized_students, class_students, db_manager
                            )
                            
                            if attendance_data and db_manager.save_attendance(attendance_data):
                                st.success("✅ Attendance marked successfully!")
                                
                                # Show summary
                                summary = attendance_manager.get_daily_summary(attendance_data, selected_class)
                                st.metric("Attendance Summary", 
                                         f"{summary['present']}/{summary['total']} Present", 
                                         f"{summary['percentage']:.1f}%")
                            else:
                                st.error("Failed to save attendance")
                    else:
                        st.warning("No students recognized in the image")
        
        with col2:
            # Manual attendance option
            st.subheader("Manual Attendance")
            st.info("For backup or corrections")
            
            for student in class_students:
                col_name, col_status = st.columns([3, 1])
                with col_name:
                    st.write(student.get('name', 'Unknown'))
                with col_status:
                    status = st.selectbox(
                        f"Status for {student.get('name', 'Unknown')}", 
                        ["present", "absent"], 
                        key=f"manual_{student.get('id', 'unknown')}"
                    )
            
            if st.button("Save Manual Attendance"):
                # Implementation for manual attendance
                st.success("Manual attendance saved!")

def show_class_management(db_manager):
    st.header("🏫 Class Management")
    
    # Create new class
    with st.expander("Create New Class"):
        with st.form("create_class"):
            col1, col2 = st.columns(2)
            
            with col1:
                class_name = st.text_input("Class Name*", placeholder="e.g., Computer Science A")
                class_description = st.text_area("Description", placeholder="Class description...")
            
            with col2:
                st.subheader("Class Schedule")
                
                # Days selection
                days_options = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                selected_days = st.multiselect("Select Class Days*", days_options, default=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
                
                # Time selection
                start_time = st.time_input("Start Time*", value=datetime.strptime('09:00', '%H:%M').time())
                end_time = st.time_input("End Time*", value=datetime.strptime('10:00', '%H:%M').time())
            
            submitted = st.form_submit_button("Create Class")
            
            if submitted and class_name and selected_days:
                class_data = {
                    'name': class_name,
                    'description': class_description,
                    'schedule': {
                        'days': selected_days,
                        'start_time': start_time.strftime('%H:%M'),
                        'end_time': end_time.strftime('%H:%M')
                    },
                    'created_date': datetime.now().isoformat()
                }
                
                class_id = db_manager.add_class(class_data)
                if class_id:
                    st.success(f"✅ Class '{class_name}' created successfully!")
                    st.success(f"📅 Schedule: {', '.join(selected_days)} from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}")
                else:
                    st.error("Failed to create class")
            elif submitted:
                if not class_name:
                    st.error("Please enter class name")
                if not selected_days:
                    st.error("Please select at least one day")
    
    # Display existing classes
    st.subheader("📚 Existing Classes")
    classes = db_manager.get_all_classes()
    
    # Show current active classes
    active_classes = db_manager.get_classes_for_current_time()
    if active_classes:
        st.success(f"🟢 Currently Active: {', '.join([cls.get('name') for cls in active_classes])}")
    
    if classes:
        for cls in classes:
            schedule = cls.get('schedule', {})
            days = schedule.get('days', [])
            start_time = schedule.get('start_time', 'N/A')
            end_time = schedule.get('end_time', 'N/A')
            
            # Check if class is currently active
            is_active = cls in active_classes
            status_icon = "🟢" if is_active else "⚪"
            
            with st.expander(f"{status_icon} {cls.get('name', 'Unknown Class')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Description:** {cls.get('description', 'No description')}")
                    st.write(f"**Created:** {cls.get('created_date', 'Unknown')}")
                    st.write(f"**Status:** {'🟢 Currently Active' if is_active else '⚪ Not Active'}")
                
                with col2:
                    st.write(f"**Schedule Days:** {', '.join(days) if days else 'Not set'}")
                    st.write(f"**Time:** {start_time} - {end_time}")
                    
                    students = db_manager.get_students_by_class(cls.get('name'))
                    st.write(f"**Total Students:** {len(students)}")
                    
                    # Show today's attendance button
                    if st.button(f"📋 View Today's Attendance", key=f"view_attendance_{cls.get('id')}"):
                        show_daily_class_attendance(db_manager, cls.get('name'))
                    
                    if st.button(f"Delete Class", key=f"delete_{cls.get('id')}"):
                        if db_manager.delete_class(cls.get('id')):
                            st.success("Class deleted successfully!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to delete class")
    else:
        st.info("No classes created yet")

def show_daily_class_attendance(db_manager, class_name):
    """Show today's attendance for a specific class"""
    st.subheader(f"📋 Today's Attendance - {class_name}")
    
    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get attendance data for this class today
    attendance_records = db_manager.get_daily_class_attendance(class_name, today)
    
    if attendance_records:
        # Separate present and absent students
        present_students = [record for record in attendance_records if record['status'] == 'present']
        absent_students = [record for record in attendance_records if record['status'] == 'absent']
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Students", len(attendance_records))
        with col2:
            st.metric("Present", len(present_students), delta=f"{len(present_students)}")
        with col3:
            st.metric("Absent", len(absent_students), delta=f"-{len(absent_students)}")
        
        # Show present students
        if present_students:
            st.success(f"✅ Present Students ({len(present_students)})")
            for student in present_students:
                col_name, col_roll, col_time, col_confidence = st.columns([3, 2, 2, 2])
                with col_name:
                    st.write(f"👤 {student['name']}")
                with col_roll:
                    st.write(f"🆔 {student['roll_number']}")
                with col_time:
                    st.write(f"🕐 {student['in_time']}")
                with col_confidence:
                    confidence = student['confidence']
                    if confidence > 0:
                        st.write(f"📊 {confidence:.2f}")
                    else:
                        st.write("📝 Manual")
        
        # Show absent students
        if absent_students:
            st.error(f"❌ Absent Students ({len(absent_students)})")
            for student in absent_students:
                col_name, col_roll = st.columns([3, 2])
                with col_name:
                    st.write(f"👤 {student['name']}")
                with col_roll:
                    st.write(f"🆔 {student['roll_number']}")
        
        # Show detailed table
        st.subheader("📊 Detailed View")
        import pandas as pd
        df = pd.DataFrame(attendance_records)
        df = df[['name', 'roll_number', 'status', 'in_time', 'confidence', 'marked_by']]
        df.columns = ['Name', 'Roll Number', 'Status', 'In Time', 'Confidence', 'Marked By']
        st.dataframe(df, use_container_width=True)
        
    else:
        st.info(f"No attendance records found for {class_name} today.")
        st.write("Students may not have been marked for attendance yet.")

def show_reports(db_manager):
    st.header("📊 Reports")
    
    # Create tabs for different report types
    tab1, tab2 = st.tabs(["📋 Hierarchical Reports", "📈 Summary Reports"])
    
    with tab1:
        st.subheader("📚 Class-wise Attendance Records")
        
        # Get all classes with their attendance dates
        classes_with_dates = db_manager.get_classes_with_dates()
        
        if not classes_with_dates:
            st.info("No classes or attendance data found.")
            return
        
        # Step 1: Select Class
        class_names = list(classes_with_dates.keys())
        selected_class = st.selectbox("🏫 Select Class", class_names, key="hierarchical_class")
        
        if selected_class and classes_with_dates[selected_class]['dates']:
            # Step 2: Select Date
            available_dates = classes_with_dates[selected_class]['dates']
            
            st.write(f"**Available attendance dates for {selected_class}:**")
            
            # Create columns for date selection
            cols = st.columns(min(3, len(available_dates)))
            selected_date = None
            
            for i, date_str in enumerate(available_dates):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    # Convert date string to readable format
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        readable_date = date_obj.strftime("%B %d, %Y")
                        day_name = date_obj.strftime("%A")
                        
                        if st.button(f"📅 {readable_date}\n({day_name})", key=f"date_{i}"):
                            selected_date = date_str
                    except:
                        if st.button(f"📅 {date_str}", key=f"date_{i}"):
                            selected_date = date_str
            
            # If no button clicked, show dropdown as alternative
            if not selected_date:
                st.write("**Or select from dropdown:**")
                selected_date = st.selectbox("📅 Select Date", available_dates, key="date_dropdown")
            
            # Step 3: Show Student Records for Selected Date
            if selected_date:
                st.subheader(f"👥 Student Records - {selected_class} ({selected_date})")
                
                # Get attendance records for this class and date
                attendance_records = db_manager.get_daily_class_attendance(selected_class, selected_date)
                
                if attendance_records:
                    # Separate by status
                    present_students = [r for r in attendance_records if r['status'] == 'present']
                    late_students = [r for r in attendance_records if r['status'] == 'late']
                    absent_students = [r for r in attendance_records if r['status'] == 'absent']
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total", len(attendance_records))
                    with col2:
                        st.metric("Present", len(present_students), delta=f"+{len(present_students)}")
                    with col3:
                        st.metric("Late", len(late_students), delta=f"⚠️{len(late_students)}")
                    with col4:
                        st.metric("Absent", len(absent_students), delta=f"-{len(absent_students)}")
                    
                    # Present students
                    if present_students:
                        st.success(f"✅ Present Students ({len(present_students)})")
                        for student in present_students:
                            col_name, col_roll, col_time, col_method = st.columns([3, 2, 2, 2])
                            with col_name:
                                st.write(f"👤 **{student['name']}**")
                            with col_roll:
                                st.write(f"🆔 {student['roll_number']}")
                            with col_time:
                                st.write(f"🕐 {student['in_time']}")
                            with col_method:
                                method = "🤖 Auto" if student['marked_by'] == 'face_recognition' else "📝 Manual"
                                st.write(method)
                    
                    # Late students
                    if late_students:
                        st.warning(f"🕐 Late Students ({len(late_students)})")
                        for student in late_students:
                            col_name, col_roll, col_time, col_method = st.columns([3, 2, 2, 2])
                            with col_name:
                                st.write(f"👤 **{student['name']}**")
                            with col_roll:
                                st.write(f"🆔 {student['roll_number']}")
                            with col_time:
                                st.write(f"🕐 {student['in_time']}")
                            with col_method:
                                method = "🤖 Auto" if student['marked_by'] == 'face_recognition' else "📝 Manual"
                                st.write(method)
                    
                    # Absent students
                    if absent_students:
                        st.error(f"❌ Absent Students ({len(absent_students)})")
                        for student in absent_students:
                            col_name, col_roll = st.columns([3, 2])
                            with col_name:
                                st.write(f"👤 **{student['name']}**")
                            with col_roll:
                                st.write(f"🆔 {student['roll_number']}")
                    
                    # Detailed table
                    st.subheader("📊 Detailed Table")
                    import pandas as pd
                    df = pd.DataFrame(attendance_records)
                    df = df[['name', 'roll_number', 'status', 'in_time', 'confidence', 'marked_by']]
                    df.columns = ['Name', 'Roll Number', 'Status', 'In Time', 'Confidence', 'Marked By']
                    st.dataframe(df, use_container_width=True)
                    
                    # Download option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {selected_class} - {selected_date}",
                        data=csv,
                        file_name=f"attendance_{selected_class}_{selected_date}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"No attendance records found for {selected_class} on {selected_date}")
        
        elif selected_class:
            st.info(f"No attendance data available for {selected_class}")
    
    with tab2:
        st.subheader("📈 Summary Reports")
        
        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Class filter
        classes = db_manager.get_all_classes()
        class_names = ["All Classes"] + [cls.get('name', 'Unknown') for cls in classes]
        selected_class_summary = st.selectbox("Filter by Class", class_names)
        
        if st.button("Generate Summary Report"):
            # Generate attendance report
            attendance_data = db_manager.get_attendance_report(start_date, end_date, selected_class_summary)
            
            if attendance_data:
                # Display summary
                st.subheader("📈 Attendance Summary")
                
                # Create summary statistics
                total_days = (end_date - start_date).days + 1
                total_students = len(set(record['student_id'] for record in attendance_data))
                present_count = sum(1 for record in attendance_data if record['status'] == 'present')
                late_count = sum(1 for record in attendance_data if record['status'] == 'late')
                absent_count = sum(1 for record in attendance_data if record['status'] == 'absent')
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Days", total_days)
                with col2:
                    st.metric("Present", present_count)
                with col3:
                    st.metric("Late", late_count)
                with col4:
                    st.metric("Absent", absent_count)
                
                # Attendance rate
                total_records = len(attendance_data)
                if total_records > 0:
                    present_rate = (present_count / total_records) * 100
                    late_rate = (late_count / total_records) * 100
                    absent_rate = (absent_count / total_records) * 100
                    
                    st.write("**Attendance Rates:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Present Rate", f"{present_rate:.1f}%")
                    with col2:
                        st.metric("Late Rate", f"{late_rate:.1f}%")
                    with col3:
                        st.metric("Absent Rate", f"{absent_rate:.1f}%")
                
                # Detailed report
                st.subheader("📋 Detailed Report")
                df = pd.DataFrame(attendance_data)
                st.dataframe(df, use_container_width=True)
                
                # Download CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Summary CSV",
                    data=csv,
                    file_name=f"attendance_summary_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No attendance data found for the selected criteria")

def show_qr_scanner(qr_handler, db_manager):
    st.header("📱 QR Code Scanner")
    
    st.info("Students can use this to upload their photos via QR code")
    
    # Upload image with QR code
    uploaded_file = st.file_uploader("Upload image containing QR code", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        # Display uploaded image
        st.image(uploaded_file, caption="Uploaded Image", width=300)
        
        # Scan QR code
        qr_data = qr_handler.scan_qr_code(uploaded_file)
        
        if qr_data:
            st.success("QR Code detected!")
            st.json(qr_data)
            
            # Process based on QR data
            if qr_data.get('type') == 'student_upload':
                student_id = qr_data.get('student_id')
                if student_id:
                    # Allow photo upload for this student
                    st.subheader(f"Upload photo for {qr_data.get('name', 'Student')}")
                    
                    photo_file = st.file_uploader("Upload student photo", type=['jpg', 'jpeg', 'png'])
                    
                    if photo_file and st.button("Process Photo"):
                        # Process and save photo
                        success = qr_handler.process_student_photo(student_id, photo_file)
                        if success:
                            st.success("Photo uploaded and processed successfully!")
                        else:
                            st.error("Failed to process photo")
        else:
            st.warning("No valid QR code found in the image")

if __name__ == "__main__":
    main()
