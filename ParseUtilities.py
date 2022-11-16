import json

def process_json(json_file, out_name):
    with open(json_file, 'r') as f:
        data = json.load(f)
    f.close()
    new_data = recursion_lower(data)
    with open(out_name, 'w') as f:
        json.dump(new_data, f, indent=2)
    f.close()

def parse_string(string):
    to_remove = " -'â€™’."
    for char in to_remove:
        string = string.replace(char, "")
    return string.lower()

def recursion_lower(data):
    if type(data) is str:
        return parse_string(data)
    elif type(data) is list:
        return [recursion_lower(i) for i in data]
    elif type(data) is dict:
        return {recursion_lower(k):recursion_lower(v) for k,v in data.items()}
    else:
        return data

if __name__ == "__main__":
    
    GEN4 = "gen4randomteams_ORIGINAL.json"

    process_json(json_file=GEN4, out_name="gen4randomteams.json")
    