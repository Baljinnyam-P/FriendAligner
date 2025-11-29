-- MySQL Workbench Forward Engineering
-- 3 version of team's schema with corrected foreign key references

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';


-- -----------------------------------------------------
-- Schema FriendAligner
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `FriendAligner` DEFAULT CHARACTER SET utf8 ;
USE `FriendAligner` ;

-- -----------------------------------------------------
-- Table `FriendAligner`.`Users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(45) NULL,
  `password` VARCHAR(255) NULL,
  `first_name` VARCHAR(45) NULL,
  `last_name` VARCHAR(45) NULL,
  `phone_number` VARCHAR(45) NULL,
  `is_admin` BOOLEAN DEFAULT FALSE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC) VISIBLE,
  PRIMARY KEY (`user_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `FriendAligner`.`Groups`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Groups` (
  `group_id` INT NOT NULL AUTO_INCREMENT,
  `organizer_id` INT NOT NULL,
  `group_name` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`group_id`),
  INDEX `FK_organizer_id_idx` (`organizer_id` ASC) VISIBLE,
  CONSTRAINT `FK_Organizer_id`
    FOREIGN KEY (`organizer_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `FriendAligner`.`Group Members`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Group Members` (
  `gm_id` INT NOT NULL AUTO_INCREMENT,
  `group_id` INT NULL,
  `user_id` INT NULL,
  `role` VARCHAR(45) NULL,
  PRIMARY KEY (`gm_id`),
  INDEX `FK_group_id_idx` (`group_id` ASC) VISIBLE,
  INDEX `FK_user_id_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `FK_gm_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `FriendAligner`.`Groups` (`group_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `FK_gm_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `FriendAligner`.`Calendar`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Calendar` (
  `calendar_id` INT NOT NULL AUTO_INCREMENT,
  `type` ENUM('personal', 'group') NOT NULL,
  `owner_user_id` INT NULL,
  `group_id` INT NULL,
  `name` VARCHAR(100) NULL,
  `month` INT NULL,
  `year` INT NULL,
  PRIMARY KEY (`calendar_id`),
  INDEX `FK_owner_user_id_idx` (`owner_user_id` ASC),
  INDEX `FK_group_id_idx` (`group_id` ASC),
  CONSTRAINT `FK_calendar_owner_user_id`
    FOREIGN KEY (`owner_user_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `FK_calendar_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `FriendAligner`.`Groups` (`group_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `FriendAligner`.`Event Finder`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Event Finder` (
  `eventFinder_id` INT NOT NULL AUTO_INCREMENT,
  `group_id` INT NULL,
  `calendar_id` INT NULL,
  `zip_code` VARCHAR(45) NULL,
  PRIMARY KEY (`eventFinder_id`),
  INDEX `FK_group_id_idx` (`group_id` ASC) VISIBLE,
  INDEX `FK_calendar_id_idx` (`calendar_id` ASC) VISIBLE,
  CONSTRAINT `FK_eventfinder_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `FriendAligner`.`Groups` (`group_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `FK_eventfinder_calendar_id`
    FOREIGN KEY (`calendar_id`)
    REFERENCES `FriendAligner`.`Calendar` (`calendar_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `FriendAligner`.`Availability`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Availability` (
  `availability_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `calendar_id` INT NOT NULL,
  `date` DATE NOT NULL,
  `status` VARCHAR(32) NOT NULL,
  `description` VARCHAR(255) NULL,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`availability_id`),
  INDEX `FK_user_id_idx` (`user_id` ASC),
  INDEX `FK_calendar_id_idx` (`calendar_id` ASC),
  CONSTRAINT `FK_availability_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `FK_availability_calendar_id`
    FOREIGN KEY (`calendar_id`)
    REFERENCES `FriendAligner`.`Calendar` (`calendar_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `FriendAligner`.`Invites`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Invites` (
  `invite_id` INT NOT NULL AUTO_INCREMENT,
  `group_id` INT NOT NULL,
  `invited_user_id` INT NULL,
  `sender_id` INT NOT NULL,
  `email` VARCHAR(120) NULL,
  `phone_number` VARCHAR(45) NULL,
  `status` VARCHAR(20) DEFAULT 'pending',
  `token` VARCHAR(64) UNIQUE,
  `date` DATE NULL,
  PRIMARY KEY (`invite_id`),
  INDEX `FK_invite_group_id_idx` (`group_id` ASC),
  INDEX `FK_invite_invited_user_id_idx` (`invited_user_id` ASC),
  INDEX `FK_invite_sender_id_idx` (`sender_id` ASC),
  CONSTRAINT `FK_invite_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `FriendAligner`.`Groups` (`group_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `FK_invite_invited_user_id`
    FOREIGN KEY (`invited_user_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `FK_invite_sender_id`
    FOREIGN KEY (`sender_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `FriendAligner`.`Events` 
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Events` (
  `event_id` INT NOT NULL AUTO_INCREMENT,
  `calendar_id` INT NOT NULL,
  `group_id` INT NULL,
  `created_by_user_id` INT NOT NULL,
  `name` VARCHAR(120) NOT NULL,
  `description` TEXT NULL,
  `date` DATE NOT NULL,
  `start_time` DATETIME NULL,
  `end_time` DATETIME NULL,
  `address` VARCHAR(255) NULL,
  `location_name` VARCHAR(120) NULL,
  `image_url` VARCHAR(255) NULL,
  `google_maps_url` VARCHAR(255) NULL,
  `place_url` VARCHAR(255) NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'suggested', --suggested or finalized
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`event_id`),
  INDEX `FK_events_calendar_id_idx` (`calendar_id` ASC),
  INDEX `FK_events_group_id_idx` (`group_id` ASC),
  INDEX `FK_events_creator_id_idx` (`created_by_user_id` ASC),
  CONSTRAINT `FK_events_calendar_id`
    FOREIGN KEY (`calendar_id`)
    REFERENCES `FriendAligner`.`Calendar` (`calendar_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `FK_events_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `FriendAligner`.`Groups` (`group_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT `FK_events_creator_id`
    FOREIGN KEY (`created_by_user_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `FriendAligner`.`Notifications`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`Notifications` (
  `notification_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `message` VARCHAR(255) NOT NULL,
  `type` VARCHAR(30),
  `event_id` INT NULL,
  `scheduled_at` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `read` BOOLEAN DEFAULT FALSE,
  `sent` BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (`notification_id`),
  INDEX `FK_notification_user_id_idx` (`user_id` ASC),
  INDEX `FK_notification_event_id_idx` (`event_id` ASC),
  CONSTRAINT `FK_notification_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `FK_notification_event_id`
    FOREIGN KEY (`event_id`)
    REFERENCES `FriendAligner`.`Events` (`event_id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `FriendAligner`.`ChatMessages`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `FriendAligner`.`ChatMessages` (
  `message_id` INT NOT NULL AUTO_INCREMENT,
  `group_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `content` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  INDEX `FK_chat_group_id_idx` (`group_id` ASC),
  INDEX `FK_chat_user_id_idx` (`user_id` ASC),
  CONSTRAINT `FK_chat_group_id`
    FOREIGN KEY (`group_id`)
    REFERENCES `FriendAligner`.`Groups` (`group_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `FK_chat_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `FriendAligner`.`Users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
