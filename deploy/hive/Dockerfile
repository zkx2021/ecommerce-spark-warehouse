FROM apache/hive:4.0.0

USER root

ADD https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.4.0/mysql-connector-j-8.4.0.jar /opt/hive/lib/mysql-connector-j.jar
RUN chmod 0644 /opt/hive/lib/mysql-connector-j.jar

USER hive
