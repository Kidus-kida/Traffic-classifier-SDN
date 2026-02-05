# CHAPTER 3: SYSTEM DESIGN

## 3.1 System Architecture Overview

The proposed AI-powered traffic classification system follows a layered architecture that integrates Software-Defined Networking with machine learning. The architecture is designed to be modular, scalable, and fault-tolerant, enabling real-time traffic classification with automatic Quality of Service enforcement.

### 3.1.1 Architectural Layers

The system consists of four primary layers:

**1. Data Plane Layer**

The data plane layer comprises the network infrastructure responsible for packet forwarding:

- **Mininet Network Emulator**: Provides a virtual network environment for testing and development
- **Open vSwitch (OVS)**: Software-based switch implementing OpenFlow protocol
- **Network Topology**: Configurable topology with multiple hosts and switches
- **Flow Tables**: Store forwarding rules installed by the controller

**2. Control Plane Layer**

The control plane layer contains the SDN controller and traffic classification logic:

- **Ryu SDN Controller**: Manages network devices via OpenFlow protocol
- **Flow Monitor**: Collects statistics from switches every second
- **Traffic Classifier**: Core classification engine integrating ML models
- **Policy Manager**: Enforces QoS policies based on classification results

**3. Intelligence Layer**

The intelligence layer provides machine learning capabilities:

- **Feature Extraction Engine**: Computes statistical features from flow data
- **Model Manager**: Loads and manages ML models with fault tolerance
- **Inference Engine**: Performs real-time traffic classification
- **Model Repository**: Stores trained models for different algorithms

**4. Application Layer**

The application layer provides user interfaces and external integrations:

- **Web Dashboard**: Real-time visualization of traffic and classifications
- **REST API**: Programmatic access to system functionality
- **Metrics Exporter**: Exports performance metrics for monitoring
- **Configuration Manager**: Manages system configuration

### 3.1.2 Component Interaction

The components interact through well-defined interfaces:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │   REST API   │  │   Metrics    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                   Intelligence Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Feature    │  │    Model     │  │  Inference   │      │
│  │  Extractor   │─▶│   Manager    │─▶│    Engine    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Control Plane Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     Flow     │  │     QoS      │  │    Health    │      │
│  │   Manager    │  │   Manager    │  │   Monitor    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                  │                                 │
│  ┌──────▼──────────────────▼───────┐                        │
│  │   Ryu SDN Controller            │                        │
│  └──────┬──────────────────────────┘                        │
└─────────┼──────────────────────────────────────────────────┘
          │ OpenFlow Protocol
┌─────────▼──────────────────────────────────────────────────┐
│                     Data Plane Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Mininet Network Topology                 │  │
│  │  ┌────┐    ┌────────┐    ┌────┐                      │  │
│  │  │ h1 │────│   s1   │────│ h2 │                      │  │
│  │  └────┘    │  (OVS) │    └────┘                      │  │
│  │            └───┬────┘                                 │  │
│  │                │                                       │  │
│  │            ┌───▼────┐                                 │  │
│  │            │   h3   │                                 │  │
│  │            └────────┘                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.1.3 Design Principles

The architecture adheres to several key design principles:

**1. Separation of Concerns**

Each layer has distinct responsibilities:
- Data plane: Packet forwarding
- Control plane: Network management
- Intelligence layer: Traffic classification
- Application layer: User interaction

**2. Modularity**

Components are designed as independent modules with clear interfaces, enabling:
- Independent development and testing
- Easy replacement or upgrade of components
- Reusability across different deployments

**3. Fault Tolerance**

The system incorporates multiple fault tolerance mechanisms:
- Robust error handling for ML inference failures
- Health monitoring for component status
- Graceful degradation when components fail
- Automatic recovery from transient failures

**4. Scalability**

The architecture supports scaling through:
- Stateless component design where possible
- Efficient data structures for flow management
- Batch processing capabilities
- Distributed deployment options

**5. Configuration-Driven Design**

All system behavior is controlled through configuration:
- No hardcoded values
- Environment-specific configurations
- Runtime parameter adjustment
- Easy customization for different deployments

---

## 3.2 Component Design

### 3.2.1 SDN Controller Module

The SDN controller module manages communication with network devices and orchestrates the classification pipeline.

**Responsibilities:**
- Establish and maintain OpenFlow connections
- Collect flow statistics from switches
- Install flow rules based on classification results
- Handle network events (topology changes, link failures)

**Key Classes:**

```python
class TrafficClassifier:
    """Main controller application"""
    - __init__(algorithm, auto_install_rules)
    - start_ryu_controller()
    - process_flow_data(line)
    - display_classification_table()
    - run()
    - cleanup()
```

**Design Decisions:**

1. **Ryu Framework Selection**: Chosen for Python compatibility, comprehensive OpenFlow support, and active community
2. **Subprocess Management**: Ryu runs as subprocess for isolation and clean shutdown
3. **Event-Driven Processing**: Processes flow statistics as they arrive from switches
4. **Periodic Classification**: Classifies flows every 10 seconds to balance accuracy and performance

**Interfaces:**

- **Input**: Flow statistics from Ryu (stdout pipe)
- **Output**: Flow rules to switches (via Ryu API)
- **Configuration**: YAML-based controller settings
- **Logging**: Structured JSON logs

### 3.2.2 Traffic Monitoring Module

The traffic monitoring module tracks bidirectional network flows and computes statistics.

**Responsibilities:**
- Parse flow statistics from controller
- Maintain flow state (forward and reverse directions)
- Compute packet/byte rates and deltas
- Detect inactive flows
- Manage flow lifecycle

**Key Classes:**

```python
class Flow:
    """Bidirectional flow representation"""
    - __init__(time_start, datapath, inport, ethsrc, ethdst, outport, packets, bytes)
    - update_forward(packets, bytes, curr_time)
    - update_reverse(packets, bytes, curr_time)
    - assign_qos(traffic_type, qos_config)
    - get_flow_id()
    - is_active()

class FlowManager:
    """Flow collection manager"""
    - process_flow_stats(fields)
    - get_flow(flow_id)
    - get_all_flows()
    - get_active_flows()
    - clear_inactive_flows(max_age)
```

**Flow State Machine:**

```
[NEW] ──create──▶ [ACTIVE] ──timeout──▶ [INACTIVE] ──cleanup──▶ [REMOVED]
         │            │
         │            └──update──▶ [ACTIVE]
         │
         └──no_traffic──▶ [INACTIVE]
```

**Statistics Computed:**

For each direction (forward/reverse):
- Total packets and bytes
- Delta packets and bytes (since last update)
- Instantaneous packets per second (PPS)
- Average packets per second
- Instantaneous bytes per second (BPS)
- Average bytes per second

**Design Decisions:**

1. **Bidirectional Tracking**: Separate statistics for forward and reverse directions enable better classification
2. **Hash-Based Flow ID**: Uses hash of (datapath, src_mac, dst_mac) for efficient lookup
3. **Lazy Cleanup**: Inactive flows removed periodically rather than immediately
4. **Status Tracking**: Flows marked ACTIVE/INACTIVE based on recent activity

### 3.2.3 Feature Extraction Module

The feature extraction module transforms raw flow statistics into features suitable for machine learning.

**Responsibilities:**
- Extract 16 statistical features from flows
- Validate feature values (no NaN, Inf, or negative values)
- Convert features to numpy arrays for ML models
- Provide feature metadata (names, count)

**Key Classes:**

```python
@dataclass
class FlowFeatures:
    """Container for extracted features"""
    - forward_packets, forward_bytes, forward_delta_packets, ...
    - reverse_packets, reverse_bytes, reverse_delta_packets, ...
    - to_array() -> np.ndarray
    - to_list() -> List[float]
    - validate() -> bool

class FeatureExtractor:
    """Feature extraction engine"""
    - extract(flow) -> FlowFeatures
    - extract_safe(flow) -> Optional[FlowFeatures]
    - get_feature_names() -> List[str]
    - get_feature_count() -> int
```

**Feature Set (16 features):**

| # | Feature | Description | Direction |
|---|---------|-------------|-----------|
| 1 | forward_packets | Total packets sent | Forward |
| 2 | forward_bytes | Total bytes sent | Forward |
| 3 | forward_delta_packets | Packets since last update | Forward |
| 4 | forward_delta_bytes | Bytes since last update | Forward |
| 5 | forward_inst_pps | Instantaneous packet rate | Forward |
| 6 | forward_avg_pps | Average packet rate | Forward |
| 7 | forward_inst_bps | Instantaneous byte rate | Forward |
| 8 | forward_avg_bps | Average byte rate | Forward |
| 9-16 | reverse_* | Same metrics for reverse direction | Reverse |

**Feature Engineering Rationale:**

1. **Packet Counts**: Different traffic types have characteristic packet patterns
2. **Byte Counts**: Payload sizes vary by application (DNS: small, video: large)
3. **Rates**: Real-time traffic has consistent rates, bulk transfers are bursty
4. **Deltas**: Capture traffic dynamics and changes over time
5. **Bidirectional**: Many protocols have asymmetric patterns (HTTP: small request, large response)

**Validation Logic:**

```python
def validate(self) -> bool:
    arr = self.to_array()
    
    # Check for NaN or Inf
    if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
        return False
    
    # Check for negative values
    if np.any(arr < 0):
        return False
    
    return True
```

### 3.2.4 ML Inference Engine

The ML inference engine manages model loading and performs traffic classification with fault tolerance.

**Responsibilities:**
- Load trained ML models from disk
- Validate models before use
- Perform inference with confidence scoring
- Handle inference failures gracefully
- Provide fallback classification

**Key Classes:**

```python
@dataclass
class PredictionResult:
    """Prediction result container"""
    - traffic_type: str
    - confidence: float
    - raw_prediction: Any
    - fallback_used: bool

class ModelManager:
    """Model management with fault tolerance"""
    - __init__(config, logger)
    - load_model(algorithm) -> bool
    - predict(features) -> PredictionResult
    - validate_model() -> bool
    - get_model_info() -> Dict[str, Any]
```

**Inference Pipeline:**

```
Features ──▶ Model.predict() ──▶ Confidence ──▶ Result
```

**Confidence Scoring:**

For models with probability support (Logistic Regression, Random Forest, SVM):
```python
probabilities = model.predict_proba(features)
confidence = np.max(probabilities)
```

For models without probability support (K-Means):
```python
confidence = 0.85  # Default confidence
```

**Label Mapping (Unsupervised Models):**

K-Means produces cluster labels (0-9) that must be mapped to traffic types:

```python
label_map = {
    0: 'dns',
    1: 'game',
    2: 'ping',
    3: 'telnet',
    4: 'voice',
    5: 'video',
    6: 'http',
    7: 'https',
    8: 'ftp',
    9: 'ssh'
}
```

### 3.2.5 QoS Policy Enforcement

The QoS policy enforcement module assigns priorities and installs flow rules based on traffic classification.

**Responsibilities:**
- Assign QoS class based on traffic type
- Generate OpenFlow rules
- Install rules on switches
- Persist rules to storage
- Prevent duplicate installations
- Provide rule analytics

**Key Classes:**

```python
@dataclass
class FlowRule:
    """OpenFlow rule representation"""
    - timestamp, flow_id, src_mac, dst_mac
    - traffic_type, qos_class, priority, action
    - datapath, in_port, out_port

class QoSManager:
    """QoS policy manager"""
    - assign_qos_class(traffic_type) -> (qos_class, priority)
    - get_flow_action(traffic_type) -> str
    - should_install_rule(flow_id, confidence) -> bool
    - create_flow_rule(flow, traffic_type, confidence) -> FlowRule
    - install_flow_rule(rule) -> bool
    - get_statistics() -> Dict[str, Any]
```

**QoS Class Mapping:**

| Traffic Type | QoS Class | Priority | Action | Rationale |
|--------------|-----------|----------|--------|-----------|
| voice | REAL_TIME | 5 | PRIORITY_FORWARD | Latency-sensitive |
| video | REAL_TIME | 4 | PRIORITY_FORWARD | Bandwidth-intensive |
| game | INTERACTIVE | 3 | PRIORITY_FORWARD | Low-latency required |
| dns | NETWORK_CONTROL | 4 | PRIORITY_FORWARD | Critical service |
| ssh | INTERACTIVE | 3 | FORWARD | Interactive session |
| http | BEST_EFFORT | 2 | FORWARD | Standard web |
| https | BEST_EFFORT | 2 | FORWARD | Secure web |
| ftp | BULK | 1 | FORWARD | Large transfers |
| telnet | INTERACTIVE | 3 | FORWARD | Legacy protocol |
| ping | NETWORK_CONTROL | 4 | FORWARD | Network testing |

**Rule Installation Logic:**

```python
def should_install_rule(self, flow_id, confidence):
    # Already installed?
    if flow_id in self.installed_rules:
        return False
    
    # Confidence too low?
    if confidence < self.confidence_threshold:
        return False
    
    # Auto-install disabled?
    if not self.auto_install:
        return False
    
    return True
```

**Rule Persistence:**

Rules are persisted to JSON for:
- Audit trail
- Recovery after restart
- Analytics and reporting
- Debugging

**Rule Cleanup:**

Old rules are periodically removed:
```python
def clear_old_rules(self, max_age_seconds=3600):
    current_time = datetime.utcnow()
    to_remove = []
    
    for flow_id, rule in self.installed_rules.items():
        rule_time = datetime.fromisoformat(rule.timestamp)
        age = (current_time - rule_time).total_seconds()
        
        if age > max_age_seconds:
            to_remove.append(flow_id)
    
    for flow_id in to_remove:
        del self.installed_rules[flow_id]
```

### 3.2.6 Web Dashboard

The web dashboard provides real-time visualization of traffic classification results.

**Responsibilities:**
- Display active flows and classifications
- Show real-time metrics and statistics
- Provide system health status
- Enable configuration management
- Support WebSocket for live updates

**Technology Stack:**
- **Backend**: Flask web framework
- **Frontend**: HTML5, CSS3, JavaScript
- **Real-time**: Socket.IO for WebSocket communication
- **Visualization**: Chart.js for graphs

**Dashboard Views:**

1. **Overview**: System status, active flows, classification stats
2. **Flows**: Detailed flow table with filtering and sorting
3. **Analytics**: Charts showing traffic distribution over time
4. **QoS**: Installed rules and policy enforcement
5. **Health**: Component status and system metrics
6. **Configuration**: Runtime parameter adjustment

**REST API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System health check |
| `/flows` | GET | List active flows |
| `/flows/<id>` | GET | Get specific flow |
| `/stats` | GET | Classification statistics |
| `/qos/rules` | GET | List installed rules |
| `/config` | GET/PUT | Get/update configuration |
| `/metrics` | GET | Performance metrics |

**WebSocket Events:**

- `flow_classified`: New flow classification
- `rule_installed`: Flow rule installed
- `stats_update`: Statistics update
- `health_update`: Health status change

---

## 3.3 Data Flow Diagrams

### 3.3.1 Level 0 DFD (Context Diagram)

```
                    ┌─────────────────────┐
                    │   Network Admin     │
                    └──────────┬──────────┘
                               │
                               │ Configuration
                               │ Monitoring
                               ▼
┌──────────┐         ┌─────────────────────┐         ┌──────────┐
│          │  Packets│                     │ Flow    │          │
│ Network  │────────▶│  AI Traffic         │ Rules   │   SDN    │
│ Hosts    │         │  Classifier         │────────▶│ Switches │
│          │◀────────│                     │         │          │
└──────────┘ Traffic └─────────────────────┘         └──────────┘
                               │
                               │ Metrics
                               │ Logs
                               ▼
                    ┌─────────────────────┐
                    │  Monitoring System  │
                    └─────────────────────┘
```

### 3.3.2 Level 1 DFD (System Decomposition)

```
┌──────────┐
│ Switches │
└────┬─────┘
     │ Flow Stats
     ▼
┌─────────────────┐
│ Flow Monitor    │
└────┬────────────┘
     │ Flow Data
     ▼
┌─────────────────┐      ┌──────────────┐
│ Flow Manager    │─────▶│ Flow Storage │
└────┬────────────┘      └──────────────┘
     │ Flow Objects
     ▼
┌─────────────────┐
│ Feature         │
│ Extractor       │
└────┬────────────┘
     │ Features
     ▼
┌─────────────────┐      ┌──────────────┐
│ Model Manager   │◀─────│ Model Storage│
└────┬────────────┘      └──────────────┘
     │ Predictions
     ▼
┌─────────────────┐
│ QoS Manager     │
└────┬────────────┘
     │ Flow Rules
     ▼
┌─────────────────┐
│ Rule Installer  │
└────┬────────────┘
     │ OpenFlow Msgs
     ▼
┌─────────────────┐
│ Switches        │
└─────────────────┘
```

---

## 3.4 Sequence Diagrams

### 3.4.1 Flow Classification Sequence

```
User    Controller  FlowMgr  FeatureExt  ModelMgr  QoSMgr  Switch
 │          │          │          │          │        │       │
 │  Start   │          │          │          │        │       │
 │─────────▶│          │          │          │        │       │
 │          │ Connect  │          │          │        │       │
 │          │─────────────────────────────────────────────────▶│
 │          │          │          │          │        │       │
 │          │◀─────────────────────────────────────────────────│
 │          │ Flow Stats          │          │        │       │
 │          │          │          │          │        │       │
 │          │ Process  │          │          │        │       │
 │          │─────────▶│          │          │        │       │
 │          │          │ Extract  │          │        │       │
 │          │          │─────────▶│          │        │       │
 │          │          │          │ Predict  │        │       │
 │          │          │          │─────────▶│        │       │
 │          │          │          │          │ Assign │       │
 │          │          │          │          │───────▶│       │
 │          │          │          │          │        │Install│
 │          │          │          │          │        │──────▶│
 │          │          │          │          │        │       │
 │  Display │          │          │          │        │       │
 │◀─────────│          │          │          │        │       │
 │          │          │          │          │        │       │
```



---

## 3.5 Class Diagrams

### 3.5.1 Core Classes

```
┌─────────────────────────────┐
│   TrafficClassifier         │
├─────────────────────────────┤
│ - config                    │
│ - logger                    │
│ - flow_manager              │
│ - model_manager             │
│ - qos_manager               │
│ - health_monitor            │
├─────────────────────────────┤
│ + __init__(algorithm)       │
│ + start_ryu_controller()    │
│ + process_flow_data(line)   │
│ + display_table()           │
│ + run()                     │
│ + cleanup()                 │
└─────────────────────────────┘
         │
         │ uses
         ▼
┌─────────────────────────────┐
│   FlowManager               │
├─────────────────────────────┤
│ - flows: Dict[int, Flow]    │
│ - logger                    │
├─────────────────────────────┤
│ + process_flow_stats()      │
│ + get_flow(id)              │
│ + get_active_flows()        │
│ + clear_inactive_flows()    │
└─────────────────────────────┘
         │
         │ manages
         ▼
┌─────────────────────────────┐
│   Flow                      │
├─────────────────────────────┤
│ - forward_packets           │
│ - forward_bytes             │
│ - reverse_packets           │
│ - reverse_bytes             │
│ - predicted_type            │
│ - confidence                │
│ - qos_class                 │
├─────────────────────────────┤
│ + update_forward()          │
│ + update_reverse()          │
│ + assign_qos()              │
│ + is_active()               │
└─────────────────────────────┘
```

---

## 3.6 Database and Storage Design

### 3.6.1 Storage Requirements

The system uses file-based storage for:

1. **Configuration Files** (YAML)
   - default.yaml
   - development.yaml
   - production.yaml

2. **Model Files** (Pickle)
   - Randomforest.pkl
   - logistic.pkl
   - kneighbors.pkl
   - svc.pkl
   - gaussiannb.pkl
   - kmeans.pkl

3. **Training Data** (CSV)
   - dns_training_data.csv
   - http_training_data.csv
   - (one file per traffic type)

4. **Flow Rules** (JSON)
   - installed_rules.json

5. **Metrics** (JSON)
   - real_time_metrics.json

6. **Logs** (JSON Lines)
   - classifier.log
   - ryu.log

### 3.6.2 Data Schemas

**Flow Rule Schema:**
```json
{
  "timestamp": "2026-02-04T23:00:00Z",
  "flow_id": 123456789,
  "src_mac": "00:00:00:00:00:01",
  "dst_mac": "00:00:00:00:00:02",
  "traffic_type": "http",
  "qos_class": "BEST_EFFORT",
  "priority": 2,
  "action": "FORWARD",
  "datapath": "1",
  "in_port": "1",
  "out_port": "2"
}
```

**Metrics Schema:**
```json
{
  "timestamp": "2026-02-04T23:00:00Z",
  "total_flows": 150,
  "active_flows": 45,
  "classifications": {
    "http": 50,
    "https": 30,
    "dns": 20,
    "video": 15,
    "voice": 10
  },
  "performance": {
    "avg_latency_ms": 45,
    "p95_latency_ms": 78,
    "p99_latency_ms": 95
  }
}
```

---

## 3.7 User Interface Design

### 3.7.1 Dashboard Layout

```
┌────────────────────────────────────────────────────────────┐
│  AI Traffic Classifier Dashboard                     [≡]   │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Active  │  │  Total   │  │  Rules   │  │  Uptime  │  │
│  │  Flows   │  │  Class.  │  │ Installed│  │  2h 15m  │  │
│  │    45    │  │   1,234  │  │    89    │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Traffic Distribution (Last Hour)                   │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │ [Chart: Pie chart showing traffic types]    │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Active Flows                          [Filter ▼]   │  │
│  ├─────┬──────┬──────┬────────┬──────┬──────┬────────┤  │
│  │ ID  │ Src  │ Dst  │ Type   │ Conf │ QoS  │ Rule   │  │
│  ├─────┼──────┼──────┼────────┼──────┼──────┼────────┤  │
│  │ 123 │ h1   │ h2   │ http   │ 95%  │ BE   │ ✓      │  │
│  │ 124 │ h2   │ h3   │ video  │ 98%  │ RT   │ ✓      │  │
│  │ 125 │ h1   │ h3   │ dns    │ 92%  │ NC   │ ✓      │  │
│  └─────┴──────┴──────┴────────┴──────┴──────┴────────┘  │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 3.8 Security Design

### 3.8.1 Security Considerations

1. **Model Validation**
   - Verify model integrity before loading
   - Validate model predictions
   - Prevent malicious model injection

2. **Input Validation**
   - Validate all flow statistics
   - Sanitize configuration inputs
   - Prevent injection attacks

3. **Access Control**
   - Dashboard authentication (production)
   - API rate limiting
   - Role-based access control

4. **Data Privacy**
   - No payload inspection
   - MAC address anonymization option
   - Secure log storage

---

## 3.9 Deployment Architecture

### 3.9.1 Docker Deployment

```
┌─────────────────────────────────────────────────┐
│              Docker Host                         │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  sdn-classifier Container                │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │  Traffic Classifier Application    │  │  │
│  │  │  - Ryu Controller                  │  │  │
│  │  │  - ML Models                       │  │  │
│  │  │  - Classification Engine           │  │  │
│  │  └────────────────────────────────────┘  │  │
│  │  Ports: 6633 (OpenFlow), 9000 (HTTP)    │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  sdn-dashboard Container (Optional)      │  │
│  │  - Web Interface                         │  │
│  │  - Real-time Updates                     │  │
│  │  Port: 8080                              │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Monitoring Stack (Optional)             │  │
│  │  - Prometheus (9090)                     │  │
│  │  - Grafana (3000)                        │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  Volumes:                                        │
│  - logs/                                         │
│  - metrics/                                      │
│  - flow_rules/                                   │
│  - config/ (read-only)                           │
│  - models/ (read-only)                           │
└─────────────────────────────────────────────────┘
```

---

**END OF CHAPTER 3**

*This chapter has provided comprehensive system design covering architecture, components, data flows, interfaces, and deployment. Chapter 4 will detail the implementation of these designs.*
