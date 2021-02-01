PREFIX := $(HOME)
MAKE_PATH := $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
DOCKERHUB_USER ?= ctxsh
VERSION ?= 2.7.0

.PHONY: all
all: kafka

###################################################################################################
# Kafka build and release targets
###################################################################################################
.PHONY: kafka
kafka:
	@docker build \
					--tag $(DOCKERHUB_USER)/kafka:$(VERSION) \
					--file Dockerfile \
					.

###################################################################################################
# Local testing targets
###################################################################################################
.PHONY: test
test: kafka local-kind local-release

.PHONY: local-kind
local-kind:
	@$(MAKE_PATH)test/kind.sh
	@kubectl cluster-info --context kind-kind

.PHONY: local-release
local-release:
	@docker tag $(DOCKERHUB_USER)/kafka:$(VERSION) localhost:5000/kafka-local:latest
	@docker push localhost:5000/kafka-local:latest

# TODO: Run the tests

###################################################################################################
# Utility targets
###################################################################################################
.PHONY: clean
clean:
	@kind delete cluster
	@docker stop kind-registry 2>/dev/null || true
	@docker rm kind-registry 2>/dev/null || true
	@docker rm $(shell docker ps -qa) 2>/dev/null || true
	@docker rmi $(shell docker images -q $(DOCKERHUB_USER)/kakfa) --force 2>/dev/null || true
