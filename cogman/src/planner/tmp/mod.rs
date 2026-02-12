/*
 * cogman/src/planner/tmp/mod.rs - Temporary Resource Management
 *
 * This module coordinates the lifecycle of temporary build directories
 * and ephemeral resources used during the planning and execution phases.
 *
 * Why: To prevent side-effect leakage and ensure that every build 
 * workspace is deterministically initialized and destroyed.
 */

pub mod lifecycle;

