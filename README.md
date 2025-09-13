# 🎓 AI Attendance Management System

A comprehensive attendance management system using face recognition, class scheduling, and automated attendance tracking.

## ✨ Key Features

### 🏫 Class Management
- **Class Registration**: Create classes with detailed schedules
- **Schedule Management**: Set specific days and times for each class
- **Active Class Detection**: Automatically identifies currently running classes
- **Real-time Status**: Shows which classes are currently active

### 👤 Student Registration
- **Complete Student Profiles**: Name, roll number, email, phone, class assignment
- **Advanced Image Processing**: Generates exactly **100 grayscale variations** per student
- **Multiple Capture Methods**: Camera, file upload, or QR code upload
- **Face Detection**: Automatic face extraction and processing
- **QR Code Generation**: Each student gets a unique QR code for photo uploads

### 📸 Image Processing (100 Grayscale Images per Student)
The system generates 100 unique grayscale variations for each student using:
1. **Original grayscale image**
2. **Brightness adjustments** (-40 to +40)
3. **Gaussian noise** (realistic variations)
4. **Rotation** (-15° to +15°)
5. **Histogram equalization** (lighting normalization)
6. **Gaussian blur** (different kernel sizes)
7. **Contrast adjustment** (alpha: 0.8-1.5)
8. **Salt and pepper noise** (random pixel variations)
9. **Horizontal flip** (mirror images)
10. **Scaling variations** (0.9x to 1.1x)
11. **Morphological operations** (open/close)

### ✅ Smart Attendance System
- **Schedule-Based Attendance**: Only allows attendance during scheduled class times
- **Face Recognition**: LBPH (Local Binary Pattern Histogram) algorithm
- **Automatic Detection**: Recognizes multiple students simultaneously
- **Confidence Scoring**: Shows recognition confidence for each student
- **Manual Override**: Backup manual attendance marking
- **Sunday Protection**: Prevents attendance marking on Sundays

### 📊 Comprehensive Reporting
- **Real-time Dashboard**: Live attendance statistics
- **Daily Summaries**: Present/absent counts and percentages
- **Date Range Reports**: Historical attendance analysis
- **Class-wise Filtering**: Filter reports by specific classes
- **CSV Export**: Download attendance reports

### 📱 QR Code Integration
- **Student QR Codes**: For mobile photo uploads
- **Attendance QR Codes**: Quick attendance marking
- **QR Scanner**: Built-in QR code scanning functionality

## 🚀 Installation & Setup

### Prerequisites
```bash
Python 3.9+
Webcam (for face recognition)
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- `streamlit` - Web interface
- `opencv-python` - Computer vision
- `opencv-contrib-python` - Face recognition algorithms
- `numpy` - Numerical operations
- `pandas` - Data manipulation
- `pillow` - Image processing
- `qrcode` - QR code generation
- `pyzbar` - QR code scanning
- `firebase-admin` - Database (optional)

### Run the Application
```bash
streamlit run main.py
```

## 📁 Project Structure
```
Ai_Attendance/
├── main.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── config/
│   └── firebase_config.json  # Firebase configuration (optional)
├── data/
│   ├── students/          # Student face images (100 per student)
│   │   └── {roll}_{name}/ # Individual student folders
│   ├── qr_codes/          # Generated QR codes
│   ├── temp/              # Temporary files
│   ├── classes.json       # Class data (local storage)
│   ├── students.json      # Student data (local storage)
│   └── attendance.json    # Attendance records (local storage)
└── modules/
    ├── attendance.py      # Attendance management
    ├── database.py        # Database operations
    ├── face_recognition.py # Face recognition engine
    └── qr_handler.py      # QR code operations
```

## 🎯 How to Use

### 1. Create Classes
1. Go to **Class Management**
2. Click **"Create New Class"**
3. Enter class details:
   - Class name
   - Description
   - Schedule days (Monday-Saturday)
   - Start and end times
4. Click **"Create Class"**

### 2. Register Students
1. Go to **Student Registration**
2. Fill in student details:
   - Name, roll number, email, phone
   - Select class
3. Capture student photo:
   - Use camera, upload file, or QR code
4. System automatically generates **100 grayscale variations**
5. Student gets a unique QR code

### 3. Mark Attendance
1. Go to **Attendance Marking**
2. System shows currently active classes
3. Select class for attendance
4. Use camera to capture group photo
5. System recognizes faces and marks attendance
6. Manual override available for corrections

### 4. View Reports
1. Go to **Reports**
2. Select date range and class filter
3. Generate comprehensive attendance reports
4. Download as CSV for external analysis

## 🔧 Technical Features

### Face Recognition Engine
- **Algorithm**: LBPH (Local Binary Pattern Histogram)
- **Training Data**: 100 grayscale variations per student
- **Recognition Threshold**: 80% confidence
- **Face Detection**: Haar Cascade Classifier
- **Image Size**: 100x100 pixels (standardized)

### Schedule Management
- **Time Matching**: Compares current time with class schedules
- **Day Matching**: Checks current day against class days
- **Active Class Detection**: Real-time identification of running classes
- **Automatic Validation**: Prevents attendance outside scheduled hours

### Data Storage
- **Local Storage**: JSON files (default)
- **Firebase Support**: Cloud database integration
- **Backup System**: Automatic data persistence
- **Data Validation**: Input validation and error handling

## 🛡️ Security Features
- **Sunday Protection**: No attendance on Sundays
- **Schedule Validation**: Only during class hours
- **Face Confidence**: Minimum confidence threshold
- **Data Integrity**: Automatic backup and validation

## 📈 Performance Optimization
- **Image Caching**: Efficient face loading
- **Batch Processing**: Multiple face recognition
- **Memory Management**: Optimized image storage
- **Real-time Processing**: Fast recognition algorithms

## 🔍 Troubleshooting

### Common Issues
1. **Face Recognition Not Working**
   - Install `opencv-contrib-python`
   - Ensure good lighting for photos
   - Check camera permissions

2. **No Classes Showing as Active**
   - Verify class schedule settings
   - Check current system time
   - Ensure class days include today

3. **Student Images Not Processing**
   - Check camera/file permissions
   - Ensure face is clearly visible
   - Try different lighting conditions

## 🎉 Success Metrics
- ✅ **100 grayscale images** generated per student
- ✅ **Schedule-based attendance** with day/time matching
- ✅ **Automatic face recognition** with confidence scoring
- ✅ **Real-time class status** detection
- ✅ **Comprehensive attendance records** with full audit trail

## 📞 Support
For issues or questions, check the troubleshooting section or review the code documentation in each module.

---
**Built with ❤️ using Streamlit, OpenCV, and Python**
