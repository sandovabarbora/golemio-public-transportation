import pandas as pd

def extract_stop_info(stops):
    stops_data = []
    for stop in stops['features']:
        stop_info = {
            'coordinates': stop['geometry']['coordinates'],
            'stop_name': stop['properties']['stop_name'],
            'stop_id': stop['properties']['stop_id']
        }
        stops_data.append(stop_info)
    return stops_data

def normalize_stops(data):
    data = data.copy()
    data['stop_id_base'] = data['stop_id'].str.extract(r'^(.*?)(?=[SZ])')[0]
    data[['longitude', 'latitude']] = pd.DataFrame(data['coordinates'].tolist(), index=data.index)
    
    normalized_data = data.groupby('stop_name').agg({
        'longitude': 'mean',
        'latitude': 'mean',
        'stop_id_base': 'first',
        'stop_id': lambda x: list(x) 
    }).reset_index()
    
    normalized_data.rename(columns={
        'longitude': 'avg_longitude',
        'latitude': 'avg_latitude',
        'stop_id_base': 'base_stop_id',
        'stop_id': 'all_stop_ids'
    }, inplace=True)
    
    return normalized_data