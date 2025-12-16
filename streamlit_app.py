import streamlit as st
import time
import pandas as pd
import requests
from streamlit_lottie import st_lottie

# --- Lottieアニメーションを読み込む関数 ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# ==========================================
#  アニメーション設定（安定版）
#  ※ここを後で好きなURLに書き換えてください
# ==========================================
LOTTIE_RUNNING_TASK = "https://assets5.lottiefiles.com/packages/lf20_w51pcehl.json"
lottie_running = load_lottieurl(LOTTIE_RUNNING_TASK)

# ページ設定
st.set_page_config(page_title="Task Walker", page_icon="📘")

# --- セッション状態の初期化 ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
    
# 移動中フラグ
if 'is_walking' not in st.session_state:
    st.session_state.is_walking = False
if 'walking_target' not in st.session_state:
    st.session_state.walking_target = ""

# --- サイドバー：ユーザー切り替え ---
st.sidebar.header("👤 ログイン設定")
current_user = st.sidebar.selectbox(
    "あなたは誰ですか？",
    ["自分", "上司", "経理担当"],
    index=0
)
st.sidebar.info(f"現在「{current_user}」として操作中")

# --- メイン画面 ---
st.title(f"Task Walker: {current_user}のデスク 🏠")

# =========================================
#  演出パート：移動中のアニメーション表示
# =========================================
if st.session_state.is_walking:
    st.info(f"📘 タスクが「{st.session_state.walking_target}」に向かって走っています！")
    
    if lottie_running:
        st_lottie(
            lottie_running,
            speed=1.5,
            reverse=False,
            loop=True,
            quality="medium",
            height=300,
            key="running_anim"
        )
    else:
        st.warning("⚠️ アニメーション読み込み失敗（URLを確認してください）")
        st.write("🏃‍♂️💨（代わりのテキスト表示）")

    time.sleep(3.5) 
    
    st.session_state.is_walking = False
    st.session_state.walking_target = ""
    st.rerun()

# -----------------------------------------

# 1. タスク一覧
my_tasks = [t for t in st.session_state.tasks if t['to'] == current_user and t['status'] == '未完了']

if len(my_tasks) > 0:
    st.error(f"⚠️ {len(my_tasks)}件のタスクが到着しています！")
    
    st.markdown("""
    <div style="font-size: 50px; text-align: center; animation: shake 0.5s infinite;">
    ✊ コンコン！
    </div>
    <style>
    @keyframes shake {
      0% { transform: translate(1px, 1px) rotate(0deg); }
      10% { transform: translate(-1px, -2px) rotate(-1deg); }
      20% { transform: translate(-3px, 0px) rotate(1deg); }
      30% { transform: translate(3px, 2px) rotate(0deg); }
      40% { transform: translate(1px, -1px) rotate(1deg); }
      50% { transform: translate(-1px, 2px) rotate(-1deg); }
      60% { transform: translate(-3px, 1px) rotate(0deg); }
      70% { transform: translate(3px, 1px) rotate(-1deg); }
      80% { transform: translate(-1px, -1px) rotate(1deg); }
      90% { transform: translate(1px, 2px) rotate(0deg); }
      100% { transform: translate(1px, -2px) rotate(-1deg); }
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        for i, task in enumerate(my_tasks):
            st.info(f"📘 **From {task['from']}**: {task['content']}")
            if st.button("受領・完了", key=f"btn_{i}"):
                st.session_state.tasks.remove(task)
                st.toast("タスク完了！", icon="✅")
                st.balloons()
                time.sleep(1)
                st.rerun()
else:
    if not st.session_state.is_walking:
        st.success("現在、タスクはありません。平和です ☕")


st.divider()

# 2. 送信フォーム
st.subheader("📤 タスクを送り出す")

with st.form("send_task_form", clear_on_submit=True):
    task_content = st.text_input("タスクの内容", placeholder="例：日報の提出")
    target_user = st.selectbox("誰のところへ歩かせますか？", ["上司", "経理担当", "自分"])
    
    submitted = st.form_submit_button(
        "タスク送信 🏃💨", 
        disabled=st.session_state.is_walking
    )

    if submitted and task_content:
        new_task = {
            "content": task_content,
            "from": current_user,
            "to": target_user,
            "status": "未完了"
        }
        st.session_state.tasks.append(new_task)
        
        st.session_state.is_walking = True
        st.session_state.walking_target = target_user
        st.toast("いってらっしゃい！", icon="👋")
        st.rerun()

# --- 全体俯瞰 ---
with st.expander("🦅 全体のタスク状況"):
    if st.session_state.tasks:
        st.dataframe(pd.DataFrame(st.session_state.tasks))
