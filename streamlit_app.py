import streamlit as st
import time

st.set_page_config(page_title="Task Walker", page_icon="🤖")

st.title("Task Walker 🤖")
st.write("タスクを歩かせてみましょう！")

# 画面のレイアウト（左：自分、右：相手）
col1, col2, col3 = st.columns([1, 4, 1])

with col1:
    st.info("🏠 自分")

with col3:
    st.success("🏢 担当者")

# タスク送信ボタン
if st.button("タスク送信 📤", type="primary"):
    # プログレスバーで移動を表現
    progress_text = "タスクが移動中..."
    my_bar = st.progress(0, text=progress_text)

    # 0%から100%まで少しずつ進める
    for percent_complete in range(100):
        time.sleep(0.02) # スピード調整
        my_bar.progress(percent_complete + 1, text=progress_text)
    
    # 到着時のアクション
    time.sleep(0.5)
    my_bar.empty() # バーを消す
    
    # ノック通知（トースト）と風船
    st.toast('コンコン！タスクが届きました！', icon='🤖')
    st.balloons()
    st.success("タスクが無事に届きました！")

