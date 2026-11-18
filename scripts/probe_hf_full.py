import sys, json, urllib.request
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

def get_tree(repo, path=""):
    url = f"https://hf-mirror.com/api/models/{repo}/tree/main/{path}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except: return None

repo = "ruchangyao/FlashVSR_plus"
print(f"Investigating {repo}...")
root = get_tree(repo)
if root:
    for item in root:
        if item['type'] == 'directory':
            print(f"DIR: {item['path']}")
            sub = get_tree(repo, item['path'])
            if sub:
                for s in sub:
                    print(f"  {s['path']} ({s.get('size', 0)/1e9:.3f} GB)")
        else:
            print(f"FILE: {item['path']} ({item.get('size', 0)/1e9:.3f} GB)")
