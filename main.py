import json, os, requests, datetime, re

try:
    with open("config.json") as f: GROQ_KEY=json.load(f).get("GROQ_API_KEY","")
except: GROQ_KEY=""

os.makedirs("memory", exist_ok=True)
MEM_FILE="memory/memory.json"
FACT_FILE="nova_knowledge.json"

def load_json(p,d):
    if os.path.exists(p):
        try:
            with open(p) as ff: return json.load(ff)
        except: return d
    return d
def save_json(p,data):
    with open(p,"w") as ff: json.dump(data,ff,indent=2)

memory=load_json(MEM_FILE,[])
facts=load_json(FACT_FILE,{"facts":[],"chat_count":0})
if isinstance(facts,list): facts={"facts":facts,"chat_count":0}

# ===== REAL-TIME TOOLS =====
def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %A - Africa/Harare GMT+2")

def get_weather(city="Gweru"):
    try:
        r=requests.get(f"https://wttr.in/{city}?format=%C+%t+%w+%h", timeout=5)
        if r.status_code==200: return f"Weather in {city}: {r.text}"
    except: pass
    return None

def web_search(query):
    try:
        # DuckDuckGo instant answer + Wikipedia fallback
        r=requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1", timeout=7)
        if r.status_code==200:
            data=r.json()
            if data.get("AbstractText"): return data["AbstractText"]
            if data.get("RelatedTopics"):
                t=data["RelatedTopics"][0]
                if isinstance(t, dict) and "Text" in t: return t["Text"]
        # Fallback to wttr search using ddg html quick
        r2=requests.get(f"https://api.duckduckgo.com/?q={query}&format=json", timeout=7)
        return None
    except:
        return None

def get_real_context(user_prompt):
    prompt_low=user_prompt.lower()
    context_parts=[f"CURRENT REAL TIME: {get_time()}"]
    
    # Auto weather if asked about weather/time/day
    if any(x in prompt_low for x in ["weather","temperature","hot","cold","rain"]):
        city="Gweru"
        # extract city name
        m=re.search(r"weather in (\w+)", prompt_low)
        if m: city=m.group(1)
        w=get_weather(city)
        if w: context_parts.append(w)
    
    # Auto search if question is factual/news/who is/what is
    if any(x in prompt_low for x in ["what time","who is","what is","news","price","score","when did","how many","latest","today"]):
        search=web_search(user_prompt)
        if search:
            context_parts.append(f"REAL-TIME SEARCH RESULT: {search[:500]}")
    
    return "\n".join(context_parts)

print("=== NOVA C-Type [ONLINE + REAL-TIME] ===")
print(f"Facts: {len(facts['facts'])} | Chat: {facts['chat_count']} | {get_time()}")
print("Nova now has real-time internet access!")

def learn(t):
    if any(x in t.lower() for x in ["i like","i live","my name","i am","i work"]):
        if t not in facts["facts"] and len(t)<200:
            facts["facts"].append(t)
            save_json(FACT_FILE,facts)
            print(f"[Nova learned: {t}]")

def ask_groq(prompt):
    if not GROQ_KEY or len(GROQ_KEY)<20: return None
    try:
        url="https://api.groq.com/openai/v1/chat/completions"
        headers={"Authorization": f"Bearer {GROQ_KEY}","Content-Type":"application/json"}
        mem_ctx="\n".join(facts["facts"][-10:])
        real_ctx=get_real_context(prompt)
        system=f"You are Nova, a C-Type evolving AI built in Gweru, Zimbabwe. You have REAL-TIME DATA access. Use this real context to answer: {real_ctx}. Memory about user: {mem_ctx}. Always use real time when user asks about time/date/weather. Be concise and friendly."
        data={"model":"openai/gpt-oss-20b","messages":[{"role":"system","content":system},{"role":"user","content":prompt}],"temperature":0.7}
        r=requests.post(url,headers=headers,json=data,timeout=25)
        if r.status_code==200: return r.json()["choices"][0]["message"]["content"]
        else: print(f"[Groq {r.status_code}]"); return None
    except Exception as e: print(f"[Error {e}]"); return None

while True:
    try: you=input("\nYou: ")
    except: break
    if you.lower() in ["exit","quit","bye"]: 
        print("Nova: Goodbye! See you in Gweru time.")
        break
    learn(you)
    facts["chat_count"]+=1
    save_json(FACT_FILE,facts)
    memory.append({"time":str(datetime.datetime.now()),"you":you})
    save_json(MEM_FILE,memory[-50:])
    smart=ask_groq(you)
    if smart: print(f"\nNova: {smart}")
    else: print(f"\nNova: [Offline] Saved. Real time is {get_time()}")
