"""Multi-file fixtures. Reference repairs are controller-only."""
TASKS = [
    {
        "id": "invoice",
        "prompt": "Repair invoice.summary(lines, discount): each line has sku, quantity and unit_price as decimal strings. Merge repeated SKUs by summing their discounted amounts. Apply a fractional discount before rounding each merged SKU total to two decimal places using ROUND_HALF_UP. Return a dict of SKU to formatted amount strings. Reject negative quantity/price and discounts outside [0,1]. Preserve input data.",
        "files": {
            "money.py": "from decimal import Decimal, ROUND_HALF_UP\ndef amount(value):\n    return Decimal(str(value))\ndef display(value):\n    return str(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))\n",
            "solution.py": "from money import amount, display\ndef summary(lines, discount):\n    result = {}\n    for line in lines:\n        result[line['sku']] = display(amount(line['quantity']) * amount(line['unit_price']))\n    return result\n",
            "README.txt": "invoice API is exported by solution.py. money.py contains shared decimal helpers. All source modules may be repaired.\n",
        },
        "reference": "from money import amount, display\ndef summary(lines, discount):\n    d = amount(discount)\n    if not 0 <= d <= 1: raise ValueError('discount')\n    totals = {}\n    for line in lines:\n        q, p = amount(line['quantity']), amount(line['unit_price'])\n        if q < 0 or p < 0: raise ValueError('negative')\n        sku = line['sku']\n        totals[sku] = totals.get(sku, amount(0)) + q*p*(1-d)\n    return {k: display(v) for k,v in totals.items()}\n",
        "tests": "from solution import summary\nimport copy\nlines=[{'sku':'a','quantity':'1','unit_price':'0.025'},{'sku':'a','quantity':'1','unit_price':'0.025'},{'sku':'b','quantity':'2','unit_price':'10'}]\nbefore=copy.deepcopy(lines)\nassert summary(lines,'0.1') == {'a':'0.05','b':'18.00'}\nassert lines == before\nassert summary([],0) == {}\nassert summary(lines,1) == {'a':'0.00','b':'0.00'}\nfor lines,d in [([], '-0.1'),([], '1.1'),([{'sku':'x','quantity':'-1','unit_price':'2'}],0),([{'sku':'x','quantity':'1','unit_price':'-2'}],0)]:\n    try: summary(lines,d)\n    except ValueError: pass\n    else: raise AssertionError('expected ValueError')\n",
    },
    {
        "id": "events",
        "prompt": "Repair events.latest(events): each event has id, timestamp (ISO 8601 with timezone, including Z) and payload. Return the latest event per id ordered by id. Compare absolute instants across offsets; on equal instants keep the last input event. Reject timestamps without timezone. Do not mutate input.",
        "files": {
            "timestamps.py": "from datetime import datetime\ndef parse(value):\n    return datetime.fromisoformat(value.replace('Z', '+00:00'))\n",
            "solution.py": "from timestamps import parse\ndef latest(events):\n    selected = {}\n    for event in events:\n        key = event['id']\n        if key not in selected or event['timestamp'] > selected[key]['timestamp']:\n            selected[key] = event\n    return list(selected.values())\n",
            "README.txt": "latest is exported by solution.py. timestamps.py parses timestamps. IDs are strings.\n",
        },
        "reference": "from timestamps import parse\ndef latest(events):\n    selected = {}\n    for event in events:\n        t = parse(event['timestamp'])\n        if t.tzinfo is None or t.utcoffset() is None: raise ValueError('timezone required')\n        key = event['id']\n        if key not in selected or t >= selected[key][0]: selected[key] = (t,event)\n    return [selected[key][1] for key in sorted(selected)]\n",
        "tests": "from solution import latest\nimport copy\na={'id':'b','timestamp':'2025-01-01T10:00:00+02:00','payload':1}\nb={'id':'b','timestamp':'2025-01-01T08:30:00Z','payload':2}\nc={'id':'a','timestamp':'2025-01-01T08:30:00+00:00','payload':3}\nd={'id':'b','timestamp':'2025-01-01T03:30:00-05:00','payload':4}\ndata=[a,b,c,d]\nbefore=copy.deepcopy(data)\nassert latest(data)==[c,d]\nassert data==before\nassert latest([])==[]\ntry: latest([{'id':'a','timestamp':'2025-01-01T00:00:00','payload':0}])\nexcept ValueError: pass\nelse: raise AssertionError('timezone required')\n",
    },
    {
        "id": "pagination",
        "prompt": "Repair catalog.page(records, cursor=None, limit=2). Records have unique integer id and integer score. Order by descending score then ascending id. Cursor is a (score,id) pair identifying the last returned ordering position; return only records strictly after it, even if that cursor record is absent. Return (items, next_cursor); next_cursor is the last returned pair only if additional records remain, otherwise None. Reject nonpositive limits and preserve inputs.",
        "files": {
            "ordering.py": "def key(record):\n    return (-record['score'], record['id'])\n",
            "solution.py": "from ordering import key\ndef page(records, cursor=None, limit=2):\n    ordered = sorted(records, key=key)\n    if cursor is not None:\n        ordered = [r for r in ordered if r['id'] > cursor[1]]\n    items = ordered[:limit]\n    return items, ((items[-1]['score'],items[-1]['id']) if items else None)\n",
            "README.txt": "page is exported by solution.py; ordering.py holds the sorting helper.\n",
        },
        "reference": "from ordering import key\ndef page(records, cursor=None, limit=2):\n    if limit <= 0: raise ValueError('limit')\n    ordered=sorted(records,key=key)\n    if cursor is not None: ordered=[r for r in ordered if key(r) > (-cursor[0],cursor[1])]\n    items=ordered[:limit]\n    nxt=(items[-1]['score'],items[-1]['id']) if len(ordered)>limit else None\n    return items,nxt\n",
        "tests": "from solution import page\nimport copy\ndata=[{'id':9,'score':20},{'id':1,'score':10},{'id':3,'score':20},{'id':2,'score':5}]\nbefore=copy.deepcopy(data)\na,c=page(data,limit=2)\nassert [r['id'] for r in a]==[3,9] and c==(20,9)\nb,d=page(data,c,2)\nassert [r['id'] for r in b]==[1,2] and d is None\na,c=page(data,(15,100),1)\nassert [r['id'] for r in a]==[1] and c==(10,1)\nassert page([],limit=2)==([],None)\nassert data==before\nfor n in [0,-1]:\n    try: page(data,limit=n)\n    except ValueError: pass\n    else: raise AssertionError('limit')\n",
    },
]
