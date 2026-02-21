#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神戸釣り情報 自動データ収集スクリプト v2.0
5つのソースから実際の釣果データを収集
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import math

# リクエストヘッダー
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
}

# 魚種の絵文字マッピング
FISH_EMOJI = {
    'アジ': '🐠', 'サバ': '🐟', 'メバル': '🐟', 'タチウオ': '🗡️',
    'タコ': '🐙', 'イカ': '🦑', 'アオリイカ': '🦑', 'チヌ': '🐟',
    'キス': '🐠', 'カレイ': '🐟', 'ハゼ': '🐠', 'カサゴ': '🐟',
    'ガシラ': '🐟', 'シーバス': '🐟', 'ハマチ': '🐟', 'サワラ': '🐟',
    'マダイ': '🎣', 'イワシ': '🐠', 'ハネ': '🐟', 'グレ': '🐟',
    'サヨリ': '🐠', 'ウミタナゴ': '🐟', 'コブダイ': '🐟', 'フグ': '🐡',
    'ウマヅラハギ': '🐟', 'カワハギ': '🐟', 'ツバス': '🐟', 'ブリ': '🐟',
    'スズキ': '🐟', 'アイナメ': '🐟', 'ヒラメ': '🐟', 'ベラ': '🐠',
    'ウナギ': '🐍', 'アナゴ': '🐍', 'サンバソウ': '🐟',
}

def get_emoji(fish_name):
    """魚名から絵文字を取得"""
    for key, emoji in FISH_EMOJI.items():
        if key in fish_name:
            return emoji
    return '🐟'


# =============================================================
# 1. 須磨海づり公園
# =============================================================
def collect_suma():
    """須磨海づり公園から釣果収集"""
    print("📡 [1/5] 須磨海づり公園から収集中...")
    catches = []
    
    try:
        # 釣果一覧ページ取得
        url = "https://sumasakana-park.com/fishing/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # 各日の釣果リンクを取得（最新5件）
        articles = soup.select('a[href*="/fishing/"]')
        detail_urls = []
        for a in articles:
            href = a.get('href', '')
            if href and '/fishing/' in href and href != '/fishing/' and 'page' not in href:
                full_url = href if href.startswith('http') else f"https://sumasakana-park.com{href}"
                if full_url not in detail_urls:
                    detail_urls.append(full_url)
        
        detail_urls = detail_urls[:7]  # 最新7日分
        
        for detail_url in detail_urls:
            try:
                time.sleep(1)  # 礼儀正しく
                resp2 = requests.get(detail_url, headers=HEADERS, timeout=15)
                resp2.encoding = 'utf-8'
                soup2 = BeautifulSoup(resp2.text, 'lxml')
                
                # 日付取得
                title = soup2.find('h2', string=re.compile(r'20\d{2}\.\d{2}\.\d{2}'))
                date_str = ""
                if title:
                    m = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', title.text)
                    if m:
                        date_str = f"{int(m.group(2))}/{int(m.group(3))}"
                
                # 天候・水温取得
                water_temp = ""
                tide = ""
                weather = ""
                for li in soup2.select('li'):
                    text = li.get_text(strip=True)
                    if '水温' in text:
                        m = re.search(r'([\d.]+)℃', text)
                        if m:
                            water_temp = m.group(1) + "℃"
                    if '潮' in text and '満潮' not in text and '干潮' not in text:
                        for s in ['大潮', '中潮', '小潮', '長潮', '若潮']:
                            if s in text:
                                tide = s
                                break
                    if any(w in text for w in ['晴れ', '曇り', '雨', '晴']):
                        for w in ['晴れ', '曇り時々雨', '曇り時々晴れ', '曇り', '雨のち曇り', '雨', '晴']:
                            if w in text:
                                weather = w
                                break
                
                # 釣果テーブル取得
                tables = soup2.select('table')
                for table in tables:
                    rows = table.select('tr')
                    for row in rows:
                        cells = row.select('td')
                        if len(cells) >= 3:
                            fish = cells[0].get_text(strip=True)
                            size = cells[1].get_text(strip=True)
                            count = cells[2].get_text(strip=True)
                            if fish and any(c.isalpha() or ord(c) > 127 for c in fish):
                                catches.append({
                                    "fish": fish,
                                    "size": size,
                                    "count": count,
                                    "method": "",
                                    "user": "",
                                    "date": date_str,
                                    "emoji": get_emoji(fish),
                                    "water_temp": water_temp,
                                    "tide": tide,
                                    "weather": weather,
                                })
                
                # テーブルがない場合、本文からも抽出を試みる
                if not any(c['date'] == date_str for c in catches):
                    content = soup2.get_text()
                    # "釣果なし" パターン
                    if '釣果なし' in content or '目立った釣果なし' in content:
                        catches.append({
                            "fish": "釣果なし",
                            "size": "-",
                            "count": "-",
                            "method": "",
                            "user": "",
                            "date": date_str,
                            "emoji": "❌",
                            "water_temp": water_temp,
                            "tide": tide,
                            "weather": weather,
                        })
                
            except Exception as e:
                print(f"  ⚠️ 須磨詳細ページエラー: {detail_url} - {e}")
                continue
        
    except Exception as e:
        print(f"  ❌ 須磨海づり公園エラー: {e}")
    
    print(f"  ✅ 須磨: {len(catches)}件取得")
    return {
        "name": "須磨海づり公園",
        "area": "神戸",
        "distance": 2.3,
        "info": "ファミリー向け・足場良好・設備充実・駐車場あり",
        "source": "sumasakana-park.com",
        "catches": catches
    }


# =============================================================
# 2. 平磯海づり公園
# =============================================================
def collect_hiraiso():
    """平磯海づり公園から釣果収集"""
    print("📡 [2/5] 平磯海づり公園から収集中...")
    catches = []
    
    try:
        url = "https://kobeumiduri.jp/fishresult/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # 月間釣果テーブル取得
        table = soup.select_one('table')
        if table:
            rows = table.select('tr')
            for row in rows[1:]:  # ヘッダースキップ
                cells = row.select('td')
                if len(cells) >= 7:
                    fish = cells[0].get_text(strip=True)
                    rating = cells[1].get_text(strip=True)
                    size = cells[2].get_text(strip=True)
                    count = cells[3].get_text(strip=True)
                    method = cells[4].get_text(strip=True)
                    bait = cells[5].get_text(strip=True)
                    location = cells[6].get_text(strip=True)
                    
                    if fish and fish != '魚種':
                        catches.append({
                            "fish": fish,
                            "size": size,
                            "count": count,
                            "method": method,
                            "user": f"エサ:{bait}",
                            "date": "今月実績",
                            "emoji": get_emoji(fish),
                            "rating": rating,
                            "location": location,
                        })
        
        # 個別釣果ページのリンク取得（最新5件）
        result_links = []
        for a in soup.select('a[href*="fishresult"]'):
            href = a.get('href', '')
            if re.search(r'20\d{2}.*\d{1,2}.*\d{1,2}', href):
                full_url = href if href.startswith('http') else f"https://kobeumiduri.jp{href}"
                if full_url not in result_links:
                    result_links.append(full_url)
        
        for detail_url in result_links[:5]:
            try:
                time.sleep(1)
                resp2 = requests.get(detail_url, headers=HEADERS, timeout=15)
                resp2.encoding = 'utf-8'
                soup2 = BeautifulSoup(resp2.text, 'lxml')
                
                # 日付取得
                h2 = soup2.find('h2', string=re.compile(r'20\d{2}年'))
                date_str = ""
                if h2:
                    m = re.search(r'(\d{1,2})月(\d{1,2})日', h2.text)
                    if m:
                        date_str = f"{m.group(1)}/{m.group(2)}"
                
                # 天候・水温
                water_temp = ""
                tide = ""
                page_text = soup2.get_text()
                m = re.search(r'水温\s*([\d.]+)', page_text)
                if m:
                    water_temp = m.group(1) + "℃"
                for s in ['大潮', '中潮', '小潮', '長潮', '若潮']:
                    if s in page_text:
                        tide = s
                        break
                
                # 個別釣果の詳細
                fish_name = ""
                size_val = ""
                count_val = ""
                method_val = ""
                bait_val = ""
                
                for text_block in page_text.split('\n'):
                    text_block = text_block.strip()
                    if '魚種' in text_block:
                        m = re.search(r'魚種\s*(.+)', text_block)
                        if m: fish_name = m.group(1).strip()
                    elif 'サイズ' in text_block:
                        m = re.search(r'サイズ\s*(.+)', text_block)
                        if m: size_val = m.group(1).strip()
                    elif '尾数' in text_block:
                        m = re.search(r'尾数\s*(.+)', text_block)
                        if m: count_val = m.group(1).strip()
                    elif '仕掛' in text_block:
                        m = re.search(r'仕掛\s*(.+)', text_block)
                        if m: method_val = m.group(1).strip()
                    elif 'エサ' in text_block:
                        m = re.search(r'エサ\s*(.+)', text_block)
                        if m: bait_val = m.group(1).strip()
                
                if fish_name:
                    catches.append({
                        "fish": fish_name,
                        "size": size_val,
                        "count": count_val,
                        "method": method_val,
                        "user": f"エサ:{bait_val}" if bait_val else "",
                        "date": date_str,
                        "emoji": get_emoji(fish_name),
                        "water_temp": water_temp,
                        "tide": tide,
                    })
                    
            except Exception as e:
                print(f"  ⚠️ 平磯詳細ページエラー: {e}")
                continue
    
    except Exception as e:
        print(f"  ❌ 平磯海づり公園エラー: {e}")
    
    print(f"  ✅ 平磯: {len(catches)}件取得")
    return {
        "name": "平磯海づり公園",
        "area": "神戸",
        "distance": 8.5,
        "info": "垂水区・足場良好・投げ釣り人気・駐車場あり",
        "source": "kobeumiduri.jp",
        "catches": catches
    }


# =============================================================
# 3. カンパリ（神戸東部・神戸西部）
# =============================================================
def collect_kanpari():
    """カンパリから釣果収集"""
    print("📡 [3/5] カンパリから収集中...")
    catches = []
    
    areas = [
        ("神戸東部", "https://fishing.ne.jp/fishingpost/area/kobe-tobu", "神戸"),
        ("神戸西部", "https://fishing.ne.jp/fishingpost/area/kobe-seibu", "神戸"),
        ("明石", "https://fishing.ne.jp/fishingpost/area/akashi", "明石"),
    ]
    
    for area_name, url, area_tag in areas:
        try:
            time.sleep(1)
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'lxml')
            
            # 投稿記事を取得
            articles = soup.select('a[href*="fishingpost&p="]')
            
            for article in articles[:5]:
                title = article.select_one('h1, h2, h3')
                title_text = title.get_text(strip=True) if title else ""
                
                # 日付取得
                date_str = ""
                date_elem = article.find(string=re.compile(r'20\d{2}/\d{2}/\d{2}'))
                if date_elem:
                    m = re.search(r'(\d{4})/(\d{2})/(\d{2})', str(date_elem))
                    if m:
                        date_str = f"{int(m.group(2))}/{int(m.group(3))}"
                
                # ユーザー名
                user_elem = article.select_one('a[href*="profile"]')
                user_name = user_elem.get_text(strip=True) if user_elem else ""
                
                # 説明文
                desc = ""
                desc_elem = article.select_one('p') or article.find(string=re.compile(r'.{10,}'))
                if desc_elem:
                    desc = str(desc_elem).strip()[:100]
                
                # 魚種をタグから取得
                fish_tags = article.select('a[href*="fish="]')
                fish_name = ""
                for ft in fish_tags:
                    t = ft.get_text(strip=True).replace('釣り', '').replace('釣果', '')
                    if t:
                        fish_name = t
                        break
                
                # 仕掛けタグ
                method_tags = article.select('a[href*="howto="]')
                method = ""
                for mt in method_tags:
                    t = mt.get_text(strip=True).replace('釣果', '')
                    if t:
                        method = t
                        break
                
                if not fish_name and title_text:
                    fish_name = title_text
                
                if fish_name or title_text:
                    catches.append({
                        "fish": fish_name or title_text,
                        "size": "",
                        "count": "",
                        "method": method,
                        "user": user_name,
                        "date": date_str,
                        "emoji": get_emoji(fish_name or title_text),
                        "description": desc,
                        "area_detail": area_name,
                    })
            
        except Exception as e:
            print(f"  ⚠️ カンパリ({area_name})エラー: {e}")
            continue
    
    print(f"  ✅ カンパリ: {len(catches)}件取得")
    return {
        "name": "カンパリ投稿",
        "area": "神戸",
        "distance": None,
        "info": "ユーザー投稿の釣果情報",
        "source": "fishing.ne.jp",
        "catches": catches
    }


# =============================================================
# 4. フィッシングマックス（Google検索経由）
# =============================================================
def collect_fishingmax():
    """フィッシングマックスの釣果をGoogle検索経由で取得"""
    print("📡 [4/5] フィッシングマックス（Google経由）から収集中...")
    catches = []
    
    try:
        # まず直接アクセスを試行
        urls_to_try = [
            "https://fishingmax.co.jp/fishingpost?shop=shop-kobeharvor",
            "https://fishingmax.co.jp/fishingpost?shop=shop-tarumi",
        ]
        
        for url in urls_to_try:
            try:
                time.sleep(1)
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    resp.encoding = 'utf-8'
                    soup = BeautifulSoup(resp.text, 'lxml')
                    
                    # 記事カードを取得
                    articles = soup.select('article, .post-item, .card, [class*="post"], [class*="article"]')
                    if not articles:
                        articles = soup.select('a[href*="fishingpost/"]')
                    
                    for article in articles[:10]:
                        text = article.get_text(strip=True)
                        
                        # 日付抽出
                        date_str = ""
                        m = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', text)
                        if m:
                            date_str = f"{int(m.group(2))}/{int(m.group(3))}"
                        
                        # テキストから魚種検出
                        found_fish = []
                        for fish_key in FISH_EMOJI.keys():
                            if fish_key in text:
                                found_fish.append(fish_key)
                        
                        # サイズ抽出
                        size = ""
                        m = re.search(r'([\d.]+)\s*[～~-]\s*([\d.]+)\s*[cC㎝]', text)
                        if m:
                            size = f"{m.group(1)}-{m.group(2)}cm"
                        else:
                            m = re.search(r'([\d.]+)\s*[cC㎝]', text)
                            if m:
                                size = f"~{m.group(1)}cm"
                        
                        title_elem = article.select_one('h2, h3, .title')
                        title = title_elem.get_text(strip=True)[:60] if title_elem else text[:60]
                        
                        for fish in found_fish[:2]:
                            catches.append({
                                "fish": fish,
                                "size": size,
                                "count": "",
                                "method": "",
                                "user": "",
                                "date": date_str,
                                "emoji": get_emoji(fish),
                                "description": title,
                            })
                        
                        if not found_fish and date_str:
                            catches.append({
                                "fish": title[:20],
                                "size": size,
                                "count": "",
                                "method": "",
                                "user": "",
                                "date": date_str,
                                "emoji": "🐟",
                                "description": title,
                            })
                    
            except Exception as e:
                print(f"  ⚠️ フィッシングマックス直接アクセスエラー: {e}")
        
        # 直接アクセスで取れなかった場合、Google検索にフォールバック
        if not catches:
            print("  ↪ Google検索にフォールバック...")
            search_url = "https://www.google.com/search"
            params = {
                'q': 'site:fishingmax.co.jp 釣果 神戸 OR 須磨 OR 垂水',
                'num': 10,
                'tbs': 'qdr:w',  # 直近1週間
            }
            
            try:
                time.sleep(2)
                resp = requests.get(search_url, params=params, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'lxml')
                    
                    for result in soup.select('div.g, div[data-sokoban-container]'):
                        title_el = result.select_one('h3')
                        snippet_el = result.select_one('span, .VwiC3b')
                        
                        if title_el:
                            title = title_el.get_text(strip=True)
                            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                            combined = title + " " + snippet
                            
                            found_fish = []
                            for fish_key in FISH_EMOJI.keys():
                                if fish_key in combined:
                                    found_fish.append(fish_key)
                            
                            date_str = ""
                            m = re.search(r'(\d{1,2})/(\d{1,2})', combined)
                            if m:
                                date_str = f"{m.group(1)}/{m.group(2)}"
                            
                            for fish in found_fish[:2]:
                                catches.append({
                                    "fish": fish,
                                    "size": "",
                                    "count": "",
                                    "method": "",
                                    "user": "",
                                    "date": date_str,
                                    "emoji": get_emoji(fish),
                                    "description": title[:60],
                                })
                            
            except Exception as e:
                print(f"  ⚠️ Google検索エラー: {e}")
    
    except Exception as e:
        print(f"  ❌ フィッシングマックスエラー: {e}")
    
    print(f"  ✅ フィッシングマックス: {len(catches)}件取得")
    return {
        "name": "フィッシングマックス",
        "area": "神戸",
        "distance": None,
        "info": "釣具店の釣果レポート（神戸ハーバー店・垂水店）",
        "source": "fishingmax.co.jp",
        "catches": catches
    }


# =============================================================
# 5. アングラーズ（Google検索経由）
# =============================================================
def collect_anglers():
    """アングラーズの釣果をGoogle検索経由で取得"""
    print("📡 [5/5] アングラーズ（Google経由）から収集中...")
    catches = []
    
    try:
        search_url = "https://www.google.com/search"
        params = {
            'q': 'site:anglers.jp 神戸 OR 須磨 OR 平磯 OR 芦屋 OR 明石 釣果',
            'num': 10,
            'tbs': 'qdr:w',
        }
        
        time.sleep(2)
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'lxml')
            
            for result in soup.select('div.g, div[data-sokoban-container]'):
                title_el = result.select_one('h3')
                snippet_el = result.select_one('span, .VwiC3b')
                
                if title_el:
                    title = title_el.get_text(strip=True)
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                    combined = title + " " + snippet
                    
                    found_fish = []
                    for fish_key in FISH_EMOJI.keys():
                        if fish_key in combined:
                            found_fish.append(fish_key)
                    
                    # エリア抽出
                    area = "神戸"
                    for a in ['明石', '芦屋', '須磨', '垂水', '平磯']:
                        if a in combined:
                            area = a
                            break
                    
                    date_str = ""
                    m = re.search(r'(\d{1,2})月(\d{1,2})日', combined)
                    if m:
                        date_str = f"{m.group(1)}/{m.group(2)}"
                    
                    for fish in found_fish[:2]:
                        catches.append({
                            "fish": fish,
                            "size": "",
                            "count": "",
                            "method": "",
                            "user": "",
                            "date": date_str,
                            "emoji": get_emoji(fish),
                            "description": title[:60],
                            "area_detail": area,
                        })
        
        # Google検索がブロックされた場合、アングラーズ兵庫県ページを試行
        if not catches:
            print("  ↪ アングラーズ兵庫県ページを直接試行...")
            try:
                time.sleep(1)
                url = "https://anglers.jp/prefectures/28/catches"
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code == 200 and len(resp.text) > 500:
                    soup = BeautifulSoup(resp.text, 'lxml')
                    
                    for card in soup.select('[class*="catch"], [class*="card"], article'):
                        text = card.get_text(strip=True)
                        found_fish = []
                        for fish_key in FISH_EMOJI.keys():
                            if fish_key in text:
                                found_fish.append(fish_key)
                        
                        for fish in found_fish[:1]:
                            catches.append({
                                "fish": fish,
                                "size": "",
                                "count": "",
                                "method": "",
                                "user": "",
                                "date": "",
                                "emoji": get_emoji(fish),
                                "description": text[:60],
                            })
            except Exception as e:
                print(f"  ⚠️ アングラーズ直接アクセスエラー: {e}")
    
    except Exception as e:
        print(f"  ❌ アングラーズエラー: {e}")
    
    print(f"  ✅ アングラーズ: {len(catches)}件取得")
    return {
        "name": "アングラーズ",
        "area": "兵庫",
        "distance": None,
        "info": "釣りSNSのユーザー投稿",
        "source": "anglers.jp",
        "catches": catches
    }


# =============================================================
# 潮汐・天文データ計算
# =============================================================
def calculate_moon_phase():
    """月齢を計算"""
    now = datetime.now()
    # 簡易月齢計算（ブラウンの近似式）
    year = now.year
    month = now.month
    day = now.day
    
    if month <= 2:
        year -= 1
        month += 12
    
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    
    # 月齢計算
    moon_age = (jd - 2451550.1) % 29.530588853
    moon_age = round(moon_age, 1)
    
    # 月の名前
    if moon_age < 1.84566:
        name, icon = "新月", "🌑"
    elif moon_age < 5.53699:
        name, icon = "三日月", "🌒"
    elif moon_age < 9.22831:
        name, icon = "上弦の月", "🌓"
    elif moon_age < 12.91963:
        name, icon = "十三夜", "🌔"
    elif moon_age < 16.61096:
        name, icon = "満月", "🌕"
    elif moon_age < 20.30228:
        name, icon = "十八夜", "🌖"
    elif moon_age < 23.99361:
        name, icon = "下弦の月", "🌗"
    elif moon_age < 27.68493:
        name, icon = "二十六夜", "🌘"
    else:
        name, icon = "新月", "🌑"
    
    # 潮名（簡易計算）
    if moon_age <= 2 or (13.5 <= moon_age <= 16.5) or moon_age >= 28:
        tide = "大潮"
    elif (3 <= moon_age <= 5) or (17 <= moon_age <= 19):
        tide = "中潮"
    elif (5 < moon_age <= 7) or (19 < moon_age <= 21):
        tide = "中潮"
    elif (7 < moon_age <= 9) or (21 < moon_age <= 23):
        tide = "小潮"
    elif (9 < moon_age <= 10.5) or (23 < moon_age <= 24.5):
        tide = "長潮"
    else:
        tide = "若潮"
    
    return {
        "age": moon_age,
        "name": name,
        "icon": icon,
        "tide": tide,
    }


def calculate_sun_times():
    """日の出・日の入り時刻の近似計算（神戸）"""
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday
    
    # 神戸（北緯34.69, 東経135.19）での簡易計算
    lat = 34.69
    
    # 赤緯の近似
    declination = -23.44 * math.cos(math.radians(360/365 * (day_of_year + 10)))
    
    # 日の出・日の入り時角
    cos_hour_angle = (-0.01454 - math.sin(math.radians(lat)) * math.sin(math.radians(declination))) / \
                     (math.cos(math.radians(lat)) * math.cos(math.radians(declination)))
    
    if -1 <= cos_hour_angle <= 1:
        hour_angle = math.degrees(math.acos(cos_hour_angle))
        
        # UTC時刻を計算し、JSTに変換
        noon_offset = 12 - (135.19 / 15)  # 経度補正
        sunrise_utc = 12 - hour_angle / 15 + noon_offset
        sunset_utc = 12 + hour_angle / 15 + noon_offset
        
        sunrise_jst = sunrise_utc + 9
        sunset_jst = sunset_utc + 9
        
        sunrise_h = int(sunrise_jst)
        sunrise_m = int((sunrise_jst - sunrise_h) * 60)
        sunset_h = int(sunset_jst)
        sunset_m = int((sunset_jst - sunset_h) * 60)
        
        sunrise = f"{sunrise_h:02d}:{sunrise_m:02d}"
        sunset = f"{sunset_h:02d}:{sunset_m:02d}"
    else:
        sunrise = "06:30"
        sunset = "17:30"
    
    return sunrise, sunset


def calculate_mazume(sunrise, sunset):
    """まずめ時間を計算"""
    # 朝まずめ：日の出30分前〜日の出30分後
    sr_h, sr_m = map(int, sunrise.split(':'))
    sr_total = sr_h * 60 + sr_m
    am_start_total = sr_total - 30
    am_end_total = sr_total + 30
    
    am_start = f"{am_start_total // 60:02d}:{am_start_total % 60:02d}"
    am_end = f"{am_end_total // 60:02d}:{am_end_total % 60:02d}"
    
    # 夕まずめ：日の入り30分前〜日の入り30分後
    ss_h, ss_m = map(int, sunset.split(':'))
    ss_total = ss_h * 60 + ss_m
    pm_start_total = ss_total - 30
    pm_end_total = ss_total + 30
    
    pm_start = f"{pm_start_total // 60:02d}:{pm_start_total % 60:02d}"
    pm_end = f"{pm_end_total // 60:02d}:{pm_end_total % 60:02d}"
    
    return {
        "morning": f"{am_start} - {am_end}",
        "evening": f"{pm_start} - {pm_end}",
    }


# =============================================================
# メイン処理
# =============================================================
def save_data(data, filename='fishing-data.json'):
    """データをJSONファイルに保存"""
    # 既存データがあれば読み込んでマージ
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            existing_catches = {}
            for spot in existing.get('spots', []):
                key = spot.get('source', spot.get('name', ''))
                for c in spot.get('catches', []):
                    catch_key = f"{key}_{c.get('fish','')}_{c.get('date','')}_{c.get('size','')}"
                    existing_catches[catch_key] = True
    except (FileNotFoundError, json.JSONDecodeError):
        existing_catches = {}
    
    print(f"💾 データを {filename} に保存中...")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ 保存完了！")


def run():
    """全データ収集を実行"""
    print("=" * 60)
    print("🎣 神戸釣り情報 自動収集 v2.0")
    print(f"📅 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print("=" * 60)
    
    # 各ソースから収集
    spots = []
    
    spot1 = collect_suma()
    spots.append(spot1)
    
    spot2 = collect_hiraiso()
    spots.append(spot2)
    
    spot3 = collect_kanpari()
    spots.append(spot3)
    
    spot4 = collect_fishingmax()
    spots.append(spot4)
    
    spot5 = collect_anglers()
    spots.append(spot5)
    
    # 潮汐・天文データ
    moon = calculate_moon_phase()
    sunrise, sunset = calculate_sun_times()
    mazume = calculate_mazume(sunrise, sunset)
    
    now = datetime.now()
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    
    # 集計
    total_catches = sum(len(s['catches']) for s in spots)
    
    data = {
        "lastUpdated": now.isoformat(),
        "lastUpdatedDisplay": f"{now.year}年{now.month}月{now.day}日({weekday_names[now.weekday()]})",
        "spots": spots,
        "tideInfo": {
            "date": f"{now.year}年{now.month}月{now.day}日({weekday_names[now.weekday()]})",
            "tide": moon["tide"],
            "moonAge": moon["age"],
            "moonName": moon["name"],
            "moonIcon": moon["icon"],
            "sunrise": sunrise,
            "sunset": sunset,
            "mazume": mazume,
        },
        "stats": {
            "totalCatches": total_catches,
            "sources": 5,
            "lastCollected": now.strftime('%Y-%m-%d %H:%M'),
        }
    }
    
    save_data(data)
    
    print("=" * 60)
    print(f"🎉 データ収集完了！ 合計 {total_catches} 件")
    for s in spots:
        print(f"  {s['source']}: {len(s['catches'])}件")
    print("=" * 60)
    
    return data


if __name__ == "__main__":
    run() 
