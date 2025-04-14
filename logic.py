# logic.py



import streamlit as st
import json
import os  # ← これを追加！


SAVE_PATH = "management_data.json"

def init_session_data():
    if 'data' not in st.session_state:
        st.session_state.data = {}

def save_data():
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

def load_data():
    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            st.session_state.data = json.load(f)

def migrate_to_nested_structure():
    """旧形式のタスク・メモ・ログを、タスク内ネスト構造に変換"""
    for genre in st.session_state.data.values():
        for project in genre.values():
            for file_name, file_data in project.items():
                # __meta__など、tasksキーを持たない辞書はスキップ
                if not isinstance(file_data, dict):
                    continue
                if "tasks" not in file_data:
                    continue
                if file_data["tasks"] and isinstance(file_data["tasks"][0], dict) and "memos" in file_data["tasks"][0]:
                    continue  # 既にネスト構造ならスキップ

                memos = file_data.pop("memos", [])
                logs = file_data.pop("logs", [])
                tasks = file_data.get("tasks", [])

                # 各タスクに空の memos/logs を付与
                for i, task in enumerate(tasks):
                    task["memos"] = [memos[i]] if i < len(memos) else []
                    task["logs"] = [logs[i]] if i < len(logs) else []

                file_data["tasks"] = tasks

def add_undo_entry(entry_type, path, data):
    if "undo_history" not in st.session_state:
        st.session_state.undo_history = []
    st.session_state.undo_history.append({
        "type": entry_type,
        "path": path,
        "data": data
    })
