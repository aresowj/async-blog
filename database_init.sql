-- database_init.sql
-- Used to create tables for the blog app

drop database if exists aresou;

create database aresou;

use aresou;

grant select, insert, update, delete on aresou.* to 'root'@'localhost' identified by 'kagami';

create table users (
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `password` varchar(50) not null,
    `admin` bool not null,
    `name` varchar(50) not null,
    `image` varchar(500) not null,
    `created_time` real not null,
    unique key `idx_email` (`email`),
    key `idx_created_time` (`created_time`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table blogs (
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `title` varchar(50) not null,
    `summary` varchar(200) not null,
    `content` mediumtext not null,
    `created_time` real not null,
    key `idx_created_time` (`created_time`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table comments (
    `id` varchar(50) not null,
    `blog_id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `content` mediumtext not null,
    `created_time` real not null,
    key `idx_created_time` (`created_time`),
    primary key (`id`)
) engine=innodb default charset=utf8;