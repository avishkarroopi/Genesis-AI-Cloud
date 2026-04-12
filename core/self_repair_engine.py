"""
GENESIS Self-Repair Engine
Analyzes system failures and auto-repairs code or configuration.
Implements File-Modification Safeguards per Phase 2.5 rules.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from core.event_bus import get_event_bus

logger = logging.getLogger(__name__)

# Mandatory Safeguard - Protected Core Files
PROTECTED_CORE_FILES = {
    "core/event_bus.py",
    "core/voice_agent.py",
    "core/genesis_voice.py",
    "core/brain_chain.py",
    "core/start_genesis.py",
    "core/system.py"
}

PROPOSAL_DIR = Path("logs/patch_proposals")

class SelfRepairEngine:
    def __init__(self):
        self.bus = get_event_bus()
        os.makedirs(PROPOSAL_DIR, exist_ok=True)
        
    async def start(self):
        if self.bus:
            self.bus.subscribe("system_failure", self.handle_failure)
            logger.info("[SELF REPAIR] Engine started and subscribed to system_failure events.")
            
    async def handle_failure(self, source: str, failure_data: dict):
        """Analyze failure and trigger repair."""
        logger.info(f"[SELF REPAIR] Analyzing failure from {source}: {failure_data}")
        # Placeholder for AI analysis of logs/failures
        # If the analysis decides a file needs modification, it calls apply_patch.
        
    def apply_patch(self, file_path: str, patch_content: str, reason: str):
        """Safely apply a patch with core protection rules."""
        # Normalize file path for comparison
        normalized_path = os.path.normpath(file_path).replace("\\", "/")
        is_protected = any(normalized_path.endswith(p) for p in PROTECTED_CORE_FILES)
        
        if is_protected:
            logger.warning(f"[SELF REPAIR] BLOCKING modification to protected file: {file_path}")
            self._generate_patch_proposal(file_path, patch_content, reason)
        else:
            logger.info(f"[SELF REPAIR] Applying patch to non-protected file: {file_path}")
            try:
                with open(file_path, "w") as f:
                    f.write(patch_content)
                logger.info(f"[SELF REPAIR] Successfully repaired {file_path}")
            except Exception as e:
                logger.error(f"[SELF REPAIR] Failed to patch {file_path}: {e}")
                
    def _generate_patch_proposal(self, file_path: str, patch_content: str, reason: str):
        """Generates a patch proposal for human/admin approval."""
        filename = os.path.basename(file_path)
        proposal_file = PROPOSAL_DIR / f"patch_proposal_{filename}.json"
        
        proposal = {
            "status": "pending_approval",
            "file": file_path,
            "reason": reason,
            "patch": patch_content
        }
        
        with open(proposal_file, "w") as f:
            json.dump(proposal, f, indent=4)
            
        logger.info(f"[SELF REPAIR] Patch proposal generated: {proposal_file}. Waiting for approval.")
        
def start_self_repair_engine():
    engine = SelfRepairEngine()
    asyncio.create_task(engine.start())
    return engine
