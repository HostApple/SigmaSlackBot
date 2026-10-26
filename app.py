import os
import random
import sqlite3
from pathlib import Path
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# tokens n stuff
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
APILEAGUE_API_KEY = os.environ.get("APILEAGUE_API_KEY", "")

app = App(token=SLACK_BOT_TOKEN)
DB_PATH = Path(os.environ.get("SIGMABOT_DB", "sigmabot.db"))


# quotes are zesty
QUOTES = [
    "The grind never stops. Unfortunately, neither does the homework lol.",
    "BE the REASON your group project finally has a plan.",
    "A locked-in legend still drinks water.",
    "YoUr FuTuRe Self Is WaTcHiNg. GiVe ThEm A dEcEnT pLoT tWiSt.",
    "Discipline is doing the task before the meme break becomes a career.",
    "Move in silence. Submit the assignment loudly.",
    "One small task today is better than a 47-tab productivity setup.",
    "Stay mysterious. Finish your homework before midnight.",
    "Sigma Simga boy yay.",
    "THE LARP MUST NEVER STOP",
    "LARP LARP LARP SAHURRR .",
]


# omg i love these
ROASTS = [
    "You opened Slack to work and somehow became a full-time spectator. 🗿",
    "Your to-do list has lore at this point. 🗿 🗿 🗿",
    "The task is not going to complete itself 🗿. It has boundaries. 🗿",
    "You have 37 tabs open and somehow none of them are the assignment.",
    "Lock in gently. Even a side quest deserves a plan.",
    "You have the incredible talent of getting lost even with a map app that literally talks to you.",
    "You operate at about 12PERCENT social battery 🗿 all day, and I respect your commitment to doing the bare minimum.", 
    "Your cooking skills start and end with water boiling—and even then, I get nervous.",
    "If being late were an Olympic sport, you’d still manage to show up ten minutes after the ceremony ended.",
    "You own five versions of the exact same shirt 🗿  and somehow act like shopping is a crisis.",

]


def connect_db():
    db = sqlite3.connect(DB_PATH)

    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            task TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    return db


# task thingy
def add_task(team_id, user_id, task):
    with connect_db() as db:
        thing = db.execute(
            "INSERT INTO tasks (team_id, user_id, task) VALUES (?, ?, ?)",
            (team_id, user_id, task)
        )
        return thing.lastrowid


def get_tasks(team_id, user_id):
    with connect_db() as db:
        stuff = db.execute(
            "SELECT id, task, done FROM tasks "
            "WHERE team_id = ? AND user_id = ? ORDER BY done, id DESC",
            (team_id, user_id)
        ).fetchall()

    return stuff


def finish_task(team_id, user_id, task_id):
    with connect_db() as db:
        thing = db.execute(
            "UPDATE tasks SET done = 1 "
            "WHERE id = ? AND team_id = ? AND user_id = ? AND done = 0",
            (task_id, team_id, user_id)
        )
        return thing.rowcount > 0


# meme fetching thing
def get_random_meme(words=""):
    if not APILEAGUE_API_KEY:
        return None, "no api key lol"

    params = {"media-type": "image"}

    if words:
        params["keywords"] = words

    r = requests.get(
        "https://api.apileague.com/retrieve-random-meme",
        headers={"x-api-key": APILEAGUE_API_KEY},
        params=params,
        timeout=15
    )

    r.raise_for_status()
    meme = r.json()

    if not meme or not isinstance(meme, dict) or not meme.get("url"):
        return None, "no meme came back bruh"

    return meme, None


# sigma wisdom generator or whatever
@app.command("/sigma-quote")
def sigma_quote(ack, respond):
    ack()
    respond(f"🗿 *Sigma wisdom of the moment:*\n>{random.choice(QUOTES)}")


# friendly bullying
@app.command("/sigma-roast")
def sigma_roast(ack, respond):
    ack()
    respond("🔥 " + random.choice(ROASTS))


# all the commands n stuff
@app.command("/sigma-help")
def sigma_help(ack, respond):
    ack()
    respond(
        "*🗿 SIGMABOT command menu*\n"
        "• `/sigma-quote` — random sigma quote\n"
        "• `/sigma-meme [keywords]` — get a meme\n"
        "• `/sigma-task add your task` — add a task\n"
        "• `/sigma-task list` — see your tasks\n"
        "• `/sigma-task done ID` — finish a task\n"
        "• `/sigma-roast` — friendly productivity roast\n"
        "• `/sigma-help` — show this menu"
    )


# i keep forgetting stuff so here we are
@app.command("/sigma-task")
def sigma_task(ack, body, respond):
    ack()

    txt = (body.get("text") or "").strip()
    team_id = body.get("team_id", "unknown-team")
    user_id = body.get("user_id", "unknown-user")

    action, _, rest = txt.partition(" ")
    action = action.lower()

    if action == "add" and rest.strip():
        task_id = add_task(team_id, user_id, rest.strip())
        respond(f"📝 Added task *#{task_id}*: {rest.strip()}")

    elif action == "list":
        tasks = get_tasks(team_id, user_id)

        if len(tasks) == 0:
            respond("no tasks rn lol. add one with `/sigma-task add WORKKKKKK`")
            return

        lines = []
        for task_id, task, done in tasks:
            mark = "✅" if done else "⬜"
            lines.append(f"{mark} *#{task_id}* — {task}")

        respond("*Your tasks:*\n" + "\n".join(lines))

    elif action == "done" and rest.strip().isdigit():
        task_id = int(rest.strip())

        if finish_task(team_id, user_id, task_id):
            respond(f"✅ Task *#{task_id}* completed. character development fr")
        else:
            respond("couldn't find that task ig you finished it. or youre lazy and deleted it TwT")

    else:
        respond(
            "use one of these lol:\n"
            "• `/sigma-task add finish my project`\n"
            "• `/sigma-task list`\n"
            "• `/sigma-task done 1`"
        )


#meme time
@app.command("/sigma-meme")
def sigma_meme(ack, body, respond):
    ack() 
    words = (body.get("text") or "").strip()
    try :
        meme,err = get_random_meme(words)

        if err:
            respond(err)
            return
        title = meme.get("description") or "random meme"
        link = meme["url"]

        respond({
            "response_type": "in_channel",
            "text": f"🗿*{title}*\n{link}"

        })

    except requests.HTTPError:
        respond("api error . i guess i ran out")

    except requests.RequestsException:
        respond("meme api isnt working rn mb gng")

    except (ValueError , KeyError , TypeError):
        respond("couldn't read the meme 🗿 response 💀")




#when someone mentiones the bot

@app.event("app_mention")
def mention_bot(event, say):
    say(f"🗿 <@{event['user']}> I am SIGMABOT. Try `/sigma-help`.")



# booting sigma bot yay
if __name__ == '__main__':
    print("sigma bot is waking up...")
    bot_runner = SocketModeHandler(app, SLACK_APP_TOKEN)
    bot_runner.start()
