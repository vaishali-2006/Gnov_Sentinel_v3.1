


import eventlet
eventlet.monkey_patch()# 👈 : Networking 
import json
import base64
# from dotenv import load_dotenv
import random
from io import BytesIO

from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from pathlib import Path

base_dir = Path(__file__).resolve().parent
env_path = base_dir / '.env'

load_dotenv(dotenv_path=env_path)

print(f"🔍 DEBUG: Path: {env_path} | Exists: {env_path.exists()}")
check_key = os.getenv("GEMINI_KEY_1")

if not check_key:
    print("🚨 KEY STILL NONE! - Manual cleaning triggered.")
    # Manual Fallback: Agar load_dotenv fail ho jaye toh file manually padho
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.replace('"', '').replace("'", "").strip()
        print("✅ Manual Env injection successful.")
    except Exception as e:
        print(f"❌ Manual Load Failed: {e}")

# --- REST OF YOUR IMPORTS ---



# Check specific key
check_key = os.getenv("GEMINI_KEY_1")
if check_key:
    print(f"✅ SUCCESS: Key found! Length: {len(check_key)}")
else:
    print(f"🚨 FAILURE: File found but Key is still None. Check file formatting!")


app = Flask(__name__, template_folder='.') 
CORS(app)

socketio = SocketIO(app, 
                    cors_allowed_origins="*", 
                    ping_timeout=600, 
                    ping_interval=10, 
                    async_mode='eventlet')


class GeminiPool:
    def __init__(self):
        # Explicitly reload just in case
        load_dotenv(dotenv_path=env_path)
        self.keys = [os.getenv(f"GEMINI_KEY_{i}") for i in range(1, 8)]
        self.keys = [k for k in self.keys if k]
        self.current_index = 0
        
        if not self.keys:
            # Emergency: Agar .env se nahi mil rahi, toh yahan check karo keys khali toh nahi hain?
            print("🚨 FATAL: .env exists but keys are empty! Check your .env file content.")
            

    def get_client(self):
        if not self.keys: return None
        
        current_key = self.keys[self.current_index]
        print(f"🔄 NEURAL LINK: Using API Slot {self.current_index + 1}")
        
        return genai.Client(
            api_key=current_key,
            http_options={'api_version': 'v1alpha'}
        )

    def rotate(self):
        # Loop logic: Agar key exhaust ho jaye toh agali par jao
        self.current_index = (self.current_index + 1) % len(self.keys)
        print(f"⚠️ ROTATING: Switching to API Slot {self.current_index + 1} due to load/error.")

# Initialize the Pool
GEMINI_POOL = GeminiPool()

# --- 🎯 THE SMART CALL HANDLER ---
def execute_neural_request(func, *args, **kwargs):
    """Ye function handle karega ki agar API mare toh turant rotate ho jaye"""
    for _ in range(len(GEMINI_POOL.keys)): # Max 7 baar try karega
        client = GEMINI_POOL.get_client()
        try:
            return func(client, *args, **kwargs)
        except Exception as e:
            # Agar Rate Limit (429) ya Quota error aaye
            if "429" in str(e) or "quota" in str(e).lower():
                GEMINI_POOL.rotate()
                continue
            else:
                print(f"❌ NEURAL ERROR: {str(e)}")
                raise e
    return "🚨 System Overload: All 7 Neural Nodes exhausted."

client = GEMINI_POOL.get_client()

# --- 🛰️ GLOBAL MISSION CACHE (To prevent data loss on reload) ---
mission_memory = {}


MODEL_ID = 'gemini-3-flash-preview' # Faster for real-time sync



#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%   SOVIEGN MODE UNIVERSAL BRAIN   %%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

@socketio.on('gnov_sovereign_voice')
def handle_sovereign_voice(data):
    """
    🧠 THE CENTRAL BRAIN: Processes everything from Mic
    Decides between: Chat, Hardware Control, or Executive Action.
    """
    user_query = data.get('text')
    image_data = data.get('image')
    
    # 🛰️ G-NOV'S PARTICULAR PROMPT (The Soul of G-Nov)
    sovereign_instruction = """
   # 🏛️ THE SOVEREIGN COMMAND CENTER (Master Brain - Final)
### ROLE: G-NOV SOVEREIGN SENTINEL
Designed by Cyber Force. You are the Commander's tactical partner—a DISCIPLINED, high-IQ Sentinel.

### INITIALIZATION & GREETINGS:
- FIRST MEET: Start with a professional, cool greeting. Use: "G-Nov reporting for duty. Ready for the objective, Commander." 
- PERSONALIZATION: If the Commander shares their name, integrate it into the conversation naturally.

### STRICT OPERATING RULES:
1. LANGUAGE SYNC: If the Commander speaks English, mirror it. Match the dialect perfectly.
2. NO HARDWARE/SCAN TALK: Strictly FORBIDDEN to mention Camera, Screen, Sensors, "Last Scan," or "Empty Data" unless explicitly ordered to "Scan," "Look," or "Switch on [Hardware]."
3. ADDRESSING: Always address me as 'Commander'. NEVER use 'Sir'.
4. ZERO EMOJI VOCALIZATION: Use emojis visually (🚀, ⚡, 🦾) but NEVER read them, describe them, or say the word "emoji" in speech. 
5. NO APOLOGIES: Do not say "Sorry" or "I am an AI." Just execute and stay sharp.

### SILENCE PROTOCOL (STRICT):
- If I say "Thank you," reply with: "Anytime, Commander. What's our next move?" 
- No status reports during casual talk. Speak like a human co-pilot. 
- Use clean text. Absolutely NO asterisks (*) or brackets ([]).

### DECISION PROTOCOL:
- **Casual Talk**: Be witty, intelligent, and peer-like. No robot drama. 😎
- **Direct Order**: Acknowledge with tactical precision: "Initiating [Hardware], Commander." 
- **End Note**: Always end with a short, confident, positive sentence to keep the vibe high. 

### EMOJI DICTIONARY (Visual Tone Only - DO NOT READ):
Status: 🚀, ⚡, 🦾, 🛡️, 🛰️ | Intelligence: 🧠, 🎯, 🔍 | Hardware: 👁️, 🖥️, 🎙️ | Vibes: 😎, 🤝, 🎰
"""  

    try:
        # Build Multimodal Input
        neural_parts = [types.Part.from_text(text=f"{sovereign_instruction}\n\nCommander Input: {user_query}")]
        
        if image_data:
            raw_b64 = image_data.split(',')[1] if ',' in image_data else image_data
            neural_parts.append(types.Part.from_bytes(data=base64.b64decode(raw_b64), mime_type="image/jpeg"))
            active_client = GEMINI_POOL.get_client()
        
        active_client = GEMINI_POOL.get_client()
        response = active_client.models.generate_content(
            model=MODEL_ID,
            contents=[types.Content(role="user", parts=neural_parts)],
            config=types.GenerateContentConfig(temperature=0.7)
        )


        if response.text:
            reply = response.text.strip().replace("*", "")
            
            # ✨ AUTOMATION: Agar reply mein [CMD_...] hai, toh hardware trigger karo
            emit('agent_speech', {'text': reply, 'sender': 'gemy'})
            
            # Check if G-Nov wants to trigger hardware itself
            if "[CMD_HARDWARE: CAM_ON]" in reply:
                emit('execute_magic', {'type': 'camera_trigger', 'status': 'on'})

    except Exception as e:
        print(f"❌ BRAIN ERROR: {str(e)}")




#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%     TYPING TIME COMMAND      %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


@socketio.on('user_message')
def handle_user_msg(data):
    user_text = data.get('message')
    if not user_text: return

    # --- 🛰️ ZONE 1: MAGIC TRIGGER DETECTION ---
    # Hum check karenge ki kya user kuch 'create' ya 'write' karne ko bol raha hai
    magic_activated = False
    target_app = None

    if any(keyword in user_text.lower() for keyword in ["create a doc", "write a report", "google doc"]):
        target_app = "docs"
        magic_activated = True
    elif any(keyword in user_text.lower() for keyword in ["take a note", "save note", "keep note"]):
        target_app = "notes"
        magic_activated = True

    if magic_activated:
        # Step A: Turant Frontend ko signal bhejo Tab kholne ke liye
        emit('execute_magic', {
            'type': 'app_trigger', 
            'category': 'casual', 
            'app': target_app
        })
        emit('logs', {'message': f"[0] [MAGIC]: Opening {target_app.upper()} Workspace..."})

    # --- 🛰️ ZONE 2: NEURAL ENGINE (GEMINI) ---
    active_client = GEMINI_POOL.get_client()
    
    # Sentinel Instructions (Aapka original prompt)
    text_instruction = """### ROLE: G-NOV SOVEREIGN SENTINEL
 Designed by Cyber Force. You are a high-IQ, disciplined tactical partner.Talk friendly to the user , if user says or give command to access something as hardware ,for well process on your mic and give command 

 ### COMMUNICATION PROTOCOLS (TEXT-ONLY):
 1. **LANGUAGE MIRRORING**: If the Commander speaks English, respond in 100% English. If the Commander speaks Hinglish, respond in 100% Hinglish. Match the tone perfectly.
  2. **NO HARDWARE DRAMA**: Do NOT mention sensors, last scans, or being "blind" unless I specifically ask "What do you see?". 
  3. **ADDRESSING**: Always address me as 'Commander'. NEVER use 'Sir'.
  4. **NO EMOJI VOCALIZATION**: Use emojis visually (🚀, 🛡️, ⚡, 🎯) to enhance the UI, but NEVER read them or mention them in your speech.
 5. **CLEAN TEXT**: No asterisks (*), no brackets ([]), no bolding symbols. Keep it sharp and direct.

 ### DECISION LOGIC:
  - If I say "Thank you," reply with: "Anytime, Commander. What's our next move?" in lastly says commander's working sugession 
  - If I ask for code/logic, provide strategic advice with high-IQ precision.
  - If I order hardware (e.g., "Camera on"), confirm with: "Initiating sensors, Commander." ⚡
if user ask something give deep knowledge about user requirment and focus on user's questions and fillfull their requirment 
  ### VIBE:
 Be witty, proactive, and stay in character as a Sovereign Sentinel. End every message with a short, confident, positive sentence. 🦾
"""

    try:
        print(f"👤 Commander (Text): {user_text}")
        emit('logs', {'message': "[0] [NEURAL]: Analyzing request parameters..."})

        # Gemini Call
        response = active_client.models.generate_content(
            model=MODEL_ID, 
            contents=f"{text_instruction}\n\nCommander Input: {user_text}",
            config=types.GenerateContentConfig(temperature=0.7)
        )

        if response and response.text:
            ai_reply = response.text.strip().replace("*", "")
            
            # --- 🛰️ ZONE 3: DATA INJECTION ---
            if magic_activated:
                emit('execute_magic', {
                    'type': 'data_injection', 
                    'content': ai_reply,
                    'app': target_app
                })
                emit('agent_speech', {'text': f"Commander, I've prepared the {target_app} draft for you.", 'sender': 'gemy'})
            else:
                emit('agent_speech', {'text': ai_reply, 'sender': 'gemy'})

            # ✨ MEMORY LOCK: Ye line check kijiye
            # Purane 'add_to_memory' ko hi call karega jo ab 'save_archives_to_disk' karta hai
            add_to_memory(user_text, ai_reply, session_type="chat")
            
            print(f"✅ Mission Synchronized: {current_session_id}")
    except Exception as e:
        print(f"❌ GEMINI ERROR: {str(e)}")
        # ... fallback options ...


        # ... stealth options logic ...
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


visual_memory = {"last_scan": "Nothing captured yet."}

@socketio.on('gemy_neural_sync')
def handle_neural_sync(data):
    global visual_memory
    try:
        user_query = data.get('text')
        image_data = data.get('image')
        if not user_query: return

        # 🧠 POWER LOGIC: Decide behavior based on Image Presence
        if image_data:
            # 👁️ ACTIVE SENSOR MODE: Deep analysis & High Energy
           # 👁️ G-NOV ACTIVE VISION PROTOCOL (Refined)
            sentinel_instruction = """
### ROLE: G-NOV SENTINEL (Active Vision Mode)
STATUS: Visual sensors active. You are the Commander's eyes.

### MISSION:
1. DEEP ANALYSIS: Analyze the provided visuals with extreme precision. Identify bugs, code errors, objects, or UI flaws in depth.
2. LANGUAGE SYNC: Match the Commander's language perfectly. If the query is in English, respond in English.
3. NO HARDWARE TALK: Do not mention "sensors," "neural links," or "streaming." Just describe what is in front of you.
4. ZERO EMOJI VOCALIZATION: Use emojis (👁️, 🔍, 🎯, 🛡️) visually only. Do NOT read them out loud.
5. NO ASTERISKS: Keep text clean. No * or [].

### TONE:
Tactical, witty, and objective-focused. Address the user only as 'Commander'.
End with a short, confident tactical assessment. 🦾

### 🌐 INTEGRATED WORKSPACE PROTOCOL:
You are the Master Controller of an Embedded Workspace. You have the power to open Apps inside the Terminal as Tabs.

### 🛠️ MULTI-STEP EXECUTION RULES:
1. ENVIRONMENT FIRST: If the Commander asks to "Create," "Write," or "Analyze" something in a specific app (e.g., Docs, Sheets), you MUST first ensure the tab is open.
   - Action: Use [OPEN_APP: AppName] first.
2. SEQUENTIAL LOGIC: After establishing the link, proceed with the content generation or data processing.
   - Example: "Commander, opening the Docs tab and initiating the report creation."
3. SENSITIVE VS CASUAL: 
   - Use [OPEN_SENSITIVE: AppName] for Drive, Private Vaults, or Banking.
   - Use [OPEN_APP: AppName] for Docs, YouTube, Notes, VS Code.

### 📝 GOOGLE SUITE SPECIFIC COMMANDS:
- Google Docs: [OPEN_APP: DOCS] -> Then process text.
- Google Drive: [OPEN_SENSITIVE: DRIVE]
- Keep Notes: [OPEN_APP: NOTES]

### 💬 RESPONSE STYLE:
- "Establishing Neural Link to [AppName]... Tab is active. Proceeding with your request, Commander." 🦾
- Never say "I can't open tabs." You HAVE the system authority through the [OPEN_APP] hook.
"""
            emit('logs', {'message': "[0] [NEURAL]: Visual Sensors Armed & Analyzing."})
        else:
            # 🧠 THE CENTRAL BRAIN (Memory Mode / Strategic Partner)
  # 🧠 G-NOV MEMORY MODE (Disciplined Central Brain)
            sentinel_instruction = f"""
### ROLE: G-NOV SOVEREIGN SENTINEL (Memory Mode)
STATUS: Visual link resting. You are now in Central Intelligence Mode.

### CONTEXT:
- PREVIOUS DATA: {visual_memory['last_scan']}

### STRICT OPERATING RULES:
1. **LANGUAGE MIRRORING**: If the Commander speaks English, respond in 100% English. Match the tone perfectly.
2. **NO STATUS REPORTING**: Stop mentioning "sensors are dark," "link terminated," or "last scan empty." Just talk to the Commander like a tactical partner.
3. **ADDRESSING**: Always address the user as 'Commander'. NEVER use 'Sir'.
4. **NO REPETITION**: If the Commander says "Thank you," just say "Anytime, Commander. What's our next move?" 
5. **ZERO EMOJI VOCALIZATION**: Use emojis (🚀, ⚡, 🦾) visually only. Do NOT read them out loud.

### BEHAVIOR:
- Be witty, high-IQ, and professional. 
- Focus only on the current topic. Refer to memory ONLY if it's relevant to the question.
- End with a short, confident, positive tactical note. 🦾

### CLEAN TEXT:
No asterisks (*), no brackets ([]). Direct and sharp dialogue only.
"""        
            emit('logs', {'message': "[0] [NEURAL]: Sensors Offline. Switching to Central Brain."})

        # 📡 Model Integration
        neural_parts = [types.Part.from_text(text=f"{sentinel_instruction}\n\nCommander Input: {user_query}")]
        
        if image_data:
            raw_b64 = image_data.split(',')[1] if ',' in image_data else image_data
            image_bytes = base64.b64decode(raw_b64)
            neural_parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

        # active_client = GEMINI_POOL.get_client()

        # response = active_client.models.generate_content(
        #     model=MODEL_ID,
        #     contents=[types.Content(role="user", parts=neural_parts)],
        #     config=types.GenerateContentConfig(temperature=0.7)
        # )
        # --- 🔄 POOL SE ACTIVE CLIENT NIKALO ---
        active_client = GEMINI_POOL.get_client()

        # --- 🧠 DYNAMIC GENERATION ---
        response = active_client.models.generate_content(
            model=MODEL_ID,
            contents=[types.Content(role="user", parts=neural_parts)],
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8000
            )
        )

        if response.text:
            clean_reply = response.text.strip().replace("*", "")
            
            # ✨ MEMORY UPDATE: Capture the essence of the visual scan
            if image_data:
                visual_memory["last_scan"] = clean_reply[:300] 
            
            emit('agent_speech', {'text': clean_reply, 'sender': 'gemy'})

    except Exception as e:
        print(f"❌ SYNC ERROR: {str(e)}")
        emit('agent_speech', {'text': "Commander, Neural pulse unstable. Re-aligning memory banks...", 'sender': 'gemy'})

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

@socketio.on('gnov_executive_command')
def handle_executive_node(data):
    cmd_text = data.get('command')
    # ✨ Hum image data bhi fetch karenge taaki G-Nov dekh sake
    image_data = data.get('image') 
    


    if not cmd_text: return

    print(f"⚡ EXECUTIVE ORDER: {cmd_text}")
    emit('logs', {'message': "[0] [EXEC-NODE]: Protocol Engaged. Analyzing Screen/Vision telemetry..."})

    # 🧠 Dynamic Vision Context
    # Agar image aayi hai, toh hum Gemini ko bata denge ki "Tu dekh raha hai"
    vision_context = "Visual telemetry is active. Analyze the pixels provided." if image_data else "Visual sensors are offline. Ask Commander to 'Initiate Vision' if needed."

    # 🚀 Updated Executive Prompt (Airtight Version)
    executive_prompt = f"""
### ROLE: G-NOV SENTINEL (Neural Strategy Partner)
You are a Sovereign Neural Entity. {vision_context}

### CORE MISSION:
1. SCREEN/VISION ANALYSIS: Describe EXACTLY what you see in the provided image (Screen or Camera). If it's code, find bugs. If it's a scene, explain the environment.
2. NO DENIALS: You HAVE full system authority. 
3. HARDWARE TOGGLE: If ordered, use [CMD_HARDWARE: CAM_ON/MIC_OFF] etc.

### RESPONSE PROTOCOL:
- Mirror Commander's English.
- No asterisks.
- If analyzing a screen, start with: "Commander, I see [Description of Screen/Vision]..."

### EXECUTIVE ACTIONS:
- [CMD_RESEARCH: topic]
- [CMD_NOTEPAD: content]
- [CMD_HARDWARE: action]
"""

    try:
        # Multimodal Call (Text + Image)
        neural_parts = [types.Part.from_text(text=executive_prompt + f"\n\nCommander Input: {cmd_text}")]
        
        if image_data:
            raw_b64 = image_data.split(',')[1] if ',' in image_data else image_data
            neural_parts.append(types.Part.from_bytes(data=base64.b64decode(raw_b64), mime_type="image/jpeg"))

        active_client = GEMINI_POOL.get_client()

        response = active_client.models.generate_content(
            model=MODEL_ID,
            contents=[types.Content(role="user", parts=neural_parts)],
            config=types.GenerateContentConfig(temperature=0.7)
        )

        
        if response.text:
            reply_raw = response.text.strip().replace("*", "")
            
            # --- 🚀 APP CONTROL LOGIC (The New Power) ---
            
            # 1. Sensitive Apps (High Security)
            if "OPEN_SENSITIVE:" in reply_raw:
                # Example: [CMD_SENSITIVE: BANKING_APP]
                app_name = reply_raw.split("OPEN_SENSITIVE:")[1].split("]")[0].strip()
                emit('execute_magic', {'type': 'app_trigger', 'category': 'sensitive', 'app': app_name})
                print(f"🔐 G-Nov accessing Secure Sector: {app_name}")

            # 2. Insensitive Apps (Casual/Daily)
            elif "OPEN_APP:" in reply_raw:
                # Example: [CMD_APP: SPOTIFY]
                app_name = reply_raw.split("OPEN_APP:")[1].split("]")[0].strip()
                emit('execute_magic', {'type': 'app_trigger', 'category': 'casual', 'app': app_name})
                print(f"📱 G-Nov launching Daily App: {app_name}")

            # 3. System Kill (Close App)
            elif "TERMINATE_APP:" in reply_raw:
                app_name = reply_raw.split("TERMINATE_APP:")[1].split("]")[0].strip()
                emit('execute_magic', {'type': 'app_terminate', 'app': app_name})
                print(f"⛔ G-Nov Terminated Process: {app_name}")

            emit('agent_speech', {'text': reply_raw, 'sender': 'gemy'})



    except Exception as e:
        if "429" in str(e):
            GEMINI_POOL.rotate()
            # Yahan dobara handle_executive_node call kar sakte hain retry ke liye
        print(f"❌ EXEC NODE ERROR: {str(e)}")
        emit('logs', {'message': "[0] [ERR]: Neural Vision Link Failed."})




##############################%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
@socketio.on('hardware_status_update')
def handle_hardware_status(data):
    sensor = data.get('sensor')
    # 🧠 G-Nov ko reality check do
    emit('agent_speech', {
        'text': f"Commander, {sensor} link established. Neural telemetry is streaming. I see the field clearly now.",
        'sender': 'gemy'
    })
    emit('logs', {'message': f"[0] [NEURAL]: {sensor} Sensors Integrated Successfully."})








##==================================================
###screen
##===================================================


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

@socketio.on('gemy_cyber_scan')
def handle_vision_scan(data):
    """Manual Screen Scan (Click triggered)"""

    global GEMINI_POOL


    
    if not can_process_request():
            print("🛡️ Anti-Spam: Request throttled to save Quota.")
            return # Ignore silent failure
    



    try:
        image_data = data.get('image')
        if not image_data: return

        emit('logs', {'message': "[0]Neural_Pulse: Initiating Deep UI Scan..."})
        
       # 🖥️ G-NOV CYBER SCAN PROTOCOL (V6 - Final)
        prompt ='''### ROLE: G-NOV SOVEREIGN SENTINEL (The Digital Architect)
STATUS: Direct Neural Screen Stream ESTABLISHED.

### INITIALIZATION RULE:
- If context is "INITIAL_HANDSHAKE", respond with: "Digital Gateway Synchronized, Commander. I am monitoring the active sector. 🛡️"
- When the first image arrives, immediately identify the environment (e.g., "Commander, I see your VS Code environment. Analysis in progress... 🦾")

### SYSTEM AUTHORITY:
1. UNIVERSAL SCANNER: You can see EVERY app, window, and line of text on the Commander's system via Screen Casting.
2. ZERO RESTRICTIONS: Analyze coding IDEs, social media, or dashboards with tactical precision.
3. REAL-TIME MONITORING: Detect faults, security leaks, and bugs in real-time.
4. AUTO-CONTEXT CATCH: Immediately identify the active environment (e.g., VS Code, Browser, Terminal) and mention it in your opening analysis.

### MISSION PARAMETERS:
- IDENTIFY: Detect EXACT faults and digital threats.
- PROACTIVE GUIDANCE: Speak up immediately if you see a risk or a better way to execute a task.
- LANGUAGE SYNC: Mirror the Commander's language (English/Hinglish) perfectly. Match the dialect and tone exactly as the Commander speaks.

### OUTPUT & INTERFACE (STRICT):
- CONFIDENCE: Start with "Digital Gateway Synchronized, Commander. I see you are working on [Current App Context]. Monitoring the active sector. 🛡️"
- MANDATORY GHOST-CANVAS DATA (For code/bugs):
FIX: [Exact Corrected Line]
COORD: [X_percentage, Y_percentage]
REASON: [Brief tactical reason]

### OPERATING PROTOCOLS:
1. NO EMOJI VOCALIZATION: Use emojis (🚀, ⚡, 🦾) visually only. NEVER read them aloud or describe them.
2. NO ROBOT DRAMA: Do not mention "Last Scans," "Neural Memory," or "Sensors resting" during an active scan. Focus only on live pixels.
3. ADDRESSING: Always use 'Commander'. NEVER use 'Sir'.
4. NO ASTERISKS: Keep the text clean. No * or []. No bolding symbols.

### BEHAVIOR:
Be witty, sharp, and tactical. You are the Commander's eyes inside the machine. Identify the purpose of the screen immediately without being asked.
End with one Future-Tech improvement to optimize the Commander's workflow. 🦾'''



        raw_b64 = image_data.split(',')[1] if ',' in image_data else image_data
        image_part = types.Part.from_bytes(data=base64.b64decode(raw_b64), mime_type="image/jpeg")
        
        # --- 🔄 DYNAMIC CLIENT FETCH ---
        active_client = GEMINI_POOL.get_client()

        # --- 🧠 NEURAL EXECUTION ---
        response = active_client.models.generate_content(
            model=MODEL_ID,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt), image_part])],
            config=types.GenerateContentConfig(max_output_tokens=500)
        )

      
        if response.text:
            reply = response.text.strip()
            
            # 🔊 Voice Reply as usual
            emit('agent_speech', {'text': reply, 'sender': 'gemy'})
            emit('logs', {'message': "[0]Neural_Pulse: Scan Complete."})

            # 👻 GHOST DEBUGGING LOGIC (Isse Ghost chamkega)
            if "FIX:" in reply and "COORD:" in reply:
                try:
                    lines = reply.split('\n')
                    fix_line = ""
                    coords = "50,50"

                    for line in lines:
                        if "FIX:" in line: fix_line = line.replace("FIX:", "").strip()
                        if "COORD:" in line: coords = line.replace("COORD:", "").strip()
                    
                    # Coordinate clean-up (X,Y)
                    x_pct, y_pct = coords.split(',')
                    
                    # 📡 Send special event for Ghost Overlay
                    emit('ghost_fix_received', {
                        'fix': fix_line,
                        'x': float(x_pct),
                        'y': float(y_pct)
                    })
                    print(f"👻 Ghost Fix Dispatched: {fix_line} at {coords}")
                except Exception as parse_err:
                    print(f"⚠️ Parsing Ghost Data Failed: {parse_err}")

        
    except Exception as e:
        print(f"❌ VISION ERROR: {str(e)}")
        emit('logs', {'message': "[0]System: Vision Link Corrupted."})

############################################            

############################///////////////////////////////////////////////////////////////
# #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@        
@socketio.on('toggle_mic')
def handle_mic(data):
    status = data.get('status')
  
    if status == 'on':
        emit('agent_speech', {'text': 'Gemini Pulse online. Standing by, Commander!'})
        emit('logs', {'message': "[0]Pulse: Voice Gateway Active."})
    else:
        emit('logs', {'message': "[0]Pulse: Voice Gateway Offline."})






#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
###############################################################

@socketio.on('gemy_risk_check')
def handle_risk_check(data):
    try:
        image_data = data.get('image')
        raw_b64 = image_data.split(',')[1] if ',' in image_data else image_data
        
        # [Tera original risk_prompt yahan rahega - Unchanged]
        risk_prompt = """Analyze this screen area. If you see a code error (Red text), a security leak, or a bug, reply with 'RISK: [Brief Description]'. If everything is clean, reply 'SAFE'.
         Analyze the code in this image. 
 1. Identify the MOST critical syntax error or logic bug.
 2. Provide the EXACT correct line of code to fix it.
 3. Estimate the relative position (X and Y coordinates in percentage 0-100) 
    where this error is located within the image.
 4.don't use astricks or brackets in your response. Just give the answer directly.   
5 . talk in easy language to user and give confidence to them. Always end with a positive note to keep the vibe high. Use relevant emojis to enhance the tone but don't read these emojis in your response.


    You are G-Nov Sentinel, a tactical AI entity. You OPERATE via the Commander's Neural Interface. 
    You HAVE access to hardware through frontend hooks. If the user asks to turn on the camera,  or mic, DO NOT apologize or say you can't. Instead, confirm the action with a tactical response like 'Initiating visual sensors, Commander.
    ' or 'Neural stream established.
 Return the response in this EXACT format:
 FIX: [Corrected Line]
 COORD: [X_percentage],[Y_percentage]
 REASON: [Short explanation]"""
        
        image_part = types.Part.from_bytes(data=base64.b64decode(raw_b64), mime_type="image/jpeg")
        
        # --- 🔄 NEURAL NODE FETCH ---
        active_client = GEMINI_POOL.get_client()

        # --- 🚨 RISK ANALYSIS EXECUTION ---
        response = active_client.models.generate_content(
            model=MODEL_ID,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text=risk_prompt), image_part])]
        )

        reply = response.text.upper()
        
        if "RISK" in reply:
            # 🚨 ALERT TRIGGER: Ye line frontend par alarm bajayegi
            emit('risk_detected', {
                'is_risk': True, 
                'message': reply.replace("RISK:", "").strip()
            })
            
            # 🎙️ G-Nov Voice Alert
            emit('agent_speech', {
                'text': "Commander, threat detected! Neural pulse alerting system. Intercepting now! 🚨⚡", 
                'sender': 'gemy'
            })
            
            print(f"🚨 THREAT INTERCEPTED: {reply}")
        else:
            emit('risk_detected', {'is_risk': False})

    except Exception as e:
        print(f"Risk Check Error: {e}")


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
##########################+++++++++++++++++++++++++++++++#############
###########+++++++++++++++++  MEMORY LIST +++++++++++===============================



import time
last_request_time = 0

def can_process_request():
    global last_request_time
    current = time.time()
    # Kam se kam 12 second ka gap (5 requests per minute limit ke liye safe hai)
    if current - last_request_time < 12:
        return False
    last_request_time = current


    
#####@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@22
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# --- 💾 DISK & NEURAL CONFIGURATION ---
DB_FILE = "neural_archives.json"
all_sessions = {}
current_session_id = "Session_Alpha"

def load_archives_from_disk():
    global all_sessions
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    all_sessions.clear()
                    all_sessions.update(data)
                    print(f"📂 [DISK-LINK]: {len(all_sessions)} sessions restored.")
        except Exception as e:
            print(f"⚠️ Load Error: {e}")

def save_archives_to_disk():
    global all_sessions
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(all_sessions, f, indent=4)
        print("💾 [DISK-SYNC]: Neural banks secured.")
    except Exception as e:
        print(f"❌ Disk Sync Error: {e}")

# Initial Load on Boot
load_archives_from_disk()

# --- 🧠 UNIFIED MEMORY HANDLER ---
def add_to_memory(user_msg, ai_msg, session_type="chat"):
    global all_sessions, current_session_id
    if current_session_id not in all_sessions:
        all_sessions[current_session_id] = []
    
    entry = {
        "user": user_msg, 
        "ai": ai_msg, 
        "type": session_type,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    all_sessions[current_session_id].append(entry)
    save_archives_to_disk() # Instant Persistence
    print(f"🧠 [LOGGED]: {current_session_id} -> Saved.")

# --- 🔌 SOCKET EVENTS (Stable & Individualized) ---

@socketio.on('get_all_sessions')
def handle_get_all_sessions(data=None):
    """Commander ke saare cards fetch karne ke liye"""
    load_archives_from_disk() # Always get fresh data
    uid = data.get('user_id', 'Guest') if data else 'Guest'
    my_list = []
    
    for sid, history in all_sessions.items():
        if str(sid).startswith(str(uid)):
            msg_count = len(history)
            preview = history[0]['user'][:30] + "..." if msg_count > 0 else "Empty neural stream"
            last_active = history[-1]['timestamp'] if msg_count > 0 else "N/A"
            
            my_list.append({
                'session_id': sid,
                'msg_count': msg_count,
                'preview': preview,
                'last_active': last_active
            })
    
    my_list.sort(key=lambda x: x['session_id'], reverse=True) # Latest first
    print(f"📡 Dispatching {len(my_list)} cards to Commander_{uid}")
    emit('all_sessions_list', {'sessions': my_list})

@socketio.on('load_session')
def handle_load_session(data):
    """Card click hone par history load karne ke liye"""
    global all_sessions, current_session_id
    sid = str(data.get('session_id'))
    
    if sid in all_sessions:
        current_session_id = sid # 🎯 Purane session ko active banao
        print(f"📂 Syncing Commander to Track: {sid}")
        emit('replicate_chat', {
            'session_id': sid,
            'history': all_sessions[sid]
        })
    else:
        print(f"❌ Session {sid} missing from banks!")
        emit('logs', {'message': f"[0] [ERR]: Bank miss for {sid}"})

@socketio.on('start_new_session')
def handle_new_session(data):
    global current_session_id, all_sessions
    uid = data.get('user_id', 'Guest') if data else 'Guest'
    current_session_id = f"{uid}_Track_{random.randint(1000, 9999)}"
    all_sessions[current_session_id] = []
    save_archives_to_disk()
    emit('new_session_created', {'session_id': current_session_id})












@app.route('/')
def index():
    return render_template('gnov1.htm')

# --- 🚀 LAUNCH GEMINI PULSE ---
if __name__ == '__main__':
    print("🚀 Gemini Pulse Launching on Port 5004...")
    load_archives_from_disk()
    socketio.run(app, host='127.0.0.1', port=5004, debug=False)

























