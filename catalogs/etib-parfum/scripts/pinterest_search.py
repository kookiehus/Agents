"""Search Pinterest pins and download images (note photos for the staff site cards).
Usage:
  python3 pinterest_search.py search "<query>" [n]            -> prints JSON list: id, url, w, h, title
  python3 pinterest_search.py get <image url> <out file>      -> downloads one image (i.pinimg.com only)
  python3 pinterest_search.py batch <queries.json> <out dir> [k] -> for each {key: query}: search, save the
        candidates to <out dir>/<key>.json and the first k usable images (portrait-ish, >=600 px) as <key>_<i>.jpg
Only www.pinterest.com (search) and i.pinimg.com (images) are contacted."""
import sys, json, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json', 'X-Pinterest-PWS-Handler': 'www/search/[scope].js'}


def search(q, n=25):
    data = json.dumps({'options': {'query': q, 'scope': 'pins', 'page_size': n}, 'context': {}})
    url = 'https://www.pinterest.com/resource/BaseSearchResource/get/?' + urllib.parse.urlencode(
        {'source_url': '/search/pins/?q=' + urllib.parse.quote(q), 'data': data})
    j = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
    out = []
    for p in j['resource_response']['data'].get('results', []):
        im = (p.get('images') or {}).get('orig') or {}
        if im.get('url'):
            out.append({'id': p.get('id'), 'url': im['url'], 'w': im.get('width'), 'h': im.get('height'),
                        'title': (p.get('title') or p.get('grid_title') or p.get('description') or '')[:80]})
    return out


def get(url, out):
    if not url.startswith('https://i.pinimg.com/'):
        sys.exit('only i.pinimg.com images')
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as r:
        open(out, 'wb').write(r.read())


def batch(qfile, outdir, k=8):
    import os, time
    os.makedirs(outdir, exist_ok=True)
    for key, q in json.load(open(qfile, encoding='utf-8')).items():
        if os.path.exists(f'{outdir}/{key}.json'):
            continue
        try:
            res = search(q, 40)
        except Exception as e:
            print(key, 'ERR', e); time.sleep(5); continue
        ok = [r for r in res if (r['w'] or 0) >= 600 and 0.9 <= (r['h'] or 0) / max(r['w'] or 1, 1) <= 2.2]
        json.dump(ok, open(f'{outdir}/{key}.json', 'w'), ensure_ascii=False)
        for i, r in enumerate(ok[:k]):
            try:
                get(r['url'], f'{outdir}/{key}_{i}.jpg')
            except Exception as e:
                print(key, i, 'ERR', e)
        print(key, len(res), len(ok)); time.sleep(1.5)


if __name__ == '__main__':
    if sys.argv[1] == 'search':
        print(json.dumps(search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 25), ensure_ascii=False))
    elif sys.argv[1] == 'get':
        get(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'batch':
        batch(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 8)
