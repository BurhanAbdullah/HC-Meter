SYSWATCH PRO Architecture

SYSWATCH PRO is designed around a modular security monitoring engine.

Core Components

core/
  engine.sh
  logger.sh
  alerts.sh
  threat_score.sh

Modules

modules/
  environment detection
  system health monitoring
  malware scanning
  network monitoring
  file integrity monitoring

Logs

logs/
  system.log
  intrusion.log

Database

database/
  integrity.db

The engine loads modules dynamically to allow extensibility.
