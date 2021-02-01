#!/usr/bin/env python3

import os
import sys
import socket
import shutil
import jinja2
import logging
from pathlib import Path
from typing import Dict, List

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)

DEFAULT_PROPERTIES = {
  "num.network.threads": "3",
  "num.io.threads": "8",
  "socket.send.buffer.bytes": "102400",
  "socket.receive.buffer.bytes": "102400",
  "socket.request.max.bytes": "104857600",
  "log.dirs": "/var/lib/kafka",
  "num.partitions": "1",
  "num.recovery.threads.per.data.dir": "1",
  "offsets.topic.replication.factor": "1",
  "transaction.state.log.replication.factor": "1",
  "transaction.state.log.min.isr": "1",
  "log.flush.interval.messages": "10000",
  "log.flush.interval.ms": "1000",
  "delete.topic.enable": "true",
  "log.retention.hours": "72",
  "log.segment.bytes": "1073741824",
  "log.retention.check.interval.ms": "300000",
  "zookeeper.connect": "localhost:2181",
  "zookeeper.connection.timeout.ms": "18000",
  "group.initial.rebalance.delay.ms": "0",
}


class Properties:
  def __init__(self: "Properties") -> None:
    # Load valid properties
    with open("/etc/kafka/valid.properties", "r") as f:
      valid = f.readlines()
    
    self.valid: List[str] = [x.strip() for x in valid if x != "" and x[0].isalpha()]

    # Set the default properties.
    self._properties: Dict[str, str] = DEFAULT_PROPERTIES

    # Customize the id, listeners and advertiser
    host = socket.getfqdn()
    try:
      name, _ = host.split(".", 1)
      _, ordinal = name.rsplit("-", 1)
    except ValueError:
      log.warn(f"Could not determine ordinal from hostname, using 0")
      ordinal = "0"

    ordinal = os.environ.get("BROKER_ID", ordinal)
    port = os.environ.get("BROKER_PORT", "9092")

    self._properties['broker.id'] = ordinal
    self._properties['listeners'] = f"PLAINTEXT://:{port}"
    self._properties['advertised.listeners'] = f"PLAINTEXT://{host}:{port}"
    self.load_environment() 

  def load_environment(self: "Properties") -> None:
    # Converts the uppercase underscore seperated into lowercase dot separated
    # variables. Since there are no camelcase
    for key, value in os.environ.items():
      if key.startswith("KAFKA_") and not key == "KAFKA_HOME":
        property = ".".join(key.lower().split("_")[1:])
        if not property in self.valid:
          log.warning(f"{key} does not reference a valid property {property}")
          continue

        log.info(f"Configuring: {property}={value}")
        self._properties[property] = value
  
  @property
  def all(self: "Properties") -> Dict[str, str]:
    return self._properties


class Kafka:
  def __init__(self: "Kafka", properties: "Properties"):
    self.properties = properties
  
  def render_server_properties(self: "Kafka"):
    template = self.get_template("server.properties.j2")
    with open("/etc/kafka/server.properties", "w") as f:
      log.info("Generating server.properties")
      f.write(template.render(properties=self.properties.all))

  def get_template(self: "Kafka", name: str) -> jinja2.Template:
    loader = jinja2.FileSystemLoader(searchpath="/etc/kafka/templates.d")
    env = jinja2.Environment(loader=loader)
    return env.get_template(name)

# Check for a mounted directory with configs and use them instead of the generated
# configs.
mounted_configs = Path("/conf.d")
configs = Path("/etc/kafka")
if mounted_configs.exists():
  log.info(f"Linking mounted configs at /conf.d")
  shutil.rmtree(configs)
  os.symlink(mounted_configs, configs)
  sys.exit(0)

properties = Properties()
kafka = Kafka(properties)
kafka.render_server_properties()
