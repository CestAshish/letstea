import json

topics_path = "profiling_app/static/topics.json"
with open(topics_path, 'r') as file:
    topics_data = json.load(file)

topic = topics_data["technical english"]["a1".upper()][str(1)]["Topic"]
print(topic)