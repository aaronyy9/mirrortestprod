# bms 项目维护脚本
##  bms prod deploy 后端
### 2025-11-10 create by aaronyou 初始化项目 目的是为了发布 bms 项目从知定堂环境发布到 prod 环境
发布地址：https://jks-deploy.depzen.com/  访问方式 depz zenx2022
使用gitlab自动发布程序到内网23

test to prod

### 2025-11-18 add by aaronyou 建立其他目录other，用于存放bms的其他脚本
1. up.sh test环境升级脚本

### 2025-11-26 add by aaronyou
1. 实现自动给gitlab打tag 以及给镜像打tag，按照下面的标准对应
Patch,minor,major 版本的区别：
    1. patch 版本：修复bug，不增加新功能，不改变接口，不改变数据库结构
    2. minor 版本：增加新功能，不改变接口，不改变数据库结构
    3. major 版本：改变接口，改变数据库结构
2. 新增demo标准版的发布在界面上

### 2025-11-27 add by aaronyou
1. 新增trial 和 同步到阿里云镜像 的发布在界面上
