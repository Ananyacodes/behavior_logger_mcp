# Behavior System

A privacy-preserving, multi-device behavior monitoring system that keeps raw interaction logs on-device while sharing verifiable proof packets and compact model updates with a coordinator.

## Core Capabilities

- Captures keystrokes, mouse activity, app-switch events, and system metrics per device.
- Builds windowed feature vectors locally and computes anomaly scores with a neural autoencoder.
- Generates HMAC commitments over feature digest, anomaly score, model digest, and nonce.
- Verifies proofs centrally without receiving raw behavior data.
- Aggregates decentralized model updates in a federated-learning style.
- Persists coordinator state across restarts (registered devices, accepted reports, update buffers).

## Project Layout

```text
src/behavior_system/
  collector.py            Event capture (live + simulation)
  features.py             Windowed feature extraction
  neural.py               Autoencoder anomaly scoring
  crypto.py               Proof generation and verification
  federated.py            Coordinator logic + persistence
  runtime.py              On-device orchestration
  schemas.py              Shared dataclasses and wire formats

scripts/
  coordinator_server.py   TCP coordinator service
  demo_device.py          Device client (simulate/live)
  run_demo.py             Single-process demo
  train_local_model.py    Local baseline training utility

tests/
  test_system.py          Integration and persistence tests

data/
  coordinator_state.json  Coordinator persisted state (created at runtime)
```

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Validate

```powershell
python -m pytest tests/test_system.py
python scripts\run_demo.py
```

## Run As Split Processes

1. Start coordinator:

```powershell
python scripts\coordinator_server.py --host 127.0.0.1 --port 8765
```

Optional flags:

```powershell
python scripts\coordinator_server.py --host 127.0.0.1 --port 8765 --state-file data\coordinator_state.json
```

2. Start one or more devices:

```powershell
python scripts\demo_device.py --device-id laptop-a --secret demo-shared-secret --coordinator-host 127.0.0.1 --coordinator-port 8765 --simulate --rounds 5 --window-seconds 30
python scripts\demo_device.py --device-id laptop-b --secret demo-shared-secret --coordinator-host 127.0.0.1 --coordinator-port 8765 --simulate --rounds 5 --window-seconds 30
```

3. Query coordinator summary:

```powershell
python -c "import json,socket; s=socket.create_connection(('127.0.0.1',8765),timeout=5); s.sendall((json.dumps({'command':'summary'})+'\n').encode()); print(s.recv(8192).decode().strip()); s.close()"
```

## Coordinator API (Line-delimited JSON over TCP)

- `register`: register device and shared secret.
- `report`: submit a proof report.
- `summary`: retrieve accepted-report stats and aggregation metadata.
- `save`: flush coordinator state to disk immediately.
- `health`: service readiness probe.

## Security Notes

- Raw event logs stay on-device.
- Shared secrets are required for proof verification.
- Persisted coordinator state contains device secrets and should be protected with filesystem permissions.

## Current Status

- End-to-end demo works in single-process and split-process modes.
- Test suite covers feature extraction, proof verification, tamper rejection, aggregation shape, and state persistence.
