# 🚀 AI-Powered Real-Time Traffic Classification for Software-Defined Networks (SDN)

> A production-ready machine learning system for real-time network traffic classification in Software-Defined Networks (SDN), enabling intelligent Quality of Service (QoS) management while preserving user privacy.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![Machine Learning](https://img.shields.io/badge/Machine-Learning-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

---

# 📖 Overview

Traditional traffic classification methods rely on Deep Packet Inspection (DPI), which introduces privacy concerns, computational overhead, and encrypted traffic limitations.

This project applies **Machine Learning** to classify network traffic using **statistical flow features** instead of packet payloads, allowing accurate and privacy-preserving traffic identification.

The trained model is deployed through a **FastAPI backend**, while a **React dashboard** provides real-time visualization for network operators.

---

# ✨ Key Features

- Real-time network traffic classification
- Privacy-preserving (No Deep Packet Inspection)
- FastAPI REST API for inference
- React-based monitoring dashboard
- Machine Learning prediction engine
- SDN-ready architecture
- Lightweight deployment
- Scalable microservice design

---

# 🏗️ System Architecture

```text
                  Network Traffic
                         │
                         ▼
               Feature Extraction
                         │
                         ▼
               Machine Learning Model
                         │
                Classification Result
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      FastAPI REST API         Prediction Logs
            │
            ▼
      React Dashboard
            │
            ▼
     Network Administrator
```

---

# 🛠️ Technology Stack

## Machine Learning

- Python
- Scikit-Learn
- Pandas
- NumPy

## Backend

- FastAPI
- Uvicorn

## Frontend

- React
- JavaScript
- HTML
- CSS

## Development

- Git
- GitHub

---

# 📂 Project Structure

```
Traffic-classifier-SDN/

├── backend/
│   ├── app/
│   ├── models/
│   ├── api/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── dataset/
│
├── notebooks/
│
├── model/
│
└── README.md
```

---

# 🧠 Machine Learning Pipeline

1. Dataset Collection
2. Data Cleaning
3. Feature Engineering
4. Model Training
5. Hyperparameter Optimization
6. Model Evaluation
7. Model Serialization
8. FastAPI Deployment
9. Real-Time Prediction

---

# 📊 Model Performance

| Metric | Result |
|---------|---------|
| Accuracy | XX% |
| Precision | XX% |
| Recall | XX% |
| F1 Score | XX% |
| Average Prediction Time | <100 ms |

> Replace the placeholder values with your actual evaluation results.

---

# 📡 REST API

## Predict Traffic

```http
POST /predict
```

Example Request

```json
{
    "packet_size": 1450,
    "flow_duration": 0.65,
    "protocol": 6
}
```

Example Response

```json
{
    "prediction": "Video Streaming",
    "confidence": 0.98
}
```

---

# 💻 Installation

## Clone Repository

```bash
git clone https://github.com/Kidus-kida/Traffic-classifier-SDN.git
```

Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 📷 Screenshots

Add screenshots here:

- Dashboard
- Prediction Result
- API Response
- Model Evaluation

---

# 🔒 Privacy

Unlike traditional Deep Packet Inspection (DPI), this system classifies traffic using statistical flow features without inspecting packet payloads, improving user privacy while maintaining high classification accuracy.

---

# 🚀 Future Improvements

- Deep Learning models
- Online model retraining
- Docker deployment
- Kubernetes scaling
- Grafana monitoring
- OpenFlow controller integration
- Multi-model ensemble learning

---

# 👨‍💻 Author

**Kidus K**

Software Engineer | AI & Machine Learning | Full Stack Developer | IoT Enthusiast

GitHub:
https://github.com/Kidus-kida

LinkedIn:
(Add your LinkedIn URL)

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.
