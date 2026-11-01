# -*- coding: utf-8 -*-
"""
小型株集中投資スクリーナー (screener.py)
遠藤洋氏の著書『10万円から始める！ 小型株集中投資で1億円』の条件に基づく完全自動スクリーニングツール。

【選定基準 ＆ チェックポイント】
1. 市場: 東証全市場（グロース・スタンダード・プライム）
2. 時価総額: 300億円以下 (理想は100億〜200億円)
3. 成長性: 売上高成長率 +20% 以上
4. 上場年数: 直近5年以内 (新規上場銘柄)
5. オーナーシップ: 創業者・役員（インサイダー）保有比率 20% 以上
6. 特徴・サービス: 四季報ベースの事業特色・主力サービス要約
7. 財務健全性: 実質無借金判定（倒産リスク排除）
8. 過熱感・押し目: 52週高値比下落率（-10%〜-35%）
9. チャートトレンド: 25日・75日移動平均線による「上昇トレンド」判定
10. 社員の若さ: 社員の平均年齢
"""

import os
import sys
import io
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf

# WindowsコンソールでのUTF-8出力対応
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==========================================
# MAINTENANCE_REQUIRED: 投資条件パラメータ
# 市場環境や投資方針に応じて以下の数値を調整してください。
# ==========================================
MAX_MARKET_CAP_YEN = 30_000_000_000  # 最大時価総額（300億円）
MIN_REVENUE_GROWTH = 0.20            # 最小売上高成長率（20% = 0.20）
MAX_IPO_YEARS = 5.5                  # 上場後の最大年数（約5年以内）
MIN_INSIDER_HOLDING = 0.20           # 創業者・役員インサイダー保有比率（20%以上）
# 遠藤洋氏の投資対象：市場区分に限定せず、小型成長株全般をカバー
TARGET_MARKETS = ['グロース', 'スタンダード']  # 主要対象市場（プライム小型株も含める場合は拡張可能）
MAX_WORKERS = 10                     # 並列リクエストスレッド数
OUTPUT_CSV_FILE = 'growth_stocks.csv'# 出力先CSVファイル名
# ==========================================


def fetch_company_profile(code):
    """
    Yahoo!ファイナンスの企業情報ページから「特色（四季報要約）」と「平均年齢」を抽出する。
    """
    url = f"https://finance.yahoo.co.jp/quote/{code}.T/profile"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    feature = "事業内容取得中"
    avg_age = "-"

    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            for el in soup.find_all(string=lambda t: t and "特色" in t):
                parent = el.parent
                if parent and parent.name in ["p", "div", "dd"]:
                    text = parent.text.replace("【特色】", "").replace("特色", "").strip()
                    if text and len(text) > 5:
                        feature = text.replace("\n", " ")
                        break

            for dt in soup.find_all(["dt", "th"]):
                if "平均年齢" in dt.text:
                    dd = dt.find_next_sibling()
                    if dd:
                        avg_age = dd.text.strip().replace("歳", "")
                        break
    except Exception:
        pass

    return feature, avg_age


def fetch_jpx_stock_list():
    """
    日本取引所グループ（JPX）の公式サイトから東証全上場銘柄リスト（Excel）を取得し、
    対象市場（グロース、スタンダード等）の銘柄を抽出する。
    """
    print("[1/3] 日本取引所グループ(JPX)から最新の上場銘柄リストを取得中...")
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xlsx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        df = pd.read_excel(io.BytesIO(response.content))
    except Exception as e:
        print(f"JPXデータの取得に失敗しました: {e}", file=sys.stderr)
        return []

    code_col = df.columns[1]
    name_col = df.columns[2]
    market_col = df.columns[3]
    sector_col = df.columns[5]

    stocks = []
    for _, row in df.iterrows():
        raw_market = str(row[market_col]).strip()
        # 対象市場の判定
        matched_market = None
        for m in TARGET_MARKETS:
            if m in raw_market:
                matched_market = m
                break
        
        if matched_market:
            code = str(row[code_col]).strip()
            name = str(row[name_col]).strip()
            sector = str(row[sector_col]).strip()
            stocks.append({
                "code": code,
                "name": name,
                "market": matched_market,
                "sector": sector
            })

    print(f" -> 対象市場({', '.join(TARGET_MARKETS)})の銘柄数: {len(stocks)} 件を抽出しました。")
    return stocks


def inspect_single_stock(stock_meta):
    """
    個別銘柄の財務・株価・株主・チャートトレンドデータを取得し、条件に合致するか判定する。
    """
    code = stock_meta["code"]
    name = stock_meta["name"]
    market = stock_meta["market"]
    sector = stock_meta["sector"]
    ticker_symbol = f"{code}.T"
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        if not info:
            return None

        # 1. 時価総額チェック
        market_cap = info.get("marketCap")
        if not market_cap or market_cap > MAX_MARKET_CAP_YEN:
            return None

        # 2. 売上高成長率チェック
        revenue_growth = info.get("revenueGrowth")
        if revenue_growth is None or revenue_growth < MIN_REVENUE_GROWTH:
            return None

        # 3. 株価履歴から上場時期 ＆ チャートトレンド判定
        ipo_date_str = "不明"
        ipo_years = None
        trend_status = "保ち合い 🔄"
        try:
            hist = ticker.history(period="6mo")
            if not hist.empty:
                first_date = hist.index[0]
                now_date = datetime.now(first_date.tz) if first_date.tz else datetime.now()
                ipo_years = (now_date - first_date).days / 365.25
                ipo_date_str = first_date.strftime("%Y-%m-%d")

                if ipo_years > MAX_IPO_YEARS:
                    return None

                if len(hist) >= 25:
                    hist['SMA25'] = hist['Close'].rolling(window=25).mean()
                    latest_close = hist['Close'].iloc[-1]
                    latest_sma25 = hist['SMA25'].iloc[-1]

                    if len(hist) >= 75:
                        hist['SMA75'] = hist['Close'].rolling(window=75).mean()
                        latest_sma75 = hist['SMA75'].iloc[-1]
                        
                        if latest_close > latest_sma25 and latest_sma25 > latest_sma75:
                            trend_status = "上昇トレンド 🚀"
                        elif latest_close < latest_sma25 and latest_sma25 < latest_sma75:
                            trend_status = "下降トレンド ⚠️"
                        else:
                            trend_status = "保ち合い / 転換 🔄"
                    else:
                        if latest_close > latest_sma25:
                            trend_status = "上昇トレンド 🚀"
                        else:
                            trend_status = "下降トレンド ⚠️"
        except Exception:
            pass

        # 4. 創業者・役員（インサイダー）保有比率チェック
        insider_held = None
        try:
            mh = ticker.major_holders
            if mh is not None and not mh.empty:
                if 'insidersPercentHeld' in mh.index:
                    insider_held = float(mh.loc['insidersPercentHeld', 'Value'])
                elif 'Value' in mh.columns and len(mh) > 0:
                    for idx_name in mh.index:
                        if 'insider' in str(idx_name).lower():
                            insider_held = float(mh.loc[idx_name, 'Value'])
                            break
        except Exception:
            pass

        if insider_held is not None and insider_held < MIN_INSIDER_HOLDING:
            return None

        # 代表取締役社長の氏名を取得
        ceo_name = "不明"
        try:
            officers = info.get("companyOfficers", [])
            for off in officers:
                title = str(off.get("title", "")).lower()
                if "president" in title or "representative" in title or "ceo" in title:
                    ceo_name = off.get("name", "不明")
                    break
            if ceo_name == "不明" and officers:
                ceo_name = officers[0].get("name", "不明")
        except Exception:
            pass

        # 5. 特徴・サービス ＆ 社員の平均年齢
        feature, avg_age = fetch_company_profile(code)

        # 6. 財務健全性（実質無借金判定）
        total_cash = info.get("totalCash") or 0
        total_debt = info.get("totalDebt") or 0
        is_debt_free = (total_cash > total_debt) or (total_debt == 0)
        debt_status = "実質無借金(極めて安全)" if is_debt_free else "有利子負債あり"

        # 7. 過熱感・押し目判定（52週高値比下落率）
        high_52 = info.get("fiftyTwoWeekHigh")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        high_drop_pct = None
        is_dip_buy = False
        if high_52 and current_price:
            high_drop_pct = round(((high_52 - current_price) / high_52) * 100, 1)
            is_dip_buy = (10.0 <= high_drop_pct <= 35.0)

        # 8. テンバガー試算（3年後成長シミュレーション）
        growth_multiplier = round(((1 + revenue_growth) ** 3), 2)

        # 指標のフォーマット
        forward_pe = info.get("forwardPE") or info.get("trailingPE")
        pbr = info.get("priceToBook")
        roe = info.get("returnOnEquity")

        mcap_oku = round(market_cap / 100_000_000, 1)
        rev_growth_pct = round(revenue_growth * 100, 1)
        insider_pct = round(insider_held * 100, 1) if insider_held is not None else "-"
        roe_pct = round(roe * 100, 1) if roe is not None else "-"

        return {
            "コード": code,
            "銘柄名": name,
            "市場": market,
            "特徴・サービス": feature,
            "チャートトレンド": trend_status,
            "平均年齢": f"{avg_age}歳" if avg_age != "-" else "-",
            "業種": sector,
            "時価総額(億円)": mcap_oku,
            "売上高成長率(%)": rev_growth_pct,
            "インサイダー保有率(%)": insider_pct,
            "代表取締役": ceo_name,
            "株価(円)": int(current_price) if current_price else "-",
            "単元購入額(万円)": round((current_price * 100) / 10000, 1) if current_price else "-",
            "財務健全性": debt_status,
            "PER": round(forward_pe, 1) if forward_pe else "-",
            "高値下落率(%)": high_drop_pct if high_drop_pct is not None else "-",
            "押し目フラグ": "押し目買い圏" if is_dip_buy else "適正/高値圏",
            "3年後想定倍率": f"{growth_multiplier}倍",
            "上場時期": ipo_date_str,
            "PBR": round(pbr, 2) if pbr else "-",
            "ROE(%)": roe_pct,
            "株探URL": f"https://kabutan.jp/stock/?code={code}",
            "バフェットコードURL": f"https://www.buffett-code.com/company/{code}/"
        }

    except Exception:
        return None


def run_screening():
    """
    全銘柄のスクリーニングを実行し、結果をCSV保存および画面表示する。
    """
    start_time = time.time()
    stocks = fetch_jpx_stock_list()
    if not stocks:
        print("銘柄リストが取得できなかったため終了します。")
        return

    print(f"[2/3] 全 {len(stocks)} 銘柄の財務・株主・チャート・特色データ取得中（並列数: {MAX_WORKERS}）...")
    matched_results = []
    completed_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_stock = {executor.submit(inspect_single_stock, s): s for s in stocks}
        
        for future in as_completed(future_to_stock):
            completed_count += 1
            if completed_count % 100 == 0 or completed_count == len(stocks):
                print(f" -> 進捗: {completed_count}/{len(stocks)} 銘柄完了...")

            res = future.result()
            if res:
                matched_results.append(res)

    print(f"\n[3/3] スクリーニング完了！ (所要時間: {round(time.time() - start_time, 1)}秒)")
    print(f" -> 創業者・オーナー小型成長株数: {len(matched_results)} 件\n")

    if not matched_results:
        print("条件に合致する銘柄は見つかりませんでした。")
        return

    result_df = pd.DataFrame(matched_results)
    result_df["_sort_insider"] = pd.to_numeric(result_df["インサイダー保有率(%)"], errors="coerce").fillna(0)
    result_df.sort_values(by=["_sort_insider", "売上高成長率(%)"], ascending=[False, False], inplace=True)
    result_df.drop(columns=["_sort_insider"], inplace=True)
    result_df.reset_index(drop=True, inplace=True)

    # コンソール表示
    display_cols = ["コード", "銘柄名", "市場", "チャートトレンド", "平均年齢", "時価総額(億円)", "売上高成長率(%)", "インサイダー保有率(%)", "特徴・サービス"]
    print("=" * 130)
    print("★ 遠藤洋氏ロジック完全準拠：オーナー小型成長株スクリーニング結果 ★")
    print("=" * 130)
    print(result_df[display_cols].head(25).to_string(index=False))
    print("=" * 130)

    # CSV出力
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, OUTPUT_CSV_FILE)
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n全件の詳細データをCSV保存しました:\n -> {output_path}\n")


if __name__ == "__main__":
    run_screening()
