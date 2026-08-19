FROM pandoc/core


ENV TZ="Europe/Tallinn"
RUN date
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
RUN echo "http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk update && apk --no-cache add openjdk14

ADD build/libs/metsis-ee-api-1.0.0-all.jar /api.jar

USER root

EXPOSE 9100

ENTRYPOINT ["java", "-jar", "/api.jar"]
