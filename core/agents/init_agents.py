import logging

logger = logging.getLogger(__name__)

def init_all_agents():
    try:
        from core.agents.file_agent import start_file_agent
        from core.agents.web_research_agent import start_web_research_agent
        from core.agents.browser_automation_agent import start_browser_automation_agent
        from core.agents.code_execution_agent import start_code_execution_agent
        from core.agents.communication_agent import start_communication_agent
        
        start_file_agent()
        start_web_research_agent()
        start_browser_automation_agent()
        start_code_execution_agent()
        start_communication_agent()
        
        logger.info("[INIT] Phase 1.5 Execution Agents started successfully.")
    except Exception as e:
        logger.error(f"[INIT] Failed to start agents: {e}")
