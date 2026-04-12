import webbrowser
import datetime
import subprocess
import os
import re

YOUTUBE_OPEN = False
BROWSER_OPEN = False

def check_and_execute_tool(command):
    cmd_lower = command.lower()
    
    # 1. Open browser
    if "open browser" in cmd_lower or "start browser" in cmd_lower or "launch browser" in cmd_lower:
        print("[TOOL] Executing: open browser", flush=True)
        global BROWSER_OPEN
        BROWSER_OPEN = True
        try:
            webbrowser.open("https://www.google.com")
        except Exception as e:
            print(f"[TOOL] Browser open error: {e}", flush=True)
        return "I have opened the browser for you."
    
    # 2. Time
    if cmd_lower in ["what time is it", "current time", "tell me the time", "what is the time"]:
        print("[TOOL] Executing: time", flush=True)
        now = datetime.datetime.now()
        return f"It is currently {now.strftime('%I:%M %p')}."
    
    # 3. Date
    if cmd_lower in ["what date is it", "today's date", "what is the date", "what day is it"]:
        print("[TOOL] Executing: date", flush=True)
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    
    # Memory update (remember name tool)
    match = re.search(r"^my name is (\w+)$", cmd_lower)
    if match:
        name = match.group(1).capitalize()
        from core.memory.memory_manager import set_user_name
        set_user_name(name)
        return f"I will remember your name is {name}."
 
    # 5. YouTube
    if "open youtube" in cmd_lower:
        print("[TOOL] Executing: open youtube", flush=True)
        global YOUTUBE_OPEN
        YOUTUBE_OPEN = True
        try:
            webbrowser.open("https://www.youtube.com")
        except Exception as e:
            print(f"[TOOL] YouTube open error: {e}", flush=True)
        return "I have opened YouTube for you."
 
    # 6. Open folder / file explorer
    if cmd_lower in ["open folder", "open explorer", "show files"]:
        print("[TOOL] Executing: open folder", flush=True)
        try:
            if os.name == 'nt':
                subprocess.Popen("explorer", shell=True)
            else:
                subprocess.Popen(["xdg-open", "."])
        except Exception as e:
            print(f"[TOOL] Explorer open error: {e}", flush=True)
        return "I have opened the file explorer."
 
    # 7. Open document / notepad
    if cmd_lower in ["open notepad", "create note", "open document"]:
        print("[TOOL] Executing: open notepad", flush=True)
        try:
            if os.name == 'nt':
                subprocess.Popen("notepad", shell=True)
        except Exception as e:
            print(f"[TOOL] Notepad open error: {e}", flush=True)
        return "I have opened a document for you."
 
    # 8. Remember something
    if cmd_lower.startswith("remember that "):
        print("[TOOL] Executing: remember", flush=True)
        from core.memory.memory_manager import load_memory, get_memory_key, set_memory_key
        data = load_memory()
        remembered = cmd_lower.replace("remember that ", "").strip()
        if remembered:
            if "notes" not in data:
                data["notes"] = []
            data["notes"].append(remembered)
            set_memory_key("notes", data["notes"])
            return f"I will remember: {remembered}."
        return "What should I remember?"
 
    # 9. What did I say / recall
    if cmd_lower in ["what did i say", "recall my last note", "what was the last thing"]:
        print("[TOOL] Executing: recall", flush=True)
        from core.memory.memory_manager import load_memory
        data = load_memory()
        notes = data.get("notes", [])
        if notes:
            last = notes[-1]
            return f"You last asked me to remember: {last}."
        return "I don't have anything saved yet."
 
    # 10. Run automation
    if cmd_lower in ["run automation", "trigger automate", "execute automation"]:
        print("[TOOL] Executing: automation", flush=True)
        try:
            from core import automation_engine
            result = automation_engine.trigger_webhook({"action": "user_request", "command": command})
            return result or "Automation triggered."
        except Exception as e:
            return f"Automation failed: {e}"

    # 11. Location
    if cmd_lower in ["what is my location", "where am i", "location", "what is your location"]:
        print("[TOOL] Executing: location", flush=True)
        return "I am operating from your local system."

    # 12. System Info
    if cmd_lower in ["system info", "system status", "what is your status"]:
        print("[TOOL] Executing: system info", flush=True)
        import platform
        return f"System is currently running on {platform.system()} {platform.release()}."

    # Play on YouTube
    if "play" in cmd_lower and "youtube" in cmd_lower:
        print("[TOOL] Executing: youtube play", flush=True)

        query = command.lower()
        query = query.replace("play", "")
        query = query.replace("in youtube", "")
        query = query.replace("on youtube", "")
        query = query.strip()

        url = "https://www.youtube.com/results?search_query=" + query.replace(" ", "+")

        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[TOOL] YouTube search error: {e}", flush=True)

        return f"Searching {query} on YouTube."

    if "close youtube" in cmd_lower or "close browser" in cmd_lower:
        print("[TOOL] Executing: close browser", flush=True)

        try:
            if os.name == "nt":
                subprocess.Popen("taskkill /IM chrome.exe /F", shell=True)
        except Exception as e:
            print(f"[TOOL] Browser close error: {e}", flush=True)

        return "Browser closed."

    if "is youtube open" in cmd_lower:
        if YOUTUBE_OPEN:
            return "Yes, YouTube is open."
        else:
            return "No, YouTube is not open."

    return None
