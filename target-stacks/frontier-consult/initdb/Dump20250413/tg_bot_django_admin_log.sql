-- MySQL dump 10.13  Distrib 8.0.38, for Win64 (x86_64)
--
-- Host: localhost    Database: tg_bot
-- ------------------------------------------------------
-- Server version	9.0.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2025-03-30 16:54:11.885414','1','default (en)',1,'[{\"added\": {}}]',10,1),(2,'2025-03-30 16:57:06.506617','2','contacts (en)',1,'[{\"added\": {}}]',10,1),(3,'2025-03-30 17:03:00.016879','2','contacts (en)',2,'[]',10,1),(4,'2025-03-30 17:03:08.107810','1','default (en)',2,'[]',10,1),(5,'2025-03-30 17:06:04.739605','1','persons',1,'[{\"added\": {}}]',7,1),(6,'2025-03-30 17:33:27.052860','2','vehicles',1,'[{\"added\": {}}]',7,1),(7,'2025-03-30 19:20:05.343773','4','test1 (en)',1,'[{\"added\": {}}]',10,1),(8,'2025-03-30 19:33:51.829503','5','test3 (ro)',1,'[{\"added\": {}}]',10,1),(9,'2025-04-05 19:36:08.923959','31','acceptedDocs (en)',2,'[{\"changed\": {\"fields\": [\"Response text\", \"Language\"]}}]',10,1),(10,'2025-04-05 19:36:22.719897','34','assurance (en)',2,'[{\"changed\": {\"fields\": [\"Response text\", \"Language\"]}}]',10,1),(11,'2025-04-05 19:38:58.000107','31','acceptedDocs (eng)',2,'[{\"changed\": {\"fields\": [\"Language\"]}}]',10,1),(12,'2025-04-05 19:39:05.432311','34','assurance (eng)',2,'[{\"changed\": {\"fields\": [\"Language\"]}}]',10,1),(13,'2025-04-05 20:04:25.968788','24','purpose (ru)',2,'[{\"changed\": {\"fields\": [\"Command\", \"Response text\"]}}]',10,1),(14,'2025-04-05 20:04:39.572377','23','purpose (ro)',2,'[{\"changed\": {\"fields\": [\"Command\", \"Response text\"]}}]',10,1),(15,'2025-04-05 20:04:50.115375','22','purpose (eng)',2,'[{\"changed\": {\"fields\": [\"Command\", \"Response text\"]}}]',10,1),(16,'2025-04-05 20:05:06.715519','33','accepted (ru)',2,'[{\"changed\": {\"fields\": [\"Command\", \"Response text\"]}}]',10,1),(17,'2025-04-05 20:05:16.397908','32','accepted (ro)',2,'[{\"changed\": {\"fields\": [\"Command\", \"Response text\"]}}]',10,1),(18,'2025-04-05 20:05:24.743463','31','accepted (eng)',2,'[{\"changed\": {\"fields\": [\"Command\"]}}]',10,1),(19,'2025-04-05 20:11:48.714444','15','vehicles (ru)',2,'[{\"changed\": {\"fields\": [\"Response text\"]}}]',10,1),(20,'2025-04-05 20:47:32.707501','33','accepted (ru)',2,'[{\"changed\": {\"fields\": [\"Response text\"]}}]',10,1),(21,'2025-04-09 18:53:14.986877','89','Q: Pe 14 ianuarie mam întors acasă MD,(având 91 de zi...',2,'[{\"changed\": {\"fields\": [\"Question\", \"Answer\", \"Processed\"]}}]',8,1),(22,'2025-04-09 19:39:41.873886','122','Q: dacă am încălcat termenul de ședere peste hotare ș...',2,'[{\"changed\": {\"fields\": [\"Answer\", \"Processed\"]}}]',8,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-13 11:28:29
