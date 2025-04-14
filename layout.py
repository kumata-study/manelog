#layout.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
from logic import save_data, add_undo_entry
from calendar import monthrange


def show_header(selected_genre):
    if not selected_genre:
        return

    st.subheader(f"現在開いているテーマ: {selected_genre}")

    projects_to_delete = []
    today = datetime.today()

    for project, files in st.session_state.data[selected_genre].items():
        with st.expander(f"📁 {project}"):
            # 🔻 プロジェクト削除ボタン
            cols_project = st.columns([5, 1])
            with cols_project[1]:
                if st.button("🗑️プロジェクトを削除", key=f"delete_project_{selected_genre}_{project}"):
                    add_undo_entry("project", [selected_genre, project], st.session_state.data[selected_genre][project])
                    projects_to_delete.append(project)

            # 🔽 タスクフォルダー追加フォームのトグル
            if f"show_add_form_{project}" not in st.session_state:
                st.session_state[f"show_add_form_{project}"] = False

            if st.button("📁 タスクフォルダーを追加", key=f"toggle_add_file_{selected_genre}_{project}"):
                st.session_state[f"show_add_form_{project}"] = not st.session_state[f"show_add_form_{project}"]

            if st.session_state[f"show_add_form_{project}"]:
                new_file_name = st.text_input(f"タスクフォルダー名（{project}）", key=f"new_file_{selected_genre}_{project}")
                folder_start = st.date_input("📅 開始日", value=today, key=f"new_file_start_{project}")
                folder_end = st.date_input("📅 終了日", value=today, key=f"new_file_end_{project}")

                if st.button("📌 登録", key=f"add_file_{selected_genre}_{project}"):
                    if new_file_name:
                        task_id = str(uuid.uuid4())
                        st.session_state.data[selected_genre][project][new_file_name] = {
                            "start": folder_start.strftime("%Y-%m-%d"),
                            "end": folder_end.strftime("%Y-%m-%d"),
                            "tasks": [], 
                            "memos": [],
                            "logs": []
                        }
                        save_data()
                        st.rerun()
                    else:
                        st.warning("タスクフォルダー名を入力してください")

            # 📂 タスク一覧
            for file, data in files.items():
                file_key = f"{selected_genre}_{project}_{file}"
                if f"show_{file_key}" not in st.session_state:
                    st.session_state[f"show_{file_key}"] = False
                if f"edit_mode_{file_key}" not in st.session_state:
                    st.session_state[f"edit_mode_{file_key}"] = False

                # 🔲 タスクフォルダー全体をボックスで囲む
                with st.container():
                    st.markdown(
                        f"""
                        <div style='padding: 15px; border: 2px solid #ccc; border-radius: 10px; margin-top: 15px; background-color: #f9f9f9;'>
                        <h4 style='margin-bottom: 10px;'>📁 タスクフォルダー：{file}</h4>
                        """,
                        unsafe_allow_html=True
                    )

                    row = st.columns([4, 1, 1])
                    with row[0]:
                        st.markdown(f"📅 {data.get('start', '未設定')} ～ {data.get('end', '未設定')}")
                    with row[1]:
                        if st.button("✏️ 編集", key=f"edit_folder_{file_key}"):
                            st.session_state[f"edit_mode_{file_key}"] = not st.session_state[f"edit_mode_{file_key}"]
                    with row[2]:
                        if st.button("🗑️タスクフォルダーを削除", key=f"delete_folder_{file_key}"):
                            del st.session_state.data[selected_genre][project][file]
                            save_data()
                            st.success(f"「{file}」を削除しました")
                            st.rerun()

                    if st.session_state[f"edit_mode_{file_key}"]:
                        start_val = data.get("start", today.strftime("%Y-%m-%d"))
                        end_val = data.get("end", today.strftime("%Y-%m-%d"))

                        folder_start_key = f"{file_key}_folder_start"
                        folder_end_key = f"{file_key}_folder_end"

                        start_date = st.date_input("📅 開始日", value=datetime.strptime(start_val, "%Y-%m-%d"), key=folder_start_key)
                        end_date = st.date_input("📅 終了日", value=datetime.strptime(end_val, "%Y-%m-%d"), key=folder_end_key)

                        data["start"] = start_date.strftime("%Y-%m-%d")
                        data["end"] = end_date.strftime("%Y-%m-%d")

                    # ヘッダー表示（詳細ページ用にセッションに記録）
                    folder_period = f"（{data.get('start', '未設定')}～{data.get('end', '未設定')}）"
                    header_text = f"{selected_genre} > {project} > {file} {folder_period}"
                    st.session_state[f"header_text_{file_key}"] = header_text

                    if st.button(f"➡️ 詳細を開く", key=f"open_{file_key}"):
                        st.session_state.selected_project = project
                        st.session_state.selected_file = file
                        st.session_state.selected_mode = "file"
                        st.session_state.current_header = header_text
                        st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)

    for p in projects_to_delete:
        del st.session_state.data[selected_genre][p]
    if projects_to_delete:
        save_data()
        st.rerun()


def show_project_input(selected_genre):
    if not selected_genre:
        st.header("📂 登録済みジャンル一覧")
        if st.session_state.data:
            for genre in st.session_state.data:
                if st.button(f"📁 {genre}", key=f"jump_{genre}"):
                    st.session_state.selected_genre = genre
                    st.session_state.selected_mode = None
                    st.session_state.selected_project = None
                    st.session_state.selected_file = None
                    st.rerun()
        else:
            st.info("ジャンルがまだ登録されていません")
        return

    st.header("📌 プロジェクト登録")

    if "show_project_input" not in st.session_state:
        st.session_state.show_project_input = False

    if st.button("➕ プロジェクトを登録"):
        st.session_state.show_project_input = not st.session_state.show_project_input

    if st.session_state.show_project_input:
        project = st.text_input("プロジェクト名（例：SOM）")
        start_date = st.date_input("開始日", value=datetime.today(), key="project_start")
        end_date = st.date_input("終了日", value=datetime.today() + timedelta(days=30), key="project_end")

        if st.button("📌 登録"):
            if project:
                st.session_state.data.setdefault(selected_genre, {})
                st.session_state.data[selected_genre][project] = {}
                save_data()
                st.success(f"プロジェクト「{project}」を作成しました")
                st.session_state.show_project_input = False
                st.rerun()
            else:
                st.warning("プロジェクト名を入力してください")


def show_file_page(selected_genre, project, file):
    file_data = st.session_state.data[selected_genre][project][file]
    start = file_data.get("start", "未設定")
    end = file_data.get("end", "未設定")
    st.header(f"{selected_genre} > {project} > {file}（{start} ～ {end}）")

    st.markdown("---")

    if "show_add_form" not in st.session_state:
        st.session_state["show_add_form"] = False

    st.markdown("## 🆕 タスクを追加")

    if st.button("➕ フォームを開く / 閉じる", key="toggle_add_task"):
        st.session_state["show_add_form"] = not st.session_state["show_add_form"]

    if st.session_state["show_add_form"]:
        new_task = st.text_area("タスク内容", key="new_task_input", value="", height=100)
        start_date = st.date_input("開始日", value=datetime.today(), key="new_task_start")
        end_date = st.date_input("終了日", value=datetime.today() + timedelta(days=6), key="new_task_end")

        if st.button("📌 登録", key="add_new_task"):
            if new_task.strip():
                file_data["tasks"].append({
                    "id": str(uuid.uuid4()),
                    "content": new_task.strip(),
                    "done": False,
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "memos": [],
                    "logs": []
                })
                save_data()
                st.rerun()
            else:
                st.warning("タスク名を入力してください")

    st.markdown("---")

    for i, task in enumerate(file_data["tasks"]):
        task_id = task["id"]
        edit_key = f"edit_mode_{task_id}"
        taskname_key = f"edit_taskname_{task_id}"

        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        cols = st.columns([2, 2, 1])

        with cols[0]:
            if not task["done"]:
                if st.button("🔄 未完了", key=f"done_{task_id}"):
                    task["done"] = True
                    save_data()
                    st.rerun()
            else:
                if st.button("✅ 完了", key=f"undone_{task_id}"):
                    task["done"] = False
                    save_data()
                    st.rerun()

        with cols[1]:
            if st.button("✏️ 編集", key=f"toggle_edit_{task_id}"):
                if not st.session_state[edit_key]:
                    st.session_state[taskname_key] = task["content"]
                    st.session_state[f"edit_memos_{task_id}"] = [memo["text"] for memo in task["memos"]]
                    st.session_state[f"edit_logs_{task_id}"] = [log["text"] for log in task["logs"]]
                else:
                    task["content"] = st.session_state[taskname_key]
                    task["memos"] = [
                        {"text": m, "time": task["memos"][j]["time"] if j < len(task["memos"]) else datetime.now().strftime("%Y-%m-%d %H:%M")}
                        for j, m in enumerate(st.session_state.get(f"edit_memos_{task_id}", [])) if m.strip()
                    ]
                    task["logs"] = [
                        {"text": l, "time": task["logs"][j]["time"] if j < len(task["logs"]) else datetime.now().strftime("%Y-%m-%d %H:%M")}
                        for j, l in enumerate(st.session_state.get(f"edit_logs_{task_id}", [])) if l.strip()
                    ]
                    save_data()
                st.session_state[edit_key] = not st.session_state[edit_key]
                st.rerun()

        with cols[2]:
            if not st.session_state[edit_key]:
                if st.button("🗑 削除", key=f"delete_{task_id}"):
                    file_data["tasks"].pop(i)
                    save_data()
                    st.rerun()

        if st.session_state[edit_key]:
            widget_key = f"{taskname_key}_widget"
            new_name = st.text_area("📝 タスク名を編集", value=st.session_state[taskname_key], key=widget_key, height=80)
            st.session_state[taskname_key] = new_name

            st.markdown("📈 **進捗を編集：**")
            log_inputs = []
            for j, log in enumerate(st.session_state.get(f"edit_logs_{task_id}", [])):
                key = f"edit_log_{task_id}_{j}"
                log_inputs.append(st.text_area(f"進捗 {j+1}", value=log, key=key, height=80))
            new_log = st.text_area("新しい進捗を追加", key=f"new_log_{task_id}", height=80)
            if new_log.strip():
                log_inputs.append(new_log)
            st.session_state[f"edit_logs_{task_id}"] = log_inputs

            st.markdown("📝 **メモを編集：**")
            memo_inputs = []
            for j, memo in enumerate(st.session_state.get(f"edit_memos_{task_id}", [])):
                key = f"edit_memo_{task_id}_{j}"
                memo_inputs.append(st.text_area(f"メモ {j+1}", value=memo, key=key, height=80))
            new_memo = st.text_area("新しいメモを追加", key=f"new_memo_{task_id}", height=80)
            if new_memo.strip():
                memo_inputs.append(new_memo)
            st.session_state[f"edit_memos_{task_id}"] = memo_inputs

        else:
            st.markdown(f"### 🎯 {task['content']}")
            st.markdown(f"📅 **期間：** {task.get('start', '未設定')} ～ {task.get('end', '未設定')}")

            st.markdown("📈 **進捗：**")
            for log in task["logs"]:
                st.markdown(f"・{log['text']}（{log['time']}）")
            if not task["logs"]:
                st.markdown("（まだ進捗がありません）")

            st.markdown("📝 **メモ：**")
            for memo in task["memos"]:
                st.markdown(f"・{memo['text']}（{memo['time']}）")
            if not task["memos"]:
                st.markdown("（まだメモがありません）")

        st.markdown("---")

    if st.button("⬅ 戻る"):
        st.session_state.selected_mode = None
        st.session_state.selected_project = None
        st.session_state.selected_file = None
        st.rerun()


def show_home():
    st.title("📊 ダッシュボード")

    st.markdown("   ")
    st.markdown("   ")
    st.markdown("   ")
    st.markdown("   ")
    st.markdown("   ")

    data = st.session_state.data
    if not data:
        st.info("データがありません。ジャンルを登録してください。")
        return

    progress_rows = []

    for genre, projects in data.items():
        for project, files in projects.items():
            all_tasks = []
            for file_data in files.values():
                all_tasks.extend(file_data.get("tasks", []))

            if not all_tasks:
                continue

            done_count = sum(task.get("done", False) for task in all_tasks)
            total_count = len(all_tasks)
            progress = (done_count / total_count * 100) if total_count > 0 else 0

            progress_rows.append({
                "ジャンル": genre,
                "プロジェクト": project,
                "完了率（％）": round(progress, 1),
                "タスク数": total_count
            })

    if not progress_rows:
        st.info("タスクデータがありません。")
        return

    df = pd.DataFrame(progress_rows)
    df["プロジェクト名"] = df["ジャンル"] + " / " + df["プロジェクト"]

    # ---------- 📈 1. ガントチャート風 ----------
    fig_gantt = go.Figure()
    fig_gantt.add_trace(go.Bar(
        x=df["完了率（％）"],
        y=df["プロジェクト名"],
        orientation='h',
        marker=dict(
            color=df["完了率（％）"],
            colorscale='RdYlGn',
            cmin=0,
            cmax=100,
            line=dict(color='black', width=1.5)
        ),
        text=df["完了率（％）"].astype(str) + "%",
        textposition='outside',
        textfont=dict(size=16)
    ))
    fig_gantt.update_layout(
        width=800,
        height=80 * len(df) + 150,
        xaxis_title="タスク完了率（％）",
        xaxis_range=[0, 100],
        yaxis=dict(tickfont=dict(size=20)),
        font=dict(size=18),
        margin=dict(l=120, r=40, t=40, b=40),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # ---------- ✅ 表示 ----------
    st.markdown("""
    <div style="border: 2px solid #ccc; padding: 25px; border-radius: 12px; background-color: #f9f9f9;">
    <h3 style="margin-top: 10px; margin-bottom: 10px;">📈 プロジェクト達成率</h3>
    """, unsafe_allow_html=True)

    st.plotly_chart(fig_gantt, use_container_width=False, key="home_progress_gantt_chart")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("   ")
    st.markdown("   ")
    
    # ✅ 月別ガントチャート
    st.markdown("""
    <div style="border: 2px solid #ccc; padding: 25px; border-radius: 12px; background-color: #f9f9f9;">
    <h3 style="margin-top: 10px; margin-bottom: 10px;">📅 月別ガントチャート</h3>
    """, unsafe_allow_html=True)

    show_monthly_gantt()

    st.markdown("</div>", unsafe_allow_html=True)


def show_monthly_gantt():
    if "selected_month" not in st.session_state:
        st.session_state.selected_month = datetime.today().strftime("%Y-%m")

    data = st.session_state.data
    if not data:
        st.info("データがありません。")
        return

    month_groups = {}

    for genre, projects in data.items():
        for project, files in projects.items():
            for file_name, file_data in files.items():
                start = file_data.get("start")
                end = file_data.get("end")
                if start and end:
                    try:
                        start_dt = datetime.strptime(start, "%Y-%m-%d")
                        end_dt = datetime.strptime(end, "%Y-%m-%d")
                    except ValueError:
                        continue

                    ym = start_dt.strftime("%Y-%m")
                    label = f"{genre} / {project} / {file_name}"
                    done_status = all(t.get("done", False) for t in file_data.get("tasks", []))
                    status = "✅ 完了" if done_status else "❌ 未完了"

                    month_groups.setdefault(ym, []).append({
                        "タスク": label,
                        "開始": start_dt,
                        "終了": end_dt,
                        "状態": status
                    })

    ym = st.session_state.selected_month
    year, month = map(int, ym.split("-"))
    current_month = datetime(year, month, 1)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅ 前の月"):
            prev_month = (current_month - timedelta(days=1)).replace(day=1)
            st.session_state.selected_month = prev_month.strftime("%Y-%m")
            st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align:center;'>📅 {ym} 月のタスクフォルダー</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("次の月 ➡"):
            next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
            st.session_state.selected_month = next_month.strftime("%Y-%m")
            st.rerun()

    rows = month_groups.get(ym, [])
    df = pd.DataFrame(rows)

    start_of_month = datetime(year, month, 1)
    end_of_month = datetime(year, month, monthrange(year, month)[1])

    if df.empty:
        st.info(f"{ym} に表示可能なタスクフォルダーはありません。")
        return

    fig = px.timeline(
        df,
        x_start="開始",
        x_end="終了",
        y="タスク",
        color="状態",
        color_discrete_map={
            "✅ 完了": "lightgreen",
            "❌ 未完了": "salmon"
        }
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=40 * len(df) + 100,
        xaxis_title="日付",
        xaxis_range=[start_of_month, end_of_month],
        margin=dict(l=100, r=40, t=40, b=40),
        font=dict(size=14)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ✅ タスクフォルダーの完了状況（当月）")

    for i, row in df.iterrows():
        folder_name = row["タスク"]
        task_id = f"{row['開始']}_{row['終了']}_{folder_name}_{i}"

        cols = st.columns([6, 2])
        with cols[0]:
            st.markdown(f"📁 {folder_name}")
        with cols[1]:
            st.markdown(row["状態"])

    st.markdown("   ")
    st.markdown("   ")
    st.markdown("   ")
    st.markdown("   ")

    # ====== タスク単位の週別ガントチャート ======
    task_rows = []
    for genre, projects in data.items():
        for project, files in projects.items():
            for file_name, file_data in files.items():
                for task in file_data.get("tasks", []):
                    try:
                        start = datetime.strptime(task["start"], "%Y-%m-%d")
                        end = datetime.strptime(task["end"], "%Y-%m-%d")
                    except:
                        continue
                    label = f"{genre} / {project} / {file_name} / {task['content']}"
                    status = "✅ 完了" if task.get("done") else "❌ 未完了"
                    task_rows.append({
                        "label": label,
                        "開始": start,
                        "終了": end,
                        "状態": status,
                        "genre": genre,
                        "project": project,
                        "file": file_name,
                        "task": task
                    })

    if task_rows:
        st.markdown("""
        <div style="border: 2px solid #ccc; padding: 25px; border-radius: 12px; background-color: #f9f9f9;">
        <h3 style="margin-top: 10px; margin-bottom: 10px;">🗓️ タスクの週別ガントチャート</h3>
        """, unsafe_allow_html=True)

        df_task = pd.DataFrame(task_rows)
        start_range = min(df_task["開始"]) - timedelta(days=min(df_task["開始"]).weekday())
        end_range = max(df_task["終了"]) + timedelta(days=(6 - max(df_task["終了"]).weekday()))

        fig_task = px.timeline(
            df_task,
            x_start="開始",
            x_end="終了",
            y="label",
            color="状態",
            color_discrete_map={
                "✅ 完了": "lightgreen",
                "❌ 未完了": "salmon"
            }
        )
        fig_task.update_yaxes(autorange="reversed")
        fig_task.update_layout(
            height=40 * len(df_task) + 100,
            xaxis_title="週",
            xaxis_range=[start_range, end_range],
            margin=dict(l=100, r=40, t=40, b=40),
            font=dict(size=14)
        )
        st.plotly_chart(fig_task, use_container_width=True)

        st.markdown("### ✅ タスクの完了状況（当月）")
        for i, row in df_task.iterrows():
            task_name = row["label"]
            cols = st.columns([6, 2])
            with cols[0]:
                st.markdown(f"📌 {task_name}")
            with cols[1]:
                if st.button("🔄 未完了" if row["状態"] == "❌ 未完了" else "✅ 完了", key=f"toggle_{i}"):
                    task = row["task"]
                    task["done"] = not task.get("done", False)
                    save_data()
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def show_weekly_task_gantt():
    data = st.session_state.data
    task_rows = []

    for genre, projects in data.items():
        for project, files in projects.items():
            for file, file_data in files.items():
                for task in file_data.get("tasks", []):
                    try:
                        start = datetime.strptime(task["start"], "%Y-%m-%d")
                        end = datetime.strptime(task["end"], "%Y-%m-%d")
                    except:
                        continue
                    label = f"{genre} / {project} / {file} / {task['content']}"
                    status = "✅ 完了" if task.get("done") else "❌ 未完了"
                    task_rows.append({
                        "タスク": label,
                        "開始": start,
                        "終了": end,
                        "状態": status
                    })

    if not task_rows:
        st.info("タスクデータが見つかりません。")
        return

    df = pd.DataFrame(task_rows)
    start_range = min(df["開始"]) - timedelta(days=min(df["開始"]).weekday())
    end_range = max(df["終了"]) + timedelta(days=(6 - max(df["終了"]).weekday()))

    st.markdown("### 🗓️ タスクの週別ガントチャート")

    fig = px.timeline(
        df,
        x_start="開始",
        x_end="終了",
        y="タスク",
        color="状態",
        color_discrete_map={
            "✅ 完了": "lightgreen",
            "❌ 未完了": "salmon"
        }
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=40 * len(df) + 100,
        xaxis_title="週",
        xaxis_range=[start_range, end_range],
        margin=dict(l=100, r=40, t=40, b=40),
        font=dict(size=14)
    )

    st.plotly_chart(fig, use_container_width=True)

