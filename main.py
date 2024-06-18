import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import requests
from countries import country_names

font_prop = fm.FontProperties(fname=fm.findfont(fm.FontProperties(family='Arial')))

api_key = ''

def fetch_countries(version):
    url = f'https://proxy6.net/api/{api_key}/getcountry?version={version}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'yes':
            return data['list']
        else:
            raise Exception('Не удалось получить список стран')
    else:
        raise Exception(f'Не удалось получить данные: {response.status_code}')

def fetch_proxy_count(country, version):
    url = f'https://proxy6.net/api/{api_key}/getcount?country={country}&version={version}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'yes':
            return data['count']
        else:
            raise Exception('Не удалось получить количество прокси')
    else:
        raise Exception(f'Не удалось получить данные: {response.status_code}')

def load_daily_data(filename='daily_data.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {'IPv4': []}

def save_daily_data(data, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def update_daily_data(daily_data, current_data):
    for proxy_type in current_data:
        for proxy in current_data[proxy_type]:
            country = proxy['country']
            count = proxy['count']
            daily_data[proxy_type].append({
                'country': country,
                'count': count,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    return daily_data

def calculate_daily_stats(daily_data):
    stats = {
        'IPv4': defaultdict(lambda: {
            'total_available': 0,
            'count': 0,
            'timestamps': []
        })
    }

    for proxy_type in daily_data:
        for entry in daily_data[proxy_type]:
            country = entry['country']
            count = entry['count']
            timestamp = entry['timestamp']
            stats[proxy_type][country]['total_available'] += count
            stats[proxy_type][country]['count'] += 1
            stats[proxy_type][country]['timestamps'].append((timestamp, count))

    for proxy_type in stats:
        for country in stats[proxy_type]:
            stats[proxy_type][country]['average_available'] = (
                stats[proxy_type][country]['total_available'] / stats[proxy_type][country]['count']
            )

    return stats

def display_daily_stats(stats):
    for proxy_type, countries in stats.items():
        print(f'{proxy_type} Proxies:')
        for country, stat in countries.items():
            country_name = country_names.get(country, country)
            print(f"Country: {country_name}, Average Available: {stat['average_available']:.2f}, Count: {stat['count']}")

def plot_graphs(daily_stats, save_dir):
    for proxy_type, countries in daily_stats.items():
        for country, stat in countries.items():
            if stat['timestamps']:
                timestamps, counts = zip(*stat['timestamps'])
                country_name = country_names.get(country, country)
                plt.figure()
                plt.plot(timestamps, counts, marker='o', linestyle='-')
                plt.xlabel('Time', fontproperties=font_prop)
                plt.ylabel('Available Proxies', fontproperties=font_prop)
                plt.title(f'{proxy_type} Proxies: {country_name}', fontproperties=font_prop)
                plt.xticks(rotation=45, fontproperties=font_prop)
                plt.yticks(fontproperties=font_prop)
                plt.tight_layout()
                plt.savefig(os.path.join(save_dir, f'graph_{country}_{proxy_type}.png'))
                plt.close()

def collect_proxy_data(duration_hours, interval):
    try:
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)

        save_dir = start_time.strftime('%Y-%m-%d_%H-%M-%S')
        os.makedirs(save_dir, exist_ok=True)

        while datetime.now() < end_time:
            current_data = {'IPv4': []}

            version = 4
            countries = fetch_countries(version)
            for country in countries:
                count = fetch_proxy_count(country, version)
                current_data['IPv4'].append({'country': country, 'count': count})

            daily_data = load_daily_data(os.path.join(save_dir, 'daily_data.json'))
            updated_daily_data = update_daily_data(daily_data, current_data)
            save_daily_data(updated_daily_data, os.path.join(save_dir, 'daily_data.json'))

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data_to_save = f'Timestamp: {timestamp}\n'
            for proxy_type, proxies in current_data.items():
                data_to_save += f'{proxy_type} Proxies:\n'
                for proxy in proxies:
                    country_name = country_names.get(proxy['country'], proxy['country'])
                    data_to_save += f"Country: {country_name}, Count: {proxy['count']}\n"
            save_data(data_to_save, os.path.join(save_dir, 'proxy_data.txt'))

            daily_stats = calculate_daily_stats(updated_daily_data)
            plot_graphs(daily_stats, save_dir)

            time.sleep(interval)

        daily_data = load_daily_data(os.path.join(save_dir, 'daily_data.json'))
        daily_stats = calculate_daily_stats(daily_data)
        display_daily_stats(daily_stats)

    except Exception as e:
        print(f"Произошла ошибка: {e}")

def save_data(data, filename):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(data + '\n')

if __name__ == '__main__':
    duration_hours = int(input("Введите продолжительность сбора данных в часах: "))
    interval = int(input("Введите интервал опроса (в секундах): "))

    collect_proxy_data(duration_hours, interval)
