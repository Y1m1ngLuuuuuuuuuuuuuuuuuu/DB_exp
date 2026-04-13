-- MySQL dump 10.13  Distrib 9.6.0, for Linux (aarch64)
--
-- Host: localhost    Database: course_system
-- ------------------------------------------------------
-- Server version	9.6.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ 'd8d47fdc-15e6-11f1-84a2-6aaf73430eed:1-456';

--
-- Current Database: `course_system`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `course_system` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `course_system`;

--
-- Table structure for table `admin_profile`
--

DROP TABLE IF EXISTS `admin_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin_profile` (
  `admin_id` varchar(20) NOT NULL COMMENT '管理员编号',
  `user_id` bigint NOT NULL COMMENT '账号编号',
  `admin_name` varchar(30) NOT NULL COMMENT '管理员姓名',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `uq_admin_user` (`user_id`),
  CONSTRAINT `fk_admin_user` FOREIGN KEY (`user_id`) REFERENCES `user_account` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='管理员资料表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin_profile`
--

LOCK TABLES `admin_profile` WRITE;
/*!40000 ALTER TABLE `admin_profile` DISABLE KEYS */;
INSERT INTO `admin_profile` VALUES ('A001',1,'系统管理员','010-88880000');
/*!40000 ALTER TABLE `admin_profile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `classroom`
--

DROP TABLE IF EXISTS `classroom`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `classroom` (
  `classroom_id` varchar(20) NOT NULL COMMENT '教室编号',
  `building` varchar(50) NOT NULL COMMENT '教学楼',
  `room_no` varchar(20) NOT NULL COMMENT '房间号',
  `capacity` int NOT NULL COMMENT '容量',
  PRIMARY KEY (`classroom_id`),
  CONSTRAINT `chk_capacity` CHECK ((`capacity` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='教室表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classroom`
--

LOCK TABLES `classroom` WRITE;
/*!40000 ALTER TABLE `classroom` DISABLE KEYS */;
INSERT INTO `classroom` VALUES ('C101','综合楼','101',60),('C201','综合楼','201',40),('C301','实验楼','301',30);
/*!40000 ALTER TABLE `classroom` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `course`
--

DROP TABLE IF EXISTS `course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course` (
  `course_id` varchar(20) NOT NULL COMMENT '课程号',
  `course_name` varchar(100) NOT NULL COMMENT '课程名',
  `course_type` enum('required','elective','public') NOT NULL DEFAULT 'required' COMMENT '课程类型',
  `credit` decimal(3,1) NOT NULL COMMENT '学分',
  `total_hours` int NOT NULL COMMENT '总学时',
  `dept_id` varchar(10) DEFAULT NULL COMMENT '开课院系',
  `description` text COMMENT '课程简介',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active' COMMENT '课程状态',
  PRIMARY KEY (`course_id`),
  KEY `fk_course_dept` (`dept_id`),
  CONSTRAINT `fk_course_dept` FOREIGN KEY (`dept_id`) REFERENCES `department` (`dept_id`),
  CONSTRAINT `chk_credit` CHECK ((`credit` > 0)),
  CONSTRAINT `chk_total_hours` CHECK ((`total_hours` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='课程基础定义表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course`
--

LOCK TABLES `course` WRITE;
/*!40000 ALTER TABLE `course` DISABLE KEYS */;
INSERT INTO `course` VALUES ('CS101','程序设计基础','required',3.0,48,'CS','C 语言基础程序设计','active'),('CS201','数据结构','required',3.0,48,'CS','线性表、树、图及常用算法','active'),('CS301','数据库原理','required',3.0,48,'CS','关系模型与 SQL，数据库设计','active'),('CS401','Python 程序设计','elective',2.0,32,'CS','Python 基础与常用库','active'),('MA101','高等数学','required',4.0,64,'MATH','微积分与级数','active');
/*!40000 ALTER TABLE `course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `course_offering`
--

DROP TABLE IF EXISTS `course_offering`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_offering` (
  `offering_id` bigint NOT NULL AUTO_INCREMENT COMMENT '开课编号',
  `course_id` varchar(20) NOT NULL COMMENT '课程号',
  `semester_id` varchar(20) NOT NULL COMMENT '学期编号',
  `teacher_id` varchar(20) NOT NULL COMMENT '任课教师号',
  `classroom_id` varchar(20) DEFAULT NULL COMMENT '教室编号',
  `max_capacity` int NOT NULL DEFAULT '60' COMMENT '最大容量',
  `selected_count` int NOT NULL DEFAULT '0' COMMENT '当前已选人数',
  `schedule_text` varchar(200) DEFAULT NULL COMMENT '上课时间说明，如 周一3-4节',
  `status` enum('open','closed','cancelled') NOT NULL DEFAULT 'open' COMMENT '开课状态',
  PRIMARY KEY (`offering_id`),
  KEY `fk_offering_course` (`course_id`),
  KEY `fk_offering_semester` (`semester_id`),
  KEY `fk_offering_teacher` (`teacher_id`),
  KEY `fk_offering_classroom` (`classroom_id`),
  CONSTRAINT `fk_offering_classroom` FOREIGN KEY (`classroom_id`) REFERENCES `classroom` (`classroom_id`),
  CONSTRAINT `fk_offering_course` FOREIGN KEY (`course_id`) REFERENCES `course` (`course_id`),
  CONSTRAINT `fk_offering_semester` FOREIGN KEY (`semester_id`) REFERENCES `semester` (`semester_id`),
  CONSTRAINT `fk_offering_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teacher` (`teacher_id`),
  CONSTRAINT `chk_max_capacity` CHECK ((`max_capacity` > 0)),
  CONSTRAINT `chk_selected_count` CHECK ((`selected_count` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='开课表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course_offering`
--

LOCK TABLES `course_offering` WRITE;
/*!40000 ALTER TABLE `course_offering` DISABLE KEYS */;
INSERT INTO `course_offering` VALUES (1,'CS101','2025-2026-2','T001','C101',60,3,'周一 1-2 节 / 周三 3-4 节','open'),(2,'CS201','2025-2026-2','T001','C201',40,0,'周二 3-4 节 / 周四 5-6 节','open'),(3,'MA101','2025-2026-2','T002','C101',60,2,'周一 5-6 节 / 周五 1-2 节','open'),(4,'CS401','2025-2026-2','T001','C301',30,1,'周三 7-8 节','open'),(5,'CS101','2025-2026-1','T001','C101',60,0,'周一 1-2 节','closed');
/*!40000 ALTER TABLE `course_offering` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `course_prerequisite`
--

DROP TABLE IF EXISTS `course_prerequisite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_prerequisite` (
  `course_id` varchar(20) NOT NULL COMMENT '课程号',
  `prereq_course_id` varchar(20) NOT NULL COMMENT '先修课程号',
  PRIMARY KEY (`course_id`,`prereq_course_id`),
  KEY `fk_prereq_pre` (`prereq_course_id`),
  CONSTRAINT `fk_prereq_course` FOREIGN KEY (`course_id`) REFERENCES `course` (`course_id`),
  CONSTRAINT `fk_prereq_pre` FOREIGN KEY (`prereq_course_id`) REFERENCES `course` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='先修课程关系表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course_prerequisite`
--

LOCK TABLES `course_prerequisite` WRITE;
/*!40000 ALTER TABLE `course_prerequisite` DISABLE KEYS */;
INSERT INTO `course_prerequisite` VALUES ('CS201','CS101'),('CS301','CS201');
/*!40000 ALTER TABLE `course_prerequisite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `department`
--

DROP TABLE IF EXISTS `department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `department` (
  `dept_id` varchar(10) NOT NULL COMMENT '院系编号',
  `dept_name` varchar(50) NOT NULL COMMENT '院系名称',
  `office_phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `office_location` varchar(100) DEFAULT NULL COMMENT '办公地点',
  PRIMARY KEY (`dept_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='院系表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department`
--

LOCK TABLES `department` WRITE;
/*!40000 ALTER TABLE `department` DISABLE KEYS */;
INSERT INTO `department` VALUES ('CS','计算机学院','010-88881111','综合楼 A301'),('MATH','数学学院','010-88882222','综合楼 B201');
/*!40000 ALTER TABLE `department` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enrollment`
--

DROP TABLE IF EXISTS `enrollment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enrollment` (
  `enrollment_id` bigint NOT NULL AUTO_INCREMENT COMMENT '选课记录编号',
  `student_id` varchar(20) NOT NULL COMMENT '学号',
  `offering_id` bigint NOT NULL COMMENT '开课编号',
  `select_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
  `status` enum('selected','dropped','completed') NOT NULL DEFAULT 'selected' COMMENT '选课状态',
  `final_score` decimal(5,2) DEFAULT NULL COMMENT '最终成绩',
  `gpa_point` decimal(3,2) DEFAULT NULL COMMENT '绩点',
  `remark` varchar(200) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`enrollment_id`),
  UNIQUE KEY `uq_student_offering` (`student_id`,`offering_id`),
  KEY `fk_enrollment_offering` (`offering_id`),
  CONSTRAINT `fk_enrollment_offering` FOREIGN KEY (`offering_id`) REFERENCES `course_offering` (`offering_id`),
  CONSTRAINT `fk_enrollment_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`),
  CONSTRAINT `chk_final_score` CHECK (((`final_score` is null) or ((`final_score` >= 0) and (`final_score` <= 100)))),
  CONSTRAINT `chk_gpa_point` CHECK (((`gpa_point` is null) or ((`gpa_point` >= 0) and (`gpa_point` <= 5))))
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='选课表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enrollment`
--

LOCK TABLES `enrollment` WRITE;
/*!40000 ALTER TABLE `enrollment` DISABLE KEYS */;
INSERT INTO `enrollment` VALUES (1,'20240001',1,'2026-04-13 07:28:39','selected',NULL,NULL,NULL),(2,'20240001',3,'2026-04-13 07:28:39','selected',NULL,NULL,NULL),(3,'20240002',1,'2026-04-13 07:28:39','selected',NULL,NULL,NULL),(4,'20240002',3,'2026-04-13 07:28:39','selected',NULL,NULL,NULL),(5,'20240003',1,'2026-04-13 07:28:39','selected',NULL,NULL,NULL),(6,'20240003',4,'2026-04-13 07:28:39','selected',NULL,NULL,NULL),(7,'20240001',5,'2026-04-13 07:28:39','completed',88.00,3.50,NULL),(8,'20240002',5,'2026-04-13 07:28:39','completed',92.00,4.00,NULL),(9,'20240003',5,'2026-04-13 07:28:39','completed',75.00,3.00,NULL);
/*!40000 ALTER TABLE `enrollment` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_enrollment_insert` AFTER INSERT ON `enrollment` FOR EACH ROW BEGIN
    IF NEW.status = 'selected' THEN
        UPDATE course_offering
        SET selected_count = selected_count + 1
        WHERE offering_id = NEW.offering_id;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_enrollment_update` AFTER UPDATE ON `enrollment` FOR EACH ROW BEGIN
    IF OLD.status = 'selected' AND NEW.status = 'dropped' THEN
        UPDATE course_offering
        SET selected_count = GREATEST(selected_count - 1, 0)
        WHERE offering_id = NEW.offering_id;
    END IF;
    IF OLD.status = 'dropped' AND NEW.status = 'selected' THEN
        UPDATE course_offering
        SET selected_count = selected_count + 1
        WHERE offering_id = NEW.offering_id;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `major`
--

DROP TABLE IF EXISTS `major`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `major` (
  `major_id` varchar(10) NOT NULL COMMENT '专业编号',
  `major_name` varchar(50) NOT NULL COMMENT '专业名称',
  `dept_id` varchar(10) NOT NULL COMMENT '所属院系',
  PRIMARY KEY (`major_id`),
  KEY `fk_major_dept` (`dept_id`),
  CONSTRAINT `fk_major_dept` FOREIGN KEY (`dept_id`) REFERENCES `department` (`dept_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='专业表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `major`
--

LOCK TABLES `major` WRITE;
/*!40000 ALTER TABLE `major` DISABLE KEYS */;
INSERT INTO `major` VALUES ('CS01','计算机科学与技术','CS'),('CS02','软件工程','CS'),('MA01','数学与应用数学','MATH');
/*!40000 ALTER TABLE `major` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `score_change_log`
--

DROP TABLE IF EXISTS `score_change_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `score_change_log` (
  `log_id` bigint NOT NULL AUTO_INCREMENT COMMENT '日志编号',
  `enrollment_id` bigint NOT NULL COMMENT '选课记录编号',
  `old_score` decimal(5,2) DEFAULT NULL COMMENT '旧成绩',
  `new_score` decimal(5,2) DEFAULT NULL COMMENT '新成绩',
  `changed_by_user_id` bigint NOT NULL COMMENT '修改人账号编号',
  `changed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `reason` varchar(200) DEFAULT NULL COMMENT '修改原因',
  PRIMARY KEY (`log_id`),
  KEY `fk_log_enrollment` (`enrollment_id`),
  KEY `fk_log_user` (`changed_by_user_id`),
  CONSTRAINT `fk_log_enrollment` FOREIGN KEY (`enrollment_id`) REFERENCES `enrollment` (`enrollment_id`),
  CONSTRAINT `fk_log_user` FOREIGN KEY (`changed_by_user_id`) REFERENCES `user_account` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='成绩修改日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `score_change_log`
--

LOCK TABLES `score_change_log` WRITE;
/*!40000 ALTER TABLE `score_change_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `score_change_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `semester`
--

DROP TABLE IF EXISTS `semester`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `semester` (
  `semester_id` varchar(20) NOT NULL COMMENT '学期编号',
  `semester_name` varchar(30) NOT NULL COMMENT '学期名称，如 2025-2026-1',
  `start_date` date NOT NULL COMMENT '开始日期',
  `end_date` date NOT NULL COMMENT '结束日期',
  `selection_start` datetime DEFAULT NULL COMMENT '选课开始时间',
  `selection_end` datetime DEFAULT NULL COMMENT '选课截止时间',
  `status` enum('planned','open','closed') NOT NULL DEFAULT 'planned' COMMENT '状态',
  PRIMARY KEY (`semester_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学期表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `semester`
--

LOCK TABLES `semester` WRITE;
/*!40000 ALTER TABLE `semester` DISABLE KEYS */;
INSERT INTO `semester` VALUES ('2025-2026-1','2025-2026学年第一学期','2025-09-01','2026-01-20','2025-08-20 09:00:00','2025-09-10 18:00:00','closed'),('2025-2026-2','2025-2026学年第二学期','2026-02-24','2026-07-10','2026-02-10 09:00:00','2026-02-20 18:00:00','open');
/*!40000 ALTER TABLE `semester` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student`
--

DROP TABLE IF EXISTS `student`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student` (
  `student_id` varchar(20) NOT NULL COMMENT '学号',
  `user_id` bigint NOT NULL COMMENT '账号编号',
  `student_name` varchar(30) NOT NULL COMMENT '姓名',
  `gender` enum('M','F','O') DEFAULT NULL COMMENT '性别 M/F/O',
  `birth_date` date DEFAULT NULL COMMENT '出生日期',
  `enroll_year` smallint DEFAULT NULL COMMENT '入学年份',
  `major_id` varchar(10) DEFAULT NULL COMMENT '所属专业',
  `class_name` varchar(30) DEFAULT NULL COMMENT '班级',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `status` enum('enrolled','suspended','graduated','dropped') NOT NULL DEFAULT 'enrolled' COMMENT '学籍状态',
  PRIMARY KEY (`student_id`),
  UNIQUE KEY `uq_student_user` (`user_id`),
  KEY `fk_student_major` (`major_id`),
  CONSTRAINT `fk_student_major` FOREIGN KEY (`major_id`) REFERENCES `major` (`major_id`),
  CONSTRAINT `fk_student_user` FOREIGN KEY (`user_id`) REFERENCES `user_account` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学生表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student`
--

LOCK TABLES `student` WRITE;
/*!40000 ALTER TABLE `student` DISABLE KEYS */;
INSERT INTO `student` VALUES ('20240001',4,'王小明','M',NULL,2024,'CS01','计科2401',NULL,'wxm@stu.edu.cn','enrolled'),('20240002',5,'陈雨欣','F',NULL,2024,'CS01','计科2401',NULL,'cyx@stu.edu.cn','enrolled'),('20240003',6,'刘强','M',NULL,2024,'CS02','软工2401',NULL,'lq@stu.edu.cn','enrolled'),('20240004',200,'赵昊瑞','M','2006-01-17',2024,'CS01','2024级1班','15930295356','20240004@gmail.com','enrolled'),('20240005',201,'徐晴','F','2005-08-14',2024,'CS01','2024级1班','15821034191','20240005@163.com','enrolled'),('20240006',202,'高欣','F','2006-11-06',2024,'CS01','2024级1班','13878208019','20240006@qq.com','enrolled'),('20240007',203,'陈秀欣','F','2006-02-22',2024,'CS01','2024级1班','15606056046','20240007@163.com','enrolled'),('20240008',204,'杨霞薇','F','2006-10-18',2024,'CS01','2024级1班','15990213570','20240008@qq.com','enrolled'),('20240009',205,'朱嘉','F','2006-02-22',2024,'CS01','2024级1班','18908935710','20240009@163.com','enrolled'),('20240010',206,'杨鹏','M','2006-02-10',2024,'CS01','2024级1班','15227242463','20240010@qq.com','enrolled'),('20240011',207,'吴浩','M','2004-01-21',2024,'CS01','2024级1班','13326987566','20240011@qq.com','enrolled'),('20240012',208,'陈刚宇','M','2006-11-01',2024,'CS01','2024级1班','13691355997','20240012@163.com','enrolled'),('20240013',209,'林萍','F','2005-07-14',2024,'CS01','2024级1班','18960146279','20240013@outlook.com','enrolled'),('20240014',210,'唐诗','F','2006-12-01',2024,'CS01','2024级1班','18180503414','20240014@gmail.com','enrolled'),('20240015',211,'杨莉','F','2005-11-06',2024,'CS01','2024级1班','15094460285','20240015@163.com','enrolled'),('20240016',212,'郭芳','F','2004-03-17',2024,'CS01','2024级1班','18211886514','20240016@gmail.com','enrolled'),('20240017',213,'徐嘉雨','F','2005-02-15',2024,'CS01','2024级1班','18140662480','20240017@qq.com','enrolled'),('20240018',214,'罗泽','M','2006-02-22',2024,'CS01','2024级1班','13061213250','20240018@qq.com','enrolled'),('20240019',215,'黄敏','F','2006-04-13',2024,'CS01','2024级1班','13610920913','20240019@qq.com','enrolled'),('20240020',216,'郑馨霞','F','2006-12-20',2024,'CS01','2024级1班','18058597066','20240020@qq.com','enrolled'),('20240021',217,'林薇','F','2006-07-16',2024,'CS01','2024级1班','18201471591','20240021@163.com','enrolled'),('20240022',218,'吴刚','M','2006-03-15',2024,'CS01','2024级1班','15110104778','20240022@qq.com','enrolled'),('20240023',219,'王瑞强','M','2004-07-04',2024,'CS01','2024级1班','18069741418','20240023@qq.com','enrolled'),('20240024',220,'郭文','M','2005-10-11',2024,'CS01','2024级1班','13915737762','20240024@163.com','enrolled'),('20240025',221,'曹鹏','M','2004-11-01',2024,'CS01','2024级1班','15234637448','20240025@gmail.com','enrolled'),('20240026',222,'李欣诗','F','2004-12-11',2024,'CS01','2024级1班','18930922777','20240026@gmail.com','enrolled'),('20240027',223,'谢宸','M','2005-06-10',2024,'CS01','2024级1班','18975063408','20240027@163.com','enrolled'),('20240028',224,'张凯强','M','2005-05-06',2024,'CS01','2024级1班','13013656333','20240028@gmail.com','enrolled'),('20240029',225,'何磊','M','2005-05-10',2024,'CS01','2024级1班','18355731921','20240029@outlook.com','enrolled'),('20240030',226,'唐强超','M','2005-10-04',2024,'CS01','2024级1班','15825152538','20240030@qq.com','enrolled'),('20240031',227,'谢飞','M','2004-10-25',2024,'CS01','2024级1班','18289803398','20240031@163.com','enrolled'),('20240032',228,'郭睿刚','M','2004-05-26',2024,'CS01','2024级1班','15182164605','20240032@gmail.com','enrolled'),('20240033',229,'杨波','M','2005-06-13',2024,'CS01','2024级1班','18286810387','20240033@gmail.com','enrolled'),('20240034',300,'韩洁薇','F','2006-03-25',2024,'CS01','2024级1班','13245496004','20240034@163.com','enrolled'),('20240035',301,'冯雨霞','F','2004-11-08',2024,'CS01','2024级1班','18297380426','20240035@163.com','enrolled'),('20240036',302,'胡阳','M','2006-01-13',2024,'CS01','2024级1班','13283596085','20240036@qq.com','enrolled'),('20240037',303,'张晴梅','F','2006-08-13',2024,'CS01','2024级1班','15555293709','20240037@gmail.com','enrolled'),('20240038',304,'高泽龙','M','2005-06-15',2024,'CS01','2024级1班','13872206771','20240038@qq.com','enrolled'),('20240039',305,'谢丽','F','2006-02-16',2024,'CS01','2024级1班','15799029366','20240039@gmail.com','enrolled'),('20240040',306,'郭莉','F','2006-05-01',2024,'CS01','2024级1班','15207194306','20240040@163.com','enrolled'),('20240041',307,'陈涛','M','2005-01-23',2024,'CS01','2024级1班','13907104694','20240041@outlook.com','enrolled'),('20240042',308,'邓龙','M','2006-03-17',2024,'CS01','2024级1班','18090828917','20240042@163.com','enrolled'),('20240043',309,'李刚健','M','2004-12-17',2024,'CS01','2024级1班','18915740670','20240043@qq.com','enrolled'),('20240044',310,'赵辉晨','M','2006-01-01',2024,'CS01','2024级1班','13861480286','20240044@outlook.com','enrolled'),('20240045',311,'许琳','F','2004-04-19',2024,'CS01','2024级1班','18658715985','20240045@qq.com','enrolled'),('20240046',312,'朱薇','F','2004-10-18',2024,'CS01','2024级1班','18888390814','20240046@outlook.com','enrolled'),('20240047',313,'张嘉','F','2004-05-19',2024,'CS01','2024级1班','15895169410','20240047@outlook.com','enrolled'),('20240048',314,'梁轩宇','M','2004-03-16',2024,'CS01','2024级1班','15181444622','20240048@163.com','enrolled'),('20240049',315,'张薇','F','2004-12-25',2024,'CS01','2024级1班','13698449952','20240049@qq.com','enrolled'),('20240050',316,'黄雨','F','2004-05-02',2024,'CS01','2024级1班','13164381616','20240050@gmail.com','enrolled'),('20240051',317,'梁嘉','F','2006-12-17',2024,'CS01','2024级1班','15105405966','20240051@163.com','enrolled'),('20240052',318,'王琳','F','2004-10-14',2024,'CS01','2024级1班','13784420621','20240052@qq.com','enrolled'),('20240053',319,'梁雨莉','F','2005-10-05',2024,'CS01','2024级1班','13875740564','20240053@gmail.com','enrolled'),('20240054',320,'高刚','M','2006-09-19',2024,'CS01','2024级1班','13912190201','20240054@163.com','enrolled'),('20240055',321,'吴宸阳','M','2004-06-13',2024,'CS01','2024级1班','15867696501','20240055@163.com','enrolled'),('20240056',322,'郑磊刚','M','2005-07-27',2024,'CS01','2024级1班','18996957593','20240056@163.com','enrolled'),('20240057',323,'孙鹏昊','M','2004-01-21',2024,'CS01','2024级1班','15804943619','20240057@qq.com','enrolled'),('20240058',324,'邓秀艳','F','2004-06-24',2024,'CS01','2024级1班','18738921061','20240058@outlook.com','enrolled'),('20240059',325,'唐琳薇','F','2005-02-12',2024,'CS01','2024级1班','13102738743','20240059@qq.com','enrolled'),('20240060',326,'马辉凯','M','2006-08-15',2024,'CS01','2024级1班','18667008278','20240060@163.com','enrolled'),('20240061',327,'郭峰强','M','2004-09-11',2024,'CS01','2024级1班','15825372199','20240061@163.com','enrolled'),('20240062',328,'何浩','M','2006-02-02',2024,'CS01','2024级1班','13052637803','20240062@outlook.com','enrolled'),('20240063',329,'胡洁','F','2005-10-04',2024,'CS01','2024级1班','13095069216','20240063@qq.com','enrolled');
/*!40000 ALTER TABLE `student` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teacher`
--

DROP TABLE IF EXISTS `teacher`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teacher` (
  `teacher_id` varchar(20) NOT NULL COMMENT '教师号',
  `user_id` bigint NOT NULL COMMENT '账号编号',
  `teacher_name` varchar(30) NOT NULL COMMENT '姓名',
  `gender` enum('M','F','O') DEFAULT NULL COMMENT '性别',
  `dept_id` varchar(10) DEFAULT NULL COMMENT '所属院系',
  `title` varchar(20) DEFAULT NULL COMMENT '职称',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `status` enum('active','retired','leave') NOT NULL DEFAULT 'active' COMMENT '在职状态',
  PRIMARY KEY (`teacher_id`),
  UNIQUE KEY `uq_teacher_user` (`user_id`),
  KEY `fk_teacher_dept` (`dept_id`),
  CONSTRAINT `fk_teacher_dept` FOREIGN KEY (`dept_id`) REFERENCES `department` (`dept_id`),
  CONSTRAINT `fk_teacher_user` FOREIGN KEY (`user_id`) REFERENCES `user_account` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='教师表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teacher`
--

LOCK TABLES `teacher` WRITE;
/*!40000 ALTER TABLE `teacher` DISABLE KEYS */;
INSERT INTO `teacher` VALUES ('T001',2,'张明','M','CS','副教授',NULL,'zhangming@edu.cn','active'),('T002',3,'李晓华','F','MATH','讲师',NULL,'lixiaohua@edu.cn','active');
/*!40000 ALTER TABLE `teacher` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_account`
--

DROP TABLE IF EXISTS `user_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_account` (
  `user_id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户编号',
  `username` varchar(50) NOT NULL COMMENT '登录名',
  `password_hash` varchar(64) NOT NULL COMMENT '密码 SHA-256 密文',
  `role` enum('admin','student','teacher') NOT NULL COMMENT '角色',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '账号状态',
  `last_login_at` datetime DEFAULT NULL COMMENT '最近登录时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uq_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=331 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='统一账号表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_account`
--

LOCK TABLES `user_account` WRITE;
/*!40000 ALTER TABLE `user_account` DISABLE KEYS */;
INSERT INTO `user_account` VALUES (1,'admin','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','admin','active','2026-04-13 11:17:33','2026-04-13 07:28:39'),(2,'t_zhang','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 07:28:39'),(3,'t_li','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 07:28:39'),(4,'s_001','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active','2026-04-13 07:30:48','2026-04-13 07:28:39'),(5,'s_002','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 07:28:39'),(6,'s_003','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 07:28:39'),(100,'202400001','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(101,'202400002','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(102,'202400003','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(103,'202400004','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(104,'202400005','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(105,'202400006','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(106,'202400007','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(107,'202400008','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(108,'202400009','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(109,'202400010','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(110,'202400011','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(111,'202400012','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(112,'202400013','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(113,'202400014','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(114,'202400015','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(115,'202400016','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(116,'202400017','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(117,'202400018','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(118,'202400019','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(119,'202400020','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(120,'202400021','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(121,'202400022','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(122,'202400023','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(123,'202400024','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(124,'202400025','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(125,'202400026','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(126,'202400027','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(127,'202400028','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(128,'202400029','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(129,'202400030','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:09:25'),(200,'20240004','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(201,'20240005','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(202,'20240006','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(203,'20240007','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(204,'20240008','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(205,'20240009','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(206,'20240010','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(207,'20240011','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(208,'20240012','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(209,'20240013','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(210,'20240014','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(211,'20240015','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(212,'20240016','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(213,'20240017','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(214,'20240018','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(215,'20240019','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(216,'20240020','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(217,'20240021','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(218,'20240022','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(219,'20240023','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(220,'20240024','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(221,'20240025','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(222,'20240026','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(223,'20240027','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(224,'20240028','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(225,'20240029','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(226,'20240030','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(227,'20240031','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(228,'20240032','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(229,'20240033','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:12:05'),(230,'t001','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(231,'t002','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(232,'t003','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(233,'t004','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(234,'t005','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(235,'t006','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(236,'t007','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(237,'t008','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','teacher','active',NULL,'2026-04-13 11:12:05'),(300,'20240034','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(301,'20240035','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(302,'20240036','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(303,'20240037','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(304,'20240038','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(305,'20240039','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(306,'20240040','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(307,'20240041','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(308,'20240042','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(309,'20240043','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(310,'20240044','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(311,'20240045','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(312,'20240046','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(313,'20240047','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(314,'20240048','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(315,'20240049','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(316,'20240050','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(317,'20240051','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(318,'20240052','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(319,'20240053','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(320,'20240054','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(321,'20240055','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(322,'20240056','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(323,'20240057','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(324,'20240058','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(325,'20240059','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(326,'20240060','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(327,'20240061','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(328,'20240062','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38'),(329,'20240063','8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92','student','active',NULL,'2026-04-13 11:14:38');
/*!40000 ALTER TABLE `user_account` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-13 11:22:30
