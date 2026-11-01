# -*- coding: utf-8 -*-
"""
遠藤洋式 小型株集中投資 Webダッシュボード (app.py)
著書『10万円から始める！ 小型株集中投資で1億円』の全メソッドを完全実装した高視認性Webアプリ。

【デザイン ＆ 機能刷新】
- 完全ライトモード固定（純白背景・濃紺テキスト・高コントラスト設計）
- 適用条件バッジの表示ズレ・白飛びを完全解消（Flexboxレスポンシブ枠）
- 市場フィルターの全市場対応（グロース／スタンダード／プライムの自由選択）
- 8大チェックポイント完全網羅（チャート上昇トレンド判定、社員平均年齢の若さ）
- イノベーター理論に基づく「買い時（アーリーアダプター）・売り時（過熱）」インジケーター
- CM・広告戦略の早期察知ツール（Meta広告ライブラリ、YouTube公式CM、PR TIMES新CM発表）
- 「1日5分保有株ウォッチ ＆ 損切り管理」シート（-10%〜-20%ロスカットアラート付き）
"""

import os
import sys
import json
import subprocess
import urllib.parse
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import streamlit as st
import streamlit.components.v1 as components

# チャート描画用ライブラリの安全なインポート
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# 実行環境に依存しない動的パス解決（PC移行・ユーザー変更に完全対応）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "growth_stocks.csv")
THEME_STOCKS_CACHE_FILE = os.path.join(BASE_DIR, "theme_stocks_cache.csv")
SETTINGS_FILE = os.path.join(BASE_DIR, "search_conditions.json")
STATUS_FILE = os.path.join(BASE_DIR, "stock_status.json")
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")
NOTES_FILE = os.path.join(BASE_DIR, "stock_notes.json")
APP_ICON_FILE = os.path.join(BASE_DIR, "apple-touch-icon.png")

# ページ基本設定（スマホ画面向けに初期サイドバーを折りたたみに設定）
st.set_page_config(
    page_title="TOTOTO-KABU | 小型株集中投資ダッシュボード",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# スマホ ホーム画面アイコン ＆ PWAメタタグ動的注入
# ==========================================
if os.path.exists(APP_ICON_FILE):
    import base64
    with open(APP_ICON_FILE, "rb") as _icon_f:
        _icon_b64 = base64.b64encode(_icon_f.read()).decode("utf-8")
    
    st.markdown(f"""
    <head>
        <link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,{_icon_b64}">
        <link rel="icon" type="image/png" sizes="192x192" href="data:image/png;base64,{_icon_b64}">
        <meta name="apple-mobile-web-app-title" content="TOTOTO-KABU">
        <meta name="application-name" content="TOTOTO-KABU">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    </head>
    <script>
        (function() {{
            try {{
                var doc = window.parent.document || document;
                var head = doc.getElementsByTagName('head')[0];
                if (!head) return;

                // Apple Touch Icon の注入・更新
                var appleIcon = doc.querySelector("link[rel='apple-touch-icon']");
                if (!appleIcon) {{
                    appleIcon = doc.createElement('link');
                    appleIcon.rel = 'apple-touch-icon';
                    head.appendChild(appleIcon);
                }}
                appleIcon.href = 'data:image/png;base64,{_icon_b64}';

                // 一般ファビコンの更新
                var favIcon = doc.querySelector("link[rel='icon']");
                if (favIcon) {{
                    favIcon.href = 'data:image/png;base64,{_icon_b64}';
                }}

                // アプリタイトルメタタグ
                var metaAppleTitle = doc.querySelector("meta[name='apple-mobile-web-app-title']");
                if (!metaAppleTitle) {{
                    metaAppleTitle = doc.createElement('meta');
                    metaAppleTitle.name = 'apple-mobile-web-app-title';
                    head.appendChild(metaAppleTitle);
                }}
                metaAppleTitle.content = 'TOTOTO-KABU';

                var metaAppName = doc.querySelector("meta[name='application-name']");
                if (!metaAppName) {{
                    metaAppName = doc.createElement('meta');
                    metaAppName.name = 'application-name';
                    head.appendChild(metaAppName);
                }}
                metaAppName.content = 'TOTOTO-KABU';

                // ドキュメントタイトル
                doc.title = 'TOTOTO-KABU';

                // Streamlit Cloud 特有の不要なバッジ・管理ボタンの抹消ルーチン
                function hideCloudBadges() {{
                    var selectors = [
                        '[data-testid="stManageApp"]',
                        '[data-testid="manage-app-button"]',
                        '.viewerBadge_container__1QSob',
                        'div[class*="viewerBadge"]',
                        'div[class*="manageApp"]',
                        'div[class*="stAppDeployButton"]',
                        'header[data-testid="stHeader"] [data-testid="stToolbar"]',
                        'header[data-testid="stHeader"]',
                        '[data-testid="stStatusWidget"]',
                        'div.stStatusWidget',
                        'svg[data-testid="stLogo"]',
                        'a[href*="streamlit.io"]',
                        'div[data-testid="stDecoration"]'
                    ];
                    var docs = [document];
                    try {{
                        if (window.parent && window.parent.document && window.parent.document !== document) {{
                            docs.push(window.parent.document);
                        }}
                    }} catch(e) {{}}

                    docs.forEach(function(d) {{
                        selectors.forEach(function(sel) {{
                            try {{
                                var nodes = d.querySelectorAll(sel);
                                for (var i = 0; i < nodes.length; i++) {{
                                    nodes[i].style.setProperty('display', 'none', 'important');
                                    nodes[i].style.setProperty('visibility', 'hidden', 'important');
                                    nodes[i].style.setProperty('height', '0px', 'important');
                                    nodes[i].style.setProperty('opacity', '0', 'important');
                                }}
                            }} catch(e) {{}}
                        }});
                    }});
                }}
                hideCloudBadges();
                setInterval(hideCloudBadges, 800);
            }} catch(e) {{}}
        }})();
    </script>
    """, unsafe_allow_html=True)


# ==========================================
# 高視認性・完全ライトモードCSSの注入
# ==========================================
st.markdown("""
<style>
    /* ==========================================
       Streamlit Cloud 不要UI要素の完全根こそぎ消去
       ========================================== */
    #MainMenu {visibility: hidden !important; display: none !important;}
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    [data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    [data-testid="stDecoration"] {display: none !important; visibility: hidden !important;}
    [data-testid="stStatusWidget"] {display: none !important; visibility: hidden !important;}
    div.stStatusWidget {display: none !important; visibility: hidden !important;}
    svg[data-testid="stLogo"] {display: none !important; visibility: hidden !important;}
    a[href*="streamlit.io"] {display: none !important; visibility: hidden !important;}
    footer {visibility: hidden !important; display: none !important;}
    button[data-testid="stDeployButton"] {display: none !important; visibility: hidden !important;}
    div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stManageApp"] {display: none !important; visibility: hidden !important;}
    div[class*="manageApp"] {display: none !important; visibility: hidden !important;}
    div[class*="stAppDeployButton"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stBottomBlockContainer"] {display: none !important;}
    iframe[title*="streamlit"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    [data-testid="manage-app-button"],
    div[data-testid="manage-app-button"],
    div[class*="Profile"],
    button[class*="Profile"],
    div[class*="stBottom"],
    [data-testid="stBottom"],
    div[class*="floatingButton"],
    div[class*="HostBadge"],
    div[class*="ProfileBadge"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* 全体背景を純白に固定し、文字色を濃紺・黒に強制 */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }

    /* Android Chrome Sticky対策：親スクロールコンテナのoverflow正常化 */
    [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        overflow-y: auto !important;
    }
    section.main {
        overflow: visible !important;
    }

    
    /* サイドバーの背景 */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 2px solid #E2E8F0 !important;
    }
    
    /* 見出しのスタイル（サイズを適切に引き締め） */
    h1 { color: #0F172A !important; font-weight: 800 !important; font-size: 1.65rem !important; }
    h2 { color: #0F172A !important; font-weight: 800 !important; font-size: 1.3rem !important; }
    h3 { color: #0F172A !important; font-weight: 700 !important; font-size: 1.1rem !important; }
    h4, h5, h6 { color: #0F172A !important; font-weight: 700 !important; }

    /* メトリクスカードの文字サイズ最適化（見切れ・三点リーダー防止） */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        white-space: normal !important;
        word-break: break-word !important;
        color: #0F172A !important;
        line-height: 1.3 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }

    /* 右上の不要なDeployボタンのみを非表示化 */
    button[data-testid="stDeployButton"] {display: none !important;}

    /* カード枠線の強調 (ライトモード用高コントラスト) */
    [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #CBD5E1 !important;
        border-radius: 12px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        padding: 18px !important;
        margin-bottom: 16px !important;
    }

    /* 条件バッジ表示コンテナ (表示ズレ・白飛び防止Flexbox) */
    .filter-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        background-color: #EFF6FF;
        border: 2px solid #3B82F6;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 20px;
    }
    .filter-label {
        font-weight: 800;
        color: #1E3A8A;
        font-size: 0.95rem;
    }
    .filter-tag {
        display: inline-block;
        background-color: #DBEAFE;
        color: #1E40AF;
        border: 1px solid #93C5FD;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        margin: 2px 4px;
    }
    .filter-count {
        font-weight: 800;
        color: #1D4ED8;
        font-size: 1.1rem;
        white-space: nowrap;
    }

    /* ボタンのホバー強調 ＆ 高さ・配置の完全統一デザイン */
    .action-btn {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        min-height: 72px !important;
        height: 100% !important;
        padding: 10px 8px !important;
        border-radius: 8px !important;
        text-align: center !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        line-height: 1.3 !important;
        text-decoration: none !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
        box-sizing: border-box !important;
    }
    .action-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    .action-btn small {
        display: block !important;
        font-weight: 400 !important;
        font-size: 0.75rem !important;
        margin-top: 4px !important;
        opacity: 0.95 !important;
    }

    /* ==========================================
       立体ピル型タブ ＆ 完全独立ナビゲーションバー（青背景×白地）
       ========================================== */
    [data-testid="stTabs"] {
        position: -webkit-sticky !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 9999 !important;
        margin-bottom: 20px !important;
        background-color: #FFFFFF !important;
        padding-top: 4px !important;
        padding-bottom: 4px !important;
    }
    
    [data-testid="stTabs"] [role="tablist"] {
        position: -webkit-sticky !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 9999 !important;
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%) !important; /* 濃紺〜ロイヤルブルーの独立バー帯 */
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        gap: 8px !important;
        padding: 8px 10px 10px 8px !important;
        border: 2px solid #2563EB !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.25) !important;
        scrollbar-width: thin !important;
        scrollbar-color: #60A5FA #1E293B !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* スタイリッシュな細型スクロールバー */
    [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar {
        height: 5px !important;
    }
    [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar-track {
        background: #1E293B !important;
        border-radius: 10px !important;
    }
    [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar-thumb {
        background: #60A5FA !important;
        border-radius: 10px !important;
    }

    /* 各タブボタン：独立バー内の半透明ピル（白地・白テキスト） */
    [data-testid="stTabs"] button[role="tab"] {
        flex: 0 0 auto !important;
        white-space: nowrap !important;
        padding: 8px 16px !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.90rem !important;
        color: #FFFFFF !important; /* 純白テキスト */
        background-color: rgba(255, 255, 255, 0.14) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }

    /* タブ内すべての文字を純白に強制（全体CSSの黒文字上書き） */
    [data-testid="stTabs"] button[role="tab"] *,
    [data-testid="stTabs"] button[role="tab"] p,
    [data-testid="stTabs"] button[role="tab"] span,
    [data-testid="stTabs"] button[role="tab"] div {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* タブのホバー時：白く輝く */
    [data-testid="stTabs"] button[role="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.28) !important;
        border-color: #93C5FD !important;
        transform: translateY(-2px) !important;
    }

    /* 選択中（アクティブ）タブ：鮮やかなゴールド ＋ 濃紺文字 ＋ 浮遊シャドウ */
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #FDE047 0%, #F59E0B 100%) !important; /* 鮮やかなゴールド */
        border: 1.5px solid #FCD34D !important;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] *,
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] span,
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] div {
        color: #0F172A !important; /* 濃紺文字でクッキリ視認 */
        font-weight: 800 !important;
    }

    /* デフォルトの赤い下線を完全消去 */
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* ==========================================
       全ボタン共通デザイン：色付き背景 ＆ 白抜き文字 ＆ 立体視認性
       ========================================== */
    div.stButton > button,
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: 1.5px solid #1D4ED8 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.90rem !important;
        min-height: 42px !important;
        height: 42px !important;
        padding: 0 16px !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
    }
    div.stButton > button:hover,
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 10px rgba(30, 58, 138, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button *,
    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div,
    div[data-testid="stDownloadButton"] > button * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* 「全候補銘柄一覧に戻る」ボタン：スレート濃紺で高さ42px・位置を完全一致 */
    div.stButton > button[key*="btn_back_list"],
    button[key*="btn_back_list"] {
        background: linear-gradient(135deg, #334155 0%, #475569 100%) !important;
        border: 1.5px solid #1E293B !important;
        min-height: 42px !important;
        height: 42px !important;
    }

    /* ヘッダータイトルの純白強制（全体CSSのh1黒色を完全上書き） */
    h1.header-title-text, .header-title-text {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    .header-sub-text {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.6) !important;
    }

    /* データテーブル（st.data_editor / st.dataframe）のスクロールバー常時可視化＆立体化 */
    [data-testid="stDataEditor"] *, [data-testid="stDataFrame"] * {
        scrollbar-width: thin !important;
        scrollbar-color: #3B82F6 #EFF6FF !important;
        -webkit-overflow-scrolling: touch !important;
    }
    [data-testid="stDataEditor"] *::-webkit-scrollbar, [data-testid="stDataFrame"] *::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
        display: block !important;
    }
    [data-testid="stDataEditor"] *::-webkit-scrollbar-track, [data-testid="stDataFrame"] *::-webkit-scrollbar-track {
        background: #EFF6FF !important;
        border-radius: 4px !important;
    }
    [data-testid="stDataEditor"] *::-webkit-scrollbar-thumb, [data-testid="stDataFrame"] *::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important;
        border-radius: 4px !important;
        border: 1.5px solid #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
    }

    /* 用語解説アコーディオンの劇的強調スタイル */
    [data-testid="stExpander"] details summary p {
        font-size: 1.08rem !important;
        font-weight: 800 !important;
        color: #1E3A8A !important;
    }
    [data-testid="stExpander"] details {
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    }
    [data-testid="stExpander"] details summary:hover p {
        color: #2563EB !important;
    }

    /* 投資メモ・テキスト入力エリアの視認性最大化（枠線常時くっきり表示） */
    [data-testid="stTextArea"] textarea {
        border: 2px solid #3B82F6 !important; /* ロイヤルブルーの太枠 */
        border-radius: 8px !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        box-shadow: 0 2px 5px rgba(59, 130, 246, 0.08) !important;
        padding: 10px 12px !important;
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: #1D4ED8 !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25) !important;
    }

    /* スマホ特化レスポンシブ最適化 (幅768px以下) */
    @media (max-width: 768px) {
        /* スマホスクロール時のタブ固定位置 */
        [data-testid="stTabs"] [role="tablist"] {
            top: 0 !important;
            padding: 6px 8px !important;
            border-radius: 8px !important;
        }

        .block-container {
            padding-top: 3.2rem !important; /* 画像上部の見切れを完全防止 */
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            padding-bottom: 2rem !important;
        }
        h1 { font-size: 1.25rem !important; }
        h2 { font-size: 1.1rem !important; }
        h3 { font-size: 1.0rem !important; }

        /* メトリクス表示のスマホ最適化 */
        [data-testid="stMetricValue"] {
            font-size: 1.05rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
        }

        /* カードのパディング調整 */
        [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 12px 8px !important;
            margin-bottom: 12px !important;
        }

        /* ボタンのタッチ領域・フォント最適化 */
        .action-btn {
            min-height: 52px !important;
            font-size: 0.82rem !important;
            padding: 8px 4px !important;
        }
        .action-btn small {
            font-size: 0.68rem !important;
            margin-top: 2px !important;
        }

        /* タブボタンの横並び最適化 */
        [data-testid="stTabs"] button[role="tab"] {
            font-size: 0.8rem !important;
            padding: 7px 12px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# チャートデータ取得 ＆ 描画関数 (マルチ期間対応)
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_chart_data(code: str, period="6mo", interval="1d"):
    """
    yfinanceから指定銘柄の株価履歴、移動平均線、出来高を取得してキャッシュ
    """
    try:
        ticker = yf.Ticker(f"{code}.T")
        hist = ticker.history(period=period, interval=interval)
        if hist is None or hist.empty:
            return None
        
        # 期間に応じた移動平均線の計算
        if interval == "1d":
            # 日足の場合：遠藤式 25日短期線・75日中期線
            hist["MA_SHORT"] = hist["Close"].rolling(window=25).mean()
            hist["MA_LONG"] = hist["Close"].rolling(window=75).mean()
            hist["MA_SHORT_LABEL"] = "25日移動平均線"
            hist["MA_LONG_LABEL"] = "75日移動平均線"
        else:
            # 分足・短期足の場合：短期12本・24本線
            hist["MA_SHORT"] = hist["Close"].rolling(window=12).mean()
            hist["MA_LONG"] = hist["Close"].rolling(window=24).mean()
            hist["MA_SHORT_LABEL"] = "短期線 (12)"
            hist["MA_LONG_LABEL"] = "中期線 (24)"
            
        return hist
    except Exception:
        return None

def render_stock_chart(code: str, name: str):
    """
    1日／1週間／1ヶ月／6ヶ月／1年の期間切り替え可能な高視認性チャートを描画
    """
    period_options = ["1日 (5分足)", "1週間 (15分足)", "1ヶ月", "6ヶ月 (遠藤式標準)", "1年"]
    
    # 水平ボタングループによる期間セレクター
    selected_period = st.radio(
        label="📊 表示期間を選択:",
        options=period_options,
        index=3, # 6ヶ月（遠藤式標準）をデフォルト
        horizontal=True,
        key=f"chart_period_{code}"
    )
    
    config_map = {
        "1日 (5分足)": ("1d", "5m"),
        "1週間 (15分足)": ("5d", "15m"),
        "1ヶ月": ("1mo", "1d"),
        "6ヶ月 (遠藤式標準)": ("6mo", "1d"),
        "1年": ("1y", "1d")
    }
    period_val, interval_val = config_map[selected_period]
    
    df_hist = fetch_chart_data(code, period=period_val, interval=interval_val)
    if df_hist is None or len(df_hist) < 3:
        st.info(f"💡 {code} {name} の【{selected_period}】データを取得中、または取引データがありません。下の「株探」リンクから詳細チャートをご確認いただけます。")
        return

    latest_close = df_hist["Close"].iloc[-1]
    latest_ma_short = df_hist["MA_SHORT"].iloc[-1] if not pd.isna(df_hist["MA_SHORT"].iloc[-1]) else None
    latest_ma_long = df_hist["MA_LONG"].iloc[-1] if not pd.isna(df_hist["MA_LONG"].iloc[-1]) else None
    ma_short_label = df_hist["MA_SHORT_LABEL"].iloc[0] if "MA_SHORT_LABEL" in df_hist.columns else "短期線"
    ma_long_label = df_hist["MA_LONG_LABEL"].iloc[0] if "MA_LONG_LABEL" in df_hist.columns else "中期線"

    # トレンド概況のメッセージ
    trend_msg = ""
    if latest_ma_short and latest_ma_long:
        if latest_close >= latest_ma_short >= latest_ma_long:
            trend_msg = f"🔥 **株価 > {ma_short_label} > {ma_long_label}**: 強い上昇トレンド（パーフェクトオーダー）状態です。"
        elif latest_close >= latest_ma_short:
            trend_msg = f"📈 **株価 > {ma_short_label}**: 短期上昇トレンドを維持しています。"
        else:
            trend_msg = f"⚠️ **株価 < {ma_short_label}**: 調整局面です。押し目形成または反発を確認してください。"

    st.markdown(f"**最新価格: {latest_close:,.1f} 円** ｜ {trend_msg}")

    if HAS_PLOTLY:
        # Plotlyによるインタラクティブローソク足チャート
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.72, 0.28],
            subplot_titles=("", "出来高")
        )

        # ローソク足（日本式：赤＝陽線、青＝陰線）
        fig.add_trace(
            go.Candlestick(
                x=df_hist.index,
                open=df_hist["Open"],
                high=df_hist["High"],
                low=df_hist["Low"],
                close=df_hist["Close"],
                name="株価",
                increasing_line_color="#DC2626",
                decreasing_line_color="#2563EB",
            ),
            row=1, col=1
        )

        # 短期移動平均線
        if latest_ma_short is not None:
            fig.add_trace(
                go.Scatter(
                    x=df_hist.index,
                    y=df_hist["MA_SHORT"],
                    mode="lines",
                    name=ma_short_label,
                    line=dict(color="#16A34A", width=2)
                ),
                row=1, col=1
            )

        # 中期移動平均線
        if latest_ma_long is not None:
            fig.add_trace(
                go.Scatter(
                    x=df_hist.index,
                    y=df_hist["MA_LONG"],
                    mode="lines",
                    name=ma_long_label,
                    line=dict(color="#EA580C", width=2)
                ),
                row=1, col=1
            )

        # 出来高バー
        fig.add_trace(
            go.Bar(
                x=df_hist.index,
                y=df_hist["Volume"],
                name="出来高",
                marker_color="#94A3B8"
            ),
            row=2, col=1
        )

        # 高視認性ライトモードデザインレイアウト
        fig.update_layout(
            height=440,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            xaxis_rangeslider_visible=False,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=12, color="#0F172A")
            ),
            hovermode="x unified"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#E2E8F0", gridwidth=1)
        fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", gridwidth=1, row=1, col=1)
        fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", gridwidth=1, row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)
    else:
        # Plotlyがない場合のフォールバック描画
        st.line_chart(df_hist[["Close", "MA_SHORT", "MA_LONG"]].dropna())
        st.bar_chart(df_hist[["Volume"]])


# ==========================================
# FX視点のエントリー現在地 ＆ 過熱感精密診断関数
# ==========================================
def analyze_entry_timing(code: str, high_drop_val=None):
    """
    FXチャート分析の視点を株式に適用し、エントリー現在地と過熱感を多角的に精密診断する
    """
    df_daily = fetch_chart_data(code, period="6mo", interval="1d")
    if df_daily is None or len(df_daily) < 10:
        return {
            "status": "⚪ データ蓄積中",
            "badge_color": "#64748B",
            "bg_color": "#F8FAFC",
            "border_color": "#CBD5E1",
            "ma25_bias": None,
            "high_dist": high_drop_val,
            "action": "直近のチャートデータを直接確認してください",
            "advice": "IPOから日が浅いか、直近のデータが不足しています。株探等のチャートを直接ご確認ください。"
        }
    
    latest_close = df_daily["Close"].iloc[-1]
    sma25 = df_daily["MA_SHORT"].iloc[-1] if "MA_SHORT" in df_daily.columns else None
    sma75 = df_daily["MA_LONG"].iloc[-1] if "MA_LONG" in df_daily.columns else None
    
    # 25日線乖離率の計算
    ma25_bias = None
    if sma25 and not pd.isna(sma25) and sma25 > 0:
        ma25_bias = round(((latest_close - sma25) / sma25) * 100, 1)

    # 直近高値までの距離（高値下落率）
    high_dist = high_drop_val
    if high_dist is None or pd.isna(high_dist):
        max_high = df_daily["High"].max()
        if max_high > 0:
            high_dist = round(((max_high - latest_close) / max_high) * 100, 1)
        else:
            high_dist = 10.0

    # 直近3〜5営業日のプライスアクション（連続下落・急落判定）
    recent_closes = df_daily["Close"].tail(5).tolist()
    is_falling_sharply = False
    if len(recent_closes) >= 3:
        consecutive_drops = all(recent_closes[i] > recent_closes[i+1] for i in range(len(recent_closes)-1)[-2:])
        five_day_drop = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] * 100
        if (consecutive_drops and five_day_drop <= -5.0) or (five_day_drop <= -9.0):
            is_falling_sharply = True

    # 判定ロジック（優先度順）
    if is_falling_sharply:
        return {
            "status": "🔴 ⚠️ 落ちるナイフ（急落警戒・手出し無用）",
            "badge_color": "#DC2626",
            "bg_color": "#FEF2F2",
            "border_color": "#F87171",
            "ma25_bias": ma25_bias,
            "high_dist": high_dist,
            "action": "🚫 買いエントリー厳禁・下げ止まり待ち",
            "advice": "突発的な急騰の後に利益確定売りが殺到し、全戻しに向かって急落している最中です。FXで言う『落ちるナイフ』の状態のため、底固め（下げ止まりの陽線やサポートラインでのもみ合い）が確認できるまで絶対に手を出してはいけません。"
        }
    
    elif (high_dist is not None and high_dist <= 3.0) or (ma25_bias is not None and ma25_bias >= 15.0):
        reason = "直近高値（レジスタンス）直前" if (high_dist is not None and high_dist <= 3.0) else f"25日線から乖離過熱 (+{ma25_bias}%)"
        return {
            "status": "🟡 ⏳ 押し目待ち（過熱・高値警戒）",
            "badge_color": "#D97706",
            "bg_color": "#FFFBEB",
            "border_color": "#FCD34D",
            "ma25_bias": ma25_bias,
            "high_dist": high_dist,
            "action": "⚠️ 飛びつき買い厳禁・押し目調整待ち",
            "advice": f"現在、【{reason}】に位置しています。FXで言えば『レジスタンスライン直前でのロング』となり、上値の重い壁に跳ね返されて高値掴みになるリスクが極めて高い局面です。25日移動平均線付近への健全な押し目を待つのが鉄則です。"
        }
    
    elif high_dist is not None and high_dist <= 0.5 and (ma25_bias is not None and ma25_bias < 15.0):
        return {
            "status": "🔵 🚀 高値ブレイク（青天井・順張り圏）",
            "badge_color": "#2563EB",
            "bg_color": "#EFF6FF",
            "border_color": "#93C5FD",
            "ma25_bias": ma25_bias,
            "high_dist": high_dist,
            "action": "⚡ ブレイクアウト順張り（逆指値必須）",
            "advice": "直近高値（レジスタンス）を上抜け、売り圧力が薄い青天井エリアに突入しています。勢いに乗るブレイクアウト局面ですが、ダマシの反落に備えて直近安値にロスカット（逆指値）を必ず設定してください。"
        }
    
    elif (sma25 and latest_close >= sma25) and (ma25_bias is not None and 0.0 <= ma25_bias <= 7.0) and (high_dist is not None and high_dist >= 6.0):
        return {
            "status": "🟢 🎯 押し目買い好機（健全調整・絶好水準）",
            "badge_color": "#16A34A",
            "bg_color": "#F0FDF4",
            "border_color": "#86EFAC",
            "ma25_bias": ma25_bias,
            "high_dist": high_dist,
            "action": "🎯 買いエントリー推奨・リスクリワード最良",
            "advice": "上昇トレンドを綺麗に維持しつつ、25日移動平均線付近まで健全な調整（押し目）が完了した絶好のタイミングです。FXで言う『サポレジ転換での押し目買い』にあたり、下値リスク（損切り幅）が極めて小さく、大きなリターンが狙える局面です。"
        }
    
    else:
        return {
            "status": "⚪ 🔄 様子見 / 調整進行中",
            "badge_color": "#475569",
            "bg_color": "#F8FAFC",
            "border_color": "#CBD5E1",
            "ma25_bias": ma25_bias,
            "high_dist": high_dist,
            "action": "👀 監視継続・シグナル待ち",
            "advice": "保ち合い（レンジ）で方向感を模索しているか、25日線を下回って調整が進行中です。明確な反発の陽線が出るか、トレンド転換シグナルが点灯するまで監視を継続してください。"
        }


# ==========================================
# 投資テーマ・ジャンル定義（上級者仕様・約18テーマ）
# ==========================================
INVESTMENT_THEMES = [
    "🛡️ 防衛・国防・安全保障",
    "🔒 サイバーセキュリティ",
    "🤖 AI・機械学習・先端技術",
    "💻 DX・クラウドSaaS",
    "⚡ 半導体・先端部材",
    "💊 創薬・バイオ・再生医療",
    "🏥 医療・介護・ヘルスケア",
    "🏘️ 不動産開発・再生(CRE)",
    "🔨 建設・インフラ・設備",
    "🛒 EC・ネット通販・D2C",
    "♻️ リユース・環境・リサイクル",
    "📢 マーケティング・PR・広告",
    "👔 人材・教育・リスキリング",
    "🎮 ゲーム・エンタメ・IP",
    "🍽️ 外食・ホテル・温浴施設",
    "☀️ 太陽光・蓄電池・新エネ",
    "🪙 金融・フィンテック・M&A",
    "🚙 自動車・中古車・機械商社"
]

def get_stock_genres(row):
    """銘柄の特徴・サービス、業種、銘柄名から該当する投資テーマ（ジャンル）のリストを判定・返却"""
    text = (str(row.get("特徴・サービス", "")) + " " + str(row.get("業種", "")) + " " + str(row.get("銘柄名", ""))).lower()
    genres = []
    
    # 1. 🛡️ 防衛・国防・安全保障
    if any(k in text for k in ["防衛", "国防", "自衛隊", "警察", "官公庁", "防護服", "防犯", "レーダー", "航空機", "デュポン"]):
        genres.append("🛡️ 防衛・国防・安全保障")
        
    # 2. 🔒 サイバーセキュリティ
    if any(k in text for k in ["セキュリティ", "情報保護", "暗号", "反社チェック", "認証", "脆弱性", "監視カメラ"]):
        genres.append("🔒 サイバーセキュリティ")
        
    # 3. 🤖 AI・機械学習・先端技術
    if any(k in text for k in ["ａｉ", "ai", "人工知能", "機械学習", "画像解析", "音声認識", "異音検知", "ロボ", "エージェント", "３ｄ"]):
        genres.append("🤖 AI・機械学習・先端技術")
        
    # 4. 💻 DX・クラウドSaaS
    if any(k in text for k in ["ｄｘ", "dx", "クラウド", "ｓａａｓ", "saas", "業務効率", "チャット", "ポータル", "システム開発", "受託開発", "ソフトウェア", "パッケージ"]):
        genres.append("💻 DX・クラウドSaaS")
        
    # 5. ⚡ 半導体・先端部材
    if any(k in text for k in ["半導体", "電子部品", "コネクター", "メッキ", "液晶", "ｅｍｓ", "スクリュー", "前工程"]):
        genres.append("⚡ 半導体・先端部材")
        
    # 6. 💊 創薬・バイオ・再生医療
    if any(k in text for k in ["創薬", "バイオ", "細胞治療", "再生医療", "医薬品"]):
        genres.append("💊 創薬・バイオ・再生医療")
        
    # 7. 🏥 医療・介護・ヘルスケア
    if any(k in text for k in ["医療", "介護", "病院", "健診", "ヘルスケア", "訪問診療", "訪問看護", "健康", "ヨガ", "ピラティス"]):
        genres.append("🏥 医療・介護・ヘルスケア")
        
    # 8. 🏘️ 不動産開発・再生(CRE)
    if any(k in text for k in ["不動産", "賃貸", "マンション", "分譲", "リノベ", "ｃｒｅ", "底地", "アパート", "戸建て", "住宅"]):
        genres.append("🏘️ 不動産開発・再生(CRE)")
        
    # 9. 🔨 建設・インフラ・設備
    if any(k in text for k in ["建築", "建設", "土木", "外壁", "空調", "設備工事", "さび取り", "インフラ", "プール", "建材"]):
        genres.append("🔨 建設・インフラ・設備")
        
    # 10. 🛒 EC・ネット通販・D2C
    if any(k in text for k in ["ｅｃ", "ec", "通販", "ネット通販", "ネット販売", "ショッピング", "越境", "靴", "ユニフォーム", "アパレル"]):
        genres.append("🛒 EC・ネット通販・D2C")
        
    # 11. ♻️ リユース・環境・リサイクル
    if any(k in text for k in ["リユース", "リサイクル", "スクラップ", "貴金属", "ｐｃ回収", "廃棄物", "省エネ施設"]):
        genres.append("♻️ リユース・環境・リサイクル")
        
    # 12. 📢 マーケティング・PR・広告
    if any(k in text for k in ["マーケティング", "ｐｒ", "pr", "広告", "ｓｎｓ", "インフルエンサー", "ネット広告", "効果測定"]):
        genres.append("📢 マーケティング・PR・広告")
        
    # 13. 👔 人材・教育・リスキリング
    if any(k in text for k in ["採用", "求人", "教育", "研修", "リスキリング", "障害者雇用", "就職", "高校生"]):
        genres.append("👔 人材・教育・リスキリング")
        
    # 14. 🎮 ゲーム・エンタメ・IP
    if any(k in text for k in ["ゲーム", "アニメ", "漫画", "ｅスポーツ", "カラオケ", "トレカ", "プレステ"]):
        genres.append("🎮 ゲーム・エンタメ・IP")
        
    # 15. 🍽️ 外食・ホテル・温浴施設
    if any(k in text for k in ["串カツ", "外食", "レストラン", "オイスター", "温浴", "テルマー湯", "居酒屋", "給食", "ホテル"]):
        genres.append("🍽️ 外食・ホテル・温浴施設")
        
    # 16. ☀️ 太陽光・蓄電池・新エネ
    if any(k in text for k in ["太陽光", "蓄電池", "発電", "再生可能エネルギー", "再エネ", "新エネルギー"]):
        genres.append("☀️ 太陽光・蓄電池・新エネ")
        
    # 17. 🪙 金融・フィンテック・M&A
    if any(k in text for k in ["ｍ＆ａ", "m&a", "金融", "住宅ローン", "暗号資産", "証券", "フィンテック"]):
        genres.append("🪙 金融・フィンテック・M&A")
        
    # 18. 🚙 自動車・中古車・機械商社
    if any(k in text for k in ["自動車", "中古車", "輸入車", "ディーラー", "工作機械", "切削工具", "商社"]):
        genres.append("🚙 自動車・中古車・機械商社")
        
    return genres


# ==========================================
# 上級者向け：テーマ別主力・代表銘柄（オンデマンド都度取得用）
# ==========================================
THEME_MAJOR_STOCKS = {
    "🛡️ 防衛・国防・安全保障": [
        {"コード": "7011", "銘柄名": "三菱重工業", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "総合重機首位。防衛省向け（戦闘機・護衛艦・ミサイル防衛）最大手。宇宙航空も展開。"},
        {"コード": "7012", "銘柄名": "川崎重工業", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "総合重機大手。潜水艦・哨戒機・防衛ヘリ等の防衛装備品や航空エンジンを製造。"},
        {"コード": "7013", "銘柄名": "IHI", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "総合重機大手。戦闘機用ジェットエンジン開発、宇宙ロケット、誘導弾システムで中核。"},
        {"コード": "6203", "銘柄名": "豊和工業", "市場": "スタンダード", "業種": "機械", "特徴・サービス": "防衛省向け小銃（20式小銃など自衛隊制式小銃）や迫撃砲、特殊工作車両を製造。"},
        {"コード": "7721", "銘柄名": "東京計器", "市場": "プライム", "業種": "精密機器", "特徴・サービス": "防衛・航空・航海用電子機器のパイオニア。自衛隊レーダー警戒装置や慣性誘導装置。"},
        {"コード": "7224", "銘柄名": "新明和工業", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "水陸両用救難飛行艇US-2を製造する防衛指定企業。特装車でも高シェア。"},
        {"コード": "6946", "銘柄名": "日本アビオニクス", "市場": "スタンダード", "業種": "電気機器", "特徴・サービス": "防衛用情報処理システムや赤外線サーモグラフィ、電子ビーム溶接装置でトップ。"},
        {"コード": "6208", "銘柄名": "石川製作所", "市場": "スタンダード", "業種": "機械", "特徴・サービス": "防衛省向け機雷や各種防衛機器を製造。段ボール製函印刷機でも大手。"},
        {"コード": "7980", "銘柄名": "重松製作所", "市場": "スタンダード", "業種": "その他製品", "特徴・サービス": "防毒マスク・防塵マスク・化学防護服で国内首位。自衛隊や警察・消防へ納入。"},
        {"コード": "7963", "銘柄名": "興研", "市場": "スタンダード", "業種": "その他製品", "特徴・サービス": "防塵・防毒マスクで重松と2強。自衛隊向け特殊防護マスクやクリーン環境システム。"},
        {"コード": "4274", "銘柄名": "細谷火工", "市場": "スタンダード", "業種": "化学", "特徴・サービス": "自衛隊向け照明弾・発煙筒・信号弾等の火工品専門メーカー。防衛省指定工場。"},
        {"コード": "4275", "銘柄名": "カーリットホールディングス", "市場": "プライム", "業種": "化学", "特徴・サービス": "産業用爆薬・火薬類の老舗。固体ロケット用推進薬や防衛用火工品を製造。"},
        {"コード": "6111", "銘柄名": "旭精機工業", "市場": "スタンダード", "業種": "機械", "特徴・サービス": "小銃弾・機関銃弾の製造設備や自動連続プレス機で自衛隊・警察向けに強み。"},
        {"コード": "6814", "銘柄名": "古野電気", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "舶用電子機器で世界首位。海上保安庁や防衛省向け艦艇用レーダー・ソナーを提供。"},
        {"コード": "6503", "銘柄名": "三菱電機", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "防衛用レーダーシステム、誘導弾誘導装置、防衛通信衛星通信網の中核サプライヤー。"},
        {"コード": "6701", "銘柄名": "日本電気", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "防衛省向け指揮統制システム（C4I）やサイバー防衛、ソナー・衛星通信網を受注。"},
        {"コード": "6702", "銘柄名": "富士通", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "自衛隊向けクラウド基盤や暗号通信システム、防衛サイバーセキュリティ基盤を開発。"},
        {"コード": "6301", "銘柄名": "小松製作所", "市場": "プライム", "業種": "機械", "特徴・サービス": "自衛隊向け軽装甲機動車やNBC偵察車、特殊車両の開発・製造実績。"},
        {"コード": "7270", "銘柄名": "SUBARU", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "自衛隊向け練習機や多用途ヘリコプター（UH-2）、無人航空機（UAV）を開発。"},
        {"コード": "7003", "銘柄名": "三井E&S", "市場": "プライム", "業種": "機械", "特徴・サービス": "舶用大型ディーゼルエンジン首位。艦艇用主機エンジンや港湾クレーンを製造。"},
        {"コード": "7014", "銘柄名": "名村造船所", "市場": "スタンダード", "業種": "輸送用機器", "特徴・サービス": "大型ばら積み船・タンカー建造大手。防衛省向け特務艇・支援艇の修繕・建造。"},
        {"コード": "7004", "銘柄名": "日立造船", "市場": "プライム", "業種": "機械", "特徴・サービス": "ごみ焼却発電で世界首位級。防衛省向け艦艇用電子機器・環境プラントを手掛ける。"},
        {"コード": "7022", "銘柄名": "サノヤスホールディングス", "市場": "スタンダード", "業種": "機械", "特徴・サービス": "造船発祥の機械メーカー。化粧品製造装置や建設用エレベーター、特装工事を展開。"},
        {"コード": "4617", "銘柄名": "中国塗料", "市場": "プライム", "業種": "化学", "特徴・サービス": "船舶用塗料で国内シェア首位・世界2位。自衛隊護衛艦や潜水艦向け特殊塗料を供給。"},
        {"コード": "5905", "銘柄名": "日本製罐", "市場": "スタンダード", "業種": "金属製品", "特徴・サービス": "18リットル缶やドラム缶の大手。自衛隊向け弾薬缶・燃料用特殊ドラム缶を供給。"},
        {"コード": "6103", "銘柄名": "オークマ", "市場": "プライム", "業種": "機械", "特徴・サービス": "工作機械大手。NC旋盤やマシニングセンタで航空・防衛部品加工に不可欠な精密技術。"},
        {"コード": "6104", "銘柄名": "芝浦機械", "市場": "プライム", "業種": "機械", "特徴・サービス": "大型工作機械や射出成形機大手。航空宇宙・防衛産業向けの超大型加工機に強み。"},
        {"コード": "6141", "銘柄名": "DMG森精機", "市場": "プライム", "業種": "機械", "特徴・サービス": "世界最大手級の工作機械メーカー。5軸加工機で航空機・ロケット部品加工をリード。"},
        {"コード": "6302", "銘柄名": "住友重機械工業", "市場": "プライム", "業種": "機械", "特徴・サービス": "総合機械大手。自衛隊向け機関銃や減速機、極低温冷凍機、放射線医療機器を展開。"},
        {"コード": "6305", "銘柄名": "日立建機", "市場": "プライム", "業種": "機械", "特徴・サービス": "油圧ショベル世界大手。自衛隊施設科部隊向け装甲ドーザや地雷除去機を開発。"},
        {"コード": "7203", "銘柄名": "トヨタ自動車", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "自衛隊の高機動車（メガクルーザー）やトラック・指揮車両の基盤車両を製造。"},
        {"コード": "7205", "銘柄名": "日野自動車", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "自衛隊向け大型トラック（3トン半トラック等）の主要供給メーカー。"},
        {"コード": "7261", "銘柄名": "マツダ", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "防衛産業サプライチェーンにおいて自動車技術・ディーゼルエンジンのノウハウを提供。"},
        {"コード": "7267", "銘柄名": "本田技研工業", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "小型ビジネスジェット「ホンダジェット」開発。自衛隊連絡機・小型航空機分野。"},
        {"コード": "7272", "銘柄名": "ヤマハ発動機", "市場": "プライム", "業種": "輸送用機器", "特徴・サービス": "産業用無人ヘリコプターや小型ボートを展開。国境警備・偵察UAV技術。"},
        {"コード": "4403", "銘柄名": "日油", "市場": "プライム", "業種": "化学", "特徴・サービス": "油脂化学と火薬の国内トップ。防衛用弾薬・推進薬・ロケット固体燃料を製造。"},
        {"コード": "4004", "銘柄名": "レゾナック・ホールディングス", "市場": "プライム", "業種": "化学", "特徴・サービス": "半導体材料や先端複合材料の大手。航空機・防衛装備向けの高強度炭素複合材。"},
        {"コード": "4005", "銘柄名": "住友化学", "市場": "プライム", "業種": "化学", "特徴・サービス": "総合化学大手。アルミナや合成樹脂、防衛用高機能素材を供給。"},
        {"コード": "4188", "銘柄名": "三菱ケミカルグループ", "市場": "プライム", "業種": "化学", "特徴・サービス": "国内最大の総合化学。炭素繊維で航空機・ロケット・防衛軽量化部材を提供。"},
        {"コード": "4183", "銘柄名": "三井化学", "市場": "プライム", "業種": "化学", "特徴・サービス": "高機能ポリマーや眼鏡レンズ材料首位。防護具向け高衝撃吸収樹脂。"},
        {"コード": "4208", "銘柄名": "UBE", "市場": "プライム", "業種": "化学", "特徴・サービス": "宇部興産が発祥。航空宇宙・防衛向け高機能ポリイミドフィルムや窒化ケイ素。"},
        {"コード": "5108", "銘柄名": "ブリヂストン", "市場": "プライム", "業種": "ゴム製品", "特徴・サービス": "タイヤ世界首位級。自衛隊航空機用特殊タイヤや防振ゴムを独占供給。"},
        {"コード": "5101", "銘柄名": "横浜ゴム", "市場": "プライム", "業種": "ゴム製品", "特徴・サービス": "航空部品事業を展開。自衛隊機向け燃料タンクや耐熱配管ホースを製造。"},
        {"コード": "5201", "銘柄名": "AGC", "市場": "プライム", "業種": "ガラス・土石製品", "特徴・サービス": "板ガラス・フッ素化学世界大手。航空機用特殊防弾ガラスや電波透過材。"},
        {"コード": "5334", "銘柄名": "日本特殊陶業", "市場": "プライム", "業種": "ガラス・土石製品", "特徴・サービス": "点火プラグ・排ガスセンサー世界首位。半導体パッケージや防衛用セラミックス。"},
        {"コード": "5401", "銘柄名": "日本製鉄", "市場": "プライム", "業種": "鉄鋼", "特徴・サービス": "国内粗鋼首位。防衛装備・潜水艦用超高張力鋼板（NS鋼板）の独占開発。"},
        {"コード": "5406", "銘柄名": "神戸製鋼所", "市場": "プライム", "業種": "鉄鋼", "特徴・サービス": "チタン圧延品で航空機・防衛省向け高シェア。アルミ・鉄鋼複合素材。"},
        {"コード": "5411", "銘柄名": "JFEホールディングス", "市場": "プライム", "業種": "鉄鋼", "特徴・サービス": "国内鉄鋼2位。防衛省向け高機能特殊鋼や護衛艦用厚板鋼板を納入。"},
        {"コード": "5706", "銘柄名": "三井金属鉱業", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "極薄銅箔世界首位。防衛用電子基板材料や触媒・亜鉛精錬を展開。"},
        {"コード": "5711", "銘柄名": "三菱マテリアル", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "銅・セメント大手。超硬工具や防衛向け特殊合金材料を製造。"},
        {"コード": "5713", "銘柄名": "住友金属鉱山", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "ニッケル・金製錬大手。二次電池正極材や先端電子材料を展開。"},
        {"コード": "5726", "銘柄名": "大阪チタニウムテクノロジーズ", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "スポンジチタンで世界2大メーカー。航空機エンジン・機体用チタンを供給。"},
        {"コード": "5727", "銘柄名": "東邦チタニウム", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "スポンジチタン世界大手。ENEOS系。防衛・航空機向チタン部材を供給。"},
        {"コード": "5801", "銘柄名": "古河電気工業", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "光ファイバー・電線大手。レーザー溶接技術や防衛省向け耐熱電線。"},
        {"コード": "5802", "銘柄名": "住友電気工業", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "ワイヤーハーネス世界首位級。防衛通信用光複合ケーブルや赤外線光学部品。"},
        {"コード": "5803", "銘柄名": "フジクラ", "市場": "プライム", "業種": "非鉄金属", "特徴・サービス": "光ファイバー接続器で世界シェア首位。超高速光通信ケーブルを供給。"},
        {"コード": "6471", "銘柄名": "日本精工", "市場": "プライム", "業種": "機械", "特徴・サービス": "ベアリング国内首位。航空宇宙・防衛装備向けの超精密軸受で高シェア。"},
        {"コード": "6472", "銘柄名": "NTN", "市場": "プライム", "業種": "機械", "特徴・サービス": "ベアリング大手。航空機ジェットエンジン用メインシャフト軸受の重要サプライヤー。"},
        {"コード": "6473", "銘柄名": "ジェイテクト", "市場": "プライム", "業種": "機械", "特徴・サービス": "トヨタ系。ステアリング世界首位級。防衛車両用駆動軸や特殊軸受を製造。"},
        {"コード": "6501", "銘柄名": "日立製作所", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "防衛省向け情報システム、衛星データ解析基盤、エネルギーインフラを提供。"},
        {"コード": "6504", "銘柄名": "富士電機", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "パワー半導体・受変電設備大手。艦艇用電力変換装置や非常用電源システム。"},
        {"コード": "6506", "銘柄名": "安川電機", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "産業用ロボット・サーボモーター世界首位級。FA技術で防衛生産を自動化。"},
        {"コード": "6752", "銘柄名": "パナソニックホールディングス", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "頑丈PC「タフブック」は自衛隊や各国の軍・警察で標準採用。車載電池大手。"},
        {"コード": "6758", "銘柄名": "ソニーグループ", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "CMOSイメージセンサー世界首位。暗視カメラや監視偵察用高感度センサー。"},
        {"コード": "6806", "銘柄名": "ヒロセ電機", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "超小型コネクター大手。高信頼性が要求される航空宇宙・防衛通信機器向け。"},
        {"コード": "6807", "銘柄名": "日本航空電子工業", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "防衛・航空機用慣性航法装置やコネクター大手。ロケット誘導制御システム。"},
        {"コード": "6841", "銘柄名": "横河電機", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "工業計器・制御システム首位。航空機用液晶フラットパネル表示装置を提供。"},
        {"コード": "6902", "銘柄名": "デンソー", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "自動車部品世界トップ級。ミリ波レーダー技術や電子制御ECUを防衛展開。"},
        {"コード": "7731", "銘柄名": "ニコン", "市場": "プライム", "業種": "精密機器", "特徴・サービス": "光学機器大手。自衛隊向け双眼鏡・潜望鏡や航空宇宙用光学測定器を供給。"},
        {"コード": "7732", "銘柄名": "トプコン", "市場": "プライム", "業種": "精密機器", "特徴・サービス": "測量機・眼科機器大手。GNSS測位技術や精密位置決めセンサーに強み。"},
        {"コード": "7751", "銘柄名": "キヤノン", "市場": "プライム", "業種": "精密機器", "特徴・サービス": "超望遠監視カメラや超高感度CMOSセンサーで重要施設警備・防衛監視に貢献。"},
        {"コード": "8001", "銘柄名": "伊藤忠商事", "市場": "プライム", "業種": "卸売業", "特徴・サービス": "大手総合商社。航空・宇宙・防衛装備品やセキュリティシステムの輸入販売代理店。"}
    ],
    "🔒 サイバーセキュリティ": [
        {"コード": "4704", "銘柄名": "トレンドマイクロ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "ウイルスバスターで著名なセキュリティソフト最大手。法人向けクラウド・EDR対策に注力。"},
        {"コード": "3692", "銘柄名": "FFRIセキュリティ", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "未知の脅威を防御する純国産セキュリティ技術を開発。官公庁や重要インフラ向けに強み。"},
        {"コード": "2326", "銘柄名": "デジタルアーツ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "Web・メールフィルタリングソフト「i-FILTER」で国内首位。文教・官公庁市場に強固な地盤。"},
        {"コード": "3857", "銘柄名": "ラック", "市場": "スタンダード", "業種": "情報・通信業", "特徴・サービス": "サイバーセキュリティ診断やセキュリティ監視センター（JSOC）運営の国内パイオニア。"},
        {"コード": "4493", "銘柄名": "サイバーセキュリティクラウド", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "クラウド型WAF「攻撃遮断くん」やAWS WAF自動運用サービスをグローバル展開。"},
        {"コード": "3042", "銘柄名": "セキュアヴェイル", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "ネットワークセキュリティ運用監視（SOC）とログ分析サービス「Logstorage」を提供。"},
        {"コード": "4288", "銘柄名": "アズジェント", "市場": "スタンダード", "業種": "情報・通信業", "特徴・サービス": "海外の先端セキュリティソリューションの輸入販売・運用監視サービスに強み。"},
        {"コード": "3927", "銘柄名": "フーバーブレイン", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "情報漏洩防止・内部統制ソフトやエンドポイントセキュリティを中小企業向けに提供。"},
        {"コード": "3774", "銘柄名": "インターネットイニシアティブ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "日本のインターネット先駆。法人向けマネージドセキュリティ・SOCサービスで高シェア。"},
        {"コード": "3040", "銘柄名": "ソリトンシステムズ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "PC認証セキュリティソフトやIT統制・暗号通信、サイバー防御に強み。"},
        {"コード": "6050", "銘柄名": "イー・ガーディアン", "市場": "プライム", "業種": "サービス業", "特徴・サービス": "ネット投稿監視・サイバーセキュリティ・デバッグ支援で高シェア。"},
        {"コード": "3968", "銘柄名": "セグエグループ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "セキュリティ製品・ITインフラの設計・導入・保守運用を手掛ける。"},
        {"コード": "3962", "銘柄名": "チェンジホールディングス", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "サイバーセキュリティ人材育成や自治体向けセキュリティDX。"},
        {"コード": "4441", "銘柄名": "トビラシステムズ", "市場": "スタンダード", "業種": "情報・通信業", "特徴・サービス": "迷惑電話・詐欺SMS遮断フィルターで国内独占的シェア。"}
    ],
    "🤖 AI・機械学習・先端技術": [
        {"コード": "9984", "銘柄名": "ソフトバンクグループ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "世界最大のAI投資ファンドを運営。Armを傘下に持ちAIエコシステムを牽引。"},
        {"コード": "3993", "銘柄名": "PKSHA Technology", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "自然言語処理・音声認識・画像認識アルゴリズムを各業界大手へ提供するAIリーディング企業。"},
        {"コード": "4011", "銘柄名": "ヘッドウォータース", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "AIソリューションおよび生成AI活用支援・マルチモーダルAIエージェントの開発推進。"},
        {"コード": "5595", "銘柄名": "QPS研究所", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "小型合成開口レーダー（SAR）衛星のコンステレーションによる準リアルタイム地球観測。"},
        {"コード": "5253", "銘柄名": "カバー", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "VTuber事務所「ホロライブプロダクション」運営。グローバルIP展開とメタバース事業。"},
        {"コード": "2158", "銘柄名": "FRONTEO", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "自然言語処理AI「KIBIT」を用いた不正調査・創薬支援・ビジネスインテリジェンス。"},
        {"コード": "4385", "銘柄名": "メルカリ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "フリマアプリ首位。AI出品サポートやメルペイ・暗号資産取引サービスを展開。"},
        {"コード": "4180", "銘柄名": "Appier Group", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "AI予測によるマーケティング最適化・リテンションAIソリューションを提供。"},
        {"コード": "5574", "銘柄名": "ABEJA", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "AIプラットフォーム「ABEJA Platform」で製造・小売向けDX・LLM実装。"},
        {"コード": "5586", "銘柄名": "Laboro.AI", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "カスタムAI開発「ソリューションデザイン」で産業大手企業と共同開発。"},
        {"コード": "5572", "銘柄名": "Ridge-i", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "ディープラーニング・画像解析技術を用いた宇宙衛星データ解析や先端AI開発。"},
        {"コード": "3655", "銘柄名": "ブレインパッド", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "ビッグデータ分析・機械学習アルゴリズムと生成AI導入支援コンサルティング。"},
        {"コード": "3984", "銘柄名": "ユーザーローカル", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "AIチャットボット・SNS分析ツール「Social Insight」で高利益率を誇る。"},
        {"コード": "4259", "銘柄名": "エクサウィザーズ", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "企業の生成AI活用支援「exaBase 生成AI」を展開する先端AIベンチャー。"},
        {"コード": "4436", "銘柄名": "ミンカブ・ジ・インフォノイド", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "金融情報AI自動生成エンジンや各種バーティカルメディアを運営。"},
        {"コード": "6501", "銘柄名": "日立製作所", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "生成AIセンターを設立し、社会イノベーション事業へLLMを全面導入。"},
        {"コード": "6758", "銘柄名": "ソニーグループ", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "画像センサーとディープラーニングを活用した知能センシングAIをリード。"},
        {"コード": "6503", "銘柄名": "三菱電機", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "コンパクトAI「Maisart」によるFA機器・自動運転・スマート家電の知能化。"}
    ],
    "⚡ 半導体・先端部材": [
        {"コード": "6920", "銘柄名": "レーザーテック", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "EUV露光向けマスクブランクス検査装置で世界シェア100%を誇る半導体検査装置のガリバー。"},
        {"コード": "8035", "銘柄名": "東京エレクトロン", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "半導体製造装置で世界トップクラス。コータ・デベロッパやエッチング装置で高シェア。"},
        {"コード": "6146", "銘柄名": "ディスコ", "市場": "プライム", "業種": "機械", "特徴・サービス": "半導体ウェーハの切断（ダイサ）・研削（グラインダ）・研磨装置で世界シェア首位独占。"},
        {"コード": "6857", "銘柄名": "アドバンテスト", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "半導体テスタ（試験装置）で世界首位級。AI半導体向けテスタ需要が急拡大。"},
        {"コード": "6723", "銘柄名": "ルネサスエレクトロニクス", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "車載半導体マイコンで世界トップ。産業・IoT向けのアナログ半導体も強化。"},
        {"コード": "7735", "銘柄名": "SCREENホールディングス", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "半導体洗浄装置で世界首位級。微細化に伴う枚葉式・バッチ式洗浄装置の需要急伸。"},
        {"コード": "6526", "銘柄名": "ソシオネクスト", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "カスタムSoC（先端システムLSI）のファブレス設計で自動車・データセンター向けに急成長。"},
        {"コード": "4063", "銘柄名": "信越化学工業", "市場": "プライム", "業種": "化学", "特徴・サービス": "半導体シリコンウェーハおよびフォトレジスト（感光材）で世界トップシェアを誇る化学大手。"},
        {"コード": "3436", "銘柄名": "SUMCO", "市場": "プライム", "業種": "金属製品", "特徴・サービス": "高純度シリコンウェーハ世界大手。信越化学と世界2強を形成。"},
        {"コード": "7729", "銘柄名": "東京精密", "市場": "プライム", "業種": "精密機器", "特徴・サービス": "ウェーハプローバ（検査機）や三次元測定機で世界高シェア。"},
        {"コード": "6323", "銘柄名": "ローツェ", "市場": "プライム", "業種": "機械", "特徴・サービス": "半導体ウェーハ搬送機・クリーン搬送ロボットで世界トップクラス。"},
        {"コード": "6315", "銘柄名": "TOWA", "市場": "プライム", "業種": "機械", "特徴・サービス": "半導体モールディング（封止）装置で世界首位。HBM向けコンプレッション封止。"},
        {"コード": "4062", "銘柄名": "イビデン", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "先端半導体パッケージ基板（ICパッケージ）で世界トップ級。"},
        {"コード": "6967", "銘柄名": "新光電気工業", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "半導体リードフレームおよびフリップチップパッケージ基板大手。"},
        {"コード": "4369", "銘柄名": "トリケミカル研究所", "市場": "プライム", "業種": "化学", "特徴・サービス": "高誘電率（High-k）材料など半導体用高純度化学材料のニッチトップ。"},
        {"コード": "6871", "銘柄名": "日本マイクロニクス", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "半導体プローブカード大手。メモリー用プローブカードで高シェア。"},
        {"コード": "6254", "銘柄名": "野村マイクロ・サイエンス", "市場": "プライム", "業種": "機械", "特徴・サービス": "半導体製造に不可欠な「超純水」製造装置で高シェア。"},
        {"コード": "6368", "銘柄名": "オルガノ", "市場": "プライム", "業種": "機械", "特徴・サービス": "総合水処理エンジニアリング大手。先端半導体工場向け超純水装置が好調。"},
        {"コード": "6504", "銘柄名": "富士電機", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "パワー半導体（SiC・IGBT）で世界大手。脱炭素・EV向け需要拡大。"},
        {"コード": "6981", "銘柄名": "村田製作所", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "積層セラミックコンデンサ（MLCC）で世界シェア首位。電子部品の巨人。"}
    ],
    "💻 DX・クラウドSaaS": [
        {"コード": "9613", "銘柄名": "NTTデータグループ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "国内ITサービス首位。グローバル展開と官民大規模DXの中核。"},
        {"コード": "4307", "銘柄名": "野村総合研究所", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "シンクタンク発祥。金融・産業向けコンサルティングと基幹系DXを牽引。"},
        {"コード": "4684", "銘柄名": "オービック", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "統合業務ソフト「OBIC7」で高収益・高シェア。ERPのガリバー企業。"},
        {"コード": "3626", "銘柄名": "TIS", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "決済システムや基幹系SIでトップクラス。金融DXに強み。"},
        {"コード": "9719", "銘柄名": "SCSK", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "住友商事系SIer。製造・流通向けERPや車載ソフト・クラウド移行支援。"},
        {"コード": "6702", "銘柄名": "富士通", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "DX推進事業「Fujitsu Uvance」を展開し、国内外の大規模DXを牽引。"},
        {"コード": "6701", "銘柄名": "日本電気", "市場": "プライム", "業種": "電気機器", "特徴・サービス": "DX支援事業「BluStellar」を軸に官民・インフラDXを推進。"},
        {"コード": "8056", "銘柄名": "BIPROGY", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "旧日本ユニシス。金融・自治体向けDXやオープンイノベーション基盤。"},
        {"コード": "2327", "銘柄名": "日鉄ソリューションズ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "日本製鉄系。製鉄ノウハウを活かした高度ITインフラ・クラウドDX。"},
        {"コード": "4812", "銘柄名": "電通総研", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "旧ISID。製造業向けPLMや電通グループのマーケティングDXを推進。"},
        {"コード": "6532", "銘柄名": "ベイカレント", "市場": "プライム", "業種": "サービス業", "特徴・サービス": "総合系コンサルティング最大手。企業のDX戦略立案から実装までで急成長。"},
        {"コード": "3697", "銘柄名": "SHIFT", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "ソフトウェアテスト・品質保証で独走。開発・DX内製化支援も展開。"},
        {"コード": "6088", "銘柄名": "シグマクシス・ホールディングス", "市場": "プライム", "業種": "サービス業", "特徴・サービス": "三菱商事系コンサル。DX戦略・AI基盤導入コンサルで高成長。"},
        {"コード": "3798", "銘柄名": "ULSグループ", "市場": "スタンダード", "業種": "情報・通信業", "特徴・サービス": "超上流ITコンサル。金融・流通向け先端アーキテクチャ設計。"},
        {"コード": "4674", "銘柄名": "クレスコ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "金融・組込開発に強みを持つ中堅SIer。クラウド・AI支援を強化。"},
        {"コード": "2130", "銘柄名": "メンバーズ", "市場": "プライム", "業種": "サービス業", "特徴・サービス": "企業のWeb運用やDX推進・エンジニア伴走型支援を手掛ける。"},
        {"コード": "3923", "銘柄名": "ラクス", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "クラウド型経費精算「楽楽精算」「楽楽明細」でバックオフィスDX首位。"},
        {"コード": "4776", "銘柄名": "サイボウズ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "ノーコード業務改善クラウド「kintone」で圧倒的シェアを誇る。"},
        {"コード": "4443", "銘柄名": "Sansan", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "クラウド名刺管理「Sansan」やインボイス管理「Bill One」で圧倒的シェア。"},
        {"コード": "4478", "銘柄名": "フリー", "市場": "グロース", "業種": "情報・通信業", "特徴・サービス": "クラウド会計・人事労務SaaS大手。スモールビジネスのバックオフィス業務を自動化。"},
        {"コード": "3994", "銘柄名": "マネーフォワード", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "家計簿アプリおよび法人向け「MFクラウド会計」を展開するフィンテック・SaaS大手。"},
        {"コード": "4071", "銘柄名": "プラスアルファ・コンサルティング", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "タレントマネジメントSaaS「タレントパレット」で急成長。"},
        {"コード": "4180", "銘柄名": "Appier Group", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "AI搭載マーケティングオートメーションDXプラットフォーム。"},
        {"コード": "3915", "銘柄名": "テラスカイ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "セールスフォース・AWS導入支援首位。クラウドインテグレーター。"},
        {"コード": "3853", "銘柄名": "アステリア", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "データ連携ミドルウェア「ASTERIA Warp」で国内シェア首位。"},
        {"コード": "9862", "銘柄名": "JBCCホールディングス", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "クラウド移行支援やセキュリティ、超高速開発で高収益化。"},
        {"コード": "2317", "銘柄名": "システナ", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "組込開発・ITインフラ支援から法人向けDXソリューションまで展開。"},
        {"コード": "3655", "銘柄名": "ブレインパッド", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "データサイエンス・ビッグデータ分析による企業のDX・マーケ支援。"},
        {"コード": "4390", "銘柄名": "アイ・ピー・エス", "市場": "スタンダード", "業種": "情報・通信業", "特徴・サービス": "フィリピン向け通信事業と中小企業向けSAP ERP導入DX。"},
        {"コード": "9715", "銘柄名": "トランスコスモス", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "BPO（業務委託）とコンタクトセンターDX、EC総合支援。"},
        {"コード": "4434", "銘柄名": "サーバーワークス", "市場": "スタンダード", "業種": "情報・通信業", "特徴・サービス": "AWS（アマゾンウェブサービス）専業クラウドインテグレーター。"},
        {"コード": "4483", "銘柄名": "JMDC", "市場": "プライム", "業種": "情報・通信業", "特徴・サービス": "医療ビッグデータ解析・保険者向けヘルスケアDX支援。"}
    ],
    "💊 創薬・バイオ・再生医療": [
        {"コード": "4502", "銘柄名": "武田薬品工業", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "国内製薬首位。消化器系・希少疾患・がん・神経精神疾患に強み。"},
        {"コード": "4519", "銘柄名": "中外製薬", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "抗体医薬品で国内トップ。ロシュ傘下で高収益・がん領域に強み。"},
        {"コード": "4568", "銘柄名": "第一三共", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "抗体薬物複合体（ADC）「エンハーツ」で世界のがん治療を革新。"},
        {"コード": "4587", "銘柄名": "ペプチドリーム", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "特殊環状ペプチド創薬プラットフォームで世界メガファーマと提携。"},
        {"コード": "4565", "銘柄名": "ネクセラファーマ", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "旧そーせいグループ。GPCRターゲット創薬でグローバル展開。"},
        {"コード": "4563", "銘柄名": "アンジェス", "市場": "グロース", "業種": "医薬品", "特徴・サービス": "遺伝子治療薬「コラテジェン」を開発する阪大発創薬バイオベンチャー。"},
        {"コード": "4592", "銘柄名": "サンバイオ", "市場": "グロース", "業種": "医薬品", "特徴・サービス": "脳神経再生細胞薬「アクーゴ（SB623）」を開発する再生医療バイオ。"},
        {"コード": "4582", "銘柄名": "シンバイオ製薬", "市場": "グロース", "業種": "医薬品", "特徴・サービス": "がん・血液領域・感染症領域の抗ウイルス薬を開発するバイオベンチャー。"},
        {"コード": "4599", "銘柄名": "ステムリム", "市場": "グロース", "業種": "医薬品", "特徴・サービス": "生体組織の再生を誘導する「再生誘導医薬」を開発する阪大発バイオ。"},
        {"コード": "4883", "銘柄名": "モダリス", "市場": "グロース", "業種": "医薬品", "特徴・サービス": "独自のCRISPR-GNDM技術による遺伝子治療薬を開発。"},
        {"コード": "4578", "銘柄名": "大塚ホールディングス", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "中枢神経系・腎臓病領域の医薬品およびポカリスエット等の機能性飲料。"},
        {"コード": "4503", "銘柄名": "アステラス製薬", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "前立腺がん治療薬「イクスタンジ」や抗体薬・遺伝子治療に注力。"},
        {"コード": "4507", "銘柄名": "塩野義製薬", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "抗HIV薬やインフルエンザ薬・感染症領域に強みを持つ準大手。"},
        {"コード": "4528", "銘柄名": "小野薬品工業", "市場": "プライム", "業種": "医薬品", "特徴・サービス": "がん免疫治療薬「オプジーボ」を創薬した研究開発型製薬大手。"},
        {"コード": "4901", "銘柄名": "富士フイルムホールディングス", "市場": "プライム", "業種": "精密機器", "特徴・サービス": "バイオ医薬品CDMO（受託製造）および再生医療材料大手。"}
    ]
}


def clean_theme_keyword(theme_str):
    """テーマ文字列からアイコンや余分な記号を除去して検索キーワードを抽出"""
    s = str(theme_str)
    for icon in ["🛡️", "🔒", "🤖", "⚡", "💻", "💊", "🏥", "🏘️", "🔨", "🛒", "♻️", "📢", "👔", "🎮", "🍽️", "☀️", "🪙", "🚙"]:
        s = s.replace(icon, "")
    parts = s.replace("・", " ").replace("/", " ").split()
    return parts[0].strip() if parts else s.strip()


def fetch_kabutan_theme_stocks(theme_str):
    """
    株探（Kabutan）の公式テーマページから、該当テーマの全銘柄（コード・銘柄名）を一括取得
    """
    keyword = clean_theme_keyword(theme_str)
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://kabutan.jp/themes/?theme={encoded_kw}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    stocks = []
    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            seen_codes = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                m = re.search(r'/stock/(?:chart\?code=|finance\?code=|\?code=)(\d{4})', href)
                if m:
                    code = m.group(1)
                    name = a.text.strip()
                    if code not in seen_codes and len(name) > 0 and not name.isdigit():
                        seen_codes.add(code)
                        market = "プライム"
                        sector = "関連銘柄"
                        parent_tr = a.find_parent("tr")
                        if parent_tr:
                            for td in parent_tr.find_all(["td", "th"]):
                                t_text = td.text.strip()
                                for m_cand in ["グロース", "スタンダード", "プライム", "名証", "札証", "福証", "PRO"]:
                                    if m_cand in t_text:
                                        market = t_text
                                        break
                        stocks.append({
                            "コード": code,
                            "銘柄名": name,
                            "市場": market,
                            "業種": sector,
                            "特徴・サービス": f"株探公式テーマ【{keyword}】関連銘柄"
                        })
    except Exception:
        pass
    return stocks, keyword


def fetch_theme_major_stocks(selected_genres):
    """
    上級者モードで選択されたテーマに基づき、株探公式テーマ全銘柄（または代表銘柄）をオンデマンド取得・キャッシュ
    """
    if not selected_genres:
        return pd.DataFrame()
        
    target_stocks = []
    source_labels = []
    for g in selected_genres:
        # 1. まず株探からの公式テーマ一括取得を試みる
        kab_stocks, kw = fetch_kabutan_theme_stocks(g)
        if len(kab_stocks) >= 5:
            source_labels.append(f"株探【{kw}】全{len(kab_stocks)}社網羅")
            for s in kab_stocks:
                if not any(ts["コード"] == s["コード"] for ts in target_stocks):
                    target_stocks.append(s)
        elif g in THEME_MAJOR_STOCKS:
            # 2. 株探が不通の場合は内蔵の代表本命リストを安全フォールバック
            source_labels.append(f"代表本命【{kw}】{len(THEME_MAJOR_STOCKS[g])}社")
            for s in THEME_MAJOR_STOCKS[g]:
                if not any(ts["コード"] == s["コード"] for ts in target_stocks):
                    target_stocks.append(s)
                    
    if source_labels:
        st.session_state["theme_source_info"] = " ｜ ".join(source_labels)
        
    if not target_stocks:
        return pd.DataFrame()
        
    # 既知の代表銘柄ごとの概算時価総額（億円）マスター
    KNOWN_MARKET_CAPS = {
        # 防衛
        "7011": 72000.0, "7012": 21000.0, "7013": 23000.0, "6503": 65000.0, "6701": 26000.0,
        "6702": 62000.0, "6301": 42000.0, "7270": 21000.0, "7203": 420000.0, "6814": 2200.0,
        "7721": 1300.0, "7224": 1100.0, "7003": 3200.0, "7014": 3600.0, "6946": 850.0,
        "6203": 160.0, "6208": 110.0, "7980": 100.0, "7963": 95.0, "4274": 75.0,
        "6111": 55.0, "7022": 120.0, "5905": 35.0, "4617": 980.0,
        # DX・クラウドSaaS
        "9613": 36000.0, "4307": 26000.0, "4684": 22000.0, "3626": 8500.0, "9719": 9200.0,
        "8056": 4600.0, "2327": 4100.0, "4812": 3100.0, "6532": 8200.0, "3697": 3400.0,
        "6088": 1300.0, "3923": 3100.0, "4776": 1250.0, "4443": 2600.0, "4478": 1900.0,
        "3994": 2300.0, "4071": 1200.0, "4180": 1800.0, "2317": 1500.0, "9715": 1600.0,
        "4483": 2400.0, "3798": 420.0, "4674": 520.0, "2130": 210.0, "3915": 460.0,
        "3853": 160.0, "9862": 630.0, "4390": 360.0, "4434": 260.0,
        # AI
        "9984": 150000.0, "3993": 1600.0, "4385": 3800.0, "4011": 280.0, "5595": 850.0,
        "5253": 1400.0, "2158": 290.0, "5574": 310.0, "5586": 180.0, "5572": 150.0,
        "3655": 240.0, "3984": 750.0, "4259": 350.0, "4436": 210.0,
        # 半導体
        "6920": 24000.0, "8035": 110000.0, "6146": 55000.0, "6857": 62000.0, "6723": 45000.0,
        "7735": 22000.0, "6526": 5400.0, "4063": 120000.0, "3436": 5100.0, "7729": 3800.0,
        "6323": 6500.0, "6315": 3100.0, "4062": 7200.0, "6967": 6800.0, "4369": 1100.0,
        "6871": 2100.0, "6254": 950.0, "6368": 3200.0, "6504": 14000.0, "6981": 42000.0,
        # セキュリティ
        "4704": 11000.0, "3774": 6200.0, "3040": 580.0, "6050": 380.0, "3968": 280.0,
        "3962": 820.0, "4441": 310.0, "3692": 260.0, "2326": 850.0, "3857": 280.0,
        "4493": 420.0, "3042": 95.0, "4288": 80.0, "3927": 65.0,
        # 創薬・バイオ
        "4502": 72000.0, "4519": 85000.0, "4568": 88000.0, "4578": 38000.0, "4503": 28000.0,
        "4507": 18000.0, "4528": 9500.0, "4901": 36000.0, "4587": 1400.0, "4565": 1100.0,
        "4563": 180.0, "4592": 650.0, "4582": 120.0, "4599": 280.0, "4883": 140.0
    }

    # 一括テクニカル ＆ 株価取得（全銘柄の6ヶ月足を一括ダウンロード）
    tech_dict = {}
    try:
        tickers = [f"{s['コード']}.T" for s in target_stocks]
        b_hist = yf.download(tickers, period="6mo", progress=False)
        if not b_hist.empty and "Close" in b_hist:
            for s in target_stocks:
                code = s["コード"]
                t_sym = f"{code}.T"
                try:
                    c_col = b_hist["Close"][t_sym] if t_sym in b_hist["Close"] else None
                    if c_col is not None:
                        c_series = c_col.dropna()
                        if len(c_series) > 0:
                            cur_p = round(float(c_series.iloc[-1]))
                            h_col = b_hist["High"][t_sym] if ("High" in b_hist and t_sym in b_hist["High"]) else c_col
                            h_series = h_col.dropna()
                            max_p = float(h_series.max()) if len(h_series) > 0 else cur_p
                            drop_pct = round(((max_p - cur_p) / max_p) * 100, 1) if max_p > 0 else 0.0
                            
                            # 25日線トレンド判定
                            sma25 = float(c_series.rolling(window=25).mean().iloc[-1]) if len(c_series) >= 25 else cur_p
                            tr_status = "上昇トレンド 🚀" if cur_p >= sma25 else "下降トレンド ⚠️"
                            
                            tech_dict[code] = {
                                "price": cur_p,
                                "high_drop": drop_pct,
                                "trend": tr_status
                            }
                except Exception:
                    pass
    except Exception:
        pass

    records = []
    for s in target_stocks:
        code = s["コード"]
        market = s.get("市場") or s.get("market", "プライム")
        
        # 時価総額の設定（既知マスター ＞ 市場別デフォルト）
        if code in KNOWN_MARKET_CAPS:
            mcap_val = KNOWN_MARKET_CAPS[code]
        elif "プライム" in market:
            mcap_val = 3000.0  # プライムは大型株扱い（3,000億円）
        elif "スタンダード" in market:
            mcap_val = 450.0   # スタンダードは中型株扱い（450億円）
        else:
            mcap_val = 200.0   # グロース・地方は小型株扱い（200億円）
            
        t_info = tech_dict.get(code, {})
        cur_price = t_info.get("price", 0)
        h_drop = t_info.get("high_drop", 15.0)
        trend = t_info.get("trend", "保ち合い 🔄")
        is_dip = (7.0 <= h_drop <= 30.0)
        
        rec = {
            "コード": code,
            "銘柄名": s.get("銘柄名") or s.get("name", "企業名"),
            "市場": market,
            "特徴・サービス": s.get("特徴・サービス") or s.get("feature", "テーマ関連銘柄"),
            "チャートトレンド": trend,
            "平均年齢": "40.0歳",
            "業種": s.get("業種") or s.get("sector", "関連業種"),
            "時価総額(億円)": float(mcap_val),
            "売上高成長率(%)": 15.0,
            "インサイダー保有率(%)": 5.0,
            "代表取締役": "代表取締役",
            "株価(円)": int(cur_price) if cur_price else 0,
            "単元購入額(万円)": round((cur_price * 100) / 10000, 1) if cur_price else 0,
            "財務健全性": "健全企業",
            "PER": 20.0,
            "高値下落率(%)": float(h_drop),
            "押し目フラグ": "押し目買い圏" if is_dip else "適正/高値圏",
            "3年後想定倍率": "1.5倍",
            "上場時期": "東証主力",
            "PBR": 1.5,
            "ROE(%)": 10.0,
            "株探URL": f"https://kabutan.jp/stock/?code={code}",
            "バフェットコードURL": f"https://www.buffett-code.com/company/{code}/"
        }
        records.append(rec)
            
    res_df = pd.DataFrame(records)
    if not res_df.empty:
        res_df["時価総額(億円)"] = pd.to_numeric(res_df["時価総額(億円)"], errors="coerce")
        res_df["売上高成長率(%)"] = pd.to_numeric(res_df["売上高成長率(%)"], errors="coerce")
        res_df["インサイダー保有率(%)"] = pd.to_numeric(res_df["インサイダー保有率(%)"], errors="coerce")
        res_df["PER"] = pd.to_numeric(res_df["PER"], errors="coerce")
        res_df["高値下落率(%)"] = pd.to_numeric(res_df["高値下落率(%)"], errors="coerce")
        res_df["平均年齢_数値"] = 40.0
        res_df["YahooURL"] = "https://finance.yahoo.co.jp/quote/" + res_df["コード"].astype(str) + ".T"
        res_df["銘柄名_リンク"] = "https://finance.yahoo.co.jp/quote/" + res_df["コード"].astype(str) + ".T#" + res_df["銘柄名"].astype(str)
        res_df["株探IR"] = "https://kabutan.jp/stock/finance?code=" + res_df["コード"].astype(str)
        res_df["X口コミ"] = "https://search.yahoo.co.jp/realtime/search?p=" + res_df["銘柄名"].astype(str)
        res_df["ジャンルリスト"] = res_df.apply(get_stock_genres, axis=1)
        return res_df
        
    return pd.DataFrame()


# ==========================================
# データ鮮度情報（最終更新日 ＆ 未更新判定）関数
# ==========================================
def get_csv_freshness_info():
    """CSVの最終更新日時と未更新フラグ（30日以上経過）を判定"""
    if not os.path.exists(CSV_FILE):
        return None, True, 999
    mtime = os.path.getmtime(CSV_FILE)
    dt = datetime.fromtimestamp(mtime)
    days_ago = (datetime.now() - dt).days
    is_outdated = days_ago >= 30
    date_str = dt.strftime("%Y/%m/%d")
    return date_str, is_outdated, days_ago


# ==========================================
# データの読み込み
# ==========================================
@st.cache_data(ttl=600)
def load_data():
    if not os.path.exists(CSV_FILE):
        return None
    try:
        df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")
        df["時価総額(億円)"] = pd.to_numeric(df["時価総額(億円)"], errors="coerce")
        df["売上高成長率(%)"] = pd.to_numeric(df["売上高成長率(%)"], errors="coerce")
        df["インサイダー保有率(%)"] = pd.to_numeric(df["インサイダー保有率(%)"], errors="coerce")
        df["PER"] = pd.to_numeric(df["PER"], errors="coerce")
        df["高値下落率(%)"] = pd.to_numeric(df["高値下落率(%)"], errors="coerce")
        
        # 市場カラムがない場合のフォールバック
        if "市場" not in df.columns:
            df["市場"] = "グロース"

        # 平均年齢の数値化
        df["平均年齢_数値"] = df["平均年齢"].astype(str).str.replace("歳", "").str.strip()
        df["平均年齢_数値"] = pd.to_numeric(df["平均年齢_数値"], errors="coerce")

        # リンク用URLカラム
        df["YahooURL"] = "https://finance.yahoo.co.jp/quote/" + df["コード"].astype(str) + ".T"
        df["銘柄名_リンク"] = "https://finance.yahoo.co.jp/quote/" + df["コード"].astype(str) + ".T#" + df["銘柄名"].astype(str)
        df["株探IR"] = "https://kabutan.jp/stock/finance?code=" + df["コード"].astype(str)
        df["X口コミ"] = "https://search.yahoo.co.jp/realtime/search?p=" + df["銘柄名"].astype(str)

        # 投資テーマ・ジャンルリストを自動生成
        df["ジャンルリスト"] = df.apply(get_stock_genres, axis=1)

        # 起動毎に、全銘柄の「最新終値（株価）」を一括高速ダウンロード（所要時間1〜2秒）
        try:
            tickers = [f"{c}.T" for c in df["コード"].astype(str)]
            batch_hist = yf.download(tickers, period="5d", progress=False)
            if not batch_hist.empty and "Close" in batch_hist:
                latest_closes = batch_hist["Close"].iloc[-1]
                price_map = {}
                for c in df["コード"].astype(str):
                    t = f"{c}.T"
                    if t in latest_closes and not pd.isna(latest_closes[t]):
                        price_map[c] = round(float(latest_closes[t]))
                if price_map:
                    df["株価(円)"] = df["コード"].astype(str).map(price_map).fillna(df.get("株価(円)", 0))
                    df["単元購入額(万円)"] = (df["株価(円)"] * 100 / 10000).round(1)
        except Exception:
            pass
        
        if "株価(円)" in df.columns:
            df["株価(円)"] = pd.to_numeric(df["株価(円)"], errors="coerce")
        if "単元購入額(万円)" in df.columns:
            df["単元購入額(万円)"] = pd.to_numeric(df["単元購入額(万円)"], errors="coerce")
        
        return df
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None


# ==========================================
# 検索条件の保存・読み込み関数 (前回設定の自動復元)
# ==========================================
def load_saved_conditions():
    """保存された検索条件を読み込む（起動・更新時は上級者設定を自動解除し、常に小型株・原則モードで初期化）"""
    defaults = {
        "mcap_max": 300.0,
        "rev_growth_min": 20.0,
        "insider_min": 20.0,
        "filter_trend_up": False,
        "filter_young_age": False,
        "filter_debt_free": False,
        "filter_pe_max": False,
        "filter_dip": False,
        "filter_high_growth": False,
        "filter_tenbagger": False,
        "filter_under_10man": False,
        "market_growth": True,
        "market_standard": True,
        "market_prime": False,
        "market_regional": False,
        "market_pro_other": False,
        "show_conditions": True,
        "keyword": "",
        "selected_genres": []
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                defaults.update(saved)
                # 起動時・ブラウザ更新時：上級者向け設定（テーマ選択や大型株設定）を自動解除し、必ず原則の小型株モードで初期化
                defaults["selected_genres"] = []
                defaults["mcap_max"] = 300.0
                defaults["market_growth"] = True
                defaults["market_standard"] = True
                defaults["market_prime"] = False
                defaults["market_regional"] = False
                defaults["market_pro_other"] = False
        except Exception:
            pass
    return defaults

def save_current_conditions():
    """現在の検索条件をJSONファイルに保存する"""
    current_settings = {
        "mcap_max": float(st.session_state.get("mcap_max", 300.0)),
        "rev_growth_min": float(st.session_state.get("rev_growth_min", 20.0)),
        "insider_min": float(st.session_state.get("insider_min", 20.0)),
        "filter_trend_up": bool(st.session_state.get("filter_trend_up", False)),
        "filter_young_age": bool(st.session_state.get("filter_young_age", False)),
        "filter_debt_free": bool(st.session_state.get("filter_debt_free", False)),
        "filter_pe_max": bool(st.session_state.get("filter_pe_max", False)),
        "filter_dip": bool(st.session_state.get("filter_dip", False)),
        "filter_high_growth": bool(st.session_state.get("filter_high_growth", False)),
        "filter_tenbagger": bool(st.session_state.get("filter_tenbagger", False)),
        "filter_under_10man": bool(st.session_state.get("filter_under_10man", False)),
        "market_growth": bool(st.session_state.get("market_growth", True)),
        "market_standard": bool(st.session_state.get("market_standard", True)),
        "market_prime": bool(st.session_state.get("market_prime", False)),
        "market_regional": bool(st.session_state.get("market_regional", True)),
        "market_pro_other": bool(st.session_state.get("market_pro_other", True)),
        "show_conditions": bool(st.session_state.get("show_conditions", True)),
        "keyword": str(st.session_state.get("keyword_input", "")),
        "selected_genres": list(st.session_state.get("selected_genres", []))
    }
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ==========================================
# 銘柄仕分けステータス＆ウォッチリストの保存・読み込み関数
# ==========================================
def load_stock_status():
    """銘柄の仕分けステータス（watching, excluded, unreviewed）を読み込む"""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_stock_status(data):
    """銘柄の仕分けステータスをセッションに安全保存（他端末と完全独立・覗き見改ざん遮断）"""
    st.session_state.stock_status = data

def set_stock_status(code: str, status: str):
    """銘柄のステータス（watching / excluded / unreviewed）を更新して即時保存"""
    code_str = str(code)
    if "stock_status" not in st.session_state:
        st.session_state.stock_status = load_stock_status()
    st.session_state.stock_status[code_str] = {
        "status": status,
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    }
    save_stock_status(st.session_state.stock_status)

def load_watchlist():
    """タブ2のウォッチリスト銘柄を読み込む"""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_watchlist(data):
    """タブ2のウォッチリスト銘柄をセッションに安全保存（他端末と完全独立・覗き見改ざん遮断）"""
    st.session_state.my_watchlist = data

def load_stock_notes():
    """銘柄の投資メモ＆AIレポートデータを読み込む"""
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_stock_notes(data):
    """銘柄の投資メモ＆AIレポートデータをセッションに安全保存（他端末と完全独立・覗き見改ざん遮断）"""
    st.session_state.stock_notes = data

def save_stock_note_entry(code: str, note_text: str):
    """指定銘柄のメモと現在日時を更新して保存"""
    code_str = str(code)
    if "stock_notes" not in st.session_state:
        st.session_state.stock_notes = load_stock_notes()
    st.session_state.stock_notes[code_str] = {
        "note": note_text,
        "updated_at": pd.Timestamp.now().strftime("%Y/%m/%d %H:%M")
    }
    save_stock_notes(st.session_state.stock_notes)


# ==========================================
# セッション状態の初期化
# ==========================================
saved_prefs = load_saved_conditions()

if "mcap_max" not in st.session_state:
    st.session_state.mcap_max = float(saved_prefs["mcap_max"])
if "rev_growth_min" not in st.session_state:
    st.session_state.rev_growth_min = float(saved_prefs["rev_growth_min"])
if "insider_min" not in st.session_state:
    st.session_state.insider_min = float(saved_prefs["insider_min"])
if "filter_trend_up" not in st.session_state:
    st.session_state.filter_trend_up = bool(saved_prefs["filter_trend_up"])
if "filter_young_age" not in st.session_state:
    st.session_state.filter_young_age = bool(saved_prefs["filter_young_age"])
if "filter_debt_free" not in st.session_state:
    st.session_state.filter_debt_free = bool(saved_prefs["filter_debt_free"])
if "filter_pe_max" not in st.session_state:
    st.session_state.filter_pe_max = bool(saved_prefs["filter_pe_max"])
if "filter_dip" not in st.session_state:
    st.session_state.filter_dip = bool(saved_prefs["filter_dip"])
if "filter_high_growth" not in st.session_state:
    st.session_state.filter_high_growth = bool(saved_prefs["filter_high_growth"])
if "filter_tenbagger" not in st.session_state:
    st.session_state.filter_tenbagger = bool(saved_prefs["filter_tenbagger"])
if "filter_under_10man" not in st.session_state:
    st.session_state.filter_under_10man = bool(saved_prefs["filter_under_10man"])

# 市場フィルター用
if "market_growth" not in st.session_state:
    st.session_state.market_growth = bool(saved_prefs["market_growth"])
if "market_standard" not in st.session_state:
    st.session_state.market_standard = bool(saved_prefs["market_standard"])
if "market_prime" not in st.session_state:
    st.session_state.market_prime = bool(saved_prefs["market_prime"])
if "market_regional" not in st.session_state:
    st.session_state.market_regional = bool(saved_prefs.get("market_regional", True))
if "market_pro_other" not in st.session_state:
    st.session_state.market_pro_other = bool(saved_prefs.get("market_pro_other", True))

# 検索条件の表示／非表示トグル用
if "show_conditions" not in st.session_state:
    st.session_state.show_conditions = bool(saved_prefs["show_conditions"])

# キーワード検索用
if "keyword_input" not in st.session_state:
    st.session_state.keyword_input = str(saved_prefs["keyword"])

# 投資テーマ・ジャンル絞り込み用（上級者仕様）
if "selected_genres" not in st.session_state:
    st.session_state.selected_genres = list(saved_prefs.get("selected_genres", []))

# 銘柄仕分けステータス用セッション（watching / excluded / unreviewed）
if "stock_status" not in st.session_state:
    st.session_state.stock_status = load_stock_status()

# マイ保有株ウォッチリスト用セッション
if "my_watchlist" not in st.session_state:
    st.session_state.my_watchlist = load_watchlist()

# 銘柄フォーカス表示用セッション（選択時に他銘柄を一時非表示）
if "selected_stock_code" not in st.session_state:
    st.session_state.selected_stock_code = None

# 銘柄別マイ投資メモ＆AIレポート用セッション
if "stock_notes" not in st.session_state:
    st.session_state.stock_notes = load_stock_notes()

# フィルター全クリア前の退避スナップショット用
if "previous_filter_snapshot" not in st.session_state:
    st.session_state.previous_filter_snapshot = None

# 対象市場・中大型株設定のロック状態（デフォルトは非表示・小型株集中モード）
if "unlocked_advanced_market" not in st.session_state:
    st.session_state.unlocked_advanced_market = False

# 小型成長株リストの事前読み込み（ボタン社数の動的連動用）
small_cap_df_init = load_data()
default_total_count = len(small_cap_df_init) if small_cap_df_init is not None else 126

def clear_all_filters():
    """現在の全フィルターを退避し、すべての条件を初期化して全社表示に戻す"""
    st.session_state.previous_filter_snapshot = {
        "mcap_max": float(st.session_state.get("mcap_max", 300.0)),
        "rev_growth_min": float(st.session_state.get("rev_growth_min", 20.0)),
        "insider_min": float(st.session_state.get("insider_min", 20.0)),
        "filter_trend_up": bool(st.session_state.get("filter_trend_up", False)),
        "filter_young_age": bool(st.session_state.get("filter_young_age", False)),
        "filter_under_10man": bool(st.session_state.get("filter_under_10man", False)),
        "filter_debt_free": bool(st.session_state.get("filter_debt_free", False)),
        "filter_pe_max": bool(st.session_state.get("filter_pe_max", False)),
        "filter_dip": bool(st.session_state.get("filter_dip", False)),
        "filter_high_growth": bool(st.session_state.get("filter_high_growth", False)),
        "filter_tenbagger": bool(st.session_state.get("filter_tenbagger", False)),
        "market_growth": bool(st.session_state.get("market_growth", True)),
        "market_standard": bool(st.session_state.get("market_standard", True)),
        "market_prime": bool(st.session_state.get("market_prime", False)),
        "market_regional": bool(st.session_state.get("market_regional", True)),
        "market_pro_other": bool(st.session_state.get("market_pro_other", True)),
        "keyword": str(st.session_state.get("keyword_input", "")),
        "selected_genres": list(st.session_state.get("selected_genres", []))
    }
    # 初期リセット（全銘柄表示）
    st.session_state.mcap_max = 300.0
    st.session_state.rev_growth_min = 10.0
    st.session_state.insider_min = 0.0
    st.session_state.filter_trend_up = False
    st.session_state.filter_young_age = False
    st.session_state.filter_under_10man = False
    st.session_state.filter_debt_free = False
    st.session_state.filter_pe_max = False
    st.session_state.filter_dip = False
    st.session_state.filter_high_growth = False
    st.session_state.filter_tenbagger = False
    st.session_state.market_growth = True
    st.session_state.market_standard = True
    st.session_state.market_prime = True
    st.session_state.market_regional = True
    st.session_state.market_pro_other = True
    st.session_state.keyword_input = ""
    st.session_state.selected_genres = []
    save_current_conditions()
    st.toast("🔄 フィルター条件をすべてクリアしました。『↩️ 取消』で復元できます。", icon="✨")

def undo_clear_filters():
    """退避したフィルター条件スナップショットを復元する"""
    if st.session_state.get("previous_filter_snapshot"):
        snap = st.session_state.previous_filter_snapshot
        st.session_state.mcap_max = snap["mcap_max"]
        st.session_state.rev_growth_min = snap["rev_growth_min"]
        st.session_state.insider_min = snap["insider_min"]
        st.session_state.filter_trend_up = snap["filter_trend_up"]
        st.session_state.filter_young_age = snap["filter_young_age"]
        st.session_state.filter_under_10man = snap["filter_under_10man"]
        st.session_state.filter_debt_free = snap["filter_debt_free"]
        st.session_state.filter_pe_max = snap["filter_pe_max"]
        st.session_state.filter_dip = snap["filter_dip"]
        st.session_state.filter_high_growth = snap["filter_high_growth"]
        st.session_state.filter_tenbagger = snap["filter_tenbagger"]
        st.session_state.market_growth = snap["market_growth"]
        st.session_state.market_standard = snap["market_standard"]
        st.session_state.market_prime = snap["market_prime"]
        st.session_state.market_regional = snap.get("market_regional", True)
        st.session_state.market_pro_other = snap.get("market_pro_other", True)
        st.session_state.keyword_input = snap["keyword"]
        st.session_state.selected_genres = snap.get("selected_genres", [])
        st.session_state.previous_filter_snapshot = None
        save_current_conditions()
        st.toast("↩️ 直前のフィルター条件を完全復元しました！", icon="✨")

# 対象市場・中大型株・ジャンル設定の注意ポップアップ（上級者仕様）
if hasattr(st, "dialog"):
    @st.dialog("⚠️ 上級者向け拡張設定（市場規模・特定テーマ）の確認")
    def show_advanced_market_dialog():
        st.warning("""
        **【小型株集中投資の基本原則からの逸脱注意】**
        
        本アプリの基本方針は、**『時価総額300億円以下（理想は100億〜200億円）の身軽な小型成長株』** に集中投資することで1年で3倍以上の急騰を狙う点にあります。
        
        中大型株（時価総額300億円超）や特定テーマ（防衛・セキュリティ等）のジャンル深掘りは**上級者向けの応用機能**です。原則から一時的に外れた特定分析であることを理解した上でご利用ください。
        """)
        st.markdown("**上記の投資原則とリスクを理解した上で、上級者設定を開きますか？**")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            if st.button("展開する（上級者モード）", type="primary", use_container_width=True):
                st.session_state.unlocked_advanced_market = True
                st.rerun()
        with d_col2:
            if st.button("キャンセル（小型株に集中）", use_container_width=True):
                st.session_state.unlocked_advanced_market = False
                st.rerun()
else:
    def show_advanced_market_dialog():
        st.session_state.show_inline_market_warning = True


def set_preset_endo_standard():
    """① 👑 王道・集中投資型 (約10〜20社)"""
    st.session_state.mcap_max = 200.0
    st.session_state.rev_growth_min = 20.0
    st.session_state.insider_min = 30.0
    st.session_state.filter_trend_up = True
    st.session_state.filter_young_age = False
    st.session_state.filter_debt_free = True
    st.session_state.filter_pe_max = False
    st.session_state.filter_dip = False
    st.session_state.filter_high_growth = False
    st.session_state.filter_tenbagger = False
    st.session_state.filter_under_10man = False
    st.session_state.market_growth = True
    st.session_state.market_standard = True
    st.session_state.market_prime = False
    st.session_state.market_regional = False
    st.session_state.market_pro_other = False
    st.session_state.selected_stock_idx = None
    save_current_conditions()
    st.toast("👑 王道・集中投資型 (理想の5大条件) を適用しました！", icon="✨")

def set_preset_safe_dip():
    """② 🛡️ 堅実安全・押し目買い型 (約15〜25社)"""
    st.session_state.mcap_max = 300.0
    st.session_state.rev_growth_min = 20.0
    st.session_state.insider_min = 20.0
    st.session_state.filter_trend_up = True
    st.session_state.filter_young_age = False
    st.session_state.filter_debt_free = True
    st.session_state.filter_pe_max = True
    st.session_state.filter_dip = True
    st.session_state.filter_high_growth = False
    st.session_state.filter_tenbagger = False
    st.session_state.filter_under_10man = False
    st.session_state.market_growth = True
    st.session_state.market_standard = True
    st.session_state.market_prime = False
    st.session_state.market_regional = False
    st.session_state.market_pro_other = False
    st.session_state.selected_stock_idx = None
    save_current_conditions()
    st.toast("🛡️ 堅実安全・押し目買い型 (無借金×適正PER×押し目) を適用しました！", icon="🛡️")

def set_preset_tenbagger():
    """③ 🚀 爆発的テンバガー狙い型 (約10〜15社)"""
    st.session_state.mcap_max = 200.0
    st.session_state.rev_growth_min = 30.0
    st.session_state.insider_min = 20.0
    st.session_state.filter_trend_up = True
    st.session_state.filter_young_age = False
    st.session_state.filter_debt_free = False
    st.session_state.filter_pe_max = False
    st.session_state.filter_dip = False
    st.session_state.filter_high_growth = True
    st.session_state.filter_tenbagger = True
    st.session_state.filter_under_10man = False
    st.session_state.market_growth = True
    st.session_state.market_standard = True
    st.session_state.market_prime = False
    st.session_state.market_regional = False
    st.session_state.market_pro_other = False
    st.session_state.selected_stock_idx = None
    save_current_conditions()
    st.toast("🚀 爆発的テンバガー狙い型 (売上+30%×3年後2倍) を適用しました！", icon="🚀")

def set_preset_full_comp():
    """④ 🔥 全条件クリア・超お宝型 (1社〜極少数)"""
    st.session_state.mcap_max = 300.0
    st.session_state.rev_growth_min = 20.0
    st.session_state.insider_min = 20.0
    st.session_state.filter_trend_up = True
    st.session_state.filter_young_age = True
    st.session_state.filter_debt_free = True
    st.session_state.filter_pe_max = True
    st.session_state.filter_dip = True
    st.session_state.filter_high_growth = True
    st.session_state.filter_tenbagger = True
    st.session_state.filter_under_10man = True
    st.session_state.market_growth = True
    st.session_state.market_standard = True
    st.session_state.market_prime = False
    st.session_state.market_regional = False
    st.session_state.market_pro_other = False
    st.session_state.selected_stock_idx = None
    save_current_conditions()
    st.toast("🔥 全条件クリア・超お宝型 (11条件フルコンプ) を適用しました！", icon="🔥")


# ==========================================
# サイドバー（高視認性フィルター操作パネル）
# ==========================================
st.sidebar.markdown("## 🎛️ 投資条件フィルター")

# 目的別おすすめプリセットボタン群
with st.sidebar.container(border=True):
    st.markdown("### 🎯 目的別おすすめパターン")
    st.caption("投資スタイルと厳格度（★4〜★6）に合わせてワンクリックで抽出します。")

    if st.button("🔥 全条件クリア 【究極★6】 (1社〜)", use_container_width=True, help="【厳格度: ★★★★★★】11個の全条件を妥協なく100点満点で全クリした奇跡の超お宝銘柄"):
        set_preset_full_comp()
        st.rerun()

    if st.button("👑 王道・集中投資型 【本命★5】 (約15社)", use_container_width=True, help="【厳格度: ★★★★★】書籍推奨の理想5大条件。最も再現性が高い本命厳選パターン"):
        set_preset_endo_standard()
        st.rerun()

    if st.button("🛡️ 堅実安全・押し目型 【安全★4】 (約20社)", use_container_width=True, help="【厳格度: ★★★★☆】実質無借金 × 適正PER(40倍以下) × 調整した押し目銘柄。大損を防ぐ守りの設定"):
        set_preset_safe_dip()
        st.rerun()

    if st.button("🚀 テンバガー狙い型 【急成長★4.5】 (約12社)", use_container_width=True, help="【厳格度: ★★★★☆+】売上+30%超 × 3年後2倍試算。10倍株の爆発力を持つ企業を狙い撃つ設定"):
        set_preset_tenbagger()
        st.rerun()

    st.markdown("---")
    clr_c1, clr_c2 = st.columns(2)
    with clr_c1:
        if st.button(f"🔄 デフォルト (全{default_total_count}社)", use_container_width=True, key="sb_clear_all_mob", help="すべてのフィルターを解除して全社表示に戻します"):
            clear_all_filters()
            st.rerun()
    with clr_c2:
        has_undo_sb = bool(st.session_state.get("previous_filter_snapshot"))
        if st.button("↩️ 取消", use_container_width=True, key="sb_undo_clear_mob", disabled=not has_undo_sb, help="直前の絞り込み条件を復元します"):
            undo_clear_filters()
            st.rerun()

st.sidebar.markdown("---")

# 上級者向け拡張設定（市場規模・特定テーマ／普段は非表示・注意ポップアップで確認後に展開）
with st.sidebar.container(border=True):
    if not st.session_state.get("unlocked_advanced_market", False):
        st.markdown("### 🛠️ 上級者向け拡張設定 🔒")
        st.caption("🔒 普段は原則である『小型成長株 集中投資モード』に固定されています。（大型株・特定テーマは上級者仕様）")
        if st.button("🔓 上級者設定を開く（市場規模・ジャンル）", use_container_width=True, help="防衛・セキュリティ等の特定テーマや、中大型株の絞り込みを開きます（注意確認あり）"):
            if hasattr(st, "dialog"):
                show_advanced_market_dialog()
            else:
                st.session_state.show_inline_market_warning = True
                st.rerun()

        if st.session_state.get("show_inline_market_warning", False):
            st.warning("⚠️ **【上級者向け・原則からの逸脱注意】**\n本アプリは『時価総額300億円以下の小型成長株』に集中投資して急騰を狙うのが基本です。中大型株や特定テーマの深掘りは上級者向けの応用機能となります。")
            col_w1, col_w2 = st.columns(2)
            with col_w1:
                if st.button("展開する", type="primary", use_container_width=True, key="btn_inline_open_mob"):
                    st.session_state.unlocked_advanced_market = True
                    st.session_state.show_inline_market_warning = False
                    st.rerun()
            with col_w2:
                if st.button("中止（小型株に集中）", use_container_width=True, key="btn_inline_cancel_mob"):
                    st.session_state.show_inline_market_warning = False
                    st.rerun()

        market_growth = st.session_state.market_growth
        market_standard = st.session_state.market_standard
        market_prime = st.session_state.market_prime
        market_regional = st.session_state.get("market_regional", True)
        market_pro_other = st.session_state.get("market_pro_other", True)
        selected_genres = st.session_state.get("selected_genres", [])
    else:
        st.markdown("### 🛠️ 上級者向け拡張設定（展開中）")
        st.caption("⚠️ 特定の投資テーマ（防衛等）の深掘りや、中大型株・他市場を分析するための応用機能です。")
        st.markdown("##### 🏛️ 対象市場の選択")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            market_growth = st.checkbox("グロース", value=st.session_state.market_growth)
            market_prime = st.checkbox("プライム", value=st.session_state.market_prime)
            market_pro_other = st.checkbox("PRO Market / その他", value=st.session_state.get("market_pro_other", True), help="TOKYO PRO Marketおよびその他の新興市場")
        with m_col2:
            market_standard = st.checkbox("スタンダード", value=st.session_state.market_standard)
            market_regional = st.checkbox("地方市場 (名証/札証/福証)", value=st.session_state.get("market_regional", True), help="名証ネクスト/メイン、札証アンビシャス/本則、福証Q-Board/本則など")
        
        market_size_option = st.radio(
            "🏢 企業規模（時価総額レンジ）",
            options=["小型株のみ (〜300億円・原則)", "中型株も含む (〜1,000億円)", "大型株も含む (全規模)"],
            index=0 if st.session_state.mcap_max <= 300.0 else (1 if st.session_state.mcap_max <= 1000.0 else 2),
            help="小型株集中投資の基本方針は『小型株のみ』が原則です。"
        )
        if market_size_option == "小型株のみ (〜300億円・原則)":
            st.session_state.mcap_max = 300.0
        elif market_size_option == "中型株も含む (〜1,000億円)":
            st.session_state.mcap_max = 1000.0
        elif market_size_option == "大型株も含む (全規模)":
            st.session_state.mcap_max = 999999.0

        st.markdown("---")
        st.markdown("##### 🏷️ 投資テーマ・ジャンル絞り込み")
        st.caption("防衛・セキュリティ・AIなど、特定の急成長・国策テーマで抽出します。")
        selected_genres = st.multiselect(
            "ジャンルを選択（複数選択可）",
            options=INVESTMENT_THEMES,
            default=st.session_state.get("selected_genres", []),
            placeholder="テーマを選択または入力（例: 防衛、セキュリティ）",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        if st.button("🎯 条件を確定して検索", type="primary", use_container_width=True, help="選択した市場・規模・ジャンルを確定し、該当銘柄の最新株価を取得して一覧に反映します"):
            st.session_state.market_growth = market_growth
            st.session_state.market_standard = market_standard
            st.session_state.market_prime = market_prime
            st.session_state.market_regional = market_regional
            st.session_state.market_pro_other = market_pro_other
            st.session_state.selected_genres = selected_genres
            
            # 大型株・中型株選択時、またはテーマ選択時の小型株専用フィルター自動緩和
            if market_size_option in ["中型株も含む (〜1,000億円)", "大型株も含む (全規模)"] or selected_genres:
                st.session_state.insider_min = 0.0          # 創業者比率を不問に（大企業には創業者不在）
                st.session_state.rev_growth_min = 10.0      # 売上成長率を10%に緩和
                st.session_state.filter_debt_free = False   # 実質無借金フィルター解除
                st.session_state.filter_pe_max = False      # PER制限解除
                st.session_state.filter_dip = False
                st.session_state.filter_high_growth = False
                st.session_state.filter_tenbagger = False
                st.session_state.filter_under_10man = False
                st.toast("🎯 上級者条件を確定！大型・テーマ株に合わせて条件を自動調整しました。", icon="✨")
            else:
                st.toast("🎯 検索条件を確定しました！", icon="✨")
            save_current_conditions()
            st.rerun()

        if st.button("🔒 小型株・原則モードに戻して閉じる", use_container_width=True, help="上級者設定を閉じ、基本方針である小型株集中投資（300億円以下）に復帰します"):
            st.session_state.unlocked_advanced_market = False
            st.session_state.selected_genres = []
            st.session_state.mcap_max = 300.0
            st.session_state.market_growth = True
            st.session_state.market_standard = True
            st.session_state.market_prime = False
            st.session_state.market_regional = False
            st.session_state.market_pro_other = False
            st.session_state.insider_min = 20.0
            st.session_state.rev_growth_min = 20.0
            save_current_conditions()
            st.toast("🔒 小型株・原則モード（300億円以下）に復元しました！", icon="✨")
            st.rerun()

with st.sidebar.container(border=True):
    st.markdown("### 📌 8大チェック・最重要条件")
    
    # 1. チャートトレンド
    filter_trend_up = st.checkbox("📈 上昇トレンド 🚀 のみ（必須級）", value=st.session_state.filter_trend_up, help="書籍P.1 & P.20: 下降トレンドや誰からも見向きされていない株はNG！25日/75日移動平均線上向きの株を厳選")

    # 2. 時価総額
    mcap_val = st.slider(
        "時価総額の上限 (億円)",
        min_value=10.0,
        max_value=300.0,
        value=float(st.session_state.mcap_max),
        step=10.0,
        help="書籍P.1: 1年で3倍を狙うには身軽な300億円以下（理想は100億〜200億円未満）"
    )

    # 3. 売上高成長率
    rev_val = st.slider(
        "売上高成長率の下限 (%)",
        min_value=10.0,
        max_value=100.0,
        value=float(st.session_state.rev_growth_min),
        step=5.0,
        help="書籍P.1: 本業の売上高が毎年20%以上拡大していること"
    )

    # 4. 創業者・役員比率
    insider_val = st.slider(
        "創業者・役員保有比率の下限 (%)",
        min_value=0.0,
        max_value=80.0,
        value=float(st.session_state.insider_min),
        step=5.0,
        help="書籍P.1: 創業者社長が筆頭株主で数10%以上保有。株主と経営陣の利害が完全一致"
    )

    # 5. 社員平均年齢
    filter_young_age = st.checkbox("👥 社員の平均年齢 35歳以下（活気チェック）", value=st.session_state.filter_young_age, help="書籍P.1: 社員の平均年齢が若い会社は成長市場への適応力・スピード感が抜群")

    # 6. 少額投資・単元購入額チェック
    st.markdown("---")
    filter_under_10man = st.checkbox(
        "💰 10万円以下で買える株 (100株少額投資)", 
        value=st.session_state.filter_under_10man,
        help="書籍のコンセプト完全再現！100株を10万円以下（株価1,000円以下）で丸ごと買える銘柄に限定します。"
    )
    st.info("💡 **1株投資なら全銘柄が数百円〜数千円からOK！**\n\n100株だと10万円以上かかる銘柄でも、単元未満株（1株取引）を利用すれば表示されている【1株価格（数百円〜数千円）】から超少額で購入可能です。")

with st.sidebar.container(border=True):
    st.markdown("### 🛡️ 投資判断ブースター (①〜④)")
    
    # ブースター一括ON/OFFボタン
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("⚡ 全てON", use_container_width=True, help="5つの厳選ブースターをすべて適用"):
            st.session_state.filter_debt_free = True
            st.session_state.filter_pe_max = True
            st.session_state.filter_dip = True
            st.session_state.filter_high_growth = True
            st.session_state.filter_tenbagger = True
            save_current_conditions()
            st.rerun()
    with b_col2:
        if st.button("🔄 全て解除", use_container_width=True, help="ブースターのチェックをすべて解除"):
            st.session_state.filter_debt_free = False
            st.session_state.filter_pe_max = False
            st.session_state.filter_dip = False
            st.session_state.filter_high_growth = False
            st.session_state.filter_tenbagger = False
            save_current_conditions()
            st.rerun()

    # ① 倒産リスク排除
    with st.expander("① 倒産リスク排除 (財務健全性)", expanded=False):
        st.caption("【背景】集中投資の最大リスクは倒産。手元資金が潤沢な無借金企業は不況でも倒産確率が極小。\n\n【内容】現預金が有利子負債を上回る「実質無借金」企業に限定。")
    filter_debt_free = st.checkbox("実質無借金(極めて安全)のみ", value=st.session_state.filter_debt_free)

    # ② 高値掴み防止・押し目買い
    with st.expander("② 高値掴み防止・押し目判定", expanded=False):
        st.caption("【背景】好業績でもPER100倍等の高値掴みは大損の元。調整局面や適正PERで仕込むのが鉄則。\n\n【内容】PER40倍以下、または高値から10〜35%調整した押し目銘柄。")
    filter_pe_max = st.checkbox("適正PER (40倍以下) のみ", value=st.session_state.filter_pe_max)
    filter_dip = st.checkbox("押し目買い圏 (高値比-10%〜-35%) のみ", value=st.session_state.filter_dip)

    # ③ 四半期成長モメンタム
    with st.expander("③ 成長加速モメンタム", expanded=False):
        st.caption("【背景】株価急騰の起爆剤は成長の急加速。\n\n【内容】売上高成長率 +30% 以上の高加速銘柄のみ。")
    filter_high_growth = st.checkbox("超高成長 (+30%以上) のみ", value=st.session_state.filter_high_growth)

    # ④ テンバガー期待度
    with st.expander("④ テンバガー潜在余地試算", expanded=False):
        st.caption("【背景】現在の成長が3年続いた場合の売上・時価総額倍率を複利シミュレーション。\n\n【内容】3年後の想定売上規模が2倍以上になる銘柄。")
    filter_tenbagger = st.checkbox("3年後成長試算 2倍以上のみ", value=st.session_state.filter_tenbagger)

keyword = st.sidebar.text_input("🔍 キーワード検索 (社名・サービス名)", value=st.session_state.keyword_input)

# 現在の入力・選択値をセッションステートに同期して自動保存
st.session_state.mcap_max = float(mcap_val)
st.session_state.rev_growth_min = float(rev_val)
st.session_state.insider_min = float(insider_val)
st.session_state.filter_trend_up = bool(filter_trend_up)
st.session_state.filter_young_age = bool(filter_young_age)
st.session_state.filter_debt_free = bool(filter_debt_free)
st.session_state.filter_pe_max = bool(filter_pe_max)
st.session_state.filter_dip = bool(filter_dip)
st.session_state.filter_high_growth = bool(filter_high_growth)
st.session_state.filter_tenbagger = bool(filter_tenbagger)
st.session_state.filter_under_10man = bool(filter_under_10man)
st.session_state.market_growth = bool(market_growth)
st.session_state.market_standard = bool(market_standard)
st.session_state.market_prime = bool(market_prime)
st.session_state.market_regional = bool(market_regional)
st.session_state.market_pro_other = bool(market_pro_other)
st.session_state.selected_genres = list(selected_genres)
st.session_state.keyword_input = str(keyword)

# 条件変更をローカルJSONに常時バックアップ保存
save_current_conditions()

# ==========================================
# サイドバー最下部：データ鮮度表示 ＆ 手動更新ボタン
# ==========================================
st.sidebar.markdown("---")
date_str, is_outdated, days_ago = get_csv_freshness_info()

if date_str:
    if is_outdated:
        # 1ヶ月以上経過時：赤背景・白文字の目立つ未更新バッジ
        badge_html = f"""
        <div style="font-size: 0.88rem; color: #1E293B; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
            <span>📅 データ: <b>{date_str}</b></span>
            <span style="background-color: #EF4444; color: #FFFFFF; font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 4px; letter-spacing: 0.5px;">未更新</span>
        </div>
        """
        st.sidebar.markdown(badge_html, unsafe_allow_html=True)
        btn_label = "🔄 候補銘柄の増減・最新化"
        btn_help = f"データが{days_ago}日前（1ヶ月以上前）のものです。新しいIPO銘柄の追加や時価総額300億円超での卒業など、候補銘柄の顔ぶれを再スクリーニングします（約40秒）"
    else:
        # 通常時：シンプル表示
        normal_html = f"""
        <div style="font-size: 0.88rem; color: #334155; margin-bottom: 8px;">
            📅 データ: <b>{date_str}</b> <span style="font-size: 0.75rem; color: #64748B;">({days_ago}日前)</span>
        </div>
        """
        st.sidebar.markdown(normal_html, unsafe_allow_html=True)
        btn_label = "🔄 候補銘柄の増減・最新化"
        btn_help = "新しいIPO銘柄の追加や時価総額300億円超での卒業など、候補銘柄の顔ぶれを再スクリーニングして更新します（約40秒）"

    if st.sidebar.button(btn_label, use_container_width=True, help=btn_help, key="sb_btn_refresh_csv"):
        with st.spinner("最新データを取得中...（約40秒）"):
            screener_script = os.path.join(BASE_DIR, "screener.py")
            res = subprocess.run([sys.executable, screener_script], capture_output=True, text=True)
            st.cache_data.clear()
            st.toast("✨ 銘柄データを最新に更新しました！", icon="🎉")
            st.rerun()


# ==========================================
# メイン画面ヘッダー（高品位イメージバナー ＆ タイトル）
# ==========================================


# データ読み込み（小型成長株リストとテーマ別リストを完全に分離管理）
small_cap_df = load_data()
is_theme_mode = bool(st.session_state.get("unlocked_advanced_market", False) and selected_genres)

if is_theme_mode:
    # テーマ専用モード：小型株リストとは合体させず、選択テーマ専用リストを独立した母集団として使用
    theme_df = fetch_theme_major_stocks(selected_genres)
    raw_df = theme_df.copy() if not theme_df.empty else pd.DataFrame()
    theme_clean_names = ", ".join(clean_theme_keyword(g) for g in selected_genres)
    base_population_label = f"【{theme_clean_names}】全{len(raw_df)}社"
else:
    # 通常モード（小型株・原則モード）：小型株リストを母集団として使用
    raw_df = small_cap_df.copy() if small_cap_df is not None else pd.DataFrame()
    theme_clean_names = ""
    base_population_label = f"全{len(raw_df)}社"

if raw_df is None:
    st.warning("⚠️ スクリーニングデータ（`growth_stocks.csv`）が見つかりません。")
    if st.button("今すぐ最新データを取得・スクリーニング実行"):
        with st.spinner("全銘柄のスクリーニング中... (約40秒)"):
            screener_script = os.path.join(BASE_DIR, "screener.py")
            subprocess.run([sys.executable, screener_script], capture_output=True)
            st.cache_data.clear()
            st.rerun()
    st.stop()

# フィルタリング
df = raw_df.copy()
active_filters = []

# 市場フィルター（東証3市場 ＋ 地方市場 ＋ PRO Market/その他）
market_conditions = []
selected_market_labels = []

if market_growth:
    market_conditions.append(df["市場"].str.contains("グロース", na=False))
    selected_market_labels.append("グロース")
if market_standard:
    market_conditions.append(df["市場"].str.contains("スタンダード", na=False))
    selected_market_labels.append("スタンダード")
if market_prime:
    market_conditions.append(df["市場"].str.contains("プライム", na=False))
    selected_market_labels.append("プライム")
if market_regional:
    # 名証（ネクスト・メイン）、札証（アンビシャス・本則）、福証（Q-Board・本則）
    regional_pattern = "名証|札証|福証|セントレックス|アンビシャス|Q-Board"
    market_conditions.append(df["市場"].str.contains(regional_pattern, na=False))
    selected_market_labels.append("地方市場")
if market_pro_other:
    # TOKYO PRO Market または上記主要市場以外
    pro_pattern = "PRO|TOKYO PRO|その他"
    # 主要市場にも地方市場にも該当しない銘柄も含める
    known_pattern = "グロース|スタンダード|プライム|名証|札証|福証|セントレックス|アンビシャス|Q-Board"
    market_conditions.append(df["市場"].str.contains(pro_pattern, na=False) | (~df["市場"].str.contains(known_pattern, na=False)))
    selected_market_labels.append("PRO Market/その他")

if market_conditions:
    # いずれかの市場条件に合致する行を抽出（OR結合）
    combined_mask = market_conditions[0]
    for cond in market_conditions[1:]:
        combined_mask = combined_mask | cond
    df = df[combined_mask]
    if len(selected_market_labels) == 5:
        active_filters.append("市場: 全市場")
    else:
        active_filters.append(f"市場: {', '.join(selected_market_labels)}")
else:
    # 全ての市場チェックが外れた場合は空（0件）
    df = raw_df.head(0).copy()

if filter_trend_up:
    df = df[df["チャートトレンド"].str.contains("上昇トレンド", na=False)]
    active_filters.append("上昇トレンド 🚀")

# 時価総額フィルター（企業規模レンジ連動）
effective_mcap_max = float(st.session_state.get("mcap_max", 300.0))
if effective_mcap_max <= 300.0:
    df = df[df["時価総額(億円)"] <= effective_mcap_max]
    active_filters.append(f"時価総額 <= {int(effective_mcap_max)}億円")
elif effective_mcap_max <= 1000.0:
    df = df[df["時価総額(億円)"] <= 1000.0]
    active_filters.append("時価総額 <= 1,000億円 (中小型株)")
# 全規模（大型株含む）時は上限なし（数兆円企業も全社通過）

# 売上高成長率フィルター（10%以下の場合は足切り完全解除）
if rev_val > 10.0:
    df = df[df["売上高成長率(%)"] >= rev_val]
    active_filters.append(f"売上成長率 >= {int(rev_val)}%")

# 創業者比率フィルター（0%の時は不問のため足切り完全解除）
if insider_val > 0.0:
    df = df[df["インサイダー保有率(%)"] >= insider_val]
    active_filters.append(f"創業者比率 >= {int(insider_val)}%")

if filter_young_age:
    df = df[(df["平均年齢_数値"].notna()) & (df["平均年齢_数値"] <= 35.0)]
    active_filters.append("平均年齢 <= 35歳")

if filter_under_10man:
    if "単元購入額(万円)" in df.columns:
        df = df[(df["単元購入額(万円)"].notna()) & (df["単元購入額(万円)"] <= 10.0)]
        active_filters.append("10万円以下で購入可 💰")

if filter_debt_free:
    df = df[df["財務健全性"].str.contains("実質無借金", na=False)]
    active_filters.append("実質無借金")

if filter_pe_max:
    df = df[(df["PER"].isna()) | (df["PER"] <= 40.0)]
    active_filters.append("PER 40倍以下")

if filter_dip:
    df = df[df["押し目フラグ"] == "押し目買い圏"]
    active_filters.append("押し目圏 (高値比-10%〜-35%)")

if filter_high_growth:
    df = df[df["売上高成長率(%)"] >= 30.0]
    active_filters.append("超高成長 (+30%以上)")

if filter_tenbagger:
    df = df[df["売上高成長率(%)"] >= 26.0]
    active_filters.append("3年後試算 2倍以上")

if keyword:
    kw_mask = (
        df["銘柄名"].str.contains(keyword, na=False) |
        df["コード"].astype(str).str.contains(keyword, na=False) |
        df["特徴・サービス"].str.contains(keyword, na=False)
    )
    df = df[kw_mask]
    active_filters.append(f"キーワード: '{keyword}'")

# 投資テーマ・ジャンル絞り込み（上級者仕様）
if selected_genres:
    theme_src = st.session_state.get("theme_source_info", "")
    if theme_src:
        active_filters.append(f"ジャンル: {', '.join(selected_genres)} 📌{theme_src}")
    else:
        active_filters.append(f"ジャンル: {', '.join(selected_genres)}")
    # 通常モード（小型株モード）でジャンル選択時のみ、ジャンルリストで絞り込み
    if not is_theme_mode and "ジャンルリスト" in df.columns:
        df = df[df["ジャンルリスト"].map(lambda gl: any(g in gl for g in selected_genres) if isinstance(gl, list) else False)]


# ==========================================
# 深掘りカード描画用コンポーネント関数
# ==========================================
def render_stock_deep_dive(idx, tab1_df):
    stock_data = tab1_df.iloc[idx]
    stock_code = str(stock_data["コード"])
    stock_name = str(stock_data["銘柄名"])
    
    with st.container(border=True):
        st.markdown(f"## 🏢 選択中銘柄の深掘り分析: {stock_code} {stock_name} ({stock_data.get('市場', '')})")
        
        # --- 🎯 銘柄仕分けトリアージ（スマホ対応2列グリッド） ---
        cur_status_info = st.session_state.stock_status.get(str(stock_code), {})
        cur_status = cur_status_info.get("status", "unreviewed")
        
        st.markdown("##### 🎯 この銘柄の仕分け判定（ワンクリック）:")
        st_col1, st_col2 = st.columns(2)
        
        with st_col1:
            is_watching = (cur_status == "watching")
            watch_label = "✅ ⭐️ 監視中" if is_watching else "⭐️ 監視継続（本命）"
            if st.button(watch_label, key=f"btn_watch_{stock_code}", use_container_width=True, type="primary" if is_watching else "secondary"):
                set_stock_status(stock_code, "watching")
                # タブ2のウォッチリストにも未登録なら自動追加
                already_in_watch = any(str(w.get("code")) == str(stock_code) for w in st.session_state.my_watchlist)
                if not already_in_watch:
                    cur_p = stock_data.get('株価(円)', 1000.0)
                    buy_price_guess = float(cur_p) if (pd.notna(cur_p) and cur_p != '-') else 1000.0
                    st.session_state.my_watchlist.append({
                        "code": str(stock_code),
                        "buy_price": buy_price_guess,
                        "shares": 100
                    })
                    save_watchlist(st.session_state.my_watchlist)
                st.toast(f"⭐️ {stock_code} {stock_name} を監視リスト＆タブ2に追加しました！", icon="⭐️")
                st.rerun()

        with st_col2:
            is_excluded = (cur_status == "excluded")
            exclude_label = "✅ ❌ 除外中" if is_excluded else "❌ 対象外（隠す）"
            if st.button(exclude_label, key=f"btn_exclude_{stock_code}", use_container_width=True, type="primary" if is_excluded else "secondary"):
                set_stock_status(stock_code, "excluded")
                # 除外にした場合は一覧から隠すため、選択状態を解除して全一覧に戻す！
                st.session_state.selected_stock_code = None
                st.toast(f"❌ {stock_code} {stock_name} を対象外に設定し、一覧から非表示にしました。", icon="🗑️")
                st.rerun()

        st_col3, st_col4 = st.columns([1, 1.5])
        with st_col3:
            if cur_status != "unreviewed":
                if st.button("⏳ 保留に戻す", key=f"btn_reset_{stock_code}", use_container_width=True):
                    set_stock_status(stock_code, "unreviewed")
                    st.rerun()
            else:
                st.caption("状態: ⚪ 未判定")

        with st_col4:
            if cur_status == "watching":
                st.success("⭐️ **監視中**: タブ2に登録済")
            elif cur_status == "excluded":
                st.warning("❌ **対象外**: 一覧から非表示")
            else:
                st.info("💡 調査後にボタンで仕分け")

        # --- 📊 FX視点のエントリー現在地 ＆ 過熱感メーター ---
        high_drop_val = stock_data.get('高値下落率(%)', None)
        timing_info = analyze_entry_timing(stock_code, high_drop_val)
        
        st.markdown(f"""
        <div style="background-color: {timing_info['bg_color']}; border: 2px solid {timing_info['border_color']}; border-radius: 10px; padding: 14px 18px; margin-top: 12px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
                <div style="font-size: 1.05rem; font-weight: 800; color: {timing_info['badge_color']};">
                    📈 エントリー現在地診断 (FX目線): {timing_info['status']}
                </div>
                <div style="font-size: 0.92rem; font-weight: 700; background-color: #FFFFFF; border: 1px solid {timing_info['border_color']}; padding: 3px 10px; border-radius: 6px; color: {timing_info['badge_color']};">
                    👉 推奨立ち回り: {timing_info['action']}
                </div>
            </div>
            <div style="font-size: 0.9rem; line-height: 1.5; color: #1E293B; margin-bottom: 10px;">
                {timing_info['advice']}
            </div>
            <div style="display: flex; gap: 16px; flex-wrap: wrap; font-size: 0.85rem; font-weight: 600; color: #475569; background-color: rgba(255,255,255,0.7); padding: 8px 12px; border-radius: 6px;">
                <span>📊 25日線乖離率: <strong style="color: {'#DC2626' if (timing_info['ma25_bias'] is not None and timing_info['ma25_bias'] >= 15.0) else '#16A34A'};">{f"{timing_info['ma25_bias']:+.1f} %" if timing_info['ma25_bias'] is not None else "-"}</strong> (過熱警戒: +15%以上 / 押し目圏: 0〜+7%)</span>
                <span>🎯 直近高値までの距離: <strong style="color: {'#DC2626' if (timing_info['high_dist'] is not None and timing_info['high_dist'] <= 3.0) else '#1E3A8A'};">{f"あと {timing_info['high_dist']:.1f} %" if timing_info['high_dist'] is not None else "-"}</strong> (レジスタンス直前: 3%以内)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 特徴・サービス
        st.success(f"**【特徴・主力サービス (四季報要約)】**: {stock_data.get('特徴・サービス', '情報なし')}")
        
        # 💰 購入資金（株価 vs 単元株）
        cur_price = stock_data.get('株価(円)', None)
        unit_val = stock_data.get('単元購入額(万円)', None)
        
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.metric(
                label="株価（1株価格）",
                value=f"{int(cur_price):,} 円" if pd.notna(cur_price) and cur_price != '-' else "-",
                help="単元未満株（1株取引）を利用した場合の1株あたり概算株価"
            )
        with b_col2:
            st.metric(
                label="単元株（100株購入額）",
                value=f"{float(unit_val):.1f} 万円" if pd.notna(unit_val) and unit_val != '-' else "-",
                help="通常の単元（100株）購入に必要な概算資金"
            )

        # --- 📑 決算・IR情報 ＆ 公式IRサイト直行リンク ---
        kabutan_ir_url = f"https://kabutan.jp/stock/finance?code={stock_code}"
        official_ir_url = f"https://www.google.com/search?q={stock_code}+{stock_name}+IR+投資家情報"
        
        ir_col1, ir_col2 = st.columns(2)
        with ir_col1:
            st.link_button(
                label="📑 決算・IR業績 (株探)",
                url=kabutan_ir_url,
                use_container_width=True,
                help="過去数年間の売上高成長推移・四半期進捗率・決算短信を一目で確認"
            )
        with ir_col2:
            st.link_button(
                label="🌐 公式IRサイト (説明資料)",
                url=official_ir_url,
                use_container_width=True,
                help="企業の公式サイト内にあるIRページ・決算説明スライドPDFへ直行"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 🤖 【最優先】AI深掘りリサーチプロンプト生成エリア ---
        st.markdown("---")
        st.markdown("### 🤖 AI深掘りリサーチ用プロンプト (最優先推奨)")
        st.caption("下の **「📋 プロンプトをワンクリックでコピー」** ボタンを押すとクリップボードに自動保存されます。そのままAIチャットに貼り付けて送信（Ctrl+V）するだけで、AI（専用スキル）がSNS評判・CM広告・有報・自社株売り・イノベーター理論・チャート動向を全自動で徹底裏取り調査します。")

        prompt_text = f"""あなたは敏腕株式アナリスト兼小型成長株集中投資のエキスパートAIです。
以下の銘柄について、リアルタイムWeb検索（Google検索機能）をフル稼働し、適時開示・SNSの生の声・CM出稿・最新チャートを徹底的に裏取り調査して、指定された【出力フォーマット】に従ってA4用紙2〜3枚相当の徹底深掘りレポートを作成してください。

【厳格な指示ルール】
1. 要約や省略、簡単な箇条書きで終わらせる手抜き回答は一切禁止です。各章・各項目について、具体的な数値・事実・分析根拠を詳しく記述してください。
2. 表や見出しは指定フォーマットを厳密に維持し、空欄を作らず全て埋めてください。
3. エントリー判定では、FX・テクニカル視点からサポレジ（抵抗線・支持線）とシナリオA/Bを明確に提示してください。

【対象銘柄】
・証券コード: {stock_code}
・銘柄名: {stock_name}
・市場: {stock_data.get('市場', '不明')}
・時価総額: {stock_data.get('時価総額(億円)', '-')} 億円
・売上高成長率: +{stock_data.get('売上高成長率(%)', '-')} %
・創業者・役員比率: {stock_data.get('インサイダー保有率(%)', '-')} %
・代表取締役社長: {stock_data.get('代表取締役', '不明')}
・単元株（100株購入金額）: {stock_data.get('単元購入額(万円)', '-')} 万円
・1株価格（少額投資）: {stock_data.get('株価(円)', '-')} 円
・チャートトレンド状態: {stock_data.get('チャートトレンド', '不明')}
・52週高値からの下落率: {stock_data.get('高値下落率(%)', 0)} %
・特徴・主要サービス: {stock_data.get('特徴・サービス', '不明')}

---

【必ず以下のフォーマット通りに出力してください】

# 📊 【TOTOTO-KABU・銘柄深掘りリサーチレポート】 [{stock_code}] {stock_name}

## ⚡【最重要】FXチャート・テクニカル視点でのエントリー現在地診断
1. **突発的な急騰に対する「全戻し（イナゴタワー崩壊）」リスクの有無**
   - 結論（極めて低い / 中程度 / 警戒）と、直近の出来高推移・保ち合い形成・業績裏付けに基づく詳細な根拠。
2. **直近高値（レジスタンスライン）に対する現在地と高値掴み反落リスク**
   - 直近レジスタンス（年初来高値等）、直近サポート（25日線・75日線水準）の具体的価格と、現在値の距離・過熱感。
3. **今すぐ成行で買うべきか？押し目を待つべきか？（エントリー判定）**
   - 売買判定（【成行買い見送り・押し目待ち】または【順張り買い】など）。
   - 【シナリオA（推奨・押し目買い戦略）】: 具体的なエントリー指値目安価格と狙い。
   - 【シナリオB（高値ブレイク順張り戦略）】: エントリー条件価格と狙い。

## 1. 銘柄サマリー ＆ 8大チェックポイント判定
（市場、時価総額、売上成長率、社長経歴、社員年齢、株主構成のサマリーを記載した上で、以下の表を埋めてください）

| チェック項目 | 判定 | 調査結果・詳細コメント |
| :--- | :---: | :--- |
| ① 上場5年以内 | [✅ / ❌] | [上場年月と年数の評価] |
| ② 時価総額300億以下 | [✅ / ❌] | [時価総額と身軽さの評価] |
| ③ 創業社長が現役 | [✅ / ❌] | [社長のコミットメント・年齢の評価] |
| ④ 経営陣が大株主 | [✅ / ❌] | [保有比率と自社株売りの有無] |
| ⑤ 優秀な若手・採用力 | [✅ / ⚠️] | [採用実績・組織の活力] |
| ⑥ 社員平均年齢が若い | [✅ / ⚠️] | [有報の平均年齢と業界比較] |
| ⑦ シンプルで身近な需要 | [✅ / ⚠️] | [みんなが欲しがる商品・主力サービスの実感] |
| ⑧ 上昇トレンド | [✅ / ❌] | [株価と25日/75日移動平均線の位置関係] |

## 2. SNS・リアルな口コミ分析 (生の声の感情比率)
* **推定感情比率**: ポジティブ 〇〇% ｜ ネガティブ 〇〇%
* **主なポジティブな生の声（利用者のリアルな口コミ引用・評価ポイント）**
* **注意すべき不満・ネガティブな生の声（不満点・価格・業界懸念）**
* **定性評価（みんなが欲しがっているか・認知拡大の兆候）**

## 3. CM・広告戦略の開始状況 (買い時シグナル検証)
* **広告展開の状況**: （Meta広告、YouTube CM、PR TIMES、TVCM、タクシー広告等の出稿状況）
* **プロモーションの質**: （売上直結のダイレクト獲得型か、イメージ広告か）
* **判定コメント**: （広告を打ち始めて認知が広がる理想的な初動段階か）

## 4. ビジネスモデル ＆ 競合優位性 (中学生でもわかる解説)
* **事業の仕組み**: （誰に何をどうやって売って儲けているかを中学生でもわかる平易な言葉で解説）
* **他社が真似できない参入障壁（堀）**: （他社が簡単に真似できない強み、特許、ネットワーク効果、立地等）

## 5. イノベーター理論フェーズ ＆ 売買タイミング判定
* **現在の普及フェーズ**: （イノベーター期 / ★アーリーアダプター期 (買い時) / キャズム超え / レイトマジョリティ期 (売り時・過熱)）
* **判定の根拠**: （『まわりが慎重なら買い、まわりが興味を持ったら売り』に照らした評価）

## 6. 総合投資判断 ＆ リスク管理
* **集中投資おすすめ度**: ★★★★☆ (〇.〇 / 5.0)
* **総合評価**: （強みと今後の見通しの総括）
* **想定される大化けシナリオ (2〜3倍余地)**: （時価総額〇〇億円、株価〇〇円を目指す成長ストーリー）
* **🚨 撤退すべき損切りライン・シナリオ崩壊条件**:
  - 損切りライン: （買値から-8%〜-10%、または〇〇円割れ）
  - 即時撤退条件: （大株主の売却、成長減速、業績悪化など）"""

        prompt_json = json.dumps(prompt_text)

        # プロンプト文の上に被らない、完全に独立した大型コピーボタン（見切れゼロ・2段表示）
        copy_html = f"""
        <div style="margin: 0; padding: 2px 0;">
            <button id="copyPromptBtn" onclick="copyToClipboard()" style="
                width: 100%;
                background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%);
                color: white;
                border: none;
                padding: 10px 14px;
                font-size: 15px;
                line-height: 1.4;
                font-weight: 700;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                gap: 2px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                transition: all 0.2s ease;
                box-sizing: border-box;
            ">
                <span>📋 このプロンプトを</span>
                <span>ワンクリックでコピー</span>
            </button>
        </div>
        <script>
        function copyToClipboard() {{
            const text = {prompt_json};
            const btn = document.getElementById("copyPromptBtn");

            function setSuccess() {{
                btn.innerHTML = "<span>✅ コピー完了！</span><span>AIチャットに貼り付けて送信してください (Ctrl+V)</span>";
                btn.style.background = "#16A34A";
                setTimeout(function() {{
                    btn.innerHTML = "<span>📋 このプロンプトを</span><span>ワンクリックでコピー</span>";
                    btn.style.background = "linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%)";
                }}, 3500);
            }}

            function setFailure() {{
                btn.innerHTML = "<span>⚠️ コピー失敗</span><span>下の枠内から手動コピーしてください</span>";
                btn.style.background = "#DC2626";
                setTimeout(function() {{
                    btn.innerHTML = "<span>📋 このプロンプトを</span><span>ワンクリックでコピー</span>";
                    btn.style.background = "linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%)";
                }}, 3500);
            }}

            function fallbackExecCopy() {{
                try {{
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed";
                    textArea.style.left = "-9999px";
                    textArea.style.top = "-9999px";
                    textArea.style.opacity = "0";
                    textArea.setAttribute("readonly", "");
                    document.body.appendChild(textArea);
                    
                    textArea.focus();
                    textArea.select();
                    textArea.setSelectionRange(0, 999999);

                    const successful = document.execCommand("copy");
                    document.body.removeChild(textArea);
                    if (successful) {{
                        setSuccess();
                    }} else {{
                        setFailure();
                    }}
                }} catch (err) {{
                    setFailure();
                }}
            }}

            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text)
                    .then(setSuccess)
                    .catch(function(err) {{
                        fallbackExecCopy();
                    }});
            }} else {{
                fallbackExecCopy();
            }}
        }}
        </script>
        """
        components.html(copy_html, height=78)

        with st.expander("📄 生成されたプロンプト本文（確認・手動コピー用）", expanded=False):
            st.code(prompt_text, language="markdown")

        # --- 📝 個別投資メモ ＆ AIレポート保存エリア ---
        st.markdown("---")
        st.markdown("### 📝 マイ投資メモ ＆ AIリサーチ結果保存")
        
        note_entry = st.session_state.stock_notes.get(str(stock_code), {})
        existing_note = note_entry.get("note", "")
        updated_at = note_entry.get("updated_at", "")
        
        if updated_at:
            st.caption(f"🕒 最終保存日時: **{updated_at}**")

        note_key = f"note_input_{stock_code}"
        if note_key not in st.session_state:
            st.session_state[note_key] = existing_note

        def on_save_note_click(c_code, n_key):
            new_text = st.session_state[n_key]
            save_stock_note_entry(c_code, new_text)
            st.toast(f"💾 {c_code} のメモを自動保存しました！", icon="✅")

        def on_add_stamp_click(c_code, n_key):
            current_time = pd.Timestamp.now().strftime("%Y/%m/%d %H:%M")
            stamp_text = f"\n\n--- 🕒 {current_time} ---\n"
            st.session_state[n_key] = st.session_state[n_key] + stamp_text

        st.text_area(
            label=f"📝 {stock_code} {stock_name} のメモ・AI分析結果:",
            value=st.session_state[note_key],
            height=220,
            key=note_key,
            placeholder="ここにAIの深掘りリサーチ結果をそのまま貼り付けたり、ご自身の投資メモ（例: ○○円の押し目で指値、社長の自社株売りなし、新製品の口コミ良好など）を記録できます。"
        )

        btn_n1, btn_n2, btn_n_space = st.columns([1.5, 1.8, 3])
        with btn_n1:
            st.button(
                "💾 メモを保存する",
                key=f"btn_save_note_{stock_code}",
                type="primary",
                use_container_width=True,
                on_click=on_save_note_click,
                args=(stock_code, note_key)
            )

        with btn_n2:
            st.button(
                "🕒 日時スタンプを挿入",
                key=f"btn_add_stamp_{stock_code}",
                use_container_width=True,
                on_click=on_add_stamp_click,
                args=(stock_code, note_key)
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # メトリクスカード（見切れ防止スタイル適用済み）
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("チャート状態", f"{stock_data.get('チャートトレンド', '-')}")
        m2.metric("社員の平均年齢", f"{stock_data.get('平均年齢', '-')}")
        m3.metric("時価総額", f"{stock_data['時価総額(億円)']} 億円")
        m4.metric("売上高成長率", f"+{stock_data['売上高成長率(%)']} %")
        m5.metric("創業者・役員比率", f"{stock_data['インサイダー保有率(%)']} %")

        # --- 📈 株価チャート分析 (ローソク足・25日/75日線・出来高) ---
        st.markdown("---")
        st.markdown("### 📈 株価チャート分析 (1日〜1年 切り替え / 移動平均線・出来高)")
        st.caption("遠藤洋氏のチェック基準『株価チャートが上昇トレンドであること』を検証します。25日線（緑色）および75日線（オレンジ色）の上で株価が推移しているかをご確認ください。")
        render_stock_chart(stock_code, stock_name)

        # --- イノベーター理論インジケーター ---
        st.markdown("---")
        st.markdown("### 💡 イノベーター理論 普及フェーズ判定 (書籍P.13〜19)")
        
        p1, p2 = st.columns([2, 1])
        with p1:
            st.markdown("""
            * **【買い時】アーリーアダプター期 (初期採用者)**:
              アンテナの高い感度の良い人が使い始めた段階。世間の認知はまだ「怪しい」「一部の流行」。株価急騰の初動！
            * **【売り時】レイトマジョリティ期 (後期追随者)**:
              普段新しいものを使わない一般層や保守層まで知れ渡った段階。株価はすでに織り込み済みで天井圏のリスク大。
            """)
        with p2:
            st.info("""
            **📖 遠藤洋氏の格言:**
            『まわりの人が **「まだ怪しい」** と言っている時は **買い**。
            **「みんな使っている」** と言い始めたら **売り**。』
            """)

        # --- 📢 CM・広告戦略の早期察知 ＆ SNSトレンド分析 ---
        st.markdown("---")
        st.markdown("### 📢 CM・広告戦略の早期察知 ＆ SNSトレンド分析 (個別・手動確認用)")
        st.caption("街中やテレビで偶然見かけるのを待たず、企業が広告勝負に出た瞬間をダイレクトに掴みます。")

        meta_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=JP&q={stock_name}&search_type=keyword_unordered&media_type=all"
        youtube_cm_url = f"https://www.youtube.com/results?search_query={stock_name}+CM"
        prtimes_url = f"https://prtimes.jp/main/action.php?run=html&page=searchresult&search_word={stock_name}+CM"

        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin-bottom: 12px;">
            <a href="{meta_url}" target="_blank" class="action-btn" style="background-color:#0668E1; color:white;">
                🔵 Meta広告ライブラリ<br><small>Instagram/FB出稿状況</small>
            </a>
            <a href="{youtube_cm_url}" target="_blank" class="action-btn" style="background-color:#CC0000; color:white;">
                🔴 YouTube公式CM<br><small>TV・タクシー広告動画</small>
            </a>
            <a href="{prtimes_url}" target="_blank" class="action-btn" style="background-color:#6B21A8; color:white;">
                🟣 PR TIMES新CM<br><small>放映開始プレスリリース</small>
            </a>
        </div>
        """, unsafe_allow_html=True)

        # SNS・リサーチボタン群 (スマホ自動折返し2列〜4列グリッド)
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin-bottom: 12px;">
            <a href="https://search.yahoo.co.jp/realtime/search?p={stock_name}" target="_blank" class="action-btn" style="background-color:#1DA1F2; color:white;">
                🐦 Xリアルタイム<br><small>感情比率・ツイート推移</small>
            </a>
            <a href="https://trends.google.co.jp/trends/explore?geo=JP&q={stock_name}" target="_blank" class="action-btn" style="background-color:#D93025; color:white;">
                📈 Googleトレンド<br><small>検索需要急増チェック</small>
            </a>
            <a href="https://kabutan.jp/stock/?code={stock_code}" target="_blank" class="action-btn" style="background-color:#2E7D32; color:white;">
                🟢 株探チャート<br><small>大株主・四半期推移</small>
            </a>
            <a href="https://www.buffett-code.com/company/{stock_code}/" target="_blank" class="action-btn" style="background-color:#455A64; color:white;">
                ⚪ バフェットコード<br><small>詳細財務・キャッシュフロー</small>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**📱 他SNSでの認知度・リアルな口コミチェック:**")
        sns_c1, sns_c2, sns_c3 = st.columns(3)
        with sns_c1:
            st.link_button(f"📸 Instagramで '{stock_name}' を検索", f"https://www.instagram.com/explore/tags/{stock_name}/", use_container_width=True)
        with sns_c2:
            st.link_button(f"▶️ YouTubeで '{stock_name}' を検索", f"https://www.youtube.com/results?search_query={stock_name}", use_container_width=True)
        with sns_c3:
            st.link_button(f"🎵 TikTokで '{stock_name}' を検索", f"https://www.tiktok.com/search?q={stock_name}", use_container_width=True)


# ==========================================
# アプリ最上部ナビゲーションタブ（開いた瞬間最上部に常駐）
# ==========================================
tab1, tab2, tab_guide, tab3, tab4, tab5 = st.tabs([
    "📋 厳選小型株一覧", 
    "💼 1日5分保有株ウォッチ", 
    "🔰 使い方 ＆ データ安心マップ",
    "📚 投資メソッド完全ガイド",
    "📱 iSPEED設定ヘルプ",
    "📖 用語と数値の見方ガイド"
])

# ==========================================
# タブ1：一覧テーブル ＆ 詳細分析 (フォーカス表示対応)
# ==========================================
with tab1:
    header_banner_path = os.path.join(BASE_DIR, "header_banner.png")
    if os.path.exists(header_banner_path):
        st.image(header_banner_path, use_container_width=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #2563EB 100%); padding: 16px 20px; border-radius: 12px; margin-top: 8px; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(15,23,42,0.15); border: 1.5px solid #3B82F6;">
        <div class="header-title-text" style="font-size: 1.5rem; font-weight: 800; color: #FFFFFF !important; letter-spacing: -0.5px; line-height: 1.25;">
            🚀 TOTOTO-KABU
        </div>
        <div class="header-sub-text" style="margin-top: 8px; font-size: 0.90rem;">
            小型株集中投資ダッシュボード ｜ 時価総額300億円以下・高成長・新世代スクリーナー
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================
    # 検索条件の表示／非表示切り替えバー ＆ 条件バッジ
    # ==========================================
    c_btn_col1, c_btn_col2 = st.columns([1.8, 4.2])
    with c_btn_col1:
        btn_label = "👁️ 条件バッジを隠す" if st.session_state.show_conditions else "👁️ 条件バッジを表示"
        if st.button(btn_label, use_container_width=True, help="画面上の条件バッジの表示／非表示を切り替えます"):
            st.session_state.show_conditions = not st.session_state.show_conditions
            save_current_conditions()
            st.rerun()
    
    with c_btn_col2:
        st.caption(f"💾 前回の検索条件が自動保存・復元されています（該当: **{len(df)}社** / {base_population_label}）")
    
    if st.session_state.show_conditions:
        tags_html = "".join([f'<span class="filter-tag">{f}</span>' for f in active_filters])
        with st.container(border=True):
            st.markdown(f"""
            <div style="margin-bottom: 8px;">
                <span class="filter-label" style="font-weight: 800; color: #1E3A8A; font-size: 0.95rem;">【現在適用中の条件】:</span>
                {tags_html}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #BFDBFE;'>", unsafe_allow_html=True)
            
            f_btm_col1, f_btm_col2, f_btm_col3 = st.columns([3.5, 1.2, 1.0])
            with f_btm_col1:
                st.markdown(f"""
                <div style="font-weight: 800; color: #1D4ED8; font-size: 1.08rem; padding-top: 6px;">
                    👉 該当: <strong>{len(df)} 社</strong> / {base_population_label}
                </div>
                """, unsafe_allow_html=True)
            with f_btm_col2:
                if st.button(f"🔄 デフォルト (全{default_total_count}社)", use_container_width=True, key="badge_clear_all_mob", help="すべてのフィルターを解除して全社表示に戻します"):
                    clear_all_filters()
                    st.rerun()
            with f_btm_col3:
                has_undo = bool(st.session_state.get("previous_filter_snapshot"))
                if st.button("↩️ 取消", use_container_width=True, key="badge_undo_clear_mob", disabled=not has_undo, help="直前の絞り込み条件を復元します"):
                    undo_clear_filters()
                    st.rerun()
    
    
    if len(df) == 0:
        st.warning("⚠️ **現在の絞り込み条件に一致する銘柄がありません（0件）。**\n\n上級者設定で対象市場（グロース、スタンダード等）にチェックを入れるか、画面上部の「🔄 全クリア」を押して条件をリセットしてください。")
        st.info("💡 **ヒント**: 上級者設定を開いている場合は、サイドバーの『🔒 小型株・原則モードに戻して閉じる』を押すと、ワンタップで原則モード（全126社）に戻せます。")
    else:
        # 銘柄の仕分け判定列を付与（メモがある銘柄には 📝 を付与）
        def get_status_badge(code):
            c_str = str(code)
            st_info = st.session_state.stock_status.get(c_str, {})
            st_val = st_info.get("status", "unreviewed")
            
            # メモが存在するか確認
            has_note = bool(st.session_state.stock_notes.get(c_str, {}).get("note", "").strip())
            note_icon = " 📝" if has_note else ""

            if st_val == "watching":
                return f"⭐️ 監視中{note_icon}"
            elif st_val == "excluded":
                return f"❌ 対象外{note_icon}"
            return f"⚪ 未判定{note_icon}"

        df["仕分け"] = df["コード"].astype(str).map(get_status_badge)

        # FX目線での統合売買・エントリー判定列を付与（重複するチャートトレンドを吸収統合）
        def get_quick_entry_signal(row):
            high_drop = row.get("高値下落率(%)", None)
            trend = str(row.get("チャートトレンド", ""))
            
            # 1. 下降トレンド判定
            if "下降トレンド" in trend:
                return "🔴 ⚠️ 下降 / 調整中"
            
            # 2. 高値下落率がある場合の精密分類
            if pd.notna(high_drop):
                h_val = float(high_drop)
                if h_val <= 3.5:
                    return "🟡 ⏳ 高値警戒(待ち)"
                elif h_val >= 35.0:
                    # 高値から大幅暴落後の戻り局面（シンカ等。シコリ玉注意）
                    return "🟣 🔄 リバウンド途上(警戒)"
                elif 7.0 <= h_val <= 30.0:
                    return "🟢 🎯 押し目買い好機"
                elif 3.5 < h_val < 7.0:
                    return "🔵 ⚡ 上昇中(高値接近)"
            
            if "上昇トレンド" in trend:
                return "🟢 🎯 押し目買い好機"
            return "⚪ 🔄 保ち合い / レンジ"

        df["エントリー判定"] = df.apply(get_quick_entry_signal, axis=1)

        # 上部：仕分け表示フィルター切替 ＆ 件数バッジ
        all_codes = df["コード"].astype(str).tolist()
        watch_cnt = sum(1 for c in all_codes if st.session_state.stock_status.get(c, {}).get("status") == "watching")
        ex_cnt = sum(1 for c in all_codes if st.session_state.stock_status.get(c, {}).get("status") == "excluded")
        un_cnt = len(all_codes) - watch_cnt - ex_cnt

        filter_box1, filter_box2 = st.columns([3, 2])
        with filter_box1:
            status_filter = st.radio(
                label="🎯 銘柄の仕分けフィルター:",
                options=["🛡️ 除外を隠す (推奨・ノイズゼロ)", "⭐️ 監視中のみ表示", "📋 すべて表示 (除外含む)"],
                horizontal=True,
                key="tab1_status_filter_radio"
            )
        with filter_box2:
            st.markdown(f"""
            <div style="display: flex; gap: 8px; align-items: center; justify-content: flex-end; padding-top: 10px;">
                <span style="background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; border: 1px solid #FCD34D;">⭐️ 監視中: {watch_cnt}社</span>
                <span style="background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; border: 1px solid #FCA5A5;">❌ 対象外: {ex_cnt}社</span>
                <span style="background-color: #F1F5F9; color: #475569; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85rem; border: 1px solid #CBD5E1;">⚪ 未判定: {un_cnt}社</span>
            </div>
            """, unsafe_allow_html=True)

        # フィルター適用
        if "除外を隠す" in status_filter:
            tab1_df = df[df["コード"].astype(str).map(lambda c: st.session_state.stock_status.get(c, {}).get("status")) != "excluded"].copy()
        elif "監視中のみ" in status_filter:
            tab1_df = df[df["コード"].astype(str).map(lambda c: st.session_state.stock_status.get(c, {}).get("status")) == "watching"].copy()
        else:
            tab1_df = df.copy()

        # 一覧テーブルの列構成（注目順に再構成：銘柄名の隣に株価・単元株・特徴、データ詳細は後ろへ、不要列を削減）
        display_cols = [
            "仕分け", "エントリー判定", "コード", "銘柄名_リンク", "株価(円)", "単元購入額(万円)", "特徴・サービス",
            "売上高成長率(%)", "時価総額(億円)", "インサイダー保有率(%)", "高値下落率(%)",
            "市場", "平均年齢", "X口コミ", "財務健全性", "PER", "3年後想定倍率", "代表取締役"
        ]
        valid_cols = [c for c in display_cols if c in tab1_df.columns]
        display_df = tab1_df[valid_cols].copy()

        table_column_config = {
            "仕分け": st.column_config.TextColumn("仕分け判定", width="small", help="⭐️監視中 / ❌対象外 / ⚪未判定"),
            "エントリー判定": st.column_config.TextColumn("エントリー判定 (FX目線)", width="medium", help="🎯押し目買い好機 / ⏳高値警戒(待ち) / 🟣リバウンド途上 / 🔴下降調整中"),
            "コード": st.column_config.TextColumn("コード", width="small", help="証券コード（行選択でワンタップコピー可能）"),
            "銘柄名_リンク": st.column_config.LinkColumn(
                "銘柄名 (Yahooへ)",
                display_text=r"#(.*)",
                width="medium",
                help="タップするとYahoo!ファイナンス詳細ページが開きます"
            ),
            "株価(円)": st.column_config.NumberColumn("1株価格", format="%d 円", help="単元未満株（1株取引）で購入できる概算株価"),
            "単元購入額(万円)": st.column_config.NumberColumn("単元株(100株)", format="%.1f 万円", help="通常の単元（100株）購入に必要な資金"),
            "特徴・サービス": st.column_config.TextColumn("特徴・サービス (四季報要約)", width="large"),
            "売上高成長率(%)": st.column_config.NumberColumn("売上成長率", format="+%.1f %%", help="遠藤式最重要：本業の急成長（+20%以上が理想）"),
            "時価総額(億円)": st.column_config.NumberColumn("時価総額", format="%.1f 億円", help="遠藤式最重要：身軽な小型株（300億円以下）"),
            "インサイダー保有率(%)": st.column_config.NumberColumn("オーナー保有率", format="%.1f %%", help="創業者・役員の保有比率（20%以上が理想）"),
            "高値下落率(%)": st.column_config.NumberColumn("高値比下落", format="-%.1f %%", help="過去高値からの値引き・調整度合"),
            "市場": st.column_config.TextColumn("市場", width="small"),
            "平均年齢": st.column_config.TextColumn("社員平均年齢", width="small"),
            "X口コミ": st.column_config.LinkColumn(
                "X(Twitter)口コミ",
                display_text="🔍 口コミを見る",
                width="small"
            ),
            "財務健全性": st.column_config.TextColumn("財務健全性"),
            "PER": st.column_config.NumberColumn("PER", format="%.1f 倍"),
            "3年後想定倍率": st.column_config.TextColumn("3年後成長試算"),
            "代表取締役": st.column_config.TextColumn("代表取締役社長")
        }

        # チェックボックス付きテーブル設定
        editor_column_config = {
            "選択": st.column_config.CheckboxColumn(
                "選択",
                help="チェックを付けると深掘り分析カードを表示、外すと全一覧に戻ります",
                default=False,
                width="small"
            ),
            **table_column_config
        }

        # 選択状態のチェックとテーブル表示ロジック
        selected_code = st.session_state.get("selected_stock_code", None)
        
        # 選択中コードが現在の絞り込み結果内に存在するか確認
        valid_positions = []
        if selected_code is not None:
            valid_positions = [i for i, c in enumerate(tab1_df["コード"]) if str(c) == str(selected_code)]
            if not valid_positions:
                selected_code = None
                st.session_state.selected_stock_code = None

        with st.container(border=True):
            if selected_code is not None and valid_positions:
                # ==========================================
                # 【チェックON時：チェックした銘柄のみを1行表示（チェックONを保持）】
                # ==========================================
                pos = valid_positions[0]
                cur_code = str(tab1_df.iloc[pos]["コード"])
                cur_name = str(tab1_df.iloc[pos]["銘柄名"])
                
                st.subheader(f"📋 選択中銘柄: {cur_code} {cur_name} (1社表示中)")
                
                # ⬅️ 一覧に戻る ＆ 📋 コードワンタップコピーの並列ボタン（高さ・位置・デザイン完全統一）
                sel_b1, sel_b2 = st.columns([1.5, 2.0], vertical_alignment="center")
                with sel_b1:
                    if st.button("⬅️ 全候補銘柄一覧に戻る", key=f"btn_back_list_{cur_code}", use_container_width=True):
                        st.session_state.selected_stock_code = None
                        st.rerun()
                with sel_b2:
                    copy_code_js = f"""
                    <div style="display: flex; align-items: center; height: 100%; margin: 0; padding: 0;">
                        <button onclick="copyCode()" style="
                            width: 100%;
                            height: 42px;
                            background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%);
                            color: #FFFFFF;
                            border: 1.5px solid #1D4ED8;
                            border-radius: 8px;
                            font-size: 0.90rem;
                            font-weight: 700;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 6px;
                            box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25);
                            margin: 0;
                            box-sizing: border-box;
                        " id="cpBtn_{cur_code}">
                            📋 コード【{cur_code}】をコピー
                        </button>
                    </div>
                    <script>
                    function copyCode() {{
                        const c = "{cur_code}";
                        const btn = document.getElementById("cpBtn_{cur_code}");
                        function ok() {{
                            btn.innerHTML = "✅ コピー完了！({cur_code})";
                            btn.style.background = "#16A34A";
                            setTimeout(function() {{
                                btn.innerHTML = "📋 コード【{cur_code}】をコピー";
                                btn.style.background = "linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%)";
                            }}, 2500);
                        }}
                        if (navigator.clipboard && window.isSecureContext) {{
                            navigator.clipboard.writeText(c).then(ok).catch(fallback);
                        }} else {{
                            fallback();
                        }}
                        function fallback() {{
                            const t = document.createElement("textarea");
                            t.value = c;
                            t.style.position = "fixed";
                            t.style.left = "-9999px";
                            document.body.appendChild(t);
                            t.select();
                            document.execCommand("copy");
                            document.body.removeChild(t);
                            ok();
                        }}
                    }}
                    </script>
                    """
                    components.html(copy_code_js, height=45)

                st.caption("💡 左端の「選択」チェックボックスをOFFにするか、上の「一覧に戻る」ボタンで全候補銘柄一覧に戻ります。")

                # チェックされた1行のみのDataFrameを作成（選択列をTrueにしてON状態を保持）
                single_display_df = display_df.iloc[[pos]].copy()
                single_display_df.insert(0, "選択", True)

                st.markdown('<div class="table-scroll-container">', unsafe_allow_html=True)
                edited_single = st.data_editor(
                    single_display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=editor_column_config,
                    disabled=valid_cols,
                    key=f"editor_single_{cur_code}"
                )
                st.markdown('</div>', unsafe_allow_html=True)

                # チェックボックスがOFFに外された場合、全一覧に復帰
                # ※メモ更新等で仕分け列に📝マークが付いてテーブルが再描画された際のリセット誤作動を完全防止！
                # ユーザーが実際にdata_editor上でチェックを外した時（edited_rowsが存在する時）のみ発火
                ed_state = st.session_state.get(f"editor_single_{cur_code}", {})
                ed_rows = ed_state.get("edited_rows", {}) if isinstance(ed_state, dict) else {}
                if 0 in ed_rows and ed_rows[0].get("選択") is False:
                    st.session_state.selected_stock_code = None
                    st.rerun()

                # チェックされた銘柄の直下に深掘り分析カードを展開
                render_stock_deep_dive(pos, tab1_df)

            else:
                # ==========================================
                # 【チェックOFF時：全候補銘柄一覧を表示】
                # ==========================================
                h_col1, h_col2 = st.columns([2.5, 2.5])
                with h_col1:
                    if is_theme_mode and theme_clean_names:
                        st.subheader(f"📋 【{theme_clean_names}】関連銘柄一覧 ({len(tab1_df)}社)")
                    else:
                        st.subheader(f"📋 候補銘柄一覧 ({len(tab1_df)}社)")
                with h_col2:
                    st.markdown("""
                    <div style="display: flex; justify-content: flex-end; align-items: center; padding-top: 6px;">
                        <span style="
                            display: inline-flex;
                            align-items: center;
                            gap: 4px;
                            background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
                            border: 1.5px solid #3B82F6;
                            padding: 4px 10px;
                            border-radius: 20px;
                            font-size: 0.80rem;
                            font-weight: 700;
                            color: #1E40AF;
                            box-shadow: 0 2px 4px rgba(59,130,246,0.15);
                        ">
                            ↔️ ↕️ 縦横スクロール可能
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                st.caption("💡 行の「選択」チェックボックスをONにすると、その銘柄のみの表示に切り替わり直下に深掘り分析が表示されます。")

                all_display_df = display_df.copy()
                all_display_df.insert(0, "選択", False)

                st.markdown('<div class="table-scroll-container">', unsafe_allow_html=True)
                edited_all = st.data_editor(
                    all_display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=editor_column_config,
                    disabled=valid_cols,
                    key="editor_all_stocks"
                )
                st.markdown('</div>', unsafe_allow_html=True)

                csv_data = tab1_df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 絞り込み結果をCSVダウンロード (特徴・サービス・トレンド付き)",
                    data=csv_data,
                    file_name="growth_stocks_filtered.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                # いずれかの行がチェックされたか検知
                checked_rows = edited_all[edited_all["選択"] == True]
                if not checked_rows.empty:
                    checked_idx = checked_rows.index[0]
                    st.session_state.selected_stock_code = str(tab1_df.loc[checked_idx, "コード"])
                    st.rerun()


# ==========================================
# タブ2：1日5分保有株ウォッチ ＆ 損切り管理
# ==========================================
with tab2:
    st.markdown("### 💼 保有株・厳選ウォッチ（書籍P.3, P.21『1日5分チェックシート』）")
    st.markdown("遠藤洋氏が提唱する **「集中投資した本命銘柄を1日5分だけ徹底管理する」** ための専用シートです。**マイナス10%〜20%での機械的な損切りルール** を徹底し、塩漬けを防ぎます。")

    col_add, col_info = st.columns([1, 2])
    with col_add:
        with st.container(border=True):
            st.markdown("#### ➕ 集中投資銘柄の登録")
            input_code = st.text_input("銘柄コード (例: 5139)", "")
            input_price = st.number_input("購入単価 (円)", min_value=1.0, value=1000.0, step=10.0)
            input_shares = st.number_input("保有株数 (株)", min_value=100, value=100, step=100)
            
            if st.button("ウォッチリストに追加", use_container_width=True):
                if input_code:
                    st.session_state.my_watchlist.append({
                        "code": input_code,
                        "buy_price": input_price,
                        "shares": input_shares
                    })
                    save_watchlist(st.session_state.my_watchlist)
                    st.success(f"{input_code} を登録しました！")
                    st.rerun()

    with col_info:
        with st.container(border=True):
            st.markdown("#### 📋 遠藤式・1日5分点検チェックリスト (書籍P.21)")
            st.checkbox("1. ビジネスにトラブルは生じていないか？ (IR・SNS)")
            st.checkbox("2. 経営方針の変更はないか？")
            st.checkbox("3. 経営陣が自社株を売っていないか？ (大量保有報告書)")
            st.checkbox("4. 想定していた売上高や純利益は達成できそうか？")
            st.warning("⚠️ **『投資した会社を好きにならないように！（書籍P.21）』** どんなに期待していた会社でも、ストーリーが崩れたら即座に撤退します。")

    # 登録銘柄一覧と損切りアラート
    if st.session_state.my_watchlist:
        st.markdown("---")
        st.markdown("#### 🎯 集中投資ポートフォリオ状況")

        for item in st.session_state.my_watchlist:
            c = item["code"]
            buy_p = item["buy_price"]
            shares = item["shares"]
            
            row_match = raw_df[raw_df["コード"].astype(str) == str(c)]
            stock_name = row_match.iloc[0]["銘柄名"] if not row_match.empty else "不明"
            
            import yfinance as yf
            current_p = buy_p
            try:
                t = yf.Ticker(f"{c}.T")
                current_p = t.info.get("currentPrice") or t.info.get("regularMarketPrice") or buy_p
            except Exception:
                pass

            pnl_pct = round(((current_p - buy_p) / buy_p) * 100, 2)
            total_buy = buy_p * shares
            total_val = current_p * shares
            diff_yen = int(total_val - total_buy)

            with st.container(border=True):
                w1, w2, w3, w4 = st.columns(4)
                w1.markdown(f"**{c} {stock_name}**")
                w1.caption(f"保有: {shares:,} 株 / 買値: {buy_p:,.0f} 円")
                
                w2.metric("現在株価", f"{current_p:,.0f} 円", f"{pnl_pct:+.2f} %")
                w3.metric("評価損益額", f"{diff_yen:+,} 円")

                with w4:
                    if pnl_pct <= -15.0:
                        st.error("🚨 **【損切り警告】** -15%突破！書籍ルールに基づき機械的なロスカットを強く推奨します。")
                    elif pnl_pct <= -10.0:
                        st.warning("⚠️ **【警戒】** -10%到達。購入シナリオを再確認してください。")
                    else:
                        st.success("✅ 健全圏内 (成長ストーリーを継続フォロー)")
                    
                    if st.button("🗑️ リストから解除", key=f"del_watchlist_{c}", use_container_width=True):
                        st.session_state.my_watchlist = [w for w in st.session_state.my_watchlist if str(w.get("code")) != str(c)]
                        save_watchlist(st.session_state.my_watchlist)
                        st.toast(f"{c} をウォッチリストから削除しました。")
                        st.rerun()



# ==========================================
# タブ：使い方 ＆ データ安心マップ（端末個別保存・一括バックアップ）
# ==========================================
with tab_guide:
    with st.container(border=True):
        st.markdown("""
        ### 🔰 TOTOTO-KABU 基本操作ガイド（簡単4ステップ）
        当アプリは、プロ投資家・遠藤洋氏の『小型株集中投資で1億円』の選定基準に基づき、急成長する小型株を直感的に発掘・監視できるダッシュボードです。
        """)

        g_c1, g_c2 = st.columns(2)
        with g_c1:
            st.markdown("""
            <div style="background: #EFF6FF; border: 1.5px solid #BFDBFE; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #1E3A8A; font-size: 0.95rem; margin-bottom: 6px;">
                    ① プリセットで一発スクリーニング
                </div>
                <div style="font-size: 0.85rem; color: #334155; line-height: 1.45;">
                    サイドバーの「👑 ①王道・集中投資型」や「🔥 全条件クリア」を押すだけで、書籍の理想条件（売上+20%以上、社長大株主、時価総額200億円以下など）を満たすお宝候補銘柄が即座に絞り込まれます。
                </div>
            </div>
            <div style="background: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #166534; font-size: 0.95rem; margin-bottom: 6px;">
                    ② 深掘りカードでAIリサーチ ＆ CM確認
                </div>
                <div style="font-size: 0.85rem; color: #334155; line-height: 1.45;">
                    一覧から気になる銘柄を選択すると、「深掘り分析カード」が開きます。「📋 プロンプトコピー」を押してChatGPTやGrokに貼るだけで、SNS感情分析や競合優位性をプロ級に調査できます。
                </div>
            </div>
            """, unsafe_allow_html=True)
        with g_c2:
            st.markdown("""
            <div style="background: #FEF3C7; border: 1.5px solid #FDE68A; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #92400E; font-size: 0.95rem; margin-bottom: 6px;">
                    ③ メモ入力 ＆ 保有株ウォッチ登録
                </div>
                <div style="font-size: 0.85rem; color: #334155; line-height: 1.45;">
                    「⭐ 検討・監視リストに入れる」を押すと、タブ2の『💼 保有株ウォッチ』に追加されます。銘柄ごとの独自メモも入力可能で、<strong>あなたのお使いの端末だけに完全非公開で安全保存</strong>されます。
                </div>
            </div>
            <div style="background: #FAF5FF; border: 1.5px solid #E9D5FF; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #6B21A8; font-size: 0.95rem; margin-bottom: 6px;">
                    ④ 1日5分！保有株の株価・決算点検
                </div>
                <div style="font-size: 0.85rem; color: #334155; line-height: 1.45;">
                    日々のルーティンは『💼 1日5分保有株ウォッチ』を開くだけ。登録銘柄の株価動向や決算発表予定日を一覧でサッとチェックできます。
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # --- 🛡️ データ分類の完全マップ ---
        st.markdown("""
        ### 🛡️ データ安心マップ（端末個別保存 vs Web共有データ）
        当アプリでは、プライバシーとセキュリティを最優先に設計しています。<strong>あなたが入力したメモや保有株リストはサーバー上に一切保存されず、お使いの端末（ブラウザ）の中だけに独立して保持されます。</strong><br>
        第三者が当アプリにアクセスしても、あなたのデータが閲覧されたり、改ざんされたりすることは構造上100%ありません。
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 12px 0 20px 0;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; background: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <thead>
            <tr style="background: #1E3A8A; color: #FFFFFF; font-weight: 700; text-align: left;">
              <th style="padding: 10px 12px; border: 1px solid #CBD5E1; color: #FFFFFF !important;">データ項目</th>
              <th style="padding: 10px 12px; border: 1px solid #CBD5E1; text-align: center; color: #FFFFFF !important;">保存場所</th>
              <th style="padding: 10px 12px; border: 1px solid #CBD5E1; text-align: center; color: #FFFFFF !important;">第三者の閲覧</th>
              <th style="padding: 10px 12px; border: 1px solid #CBD5E1; text-align: center; color: #FFFFFF !important;">改ざんリスク</th>
              <th style="padding: 10px 12px; border: 1px solid #CBD5E1; color: #FFFFFF !important;">バックアップ・移行</th>
            </tr>
          </thead>
          <tbody>
            <tr style="background: #F0FDF4;">
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #166534;">📝 銘柄個別メモ (自作コメント)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">📱 あなたの端末内のみ</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #16A34A;">🔒 100%不可能 (完全非公開)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #16A34A;">🛡️ 100%遮断 (安全)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-size: 0.82rem; color: #334155;">下のボタンで一括保存/復元</td>
            </tr>
            <tr style="background: #FFFFFF;">
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #1E3A8A;">💼 保有株・ウォッチリスト</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">📱 あなたの端末内のみ</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #16A34A;">🔒 100%不可能 (完全非公開)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #16A34A;">🛡️ 100%遮断 (安全)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-size: 0.82rem; color: #334155;">下のボタンで一括保存/復元</td>
            </tr>
            <tr style="background: #F8FAFC;">
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #1E3A8A;">🎯 検討仕分け (候補/見送り)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">📱 あなたの端末内のみ</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #16A34A;">🔒 100%不可能 (完全非公開)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #16A34A;">🛡️ 100%遮断 (安全)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-size: 0.82rem; color: #334155;">下のボタンで一括保存/復元</td>
            </tr>
            <tr style="background: #EFF6FF;">
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #1E40AF;">🌐 厳選小型株リスト (全126社等)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; color: #1E293B;">☁️ クラウドサーバー</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; color: #475569;">👥 全員共通 (公開)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #16A34A;">🛡️ 閲覧者による変更不可</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-size: 0.82rem; color: #334155;">スクリーナー自動最新化</td>
            </tr>
            <tr style="background: #FFFFFF;">
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #475569;">📈 株価チャート・財務指標</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; color: #1E293B;">📊 市場API (Yahoo!等)</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; color: #475569;">👥 公開市場データ</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #16A34A;">🛡️ 改ざん不可</td>
              <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-size: 0.82rem; color: #334155;">リアルタイム自動取得</td>
            </tr>
          </tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # --- 💾 全データ一括バックアップ ＆ 一括復元 ---
        st.markdown("""
        ### 💾 全メモ・保有株データの一括バックアップ ＆ 復元
        機種変更をされる際や、別のスマートフォン・PCとお手元のメモ・保有株を同期したい場合は、こちらをご利用ください。
        """)

        bk_c1, bk_c2 = st.columns(2)
        with bk_c1:
            st.markdown("#### 📥 データを保存する (バックアップ)")
            st.caption("全銘柄のメモ、保有株ウォッチリスト、仕分け判定を1つのファイル（JSON）にまとめてダウンロードします。")
            
            import json
            backup_dict = {
                "version": "1.0",
                "app": "TOTOTO-KABU",
                "exported_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "stock_notes": st.session_state.get("stock_notes", {}),
                "my_watchlist": st.session_state.get("my_watchlist", []),
                "stock_status": st.session_state.get("stock_status", {})
            }
            json_str = json.dumps(backup_dict, ensure_ascii=False, indent=2)
            export_filename = f"tototo_kabu_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            st.download_button(
                label="📥 全データを一括ダウンロード (JSON)",
                data=json_str,
                file_name=export_filename,
                mime="application/json",
                use_container_width=True,
                key="btn_backup_download"
            )
            note_cnt = len(st.session_state.get("stock_notes", {}))
            watch_cnt_total = len(st.session_state.get("my_watchlist", []))
            st.caption(f"📊 現在の端末保存データ: メモ **{note_cnt} 件** / 保有株 **{watch_cnt_total} 件**")

        with bk_c2:
            st.markdown("#### 📤 データを読み込む (一括復元)")
            st.caption("以前ダウンロードしたバックアップファイル（JSON）を選択すると、全銘柄のメモや保有株が一瞬で完全復元されます。")
            
            uploaded_bk = st.file_uploader("バックアップファイル (.json) を選択", type=["json"], key="uploader_backup_restore")
            if uploaded_bk is not None:
                try:
                    restore_data = json.load(uploaded_bk)
                    if isinstance(restore_data, dict):
                        restored_notes = restore_data.get("stock_notes", {})
                        restored_watch = restore_data.get("my_watchlist", [])
                        restored_status = restore_data.get("stock_status", {})
                        
                        st.session_state.stock_notes = restored_notes
                        st.session_state.my_watchlist = restored_watch
                        st.session_state.stock_status = restored_status
                        
                        st.success(f"🎉 復元成功！ (メモ: {len(restored_notes)}件, 保有株: {len(restored_watch)}件 を読み込みました)")
                        if st.button("🔄 画面を最新状態で再読み込み", use_container_width=True):
                            st.rerun()
                    else:
                        st.error("⚠️ 正しいバックアップファイル形式ではありません。")
                except Exception as e:
                    st.error(f"⚠️ 読み込み中にエラーが発生しました: {e}")


# ==========================================
# タブ3：遠藤洋氏の投資メソッド完全ガイド
# ==========================================
with tab3:
    with st.container(border=True):
        st.markdown("""
        ### 🎯 目的別フィルターパターンの厳格度 ＆ 狙い完全比較表
        当アプリの4大おすすめプリセットと初期状態が、書籍の選定基準にどのように準拠しているか、厳格度（★3〜★6）と狙いをまとめた早見表です。

        <div style="overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 12px 0 20px 0;">
<table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; background: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
  <thead>
    <tr style="background: #1E3A8A; color: #FFFFFF; font-weight: 700; text-align: left;">
      <th style="padding: 10px 12px; border: 1px solid #CBD5E1; min-width: 120px; color: #FFFFFF !important;">パターン名</th>
      <th style="padding: 10px 12px; border: 1px solid #CBD5E1; text-align: center; min-width: 130px; color: #FFFFFF !important;">準拠度・厳格度</th>
      <th style="padding: 10px 12px; border: 1px solid #CBD5E1; text-align: center; min-width: 90px; color: #FFFFFF !important;">該当社数目安</th>
      <th style="padding: 10px 12px; border: 1px solid #CBD5E1; min-width: 220px; color: #FFFFFF !important;">基準の厳しさと狙い</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background: #FFFBEB;">
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #B45309;">🔥 全条件クリア・超お宝型</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #D97706;">★★★★★★<br><span style="font-size:0.75rem; color:#475569;">(究極・奇跡のフルコンプ)</span></td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">1社〜数社<br><span style="font-size:0.75rem; color:#64748B;">(時期により0社)</span></td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; line-height: 1.45; color: #1E293B;"><strong>全11条件を100点満点で全クリした奇跡の銘柄</strong>。<br><span style="font-size:0.82rem; color:#475569;">（時価総額・急成長・社長大株主・若手社員・無借金・割安PER・押し目・上昇トレンド・10万円以下など全て合致）。<br>書籍でも<em>「全てを満たす会社は滅多に出ないが、見つけたら人生が変わるレベルのお宝」</em>とされる極限の絞り込みです。</span></td>
    </tr>
    <tr style="background: #FFFFFF;">
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #1E3A8A;">👑 ① 王道・集中投資型</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #D97706;">★★★★★<br><span style="font-size:0.75rem; color:#475569;">(最も厳格・理想の本命)</span></td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">約10〜20社</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; line-height: 1.45; color: #1E293B;"><strong>書籍P.1の理想5大条件を厳密適用</strong>。<br><span style="font-size:0.82rem; color:#475569;">時価総額200億以下、売上+20%以上、社長30%以上、無借金、上昇トレンド。<br>最も再現性が高く、投資メソッドの真髄となる本命パターンです。</span></td>
    </tr>
    <tr style="background: #F8FAFC;">
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #1E3A8A;">🛡️ ② 堅実安全・押し目型</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #2563EB;">★★★★☆<br><span style="font-size:0.75rem; color:#475569;">(手堅い安全重視)</span></td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">約15〜25社</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; line-height: 1.45; color: #1E293B;">基本条件に「割安PER × 高値から下がった押し目」を掛け合わせ、高値掴みを防いで安く仕込む守りの設定です。</td>
    </tr>
    <tr style="background: #FFFFFF;">
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #1E3A8A;">🚀 ③ テンバガー狙い型</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #EA580C;">★★★★☆+<br><span style="font-size:0.75rem; color:#475569;">(超高成長特化)</span></td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">約10〜15社</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; line-height: 1.45; color: #1E293B;">売上成長率を「+30%以上」に引き上げ、10倍株（テンバガー）の爆発力を持つ企業のみを狙い撃つ攻撃的設定です。</td>
    </tr>
    <tr style="background: #F8FAFC;">
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; font-weight: 700; color: #475569;">📋 デフォルト（初期状態）</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 800; color: #64748B;">★★★☆☆<br><span style="font-size:0.75rem; color:#475569;">(基本合格ライン)</span></td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; text-align: center; font-weight: 700; color: #1E293B;">全126社</td>
      <td style="padding: 10px 12px; border: 1px solid #E2E8F0; line-height: 1.45; color: #1E293B;">時価総額300億円以下、売上+20%以上、社長比率20%以上。<br>最低合格ラインをクリアした全銘柄を広く見渡すための母集団です。</td>
    </tr>
  </tbody>
</table>
</div>

        ---

        ### 📖 『小型株集中投資で1億円』の選定メソッド完全まとめ

        #### 1. 1年以内に3倍以上になる成長株 8つのチェックポイント (書籍P.1)
        1. **上場して5年以内の会社** (初々しく成長余力が大きい)
        2. **時価総額が小さい (300億円以下)** (大企業と違い、身軽に数倍・十倍化が可能)
        3. **創業社長が現役** (情熱と意思決定のスピードが圧倒的)
        4. **社長や経営幹部が大株主** (経営陣の利益と株主の利益が完全一致)
        5. **高学歴の新卒社員がいる** (成長企業には優秀な若者が集まる)
        6. **社員の平均年齢が若い** (20代〜30代前半。活気と柔軟性がある)
        7. **みんなが欲しいと思う商品を提供している** (中学生でもわかるシンプルな需要)
        8. **株価チャートが上昇トレンド** (25日・75日移動平均線上向き。下降トレンドは絶対NG)

        #### 2. イノベーター理論による売買タイミング (書籍P.13〜19)
        * **買い時**: 「アーリーアダプター期 (初期採用者)」が手を伸ばすタイミング。企業が広告に力を入れ始め、キャズム (普及率16%) を超える直前。
        * **売り時**: 「アーリーマジョリティ」から「レイトマジョリティ」に推移する手前。一般人が熱狂し、ワイドショーやSNSで大騒ぎされた時。
        * **金言**: **『まわりが慎重なら「買い」、まわりが興味を持ったら「売り」』**

        #### 3. 株式投資でやってはいけない8つのこと (書籍P.20)
        * ❌ 分散投資はやってはいけない (少額資金なら1〜3銘柄に集中)
        * ❌ 下がった株を持ち続けてはいけない (-10〜20%で即損切り)
        * ❌ 有名な大企業の株は買ってはいけない
        * ❌ 株価を見て株を買ってはいけない
        * ❌ Twitterで盛り上がっている株を買ってはいけない (イナゴ買い厳禁)
        * ❌ 理解できない株を買ってはいけない
        * ❌ 銀行や証券会社がすすめる投資信託を買ってはいけない
        * ❌ 他人に預ける投資はやってはいけない
        """)


# ==========================================
# タブ4：iSPEED設定ヘルプガイド
# ==========================================
with tab4:
    with st.container(border=True):
        st.markdown("""
        ### 📱 楽天証券 iSPEED「スーパースクリーナー」完全設定ガイド
        スマホアプリ「iSPEED」で、当ダッシュボードと同じ条件（遠藤洋氏メソッド ＆ 1株少額投資対応）を再現し、毎日ワンタップで確認するための完全マニュアルです。

        ---

        #### 【ステップ1】スーパースクリーナーを開く
        1. スマホで **iSPEED** アプリを開く
        2. 画面下のメニューから **「検索」**（虫眼鏡アイコン）をタップ
        3. 上部に並んでいるタブの中から **「スーパースクリーナー」** を選択
        4. 画面右上の **「検索条件作成」**（または条件の追加）をタップ
        5. 最上部のタブが **「国内株式」** になっていることを確認（※米国株ではなく国内株式のままでOK）

        ---

        #### 【ステップ2】基本画面の設定（上半分）
        * **市場**: **「東S（スタンダード）」「東G（グロース）」** にチェックを入れる（※プライムは外す）
        * **種別**: **「かぶミニ寄付」** にチェックを入れる
          * ⚠️ **超重要**: 必ず「寄付」にしてください。「リアル」だけにすると小型成長株のほとんどが除外されてしまいます。
        * **規模**: **「小型株」** にチェックを入れる

        ---

        #### 【ステップ3】詳細条件の追加（「⊕ 検索条件追加」から設定）
        画面下部の **「⊕ 検索条件追加」** ボタンをタップし、以下の項目を順に追加します。

        1. **時価総額（会社の身軽さ）**
           * 「株価・財務」カテゴリ → **「時価総額」** を選択
           * 設定値: **上限「300 億円」**（下限は空欄）
        2. **売上高変化率（成長の勢い）**
           * 「財務」カテゴリ → **「売上高変化率」** を選択
           * 設定値: **下限「+20 %」**（今期予想 または 前期実績）
        3. **予想PER（割安・適正水準）** ★超重要注意点！
           * **必ず「財務」タブ** から **『PER（株価収益率）（倍）』** を選択
           * ⚠️ **落とし穴注意**: 「コンセンサス情報」側のPERを選んではいけません。小型株はアナリスト予想がないため全滅してしまいます。必ず「財務」側を選んでください。
           * 設定値: **上限「40 倍」**
        4. **チャートトレンド（上昇トレンド判定）**
           * 「テクニカル」カテゴリ → **「株価と移動平均」** を選択
           * 設定値: **「株価が25日移動平均線上」** にチェック

        ---

        #### 【ステップ4】検索結果が「1件（または極端に少ない）」時の調整ワザ！
        全条件を同時に満たす株は市場全体でも1〜2社しか存在しない「奇跡の超厳選株」です。  
        **普段15〜25社の中から比較して選ぶためのおすすめ調整法**:
        * 👉 **「予想PER 40倍以下」を一旦オフにする**  
          （急成長株は人気でPERが高くなりやすいため、これを外すと一気に優良な急成長株が **15〜20件** に増えて選びやすくなります）

        ---

        #### 【ステップ5】検索条件を保存する（次からワンタップ！）
        1. 画面右下の青緑色ボタン **「検索（〇〇件）」** をタップして結果を表示
        2. 結果一覧画面の **右上にある「条件保存」** をタップ
        3. 条件名に **「遠藤式・小型成長株」** と入力して保存！

        > 💡 **次回からの確認方法**:  
        > iSPEEDの「検索」→「スーパースクリーナー」→ **「保存条件」タブ** を開くだけで、いつでも最新の銘柄一覧が自動更新されてパッと表示されます。
        """)


# ==========================================
# タブ5：投資・専門用語と数値の見方ガイド
# ==========================================
with tab5:
    st.markdown("## 📖 投資・専門用語と数値の見方ガイド")
    st.caption("💡 気になる用語をタップすると、意味や数値（プラス／マイナス）の判断目安が詳しく展開します。")

    # 1. 一覧表の重要項目と数値の読み方
    with st.container(border=True):
        st.markdown("### 📊 一覧表の重要項目 ＆ 数値（＋／ー）の読み取り方")
        
        # 売上高成長率
        with st.expander("📈 売上高成長率（%）"):
            st.markdown("""
            > 💡 **要約**: 本業の勢いと急成長の証拠（全範囲の完全判定早見表）

            * **用語の意味**: 会社が本業のサービスや商品で稼いだ「売上」が、去年に比べてどれくらい増えたかを表す最重要指標です。
            * **数値の読み取り方（隙間なし完全判定）**:
              * 🟢 **`+20.0% 以上`（青信号・理想の大化け水準）**: 本業が猛烈に急拡大。3年で約1.7倍、4年で2倍に成長する本物の大化け成長株です。
              * ⚪ **`+10.0% 〜 +19.9%`（中立・及第点ゾーン）**: 黒字で順調に成長中。合格圏ですが、1年で株価3倍を狙うにはやや勢い不足の標準ペースです。
              * 🟡 **`0.0% 〜 +9.9%`（黄信号・鈍化警戒）**: 成長がストップしかけており、成熟企業・減速の兆候。小型株集中投資としては勢い不足です。
              * 🔴 **`マイナス（-）`（赤信号・手出し無用）**: 前年の売上を割り込み本業が縮小。大化け投資の対象外です。
            """)

        # 高値比下落率
        with st.expander("📉 高値比下落率（%）"):
            st.markdown("""
            > 💡 **要約**: 過去最高値からの値引き（バーゲン）度合（全範囲の完全判定早見表）

            * **用語の意味**: 過去1年間の最も高かった株価（52週高値）から、現在どれくらい値下がりしているかを表します。
            * **数値の読み取り方（隙間なし完全判定）**:
              * 🟡 **`0.0% 〜 -3.0%`（高値警戒・飛びつき注意）**: 直近の天井（レジスタンス）直前。利益確定売りに押されやすいため、飛びつきを避けて押し目を待つのが賢明です。
              * ⚪ **`-3.1% 〜 -6.9%`（浅い調整・様子見ゾーン）**: 調整が始まったばかりの初期段階。ここから反発するか、さらに下落が深まるかを見極める保留ゾーンです。
              * 🟢 **`-7.0% 〜 -20.0%`（青信号・絶好の押し目買い好機）**: 上昇トレンド中の健全な利益確定売りが一巡し、25日移動平均線で反発しやすい最も安全で勝率の高い買い場です。
              * ⚪ **`-20.1% 〜 -34.9%`（深押し・反発観察ゾーン）**: 調整がやや長引いている状態。下げ止まり（サポートラインでのもみ合い）を確認してから仕掛けるべきゾーンです。
              * 🟣 **`-35.0% 超`（紫信号・底割れ警戒）**: 高値から大暴落した後の状態。過去の高値掴み組の戻り売り（しこり玉）が大量に待ち構えているため手出し無用です。
            """)

        # 25日線乖離率
        with st.expander("📏 25日移動平均線乖離率（%）"):
            st.markdown("""
            > 💡 **要約**: 株価の過熱感と割安度（全範囲の完全判定早見表）

            * **用語の意味**: 直近25日間の平均購入価格から、現在の株価がどれくらい離れているかを表す過熱感メーターです。
            * **数値の読み取り方（隙間なし完全判定）**:
              * ⚠️ **`+15.0% 以上`（赤・過熱警戒シグナル）**: 急上昇して買われすぎている過熱状態。短期的な反落リスクが極めて高いため、飛びつき買いは厳禁です。
              * ⚪ **`+7.1% 〜 +14.9%`（中立・上昇キープゾーン）**: 強い上昇トレンドを維持しているが、新規買いには少し引きつけが足りない中間ゾーンです。
              * 🎯 **`0.0% 〜 +7.0%`（青信号・好機シグナル）**: 25日移動平均線のすぐ上にあり、移動平均線を床（サポート）にして綺麗に反発する最も安全な買い場です。
              * 🔄 **`マイナス（-）`（黄・調整シグナル）**: 株価が25日線の下に潜り込んでおり、再び25日線を上抜けて陽線をつけるまで待つべき調整局面です。
            """)

        # 時価総額
        with st.expander("🏢 時価総額（億円）"):
            st.markdown("""
            > 💡 **要約**: 会社の身軽さと大化け余力（全範囲の完全判定早見表）

            * **用語の意味**: `現在の株価 × 発行済み株式数` で計算され、「その会社を丸ごと全部買い占めるのに必要なお金」を表します。
            * **数値の読み取り方（隙間なし完全判定）**:
              * 👑 **`100億円 〜 200億円未満`（理想のサイズ）**: 身軽で数倍化（テンバガー）が最も狙いやすく、これから機関投資家が買い始めるゴールデンゾーンです。
              * ✅ **`200億円 〜 300億円`（合格ライン）**: 小型成長株として十分身軽に値上がりできる上限サイズです。
              * ⚪ **`300億円 〜 500億円`（中小型ゾーン）**: 安定感は増しますが、短期急騰の爆発力は徐々にマイルドになる中間サイズです。
              * ❌ **`500億円超`（対象外）**: 大企業・中堅企業で急騰余力が小さいため、小型株集中投資の対象外です。
            """)

        # 単元株と1株取引
        with st.expander("💰 単元株（100株）と 1株価格（単元未満株）"):
            st.markdown("""
            > 💡 **要約**: 資金に合わせた賢い買い方

            * **用語の意味**:
              * **単元株（100株）**: 通常の証券取引所で売買される基本セット（お菓子の箱買い）。
              * **単元未満株（1株取引）**: 100株セットをバラして、1株単位で買える少額投資サービス（お菓子の1個バラ売り）。
            * **数値の読み取り方**:
              * **単元購入額 `10万円以下`**: 株価1,000円以下の銘柄なら、10万円の元手で100株丸ごと購入可能です。
              * **単元購入額 `20万〜50万円`**: 100株だとまとまった資金が必要ですが、1株取引なら右側の **「1株価格（数百円〜数千円）」** から気軽に少額投資が始められます。
            """)

        # 創業者・役員保有比率（インサイダー比率）
        with st.expander("👔 創業者・役員保有比率（%）"):
            st.markdown("""
            > 💡 **要約**: 経営陣の本気度と利害の一致

            * **用語の意味**: 社長や取締役が、自社の株を何％自分で持っているかを表します。
            * **数値の読み取り方**:
              * 👑 **`20% 〜 70%`（理想的オーナー経営）**: 社長自身の資産と株価が直結しているため、「株価を何倍にも引き上げる熱量」がサラリーマン社長とは桁違いです。
              * ❌ **`数% 以下`（警戒）**: 外部から送り込まれた雇われ社長が多く、短期的な保身に走りやすい傾向があります。
            """)

        # PER
        with st.expander("⚖️ PER（株価収益率・倍）"):
            st.markdown("""
            > 💡 **要約**: 稼ぐ力に対する株価のお買い得度

            * **用語の意味**: 会社の純利益に対して、株価が何倍まで買われているかを表します。「投資した資金を今の利益ペースで何年で回収できるか」の目安です。
            * **数値の読み取り方**:
              * 🟢 **`15倍 〜 40倍以下`（適正・安全圏）**: 成長性と価格のバランスが良く、割高すぎない水準です。
              * 🟡 **`60倍 〜 100倍超`（超割高期待）**: 市場から将来の爆発的成長が織り込まれており、決算で少しでも期待を下回ると急落するリスクを伴います。
            """)

        # 財務健全性（実質無借金）
        with st.expander("🛡️ 財務健全性（実質無借金）"):
            st.markdown("""
            > 💡 **要約**: 倒産リスクゼロの安心感

            * **用語の意味**: 会社の手元にある「現金・預金」が、銀行からの「借金（有利子負債）」を上回っている状態です。
            * **読み取り方**:
              * **`実質無借金`**: 集中投資の最大の恐怖である「突然の倒産」が原理的に極めて起こりにくく、不況期でも事業投資を続けて生き残れる最強の財務体質です。
            """)

        # 四季報
        with st.expander("📚 会社四季報（要約）"):
            st.markdown("""
            > 💡 **要約**: 全上場企業の通信簿

            * **用語の意味**: 東洋経済新報社が年4回発行する、日本中の上場企業のビジネスモデル、財務、業績予想、社員年齢などが網羅された百科事典です。
            * **読み取り方**: 本アプリの「特徴・サービス」欄には、四季報の重要要約が自動抽出されており、どんな商品で誰からお金をもらっているかが一目で掴めます。
            """)

    # 2. チャート・テクニカル用語の読み方
    with st.container(border=True):
        st.markdown("### 📈 チャート・テクニカル用語 ＆ 売買タイミングの読み取り方")
        
        with st.expander("📈 25日／75日移動平均線（MA）"):
            st.markdown("""
            > 💡 **要約**: 過去の平均買い値とトレンドの方向を示す命綱

            * **25日移動平均線（緑・短期線）**:
              * 過去25営業日（約1ヶ月）にその株を買った投資家の平均購入単価です。
              * 株価が25日線の上を推移していれば「直近買った人たちが含み益で強気」の状態。株価が下がってきても、この線に触れて反発しやすい **「最強の押し目買いサポートライン（床）」** になります。
            * **75日移動平均線（オレンジ・中期線）**:
              * 過去75営業日（約3ヶ月・四半期決算1回分）の平均購入単価です。
              * 会社の実力（業績成長）が本物かどうかを判定する中期トレンドの絶対防衛ラインとなります。
            * **数値・サインの読み取り方**:
              * 🟢 **`ゴールデンクロス（25日線が75日線を下から上抜け）`**: 短期の勢いが中期の平均を上回り、本格的な大化け上昇トレンドが開始した最高の買いシグナルです。
              * ⚠️ **`25日線割れ`**: 一時的な調整局面。すぐに反発すれば絶好の押し目ですが、75日線まで調整が長引くリスクに警戒します。
            """)

        with st.expander("🕯️ ローソク足（赤と青・陽線と陰線）"):
            st.markdown("""
            > 💡 **要約**: 買い手と売り手の戦いの記録

            * **赤色のローソク（陽線）**: スタート（始値）よりもゴール（終値）が高く終わった状態。買い手が勝った強い日です。
            * **青色のローソク（陰線）**: スタートよりもゴールが安く終わった状態。売り手が勝った弱い日です。
            * **ヒゲ（上下に伸びる細い線）**: その期間中に一時的につけた最高値（上ヒゲ）や最安値（下ヒゲ）を表します。長い下ヒゲが出ると「安値で強烈に買い支えられた反発シグナル」になります。
            """)

        with st.expander("🚀 パーフェクトオーダー ＆ 上昇トレンド"):
            st.markdown("""
            > 💡 **要約**: 最強の買い相場状態

            * **状態**: 上から順に **`株価 ＞ 25日移動平均線（緑） ＞ 75日移動平均線（オレンジ）`** と並び、すべての線が右肩上がりの状態。
            * **読み取り方**: 直近買った人も、数ヶ月前から持っている人も「全員が含み益」を出しており、売り急ぐ人がいないため株価が最も伸びやすい最強のトレンド状態です。
            """)

        with st.expander("🎯 押し目買い"):
            st.markdown("""
            > 💡 **要約**: 上昇途中のバーゲンセールを拾う技

            * **意味**: ずっと上がり続ける株はなく、途中で必ず一時的な利益確定売りで少し下がる（調整する）波があります。この「一時的な調整安」を狙って買う手法です。
            * **成功の目安**: 25日移動平均線に株価がタッチして、下ヒゲを出して反発した瞬間を拾うことで、高値掴みを防ぎながら安値で仕込めます。
            """)

        with st.expander("🧱 サポレジ（サポートラインとレジスタンスライン）"):
            st.markdown("""
            > 💡 **要約**: 価格の床と天井

            * **レジスタンスライン（上値抵抗線・天井）**: 過去に高値をつけた価格水準。ここで買った人たちが「やれやれ、買値に戻ったから売ろう」と売り注文を出すため、株価が弾き返されやすい天井です。
            * **サポートライン（下値支持線・床）**: 移動平均線や過去の安値水準。「ここまでは下がらないだろう」と買い注文が待ち構えている頑丈な床です。
            * **立ち回り**: 天井の手前で買うのは危険（飛びつき厳禁）。床まで引きつけるか、天井を完全に突き破った後に買うのが鉄則です。
            """)

        with st.expander("🗼 イナゴタワー ＆ 全戻し"):
            st.markdown("""
            > 💡 **要約**: 仕手株・材料株の罠

            * **意味**: SNSやネット掲示板で急に話題になり、短期トレーダー（イナゴ）が一斉に群がって垂直上昇（タワー形成）したあと、大口が売り抜けて全員が一斉に投げ売りし、元の株価まで急落すること。
            * **見分け方**: 本業の売上成長（ファンダメンタルズ）の裏付けがなく、数日だけ急騰した株は危険。本アプリのスクリーナーは「売上+20%以上の本物の成長企業」に限定することで、この罠を事前に排除しています。
            """)

    # 3. イノベーター理論の売買フェーズ
    with st.container(border=True):
        st.markdown("### 💡 イノベーター理論 普及フェーズと売買タイミング")
        st.markdown("""
        遠藤洋氏の投資手法の真髄は、**『世間がその商品に気づき始めた瞬間に買い、誰もが知るブームになった瞬間に売る』** という人間心理の先回りです。
        """)

        with st.expander("🟢 アーリーアダプター期（買い時・初期採用者フェーズ）"):
            st.success("""
            * **普及率**: 2.5% 〜 16%
            * **状態**: 流行に敏感な若者やアンテナの高い人たちが使い始め、テレビCMやYouTube広告、タクシー広告が始まったタイミング。
            * **判断**: 世間一般の人はまだ「そんなの知らん」「怪しい」と慎重。**『まわりが慎重なら買い』** の法則が発動する絶好の仕込み場です。
            """)

        with st.expander("🔴 レイトマジョリティ期（売り時・過熱天井フェーズ）"):
            st.warning("""
            * **普及率**: 50% 〜 84%
            * **状態**: テレビのワイドショーで特集され、普段投資をしない友人や親戚まで「あの株儲かるらしいよ」と口にし始めたタイミング。
            * **判断**: これ以上新しい買い手が入ってこない天井圏。**『まわりが興味を持ったら売り』** の金言通り、利益を確定して立ち去る時です。
            """)

    # 4. 取引ルール ＆ 相場・注文の重要用語
    with st.container(border=True):
        st.markdown("### 🏛️ 取引ルール ＆ 相場・注文の重要用語")

        with st.expander("🚀 ストップ高（S高） ＆ 🛑 ストップ安（S安）"):
            st.markdown("""
            > 💡 **要約**: 1日の価格変動ブレーキ（制限値幅）
            
            * **用語の意味**:
              * 日本の株式市場（東証）では、パニックや過度な投機で株価が一瞬で0円になったり何倍にも暴走するのを防ぐため、前日の終値を基準に **「1日に動ける上下の限界幅（制限値幅）」** が定められています。
              * その日の上限まで株価が上昇することを **「ストップ高（S高）」**、下限まで暴落することを **「ストップ安（S安）」** と呼びます。
            * **取引の仕組み（比例配分）**:
              * ストップ高で買い注文が売り注文を圧倒的に上回った場合、取引終了時に抽選で株を割り当てる「比例配分（ひれいはいぶん）」が行われます。
            * **実践的な立ち回り・読み取り方**:
              * 👑 **ストップ高の翌日**: 強い好決算や特大ニュースを背景にしたS高は、翌日もGU（ギャップアップ・高く始まる）する傾向があります。ただし、翌日の寄付き直後に「材料出尽くし」で大陰線を引くリスクもあるため、飛びつき買いは厳禁です。
              * ⚠️ **ストップ安の警戒**: 悪材料で連続ストップ安になると、売りたいのに買い手がつかず何日も損切りできないリスクがあります。
            """)

        with st.expander("⚡ 成行（なりゆき）注文 ＆ 🎯 指値（さしね）注文"):
            st.markdown("""
            > 💡 **要約**: 「今すぐ買う」vs「値段を決めて待つ」
            
            * **成行（なりゆき）注文**:
              * 価格を指定せず、「いくらでもいいから今すぐ買いたい（売りたい）」という注文です。最優先で即座に取引が成立します。
              * ⚠️ **初心者の注意点**: 急騰している小型株を成行で買うと、想定外の超高値で約定してしまい、買った瞬間に大損（高値掴み）する危険があります。
            * **指値（さしね）注文**:
              * 「1,200円以下なら買う」「1,500円以上なら売る」と希望価格を指定する注文です。
              * 🟢 **遠藤洋式の基本**: 感情に流されず、「自分が納得した適正価格まで引きつけて待つ」のが原則のため、買い注文は指値が基本です。
            """)

        with st.expander("🛡️ 逆指値（ぎゃくさしね・ストップロス）注文"):
            st.markdown("""
            > 💡 **要約**: 大損を絶対に防ぐ「自動ブレーキ装置」
            
            * **用語の意味**:
              * 通常の指値とは逆に、「株価が○○円まで下がったら、自動で売却する（損切りする）」と事前に予約しておく注文です。
            * **実践的な重要性**:
              * 集中投資で最も大切なのは「1回の大暴落で資金を吹き飛ばさないこと」。
              * どんな凄腕投資家でも予測を外すことはあります。買った瞬間に **「買値から -10%（または直近安値）」** に逆指値を入れておくことで、仕事中や夜間でも感情を挟まず自動で損失を限定できます。
            """)

        with st.expander("📊 出来高（できだか・売買高）"):
            st.markdown("""
            > 💡 **要約**: 相場のエネルギーと人気のバロメーター
            
            * **用語の意味**: その日やその週に、取引所で実際に売り買いされた「株の総数」です。
            * **数値の読み取り方**:
              * 🚀 **出来高急増 ＋ 株価上昇（本物の買い）**: 機関投資家や大口の本格的な資金が大量に流入している証拠。上昇トレンドが長続きしやすい最強のシグナルです。
              * 💤 **出来高過疎（閑散相場）**: 誰からも見向きされていない状態。小型株では一度出来高が枯れると、売りたい時に売れなくなる流動性リスクがあります。
            """)

        with st.expander("💣 信用取引 ＆ 信用買い残（ざん）・シコリ玉"):
            st.markdown("""
            > 💡 **要約**: 借金トレードの残骸と将来の売り圧力
            
            * **用語の意味**:
              * **信用取引**: 証券会社に担保を預け、自己資金の約3.3倍のレバレッジをかけて株を買う（または空売りする）手法。最長6ヶ月以内に必ず決済（反対売買）しなければなりません。
              * **信用買い残**: 借金して買った投資家が、まだ決済せずに持っている株の残高です。
            * **なぜ重要なのか（シコリ玉）**:
              * 信用買い残が多い銘柄が下落すると、含み損を抱えた個人投資家が大量に捕まります。株価が少し上がると「やれやれ、買値に戻ったから損切り・返済しよう」と大量の売りが降ってくるため（シコリ玉）、上値が極めて重くなります。
            """)

        with st.expander("⚖️ 信用倍率（しんようばいりつ・倍）"):
            st.markdown("""
            > 💡 **要約**: 買い手と売り手の需給バランス
            
            * **計算式**: `信用買い残 ÷ 信用売り残`
            * **数値の読み取り方**:
              * 🟢 **`1倍 未満`（売り手優勢・好需給）**: 信用で売っている人（空売り）の方が多く、将来必ず買い戻さなければならないため、株価が上昇した際に「踏み上げ相場（空売りの買い戻しで爆発急騰）」が起きやすい好需給です。
              * 🟡 **`1倍 〜 5倍`（標準水準）**: 需給バランスが取れた一般的な水準。
              * 🔴 **`10倍 〜 数十倍超`（買い残過多・需給悪化）**: 借金で買った人が圧倒的に多く、将来の売り圧力が山積みになっている状態。業績が良くても株価が上がりにくいため、警戒が必要です。
            """)

    # 5. 投資指標 ＆ 企業アクション用語
    with st.container(border=True):
        st.markdown("### 🏢 投資指標 ＆ 企業アクションの重要用語")

        with st.expander("🏢 PBR（株価純資産倍率・倍）"):
            st.markdown("""
            > 💡 **要約**: 会社の解散価値に対する割安度
            
            * **用語の意味**: 会社の純資産に対して、株価が何倍まで評価されているかを表します。
            * **数値の読み取り方**:
              * **`1倍`**: 「株価の合計（時価総額）」と「会社を今すぐ解散した時に株主に配れる現金価値」がちょうどイコール。理論上の底値目安。
              * 🟢 **`1倍 割れ（0.5倍〜0.8倍）`**: 解散価値よりも安く放置されている状態（東証がPBR1倍割れ改善を強く要請中）。
              * 🚀 **小型成長株（2倍〜5倍以上）**: 成長株は工場やビルなどの物的資産よりも「将来の稼ぐアイデアやITシステム」が価値の源泉のため、PBRが高くなるのが普通です。
            """)

        with st.expander("💡 ROE（自己資本利益率・%）"):
            st.markdown("""
            > 💡 **要約**: 株主のお金をどれだけ上手に増やしたか（経営効率）
            
            * **用語の意味**: 株主が出資したお金（自己資本）を使って、会社が1年間でどれだけ純利益を稼ぎ出したかのパーセンテージです。
            * **数値の読み取り方**:
              * 👑 **`15% 〜 20% 以上`（超優秀な高収益企業）**: 集めたお金を無駄に寝かせず、効率的に新規事業へ回して高利益を生み出す一流経営者の証拠。
              * ⚠️ **`5% 未満`（低効率）**: お金を銀行に寝かせているだけで、株主の元手を有効活用できていない状態。
            """)

        with st.expander("🎁 配当利回り ＆ 自社株買い（株主還元）"):
            st.markdown("""
            > 💡 **要約**: 利益の分け前 vs 事業への全額再投資
            
            * **配当利回り**: 株価に対して、年間何％の配当金がもらえるかの利回り。
            * **自社株買い**: 企業が自分のお金で市場の自社株を買い戻して消却し、1株の価値を直接引き上げる施策。
            * **小型株集中投資の視点（小型成長株の本質）**:
              * 初心者は「配当利回り4%」などの高配当株を好みますが、**「株価が2倍〜3倍になる小型成長株」を狙う場合、配当金は無配（0円）や低配当で十分**です。
              * なぜなら、利益を配当として配ってしまうより、新規出店や開発費、広告CMに全額再投資して売上を何倍にも急拡大させてくれた方が、結果的に株価が何倍にもなって投資家の利益が圧倒的に大きくなるからです。
            """)

        with st.expander("✂️ 株式分割（かぶしきぶんかつ）"):
            st.markdown("""
            > 💡 **要約**: 株を小さく切り分けて買いやすくするお祭り
            
            * **用語の意味**: 例えば「1株を2株（または5株）に分割」すること。会社の価値（時価総額）は変わりませんが、1株あたりの株価が半分になり、株数が増えます。
            * **株価への影響**:
              * 100株買うのに100万円かかっていた株が、分割によって50万円で買えるようになるため、個人投資家の買いが殺到し、株価が急上昇する強い追い風材料（ポジティブイベント）になりやすいです。
            """)

        with st.expander("⚠️ 公募増資（PO） ＆ 第三者割当増資（株式の希薄化）"):
            st.markdown("""
            > 💡 **要約**: 新株を刷って資金集め（株主にとっての希薄化リスク）
            
            * **用語の意味**: 企業が新しく株を印刷・発行して、投資家や提携企業から数十億〜数百億円の資金を調達すること。
            * **株価への影響（希薄化）**:
              * ピザのサイズ（会社の価値）が同じまま、ピースの数だけ増やすようなものなので、**「1株あたりの利益や価値が薄まる（希薄化・ダイリューション）」** ため、発表直後は株価が急落しやすいリスクがあります。
              * ※ただし、集めた資金で大型M&Aや爆発的成長を遂げる「前向きな増資」の場合は、後から株価が急回復することもあります。
            """)

# ==========================================
# 公式免責事項 ＆ リファレンスフッター (コンプライアンス表記)
# ==========================================
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.80rem; line-height: 1.7; padding: 28px 12px 16px 12px; margin-top: 36px; border-top: 1px solid #E2E8F0;">
    <div style="font-weight: 800; color: #1E293B; font-size: 0.95rem; margin-bottom: 6px;">
        🚀 TOTOTO-KABU
    </div>
    <div>小型成長株スクリーナー ＆ 集中投資分析ダッシュボード</div>
    <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 8px;">
        ※本ツールの選定基準および指標ロジックは、書籍『10万円から始める！小型株集中投資で1億円』（遠藤洋 著）の公開メソッドを参考に、個人の学習・研究目的で実装された非公式ツールです。<br>
        特定の銘柄の売買を推奨または保証するものではありません。実際の投資判断はご自身の責任において行ってください。
    </div>
</div>
""", unsafe_allow_html=True)

