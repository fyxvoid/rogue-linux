PLANNER_DIR = cogman/src/planner
EXECUTOR_DIR = cogman/src/executor
TARGET_DIR = cogman/src/target/debug
BIN_DIR = bin

INSTALL_DIR = /usr/local/bin

.PHONY: all clean test planner executor install system-install system-uninstall

all: planner executor install

planner:
	@echo "Building Cogman Planner..."
	@cd $(PLANNER_DIR) && cargo build

executor:
	@echo "Building Cogman Executor..."
	@$(MAKE) -C $(EXECUTOR_DIR)

install: planner executor
	@echo "Installing specialized Cogman environment to $(BIN_DIR)..."
	@mkdir -p $(BIN_DIR)
	@cp $(TARGET_DIR)/cogman_planner $(BIN_DIR)/cogman-planner
	@cp $(EXECUTOR_DIR)/cogman-exec $(BIN_DIR)/cogman-executor
	@echo "Environment ready: ./bin/cogman-planner, ./bin/cogman-executor"

system-install: install
	@echo "Deploying Cogman to $(INSTALL_DIR) (requires sudo)..."
	@sudo cp $(BIN_DIR)/cogman-planner $(INSTALL_DIR)/
	@sudo cp $(BIN_DIR)/cogman-executor $(INSTALL_DIR)/
	@echo "System-wide deployment complete: cogman-planner, cogman-executor"

system-uninstall:
	@echo "Removing Cogman from $(INSTALL_DIR) (requires sudo)..."
	@sudo rm -f $(INSTALL_DIR)/cogman-planner
	@sudo rm -f $(INSTALL_DIR)/cogman-executor
	@echo "System-wide removal complete."

clean:
	@cd $(PLANNER_DIR) && cargo clean
	@$(MAKE) -C $(EXECUTOR_DIR) clean
	@rm -rf $(BIN_DIR)
	@rm -rf tests/graph/cases tests/metadata/cases

test: planner
	@echo "Running Unified Validation Suite..."
	@python3 tests/run_all.py
