import json
import os


"""
This helper renders chat conversations passed as a json dump of a dictionary:
    --conversation contact id/name
        --num message (start from 0 each time is fine)
            --data-name = correspondant (phone or ID)
            --data-time = time of message (formatted as str)
            --from_me = (boolean - 0 = received / 1 = sent)
            --message = message content

example:
    {
        "Vincent":{
            "0":{
                "data-name": "Vincent",
                "data-time": "2020-11-10 08:00:00",
                "from_me" : 0,
                "Message": "What is your favorite tool?"
            },
            "1":{
                "data-name": "Vincent",
                "data-time": "2020-11-10 08:01:00",
                "from_me" : 1,
                "Message": "xLEAPP !"
            },
        },
        "Mike,Vincent":{
            "0":{
                "data-name": "Mike",
                "data-time": "2020-11-10 08:08:00",
                "from_me" : 0,
                "Message": "Who like apples ?"
            },
            "1":{
                "data-name": "Vincent",
                "data-time": "2020-11-10 08:09:00",
                "from_me" : 1,
                "Message": "I do!"
            }
    }

"""

mimeTypeIcon = {
    "image": "📷",
    "audio": "🎧",
    "video": "🎥",
    "animated": "🎡",
    "application": "📎",
    "text": "Ŧ",
}


"""
helper to render body with attachments
"""


def integrateAtt(rec):
    if rec["file-path"]:
        att_type = (
            rec["content-type"].split("/")[0] if rec["content-type"] else "application"
        )
        filename = os.path.basename(rec["file-path"])
        body = rec["message"] if rec["message"] else ""
        if att_type == "image":
            source = '<img src="{}" width="256" height="256"/>'.format(rec["file-path"])

        elif att_type == "audio":
            source = """
            <audio controls>
              <source src="{0}" type="{1}">
              <p><a href="{0}"></a> </p>
            </audio>
            """.format(
                rec["file-path"], rec["content-type"]
            )
        elif att_type == "video":
            source = """
            <video controls width="256">
              <source src="{0}" type="{1}">
              <p><a href="{0}"></a> </p>
            </video>
            """.format(
                rec["file-path"], rec["content-type"]
            )
        else:
            source = '<a href="{}">{}</a>'.format(rec["file-path"], filename)

        return "\n".join([body, mimeTypeIcon[att_type] + " " + source])
    else:
        return rec["message"]


"""
transform a chat df to be rendered to js
input : df with following columns:
    - data-name str : contact name / number
    - data-time dt : time of message (needs to be datetime format)
    - message str : text message
    - content-type str : mime type of atachement or None (ex : 'image/jpeg')
    - file-path str : path of attachment to render
    - from_me bool : 0 if received, 1 if sent
output :
    str including script and data to include in report html

"""


def render_chat(df):
    df["body_to_render"] = df.apply(lambda rec: integrateAtt(rec), axis=1)
    latest_mess = df.groupby("data-name", as_index=False)["data-time"].max()
    df = df.merge(
        latest_mess, on=["data-name"], how="right", suffixes=["", "_latest"]
    ).sort_values(by=["data-time_latest", "data-name"], ascending=[False, True])
    df["data-time"] = df["data-time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    chats = {}
    for c in df["data-name"].unique():
        chats[c] = (
            df[df["data-name"] == c][
                ["data-name", "from_me", "body_to_render", "data-time"]
            ]
            .reset_index(drop=True)
            .to_dict(orient="index")
        )

    json_chat = json.dumps(chats)
    return render_js_chat(json_chat)
