# 🔐 SecureHomeAI

## AI-Powered Secure Home Authentication and Access Control System

SecureHomeAI is our Major Project focused on building an **AI-powered home security and biometric authentication system**.

The project started with the goal of creating a system that does more than simple face recognition. The authentication process is designed as a layered security pipeline:

```text
Camera
   ↓
Liveness Verification
   ↓
Face Recognition
   ↓
Access Control
   ↓
Security Logging
   ↓
Future: Physical Door / IoT Control
```

The main idea is that a person should not receive access simply because their face matches a registered user. The system first verifies that a real person is actively responding to a liveness challenge, and only then performs biometric face recognition.

---

# 🎯 Project Goal

The long-term goal of SecureHomeAI is to develop a complete smart-home security system that can:

- Detect a person using a camera
- Verify that the person is physically present
- Perform biometric face recognition
- Identify registered users
- Reject unknown users
- Make an access decision
- Record authentication events
- Provide a foundation for a physical electronic door-lock / IoT system
- Eventually provide backend and frontend interfaces for monitoring and management

The project is being developed incrementally so that each major component can be tested independently before being integrated into the complete system.

---

# 🏗️ Development Approach

We are following a modular development process.

Instead of immediately building the complete application, the system is being developed layer by layer:

```text
1. Camera / Vision
        ↓
2. Face Detection
        ↓
3. Liveness Detection
        ↓
4. Liveness Engine
        ↓
5. Face Registration
        ↓
6. Face Recognition
        ↓
7. Multi-User Recognition
        ↓
8. Access Control
        ↓
9. Security Logging
        ↓
10. Integrated Authentication Pipeline
        ↓
Future:
Backend + Frontend + IoT Door Control
```

This approach makes it easier to test, debug, document, and improve each part of the project.

---

# 🧠 System Architecture

The current working architecture is:

```text
                         ┌───────────────┐
                         │    CAMERA     │
                         └───────┬───────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ LIVENESS VERIFICATION  │
                    │                        │
                    │  • Blink Detection     │
                    │  • Head Pose Detection │
                    │  • Random Challenge     │
                    └───────────┬────────────┘
                                │
                         LIVENESS PASS
                                │
                                ▼
                    ┌────────────────────────┐
                    │    FACE RECOGNITION    │
                    │                        │
                    │ • Face Detection       │
                    │ • Embedding Generation │
                    │ • Multi-user Matching  │
                    └───────────┬────────────┘
                                │
                         Recognized / Unknown
                                │
                                ▼
                    ┌────────────────────────┐
                    │     ACCESS CONTROL     │
                    │                        │
                    │ Liveness + Recognition │
                    └───────────┬────────────┘
                                │
                         ┌──────┴──────┐
                         │             │
                         ▼             ▼
                     GRANTED        DENIED
                         │             │
                         └──────┬──────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │    SECURITY LOGGER     │
                    │                        │
                    │ • Timestamp            │
                    │ • User                 │
                    │ • Liveness result      │
                    │ • Recognition result   │
                    │ • Access result        │
                    └────────────────────────┘
```

---

# 📌 What We Started With

At the beginning of the AI-engine development, the project had the basic structure for a larger SecureHomeAI system.

The repository contains areas for:

```text
SecureHomeAI/
├── ai-engine/
├── backend/
├── frontend/
└── docs/
```

The initial work focused on the **AI authentication core**, because this is the central security component of the project.

The first objective was to make the camera and computer-vision components work reliably before connecting them to access control, logging, backend services, frontend interfaces, or hardware.

---

# 🚀 Development Progress

## Phase 1 — Computer Vision Foundation

The first stage focused on getting camera-based computer vision working.

The project includes:

```text
ai-engine/vision/
├── camera_test.py
├── yolo_detection.py
└── yolov8n.pt
```

This established the initial computer-vision foundation and provided a place for future object/person detection work.

---

# 👁️ Phase 2 — Face and Landmark Processing

The next stage focused on facial analysis.

The project introduced face-related modules including:

```text
face_detection.py
head_pose.py
liveness_detection.py
```

The purpose was to move from simply detecting a camera image toward understanding the user's face and facial movement.

---

# 👀 Phase 3 — Blink Detection

One of the first liveness components implemented was blink detection.

The system uses facial landmarks and the **Eye Aspect Ratio (EAR)** to determine whether the user's eyes have closed and reopened.

Conceptually:

```text
Camera
   ↓
Face Landmarks
   ↓
Eye Landmarks
   ↓
Eye Aspect Ratio
   ↓
Blink Detection
```

The system was tested with real camera input and successfully detected blinks.

This became the first active challenge in the liveness-verification process.

---

# 🧭 Phase 4 — Head Pose Detection

After blink detection, head movement detection was implemented.

The system analyzes the relative position of facial landmarks and determines whether the user moves their head in a required direction.

Supported directions:

```text
LEFT
RIGHT
UP
DOWN
```

The head-pose module also introduced:

- Baseline calibration
- Relative nose position
- Eye-distance normalization
- Direction thresholds
- Random movement challenges

The calibration process helps the system determine the user's neutral head position before checking movement.

---

# 🎲 Phase 5 — Random Head Challenge

The head-pose system was then turned into a challenge-response mechanism.

Instead of always asking the same movement, the system randomly selects:

```text
LEFT
RIGHT
UP
DOWN
```

Example:

```text
Challenge: RIGHT
```

The user must perform the requested movement.

If the movement is detected:

```text
Head challenge passed: RIGHT
```

This was an important step because the project moved from simple face analysis toward active liveness verification.

---

# 🔐 Phase 6 — Combined Liveness Engine

Blink detection and head-pose challenge were then combined into a reusable liveness engine.

The resulting flow became:

```text
START
  ↓
Blink Challenge
  ↓
Blink Detected
  ↓
Head Calibration
  ↓
Random Head Challenge
  ↓
Challenge Passed
  ↓
LIVENESS VERIFIED
```

The reusable module is:

```text
liveness_engine.py
```

The main function is:

```text
run_liveness_check()
```

It returns whether the liveness verification succeeded.

This allowed liveness detection to become a component that could be called by the main authentication system rather than being only a standalone test script.

---

# 🧑‍💻 Phase 7 — Face Registration

After liveness was working, the project moved to biometric registration.

InsightFace was introduced for face recognition and embedding generation.

The registration process captures the user's face and generates a biometric embedding.

The first registration system supported a single user.

The registered information was stored locally.

The original database structure contained:

```text
name
embedding
```

This established the biometric identity database for the project.

---

# 🧠 Phase 8 — Face Recognition

The next step was to recognize a registered user from the camera.

The recognition system:

1. Opens the camera
2. Detects a face
3. Generates a face embedding
4. Loads registered biometric embeddings
5. Compares the embeddings
6. Calculates similarity
7. Determines whether the person is recognized

Conceptually:

```text
Camera
   ↓
Face Detection
   ↓
Face Embedding
   ↓
Compare with Registered Embeddings
   ↓
Similarity Score
   ↓
Known / Unknown
```

The recognition threshold is currently configured in:

```text
recognize_user.py
```

The project successfully recognized registered users using real camera input.

---

# 🔄 Phase 9 — Reusable Face Recognition Module

The recognition logic was refactored into a reusable function:

```text
run_face_recognition()
```

This was important because the main authentication program could now call face recognition as a service/component instead of duplicating the recognition code.

The recognition module returns the authentication result and the recognized user identity.

---

# 👥 Phase 10 — Multi-User Support

The project was then upgraded from a single-user database to a multi-user biometric database.

Previously the database contained one user object.

It was migrated to a list-based structure:

```json
[
    {
        "name": "User 1",
        "embedding": [...]
    },
    {
        "name": "User 2",
        "embedding": [...]
    }
]
```

The registration system was updated to:

- Ask for the user's name
- Check whether the name already exists
- Capture the new user's face
- Generate the embedding
- Append the new user
- Save the updated database

The recognition system was updated to compare a detected face against all registered users.

This means the system can now identify the best matching registered person.

---

# 🧪 Multi-User Test

The current development database has been tested with multiple users.

Example:

```text
Registered users: 2
```

A successful recognition test produced:

```text
FACE RECOGNIZED
User: Thirupathi Reddy
Similarity: 0.838
ACCESS GRANTED
```

The full integrated pipeline later recognized the same user with a similarity of approximately:

```text
0.836
```

This confirms that the multi-user recognition functionality is working.

---

# 🚦 Phase 11 — Access Control

After face recognition was working, an explicit access-control module was introduced.

File:

```text
access_control.py
```

The access decision is based on two authentication conditions:

```text
Liveness
    +
Face Recognition
```

Access is granted only if both succeed.

```text
Liveness PASS
       +
Recognition PASS
       ↓
ACCESS GRANTED
```

Otherwise:

```text
ACCESS DENIED
```

The access-control module also provides a reason for the decision.

Example:

```text
ACCESS: GRANTED
Reason: Liveness and face recognition passed
```

This separates the security decision from the face-recognition implementation.

---

# 📝 Phase 12 — Security Logging

The next major component added was security event logging.

File:

```text
security_logger.py
```

Authentication attempts are stored in:

```text
database/security_logs.json
```

Current log information includes:

```text
timestamp
user
liveness
face_recognition
access
```

Example:

```json
{
    "timestamp": "2026-10-05 21:47:xx",
    "user": "Thirupathi Reddy",
    "liveness": "PASS",
    "face_recognition": "PASS",
    "access": "GRANTED"
}
```

This gives the project an audit trail of authentication events.

---

# 🔗 Phase 13 — Complete Authentication Integration

The individual modules were then connected together.

The main controller is:

```text
main.py
```

The complete flow is now:

```text
STEP 1
LIVENESS VERIFICATION
        ↓
STEP 2
FACE RECOGNITION
        ↓
STEP 3
ACCESS CONTROL
        ↓
STEP 4
SECURITY LOGGING
```

The complete system has been successfully tested.

Example successful flow:

```text
STEP 1: LIVENESS VERIFICATION

Blink detected!

Challenge: RIGHT
Head challenge passed: RIGHT

LIVENESS VERIFIED
```

Then:

```text
STEP 2: FACE RECOGNITION

Registered users: 2

FACE RECOGNIZED
User: Thirupathi Reddy
Similarity: 0.836
ACCESS GRANTED
```

Then:

```text
STEP 3: ACCESS CONTROL

ACCESS: GRANTED
Reason: Liveness and face recognition passed
```

Finally:

```text
STEP 4: SECURITY LOGGING

Security event logged.

AUTHENTICATION COMPLETE
```

This represents the current working AI authentication core.

---

# 🧩 Current Module Responsibilities

## `camera_test.py`

Used for testing camera access and basic camera functionality.

---

## `face_detection.py`

Contains face-detection related functionality.

---

## `head_pose.py`

Responsible for head-pose analysis and directional challenge testing.

Supported directions:

```text
LEFT
RIGHT
UP
DOWN
```

---

## `liveness_detection.py`

Contains blink/liveness-related facial landmark processing.

---

## `liveness_engine.py`

Combines the liveness stages into a reusable authentication component.

Main responsibility:

```text
Blink
+
Random Head Challenge
=
Liveness Verification
```

---

## `register_user.py`

Registers new users and stores their biometric embeddings.

Current functionality includes:

- User name input
- Duplicate-name checking
- Camera capture
- Face detection
- Face embedding generation
- Multi-user database update

---

## `recognize_user.py`

Performs multi-user face recognition.

Main responsibilities:

- Load registered users
- Detect faces
- Generate embeddings
- Compare embeddings
- Find the best match
- Return recognized identity

---

## `access_control.py`

Makes the final access decision based on authentication results.

---

## `security_logger.py`

Stores authentication events.

---

## `main.py`

Controls the complete authentication pipeline.

---

# 📁 Current Project Structure

```text
SecureHomeAI/
│
├── README.md
│
├── ai-engine/
│   │
│   ├── requirements.txt
│   ├── venv/
│   │
│   ├── face-recognition/
│   │   ├── face_detection.py
│   │   ├── head_pose.py
│   │   ├── liveness_detection.py
│   │   ├── liveness_engine.py
│   │   ├── recognize_user.py
│   │   ├── register_user.py
│   │   ├── security_logger.py
│   │   ├── access_control.py
│   │   ├── main.py
│   │   ├── utils.py
│   │   │
│   │   └── database/
│   │       ├── users.json
│   │       └── security_logs.json
│   │
│   └── vision/
│       ├── camera_test.py
│       ├── yolo_detection.py
│       └── yolov8n.pt
│
├── backend/
│
├── frontend/
│
└── docs/
```

---

# 🧰 Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Computer Vision | OpenCV |
| Face Recognition | InsightFace |
| Face Embeddings | InsightFace |
| Facial Landmarks / Liveness | MediaPipe |
| Numerical Processing | NumPy |
| Local Data Storage | JSON |
| Version Control | Git |
| Repository | GitHub |

---

# ▶️ How to Run the Current System

## 1. Clone the repository

```bash
git clone https://github.com/Shivamruth/SecureHomeAI.git
cd SecureHomeAI
```

## 2. Enter the AI engine

```bash
cd ai-engine
```

## 3. Activate the virtual environment

Windows PowerShell:

```powershell
venv\Scripts\activate
```

## 4. Enter the face-recognition module

```powershell
cd face-recognition
```

## 5. Run the complete authentication system

```powershell
python main.py
```

---

# 👤 Registering a New User

Run:

```powershell
python register_user.py
```

The program asks:

```text
Enter user name:
```

Then the camera opens.

The user looks at the camera and presses:

```text
R
```

to register.

Press:

```text
Q
```

to cancel.

The new biometric identity is appended to:

```text
database/users.json
```

---

# 🔎 Testing Face Recognition Separately

Run:

```powershell
python recognize_user.py
```

The system loads all registered users and attempts to identify the person in front of the camera.

---

# 🔐 Running the Complete Authentication System

Run:

```powershell
python main.py
```

The system performs:

```text
1. Blink
2. Random head challenge
3. Face recognition
4. Access decision
5. Security logging
```

---

# 🧪 Development Milestones

| Milestone | Description | Status |
|---|---|---|
| M3 | Head pose detection | ✅ PASS |
| M4 | Combined liveness | ✅ PASS |
| M5.1 | Registration + recognition | ✅ PASS |
| M5.2 | Liveness refactor | ✅ PASS |
| M5.3 | Reusable recognition | ✅ PASS |
| M5.4 | Integrated main pipeline | ✅ PASS |
| M6.1 | Security logger | ✅ PASS |
| M6.2 | Logging integration | ✅ PASS |
| M7.1 | Access-control unit test | ✅ PASS |
| M7.2 | Access control integration | ✅ PASS |
| M8 | Multi-user biometric support | ✅ PASS |
| M8.1 | Multi-user registration | ✅ PASS |
| M8.2 | Identity-aware complete pipeline | ✅ PASS |
| M9 | Security / negative testing | 🔄 NEXT |

---

# 🧪 Current Testing Status

Completed:

- [x] Camera access
- [x] Face detection
- [x] Blink detection
- [x] Head-pose detection
- [x] Random head challenges
- [x] Liveness engine
- [x] User registration
- [x] Face recognition
- [x] Multi-user registration
- [x] Multi-user recognition
- [x] Access-control logic
- [x] Security logging
- [x] Complete authentication pipeline
- [x] Identity-aware authentication
- [x] Identity-aware security logging

Next testing:

- [ ] Unknown-person rejection
- [ ] Liveness-failure rejection
- [ ] Multi-user negative testing
- [ ] Authentication edge cases
- [ ] Security-event improvements

---

# ⚠️ Current Known Warnings

## CUDA / ONNX Runtime

On systems without the required CUDA runtime libraries, InsightFace may display an error similar to:

```text
onnxruntime_providers_cuda.dll
cublasLt64_13.dll is missing
```

The system currently falls back to:

```text
CPUExecutionProvider
```

The authentication pipeline has been successfully tested using CPU inference.

GPU/CUDA optimization can be addressed later.

---

## MediaPipe / Protobuf Warnings

The current environment may display warnings related to:

- TensorFlow Lite XNNPACK
- MediaPipe feedback manager
- Protobuf deprecations
- InsightFace face-alignment deprecations

These warnings have not prevented the current authentication pipeline from operating successfully.

---

# 🔒 Security and Privacy

Biometric embeddings are sensitive information.

For this reason, local biometric and runtime JSON files are excluded from Git tracking through `.gitignore`.

The repository should **not contain real user biometric embeddings**.

The local database files are intended for development/testing on the local machine.

---

# ⚠️ Liveness Security Limitation

The current liveness system uses challenge-response mechanisms including:

- Blink detection
- Random head movement

This improves security compared with face recognition alone, but it should **not be described as a complete defense against all presentation attacks**.

Advanced attacks involving sophisticated replay videos, deepfakes, or other presentation attacks may require additional anti-spoofing techniques.

Future versions can improve liveness security using additional signals and dedicated anti-spoofing models.

---

# 🗺️ Future Development Roadmap

The current AI authentication core is working. The next stages will expand the project into a more complete smart-home security platform.

## Phase 14 — Security Testing

- [ ] Test unknown users
- [ ] Test liveness failures
- [ ] Test recognition failures
- [ ] Test multiple registered users
- [ ] Test edge cases
- [ ] Improve authentication event details

---

## Phase 15 — Improved Security

Potential improvements:

- [ ] Stronger anti-spoofing
- [ ] More robust liveness detection
- [ ] Better threshold calibration
- [ ] Failed-attempt tracking
- [ ] Security alerts
- [ ] Rate limiting
- [ ] Improved biometric data protection

---

## Phase 16 — Backend

Planned backend components:

```text
Backend API
     ↓
User Management
     ↓
Authentication Service
     ↓
Security Events
     ↓
Database
```

Possible future functionality:

- [ ] User management API
- [ ] Authentication API
- [ ] Security-log API
- [ ] Database integration
- [ ] User registration management
- [ ] Access history

---

## Phase 17 — Frontend

A frontend dashboard is planned for monitoring and management.

Possible features:

```text
Dashboard
├── Authentication Status
├── Registered Users
├── Access History
├── Security Events
├── Alerts
└── System Status
```

---

## Phase 18 — IoT / Physical Access Control

The long-term goal is to connect the AI authentication system to a physical access-control mechanism.

Possible architecture:

```text
Camera
   ↓
AI Authentication
   ↓
Access Decision
   ↓
Backend / Controller
   ↓
Relay / Electronic Lock
   ↓
Door
```

Potential components:

- [ ] Relay integration
- [ ] Electronic door lock
- [ ] Door-state sensor
- [ ] Microcontroller integration
- [ ] Physical access logging

---

# 📈 Current Project Status

```text
┌──────────────────────────────────────┐
│       SECUREHOMEAI CURRENT STATUS    │
├──────────────────────────────────────┤
│ Camera                    ✅          │
│ Face Detection            ✅          │
│ Blink Detection           ✅          │
│ Head Pose Detection       ✅          │
│ Random Liveness Challenge ✅          │
│ Liveness Engine           ✅          │
│ Face Registration         ✅          │
│ Face Recognition          ✅          │
│ Multi-User Support        ✅          │
│ Access Control            ✅          │
│ Security Logging          ✅          │
│ Full AI Authentication    ✅          │
│ Security Testing          🔄          │
│ Backend                   🔜          │
│ Frontend                  🔜          │
│ IoT / Door Lock           🔜          │
└──────────────────────────────────────┘
```

---

# 👥 Team Development

SecureHomeAI is being developed as a modular team project.

### AI / Computer Vision

Responsible for:

```text
Face Detection
Liveness Detection
Face Recognition
Biometric Processing
Authentication Pipeline
```

### Backend

Planned responsibilities:

```text
APIs
Database
User Management
Authentication Services
Security Events
```

### Frontend

Planned responsibilities:

```text
Dashboard
User Interface
Authentication Status
Security Logs
Alerts
```

### Hardware / IoT

Planned responsibilities:

```text
Electronic Lock
Relay
Sensors
Microcontroller
Physical Door Control
```

---

# 📌 Important Development Principle

The project is being developed in stages.

A feature is considered part of the working system only after it has been implemented and tested.

Current working core:

```text
Camera
   ↓
Blink
   ↓
Random Head Challenge
   ↓
Liveness Verified
   ↓
Multi-User Face Recognition
   ↓
Identity
   ↓
Access Control
   ↓
Security Logging
```

This AI authentication core forms the foundation for the future backend, frontend, and physical access-control layers.

---

# 📜 Project Status

**SecureHomeAI is currently under active development as an academic Major Project.**

The **AI-based authentication core is operational**, while security testing, backend, frontend, and physical IoT access-control components remain part of the planned development roadmap.


