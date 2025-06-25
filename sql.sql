-- SQL Script for the WildWaste application database
-- Database: wildwaste_db

-- Create the 'users' table to store user information.
-- We'll store a hashed version of the password for security.
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create the 'trash_reports' table to store information about collected trash.
-- It links back to the user who reported it via the 'user_id' foreign key.
-- The image is stored as a LONGTEXT to accommodate the Base64 encoded string.
CREATE TABLE IF NOT EXISTS `trash_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `latitude` DOUBLE NOT NULL,
    `longitude` DOUBLE NOT NULL,
    `trash_type` VARCHAR(100) NOT NULL,
    `quantity` VARCHAR(100) NOT NULL,
    `image_base64` LONGTEXT, -- Using LONGTEXT to store the base64 string of the image
    `notes` TEXT,
    `reported_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT * FROM trash_reports;