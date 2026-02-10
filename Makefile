# Roguelinux Main Makefile
# Delegates to cogman components

PLANNER_DIR = cogman/planner
EXECUTOR_DIR = cogman/executor
TARGET_DIR = cogman/planner/target/debug

.PHONY: all clean test planner executor

all: planner executor

planner:
	@echo "Building Cogman Planner..."
	@cd $(PLANNER_DIR) && cargo build

executor:
	@echo "Building Cogman Executor..."
	@$(MAKE) -C $(EXECUTOR_DIR)

clean:
	@cd $(PLANNER_DIR) && cargo clean
	@$(MAKE) -C $(EXECUTOR_DIR) clean
	@rm -rf tests/graph/cases tests/metadata/cases

test: planner
	@echo "Running Unified Validation Suite..."
	@python3 tests/run_all.py
