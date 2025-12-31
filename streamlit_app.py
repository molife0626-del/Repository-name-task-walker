import streamlit as st
import time
import requests
import uuid
import base64
import random
import threading
from datetime import datetime

# ==========================================
#   ⚙️ 設定エリア
# ==========================================
# ★ここに新しいGASのウェブアプリURLを貼り付けてください
# デプロイ時は「アクセスできるユーザー：全員」にすることを忘れずに！
GAS_URL = "https://script.google.com/macros/s/AKfycbxFbhiE8ikUs9ebv1BTba9bZbAZ80nWDESVS85Iev1aSitwtwV4VUGE0UBMi3xdyVO7/exec"

# ユーザー管理
USERS = {
    "森": "3457",
    "社長": "3457",
    "経理": "3333",
    "メンバーA": "aaaa"
}
ADMIN_USERS = {"森", "社長"} 

st.set_page_config(page_title="MBS Task Walker", page_icon="Ⓜ️", layout="wide")

# ==========================================
#   🎨 デザイン (CSS)
# ==========================================
st.markdown("""
<style>
    .block-container { padding-top: 5rem !important; padding-bottom: 3rem !important; }
    .stApp { background-color: #FFFAF5; }
    [data-testid="stSidebar"] { background-color: #FFF3E0; border-right: 1px solid #FFCC80; }
    h1, h2, h3 { color: #E65100 !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton > button {
        background-color: white; color: #E65100; border: 2px solid #E65100;
        border-radius: 8px; font-weight: bold; transition: all 0.2s;
        width: 100%;
    }
    .stButton > button:hover { background-color: #E65100; color: white; border-color: #E65100; }
    .stButton > button:active { transform: scale(0.98); }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #FFE0B2 !important; background-color: white;
        border-radius: 10px; box-shadow: 0 2px 4px rgba(230, 81, 0, 0.1);
    }
    /* ログ表示用のスタイル */
    .log-entry { font-size: 0.85em; color: #666; border-bottom: 1px solid #eee; padding: 4px 0; }
    .log-date { color: #E65100; font-weight: bold; margin-right: 5px; }
    
    @media (max-width: 768px) {
        [data-testid="column"] { width: 100% !important; flex: 1 1 auto !important; min-width: 100% !important; }
        h1 { font-size: 1.8em !important; }
    }
    @keyframes runIn { 0% { left: -20%; } 100% { left: 45%; } }
    @keyframes receive { 0% { opacity: 0; } 100% { opacity: 1; } }
    @keyframes textFade { 0% { opacity: 0; top: 60%; } 100% { opacity: 1; top: 55%; } }
    
    .anim-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255, 250, 245, 0.95); z-index: 99999;
        display: flex; align-items: center; justify-content: center;
        pointer-events: none;
    }
    .runner-book { position: absolute; font-size: 6rem; top: 40%; animation: runIn 0.8s ease-out forwards; }
    .receiver-book { position: absolute; font-size: 6rem; top: 40%; right: 40%; opacity: 0; animation: receive 0.3s 0.8s forwards; }
    .pass-message { position: absolute; font-size: 2rem; color: #E65100; top: 55%; opacity: 0; animation: textFade 0.3s 1.0s forwards; font-weight: bold;}
    
    [data-testid="stStatusWidget"] { display: none; }
    .bearing-loader {
        display: inline-block; width: 20px; height: 20px;
        border: 2px solid #FF9800; border-radius: 50%;
        border-top: 2px solid transparent;
        animation: spin 1s linear infinite; margin-right: 5px; position: relative;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
""", unsafe_allow_html=True)

# --- キャッシュ & ユーティリティ ---
if 'tasks_cache' not in st.session_state: st.session_state['tasks_cache'] = []
if 'video_cache' not in st.session_state: st.session_state['video_cache'] = {}

def get_now_str():
    return datetime.now().strftime("%m/%d %H:%M")

def show_baton_pass_animation():
    st.markdown("""
    <div class="anim-overlay">
        <div class="runner-book">📘💨</div><div class="receiver-book">📙✨</div>
        <div class="pass-message">Nice Pass!</div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(1.5)

def render_video_html(video_path):
    if video_path not in st.session_state['video_cache']:
        try:
            with open(video_path, "rb") as f:
                st.session_state['video_cache'][video_path] = base64.b64encode(f.read()).decode()
        except: return
    
    video_b64 = st.session_state['video_cache'][video_path]
    st.markdown(f"""
        <video width="100%" autoplay loop muted playsinline style="border-radius:15px;box-shadow:0 8px 16px rgba(230,81,0,0.2);max-width:100%;">
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>""", unsafe_allow_html=True)

# --- 通信周り (同期・非同期ハイブリッド) ---

def _background_worker(payload):
    # 送信専用のバックグラウンド処理
    try: requests.post(GAS_URL, json=payload, timeout=5)
    except: pass

def safe_post(data):
    # 非同期でデータを送信する（画面をブロックしない）
    t = threading.Thread(target=_background_worker, args=(data,), daemon=True)
    t.start()

def get_tasks_from_server_async():
    # 裏側でデータを最新にする（更新ボタン用）
    def _fetch():
        try:
            r = requests.get(GAS_URL, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    clean_data = [{k: (v if v is not None else "") for k, v in item.items()} for item in data]
                    st.session_state['tasks_cache'] = clean_data
        except: pass
    
    t = threading.Thread(target=_fetch, daemon=True)
    t.start()

def get_tasks_sync():
    """ログイン時専用：確実にデータを取ってから次へ進む関数"""
    try:
        r = requests.get(GAS_URL, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                clean_data = [{k: (v if v is not None else "") for k, v in item.items()} for item in data]
                st.session_state['tasks_cache'] = clean_data
                return True
            else:
                return False # リストじゃないものが返ってきた
    except:
        pass
    return False

# --- ロジック（履歴機能付き） ---
def update_task_local(task_id, new_status=None, new_content=None, log_msg=None):
    """
    タスクを更新し、履歴(logs)を追記する
    """
    user = st.session_state.get('user_id', 'Unknown')
    now = get_now_str()
    
    target_task = None
    # 高速検索
    for t in st.session_state['tasks_cache']:
        if t['id'] == task_id:
            target_task = t
            break
    
    if target_task:
        # 値の更新
        if new_status: target_task['status'] = new_status
        if new_content: target_task['content'] = new_content
        
        # ログの追記
        if log_msg:
            add_line = f"{now} [{user}] {log_msg}"
            current_logs = target_task.get('logs', '')
            # 空でなければ改行を入れて追記
            target_task['logs'] = f"{current_logs}\n{add_line}" if current_logs else add_line

        # サーバー送信データの準備
        data = {
            "action": "update", 
            "id": task_id,
            "logs": target_task['logs'] # 更新されたログ全文を送る
        }
        if new_status: data["status"] = new_status
        if new_content: data["content"] = new_content
        
        safe_post(data)

def forward_task_local(current_id, new_content, new_target, my_name):
    # 1. 元のタスクを完了＆ログ記録
    update_task_local(current_id, new_status="完了", log_msg=f"➡ {new_target}へバトンパス")
    
    # 2. 新規タスク作成
    new_id = str(uuid.uuid4())
    now = get_now_str()
    first_log = f"{now} [{my_name}] {current_id[:4]}...から引継ぎ作成"
    
    new_task = {
        "id": new_id, "content": new_content, "from_user": my_name, 
        "to_user": new_target, "status": "未着手", "logs": first_log
    }

    # 自分宛てなら即表示
    if new_target == st.session_state.get('user_id'):
        st.session_state['tasks_cache'].append(new_task)

    # 3. 送信
    safe_post({**new_task, "action": "forward", "id": current_id, "new_id": new_id, "new_target": new_target})

# --- 認証 ---
def login():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.5, 1])
    with col1:
        render_video_html("Video Project 3.mp4")
        st.markdown("""
            <h1 style='color:#E65100;font-size:2.2em;'>停滞を、前進へ。<br>タスクが歩き出す。</h1>
            <p style='color:#FB8C00;'>Task Walker gives footsteps to your workflow.</p>
        """, unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown("#### 🔐 MBS Member")
            with st.form("login"):
                uid = st.text_input("ID")
                pwd = st.text_input("Password", type="password")
                submit = st.form_submit_button("LOGIN 👟", use_container_width=True)
                
                if submit:
                    if USERS.get(uid) == pwd:
                        # ★修正：ログイン時はデータをしっかり待って取得する
                        with st.spinner("データを読み込んでいます..."):
                            success = get_tasks_sync()
                            
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = uid
                        if not success:
                            st.toast("⚠️ データの取得に失敗したか、データが空です", icon="⚠️")
                        st.rerun()
                    else: st.error("パスワードが違います")

# ==========================================
#   メイン処理
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "confirm_id" not in st.session_state: st.session_state.confirm_id = None
if "fwd_id" not in st.session_state: st.session_state.fwd_id = None
if "show_anim" not in st.session_state: st.session_state.show_anim = False

if not st.session_state["logged_in"]:
    login()
else:
    if st.session_state.show_anim:
        show_baton_pass_animation()
        st.session_state.show_anim = False
        st.rerun()

    current_user = st.session_state["user_id"]
    is_admin = current_user in ADMIN_USERS
    
    tasks = st.session_state['tasks_cache']
    my_active = sum(1 for t in tasks if t.get('to_user') == current_user and t.get('status') != '完了')
    my_done_rep = sum(1 for t in tasks if t.get('from_user') == current_user and t.get('status') == '完了' and t.get('to_user') != current_user)
    
    label = f"Ⓜ️ {current_user}" + (" 🛡️" if is_admin else "")
    noti_badge = f" 🔴{my_active}" if my_active else ""
    rep_badge = f" ✅{my_done_rep}" if my_done_rep else ""

    with st.sidebar:
        st.title(label)
        menu = st.radio("Menu", [f"📊 マイタスク{noti_badge}", "📝 新規依頼", f"🔔 通知{rep_badge}", "📈 分析"])
        
        # --- 接続診断 & キャッシュクリアボタン ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 ツール")
        
        if st.sidebar.button("⚠️ キャッシュ全削除"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        with st.sidebar.expander("🔍 接続診断"):
            if st.button("データ生受信テスト"):
                try:
                    st.write(f"通信先: {GAS_URL[:20]}...")
                    r = requests.get(GAS_URL, timeout=10)
                    st.write(f"Status: {r.status_code}")
                    if r.status_code == 200:
                        data = r.json()
                        st.success(f"受信成功! {len(data)}件")
                        st.json(data)
                    else:
                        st.error("GASエラー")
                        st.text(r.text)
                except Exception as e:
                    st.error(f"通信エラー: {e}")
        # ------------------------------------

        st.sidebar.divider()
        if st.sidebar.button("ログアウト"):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- 1. マイタスク ---
    if "マイタスク" in menu:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.subheader("📊 マイタスクボード")
        if c2.button("🔄 同期", use_container_width=True):
            get_tasks_from_server_async()
            st.toast("同期を開始しました（裏側）")
            time.sleep(0.5)
            st.rerun()
        
        show_hist = c3.toggle("履歴", False)
        if show_hist: main_col, side_col = st.columns([3, 1])
        else: main_col = st.container(); side_col = None

        with main_col:
            my_tasks = [t for t in tasks if t.get('to_user') == current_user]
            col_todo, col_doing, col_routine = st.columns(3)
            with col_todo: st.error("🛑 未着手")
            with col_doing: st.warning("🏃 対応中")
            with col_routine: st.info("🟣 ルーティン")
            col_map = {"未着手": col_todo, "対応中": col_doing, "ルーティン": col_routine}
            done_list = []

            for t in my_tasks:
                stat = t.get('status', '未着手')
                if stat == "完了":
                    done_list.append(t)
                    continue
                
                target_col = col_map.get(stat, col_todo)
                tid = t['id']
                
                with target_col:
                    with st.container(border=True):
                        st.markdown(f"**{t.get('content')}**")
                        st.caption(f"From: {t.get('from_user')}")
                        
                        # --- 履歴表示エリア ---
                        logs_str = t.get('logs', '')
                        if logs_str:
                            with st.expander("🕒 履歴を確認"):
                                lines = logs_str.split('\n')
                                for line in reversed(lines):
                                    if len(line) > 10:
                                        parts = line.split(' ', 2)
                                        if len(parts) >= 2:
                                            d_str = parts[0] + " " + parts[1]
                                            c_str = parts[2] if len(parts) > 2 else ""
                                            st.markdown(f"<div class='log-entry'><span class='log-date'>{d_str}</span>{c_str}</div>", unsafe_allow_html=True)
                                        else:
                                            st.caption(line)

                        if st.session_state.confirm_id == tid:
                            st.info("完了しますか？")
                            b1, b2 = st.columns(2)
                            if b1.button("完結", key=f"fin{tid}", use_container_width=True):
                                update_task_local(tid, "完了", log_msg="タスク完結")
                                st.session_state.confirm_id = None
                                st.balloons()
                                st.rerun()
                            if b2.button("渡す", key=f"pass{tid}", use_container_width=True):
                                st.session_state.confirm_id = None
                                st.session_state.fwd_id = tid
                                st.rerun()
                            if st.button("戻る", key=f"cncl{tid}", use_container_width=True):
                                st.session_state.confirm_id = None
                                st.rerun()
                        
                        elif st.session_state.fwd_id == tid:
                            st.markdown("##### バトンパス")
                            with st.form(f"fwd{tid}"):
                                to = st.selectbox("誰に", list(USERS.keys()))
                                cont = st.text_input("内容", t.get('content'))
                                if st.form_submit_button("送信"):
                                    forward_task_local(tid, cont, to, current_user)
                                    st.session_state.fwd_id = None
                                    st.session_state.show_anim = True
                                    st.rerun()
                            if st.button("中止", key=f"bck{tid}"):
                                st.session_state.fwd_id = None
                                st.rerun()
                        
                        else:
                            if stat == "未着手":
                                b1, b2 = st.columns(2)
                                if b1.button("着手", key=f"go{tid}", use_container_width=True):
                                    update_task_local(tid, "対応中", log_msg="作業開始")
                                    st.rerun()
                                if b2.button("即完", key=f"qq{tid}", use_container_width=True):
                                    st.session_state.confirm_id = tid
                                    st.rerun()
                            elif stat == "対応中":
                                if st.button("完了へ", key=f"dn{tid}", use_container_width=True):
                                    st.session_state.confirm_id = tid
                                    st.rerun()
                            elif stat == "ルーティン":
                                if st.button("完了", key=f"rdn{tid}", use_container_width=True):
                                    update_task_local(tid, "完了", log_msg="ルーティン完了")
                                    st.balloons()
                                    st.rerun()
                            
                            with st.expander("編集"):
                                ec = st.text_input("修正", t.get('content'), key=f"e{tid}")
                                if st.button("保存", key=f"s{tid}"):
                                    update_task_local(tid, new_content=ec, log_msg=f"内容変更: {ec}")
                                    st.rerun()
                                if st.button("削除", key=f"d{tid}"):
                                    st.session_state['tasks_cache'] = [x for x in st.session_state['tasks_cache'] if x['id'] != tid]
                                    safe_post({"action":"delete", "id":tid})
                                    st.rerun()

        if show_hist and side_col:
            with side_col:
                st.caption("最近の完了済み")
                for t in done_list[:10]:
                    with st.container(border=True):
                        st.markdown(f"~~{t.get('content')}~~")
                        if t.get('logs'):
                            st.caption(f"最終: {t['logs'].splitlines()[-1]}")
                        if st.button("戻す", key=f"rev{t['id']}"):
                            update_task_local(t['id'], "対応中", log_msg="完了から差し戻し")
                            st.rerun()

    # --- 2. 新規 ---
    elif "新規" in menu:
        st.subheader("📤 新規タスク")
        with st.container(border=True):
            ct = st.text_input("タイトル")
            tg = st.selectbox("誰に", list(USERS.keys()))
            ir = st.checkbox("ルーティン")
            if st.button("送信 🚀", use_container_width=True):
                if ct:
                    now = get_now_str()
                    new_obj = {
                        "id": str(uuid.uuid4()), "content": ct, "from_user": current_user,
                        "to_user": tg, "status": "ルーティン" if ir else "未着手", 
                        "logs": f"{now} [{current_user}] 新規作成"
                    }
                    if tg == current_user: st.session_state['tasks_cache'].append(new_obj)
                    safe_post({**new_obj, "action":"create"})
                    st.session_state.show_anim = True
                    st.rerun()

    # --- 3. 通知 ---
    elif "通知" in menu:
        st.subheader("🔔 通知")
        if st.button("更新"): 
            get_tasks_from_server_async()
            st.toast("更新中...")
            st.rerun()
        
        t_me = [t for t in tasks if t.get('to_user') == current_user]
        t_done = [t for t in tasks if t.get('from_user') == current_user and t.get('status') == '完了' and t.get('to_user') != current_user]
        
        t1, t2 = st.tabs([f"依頼 ({len(t_me)})", f"完了報告 ({len(t_done)})"])
        with t1:
            for t in reversed(t_me):
                with st.expander(f"**{t['from_user']}** ➡ {t['content']}"):
                    st.info(f"Status: {t['status']}")
                    st.text(t.get('logs',''))
        with t2:
            for t in reversed(t_done):
                st.success(f"✅ {t['to_user']} が完了: {t['content']}")
                st.caption(t.get('logs','').splitlines()[-1] if t.get('logs') else "")

    # --- 4. 分析 ---
    elif "分析" in menu:
        st.subheader("📊 チーム分析")
        import pandas as pd
        import plotly.express as px
        if st.button("データ更新"): get_tasks_from_server_async()
        
        if tasks:
            df = pd.DataFrame(tasks)
            if not is_admin:
                df = df[(df['to_user'] == current_user) | (df['from_user'] == current_user)]
            
            c1, c2 = st.columns(2)
            active_df = df[df['status'] != '完了']
            
            with c1:
                if not active_df.empty:
                    st.caption("残タスク数")
                    cnt = active_df['to_user'].value_counts().reset_index()
                    st.plotly_chart(px.bar(cnt, x='to_user', y='count', color='to_user'), use_container_width=True)
            with c2:
                st.caption("ステータス割合")
                st.plotly_chart(px.pie(df, names='status'), use_container_width=True)
            
            st.dataframe(df[['content','status','to_user','from_user', 'logs']], use_container_width=True)
