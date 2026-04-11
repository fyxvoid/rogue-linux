PLANNER_DIR    = cogman/src/planner
EXECUTOR_DIR   = cogman/src/executor
SUPERVISOR_DIR = cogman/src/supervisor
COGMAN_DIR     = cogman/src/cogman
WORKSPACE_DIR  = cogman/src
TARGET_DIR     = cogman/src/target/debug
BIN_DIR        = bin

INSTALL_DIR = /usr/local/bin

.PHONY: all clean test planner executor supervisor cogman install system-install system-uninstall

all: planner executor supervisor cogman install

planner:
	@echo "Building Cogman Planner..."
	@cd $(PLANNER_DIR) && cargo build

executor:
	@echo "Building Cogman Executor..."
	@$(MAKE) -C $(EXECUTOR_DIR)

supervisor:
	@echo "Building Cogman Supervisor..."
	@$(MAKE) -C $(SUPERVISOR_DIR)

cogman:
	@echo "Building Cogman (unified Rust daemon)..."
	@cd $(WORKSPACE_DIR) && cargo build -p cogman

install: planner executor supervisor cogman
	@echo "Installing Cogman environment to $(BIN_DIR)..."
	@mkdir -p $(BIN_DIR)
	@cp $(TARGET_DIR)/cogman_planner $(BIN_DIR)/cogman-planner
	@cp $(EXECUTOR_DIR)/cogman-exec $(BIN_DIR)/cogman-executor
	@cp $(SUPERVISOR_DIR)/cogman-supervisor $(BIN_DIR)/cogman-supervisor
	@cp $(SUPERVISOR_DIR)/cogman-ctl $(BIN_DIR)/cogman-ctl
	@cp $(TARGET_DIR)/cogman $(BIN_DIR)/cogman
	@echo "Environment ready: bin/cogman, bin/cogman-planner, bin/cogman-executor, bin/cogman-supervisor, bin/cogman-ctl"

system-install: install
	@echo "Deploying Cogman to $(INSTALL_DIR) (requires sudo)..."
	@sudo cp $(BIN_DIR)/cogman $(INSTALL_DIR)/
	@sudo cp $(BIN_DIR)/cogman-planner $(INSTALL_DIR)/
	@sudo cp $(BIN_DIR)/cogman-executor $(INSTALL_DIR)/
	@sudo cp $(BIN_DIR)/cogman-supervisor $(INSTALL_DIR)/
	@sudo cp $(BIN_DIR)/cogman-ctl $(INSTALL_DIR)/
	@echo "System-wide deployment complete."

system-uninstall:
	@echo "Removing Cogman from $(INSTALL_DIR) (requires sudo)..."
	@sudo rm -f $(INSTALL_DIR)/cogman
	@sudo rm -f $(INSTALL_DIR)/cogman-planner
	@sudo rm -f $(INSTALL_DIR)/cogman-executor
	@sudo rm -f $(INSTALL_DIR)/cogman-supervisor
	@sudo rm -f $(INSTALL_DIR)/cogman-ctl
	@echo "System-wide removal complete."

clean:
	@cd $(WORKSPACE_DIR) && cargo clean
	@$(MAKE) -C $(EXECUTOR_DIR) clean
	@$(MAKE) -C $(SUPERVISOR_DIR) clean
	@rm -rf $(BIN_DIR)
	@rm -rf tests/graph/cases tests/metadata/cases

test: planner
	@echo "Running Unified Validation Suite..."
	@python3 tests/run_all.py
