import streamlit as st
import time
import pandas as pd

# ページ設定
st.set_page_config(page_title="Task Walker", page_icon="🚶")

# --- セッション状態の初期化（簡易データベース代わり） ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

# --- サイドバー：ユーザー切り替え（なりきりモード） ---
st.sidebar.header("👤 ログイン設定")
current_user = st.sidebar.selectbox(
    "あなたは誰ですか？",
    ["自分", "上司", "経理担当"],
    index=0
)
st.sidebar.info(f"現在「{current_user}」として操作中")

# --- メイン画面 ---
st.title(f"Task Walker: {current_user}のデスク 🏠")

# 1. タスク一覧の強制表示（タスクが溜まると画面を圧迫する仕様）
# 自分宛てのタスクを抽出
my_tasks = [t for t in st.session_state.tasks if t['to'] == current_user and t['status'] == '未完了']

if len(my_tasks) > 0:
    # タスクがある場合：警告表示とノック
    st.error(f"⚠️ {len(my_tasks)}件のタスクがあなたの部屋の前で待っています！")
    
    # 視覚的な「ノック」演出
    st.markdown("""
    <div style="font-size: 50px; text-align: center; animation: shake 0.5s infinite;">
    ✊ コンコン！
    </div>
    """, unsafe_allow_html=True)

    # タスクカードの表示
    for i, task in enumerate(my_tasks):
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"🤖 **From {task['from']}**: {task['content']}")
            with col2:
                if st.button("受領・完了", key=f"btn_{i}"):
                    # タスクを完了状態にする（リストから削除）
                    st.session_state.tasks.remove(task)
                    st.toast("お疲れ様です！タスクを完了しました。", icon="✅")
                    st.balloons()
                    time.sleep(1)
                    st.rerun() # 画面更新
else:
    # タスクがない場合
    st.success("現在、あなたの手持ちタスクはありません。平和です ☕")


st.divider() # --- 区切り線 ---

# 2. 新しいタスクを歩かせる（送信）
st.subheader("📤 新しいタスクを歩かせる")

with st.form("send_task_form"):
    task_content = st.text_input("タスクの内容", placeholder="例：見積書の承認をお願いします")
    target_user = st.selectbox("誰に歩いて行かせますか？", ["上司", "経理担当", "自分"])
    
    submitted = st.form_submit_button("タスク送信 🚶💨")

    if submitted and task_content:
        # アニメーション演出
        progress_text = f"「{task_content}」が {target_user} に向かって歩いています..."
        my_bar = st.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.01) # 歩くスピード
            my_bar.progress(percent_complete + 1, text=progress_text)
        
        time.sleep(0.5)
        my_bar.empty()

        # データを保存
        new_task = {
            "content": task_content,
            "from": current_user,
            "to": target_user,
            "status": "未完了"
        }
        st.session_state.tasks.append(new_task)
        
        st.success(f"{target_user}さんのデスクに到着しました！")
        st.toast("タスクを送信しました！", icon="📤")

# --- 全体俯瞰（管理者用） ---
with st.expander("🦅 全体のタスク状況を見る（管理者ビュー）"):
    if st.session_state.tasks:
        df = pd.DataFrame(st.session_state.tasks)
        st.dataframe(df)
    else:
        st.write("現在、世界にタスクは存在しません。")

