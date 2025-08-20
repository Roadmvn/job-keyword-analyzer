-- Initialisation MySQL pour Job Keywords Analyzer (utilisé par Docker Compose)

CREATE DATABASE IF NOT EXISTS `job_analyzer` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'app_user'@'%' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON `job_analyzer`.* TO 'app_user'@'%';
FLUSH PRIVILEGES;


