import sys, json, urllib.request
def probe(repo):
    url = f"https://modelscope.cn/api/v1/models/{repo}/repo/files?Revision=master"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            files = data.get('Data', {}).get('Files', [])
            blobs = [f for f in files if f.get('Type') == 'blob']
            if blobs:
                print(f"FOUND: {repo} ({len(blobs)} blobs)")
                for b in blobs:
                    print(f"  {b['Path']} ({int(b['Size'])/1e9:.3f} GB)")
                return True
    except: pass
    return False

repos = ["ruchangyao/FlashVSR_plus", "ruchangyao/FlashVSR_Plus", "JunhaoZhuang/FlashVSR_plus", "kuohao/FlashVSR_plus"]
for r in repos:
    if probe(r): break
else:
    print("NOT_FOUND")
