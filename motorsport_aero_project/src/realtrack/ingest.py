"""Read an attributed OSM snapshot; download when absent or explicitly refreshed."""
from pathlib import Path
import hashlib,json,urllib.request
from datetime import datetime,timezone
import numpy as np

def load_route(folder: Path, circuit: dict, download=False):
    folder.mkdir(parents=True,exist_ok=True)
    relation_id=circuit['osm_relation_id']
    path=folder/f'osm_relation_{relation_id}.json'
    url=f'https://api.openstreetmap.org/api/0.6/relation/{relation_id}/full.json'
    if download or not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'AeroLab educational circuit analysis/1.0'})
        content=urllib.request.urlopen(request,timeout=45).read()
        json.loads(content)  # Do not overwrite a working snapshot with an error page.
        path.write_bytes(content)
    raw=path.read_bytes(); data=json.loads(raw)
    nodes={e['id']:e for e in data['elements'] if e['type']=='node'}
    ways={e['id']:e for e in data['elements'] if e['type']=='way'}
    relation=next(e for e in data['elements'] if e['type']=='relation' and e['id']==relation_id)
    members=[m['ref'] for m in relation['members'] if m['type']=='way' and m['role']!='pit_lane' and ways[m['ref']].get('tags',{}).get('raceway')!='pit_lane']
    ids=list(dict.fromkeys(members))  # Current Silverstone relation repeats many members.
    first=circuit.get('start_way_id')
    if first:
        if first not in ids: raise ValueError('Configured start way is not in the circuit relation')
        order=[first]; route=list(ways[first]['nodes']);remaining=set(ids)-{first}
        while remaining:
            matches=[w for w in remaining if ways[w]['nodes'][0]==route[-1]]
            if len(matches)!=1: raise ValueError(f'Route topology is ambiguous or disconnected after way {order[-1]}')
            w=matches[0];route.extend(ways[w]['nodes'][1:]);order.append(w);remaining.remove(w)
    else:
        valid_orders = []
        for candidate_first in ids:
            curr_order = [candidate_first]; curr_route = list(ways[candidate_first]['nodes'])
            curr_remaining = set(ids) - {candidate_first}; valid = True
            while curr_remaining:
                matches = [w for w in curr_remaining if ways[w]['nodes'][0] == curr_route[-1]]
                if len(matches) != 1:
                    matches_rev = [w for w in curr_remaining if ways[w]['nodes'][-1] == curr_route[-1]]
                    if not matches and len(matches_rev) == 1:
                        w = matches_rev[0]
                        curr_route.extend(ways[w]['nodes'][-2::-1])
                        curr_order.append(w)
                        curr_remaining.remove(w)
                        continue
                    valid = False; break
                w = matches[0]; curr_route.extend(ways[w]['nodes'][1:])
                curr_order.append(w); curr_remaining.remove(w)
            if valid and curr_route[0] == curr_route[-1]: valid_orders.append((curr_order, curr_route))
        if not valid_orders: raise ValueError('Could not find valid closed route')
        if len(valid_orders) > 1:
            hint = circuit.get('start_node_hint')
            if hint:
                valid_orders = [o for o in valid_orders if o[1][0] == hint] or valid_orders
            center_lat = np.mean([nodes[n]['lat'] for n in set(valid_orders[0][1])])
            center_lon = np.mean([nodes[n]['lon'] for n in set(valid_orders[0][1])])
            valid_orders.sort(key=lambda o: (nodes[o[1][0]]['lat'] - center_lat)**2 + (nodes[o[1][0]]['lon'] - center_lon)**2)
        order, route = valid_orders[0]
    if route[0]!=route[-1]: raise ValueError('OSM route is not closed')
    coords=np.array([[nodes[i]['lon'],nodes[i]['lat']] for i in route],dtype=float)
    if not np.isfinite(coords).all(): raise ValueError('Nonfinite geographic coordinates')
    provenance={'data_source':'OpenStreetMap contributors','source_url':f'https://www.openstreetmap.org/relation/{relation_id}',
        'download_url':url,'source_license':'ODbL-1.0','license_url':'https://www.openstreetmap.org/copyright',
        'snapshot_sha256':hashlib.sha256(raw).hexdigest(),'relation_version':relation['version'],
        'relation_timestamp':relation['timestamp'],'processed_at_utc':datetime.now(timezone.utc).isoformat(),
        'unique_route_ways':len(ids),'duplicate_members_removed':len(members)-len(ids),'ordered_way_ids':order,
        'source_warnings':[{ 'way_id':i,'note':ways[i]['tags']['note']} for i in order if 'note' in ways[i].get('tags',{})],
        'start_definition':'First node of configured Hamilton Straight way; analytical lap origin, not an official timing-line claim.',
        'is_synthetic':False,'is_derived':False}
    (folder/'provenance.json').write_text(json.dumps(provenance,indent=2))
    return coords,provenance
