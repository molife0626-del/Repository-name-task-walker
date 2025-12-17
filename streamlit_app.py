import streamlit as st
import time
import requests
from streamlit_lottie import st_lottie

# ==========================================
#  ⚙️ 設定エリア
# ==========================================

# 1. Google Apps ScriptのURL（さっきコピーしたもの）
# 引用符 "" の中に貼り付けてください
GAS_URL = "https://script.google.com/macros/s/AKfycbzqYGtlTBRVPiV6Ik4MdZM4wSYSQd5lDvHzx0zfwjUk1Cpb9woC3tKppCOKQ364ppDp/exec"

# 2. アプリのパスワード
APP_PASSWORD = "task" 

# 3. アニメーション（歩く本）
LOTTIE_WALKING_BOOK = "https://lottie.host/c6840845-b867-4323-9123-523760e2587c/8s565656.json"

# ==========================================

st.set_page_config(page_title="Task Walker", page_icon="📘")

# --- 通信用の関数 ---
def get_tasks():
    """スプレッドシートからデータを取得"""
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def send_task(data):
    """スプレッドシートへデータを送信"""
    try:
        requests.post(GAS_URL, json=data)
        return True
    except:
        return False

def load_lottieurl(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 認証機能 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    def password_entered():
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.text_input("🔑 パスワードを入力してください", type="password", on_change=password_entered, key="password")
        return False
    return True

# ==========================================
#  メイン処理
# ==========================================

if check_password():
    
    lottie_book = load_lottieurl(LOTTIE_WALKING_BOOK)

    # セッション初期化
    if 'is_walking' not in st.session_state:
        st.session_state.is_walking = False
    if 'walking_target' not in st.session_state:
        st.session_state.walking_target = ""
    if 'walking_speed' not in st.session_state:
        st.session_state.walking_speed = 1.0

    # --- サイドバー ---
    st.sidebar.header("👤 ログイン設定")
    current_user = st.sidebar.selectbox("あなたは誰ですか？", ["自分", "上司", "経理担当"])
    
    if st.sidebar.button("🔄 最新データを受信"):
        st.rerun()
        
    if st.sidebar.button("🔒 ログアウト"):
        del st.session_state["password_correct"]
        st.rerun()
        
    st.sidebar.info(f"現在「{current_user}」として操作中")

    # --- メイン画面 ---
    st.title(f"Task Walker: {current_user}のデスク 🏠")

    # 🏃 アニメーション演出
    if st.session_state.is_walking:
        speed = st.session_state.walking_speed
        msg = "🔥 猛ダッシュ！" if speed > 1.5 else "📘 テクテク..."
        st.info(f"{msg} タスクが「{st.session_state.walking_target}」へ向かっています！")
        
        if lottie_book:
            st_lottie(lottie_book, speed=speed, loop=True, height=250, key="walking")
        
        time.sleep(3.5 if speed <= 1.5 else 1.5)
        st.session_state.is_walking = False
        st.rerun()

    # 1. データ取得と表示
    all_tasks = get_tasks() # ネットから取得
    
    # 自分宛てのタスク
    my_tasks = [t for t in all_tasks if t['to_user'] == current_user and t['status'] == '未完了']

    if len(my_tasks) > 0:
        st.error(f"⚠️ {len(my_tasks)}冊のタスクブックが届いています！")
        st.markdown("""<div style="font-size: 50px; text-align: center; animation: shake 0.5s infinite;">✊ コンコン！</div><style>@keyframes shake {0% { transform: translate(1px, 1px) rotate(0deg); } 50% { transform: translate(-1px, 2px) rotate(-1deg); } 100% { transform: translate(1px, -2px) rotate(-1deg); }}</style>""", unsafe_allow_html=True)

        with st.container():
            for i, task in enumerate(my_tasks):
                prio = task.get('priority', '🌲 通常')
                icon = "🔥" if prio == "🔥 至急" else "📘"
                st.info(f"{icon} **From {task['from_user']}**: {task['content']}")
                
                # ※完了機能（削除）は簡易版のため未実装
                if st.button("確認しました", key=f"btn_{i}"):
                    st.toast("確認しました！")
    else:
        if not st.session_state.is_walking:
            st.success("現在、タスクはありません。")

    st.divider()

    # 2. 送信フォーム
    st.subheader("📤 新しいタスクを送り出す")
    with st.form("send_task_form", clear_on_submit=True):
        content = st.text_input("タスクの内容")
        target = st.selectbox("宛先", ["上司", "経理担当", "自分"])
        priority = st.radio("優先度", ["🔥 至急", "🌲 通常", "🐢 なる早"], horizontal=True, index=1)
        
        if st.form_submit_button("タスク送信 🏃💨", disabled=st.session_state.is_walking):
            if content:
                # 送信データ作成
                new_task = {
                    "content": content,
                    "from_user": current_user,
                    "to_user": target,
                    "priority": priority,
                    "status": "未完了"
                }
                # 送信実行
                if send_task(new_task):
                    st.session_state.is_walking = True
                    st.session_state.walking_target = target
                    st.session_state.walking_speed = 2.5 if priority == "🔥 至急" else 1.0
                    st.rerun()
                else:
                    st.error("送信失敗。URL設定を確認してください。")
