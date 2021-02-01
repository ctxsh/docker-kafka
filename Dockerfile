FROM ctxsh/java:jre14 as extract

ARG VERSION=2.7.0
ARG SCALA_VERSION=2.13
ARG URL=https://apache.osuosl.org/kafka/${VERSION}/kafka_${SCALA_VERSION}-${VERSION}.tgz
ARG KAFKACAT_VERSION=1.6.0-1
ARG KAFKACAT_URL=https://github.com/edenhill/kafkacat/archive/debian/${KAFKACAT_VERSION}.tar.gz

WORKDIR /output

RUN : \
  && mkdir -p opt/kafka \
  && curl -sL $URL | tar zxf - -C opt/kafka --strip-components=1 \
  && cd opt/kafka \
  && rm -rf *.txt *.md docs conf \
  && :

FROM ctxsh/java:jre14

ENV KAFKA_HOME /opt/kafka
ENV PATH $KAFKA_HOME/bin:$PATH
ENV S6_KEEP_ENV=1
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2

COPY --from=extract /output /
COPY kafka /etc/kafka
COPY permissions /etc/fix-attrs.d
COPY entrypoints /etc/cont-init.d

RUN : \
  && apt-get update \
  && apt-get -y install kafkacat \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean \
  && rm -rf /tmp/* \
  && :

RUN : \
  && useradd -u 1000 -r kafka \
  && mkdir -p /var/lib/kafka \
  && chown -R kafka:kafka /etc/kafka \
  && chown -R kafka:kafka /var/lib/kafka \
  && :

EXPOSE 9092

ENTRYPOINT ["/init"]
CMD ["/opt/kafka/bin/kafka-server-start.sh", "/etc/kafka/server.properties"]
