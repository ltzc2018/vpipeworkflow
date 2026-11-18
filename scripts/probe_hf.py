import sys, json, urllib.request
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
def probe_hf(repo):
    url = f"https://hf-mirror.com/api/models/{repo}/tree/main"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            print(f"FOUND HF: {repo}")
            for f in data:
                if f.get('type') == 'file':
                    print(f"  {f['path']} ({f.get('size', 0)/1e9:.3f} GB)")
            return True
    except Exception as e:
        if 'rate limit' in str(e).lower(): print("HF_RATE_LIMIT")
        pass
    return False

repos = ["ruchangyao/FlashVSR_plus", "Dirdx/FlashVSR_plus"]
for r in repos:
    if probe_hf(r): break
else:
    print("NOT_FOUND_ON_HF")
