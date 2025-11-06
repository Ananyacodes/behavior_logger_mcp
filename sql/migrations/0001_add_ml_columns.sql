-- Migration: add ML/anomaly detection columns to behavior_logs and ensure anomaly_stats exists
-- Safe for MySQL 8.0.16+ (uses ADD COLUMN IF NOT EXISTS)

ALTER TABLE behavior_logs
  ADD COLUMN IF NOT EXISTS anomaly_score DOUBLE NULL,
  ADD COLUMN IF NOT EXISTS detector VARCHAR(64) NULL,
  ADD COLUMN IF NOT EXISTS model_version VARCHAR(32) NULL,
  ADD COLUMN IF NOT EXISTS detected_by VARCHAR(32) NULL;

CREATE TABLE IF NOT EXISTS anomaly_stats (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  window_start DATETIME NOT NULL,
  window_end DATETIME NOT NULL,
  total_events INT DEFAULT 0,
  anomalies INT DEFAULT 0,
  avg_anomaly_score DOUBLE DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
