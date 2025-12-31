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
# ★ここにGASのURLを確認して貼ってください★
# デプロイ時は「アクセスできるユーザー：全員」を忘れずに！
GAS_URL = "https://script.google.com/macros/s/AKfycbzqYGtlTBRVPiV6Ik4MdZM4wSYSQd5lDvHzx0zfwjUk1Cpb9woC3tKppCOKQ364ppDp/exec"

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
#   🛠 緊急診断エリア (画面の一番上に表示)
# ==========================================
# 接続確認用。不要になったらこのブロックを削除してください
st.markdown("### 🚑 緊急接続テスト")
if st.button("ここを押して通信テストを実行"):
    try:
        st.info(f"通信開始... URL: {GAS_URL[:30]}...")
        r = requests.get(GAS_URL, timeout=10)
        st.write(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            st.success("✅ 通信成功！データが届いています↓")
            st.json(data) # データの生中身を表示
        else:
            st.error("❌ エラー：GASには繋がりましたが、データが取れません。")
            st.write(r.text)
    except Exception as e:
        st.error(f"❌ 通信失敗：URLが間違っているか、ネットが切れています。\n{e}")
st.markdown("---") 

# ==========================================
#   🎨 デザイン (CSS)
# ==========================================
st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; }
    .stApp { background-color: #FFFAF5; }
    [data-testid="stSidebar"] { background-color: #FFF3E0; border-right: 1px solid #FFCC80; }
    h1, h2, h3 { color: #E65100 !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton > button {
        background-color: white; color: #E65100; border: 2px solid #E65100;
        border-radius: 8px; font-weight: bold; transition: all 0.2s;
        width: 100%;
    }
    .stButton > button:hover { background-color: #E65100; color: white; border-color: #E65100; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #FFE0B2 !important; background-color: white;
        border-radius: 10px; box-shadow: 0 2px 4px rgba(230, 81, 0, 0.1);
    }
    .log-entry { font-size: 0.85em; color: #666; border-bottom: 1px solid #eee; padding: 4px 0; }
    .log-date { color: #E65100; font-weight: bold; margin-right: 5px; }
    [data-testid="stStatusWidget"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- キャッシュ & ユーティリティ ---
if 'tasks_cache' not in st.session_state: st.session_state['tasks_cache'] = []
if 'video_cache' not in st.session_state: st.session_state['video_cache'] = {}

def get_now_str():
    # ★ここを変更しました： 年/月/日 時:分
    return datetime.now().strftime("%Y/%m/%d %H:%M")

def render_video_html(video_path):
    try:
        if video_path not in st.session_state['video_cache']:
            with open(video_path, "rb") as f:
                st.session_state['video_cache'][video_path] = base64.b64encode(f.read()).decode()
        
        video_b64 = st.session_state['video_cache'][video_path]
        st.markdown(f"""
            <video width="100%" autoplay loop muted playsinline style="border-radius:15px;box-shadow:0 8px 16px rgba(230,81,0,0.2);max-width:100%;">
                <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
            </video>""", unsafe_allow_html=True)
    except:
        st.warning("動画ファイルが見つかりませんでしたが続行します")

# --- 通信周り ---
def _background_worker(payload):
    try: requests.post(GAS_URL, json=payload, timeout=5)
    except: pass

def safe_post(data):
    t = threading.Thread(target=_background_worker, args=(data,), daemon=True)
    t.start()

def get_tasks_from_server_async():
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
    try:
        r = requests.get(GAS_URL, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                clean_data = [{k: (v if v is not None else "") for k, v in item.items()} for item in data]
                st.session_state['tasks_cache'] = clean_data
                return True
    except: pass
    return False

# --- ロジック ---
def update_task_local(task_id, new_status=None, new_content=None, log_msg=None):
    user = st.session_state.get('user_id', 'Unknown')
    now = get_now_str()
    target_task = None
    for t in st.session_state['tasks_cache']:
        if t['id'] == task_id:
            target_task = t
            break
    
    if target_task:
        if new_status: target_task['status'] = new_status
        if new_content: target_task['content'] = new_content
        if log_msg:
            add_line = f"{now} [{user}] {log_msg}"
            current_logs = target_task.get('logs', '')
            target_task['logs'] = f"{current_logs}\n{add_line}" if current_logs else add_line

        data = {"action": "update", "id": task_id, "logs": target_task['logs']}
        if new_status: data["status"] = new_status
        if new_content: data["content"] = new_content
        safe_post(data)

def forward_task_local(current_id, new_content, new_target, my_name):
    update_task_local(current_id, new_status="完了", log_msg=f"➡ {new_target}へバトンパス")
    new_id = str(uuid.uuid4())
    now = get_now_str()
    first_log = f"{now} [{my_name}] {current_id[:4]}...から引継ぎ作成"
    
    new_task = {
        "id": new_id, "content": new_content, "from_user": my_name, 
        "to_user": new_target, "status": "未着手", "logs": first_log
    }
    if new_target == st.session_state.get('user_id'):
        st.session_state['tasks_cache'].append(new_task)
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
                        with st.spinner("データを読み込んでいます..."):
                            success = get_tasks_sync()
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = uid
                        if not success:
                            st.toast("⚠️ データの取得に失敗", icon="⚠️")
                        st.rerun()
                    else: st.error("パスワードが違います")

# ==========================================
#   メイン処理
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "confirm_id" not in st.session_state: st.session_state.confirm_id = None
if "fwd_id" not in st.session_state: st.session_state.fwd_id = None

if not st.session_state["logged_in"]:
    login()
else:
    current_user = st.session_state["user_id"]
    is_admin = current_user in ADMIN_USERS
    tasks = st.session_state['tasks_cache']
    
    # バッジ計算
    my_active = sum(1 for t in tasks if t.get('to_user') == current_user and t.get('status') != '完了')
    my_done_rep = sum(1 for t in tasks if t.get('from_user') == current_user and t.get('status') == '完了' and t.get('to_user') != current_user)
    label = f"Ⓜ️ {current_user}" + (" 🛡️" if is_admin else "")
    noti_badge = f" 🔴{my_active}" if my_active else ""
    rep_badge = f" ✅{my_done_rep}" if my_done_rep else ""

    with st.sidebar:
        st.title(label)
        menu = st.radio("Menu", [f"📊 マイタスク{noti_badge}", "📝 新規依頼", f"🔔 通知{rep_badge}", "📈 分析"])
        st.divider()
        if st.button("ログアウト"):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- 1. マイタスク ---
    if "マイタスク" in menu:
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.subheader("📊 マイタスクボード")
        if c2.button("🔄 同期", use_container_width=True):
            get_tasks_from_server_async()
            st.toast("同期中...")
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
                        logs_str = t.get('logs', '')
                        if logs_str:
                            with st.expander("🕒 履歴"):
                                st.text(logs_str)

                        if st.session_state.confirm_id == tid:
                            st.info("完了しますか？")
                            b1, b2 = st.columns(2)
                            if b1.button("完結", key=f"fin{tid}"):
                                update_task_local(tid, "完了", log_msg="完結")
                                st.session_state.confirm_id = None
                                st.rerun()
                            if b2.button("渡す", key=f"pass{tid}"):
                                st.session_state.confirm_id = None
                                st.session_state.fwd_id = tid
                                st.rerun()
                        elif st.session_state.fwd_id == tid:
                            with st.form(f"fwd{tid}"):
                                to = st.selectbox("誰に", list(USERS.keys()))
                                cont = st.text_input("内容", t.get('content'))
                                if st.form_submit_button("送信"):
                                    forward_task_local(tid, cont, to, current_user)
                                    st.session_state.fwd_id = None
                                    st.rerun()
                        else:
                            if stat == "未着手":
                                if st.button("着手", key=f"go{tid}"):
                                    update_task_local(tid, "対応中", log_msg="着手")
                                    st.rerun()
                            elif stat == "対応中":
                                if st.button("完了へ", key=f"dn{tid}"):
                                    st.session_state.confirm_id = tid
                                    st.rerun()
                            elif stat == "ルーティン":
                                if st.button("完了", key=f"rdn{tid}"):
                                    update_task_local(tid, "完了", log_msg="ルーティン完了")
                                    st.rerun()
                                    
                            with st.expander("編集"):
                                ec = st.text_input("修正", t.get('content'), key=f"e{tid}")
                                if st.button("保存", key=f"s{tid}"):
                                    update_task_local(tid, new_content=ec)
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
                        if st.button("戻す", key=f"rev{t['id']}"):
                            update_task_local(t['id'], "対応中")
                            st.rerun()
    
    # 他のメニュー
    elif "新規" in menu:
        st.subheader("📤 新規")
        with st.container(border=True):
            ct = st.text_input("内容")
            tg = st.selectbox("誰に", list(USERS.keys()))
            ir = st.checkbox("ルーティン")
            if st.button("送信"):
                now = get_now_str()
                new_obj = {"id": str(uuid.uuid4()), "content": ct, "from_user": current_user, "to_user": tg, "status": "ルーティン" if ir else "未着手", "logs": f"{now} 作成"}
                if tg == current_user: st.session_state['tasks_cache'].append(new_obj)
                safe_post({**new_obj, "action":"create"})
                st.rerun()
    
    elif "通知" in menu:
        st.subheader("🔔 通知")
        if st.button("更新"): get_tasks_from_server_async(); st.rerun()
        t_me = [t for t in tasks if t.get('to_user') == current_user]
        for t in reversed(t_me): st.info(f"{t['from_user']}➡{t['content']} ({t['status']})")
        
    elif "分析" in menu:
        st.subheader("📊 分析")
        if st.button("更新"): get_tasks_from_server_async()
        if tasks:
            import pandas as pd
            st.dataframe(pd.DataFrame(tasks))
