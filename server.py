import os
import json
import urllib.request
import urllib.parse
import time
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# 讀取本地的 .env 檔案
def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1)
                    os.environ[k.strip()] = v.strip()

load_env()

# --- 在地精品資料庫 (Local Gold Database) ---
# 免除 API 額度限制，為最常見錶款提供秒回體驗與 100% 正確圖片
LOCAL_WATCH_DB = {
    "126610LN": {
        "brand": "Rolex 勞力士",
        "name": "Submariner Date 潛航者系列",
        "model": "126610LN",
        "officialPrice": "NT$ 341,000",
        "marketPrice": "NT$ 420,000 ~ 460,000",
        "size": "41 mm",
        "lugToLug": "47.6 mm",
        "material": "Oystersteel 蠔式鋼",
        "strap": "Oystersteel 蠔式鋼 (三排鏈節)",
        "power": "70 小時",
        "functions": "時、分、秒、日期顯示、停秒功能",
        "frontImageUrl": "./assets/watch_front.png",
        "sideImageUrl": "-",
        "backImageUrl": "-"
    },
    "126500LN": {
        "brand": "Rolex 勞力士",
        "name": "Cosmograph Daytona 迪通拿",
        "model": "126500LN",
        "officialPrice": "NT$ 531,500",
        "marketPrice": "NT$ 1,150,000 ~ 1,350,000",
        "size": "40 mm",
        "lugToLug": "46.5 mm",
        "material": "Oystersteel 蠔式鋼、陶瓷圈",
        "strap": "Oystersteel 蠔式鋼",
        "power": "72 小時",
        "functions": "計時功能、測速計、停秒",
        "frontImageUrl": "https://www.watchclub.com/upload/watches/main-image/watch-club-rolex-daytona-steel-ceramic-bezel-black-dial-unworn-ref-116500ln-year-2022-1.jpg",
        "sideImageUrl": "-",
        "backImageUrl": "-"
    },
    "5711": {
        "brand": "Patek Philippe 百達翡麗",
        "name": "Nautilus 金鷹系列",
        "model": "5711/1A-010",
        "officialPrice": "NT$ 1,025,000 (已停產)",
        "marketPrice": "NT$ 2,800,000 ~ 3,500,000",
        "size": "40 mm",
        "lugToLug": "44 mm",
        "material": "不鏽鋼",
        "strap": "不鏽鋼",
        "power": "45 小時",
        "functions": "日期、中央大三針",
        "frontImageUrl": "./assets/patek_nautilus.png",
        "sideImageUrl": "-",
        "backImageUrl": "-"
    },
    "15500ST": {
        "brand": "Audemars Piguet 愛彼",
        "name": "Royal Oak 皇家橡樹",
        "model": "15500ST.OO.1220ST.01",
        "officialPrice": "NT$ 851,000",
        "marketPrice": "NT$ 1,250,000 ~ 1,450,000",
        "size": "41 mm",
        "lugToLug": "51 mm",
        "material": "不鏽鋼",
        "strap": "不鏽鋼",
        "power": "70 小時",
        "functions": "日期、時分秒",
        "frontImageUrl": "https://images.audemarspiguet.com/v2/master/AP_15500ST_OO_1220ST_01_A/front.png",
        "sideImageUrl": "https://www.watchclub.com/upload/watches/main-image/watch-club-audemars-piguet-royal-oak-41mm-black-dial-unused-box-papers-ref-15500st-year-2022-2.jpg",
        "backImageUrl": "https://www.watchclub.com/upload/watches/main-image/watch-club-audemars-piguet-royal-oak-41mm-black-dial-unused-box-papers-ref-15500st-year-2022-10.jpg"
    },
    "NOIMG": {
        "brand": "Test 測試頻目",
        "name": "No Image Test Watch",
        "model": "NOIMG-999",
        "officialPrice": "NT$ 99,999",
        "marketPrice": "NT$ 88,888",
        "size": "40 mm",
        "lugToLug": "-",
        "material": "不鏽鋼",
        "strap": "-",
        "power": "-",
        "functions": "測試無圖片顯示功能",
        "frontImageUrl": "https://invalid-url.com/broken.jpg",
        "sideImageUrl": "-",
        "backImageUrl": "-"
    },
    "310.30.42.50.01.001": {
        "brand": "Omega 歐米茄",
        "name": "Speedmaster 登月錶",
        "model": "310.30.42.50.01.001",
        "officialPrice": "NT$ 215,000",
        "marketPrice": "NT$ 185,000 ~ 205,000",
        "size": "42 mm",
        "lugToLug": "47.2 mm",
        "material": "不鏽鋼 / 藍寶石水晶玻璃",
        "strap": "不鏽鋼",
        "power": "50 小時",
        "functions": "手動計時、測速、防磁",
        "frontImageUrl": "https://www.omegawatches.com/media/catalog/product/o/m/omega-speedmaster-moonwatch-professional-co-axial-master-chronometer-chronograph-42-mm-31030425001001-l.png",
        "sideImageUrl": "https://www.fratellowatches.com/wp-content/uploads/2021/01/Omega-Speedmaster-310.30.42.50.01.001-Moonwatch-23.jpg",
        "backImageUrl": "https://www.fratellowatches.com/wp-content/uploads/2021/01/Omega-Speedmaster-310.30.42.50.01.001-Moonwatch-13.jpg"
    }
}

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class TimersHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/search'):
            self.handle_api_search()
        else:
            super().do_GET()

    def call_gemini(self, api_key, model, payload):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            cmd = ['curl', '-s', '-X', 'POST', url, '-H', 'Content-Type: application/json', '-d', json.dumps(payload)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0: raise Exception(f"Curl failed: {result.stderr}")
            res_json = json.loads(result.stdout)
            if 'error' in res_json:
                msg = res_json['error']['message']
                if "429" in str(res_json['error'].get('code', '')):
                    raise Exception(f"RETRY_429:{msg}")
                raise Exception(msg)
            return res_json
        except Exception as e:
            raise e

    def handle_api_search(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        brand = query_params.get('brand', [''])[0]
        query = query_params.get('query', [''])[0].strip().upper()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # 1. 優先檢查在地資料庫 (包含關鍵字匹配)
        matched_local = None
        for key in LOCAL_WATCH_DB:
            if key in query or query in key:
                matched_local = LOCAL_WATCH_DB[key]
                break
        
        if matched_local:
            print(f"--- [LOCAL DB] 命中成功: {query} ---")
            self.wfile.write(json.dumps({"success": True, "data": matched_local, "source": "local"}).encode('utf-8'))
            return

        # 2. API 搜尋 (優化為高效單路徑帶重試)
        load_env()
        api_key = os.environ.get('GEMINI_API_KEY', '')
        if not api_key or api_key == 'YOUR_GEMINI_API_KEY_HERE':
            self.send_error_response("API Key Missing", brand, query)
            return

        print(f"--- [API SEARCH] 開始檢索: [{brand}] {query} ---")
        model_name = "gemini-2.5-flash"
        prompt = f"""請幫我以專業顧問角度搜尋並整理腕錶資訊。
        品牌：{brand}，型號/關鍵字：{query}。
        請幫我搜尋其官網價格(NT$)與市場行情(NT$)，並詳細列出圖片網址(正面、側面、背面)。
        請務必以 JSON 格式輸出，不要 markdown 標籤。
        格式：{{brand, name, model, officialPrice, marketPrice, size, lugToLug, material, strap, power, functions, frontImageUrl, sideImageUrl, backImageUrl}}
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}]
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"遇到 429，等待後進行第 {attempt+1} 次重試...")
                    time.sleep(3.5) # 429 延遲較長
                
                res = self.call_gemini(api_key, model_name, payload)
                text = res['candidates'][0]['content']['parts'][0]['text'].strip()
                if "```json" in text: text = text.split("```json")[1].split("```")[0]
                elif "```" in text: text = text.split("```")[1].split("```")[0]
                
                watch_data = json.loads(text.strip())
                self.wfile.write(json.dumps({"success": True, "data": watch_data, "source": "api"}).encode('utf-8'))
                print(f"--- 搜尋成功 ---")
                return
            except Exception as e:
                err_str = str(e)
                if attempt < max_retries - 1 and "RETRY_429" in err_str:
                    continue
                print(f"API 最終失敗: {err_str}")
                break

        # 3. 失敗時的熱門錶款降級 (如果搜尋包含關鍵字但型號非完全匹配)
        self.send_error_response("搜尋服務暫時忙碌，請稍後再試。", brand, query)

    def send_error_response(self, error_msg, brand, query):
        error_response = {
            "success": False,
            "error": error_msg,
            "data": {
                "brand": brand, "name": query, "model": "...",
                "officialPrice": "-", "marketPrice": "-", "size": "-", "lugToLug": "-", "material": "-", "strap": "-", "power": "-", "functions": "-",
                "frontImageUrl": "./assets/watch_front.png", "sideImageUrl": "./assets/placeholder_side.png", "backImageUrl": "./assets/watch_back.png"
            }
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8086))
    print(f"Timers AI Server (Python) is running on http://127.0.0.1:{port}")
    HTTPServer(('0.0.0.0', port), TimersHandler).serve_forever()
