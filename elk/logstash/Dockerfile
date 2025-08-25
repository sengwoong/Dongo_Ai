FROM docker.elastic.co/logstash/logstash:8.14.0

# Add MySQL JDBC driver
RUN curl -L -o /usr/share/logstash/logstash-core/lib/jars/mysql-connector-j-8.4.0.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.4.0/mysql-connector-j-8.4.0.jar

COPY pipeline /usr/share/logstash/pipeline



